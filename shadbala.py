"""
Shadbala: the six-fold planetary strength of Parashara (BPHS), in virupas (60 virupas = 1 rupa).

Components: Sthana (positional), Dig (directional), Kala (temporal), Chesta (motional),
Naisargika (natural) and Drik (aspectual). Checked against AstroSage's Shadbala table.
"""
from __future__ import annotations

from datetime import timedelta

import swisseph as swe

import astro_core as ac

SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
EXALT_DEG = {"Sun": 10, "Moon": 33, "Mars": 298, "Mercury": 165, "Jupiter": 95, "Venus": 357, "Saturn": 200}
MOOLA = {"Sun": (4, 0, 20), "Moon": (1, 3, 30), "Mars": (0, 0, 12), "Mercury": (5, 15, 20),
         "Jupiter": (8, 0, 10), "Venus": (6, 0, 15), "Saturn": (10, 0, 20)}
NAISARGIKA = {"Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29, "Mercury": 25.71,
              "Mars": 17.14, "Saturn": 8.57}
REQUIRED = {"Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420, "Jupiter": 390, "Venus": 330, "Saturn": 300}
MALE, FEMALE = {"Sun", "Mars", "Jupiter"}, {"Moon", "Venus"}
# mean longitudes (Meeus, tropical, J2000 + rate per Julian century)
MEAN_EL = {"Mercury": (252.250906, 149472.6746358), "Venus": (181.979801, 58517.8156760),
           "Earth": (100.466457, 35999.3728565), "Mars": (355.433000, 19140.2993039),
           "Jupiter": (34.351519, 3034.9056606), "Saturn": (50.077444, 1222.1138488)}
KALI_EPOCH = 588464.5  # Kali Yuga epoch counted from the Thursday midnight (matches AstroSage year/month lords)
WEEKDAY_FROM_SUN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def _d30(lon: float) -> int:
    s, deg = ac.sign_of(lon), lon % 30
    if s % 2 == 0:  # odd sign
        cuts = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]
    else:
        cuts = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
    return next(sg for lim, sg in cuts if deg < lim)


def _varga(lon: float, d: int) -> int:
    return _d30(lon) if d == 30 else ac.varga_sign(lon, d)


def _compound(ch: ac.Chart, a: str, b: str) -> str:
    nat = ac.relationship(a, b)
    if nat == "same":
        return "own"
    dist = ac._house_from(ch.planets[a]["sign"], ch.planets[b]["sign"])
    temp_friend = dist in (2, 3, 4, 10, 11, 12)
    return {("friend", True): "great friend", ("friend", False): "neutral",
            ("neutral", True): "friend", ("neutral", False): "enemy",
            ("enemy", True): "neutral", ("enemy", False): "great enemy"}[(nat, temp_friend)]


VARGA_POINTS = {"moola": 45, "own": 30, "great friend": 22.5, "friend": 15, "neutral": 7.5,
                "enemy": 3.75, "great enemy": 1.875}


def _sthana(ch: ac.Chart, p: str) -> dict:
    d = ch.planets[p]
    lon = d["lon"]
    deb = (EXALT_DEG[p] + 180) % 360
    uchcha = ac.angdist(lon, deb) / 3
    sv = 0.0
    for v in (1, 2, 3, 7, 9, 12, 30):
        sg = _varga(lon, v)
        ms, a, b = MOOLA[p]
        if v == 1 and sg == ms and a <= d["deg"] < b:
            sv += VARGA_POINTS["moola"]
            continue
        lord = ac.SIGN_LORD[sg]
        sv += VARGA_POINTS[_compound(ch, p, lord)] if lord != p else VARGA_POINTS["own"]
    odd1 = d["sign"] % 2 == 0
    odd9 = ac.varga_sign(lon, 9) % 2 == 0
    if p in FEMALE:
        oja = (15 if not odd1 else 0) + (15 if not odd9 else 0)
    else:
        oja = (15 if odd1 else 0) + (15 if odd9 else 0)
    h = d["house"]
    kendra = 60 if h in (1, 4, 7, 10) else 30 if h in (2, 5, 8, 11) else 15
    dk = int(d["deg"] // 10)
    drek = 15 if (p in MALE and dk == 0) or (p in FEMALE and dk == 2) or (p in ("Mercury", "Saturn") and dk == 1) else 0
    return dict(uchcha=uchcha, saptavargaja=sv, ojayugma=oja, kendra=kendra, drekkana=drek,
                total=uchcha + sv + oja + kendra + drek)


def _dig(ch: ac.Chart, p: str) -> float:
    lon = ch.planets[p]["lon"]
    strong = {"Sun": ch.mc, "Mars": ch.mc, "Jupiter": ch.asc, "Mercury": ch.asc,
              "Saturn": (ch.asc + 180) % 360, "Moon": (ch.mc + 180) % 360, "Venus": (ch.mc + 180) % 360}[p]
    return (180 - ac.angdist(lon, strong)) / 3


def _declination(jd: float, p: str) -> float:
    """Declination of the planet's ecliptic point (latitude ignored, as in classical Kranti)."""
    import math
    lam = swe.calc_ut(jd, ac.SWE_ID[p], ac.EPH)[0][0]
    eps = 24.0  # classical maximum declination
    return math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))


