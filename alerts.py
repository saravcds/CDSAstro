"""
Next-90-days alerts: one timeline of the days and turning points worth knowing about,
in plain words, with a calendar (.ics) export.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import uuid

import swisseph as swe

import astro_core as ac

BAD_TARA = {"Vipat": "The Moon passes a star that brings obstacles for you.",
            "Pratyak": "The Moon passes a star that brings resistance from others.",
            "Naidhana": "The Moon passes your Naidhana star, the weakest star of the month for you."}
NATAL_ORB = 3.0


def _local(jd, tz):
    return ac.jd_to_local(jd, tz)


def _moon_8th_spans(ch, j0, j1):
    """Exact Chandrashtama spans: the Moon in the 8th sign from the natal Moon."""
    target = (ch.moon_sign + 7) % 12
    out, t, inside, start = [], j0, False, None
    step = 1 / 24
    while t <= j1:
        s = ac.sign_of(ac.sidereal_lon(t, "Moon", ch.ayanamsa)[0])
        if s == target and not inside:
            lo, hi = t - step, t
            for _ in range(12):
                mid = (lo + hi) / 2
                if ac.sign_of(ac.sidereal_lon(mid, "Moon", ch.ayanamsa)[0]) == target:
                    hi = mid
                else:
                    lo = mid
            inside, start = True, hi if t > j0 else j0
        elif s != target and inside:
            lo, hi = t - step, t
            for _ in range(12):
                mid = (lo + hi) / 2
                if ac.sign_of(ac.sidereal_lon(mid, "Moon", ch.ayanamsa)[0]) == target:
                    lo = mid
                else:
                    hi = mid
            out.append((start, hi))
            inside = False
        t += step
    if inside:
        out.append((start, j1))
    return out


def _dasha_changes(md_list, j0, j1):
    rows = []
    for md in md_list:
        if md.end < j0 or md.start > j1:
            continue
        if j0 <= md.start <= j1:
            rows.append((md.start, 1, md.lord, None, None))
        for ad in md.children:
            if ad.end < j0 or ad.start > j1:
                continue
            if j0 <= ad.start <= j1:
                rows.append((ad.start, 2, md.lord, ad.lord, None))
            if ad.children:
                last = ad.children[-1]
                if last.end >= j0 and last.start <= j1:
                    rows.append((max(last.start, j0), 9, md.lord, ad.lord, last))
            for pd in ad.children:
                if j0 <= pd.start <= j1 and pd is not ad.children[0]:
                    rows.append((pd.start, 3, md.lord, ad.lord, pd))
    return rows


def _eclipses(ch, j0, j1):
    pts = {"your Ascendant": ch.asc, "your natal Sun": ch.planets["Sun"]["lon"],
           "your natal Moon": ch.planets["Moon"]["lon"]}
    out = []
    for fn, kind, body in ((swe.sol_eclipse_when_glob, "Solar", "Sun"), (swe.lun_eclipse_when, "Lunar", "Moon")):
        t = j0
        while True:
            r = fn(t, ac.EPH)[1][0]
            if r > j1:
                break
            lon = ac.sidereal_lon(r, body, ch.ayanamsa)[0]
            hit = [n for n, p in pts.items() if ac.angdist(lon, p) <= NATAL_ORB
                   or ac.angdist((lon + 180) % 360, p) <= NATAL_ORB]
            out.append((r, kind, ch.house_of_sign(ac.sign_of(lon)), hit))
            t = r + 20
    return out


def alerts(ch: ac.Chart, md_list: list, d0: date, lat: float, lon: float, tz: str, days: int = 90) -> list[dict]:
    """Each item: start, end (jd), day (date), kind, tone (good/care/info), title, text, do."""
    import life
    items = []
    j0 = ac.to_jd(datetime(d0.year, d0.month, d0.day, 0, 0), tz)
    j1 = j0 + days

    # 1. Daily scores: best days and weak-star days
    scores = []
    for i in range(days):
        d = d0 + timedelta(i)
        f = ac.daily_forecast(ch, d, lat, lon, tz)
        scores.append((d, f))
    best = sorted([x for x in scores if x[1]["score"] >= 75], key=lambda x: -x[1]["score"])
    for d, f in best:
        jd = ac.to_jd(datetime(d.year, d.month, d.day, 6), tz)
        items.append(dict(start=jd, end=jd + 1, day=d, kind="Best day", tone="good",
                          title=f"Strong day ({f['score']}/100)",
                          text="Your star and the Moon both support you.",
                          do="Use it for launches, pitches, signing, travel or asking for something important."))
    for d, f in scores:
        if f["tara"] == "Naidhana" or (f["tara"] in BAD_TARA and f["score"] < 45):
            jd = ac.to_jd(datetime(d.year, d.month, d.day, 6), tz)
            strong = f["tara"] == "Naidhana"
            items.append(dict(start=jd, end=jd + 1, day=d, kind="Weak star", tone="care",
                              title=f"{f['tara']} star day" + (" (weakest)" if strong else ""),
                              text=BAD_TARA[f["tara"]],
                              do="Keep to routine work; move big starts, signings and hard conversations."))

    # 2. Chandrashtama
    for s, e in _moon_8th_spans(ch, j0, j1):
        ls, le = _local(s, tz), _local(e, tz)
        items.append(dict(start=s, end=e, day=ls.date(), kind="Chandrashtama", tone="care",
                          title="Chandrashtama (Moon in your 8th from birth Moon)",
                          text=f"From {ls:%a %d %b %I:%M %p} to {le:%a %d %b %I:%M %p}. Mood dips, "
                               f"misunderstandings and tiredness are more likely.",
                          do="Rest well, avoid arguments, risky travel and major decisions. Postpone surgery "
                             "if you have a choice."))

    # 3. Dasha turning points
    for jd, lvl, md, ad, pd in _dasha_changes(md_list, j0, j1):
        d = _local(jd, tz).date()
        if lvl == 1:
            items.append(dict(start=jd - 7, end=jd + 7, day=d, kind="Period change", tone="info",
                              title=f"New main period: {md}",
                              text=f"A major new chapter ({md} Mahadasha) begins. The two weeks around the change "
                                   f"(the 'sandhi') feel unsettled.",
                              do="Finish open matters before the change; make big commitments after it settles."))
        elif lvl == 2:
            rating = next((p["rating"] for p in life.dasha_periods(ch, [m for m in md_list if m.lord == md])
                           if p["ad"] == ad and abs(p["start"] - jd) < 2), "Mixed")
            tone = {"Good": "good", "Challenging": "care"}.get(rating, "info")
            items.append(dict(start=jd - 3, end=jd + 3, day=d, kind="Period change", tone=tone,
                              title=f"New sub-period: {md} – {ad} ({rating.lower()})",
                              text=f"The {ad} sub-period starts and colours the coming months. "
                                   f"The few days around the change can feel unsettled.",
                              do="Avoid launching anything major in the 3 days around the change."))
        elif lvl == 9:
            items.append(dict(start=jd, end=pd.end, day=d, kind="Period change", tone="care",
                              title=f"Last phase of the {md} – {ad} sub-period (chhidra)",
                              text=f"The closing phase ({pd.lord}) of this sub-period, until "
                                   f"{_local(pd.end, tz):%d %b %Y}. Endings are natural now; new starts are weaker.",
                              do="Wrap up, review and plan; start big new things after the next sub-period begins."))
        else:
            items.append(dict(start=jd, end=pd.end, day=d, kind="Short phase", tone="info",
                              title=f"Short phase of {pd.lord} begins ({md} – {ad} – {pd.lord})",
                              text=f"Runs until {_local(pd.end, tz):%d %b}. "
                                   + (f"Watch for {life.PLANET_CAUTION[pd.lord]}."
                                      if life._nature(ch, pd.lord) < 0
                                      else f"A supportive few weeks for {life.HOUSE_USE[ch.planets[pd.lord]['house']]}."
                                      if ch.planets[pd.lord]['house'] not in (6, 8, 12)
                                      else "A neutral short phase; steady effort works best."),
                              do=""))

    # 4. Sky events: slow sign changes, retrograde stations, transits over natal points
    for e in ac.key_events(ch, j0, months=max(1, round(days / 30.44)), dashas=None):
        if e["jd"] > j1 or "eclipse" in e["event"].lower():
            continue
        cat = e["category"]
        tone = "info"
        if cat == "Retrograde / direct" and "Mercury" in e["event"] and "retrograde" in e["event"]:
            tone = "care"
        items.append(dict(start=e["jd"], end=e["jd"] + 1, day=_local(e["jd"], tz).date(), kind="Sky event",
                          tone=tone, title=e["event"].split(" - ")[0].split(" (")[0],
                          text=e["event"], do=("Double-check messages, contracts and travel plans."
                                               if tone == "care" else "")))

    # 5. Eclipses
    for jd, kind, h, hit in _eclipses(ch, j0, j1):
        care = bool(hit)
        items.append(dict(start=jd, end=jd + 1, day=_local(jd, tz).date(), kind="Eclipse",
                          tone="care" if care else "info",
                          title=f"{kind} eclipse in your {h}{'st' if h == 1 else 'nd' if h == 2 else 'rd' if h == 3 else 'th'} house"
                                + (f", close to {', '.join(hit)}" if hit else ""),
                          text=f"Highlights {ac.HOUSE_THEMES[h]}." + (" It falls on a sensitive point of your "
                                                                       "chart, so expect a turning point." if care else ""),
                          do="Avoid starting important things on the eclipse day; quiet reflection, "
                             "prayer or charity suit it."))

    # 6. Saturn phases (Sade Sati, Ashtama)
    for s in ac.sade_sati(ch, years_ahead=max(1, int((j1 - ch.jd) / 365.25) + 1)):
        if j0 <= s["start"] <= j1:
            items.append(dict(start=s["start"], end=s["start"] + 1, day=_local(s["start"], tz).date(),
                              kind="Saturn phase", tone="care", title=f"{s['phase']} begins",
                              text="Saturn starts a long testing phase related to your Moon.",
                              do="Slow down, keep commitments, look after health and avoid shortcuts."))
    items.sort(key=lambda x: x["start"])
    return items


def summary(items: list[dict]) -> dict:
    good = [i for i in items if i["kind"] == "Best day"]
    care = [i for i in items if i["tone"] == "care"]
    return dict(n_good=len(good), n_care=len(care),
                best=sorted(good, key=lambda x: x["start"])[:5],
                chandrashtama=[i for i in items if i["kind"] == "Chandrashtama"])


def _ics_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def to_ics(items: list[dict], name: str, tz: str) -> str:
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CDS Astro//Next 90 days//EN", "CALSCALE:GREGORIAN",
           f"X-WR-CALNAME:{_ics_text(name)} - CDS Astro"]
    for it in items:
        if it["kind"] == "Short phase":
            continue
        ls = _local(it["start"], tz)
        le = _local(it["end"], tz)
        out.append("BEGIN:VEVENT")
        out.append(f"UID:{uuid.uuid4()}@cdsastro")
        out.append(f"DTSTAMP:{now}")
        if it["kind"] == "Chandrashtama":
            out.append(f"DTSTART:{ls.astimezone(ac.ZoneInfo('UTC')):%Y%m%dT%H%M%SZ}")
            out.append(f"DTEND:{le.astimezone(ac.ZoneInfo('UTC')):%Y%m%dT%H%M%SZ}")
        else:
            d1 = it["day"]
            d2 = max(le.date(), d1) + timedelta(1) if it["end"] - it["start"] > 1.5 else d1 + timedelta(1)
            out.append(f"DTSTART;VALUE=DATE:{d1:%Y%m%d}")
            out.append(f"DTEND;VALUE=DATE:{d2:%Y%m%d}")
        icon = {"good": "✅ ", "care": "⚠️ "}.get(it["tone"], "")
        out.append(f"SUMMARY:{_ics_text(icon + it['title'])}")
        out.append(f"DESCRIPTION:{_ics_text((it['text'] + ' ' + it['do']).strip())}")
        out.append("TRANSP:TRANSPARENT")
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"
