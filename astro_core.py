"""
Core Vedic astrology calculations built on the Swiss Ephemeris.

Systems covered
- Parashari: sidereal chart, whole-sign houses, dignities, aspects, vargas,
  Vimshottari dasha, yogas, functional nature, gochara (transits)
- KP (Krishnamurti): Placidus cusps, star lord / sub lord / sub-sub lord
- Jaimini: 7 chara karakas
- Yogini dasha
- Panchang, Tara Bala, Chandra Bala, Rahu Kalam etc., planetary hours (hora)
- Muhurta search
- Compatibility: Ashtakoota (36 points), Manglik check, professional synastry

All positions use the built-in Moshier ephemeris of the Swiss Ephemeris
(no data files needed; accuracy is well under 1 arc-second for planets,
which is far finer than any astrological rule needs).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import swisseph as swe

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
EPH = swe.FLG_MOSEPH
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_SHORT = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag",
              "Cap", "Aqu", "Pis"]
SIGN_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus",
             "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
              "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
              "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
              "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]
NAK = 360.0 / 27.0
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
               "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu"]
ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra",
        "Ketu": "Ke", "Asc": "Asc"}
SWE_ID = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
          "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
          "Saturn": swe.SATURN}
AYANAMSAS = {
    "Lahiri (Chitrapaksha)": swe.SIDM_LAHIRI,
    "KP (Krishnamurti)": swe.SIDM_KRISHNAMURTI,
    "Raman": swe.SIDM_RAMAN,
    "Yukteshwar": swe.SIDM_YUKTESHWAR,
    "True Chitra": swe.SIDM_TRUE_CITRA,
}

EXALT_SIGN = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
              "Venus": 11, "Saturn": 6, "Rahu": 1, "Ketu": 7}
OWN_SIGNS = {"Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
             "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10]}
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"}, "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"}, "Moon": set(), "Mars": {"Mercury"},
    "Mercury": {"Moon"}, "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"}, "Saturn": {"Sun", "Moon", "Mars"},
}
COMBUST_ORB = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11,
               "Venus": 10, "Saturn": 15}
SPECIAL_ASPECTS = {"Mars": [4, 8], "Jupiter": [5, 9], "Saturn": [3, 10],
                   "Rahu": [5, 9], "Ketu": [5, 9]}

HOUSE_THEMES = {
    1: "self, health and confidence",
    2: "money, family and speech",
    3: "effort, courage, communication and short travel",
    4: "home, mother, property and peace of mind",
    5: "intelligence, children, investments and romance",
    6: "work pressure, competition, debts and health issues",
    7: "spouse, partners, clients and contracts",
    8: "sudden events, other people's money and hidden matters",
    9: "fortune, father, mentors and long-distance matters",
    10: "career, status and authority",
    11: "income, gains, networks and wishes",
    12: "expenses, foreign matters, rest and losses",
}
PLANET_KEYWORDS = {
    "Sun": "authority, ego, government and vitality",
    "Moon": "mind, emotions, public and comfort",
    "Mars": "energy, courage, property, disputes and drive",
    "Mercury": "intellect, business, communication and analysis",
    "Jupiter": "wisdom, growth, wealth, children and protection",
    "Venus": "relationships, comfort, luxury and the arts",
    "Saturn": "discipline, delay, hard work and longevity",
    "Rahu": "ambition, obsession, foreign and unconventional matters",
    "Ketu": "detachment, spirituality, sudden breaks and insight",
}
LAGNA_TRAITS = {
    0: "Direct, energetic, competitive; starts things fast, needs patience.",
    1: "Steady, practical, comfort-loving; loyal but can be stubborn.",
    2: "Quick, talkative, adaptable; many interests, needs focus.",
    3: "Caring, protective, intuitive; mood-sensitive, family-centred.",
    4: "Confident, proud, generous; natural leader, wants recognition.",
    5: "Analytical, precise, service-minded; can over-worry.",
    6: "Diplomatic, fair, sociable; seeks balance, can be indecisive.",
    7: "Intense, private, determined; deep insight, can hold grudges.",
    8: "Optimistic, principled, independent; loves learning and freedom.",
    9: "Ambitious, disciplined, patient; builds slowly and surely.",
    10: "Original, humanitarian, systems-minded; values independence.",
    11: "Compassionate, imaginative, spiritual; absorbs others' feelings.",
}

GOOD_FROM_MOON = {"Sun": {3, 6, 10, 11}, "Moon": {1, 3, 6, 7, 10, 11},
                  "Mars": {3, 6, 11}, "Mercury": {2, 4, 6, 8, 10, 11},
                  "Jupiter": {2, 5, 7, 9, 11},
                  "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
                  "Saturn": {3, 6, 11}, "Rahu": {3, 6, 11}, "Ketu": {3, 6, 11}}

TARAS = [("Janma", "mixed"), ("Sampat", "good"), ("Vipat", "bad"),
         ("Kshema", "good"), ("Pratyak", "bad"), ("Sadhana", "good"),
         ("Naidhana", "bad"), ("Mitra", "good"), ("Parama Mitra", "good")]
TARA_MEANING = {"Janma": "birth star - mixed, take care",
                "Sampat": "wealth", "Vipat": "obstacle",
                "Kshema": "well-being", "Pratyak": "opposition",
                "Sadhana": "achievement", "Naidhana": "danger - least favourable",
                "Mitra": "friend", "Parama Mitra": "best friend"}

TITHI_NAMES = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
               "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGA_NAMES = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
              "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
              "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
              "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
              "Shukla", "Brahma", "Indra", "Vaidhriti"]
BAD_YOGAS = {"Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra",
             "Vyatipata", "Parigha", "Vaidhriti"}
KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija",
                  "Vishti (Bhadra)"]
WEEKDAY_LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
HORA_SEQ = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
HORA_GOOD_FOR = {
    "Sun": "authority, government, meeting seniors",
    "Moon": "public dealings, travel, family, emotional talks",
    "Mars": "property, sport, bold action; avoid arguments",
    "Mercury": "business, contracts, writing, calls, trading",
    "Jupiter": "finance, advice, learning, prayer, auspicious starts",
    "Venus": "relationships, arts, shopping, luxury, celebrations",
    "Saturn": "routine work, labour, old matters; avoid new starts",
}
# Day divided into 8 parts (1-based) by weekday: Mon..Sun
RAHU_PART = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA_PART = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULIKA_PART = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
RIKTA_TITHIS = {4, 9, 14, 19, 24, 29}

# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def set_ayanamsa(name: str) -> None:
    swe.set_sid_mode(AYANAMSAS[name], 0, 0)


def to_jd(local_dt: datetime, tz: str) -> float:
    aware = local_dt.replace(tzinfo=ZoneInfo(tz))
    u = aware.astimezone(ZoneInfo("UTC"))
    return swe.julday(u.year, u.month, u.day,
                      u.hour + u.minute / 60 + u.second / 3600)


def jd_to_local(jd: float, tz: str) -> datetime:
    y, m, d, h = swe.revjul(jd)
    base = datetime(y, m, d, tzinfo=ZoneInfo("UTC")) + timedelta(hours=h)
    return base.astimezone(ZoneInfo(tz))


def sign_of(lon: float) -> int:
    return int(lon // 30) % 12


def nak_of(lon: float) -> int:
    return int(lon // NAK) % 27


def pada_of(lon: float) -> int:
    return int((lon % NAK) // (NAK / 4)) + 1


def fmt_deg(lon: float) -> str:
    d = lon % 30
    deg = int(d)
    minutes = int(round((d - deg) * 60))
    if minutes == 60:
        deg, minutes = deg + 1, 0
    return f"{deg:02d}°{minutes:02d}'"


def angdist(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def relationship(a: str, b: str) -> str:
    if a == b:
        return "same"
    if b in FRIENDS.get(a, set()):
        return "friend"
    if b in ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"


def dignity(planet: str, sign: int) -> str:
    if planet in EXALT_SIGN and sign == EXALT_SIGN[planet]:
        return "Exalted"
    if planet in EXALT_SIGN and sign == (EXALT_SIGN[planet] + 6) % 12:
        return "Debilitated"
    if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
        return "Own sign"
    if planet in ("Rahu", "Ketu"):
        return "-"
    rel = relationship(planet, SIGN_LORD[sign])
    return {"friend": "Friendly sign", "enemy": "Enemy sign",
            "neutral": "Neutral sign", "same": "Own sign"}[rel]


def kp_lords(lon: float) -> tuple[str, str, str, str]:
    """Sign lord, star lord, sub lord, sub-sub lord (KP)."""
    n = nak_of(lon)
    star = DASHA_ORDER[n % 9]
    pos = lon % 360 - n * NAK
    i0 = DASHA_ORDER.index(star)
    acc = 0.0
    for k in range(9):
        sub = DASHA_ORDER[(i0 + k) % 9]
        span = NAK * DASHA_YEARS[sub] / 120
        if pos < acc + span or k == 8:
            pos2, acc2 = pos - acc, 0.0
            j0 = DASHA_ORDER.index(sub)
            for q in range(9):
                ss = DASHA_ORDER[(j0 + q) % 9]
                span2 = span * DASHA_YEARS[ss] / 120
                if pos2 < acc2 + span2 or q == 8:
                    return SIGN_LORD[sign_of(lon)], star, sub, ss
                acc2 += span2
        acc += span
    return SIGN_LORD[sign_of(lon)], star, star, star


def tara_of(birth_nak: int, day_nak: int) -> tuple[str, str]:
    idx = ((day_nak - birth_nak) % 27) % 9
    return TARAS[idx]


def sidereal_lon(jd: float, planet: str, ayanamsa: str, node: str = "True"):
    """Return (longitude, speed) of a planet, Rahu or Ketu."""
    set_ayanamsa(ayanamsa)
    fl = EPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    if planet in ("Rahu", "Ketu"):
        nid = swe.TRUE_NODE if node == "True" else swe.MEAN_NODE
        x = swe.calc_ut(jd, nid, fl)[0]
        lon = x[0] % 360 if planet == "Rahu" else (x[0] + 180) % 360
        return lon, x[3]
    x = swe.calc_ut(jd, SWE_ID[planet], fl)[0]
    return x[0] % 360, x[3]


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------

@dataclass
class Chart:
    name: str
    dt_local: datetime
    tz: str
    lat: float
    lon: float
    place: str
    ayanamsa: str
    node: str
    jd: float = 0.0
    ayan_value: float = 0.0
    asc: float = 0.0
    mc: float = 0.0
    cusps: list = field(default_factory=list)
    planets: dict = field(default_factory=dict)

    @property
    def asc_sign(self) -> int:
        return sign_of(self.asc)

    @property
    def moon_sign(self) -> int:
        return self.planets["Moon"]["sign"]

    @property
    def moon_nak(self) -> int:
        return self.planets["Moon"]["nak"]

    def house_of_sign(self, sign: int) -> int:
        return (sign - self.asc_sign) % 12 + 1

    def lord_of_house(self, h: int) -> str:
        return SIGN_LORD[(self.asc_sign + h - 1) % 12]

    def houses_owned(self, planet: str) -> list[int]:
        return [h for h in range(1, 13) if self.lord_of_house(h) == planet]

    def kp_house(self, lon: float) -> int:
        c = self.cusps
        for i in range(12):
            a, b = c[i], c[(i + 1) % 12]
            span = (b - a) % 360
            if (lon - a) % 360 < span:
                return i + 1
        return 1


def compute_chart(name: str, dt_local: datetime, tz: str, lat: float,
                  lon: float, place: str = "",
                  ayanamsa: str = "Lahiri (Chitrapaksha)",
                  node: str = "True") -> Chart:
    jd = to_jd(dt_local, tz)
    set_ayanamsa(ayanamsa)
    ch = Chart(name, dt_local, tz, lat, lon, place, ayanamsa, node, jd=jd)
    ch.ayan_value = swe.get_ayanamsa_ut(jd)
    fl = swe.FLG_SIDEREAL | EPH
    try:
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", fl)
    except Exception:  # Placidus fails near the poles
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"O", fl)
    ch.asc, ch.mc = ascmc[0] % 360, ascmc[1] % 360
    ch.cusps = [c % 360 for c in cusps[:12]]

    raw = {p: sidereal_lon(jd, p, ayanamsa, node) for p in PLANETS}
    sun_lon = raw["Sun"][0]
    for p, (plon, speed) in raw.items():
        s = sign_of(plon)
        retro = speed < 0 if p not in ("Rahu", "Ketu") else True
        combust = False
        if p in COMBUST_ORB:
            orb = COMBUST_ORB[p]
            if p == "Mercury" and speed < 0:
                orb = 12
            if p == "Venus" and speed < 0:
                orb = 8
            combust = angdist(plon, sun_lon) <= orb
        sl, star, sub, ss = kp_lords(plon)
        ch.planets[p] = dict(
            lon=plon, speed=speed, retro=retro and p not in ("Rahu", "Ketu"),
            sign=s, deg=plon % 30, nak=nak_of(plon), pada=pada_of(plon),
            sign_lord=sl, star_lord=star, sub_lord=sub, subsub_lord=ss,
            house=(s - sign_of(ch.asc)) % 12 + 1,
            dignity=dignity(p, s), combust=combust,
        )
    ch.planets["Rahu"]["kp_house"] = ch.kp_house(ch.planets["Rahu"]["lon"])
    for p in PLANETS:
        ch.planets[p]["kp_house"] = ch.kp_house(ch.planets[p]["lon"])
    return ch


def aspected_houses(planet: str, house: int) -> list[int]:
    offs = [7] + SPECIAL_ASPECTS.get(planet, [])
    return sorted({(house - 1 + o - 1) % 12 + 1 for o in offs})


def functional_nature(ch: Chart, planet: str) -> str:
    if planet in ("Rahu", "Ketu"):
        return "Shadow (acts like its sign lord)"
    owned = set(ch.houses_owned(planet))
    if owned & {4, 7, 10} and owned & {5, 9}:
        return "Yogakaraka (best benefic)"
    if owned & {1, 5, 9}:
        return "Benefic"
    if owned & {3, 6, 8, 11, 12}:
        return "Malefic"
    return "Neutral"


# ---------------------------------------------------------------------------
# Divisional charts
# ---------------------------------------------------------------------------
VARGAS = {1: "D1 Rasi (overall life)", 2: "D2 Hora (wealth)",
          3: "D3 Drekkana (siblings, courage)", 4: "D4 Chaturthamsa (property)",
          7: "D7 Saptamsa (children)", 9: "D9 Navamsa (marriage, inner strength)",
          10: "D10 Dasamsa (career)", 12: "D12 Dwadasamsa (parents)"}


def varga_sign(lon: float, d: int) -> int:
    s, deg = sign_of(lon), lon % 30
    odd = s % 2 == 0  # Aries, Gemini, ... are odd signs
    if d == 1:
        return s
    if d == 2:
        first = deg < 15
        if odd:
            return 4 if first else 3
        return 3 if first else 4
    if d == 3:
        return (s + [0, 4, 8][min(int(deg // 10), 2)]) % 12
    if d == 4:
        return (s + [0, 3, 6, 9][min(int(deg // 7.5), 3)]) % 12
    if d == 7:
        part = min(int(deg // (30 / 7)), 6)
        return (s + part) % 12 if odd else (s + 6 + part) % 12
    if d == 9:
        return int((lon % 360) // (10 / 3)) % 12
    if d == 10:
        part = min(int(deg // 3), 9)
        return (s + part) % 12 if odd else (s + 8 + part) % 12
    if d == 12:
        return (s + min(int(deg // 2.5), 11)) % 12
    raise ValueError(d)


def varga_chart(ch: Chart, d: int) -> dict:
    out = {"Asc": varga_sign(ch.asc, d)}
    for p in PLANETS:
        out[p] = varga_sign(ch.planets[p]["lon"], d)
    return out


# ---------------------------------------------------------------------------
# Dashas
# ---------------------------------------------------------------------------

@dataclass
class Period:
    lord: str
    start: float
    end: float
    level: int
    children: list = field(default_factory=list)


def _subdivide(p: Period, depth: int, order: list, years: dict, total: float):
    if depth <= 0:
        return
    i0 = order.index(p.lord)
    s = p.start
    length = p.end - p.start
    for k in range(len(order)):
        lord = order[(i0 + k) % len(order)]
        dur = length * years[lord] / total
        child = Period(lord, s, s + dur, p.level + 1)
        _subdivide(child, depth - 1, order, years, total)
        p.children.append(child)
        s += dur


def vimshottari(ch: Chart, year_days: float = 365.25, depth: int = 3,
                cycles: int = 1) -> list[Period]:
    moon = ch.planets["Moon"]["lon"]
    n = nak_of(moon)
    frac = (moon % NAK) / NAK
    first = DASHA_ORDER[n % 9]
    s = ch.jd - DASHA_YEARS[first] * frac * year_days
    i0 = DASHA_ORDER.index(first)
    out = []
    for k in range(9 * cycles):
        lord = DASHA_ORDER[(i0 + k) % 9]
        e = s + DASHA_YEARS[lord] * year_days
        md = Period(lord, s, e, 1)
        _subdivide(md, depth - 1, DASHA_ORDER, DASHA_YEARS, 120)
        out.append(md)
        s = e
    return out


YOGINIS = [("Mangala", "Moon", 1), ("Pingala", "Sun", 2),
           ("Dhanya", "Jupiter", 3), ("Bhramari", "Mars", 4),
           ("Bhadrika", "Mercury", 5), ("Ulka", "Saturn", 6),
           ("Siddha", "Venus", 7), ("Sankata", "Rahu", 8)]


def yogini_dasha(ch: Chart, year_days: float = 365.25, cycles: int = 3):
    moon = ch.planets["Moon"]["lon"]
    n = nak_of(moon) + 1
    r = (n + 3) % 8
    r = 8 if r == 0 else r
    idx0 = r - 1
    frac = (moon % NAK) / NAK
    names = [y[0] for y in YOGINIS]
    yrs = {y[0]: y[2] for y in YOGINIS}
    s = ch.jd - yrs[names[idx0]] * frac * year_days
    out = []
    for k in range(8 * cycles):
        nm = names[(idx0 + k) % 8]
        e = s + yrs[nm] * year_days
        p = Period(nm, s, e, 1)
        _subdivide(p, 1, names, yrs, 36)
        out.append(p)
        s = e
    return out


YOGINI_LORD = {y[0]: y[1] for y in YOGINIS}


def current_chain(periods: list[Period], jd: float) -> list[Period]:
    chain = []
    level = periods
    while level:
        hit = next((p for p in level if p.start <= jd < p.end), None)
        if not hit:
            break
        chain.append(hit)
        level = hit.children
    return chain


def dasha_interpretation(ch: Chart, lord: str) -> str:
    if lord in ("Rahu", "Ketu"):
        p = ch.planets[lord]
        disp = SIGN_LORD[p["sign"]]
        return (f"{lord} sits in house {p['house']} ({SIGNS[p['sign']]}) and acts "
                f"like its sign lord {disp}. Themes: {HOUSE_THEMES[p['house']]}; "
                f"{PLANET_KEYWORDS[lord]}.")
    p = ch.planets[lord]
    owned = ch.houses_owned(lord)
    owned_txt = "; ".join(f"house {h} ({HOUSE_THEMES[h]})" for h in owned)
    extra = []
    if p["dignity"] in ("Exalted", "Own sign"):
        extra.append(f"{lord} is strong ({p['dignity'].lower()}), so results tend to be good.")
    if p["dignity"] == "Debilitated":
        extra.append(f"{lord} is debilitated; results come after effort (check Neecha Bhanga).")
    if p["combust"]:
        extra.append(f"{lord} is combust; its results can be overshadowed.")
    return (f"{lord} rules {owned_txt}, and sits in house {p['house']} "
            f"({HOUSE_THEMES[p['house']]}). Functional nature: "
            f"{functional_nature(ch, lord)}. " + " ".join(extra))


# ---------------------------------------------------------------------------
# Jaimini, yogas
# ---------------------------------------------------------------------------
KARAKA_NAMES = ["Atmakaraka (self, soul)", "Amatyakaraka (career, advisers)",
                "Bhratrikaraka (siblings, courage)", "Matrikaraka (mother, home)",
                "Putrakaraka (children, creativity)", "Gnatikaraka (rivals, health)",
                "Darakaraka (spouse, partners)"]


def chara_karakas(ch: Chart) -> list[tuple[str, str, float]]:
    items = sorted(((ch.planets[p]["deg"], p) for p in PLANETS[:7]),
                   reverse=True)
    return [(KARAKA_NAMES[i], p, d) for i, (d, p) in enumerate(items)]


def _house_from(a_sign: int, b_sign: int) -> int:
    return (b_sign - a_sign) % 12 + 1


def detect_yogas(ch: Chart) -> list[dict]:
    P = ch.planets
    res = []
    moon_s = P["Moon"]["sign"]
    kendra = {1, 4, 7, 10}

    jh = _house_from(moon_s, P["Jupiter"]["sign"])
    res.append(dict(name="Gaja Kesari", present=jh in kendra,
                    detail=f"Jupiter is house {jh} from the Moon.",
                    meaning="Respect, wisdom and protection; rises after effort."))

    res.append(dict(name="Budha-Aditya", present=P["Sun"]["sign"] == P["Mercury"]["sign"],
                    detail=f"Sun in {SIGNS[P['Sun']['sign']]}, Mercury in {SIGNS[P['Mercury']['sign']]}.",
                    meaning="Sharp intellect and good communication (weaker if Mercury is deeply combust)."))

    mm = _house_from(moon_s, P["Mars"]["sign"])
    res.append(dict(name="Chandra-Mangala", present=mm in (1, 7),
                    detail=f"Mars is house {mm} from the Moon.",
                    meaning="Drive to earn; can bring emotional heat."))

    mahapurusha = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa",
                   "Venus": "Malavya", "Saturn": "Sasa"}
    for pl, yname in mahapurusha.items():
        ok = P[pl]["house"] in kendra and P[pl]["dignity"] in ("Exalted", "Own sign")
        res.append(dict(name=f"{yname} (Pancha Mahapurusha)", present=ok,
                        detail=f"{pl} in house {P[pl]['house']}, {P[pl]['dignity']}.",
                        meaning=f"Strong {pl} qualities: {PLANET_KEYWORDS[pl]}."))

    # Neecha Bhanga
    for pl in PLANETS[:7]:
        if P[pl]["dignity"] != "Debilitated":
            continue
        dsign = P[pl]["sign"]
        reasons = []
        lord = SIGN_LORD[dsign]
        if P[lord]["house"] in kendra:
            reasons.append(f"lord of the debilitation sign ({lord}) is in a kendra from the Ascendant")
        if lord != "Moon" and _house_from(moon_s, P[lord]["sign"]) in kendra:
            reasons.append(f"{lord} is in a kendra from the Moon")
        exalted_here = [q for q, s in EXALT_SIGN.items() if s == dsign and q in SWE_ID]
        for q in exalted_here:
            if P[q]["house"] in kendra or (q != "Moon" and _house_from(moon_s, P[q]["sign"]) in kendra):
                reasons.append(f"{q}, which is exalted in {SIGNS[dsign]}, is in a kendra")
        ex_lord = SIGN_LORD[EXALT_SIGN[pl]]
        if P[ex_lord]["house"] in kendra:
            reasons.append(f"lord of {pl}'s exaltation sign ({ex_lord}) is in a kendra")
        res.append(dict(name=f"Neecha Bhanga for {pl}", present=bool(reasons),
                        detail="; ".join(reasons) or f"{pl} is debilitated without cancellation.",
                        meaning="Debilitation cancelled: struggle first, then rise."))

    # Kemadruma
    others = [p for p in PLANETS if p not in ("Sun", "Moon", "Rahu", "Ketu")]
    near = [p for p in others if _house_from(moon_s, P[p]["sign"]) in (1, 2, 12)]
    if near:
        kd_detail, kd_present = f"Moon supported by {', '.join(near)}.", False
    else:
        cancel = [p for p in others + ["Sun"] if _house_from(moon_s, P[p]["sign"]) in kendra]
        if P["Moon"]["house"] in kendra:
            cancel.append("Moon in a kendra from the Ascendant")
        kd_present = not cancel
        kd_detail = ("No planets beside the Moon, but cancelled by: " + ", ".join(cancel)
                     if cancel else "No planets beside the Moon and no cancellation.")
    res.append(dict(name="Kemadruma", present=kd_present, detail=kd_detail,
                    meaning="Periods of loneliness or financial ups and downs."))

    # Raja and Dhana yogas by conjunction of lords
    kendra_l = {ch.lord_of_house(h) for h in (1, 4, 7, 10)}
    trikona_l = {ch.lord_of_house(h) for h in (1, 5, 9)}
    found = set()
    for a in kendra_l:
        for b in trikona_l:
            if a != b and P[a]["sign"] == P[b]["sign"]:
                found.add(tuple(sorted((a, b))))
    res.append(dict(name="Raja Yoga (kendra + trikona lords together)", present=bool(found),
                    detail=", ".join(f"{a} + {b}" for a, b in found) or "None by conjunction.",
                    meaning="Status, authority and success in the periods of these planets."))
    wealth_l = {ch.lord_of_house(h) for h in (2, 11)}
    found2 = set()
    for a in wealth_l:
        for b in trikona_l:
            if a != b and P[a]["sign"] == P[b]["sign"]:
                found2.add(tuple(sorted((a, b))))
    res.append(dict(name="Dhana Yoga (wealth lords with trikona lords)", present=bool(found2),
                    detail=", ".join(f"{a} + {b}" for a, b in found2) or "None by conjunction.",
                    meaning="Wealth accumulation in the periods of these planets."))
    dust = {6, 8, 12}
    vip = [ch.lord_of_house(h) for h in dust
           if P[ch.lord_of_house(h)]["house"] in dust and ch.lord_of_house(h) != ch.lord_of_house(1)]
    res.append(dict(name="Vipareeta Raja Yoga", present=bool(vip),
                    detail=", ".join(sorted(set(vip))) + " in dusthanas." if vip else "None.",
                    meaning="Success arising out of difficulty or others' losses."))
    return res


# ---------------------------------------------------------------------------
# Transits, Sade Sati, key dates
# ---------------------------------------------------------------------------

def gochara(ch: Chart, jd: float) -> list[dict]:
    rows = []
    for p in PLANETS:
        lon, speed = sidereal_lon(jd, p, ch.ayanamsa, ch.node)
        s = sign_of(lon)
        hm = _house_from(ch.moon_sign, s)
        rows.append(dict(planet=p, sign=SIGNS[s], degree=fmt_deg(lon),
                         nakshatra=NAKSHATRAS[nak_of(lon)],
                         retro=(speed < 0 and p not in ("Rahu", "Ketu")),
                         house_from_asc=ch.house_of_sign(s), house_from_moon=hm,
                         result="Favourable" if hm in GOOD_FROM_MOON[p] else "Challenging"))
    return rows


def _scan_segments(planet: str, ch: Chart, j0: float, j1: float, step: float = 1.0):
    segs = []
    t = j0
    cur = sign_of(sidereal_lon(t, planet, ch.ayanamsa, ch.node)[0])
    start = t
    while t < j1:
        t2 = t + step
        s2 = sign_of(sidereal_lon(t2, planet, ch.ayanamsa, ch.node)[0])
        if s2 != cur:
            lo, hi = t, t2
            for _ in range(20):
                mid = (lo + hi) / 2
                if sign_of(sidereal_lon(mid, planet, ch.ayanamsa, ch.node)[0]) == cur:
                    lo = mid
                else:
                    hi = mid
            segs.append((start, hi, cur))
            cur, start = s2, hi
        t = t2
    segs.append((start, j1, cur))
    return segs


def sade_sati(ch: Chart, years_ahead: int = 90) -> list[dict]:
    j0 = ch.jd
    j1 = ch.jd + years_ahead * 365.25
    segs = _scan_segments("Saturn", ch, j0, j1, step=5)
    labels = {12: "Sade Sati - phase 1 (rising)", 1: "Sade Sati - phase 2 (peak)",
              2: "Sade Sati - phase 3 (setting)", 8: "Ashtama Shani (8th from Moon)",
              4: "Kantaka Shani (4th from Moon)"}
    out = []
    for s, e, sg in segs:
        h = _house_from(ch.moon_sign, sg)
        if h in labels:
            out.append(dict(start=s, end=e, sign=SIGNS[sg], phase=labels[h]))
    return out


def key_events(ch: Chart, j0: float, months: int = 24,
               dashas: list[Period] | None = None) -> list[dict]:
    j1 = j0 + months * 30.44
    ev = []
    for p in ["Jupiter", "Saturn", "Rahu", "Mars"]:
        for s, e, sg in _scan_segments(p, ch, j0, j1, step=1)[1:]:
            ev.append(dict(jd=s, category="Sign change",
                           event=f"{p} enters {SIGNS[sg]} - house {ch.house_of_sign(sg)} from Ascendant, "
                                 f"{_house_from(ch.moon_sign, sg)} from Moon "
                                 f"({HOUSE_THEMES[ch.house_of_sign(sg)]})"))
            if p == "Rahu":
                ks = (sg + 6) % 12
                ev.append(dict(jd=s, category="Sign change",
                               event=f"Ketu enters {SIGNS[ks]} - house {ch.house_of_sign(ks)} from Ascendant"))
    for p in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        t, prev = j0, sidereal_lon(j0, p, ch.ayanamsa)[1] < 0
        while t < j1:
            t += 1
            lon, sp = sidereal_lon(t, p, ch.ayanamsa)
            r = sp < 0
            if r != prev:
                ev.append(dict(jd=t, category="Retrograde / direct",
                               event=f"{p} turns {'retrograde' if r else 'direct'} in {SIGNS[sign_of(lon)]} "
                                     f"(house {ch.house_of_sign(sign_of(lon))})"))
            prev = r
    natal_pts = {"Ascendant": ch.asc, "natal Sun": ch.planets["Sun"]["lon"],
                 "natal Moon": ch.planets["Moon"]["lon"]}
    ll = ch.lord_of_house(1)
    natal_pts[f"natal {ll} (Ascendant lord)"] = ch.planets[ll]["lon"]
    tl = ch.lord_of_house(10)
    natal_pts[f"natal {tl} (10th lord)"] = ch.planets[tl]["lon"]
    for p in ["Jupiter", "Saturn", "Rahu"]:
        for label, nl in natal_pts.items():
            t = j0
            prev = (sidereal_lon(t, p, ch.ayanamsa, ch.node)[0] - nl + 180) % 360 - 180
            while t < j1:
                t += 1
                d = (sidereal_lon(t, p, ch.ayanamsa, ch.node)[0] - nl + 180) % 360 - 180
                if abs(d) < 10 and (d == 0 or (d > 0) != (prev > 0)):
                    ev.append(dict(jd=t, category="Transit over natal point",
                                   event=f"Transit {p} exactly over {label}"))
                prev = d
    # eclipses
    t = j0
    while True:
        r = swe.sol_eclipse_when_glob(t, EPH)[1][0]
        if r > j1:
            break
        lon = sidereal_lon(r, "Sun", ch.ayanamsa)[0]
        ev.append(_eclipse_event(ch, r, lon, "Solar"))
        t = r + 20
    t = j0
    while True:
        r = swe.lun_eclipse_when(t, EPH)[1][0]
        if r > j1:
            break
        lon = sidereal_lon(r, "Moon", ch.ayanamsa)[0]
        ev.append(_eclipse_event(ch, r, lon, "Lunar"))
        t = r + 20
    if dashas:
        for md in dashas:
            for ad in md.children:
                if j0 <= ad.start <= j1:
                    ev.append(dict(jd=ad.start, category="Dasha change",
                                   event=f"Antardasha {md.lord}-{ad.lord} begins"))
                for pd in ad.children:
                    if j0 <= pd.start <= j1:
                        ev.append(dict(jd=pd.start, category="Dasha change (sub-sub)",
                                       event=f"Pratyantar {md.lord}-{ad.lord}-{pd.lord} begins"))
    ev.sort(key=lambda x: x["jd"])
    return ev


def _eclipse_event(ch: Chart, jd: float, lon: float, kind: str) -> dict:
    hits = []
    pts = {"Ascendant": ch.asc, **{p: ch.planets[p]["lon"] for p in PLANETS}}
    for name, pl in pts.items():
        if angdist(lon, pl) <= 3 or (kind == "Lunar" and angdist((lon + 180) % 360, pl) <= 3):
            hits.append(name)
    h = ch.house_of_sign(sign_of(lon))
    txt = (f"{kind} eclipse at {SIGNS[sign_of(lon)]} {fmt_deg(lon)} - house {h} "
           f"({HOUSE_THEMES[h]})")
    if hits:
        txt += " - CLOSE TO natal " + ", ".join(hits)
    return dict(jd=jd, category="Eclipse", event=txt)


# ---------------------------------------------------------------------------
# Panchang and daily forecast
# ---------------------------------------------------------------------------

def _sun_event(jd_start: float, lat: float, lon: float, rise: bool) -> float:
    flag = swe.CALC_RISE if rise else swe.CALC_SET
    res, tret = swe.rise_trans(jd_start, swe.SUN, flag, (lon, lat, 0), 0, 0, EPH)
    return tret[0]


def sun_times(d: date, lat: float, lon: float, tz: str) -> tuple[float, float, float]:
    """Sunrise, sunset and next sunrise (JD UT) for a local date."""
    j_mid = to_jd(datetime(d.year, d.month, d.day, 0, 0), tz)
    rise = _sun_event(j_mid, lat, lon, True)
    sset = _sun_event(rise, lat, lon, False)
    nrise = _sun_event(sset, lat, lon, True)
    return rise, sset, nrise


def tithi_at(jd: float, ayanamsa: str) -> int:
    m = sidereal_lon(jd, "Moon", ayanamsa)[0]
    s = sidereal_lon(jd, "Sun", ayanamsa)[0]
    return int(((m - s) % 360) // 12) + 1


def tithi_name(t: int) -> str:
    if t == 15:
        return "Shukla Purnima (full moon)"
    if t == 30:
        return "Krishna Amavasya (new moon)"
    paksha = "Shukla" if t <= 15 else "Krishna"
    return f"{paksha} {TITHI_NAMES[(t - 1) % 15]}"


def yoga_at(jd: float, ayanamsa: str) -> str:
    m = sidereal_lon(jd, "Moon", ayanamsa)[0]
    s = sidereal_lon(jd, "Sun", ayanamsa)[0]
    return YOGA_NAMES[int(((m + s) % 360) // NAK)]


def karana_at(jd: float, ayanamsa: str) -> str:
    m = sidereal_lon(jd, "Moon", ayanamsa)[0]
    s = sidereal_lon(jd, "Sun", ayanamsa)[0]
    k = int(((m - s) % 360) // 6)
    if k == 0:
        return "Kimstughna"
    if k == 57:
        return "Shakuni"
    if k == 58:
        return "Chatushpada"
    if k == 59:
        return "Naga"
    return KARANA_MOVABLE[(k - 1) % 7]


def _next_change(fn, jd: float, limit: float = 2.0, step: float = 1 / 48) -> float | None:
    v0 = fn(jd)
    t = jd
    while t < jd + limit:
        t2 = t + step
        if fn(t2) != v0:
            lo, hi = t, t2
            for _ in range(16):
                mid = (lo + hi) / 2
                if fn(mid) == v0:
                    lo = mid
                else:
                    hi = mid
            return hi
        t = t2
    return None


def segments(fn, j0: float, j1: float) -> list[tuple[float, float, object]]:
    out = []
    t = j0
    while t < j1:
        v = fn(t)
        nxt = _next_change(fn, t, limit=j1 - t + 1e-9)
        end = min(nxt, j1) if nxt else j1
        out.append((t, end, v))
        t = end + 1e-7
    return out


def panchang(d: date, lat: float, lon: float, tz: str, ayanamsa: str) -> dict:
    rise, sset, nrise = sun_times(d, lat, lon, tz)
    wd = d.weekday()  # Mon=0
    dl = sset - rise
    part = dl / 8

    def window(idx):
        return rise + (idx - 1) * part, rise + idx * part

    moon_nak = lambda t: nak_of(sidereal_lon(t, "Moon", ayanamsa)[0])
    tithi_fn = lambda t: tithi_at(t, ayanamsa)
    noon = (rise + sset) / 2
    muhurta = dl / 15
    vara_lord = WEEKDAY_LORD[wd]
    i0 = HORA_SEQ.index(vara_lord)
    horas = []
    dh, nh = dl / 12, (nrise - sset) / 12
    for k in range(24):
        lord = HORA_SEQ[(i0 + k) % 7]
        if k < 12:
            s, e = rise + k * dh, rise + (k + 1) * dh
        else:
            s, e = sset + (k - 12) * nh, sset + (k - 11) * nh
        horas.append(dict(start=s, end=e, lord=lord, day=k < 12))
    return dict(
        date=d, weekday=d.strftime("%A"), vara_lord=vara_lord,
        sunrise=rise, sunset=sset, next_sunrise=nrise,
        tithi=segments(tithi_fn, rise, nrise),
        nakshatra=segments(moon_nak, rise, nrise),
        yoga=yoga_at(rise, ayanamsa), karana=karana_at(rise, ayanamsa),
        moon_sign_rise=sign_of(sidereal_lon(rise, "Moon", ayanamsa)[0]),
        moon_sign_segments=segments(lambda t: sign_of(sidereal_lon(t, "Moon", ayanamsa)[0]), rise, nrise),
        rahu_kalam=window(RAHU_PART[wd]), yamagandam=window(YAMA_PART[wd]),
        gulika=window(GULIKA_PART[wd]),
        abhijit=(noon - muhurta / 2, noon + muhurta / 2),
        horas=horas,
    )


def daily_forecast(ch: Chart, d: date, lat: float, lon: float, tz: str) -> dict:
    pc = panchang(d, lat, lon, tz, ch.ayanamsa)
    rise, sset = pc["sunrise"], pc["sunset"]
    mid = (rise + sset) / 2
    moon_lon = sidereal_lon(mid, "Moon", ch.ayanamsa)[0]
    msign = sign_of(moon_lon)
    tnak = nak_of(moon_lon)
    tara, tq = tara_of(ch.moon_nak, tnak)
    h_asc = ch.house_of_sign(msign)
    h_moon = _house_from(ch.moon_sign, msign)
    tithi = tithi_at(mid, ch.ayanamsa)
    yoga = yoga_at(mid, ch.ayanamsa)

    score, parts = 50, []

    def add(pts, why):
        nonlocal score
        score += pts
        parts.append((why, pts))

    tara_pts = {"good": 15, "bad": -15, "mixed": -5}[tq]
    if tara == "Naidhana":
        tara_pts = -25
    add(tara_pts, f"Tara Bala: {tara} ({TARA_MEANING[tara]})")
    if h_moon == 8:
        add(-20, "Chandrashtama: Moon in 8th from natal Moon")
    elif h_moon in (1, 3, 6, 7, 10, 11):
        add(10, f"Chandra Bala good: Moon {h_moon} from natal Moon")
    else:
        add(-5, f"Chandra Bala weak: Moon {h_moon} from natal Moon")
    if h_asc in (8, 12):
        add(-8, f"Moon in house {h_asc} from Ascendant ({HOUSE_THEMES[h_asc]})")
    elif h_asc in (1, 5, 9, 10, 11):
        add(6, f"Moon in house {h_asc} from Ascendant ({HOUSE_THEMES[h_asc]})")
    if tithi in RIKTA_TITHIS:
        add(-8, f"Rikta tithi ({tithi_name(tithi)}) - avoid new starts")
    elif tithi == 30:
        add(-10, "Amavasya (new moon)")
    elif tithi in (5, 10, 15, 20, 25):
        add(5, f"Purna tithi ({tithi_name(tithi)})")
    if yoga in BAD_YOGAS:
        add(-5, f"Inauspicious yoga ({yoga})")
    vl = pc["vara_lord"]
    fn = functional_nature(ch, vl)
    if fn.startswith(("Benefic", "Yogakaraka")):
        add(5, f"Day lord {vl} is a functional benefic for this chart")
    elif fn.startswith("Malefic"):
        add(-3, f"Day lord {vl} is a functional malefic for this chart")
    score = max(0, min(100, score))

    def windows():
        bad = [pc["rahu_kalam"], pc["yamagandam"], pc["gulika"]]
        slots, t, step = [], rise, 1 / 48
        while t + step <= sset + 1e-9:
            s, e = t, t + step
            clash = any(not (e <= b0 or s >= b1) for b0, b1 in bad)
            mnak = nak_of(sidereal_lon((s + e) / 2, "Moon", ch.ayanamsa)[0])
            good = tara_of(ch.moon_nak, mnak)[1] == "good"
            slots.append((s, e, (not clash) and good))
            t = e
        merged = []
        for s, e, ok in slots:
            if ok and merged and abs(merged[-1][1] - s) < 1e-6:
                merged[-1] = (merged[-1][0], e)
            elif ok:
                merged.append((s, e))
        return [w for w in merged if w[1] - w[0] >= 1 / 48 - 1e-6]

    tara_segments = [(s, e, tara_of(ch.moon_nak, v)) for s, e, v in pc["nakshatra"]]
    hora_rows = []
    for h in pc["horas"]:
        hora_rows.append(dict(**h, good_for=HORA_GOOD_FOR[h["lord"]],
                              for_you=functional_nature(ch, h["lord"])))
    text = []
    text.append(f"Moon in {SIGNS[msign]}, your house {h_asc}: focus on {HOUSE_THEMES[h_asc]}.")
    text.append(f"Star of the day: {NAKSHATRAS[tnak]} - your {tara} tara ({TARA_MEANING[tara]}).")
    if h_moon == 8:
        text.append("Chandrashtama day: keep important decisions and arguments for another day.")
    if tithi in RIKTA_TITHIS:
        text.append("Rikta tithi: good for finishing work, not for beginnings.")
    return dict(panchang=pc, score=score, parts=parts, moon_sign=msign,
                house_from_asc=h_asc, house_from_moon=h_moon, tara=tara,
                tara_quality=tq, tara_segments=tara_segments,
                good_windows=windows(), horas=hora_rows, text=text)


# ---------------------------------------------------------------------------
# Muhurta search
# ---------------------------------------------------------------------------
MUHURTA_PURPOSES = {
    "General auspicious start": dict(
        naks={"Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni",
              "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana",
              "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"},
        days={0, 2, 3, 4}, avoid_merc_retro=False),
    "Business deal / contract signing": dict(
        naks={"Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni",
              "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana",
              "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"},
        days={0, 2, 3, 4}, avoid_merc_retro=True),
    "Property purchase / registration": dict(
        naks={"Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta",
              "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
              "Shatabhisha", "Uttara Bhadrapada", "Revati"},
        days={0, 2, 3, 4}, avoid_merc_retro=True),
    "Joining a job / new role / hiring": dict(
        naks={"Ashwini", "Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta",
              "Chitra", "Anuradha", "Uttara Ashadha", "Shravana", "Revati"},
        days={0, 2, 3, 4, 6}, avoid_merc_retro=False),
    "Travel": dict(
        naks={"Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Anuradha",
              "Shravana", "Dhanishta", "Revati"},
        days={0, 2, 3, 4}, avoid_merc_retro=False),
    "Wearing gemstone / crystal": dict(
        naks={"Ashwini", "Rohini", "Pushya", "Uttara Phalguni", "Hasta", "Chitra",
              "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta",
              "Uttara Bhadrapada", "Revati"},
        days={0, 2, 3, 4, 6}, avoid_merc_retro=False),
}


def eclipse_jds(j0: float, j1: float) -> list[float]:
    out = []
    for fn in (swe.sol_eclipse_when_glob, swe.lun_eclipse_when):
        t = j0 - 5
        while True:
            r = fn(t, EPH)[1][0]
            if r > j1 + 5:
                break
            out.append(r)
            t = r + 20
    return out


def find_muhurtas(ch: Chart, purpose: str, d0: date, d1: date, lat: float,
                  lon: float, tz: str, shukla_only: bool = False,
                  avoid_ashtami: bool = True, avoid_eclipse_days: int = 3,
                  second: Chart | None = None, hours: tuple[int, int] = (7, 19)) -> list[dict]:
    cfg = MUHURTA_PURPOSES[purpose]
    j0 = to_jd(datetime(d0.year, d0.month, d0.day), tz)
    j1 = to_jd(datetime(d1.year, d1.month, d1.day, 23, 59), tz)
    ecl = eclipse_jds(j0, j1)
    results = []
    d = d0
    while d <= d1:
        if d.weekday() not in cfg["days"]:
            d += timedelta(days=1)
            continue
        pc = panchang(d, lat, lon, tz, ch.ayanamsa)
        if any(abs(pc["sunrise"] - e) <= avoid_eclipse_days for e in ecl):
            d += timedelta(days=1)
            continue
        if cfg["avoid_merc_retro"] and sidereal_lon(pc["sunrise"], "Mercury", ch.ayanamsa)[1] < 0:
            d += timedelta(days=1)
            continue
        bad = [pc["rahu_kalam"], pc["yamagandam"], pc["gulika"]]
        lo = to_jd(datetime(d.year, d.month, d.day, hours[0]), tz)
        hi = to_jd(datetime(d.year, d.month, d.day, hours[1]), tz)
        t, step = max(lo, pc["sunrise"]), 1 / 48
        wins, cur = [], None
        while t + step <= min(hi, pc["sunset"]) + 1e-9:
            m = (t + step / 2)
            mlon = sidereal_lon(m, "Moon", ch.ayanamsa)[0]
            nk = nak_of(mlon)
            tt = tithi_at(m, ch.ayanamsa)
            ok = NAKSHATRAS[nk] in cfg["naks"]
            ok &= tara_of(ch.moon_nak, nk)[1] == "good"
            if second is not None:
                ok &= tara_of(second.moon_nak, nk)[1] == "good"
            ok &= tt not in RIKTA_TITHIS and tt != 30
            if avoid_ashtami:
                ok &= tt not in (8, 23)
            if shukla_only:
                ok &= tt <= 15
            hs = ch.house_of_sign(sign_of(mlon))
            ok &= hs not in (8, 12)
            ok &= _house_from(ch.moon_sign, sign_of(mlon)) != 8
            ok &= not any(not (t + step <= b0 or t >= b1) for b0, b1 in bad)
            if ok:
                if cur and abs(cur[1] - t) < 1e-6:
                    cur = (cur[0], t + step, cur[2])
                else:
                    if cur:
                        wins.append(cur)
                    cur = (t, t + step, (NAKSHATRAS[nk], tara_of(ch.moon_nak, nk)[0], tt, hs))
            t += step
        if cur:
            wins.append(cur)
        for s, e, (nk, tr, tt, hs) in wins:
            if e - s >= 1 / 24 - 1e-6:
                results.append(dict(date=d, start=s, end=e, nakshatra=nk, tara=tr,
                                    tithi=tithi_name(tt), moon_house=hs,
                                    weekday=d.strftime("%a")))
        d += timedelta(days=1)
    return results


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------
VARNA = {3: 4, 7: 4, 11: 4, 0: 3, 4: 3, 8: 3, 1: 2, 5: 2, 9: 2, 2: 1, 6: 1, 10: 1}
VARNA_NAME = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}
YONI_OF = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep",
           "Cat", "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer",
           "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow",
           "Elephant"]
YONI_LIST = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat", "Cow",
             "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose", "Lion"]
YONI_MATRIX = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]
GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva",
        "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva",
        "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva",
        "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
GANA_SCORE = {("Deva", "Deva"): 6, ("Deva", "Manushya"): 5, ("Deva", "Rakshasa"): 1,
              ("Manushya", "Deva"): 6, ("Manushya", "Manushya"): 6,
              ("Manushya", "Rakshasa"): 0, ("Rakshasa", "Deva"): 1,
              ("Rakshasa", "Manushya"): 0, ("Rakshasa", "Rakshasa"): 6}
NADI = ["Aadi", "Madhya", "Antya", "Antya", "Madhya", "Aadi", "Aadi", "Madhya", "Antya",
        "Antya", "Madhya", "Aadi", "Aadi", "Madhya", "Antya", "Antya", "Madhya", "Aadi",
        "Aadi", "Madhya", "Antya", "Antya", "Madhya", "Aadi", "Aadi", "Madhya", "Antya"]
VASHYA_GROUPS = ["Chatushpada", "Manava", "Jalachara", "Vanachara", "Keeta"]
VASHYA_MATRIX = [[2, 1, 1, 0.5, 1], [1, 2, 0.5, 0, 1], [1, 0.5, 2, 1, 1],
                 [0.5, 0, 1, 2, 0], [1, 1, 1, 0, 2]]


def vashya_group(lon: float) -> str:
    s, deg = sign_of(lon), lon % 30
    if s in (0, 1):
        return "Chatushpada"
    if s == 8:
        return "Manava" if deg < 15 else "Chatushpada"
    if s == 9:
        return "Chatushpada" if deg < 15 else "Jalachara"
    if s in (2, 5, 6, 10):
        return "Manava"
    if s in (3, 11):
        return "Jalachara"
    if s == 4:
        return "Vanachara"
    return "Keeta"


def _maitri_score(a: str, b: str) -> float:
    if a == b:
        return 5
    r1, r2 = relationship(a, b), relationship(b, a)
    pair = sorted([r1, r2])
    table = {("friend", "friend"): 5, ("friend", "neutral"): 4,
             ("neutral", "neutral"): 3, ("enemy", "friend"): 1,
             ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0}
    return table[tuple(pair)]


def ashtakoota(groom: Chart, bride: Chart) -> list[dict]:
    gm, bm = groom.planets["Moon"], bride.planets["Moon"]
    gs, bs, gn, bn = gm["sign"], bm["sign"], gm["nak"], bm["nak"]
    rows = []
    v = 1 if VARNA[gs] >= VARNA[bs] else 0
    rows.append(dict(koota="Varna (work nature)", max=1, score=v,
                     detail=f"{VARNA_NAME[VARNA[gs]]} / {VARNA_NAME[VARNA[bs]]}"))
    g1, g2 = vashya_group(gm["lon"]), vashya_group(bm["lon"])
    rows.append(dict(koota="Vashya (mutual influence)", max=2,
                     score=VASHYA_MATRIX[VASHYA_GROUPS.index(g1)][VASHYA_GROUPS.index(g2)],
                     detail=f"{g1} / {g2}"))
    t1 = ((gn - bn) % 27) % 9
    t2 = ((bn - gn) % 27) % 9
    bad = {2, 4, 6}
    ts = (0 if t1 in bad else 1.5) + (0 if t2 in bad else 1.5)
    rows.append(dict(koota="Tara (destiny)", max=3, score=ts,
                     detail=f"{TARAS[t2][0]} / {TARAS[t1][0]}"))
    y1, y2 = YONI_OF[gn], YONI_OF[bn]
    rows.append(dict(koota="Yoni (temperament, intimacy)", max=4,
                     score=YONI_MATRIX[YONI_LIST.index(y1)][YONI_LIST.index(y2)],
                     detail=f"{y1} / {y2}"))
    l1, l2 = SIGN_LORD[gs], SIGN_LORD[bs]
    rows.append(dict(koota="Graha Maitri (mental compatibility)", max=5,
                     score=_maitri_score(l1, l2), detail=f"{l1} / {l2}"))
    ga, gb = GANA[gn], GANA[bn]
    rows.append(dict(koota="Gana (nature)", max=6, score=GANA_SCORE[(ga, gb)],
                     detail=f"{ga} / {gb}"))
    dist = (gs - bs) % 12 + 1
    bk = 0 if dist in (2, 12, 5, 9, 6, 8) else 7
    rows.append(dict(koota="Bhakoot (love, finances, family)", max=7, score=bk,
                     detail=f"Moon signs {dist}/{(bs - gs) % 12 + 1} apart"))
    n1, n2 = NADI[gn], NADI[bn]
    rows.append(dict(koota="Nadi (health, progeny)", max=8, score=0 if n1 == n2 else 8,
                     detail=f"{n1} / {n2}"))
    return rows


def manglik(ch: Chart) -> dict:
    m = ch.planets["Mars"]
    h_asc = m["house"]
    h_moon = _house_from(ch.moon_sign, m["sign"])
    h_ven = _house_from(ch.planets["Venus"]["sign"], m["sign"])
    dosha = {1, 2, 4, 7, 8, 12}
    return dict(from_asc=h_asc in dosha, from_moon=h_moon in dosha,
                from_venus=h_ven in dosha, houses=(h_asc, h_moon, h_ven))


PLANET_ACTION = {"Sun": "brings authority and visibility to",
                 "Moon": "brings emotional comfort and sensitivity to",
                 "Mars": "energises, pushes or provokes",
                 "Mercury": "stimulates ideas and discussion about",
                 "Jupiter": "supports, protects and expands",
                 "Venus": "brings warmth and liking to",
                 "Saturn": "adds discipline, pressure or delay to",
                 "Rahu": "amplifies, unsettles or challenges",
                 "Ketu": "detaches from or questions"}
POINT_MEANING = {"Asc": "self and direction", "Sun": "authority and ego",
                 "Moon": "feelings and mind", "Mars": "drive and temper",
                 "Mercury": "thinking and communication", "Jupiter": "wisdom and growth",
                 "Venus": "relationships and values", "Saturn": "duties and fears",
                 "Rahu": "ambitions", "Ketu": "detachment"}
SIGN_DISTANCE_NOTE = {1: "same sign - think alike", 7: "1/7 - complementary opposites",
                      4: "4/10 - good working link", 10: "4/10 - good working link",
                      5: "5/9 - very harmonious", 9: "5/9 - very harmonious",
                      3: "3/11 - supportive", 11: "3/11 - supportive",
                      2: "2/12 - mixed, careful with money",
                      12: "2/12 - mixed, careful with money",
                      6: "6/8 - friction, different styles",
                      8: "6/8 - friction, different styles"}


def synastry(a: Chart, b: Chart, orb: float = 5.0) -> dict:
    ta = tara_of(a.moon_nak, b.moon_nak)
    tb = tara_of(b.moon_nak, a.moon_nak)
    asc_d = (b.asc_sign - a.asc_sign) % 12 + 1
    moon_d = (b.moon_sign - a.moon_sign) % 12 + 1
    contacts = []
    pts_a = {"Asc": a.asc, **{p: a.planets[p]["lon"] for p in PLANETS}}
    pts_b = {"Asc": b.asc, **{p: b.planets[p]["lon"] for p in PLANETS}}
    for x, y, nx, ny in ((pts_a, pts_b, a.name, b.name), (pts_b, pts_a, b.name, a.name)):
        for pa, la in x.items():
            if pa == "Asc":
                continue
            for pb, lb in y.items():
                d = angdist(la, lb)
                if d <= orb:
                    contacts.append(dict(
                        key=frozenset({(nx, pa), (ny, pb), "conj"}) if pb != "Asc" else (nx, pa, ny, pb),
                        contact=f"{nx}'s {pa} - {ny}'s {pb}", orb=round(d, 1),
                        reading=f"{nx}'s {pa} {PLANET_ACTION[pa]} {ny}'s {POINT_MEANING[pb]}."))
                elif abs(d - 180) <= orb and pa in ("Sun", "Moon", "Mars", "Saturn", "Jupiter") and pb in ("Sun", "Moon", "Mars", "Saturn", "Asc"):
                    contacts.append(dict(
                        key=frozenset({(nx, pa), (ny, pb), "opp"}),
                        contact=f"{nx}'s {pa} opposite {ny}'s {pb}", orb=round(abs(d - 180), 1),
                        reading=f"Opposition: {nx}'s {pa} faces {ny}'s {POINT_MEANING[pb]} - balance or tension."))
    seen, uniq = set(), []
    for c in sorted(contacts, key=lambda c: c["orb"]):
        k = c.pop("key")
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    overlays = {
        f"{b.name}'s Ascendant in {a.name}'s house": a.house_of_sign(b.asc_sign),
        f"{b.name}'s Moon in {a.name}'s house": a.house_of_sign(b.moon_sign),
        f"{a.name}'s Ascendant in {b.name}'s house": b.house_of_sign(a.asc_sign),
        f"{a.name}'s Moon in {b.name}'s house": b.house_of_sign(a.moon_sign),
    }
    return dict(tara_a_to_b=ta, tara_b_to_a=tb, asc_relation=SIGN_DISTANCE_NOTE[asc_d],
                moon_relation=SIGN_DISTANCE_NOTE[moon_d],
                lagna_lords=(a.lord_of_house(1), b.lord_of_house(1),
                             relationship(a.lord_of_house(1), b.lord_of_house(1)),
                             relationship(b.lord_of_house(1), a.lord_of_house(1))),
                contacts=uniq, overlays=overlays)


# ---------------------------------------------------------------------------
# Natal interpretation text
# ---------------------------------------------------------------------------

def planet_reading(ch: Chart, p: str) -> str:
    d = ch.planets[p]
    mod = []
    if d["dignity"] == "Exalted":
        mod.append("very strong (exalted)")
    elif d["dignity"] == "Own sign":
        mod.append("strong (own sign)")
    elif d["dignity"] == "Debilitated":
        mod.append("weak (debilitated) - check Neecha Bhanga")
    if d["combust"]:
        mod.append("combust - overshadowed by the Sun")
    if d["retro"]:
        mod.append("retrograde - results come with revisions or delay")
    m = f" – {'; '.join(mod)}" if mod else ""
    return (f"**{p} in house {d['house']}, {SIGNS[d['sign']]}**{m}. Brings "
            f"{PLANET_KEYWORDS[p]} into {HOUSE_THEMES[d['house']]}.")