def _elong(ch: ac.Chart) -> float:
    e = (ch.planets["Moon"]["lon"] - ch.planets["Sun"]["lon"]) % 360
    return e if e <= 180 else 360 - e


def _benefic_set(ch: ac.Chart) -> set:
    ben = {"Jupiter", "Venus"}
    if _elong(ch) >= 90:  # bright Moon (from Shukla Ashtami to Krishna Ashtami)
        ben.add("Moon")
    malefic_with_merc = [q for q in ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
                         if ch.planets[q]["sign"] == ch.planets["Mercury"]["sign"]]
    if not malefic_with_merc:
        ben.add("Mercury")
    return ben


def _kala(ch: ac.Chart) -> dict:
    jd = ch.jd
    d0 = ch.dt_local.date()
    rise, sset, nrise = ac.sun_times(d0, ch.lat, ch.lon, ch.tz)
    if jd < rise:  # before sunrise: the Hindu day began at the previous sunrise
        rise, sset, nrise = ac.sun_times(d0 - timedelta(days=1), ch.lat, ch.lon, ch.tz)
    day = rise <= jd < sset
    noon = (rise + sset) / 2
    midnight = noon + 0.5 if jd > noon else noon - 0.5
    unnata = min(abs(jd - midnight) * 60, 30)  # ghatis from midnight (1 day = 60 ghatis)
    out = {p: {} for p in SEVEN}
    for p in SEVEN:
        if p == "Mercury":
            out[p]["nathonnatha"] = 60.0
        elif p in ("Sun", "Jupiter", "Venus"):
            out[p]["nathonnatha"] = 2 * unnata
        else:
            out[p]["nathonnatha"] = 60 - 2 * unnata
    el = _elong(ch)
    ben = _benefic_set(ch)
    for p in SEVEN:
        out[p]["paksha"] = el / 3 if p in ben else 60 - el / 3
    # tribhaga
    if day:
        third = int((jd - rise) / ((sset - rise) / 3))
        tlord = ["Mercury", "Sun", "Saturn"][min(third, 2)]
    else:
        third = int((jd - sset) / ((nrise - sset) / 3))
        tlord = ["Moon", "Venus", "Mars"][min(third, 2)]
    for p in SEVEN:
        out[p]["tribhaga"] = 60.0 if p in (tlord, "Jupiter") else 0.0
    # year, month, weekday and hora lords
    rd = ac.jd_to_local(rise, ch.tz).date()  # civil date of the Hindu day
    ahar = int(swe.julday(rd.year, rd.month, rd.day, 0.0) - KALI_EPOCH)  # days since the epoch (a Thursday)
    wd = lambda n: WEEKDAY_FROM_SUN[(4 + n) % 7]
    abda = wd((ahar // 360) * 360)
    masa = wd((ahar // 30) * 30)
    vara = ac.WEEKDAY_LORD[rd.weekday()]
    hrs = int((jd - rise) * 24)
    hora = ac.HORA_SEQ[(ac.HORA_SEQ.index(vara) + hrs) % 7]
    for p in SEVEN:
        out[p]["abda"] = 15.0 if p == abda else 0.0
        out[p]["masa"] = 30.0 if p == masa else 0.0
        out[p]["vara"] = 45.0 if p == vara else 0.0
        out[p]["hora"] = 60.0 if p == hora else 0.0
    # ayana bala from declination
    for p in SEVEN:
        dec = _declination(jd, p)
        if p == "Mercury":
            v = (24 + abs(dec)) / 48 * 60
        elif p in ("Moon", "Saturn"):
            v = (24 - dec) / 48 * 60
        else:
            v = (24 + dec) / 48 * 60
        out[p]["ayana"] = 2 * v if p == "Sun" else v
    for p in SEVEN:
        out[p]["total"] = sum(out[p].values())
    return dict(planets=out, lords=dict(year=abda, month=masa, weekday=vara, hora=hora), day=day)


def _mean(name: str, jd: float) -> float:
    t = (jd - 2451545.0) / 36525
    l0, n = MEAN_EL[name]
    return (l0 + n * t) % 360


def _chesta(ch: ac.Chart, kala: dict) -> dict:
    jd = ch.jd
    out = {"Sun": kala["planets"]["Sun"]["ayana"] / 2, "Moon": _elong(ch) / 3}
    mean_sun = (_mean("Earth", jd) + 180) % 360
    for p in ("Mars", "Jupiter", "Saturn", "Mercury", "Venus"):
        true = swe.calc_ut(jd, ac.SWE_ID[p], ac.EPH)[0][0]
        if p in ("Mars", "Jupiter", "Saturn"):
            mean_p, seeghra = _mean(p, jd), mean_sun
        else:
            mean_p, seeghra = mean_sun, _mean(p, jd)
        avg = (mean_p + true) / 2 if abs(mean_p - true) <= 180 else ((mean_p + true + 360) / 2) % 360
        k = (seeghra - avg) % 360
        k = 360 - k if k > 180 else k
        out[p] = k / 3
    return out


def _aspect_value(angle: float, p: str) -> float:
    a = angle % 360
    if a < 30 or a >= 300:
        v = 0.0
    elif a < 60:
        v = (a - 30) / 2
    elif a < 90:
        v = a - 60 + 15
    elif a < 120:
        v = (120 - a) / 2 + 30
    elif a < 150:
        v = 150 - a
    elif a < 180:
        v = (a - 150) * 2
    else:
        v = (300 - a) / 2
    if p == "Saturn" and (60 <= a < 90 or 270 <= a < 300):
        v += 45
    elif p == "Jupiter" and (120 <= a < 150 or 240 <= a < 270):
        v += 30
    elif p == "Mars" and (90 <= a < 120 or 210 <= a < 240):
        v += 15
    return v


def _drik(ch: ac.Chart) -> dict:
    ben = _benefic_set(ch)
    out = {}
    for t in SEVEN:
        s = 0.0
        for a in SEVEN:
            if a == t:
                continue
            v = _aspect_value(ch.planets[t]["lon"] - ch.planets[a]["lon"], a)
            s += v if a in ben else -v
        out[t] = s / 4
    return out


def shadbala(ch: ac.Chart) -> dict:
    """Return per-planet components, totals in virupas and rupas, ratio to the classical minimum and rank."""
    kala = _kala(ch)
    chesta = _chesta(ch, kala)
    drik = _drik(ch)
    rows = {}
    for p in SEVEN:
        st = _sthana(ch, p)
        dig = _dig(ch, p)
        kl = kala["planets"][p]["total"]
        total = st["total"] + dig + kl + chesta[p] + NAISARGIKA[p] + drik[p]
        rows[p] = dict(sthana=st, dig=dig, kala=kala["planets"][p], chesta=chesta[p],
                       naisargika=NAISARGIKA[p], drik=drik[p], total=total, rupas=total / 60,
                       required=REQUIRED[p] / 60, ratio=total / REQUIRED[p])
    for i, p in enumerate(sorted(SEVEN, key=lambda q: -rows[q]["ratio"]), 1):
        rows[p]["rank"] = i
    return dict(planets=rows, lords=kala["lords"])


def strength_word(ratio: float) -> str:
    return "very strong" if ratio >= 1.35 else "strong" if ratio >= 1.1 else "average" if ratio >= 0.9 else "weak"


_CACHE: dict = {}


def cached(ch: ac.Chart) -> dict:
    key = (ch.name, ch.jd, ch.lat, ch.lon, ch.ayanamsa, ch.node)
    if key not in _CACHE:
        _CACHE[key] = shadbala(ch)
    return _CACHE[key]
