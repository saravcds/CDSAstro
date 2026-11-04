"""
Rule-based predictions for a day, week, month and year.

Everything here is derived from the app's own calculations (astro_core) using
traditional rules: Tara Bala, Chandra Bala, tithi, Moon's house, gochara of the
slow planets, Saturn cycles and the running dasha. Scores are indicators on a
0-100 scale (50 = neutral), not forecasts of events.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

import astro_core as ac

# ---------------------------------------------------------------------------
# Text tables
# ---------------------------------------------------------------------------
# Moon's house from the Ascendant on a given day:
# (headline, work, money, relationships, health)
MOON_HOUSE_DAY = {
    1: ("Personal focus. Good energy to start things for yourself.",
        "Take the lead on your own priorities.", "Neutral; avoid impulse buys.",
        "You are noticed; keep the tone warm.", "Good energy; do not overdo it."),
    2: ("Money, family and speech are in focus.",
        "Good for financial reviews and pricing.", "Good for collections and budgeting.",
        "Family matters come up; speak gently.", "Watch food habits."),
    3: ("Effort pays off. Good for initiative and communication.",
        "Calls, pitches, follow-ups and short trips go well.", "Gains through your own effort.",
        "Good for reaching out to siblings and friends.", "Active and energetic."),
    4: ("Home, comfort and peace of mind are in focus.",
        "Steady day; good for office set-up and internal work.", "Spending on home or comfort likely.",
        "Time with family and mother is favoured.", "Rest well; emotions can run high."),
    5: ("Ideas, children and investments are in focus.",
        "Good for planning, strategy and creative work.", "Think long-term; avoid speculation.",
        "Warm day for romance and children.", "Generally good."),
    6: ("A problem-solving day. Good against competition.",
        "Clear backlog, handle disputes, beat deadlines.", "Settle dues; avoid new loans.",
        "Avoid arguments; be practical.", "Watch digestion and stress."),
    7: ("Partners, clients and contracts are in focus.",
        "Good for client meetings and negotiations.", "Gains through partners.",
        "Good for the spouse and close partners.", "Balanced."),
    8: ("A sensitive day. Hidden issues may surface.",
        "Avoid big decisions; do research and checks.", "Be careful with money and paperwork.",
        "Keep conversations calm and private.", "Rest; take care while travelling."),
    9: ("Fortune, mentors and long-distance matters are favoured.",
        "Good for advice from seniors and travel plans.", "Luck supports planned moves.",
        "Good for elders and teachers.", "Good."),
    10: ("Career and visibility are in focus.",
         "Strong for leadership, meetings and public work.", "Gains through work.",
         "Work can crowd out family time.", "Busy; pace yourself."),
    11: ("Gains, networks and wishes are favoured.",
         "Good for closing, networking and results.", "Good for income and receipts.",
         "Friends and groups are helpful.", "Good."),
    12: ("Expenses, rest and behind-the-scenes work.",
         "Good for planning and foreign matters; slow for launches.", "Spending likely; keep a check.",
         "Quiet time; avoid misunderstandings.", "Rest and sleep well."),
}
TRANSIT_VERB = {
    "Jupiter": "expands, protects and brings opportunities in",
    "Saturn": "slows down, tests and builds discipline in",
    "Rahu": "brings ambition, restlessness and unusual openings in",
    "Ketu": "brings detachment or sudden change in",
    "Mars": "energises and can bring friction in",
    "Sun": "puts focus and visibility on",
    "Venus": "brings comfort and pleasant contacts in",
    "Mercury": "activates thinking, talks and trade in",
}
AREAS = {
    "Career": {1, 6, 10, 11},
    "Money": {2, 5, 9, 11},
    "Relationships": {5, 7},
    "Home & family": {2, 4},
    "Health": {1, 6, 8, 12},
}
SLOW_WEIGHT = {"Jupiter": 3.0, "Saturn": 3.0, "Rahu": 1.5, "Ketu": 1.0, "Mars": 1.0, "Sun": 0.7}


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def _house_from(a: int, b: int) -> int:
    return (b - a) % 12 + 1


def quick_day(ch: ac.Chart, d: date, tz: str) -> dict:
    """Fast day score at local noon (no sunrise maths). Used for weeks, months and years."""
    jd = ac.to_jd(datetime(d.year, d.month, d.day, 12), tz)
    m = ac.sidereal_lon(jd, "Moon", ch.ayanamsa)[0]
    s = ac.sidereal_lon(jd, "Sun", ch.ayanamsa)[0]
    msign, nk = ac.sign_of(m), ac.nak_of(m)
    tara, tq = ac.tara_of(ch.moon_nak, nk)
    h_asc = ch.house_of_sign(msign)
    h_moon = _house_from(ch.moon_sign, msign)
    tithi = int(((m - s) % 360) // 12) + 1
    yoga = ac.YOGA_NAMES[int(((m + s) % 360) // ac.NAK)]
    score, flags = 50, []
    score += {"good": 15, "bad": -15, "mixed": -5}[tq] if tara != "Naidhana" else -25
    if h_moon == 8:
        score -= 20
        flags.append("Chandrashtama")
    elif h_moon in (1, 3, 6, 7, 10, 11):
        score += 10
    else:
        score -= 5
    if h_asc in (8, 12):
        score -= 8
    elif h_asc in (1, 5, 9, 10, 11):
        score += 6
    if tithi in ac.RIKTA_TITHIS:
        score -= 8
        flags.append("Rikta tithi")
    elif tithi == 30:
        score -= 10
        flags.append("Amavasya")
    elif tithi in (5, 10, 15, 20, 25):
        score += 5
    if tithi == 15:
        flags.append("Full moon")
    if yoga in ac.BAD_YOGAS:
        score -= 5
    vl = ac.WEEKDAY_LORD[d.weekday()]
    fn = ac.functional_nature(ch, vl)
    if fn.startswith(("Benefic", "Yogakaraka")):
        score += 5
    elif fn.startswith("Malefic"):
        score -= 3
    if tara == "Naidhana":
        flags.append("Naidhana tara")
    score = max(0, min(100, score))
    good_for = []
    if tq == "good" and tithi not in ac.RIKTA_TITHIS and tithi != 30 and h_moon != 8 and h_asc not in (8, 12):
        if d.weekday() in (0, 2, 3, 4):
            good_for.append("business / signing")
        if h_asc in (2, 11) or tara == "Sampat":
            good_for.append("money matters")
        if h_asc in (5, 7) or d.weekday() == 4:
            good_for.append("relationships")
        if h_asc in (3, 9):
            good_for.append("travel / outreach")
    if h_asc in (6, 12) or h_moon == 8:
        good_for.append("rest, review, clearing backlog")
    return dict(date=d, weekday=d.strftime("%a"), score=score, tara=tara, tara_quality=tq,
                nakshatra=ac.NAKSHATRAS[nk], moon_sign=ac.SIGNS[msign], house_from_asc=h_asc,
                house_from_moon=h_moon, tithi=ac.tithi_name(tithi), flags=flags,
                good_for=good_for, theme=MOON_HOUSE_DAY[h_asc][0])


GOOD_FROM_LAGNA = {"Jupiter": {1, 2, 5, 7, 9, 10, 11}, "Saturn": {3, 6, 11},
                   "Rahu": {3, 6, 10, 11}, "Ketu": {3, 6, 11}, "Mars": {3, 6, 10, 11},
                   "Sun": {3, 6, 10, 11}}


def transit_strength(ch: ac.Chart, jd: float) -> tuple[float, list[str]]:
    """Background strength from slow planets, judged equally from the natal Moon (gochara)
    and from the Ascendant, plus Saturn cycles."""
    total, notes = 0.0, []
    for p, w in SLOW_WEIGHT.items():
        lon = ac.sidereal_lon(jd, p, ch.ayanamsa, ch.node)[0]
        s = ac.sign_of(lon)
        hm = _house_from(ch.moon_sign, s)
        ha = ch.house_of_sign(s)
        total += 0.5 * (w if hm in ac.GOOD_FROM_MOON[p] else -0.6 * w)
        total += 0.5 * (w if ha in GOOD_FROM_LAGNA[p] else -0.6 * w)
    sat = ac.sign_of(ac.sidereal_lon(jd, "Saturn", ch.ayanamsa)[0])
    hs = _house_from(ch.moon_sign, sat)
    if hs in (12, 1, 2):
        total -= 2
        notes.append(f"Sade Sati ({ {12: 'rising', 1: 'peak', 2: 'setting'}[hs] } phase)")
    elif hs == 8:
        total -= 2
        notes.append("Ashtama Shani (Saturn 8th from Moon)")
    elif hs == 4:
        total -= 1
        notes.append("Kantaka Shani (Saturn 4th from Moon)")
    return total, notes


def _nature_points(ch: ac.Chart, lord: str) -> float:
    if lord in ("Rahu", "Ketu"):
        disp = ac.SIGN_LORD[ch.planets[lord]["sign"]]
        return 0.5 * _nature_points(ch, disp)
    fn = ac.functional_nature(ch, lord)
    if fn.startswith("Yogakaraka"):
        return 6
    if fn.startswith("Benefic"):
        return 4
    if fn.startswith("Malefic"):
        return -3
    return 0


def dasha_points(ch: ac.Chart, md_list: list, jd: float) -> tuple[float, list]:
    chain = ac.current_chain(md_list, jd)
    pts = 0.0
    for p, w in zip(chain, (0.5, 0.35, 0.15)):
        pts += w * _nature_points(ch, p.lord)
    return pts, chain


def period_rating(ch: ac.Chart, md_list: list, days: list[dict], jd_mid: float) -> dict:
    avg = sum(x["score"] for x in days) / max(1, len(days))
    ts, notes = transit_strength(ch, jd_mid)
    dp, chain = dasha_points(ch, md_list, jd_mid)
    rating = 50 + 0.6 * (avg - 50) + 1.6 * ts + dp
    return dict(rating=int(max(0, min(100, round(rating)))), daily_avg=round(avg),
                transit=round(ts, 1), dasha=round(dp, 1), notes=notes, chain=chain)


def slow_transits(ch: ac.Chart, j0: float, j1: float,
                  planets=("Jupiter", "Saturn", "Rahu", "Ketu")) -> list[dict]:
    out = []
    for p in planets:
        src = "Rahu" if p == "Ketu" else p
        for s, e, sg in ac._scan_segments(src, ch, j0, j1, step=1):
            if p == "Ketu":
                sg = (sg + 6) % 12
            h = ch.house_of_sign(sg)
            hm = _house_from(ch.moon_sign, sg)
            out.append(dict(planet=p, start=s, end=e, sign=ac.SIGNS[sg], house=h, house_from_moon=hm,
                            classical="favourable" if hm in ac.GOOD_FROM_MOON[p] else "challenging",
                            text=f"{p} in your house {h} ({ac.HOUSE_THEMES[h]}) "
                                 f"{TRANSIT_VERB[p].split(' in')[0]}."))
    return out


def area_outlook(ch: ac.Chart, transits: list[dict], chain: list) -> list[dict]:
    """Score each life area from slow-planet houses and the running dasha lords."""
    rows = []
    for area, houses in AREAS.items():
        pts, why = 0.0, []
        for t in transits:
            if t["house"] not in houses:
                continue
            p = t["planet"]
            if area == "Health":
                delta = {"Jupiter": 1, "Saturn": -1.5, "Rahu": -1, "Ketu": -1, "Mars": -0.5}.get(p, 0)
                if t["house"] == 6 and p in ("Saturn", "Rahu", "Ketu", "Mars"):
                    delta = 0.5
            else:
                delta = {"Jupiter": 2, "Saturn": -1, "Rahu": 0.5, "Ketu": -0.5}.get(p, 0)
                if p in ("Saturn", "Rahu") and t["house"] in (6, 11):
                    delta = 1.5
            pts += delta
            why.append(f"{p} in house {t['house']}")
        for p in chain[:2]:
            lord = p.lord
            rel = set(ch.houses_owned(lord)) | {ch.planets[lord]["house"]}
            if rel & houses:
                pts += 1 if _nature_points(ch, lord) >= 0 else -0.5
                why.append(f"dasha lord {lord} linked to house(s) {', '.join(map(str, sorted(rel & houses)))}")
        verdict = "Supportive" if pts >= 1.5 else "Challenging" if pts <= -1 else "Mixed / steady"
        rows.append(dict(area=area, verdict=verdict, points=round(pts, 1),
                         why="; ".join(dict.fromkeys(why)) or "no major transit in these houses"))
    return rows


def ingress_events(ch: ac.Chart, j0: float, j1: float, planets=("Sun", "Mercury", "Venus")) -> list[dict]:
    ev = []
    for p in planets:
        for s, e, sg in ac._scan_segments(p, ch, j0, j1, step=0.5)[1:]:
            h = ch.house_of_sign(sg)
            ev.append(dict(jd=s, category="Sign change",
                           event=f"{p} enters {ac.SIGNS[sg]} - your house {h} ({ac.HOUSE_THEMES[h]})"))
    return ev


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def predict_day(ch: ac.Chart, md_list: list, d: date, lat: float, lon: float, tz: str) -> dict:
    fc = ac.daily_forecast(ch, d, lat, lon, tz)
    h = fc["house_from_asc"]
    head, work, money, rel, health = MOON_HOUSE_DAY[h]
    tara = fc["tara"]
    do, avoid = [], []
    if fc["tara_quality"] == "good":
        do.append("Schedule important calls and meetings in the best windows.")
    else:
        avoid.append(f"Starting new ventures or signing (star is your {tara} tara).")
    if fc["house_from_moon"] == 8:
        avoid.append("Big decisions and arguments (Chandrashtama day).")
        rel = "Keep conversations calm; misunderstandings are more likely today."
    tt = fc["panchang"]["tithi"][0][2]
    if tt in ac.RIKTA_TITHIS:
        avoid.append("New beginnings (Rikta tithi). Finish pending work instead.")
    if h in (2, 11):
        do.append("Follow up on payments and receivables.")
    if h in (3, 10, 11):
        do.append("Push visible work: pitches, leadership tasks, outreach.")
    if h in (6,):
        do.append("Clear backlog and resolve pending issues.")
    if h in (8, 12):
        avoid.append("Large spending and risky commitments.")
    pc = fc["panchang"]
    avoid.append(f"Rahu Kalam {ac.jd_to_local(pc['rahu_kalam'][0], tz).strftime('%H:%M')}–"
                 f"{ac.jd_to_local(pc['rahu_kalam'][1], tz).strftime('%H:%M')} for anything important.")
    good_horas = [x for x in fc["horas"] if x["day"] and x["lord"] in ("Mercury", "Jupiter", "Venus", "Moon")
                  and ac.functional_nature(ch, x["lord"]).startswith(("Benefic", "Yogakaraka", "Neutral"))]
    dp, chain = dasha_points(ch, md_list, (pc["sunrise"] + pc["sunset"]) / 2)
    return dict(forecast=fc, headline=head, areas=dict(Work=work, Money=money, Relationships=rel, Health=health),
                do=do, avoid=avoid, good_horas=good_horas, chain=chain)


def predict_range(ch: ac.Chart, md_list: list, d0: date, ndays: int, tz: str) -> dict:
    days = [quick_day(ch, d0 + timedelta(days=k), tz) for k in range(ndays)]
    j0 = ac.to_jd(datetime(d0.year, d0.month, d0.day), tz)
    j1 = j0 + ndays
    pr = period_rating(ch, md_list, days, (j0 + j1) / 2)
    ev = [e for e in ac.key_events(ch, j0, ndays / 30.44 + 0.01, md_list) if e["jd"] < j1]
    ev += ingress_events(ch, j0, j1)
    ev.sort(key=lambda e: e["jd"])
    trans = slow_transits(ch, j0, j1, ("Jupiter", "Saturn", "Rahu", "Ketu", "Mars", "Sun"))
    areas = area_outlook(ch, [t for t in trans if t["planet"] in ("Jupiter", "Saturn", "Rahu", "Ketu")],
                         pr["chain"])
    ranked = sorted(days, key=lambda x: x["score"], reverse=True)
    return dict(days=days, rating=pr, events=ev, transits=trans, areas=areas,
                best=ranked[: max(1, min(5, ndays // 6 + 1))],
                worst=sorted(days, key=lambda x: x["score"])[: max(1, min(5, ndays // 6 + 1))])


def predict_year(ch: ac.Chart, md_list: list, d0: date, tz: str) -> dict:
    months = []
    cur = date(d0.year, d0.month, 1)
    for _ in range(12):
        nxt = date(cur.year + (cur.month // 12), cur.month % 12 + 1, 1)
        days = [quick_day(ch, cur + timedelta(days=k), tz) for k in range((nxt - cur).days)]
        j_mid = ac.to_jd(datetime(cur.year, cur.month, 15, 12), tz)
        pr = period_rating(ch, md_list, days, j_mid)
        chain = pr["chain"]
        good = sum(1 for x in days if x["score"] >= 65)
        hard = sum(1 for x in days if x["score"] < 40)
        months.append(dict(month=cur, rating=pr["rating"], daily_avg=pr["daily_avg"], transit=pr["transit"],
                           dasha=" – ".join(p.lord for p in chain[:2]), notes=pr["notes"],
                           good_days=good, hard_days=hard,
                           best_days=[x["date"] for x in sorted(days, key=lambda x: -x["score"])[:3]]))
        cur = nxt
    j0 = ac.to_jd(datetime(d0.year, d0.month, 1), tz)
    j1 = ac.to_jd(datetime(cur.year, cur.month, 1), tz)
    trans = slow_transits(ch, j0, j1)
    weight = Counter()
    for t in trans:
        weight[(t["planet"], t["house"])] += t["end"] - t["start"]
    main_tr = [t for t in trans if weight[(t["planet"], t["house"])] >= 60]
    chain_mid = ac.current_chain(md_list, (j0 + j1) / 2)
    areas = area_outlook(ch, main_tr, chain_mid)
    ev = [e for e in ac.key_events(ch, j0, 12, md_list)
          if e["category"] in ("Sign change", "Eclipse", "Dasha change", "Transit over natal point")
          or (e["category"] == "Retrograde / direct" and any(p in e["event"] for p in ("Jupiter", "Saturn")))]
    dashas = []
    for md in md_list:
        for ad in md.children:
            if ad.end > j0 and ad.start < j1:
                dashas.append(dict(period=f"{md.lord} – {ad.lord}", start=ad.start, end=ad.end,
                                   meaning=ac.dasha_interpretation(ch, ad.lord)))
    ranked = sorted(months, key=lambda m: -m["rating"])
    return dict(months=months, transits=trans, areas=areas, events=ev, dashas=dashas,
                best=ranked[:3], worst=ranked[-3:][::-1],
                rating=round(sum(m["rating"] for m in months) / len(months)))
