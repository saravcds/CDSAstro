"""
Varshaphal (Tajika annual chart): solar return, Muntha, Panchadhikari, year lord and Mudda dasha,
with a plain-language reading. Checked against AstroSage's Varshphal pages.
"""
from __future__ import annotations

from datetime import datetime

import swisseph as swe

import astro_core as ac
import shadbala as sb

TRIRASHI = {0: ("Sun", "Jupiter"), 1: ("Venus", "Moon"), 2: ("Saturn", "Mercury"), 3: ("Venus", "Mars"),
            4: ("Jupiter", "Sun"), 5: ("Moon", "Venus"), 6: ("Mercury", "Saturn"), 7: ("Mars", "Venus"),
            8: ("Saturn", "Saturn"), 9: ("Mars", "Jupiter"), 10: ("Jupiter", "Moon"), 11: ("Moon", "Mars")}
HOUSE_PLAIN = {1: "health, confidence and personal growth", 2: "money, savings and family",
               3: "effort, courage, short trips and siblings", 4: "home, property, vehicles and peace of mind",
               5: "children, studies, ideas and investments", 6: "health, debts, competition and daily work",
               7: "marriage, partners and business deals", 8: "sudden changes, hidden matters and others' money",
               9: "luck, father, mentors and long travel", 10: "career, status and recognition",
               11: "income, gains, friends and wishes", 12: "expenses, foreign links, rest and spirituality"}
MUNTHA_TXT = {
    1: "A year of personal progress. Confidence and health improve, and new beginnings succeed.",
    2: "A good year for money and family. Savings grow and family support is strong.",
    3: "Your efforts pay off this year. Courage, short trips and help from siblings or colleagues bring results.",
    4: "Home and property matters take attention. Keep peace at home and check property papers carefully.",
    5: "A creative and happy year. Good for children, studies, new ideas and sensible investments.",
    6: "A year of hard work and competition. Look after your health, avoid new debts and handle disputes calmly.",
    7: "Partnerships and marriage are in focus. Be patient with your partner and read contracts closely.",
    8: "A year that needs care. Avoid risky decisions, guard your health and money, and keep away from bad company.",
    9: "A lucky year. Support from elders and mentors, spiritual growth and fruitful long-distance travel.",
    10: "A strong year for career and status. Recognition, promotions or business growth are likely.",
    11: "One of the best years for income and gains. Wishes are fulfilled and your network helps you.",
    12: "Expenses rise this year. Plan your budget, rest well, and use the year for foreign links or spiritual work.",
}
GOOD_HOUSES = {"benefic": {1, 2, 3, 4, 5, 7, 9, 10, 11}, "malefic": {3, 6, 10, 11}}
NATURAL_BENEFIC = {"Jupiter", "Venus", "Mercury", "Moon"}


def _sun_lon(jd: float, ayan: str) -> float:
    return ac.sidereal_lon(jd, "Sun", ayan)[0]


def solar_return(ch: ac.Chart, year: int) -> float:
    """JD (UT) when the sidereal Sun returns to its natal longitude in the given year."""
    target = ch.planets["Sun"]["lon"]
    b = ch.dt_local
    jd = swe.julday(year, b.month, min(b.day, 28), 12.0)
    for _ in range(30):
        diff = ((target - _sun_lon(jd, ch.ayanamsa) + 180) % 360) - 180
        if abs(diff) < 1e-7:
            break
        jd += diff / 0.9856
    return jd


def _chart_at(ch: ac.Chart, jd: float, lat: float, lon: float, tz: str, place: str) -> ac.Chart:
    loc = ac.jd_to_local(jd, tz).replace(tzinfo=None)
    return ac.compute_chart(f"{ch.name} {loc.year}", loc, tz, lat, lon, place, ch.ayanamsa, ch.node)


def _aspects_lagna(ann: ac.Chart, p: str) -> bool:
    return ac._house_from(ann.planets[p]["sign"], ann.asc_sign) not in (2, 6, 8, 12)


def mudda_dasha(ch: ac.Chart, years: int, start: float, end: float) -> list[dict]:
    first = (ch.moon_nak + 1 + years) % 9  # 1 = Ketu, 2 = Venus, ...
    i0 = (first - 1) % 9
    length = end - start
    out, t = [], start
    for k in range(9):
        lord = ac.DASHA_ORDER[(i0 + k) % 9]
        dur = length * ac.DASHA_YEARS[lord] / 120
        out.append(dict(lord=lord, start=t, end=t + dur))
        t += dur
    return out


