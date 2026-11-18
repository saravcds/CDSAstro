"""
Persistent storage for people's birth details.

Streamlit Cloud does not keep files between restarts, and app secrets are
read-only, so new people must be saved somewhere outside the app.

Backends, in order of preference:
1. A private GitHub repository (secrets GITHUB_TOKEN and GITHUB_DATA_REPO).
   The app reads and writes one JSON file through the GitHub API.
2. A local profiles.json next to the app (works when running on your own computer).

The PROFILES_JSON secret is only used to seed storage the first time,
when no saved file exists yet.
"""
from __future__ import annotations

import base64
import json
import os

import requests

API = "https://api.github.com"
LOCAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")


class Storage:
    def __init__(self, token: str | None, repo: str | None, path: str = "profiles.json",
                 branch: str | None = None):
        self.token, self.repo, self.path, self.branch = token, repo, path or "profiles.json", branch

    @property
    def is_github(self) -> bool:
        return bool(self.token and self.repo)

    @property
    def label(self) -> str:
        return f"private GitHub repo {self.repo}" if self.is_github else "local file on the server"

    # -- GitHub ---------------------------------------------------------------
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"}

    def _url(self) -> str:
        return f"{API}/repos/{self.repo}/contents/{self.path}"

    def _get(self) -> tuple[dict | None, str | None]:
        params = {"ref": self.branch} if self.branch else None
        r = requests.get(self._url(), headers=self._headers(), params=params, timeout=20)
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        j = r.json()
        return json.loads(base64.b64decode(j["content"]).decode("utf-8")), j["sha"]

    def _put(self, data: dict, message: str) -> None:
        _, sha = self._get()  # always use the latest version to avoid conflicts
        body = {"message": message,
                "content": base64.b64encode(json.dumps(data, indent=2, ensure_ascii=False).encode()).decode()}
        if sha:
            body["sha"] = sha
        if self.branch:
            body["branch"] = self.branch
        r = requests.put(self._url(), headers=self._headers(), json=body, timeout=20)
        r.raise_for_status()

    # -- Public ---------------------------------------------------------------
    def load(self) -> dict | None:
        """Return saved profiles, or None if nothing has been saved yet."""
        if self.is_github:
            data, _ = self._get()
            return data
        try:
            with open(LOCAL_FILE, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def save(self, data: dict, message: str = "Update profiles") -> None:
        if self.is_github:
            self._put(data, message)
            return
        with open(LOCAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
