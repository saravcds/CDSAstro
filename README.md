# CDS Astro – Jyotish Workbench

A password-protected Streamlit app for Vedic astrology calculations, built on the Swiss Ephemeris
(the same engine used by Jagannatha Hora, Parashara's Light and AstroSage), with Day, Week, Month and Year predictions.

## Features
- **Birth chart** (South Indian style), D2/D3/D4/D7/D9/D10/D12, dignities, combustion, aspects, rule-based readings
- **KP**: Placidus cusps, star / sub / sub-sub lords for planets and cusps
- **Dashas**: Vimshottari (to pratyantar) and Yogini, with the current period highlighted
- **Yogas & Jaimini**: common yogas, chara karakas, functional benefics/malefics, lifetime Saturn cycles
- **Transits & key dates**: gochara, sign changes, stations, eclipses on natal points, dasha changes
- **Daily**: panchang, Tara Bala, Chandra Bala, Rahu Kalam / Yamagandam / Gulika / Abhijit,
  best windows, 24 horas, transparent day rating
- **Muhurta finder** by purpose, optionally checked for a second person
- **Compatibility**: Ashtakoota (36), Mars dosha, professional synastry
- **Predictions**: one-click Day, Week, Month and Year predictions. Rule-based (no external AI): Tara Bala,
  Chandra Bala, tithi, Moon's house, slow-planet transits from both Moon and Ascendant, Saturn cycles and the
  running dasha, with ratings, best and difficult days or months, outlook by life area, and key dates.
- **Password protection** with a lock-out after repeated failures

## Secrets
| Name | Required | Purpose |
|---|---|---|
| `APP_PASSWORD` | Yes | Sign-in password. The app stays locked if it is not set |
| `PROFILES_JSON` | No | People to load automatically, as JSON (see `.streamlit/secrets.toml.example`) |

## Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io and sign in with GitHub.
2. **Create app** → pick this repository, branch `main`, main file `app.py`.
3. **Advanced settings** → Python **3.11** or **3.12**, and paste your secrets
   (format as in `.streamlit/secrets.toml.example`).
4. Deploy. The first build takes a few minutes because `pyswisseph` compiles from source.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit it
streamlit run app.py
```

## Privacy
- Never commit `profiles.json` or `.streamlit/secrets.toml` (both are in `.gitignore`).
- All calculations run inside the app; no chart data is sent to outside services.

## Accuracy notes
- Positions match Jagannatha Hora / AstroSage to within about 0.01° with the same settings.
- Differences between programs come from ayanamsa, true vs mean node, and dasha year length.
- Interpretations describe traditional principles, not certainties.