def varshaphal(ch: ac.Chart, year: int, lat: float | None = None, lon: float | None = None,
               tz: str | None = None, place: str | None = None) -> dict:
    lat = ch.lat if lat is None else lat
    lon = ch.lon if lon is None else lon
    tz = tz or ch.tz
    place = place or ch.place
    j0, j1 = solar_return(ch, year), solar_return(ch, year + 1)
    ann = _chart_at(ch, j0, lat, lon, tz, place)
    n = year - ch.dt_local.year
    muntha = (ch.asc_sign + n) % 12
    m_house = ann.house_of_sign(muntha)
    rise, sset, _ = ac.sun_times(ac.jd_to_local(j0, tz).date(), lat, lon, tz)
    day = rise <= j0 < sset
    tri = TRIRASHI[ann.asc_sign][0 if day else 1]
    dinratri = ac.SIGN_LORD[ann.planets["Sun" if day else "Moon"]["sign"]]
    office = {"Muntha lord": ac.SIGN_LORD[muntha], "Birth ascendant lord": ch.lord_of_house(1),
              "Year ascendant lord": ann.lord_of_house(1), "Tri-rashi lord": tri, "Day/night lord": dinratri}
    sbv = sb.shadbala(ann)["planets"]
    cands = list(dict.fromkeys(office.values()))
    aspecting = [p for p in cands if _aspects_lagna(ann, p)] or cands
    year_lord = max(aspecting, key=lambda p: sbv[p]["ratio"])
    md = mudda_dasha(ch, n, j0, j1)
    return dict(year=year, start=j0, end=j1, chart=ann, years_completed=n, muntha_sign=muntha,
                muntha_house=m_house, muntha_natal_house=ch.house_of_sign(muntha), day_birth=day,
                office=office, year_lord=year_lord, mudda=md, shadbala=sbv)


def _period_text(ann: ac.Chart, p: str) -> tuple[str, str]:
    h = ann.planets[p]["house"]
    nature = "benefic" if p in NATURAL_BENEFIC else "malefic"
    good = h in GOOD_HOUSES[nature]
    dig = ann.planets[p]["dignity"]
    if dig in ("Exalted", "Own sign"):
        good = True
    if dig == "Debilitated":
        good = False
    theme = HOUSE_PLAIN[h]
    if good:
        txt = f"A helpful period for {theme}. Plans in this area move forward and support comes easily."
    else:
        txt = f"Go carefully with {theme}. Expect some delays or pressure; patience and planning help."
    return txt, "good" if good else "care"


def plain_reading(v: dict) -> dict:
    ann, tz = v["chart"], v["chart"].tz
    mh = v["muntha_house"]
    ml = v["office"]["Muntha lord"]
    ml_ok = ann.planets[ml]["house"] not in (6, 8, 12)
    yl = v["year_lord"]
    yl_ratio = v["shadbala"][yl]["ratio"]
    good_m = mh in (1, 2, 3, 5, 9, 10, 11)
    score = 50 + (12 if good_m else -12) + (6 if ml_ok else -6) + (8 if yl_ratio >= 1.1 else -6 if yl_ratio < 0.9 else 0)
    asc = ann.asc_sign
    summary = [
        f"Your new year begins on {ac.jd_to_local(v['start'], tz).strftime('%d %b %Y at %I:%M %p')}, "
        f"when the Sun returns to its birth position.",
        f"Year focus (Muntha in house {mh}): {MUNTHA_TXT[mh]}",
        f"Ruling planet of the year: {yl}. "
        + ("It is strong in this year's chart, so the year has good support." if yl_ratio >= 1.1 else
           "It is weak in this year's chart, so results need more effort." if yl_ratio < 0.9 else
           "It is of average strength, so steady effort brings steady results."),
        f"The year's rising sign is {ac.SIGNS[asc]}. Mood of the year: " + ac.LAGNA_TRAITS[asc][0].lower() + ac.LAGNA_TRAITS[asc][1:],
    ]
    periods = []
    for m in v["mudda"]:
        txt, tone = _period_text(ann, m["lord"])
        periods.append(dict(lord=m["lord"], start=m["start"], end=m["end"], text=txt, tone=tone))
    return dict(score=max(10, min(90, score)), summary=summary, periods=periods)
