"""
Life reading: a rule-based description of a person by life area, and a
lifetime table of significant periods marked good, mixed or challenging.

Method (traditional Parashari rules):
- House strength: placement and dignity of the house lord, planets in the
  house, and aspects on it (malefics are treated as helpful in the growth
  houses 3, 6, 10 and 11).
- Planet strength: dignity, house placement, combustion, Neecha Bhanga.
- Each life area combines its houses with its natural significators (karakas)
  and the relevant divisional chart.
- Periods: Vimshottari antardashas rated from the functional nature and
  strength of the period lords and their relative placement, plus major
  transit milestones (Sade Sati, Saturn / Jupiter / Rahu returns) and eclipses
  falling on key natal points.
"""
from __future__ import annotations

from datetime import datetime

import swisseph as swe

import astro_core as ac

KENDRA, TRIKONA, DUSTHANA, UPACHAYA = {1, 4, 7, 10}, {1, 5, 9}, {6, 8, 12}, {3, 6, 10, 11}
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}

BODY_BY_SIGN = ["head, face and brain", "throat, neck and face", "lungs, shoulders, arms and nerves",
                "chest, stomach and breasts", "heart, spine and upper back", "digestion and intestines",
                "kidneys, lower back and skin", "reproductive, urinary and excretory organs",
                "hips, thighs and liver", "knees, bones and joints", "ankles, circulation and nerves",
                "feet, immunity and lymph"]
PLANET_HEALTH = {"Sun": "heart, eyes, bones and vitality", "Moon": "mind, sleep, fluids and chest",
                 "Mars": "blood, blood pressure, injuries, inflammation and surgery",
                 "Mercury": "nerves, skin, speech and anxiety",
                 "Jupiter": "liver, weight, blood sugar and fat",
                 "Venus": "kidneys, hormones, reproductive health and sugar",
                 "Saturn": "joints, bones, teeth, chronic and long-lasting conditions",
                 "Rahu": "allergies, toxins, unusual or hard-to-diagnose conditions",
                 "Ketu": "infections, sudden or mysterious complaints"}
PLANET_CAREER = {"Sun": "leadership, government, administration, top management",
                 "Moon": "public-facing work, hospitality, healthcare, food, travel",
                 "Mars": "engineering, real estate, defence, sports, technical operations",
                 "Mercury": "IT, analytics, trading, commerce, writing, consulting",
                 "Jupiter": "finance, banking, education, law, advisory, mentoring",
                 "Venus": "design, media, luxury, hospitality, arts, fashion",
                 "Saturn": "operations, manufacturing, infrastructure, labour, long-term institutions",
                 "Rahu": "technology, foreign companies, innovation, unconventional fields",
                 "Ketu": "research, specialised technical work, spirituality, healing"}
HOUSE_AREA = {1: "Self, health", 2: "Wealth, family", 3: "Effort, communication", 4: "Home, property",
              5: "Children, education", 6: "Health, competition", 7: "Marriage, partners", 8: "Sudden change",
              9: "Fortune, mentors", 10: "Career", 11: "Gains", 12: "Expenses, foreign"}
HOUSE_CAUTION = {1: "health and confidence dips", 2: "family disputes, harsh speech, money leaks",
                 3: "conflicts with siblings or colleagues, overexertion",
                 4: "unrest at home, property or vehicle problems, mother's health",
                 5: "worries about children, speculative losses",
                 6: "health issues, debts, disputes or litigation",
                 7: "strain with spouse or business partners",
                 8: "sudden events, accidents, surgery, tax or inheritance issues",
                 9: "disagreements with father or mentors, travel problems",
                 10: "career setbacks, conflict with seniors",
                 11: "delayed gains, issues within networks",
                 12: "heavy expenses, losses, sleep problems, foreign hassles"}
HOUSE_USE = {1: "personal initiatives and health", 2: "saving, family and income",
             3: "initiative, outreach, short trips", 4: "home, property, vehicles",
             5: "education, children, investments, creativity", 6: "beating competition, clearing debts",
             7: "marriage, partnerships, contracts", 8: "research, inheritance, transformation",
             9: "fortune, higher learning, mentors, long-distance travel",
             10: "career growth, recognition, leadership", 11: "income, gains, networks",
             12: "foreign work, spiritual growth, investment in assets"}
PLANET_CAUTION = {"Sun": "ego clashes and conflict with authority",
                  "Moon": "emotional ups and downs and anxiety",
                  "Mars": "anger, haste, accidents and disputes",
                  "Mercury": "miscommunication, contract errors and nervous stress",
                  "Jupiter": "over-optimism and over-expansion",
                  "Venus": "overindulgence and relationship strain",
                  "Saturn": "delays, low mood and heavy responsibilities",
                  "Rahu": "deception, risky shortcuts, confusion and addictions",
                  "Ketu": "sudden breaks, detachment and loss of direction"}
NAK_TRAITS = [
    "quick, pioneering, healing nature", "intense, responsible, strong-willed",
    "sharp, direct, purifying; can be critical", "attractive, creative, steady, comfort-loving",
    "curious, searching, gentle and restless", "intellectual, intense, transformative",
    "optimistic, resilient, returns to balance", "nurturing, disciplined, supportive",
    "perceptive, strategic, private", "dignified, traditional, leadership-minded",
    "warm, sociable, enjoys life", "generous, reliable, helpful in partnerships",
    "skilful with hands, practical, witty", "creative, stylish, builder of beautiful things",
    "independent, flexible, business-minded", "goal-driven, ambitious, determined",
    "loyal, devoted, good at friendships and organisation", "protective, capable, senior, can be secretive",
    "deep, root-seeking, questioning", "confident, persuasive, invincible spirit",
    "principled, persistent, lasting success", "good listener, learner, well-connected",
    "rhythmic, wealthy, generous, group-minded", "independent, healing, secretive, scientific",
    "intense, idealistic, transformative", "wise, patient, compassionate, steady",
    "kind, gentle, protective, guiding"]


def _dig_points(ch: ac.Chart, p: str) -> tuple[float, str]:
    d = ch.planets[p]["dignity"]
    pts = {"Exalted": 2, "Own sign": 1.5, "Friendly sign": 0.5, "Neutral sign": 0, "Enemy sign": -0.5,
           "Debilitated": -2, "-": 0}[d]
    if d == "Debilitated" and any(y["present"] for y in ac.detect_yogas(ch) if y["name"] == f"Neecha Bhanga for {p}"):
        return -0.5, "debilitated, but with cancellation (Neecha Bhanga)"
    return pts, d.lower()


def planet_strength(ch: ac.Chart, p: str) -> float:
    P = ch.planets[p]
    s, _ = _dig_points(ch, p)
    h = P["house"]
    s += 1 if h in KENDRA | TRIKONA else 0.5 if h == 11 else -1 if h in DUSTHANA else 0
    if P["combust"]:
        s -= 1
    if p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        import shadbala
        r = shadbala.cached(ch)["planets"][p]["ratio"]
        s += max(-1.5, min(1.5, (r - 1.0) * 4))  # classical six-fold strength
    return s


def house_strength(ch: ac.Chart, h: int) -> tuple[float, list[tuple[float, str]]]:
    P = ch.planets
    notes: list[tuple[float, str]] = []
    lord = ch.lord_of_house(h)
    lh = P[lord]["house"]
    if lh in KENDRA | TRIKONA:
        notes.append((2, f"House {h} lord {lord} is well placed in house {lh}"))
    elif lh == 11:
        notes.append((1.5, f"House {h} lord {lord} is in the house of gains (11th)"))
    elif lh in DUSTHANA:
        if h in DUSTHANA:
            notes.append((1, f"House {h} lord {lord} sits in house {lh}: difficulties tend to turn into advantage"))
        else:
            notes.append((-2, f"House {h} lord {lord} sits in a difficult house ({lh})"))
    pts, txt = _dig_points(ch, lord)
    if pts:
        notes.append((pts, f"{lord} (lord of house {h}) is {txt}"))
    if P[lord]["combust"]:
        notes.append((-1, f"{lord} (lord of house {h}) is combust"))
    for p in ac.PLANETS:
        if P[p]["house"] != h or p == lord:
            continue
        if p in NATURAL_BENEFICS:
            notes.append((1.5 if P[p]["dignity"] != "Debilitated" else 0.5, f"{p} sits in house {h}"))
        elif h in UPACHAYA:
            notes.append((1, f"{p} in house {h} gives drive and results through effort"))
        else:
            notes.append((-0.5 if p == "Sun" else -1.5, f"{p} sits in house {h}"))
    for p in ("Jupiter", "Venus", "Mercury", "Moon", "Saturn", "Mars"):
        ph = P[p]["house"]
        if ph != h and h in ac.aspected_houses(p, ph):
            if p == "Jupiter":
                notes.append((1.5, f"Jupiter aspects house {h} (protection)"))
            elif p in ("Venus", "Mercury", "Moon"):
                notes.append((0.5, f"{p} aspects house {h}"))
            elif h in UPACHAYA:
                notes.append((0.5, f"{p} aspects house {h} (pushes effort)"))
            else:
                notes.append((-1 if p == "Saturn" else -0.75, f"{p} aspects house {h}"))
    return sum(n for n, _ in notes), notes


def _stars(score: float) -> int:
    # centred so that an average area (score about 2) gets 3 stars; 5 stars are kept for clearly strong areas
    return int(max(1, min(5, int(3 + (score - 2) / 2.5 + 0.5))))


VERDICT = {5: "Very strong", 4: "Strong", 3: "Steady / mixed", 2: "Needs care", 1: "Challenging"}


def _area(ch, houses: dict, karakas: list, extra: list[tuple[float, str]] | None = None):
    total, notes = 0.0, []
    wsum = 0.0
    for h, w in houses.items():
        s, n = house_strength(ch, h)
        total += w * s
        wsum += w
        notes += n
    for k in karakas:
        s = planet_strength(ch, k)
        total += 0.8 * s
        wsum += 0.4
        d = ch.planets[k]
        notes.append((s, f"Significator {k} is in house {d['house']}, {d['dignity'].lower()}"
                         + (", combust" if d["combust"] else "")))
    for pts, txt in extra or []:
        total += pts
        notes.append((pts, txt))
    score = total / max(wsum, 1) * 1.6
    seen, strengths, cautions = set(), [], []
    for pts, txt in sorted(notes, key=lambda x: -abs(x[0])):
        if txt in seen or pts == 0:
            continue
        seen.add(txt)
        (strengths if pts > 0 else cautions).append(txt)
    st = _stars(score)
    return dict(score=round(score, 2), stars=st, verdict=VERDICT[st],
                strengths=strengths[:6], cautions=cautions[:6])


def _connected(ch: ac.Chart, lord: str, houses: set) -> bool:
    if lord in ("Rahu", "Ketu"):
        return ch.planets[lord]["house"] in houses
    return bool((set(ch.houses_owned(lord)) | {ch.planets[lord]["house"]}) & houses)


def _period_table(ch, periods: list[dict], houses: set, now_jd: float, n_good=3, n_bad=2):
    fut = [p for p in periods if p["end"] > now_jd and p["start"] < now_jd + 365.25 * 35
           and _connected(ch, p["ad"], houses)]
    good = [p for p in fut if p["rating"] == "Good"][:n_good]
    bad = [p for p in fut if p["rating"] == "Challenging"][:n_bad]
    return good, bad


# ---------------------------------------------------------------------------
# Periods (antardashas) and milestones
# ---------------------------------------------------------------------------

def _nature(ch, lord):
    if lord in ("Rahu", "Ketu"):
        return 0.5 * _nature(ch, ac.SIGN_LORD[ch.planets[lord]["sign"]])
    fn = ac.functional_nature(ch, lord)
    return 6 if fn.startswith("Yogakaraka") else 4 if fn.startswith("Benefic") else -3 if fn.startswith("Malefic") else 0


def dasha_periods(ch: ac.Chart, md_list: list) -> list[dict]:
    rows = []
    for md in md_list:
        for ad in md.children:
            s = 0.4 * _nature(ch, md.lord) + 0.6 * _nature(ch, ad.lord) + 0.6 * planet_strength(ch, ad.lord)
            rel = (ch.planets[ad.lord]["house"] - ch.planets[md.lord]["house"]) % 12 + 1
            if md.lord != ad.lord:
                s += -1.5 if rel in (6, 8, 12) else 0.5 if rel in (1, 4, 5, 7, 9, 10, 11) else 0
            rating = "Good" if s >= 2.5 else "Challenging" if s <= -0.5 else "Mixed"
            p = ch.planets[ad.lord]
            houses = sorted(set(ch.houses_owned(ad.lord)) | {p["house"]}) if ad.lord not in ("Rahu", "Ketu") \
                else [p["house"]]
            seen_a = {}
            for h in houses:
                for a in HOUSE_AREA[h].split(", "):
                    seen_a.setdefault(a.lower(), a.capitalize())
            areas = ", ".join(seen_a.values())
            good_use = "; ".join(HOUSE_USE[h] for h in houses if h not in DUSTHANA) or HOUSE_USE[houses[0]]
            care = [HOUSE_CAUTION[h] for h in houses if h in DUSTHANA or rating == "Challenging"]
            care.append(PLANET_CAUTION[ad.lord])
            guidance = (f"Use for: {good_use}." if rating == "Good" else
                        f"Use for: {good_use}. Be careful about: {'; '.join(dict.fromkeys(care))}."
                        if rating == "Mixed" else f"Be careful about: {'; '.join(dict.fromkeys(care))}.")
            label = (f"{md.lord} Mahadasha begins ({md.lord} – {ad.lord})" if ad is md.children[0]
                     else f"{md.lord} – {ad.lord} period")
            rows.append(dict(kind="Dasha", event=label, start=ad.start, end=ad.end,
                             md=md.lord, ad=ad.lord, rating=rating, score=round(s, 1), areas=areas,
                             guidance=guidance))
    return rows


def _crossings(ch, planet, target, j0, j1, step=2.0, node=None, gap=120):
    out, t = [], j0
    prev = (ac.sidereal_lon(t, planet, ch.ayanamsa, node or ch.node)[0] - target + 180) % 360 - 180
    while t < j1:
        t += step
        d = (ac.sidereal_lon(t, planet, ch.ayanamsa, node or ch.node)[0] - target + 180) % 360 - 180
        if abs(d) < 20 and (d > 0) != (prev > 0):
            if not out or t - out[-1] > gap:
                out.append(t)
        prev = d
    return out


def milestones(ch: ac.Chart, years: int = 95) -> list[dict]:
    j0, j1 = ch.jd, ch.jd + years * 365.25
    rows = []
    segs = ac.sade_sati(ch, years)
    def group(pred):
        out = []
        for x in segs:
            if not pred(x["phase"]):
                continue
            if out and x["start"] - out[-1]["end"] < 400:
                out[-1]["end"] = x["end"]
                out[-1]["parts"].append(x)
            else:
                out.append(dict(start=x["start"], end=x["end"], parts=[x]))
        return out
    for g in group(lambda ph: "Sade Sati" in ph):
        peaks = [x for x in g["parts"] if "phase 2" in x["phase"]]
        pk = (f" Peak (Saturn over natal Moon): {ac.jd_to_local(peaks[0]['start'], ch.tz).strftime('%b %Y')} to "
              f"{ac.jd_to_local(peaks[-1]['end'], ch.tz).strftime('%b %Y')}.") if peaks else ""
        rows.append(dict(kind="Transit", event="Sade Sati (7½ years of Saturn over the Moon)", start=g["start"],
                         end=g["end"], rating="Challenging", areas="Mind, health, career pressure, finances",
                         guidance="Be careful about: stress, low mood, health of self and parents, rising expenses "
                                  "and hasty career moves. Results come slowly but last." + pk))
        rows.append(dict(kind="Transit", event="Sade Sati ends: relief", start=g["end"], end=g["end"] + 180,
                         rating="Good", areas="Mind, career, finances",
                         guidance="Use for: rebuilding, fresh plans and commitments that were on hold."))
    for g in group(lambda ph: "Ashtama" in ph):
        rows.append(dict(kind="Transit", event="Ashtama Shani (Saturn 8th from Moon)", start=g["start"],
                         end=g["end"], rating="Challenging", areas="Health, sudden change",
                         guidance="Be careful about: health, accidents, sudden setbacks, debts and legal issues."))
    for t in _crossings(ch, "Saturn", ch.planets["Saturn"]["lon"], j0 + 365 * 20, j1, 3, gap=500):
        rows.append(dict(kind="Transit", event="Saturn return", start=t, end=t + 365, rating="Mixed",
                         areas="Career, responsibilities, maturity",
                         guidance="A reset of life structure. Use for long-term commitments. Be careful about: "
                                  "rigid decisions and overwork."))
    for t in _crossings(ch, "Jupiter", ch.planets["Jupiter"]["lon"], j0 + 365 * 10, j1, 2, gap=300):
        rows.append(dict(kind="Transit", event="Jupiter return (new 12-year cycle)", start=t, end=t + 365,
                         rating="Good", areas="Growth, learning, fortune",
                         guidance=f"Use for: new beginnings, learning, expansion; Jupiter is in your house "
                                  f"{ch.planets['Jupiter']['house']} ({ac.HOUSE_THEMES[ch.planets['Jupiter']['house']]})."))
    for t in _crossings(ch, "Rahu", ch.planets["Rahu"]["lon"], j0 + 365 * 15, j1, 4, gap=400):
        rows.append(dict(kind="Transit", event="Rahu return (18-year cycle)", start=t, end=t + 300, rating="Mixed",
                         areas="Ambition, direction",
                         guidance="Sudden shifts of direction. Be careful about: impulsive decisions and "
                                  "people promising too much."))
    return rows


def eclipse_hits(ch: ac.Chart, j0: float, years: int = 12, orb: float = 3.0) -> list[dict]:
    pts = {"Ascendant": ch.asc, "Sun": ch.planets["Sun"]["lon"], "Moon": ch.planets["Moon"]["lon"]}
    for h in (1, 7, 10):
        lord = ch.lord_of_house(h)
        if lord in pts:
            continue
        pts[f"{lord} ({ {1: '1st', 7: '7th', 10: '10th'}[h] } lord)"] = ch.planets[lord]["lon"]
    rows, j1 = [], j0 + years * 365.25
    for fn, kind, body in ((swe.sol_eclipse_when_glob, "Solar", "Sun"), (swe.lun_eclipse_when, "Lunar", "Moon")):
        t = j0
        while True:
            r = fn(t, ac.EPH)[1][0]
            if r > j1:
                break
            lon = ac.sidereal_lon(r, body, ch.ayanamsa)[0]
            hit = [n for n, pl in pts.items() if ac.angdist(lon, pl) <= orb or ac.angdist((lon + 180) % 360, pl) <= orb]
            if hit:
                h = ch.house_of_sign(ac.sign_of(lon))
                rows.append(dict(kind="Eclipse", event=f"{kind} eclipse on or opposite natal {', '.join(hit)}",
                                 start=r, end=r + 1, rating="Challenging", areas=HOUSE_AREA[h],
                                 guidance=f"A turning point in {ac.HOUSE_THEMES[h]}. Be careful about: "
                                          f"major irreversible decisions in the two weeks either side."))
            t = r + 20
    return rows


# ---------------------------------------------------------------------------
# Full reading
# ---------------------------------------------------------------------------

def _spouse_line(ch: ac.Chart, sex: str) -> str:
    """Plain sentence on the classical significator of the husband or wife."""
    if sex not in ("male", "female"):
        return ("Spouse significator: Venus is used, as sex is not set in the profile. "
                "Set it to read the husband's or wife's significator correctly.")
    k, who = ("Jupiter", "husband") if sex == "female" else ("Venus", "wife")
    s = planet_strength(ch, k)
    d = ch.planets[k]
    word = ("strong, a good sign for a supportive and respected " + who if s >= 1.5 else
            "weak, so the " + who + " may feel less supportive at times; patience and remedies help" if s <= -1 else
            "of average strength: the bond grows with effort")
    return (f"{k}, the traditional significator of the {who}, is in your {_ord(d['house'])} house and is {word}.")


def _ord(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def life_reading(ch: ac.Chart, md_list: list, now_jd: float) -> dict:
    P = ch.planets
    periods = dasha_periods(ch, md_list)
    strengths = sorted(((planet_strength(ch, p), p) for p in ac.PLANETS[:7]), reverse=True)
    yogas = [y for y in ac.detect_yogas(ch) if y["present"]]
    chain = ac.current_chain(md_list, now_jd)
    mds = [(m.lord, m.start, m.end, _nature(ch, m.lord) + planet_strength(ch, m.lord)) for m in md_list]

    # ---- Summary
    moon = P["Moon"]
    summary = [
        f"Ascendant {ac.SIGNS[ch.asc_sign]}: {ac.LAGNA_TRAITS[ch.asc_sign]}",
        f"Moon in {ac.SIGNS[moon['sign']]} (emotional nature): {ac.LAGNA_TRAITS[moon['sign']]}",
        f"Birth star {ac.NAKSHATRAS[moon['nak']]}: {NAK_TRAITS[moon['nak']]}.",
        f"Strongest planets: {', '.join(p for _, p in strengths[:3])}. "
        f"Weakest: {', '.join(p for _, p in strengths[-2:])}.",
    ]
    if yogas:
        summary.append("Notable combinations: " + ", ".join(y["name"] for y in yogas) + ".")
    best_md = [m for m in mds if m[2] > now_jd and m[1] < now_jd + 365.25 * 40]
    if best_md:
        top = max(best_md, key=lambda m: m[3])
        summary.append(f"Strongest life chapter ahead: {top[0]} Mahadasha "
                       f"({ac.jd_to_local(top[1], ch.tz).year}–{ac.jd_to_local(top[2], ch.tz).year}).")

    areas = {}

    # ---- Life (overall)
    a = _area(ch, {1: 2, 9: 1, 10: 0.7}, ["Sun", "Moon"])
    lord1 = ch.lord_of_house(1)
    a["details"] = [
        f"Ascendant lord {lord1} is in house {P[lord1]['house']} ({ac.HOUSE_THEMES[P[lord1]['house']]}): "
        f"life tends to centre on these themes.",
        f"Moon (mind) is in house {moon['house']} ({moon['dignity'].lower()}).",
        f"Atmakaraka (soul's focus): {ac.chara_karakas(ch)[0][1]}.",
    ]
    a["houses"] = {1, 9}
    areas["Life"] = a

    # ---- Health
    extra = []
    for p in ac.PLANETS:
        if P[p]["house"] in (1, 8) and p not in NATURAL_BENEFICS:
            extra.append((-0.5, f"{p} in house {P[p]['house']} points to care with {PLANET_HEALTH[p]}"))
    a = _area(ch, {1: 2, 6: 1, 8: 1}, ["Sun", "Moon"], extra)
    s6 = (ch.asc_sign + 5) % 12
    lord6 = ch.lord_of_house(6)
    sens = [BODY_BY_SIGN[ch.asc_sign], BODY_BY_SIGN[s6]]
    for p in ac.PLANETS:
        if P[p]["house"] in (1, 6, 8) and p not in NATURAL_BENEFICS:
            sens.append(PLANET_HEALTH[p])
    sens.append(PLANET_HEALTH[lord6])
    a["details"] = [
        "Areas to look after: " + "; ".join(dict.fromkeys(sens)) + ".",
        f"Mind and sleep: Moon is in house {moon['house']} ({moon['dignity'].lower()})"
        + (" (well supported)." if moon["house"] in KENDRA | TRIKONA | {11} else " (needs rest and routine)."),
        "Regular check-ups for these areas, steady sleep and exercise are the practical remedies.",
    ]
    a["houses"] = {1, 6, 8}
    areas["Health"] = a

    # ---- Career
    lord10 = ch.lord_of_house(10)
    amk = ac.chara_karakas(ch)[1][1]
    infl = [p for p in ac.PLANETS if P[p]["house"] == 10] + [lord10, amk]
    infl += [p for p in ac.PLANETS if P[p]["house"] == 11 and P[p]["dignity"] in ("Exalted", "Own sign")]
    infl += [p for p in ("Jupiter", "Saturn", "Mars") if 10 in ac.aspected_houses(p, P[p]["house"]) and P[p]["house"] != 10]
    infl = list(dict.fromkeys(infl))[:4]
    d10 = ac.varga_chart(ch, 10)
    l10_d10 = ac.dignity(lord10, d10[lord10])
    extra = [(1 if l10_d10 in ("Exalted", "Own sign") else -1 if l10_d10 == "Debilitated" else 0,
              f"In the career chart (D10), the 10th lord {lord10} is {l10_d10.lower()}")]
    a = _area(ch, {10: 2, 1: 0.7, 11: 0.7, 6: 0.4}, ["Sun", "Saturn"], extra)
    business = any(_connected(ch, p, {7}) for p in (lord10,)) or P["Mercury"]["dignity"] in ("Exalted", "Own sign") \
        or P["Rahu"]["house"] in (7, 10)
    a["details"] = [
        "Suitable fields: " + "; ".join(PLANET_CAREER[p] for p in infl) + ".",
        f"10th lord {lord10} is in house {P[lord10]['house']}: career is linked to "
        f"{ac.HOUSE_THEMES[P[lord10]['house']]}.",
        f"Amatyakaraka (career significator): {amk}.",
        ("Chart supports business or partnership-led work as well as senior roles."
         if business else "Chart favours a senior role or profession over a pure business venture."),
    ]
    a["houses"] = {10, 11}
    areas["Career"] = a

    # ---- Wealth
    dh = [y for y in yogas if y["name"].startswith(("Dhana", "Raja"))]
    extra = [(1.5, f"{y['name']}: {y['detail']}") for y in dh]
    a = _area(ch, {2: 1.5, 11: 1.5, 5: 0.7, 9: 0.7}, ["Jupiter", "Venus"], extra)
    lord2, lord11, lord4 = ch.lord_of_house(2), ch.lord_of_house(11), ch.lord_of_house(4)
    a["details"] = [
        f"Income (11th lord {lord11}) comes through {ac.HOUSE_THEMES[P[lord11]['house']]} "
        f"(house {P[lord11]['house']}).",
        f"Savings (2nd lord {lord2}) are linked to {ac.HOUSE_THEMES[P[lord2]['house']]} (house {P[lord2]['house']}).",
        f"Property (4th lord {lord4}) is {P[lord4]['dignity'].lower()} in house {P[lord4]['house']}"
        + (": good for owning property." if P[lord4]["dignity"] in ("Exalted", "Own sign") or P[lord4]["house"] in KENDRA | TRIKONA | {11}
           else ": property comes with effort."),
        ("Speculation: Mars or Saturn affliction suggests long-term investing over short-term trading."
         if any(P[p]["house"] in (5, 9) for p in ("Mars", "Saturn", "Rahu")) or P["Mars"]["dignity"] == "Debilitated"
         else "Speculation: no strong warning; still favour diversified, long-term investing."),
    ]
    a["houses"] = {2, 11}
    areas["Wealth"] = a

    # ---- Children
    d7 = ac.varga_chart(ch, 7)
    jd7 = ac.dignity("Jupiter", d7["Jupiter"])
    extra = [(0.5 if jd7 in ("Exalted", "Own sign", "Friendly sign") else -0.5 if jd7 in ("Debilitated", "Enemy sign") else 0,
              f"In the children chart (D7), Jupiter is {jd7.lower()}")]
    a = _area(ch, {5: 2, 9: 0.5}, ["Jupiter"], extra)
    lord5 = ch.lord_of_house(5)
    in5 = [p for p in ac.PLANETS if P[p]["house"] == 5]
    a["details"] = [
        f"5th lord {lord5} is in house {P[lord5]['house']}, {P[lord5]['dignity'].lower()}.",
        ("Planets in the 5th: " + ", ".join(in5) + ".") if in5 else "No planets in the 5th; the lord and Jupiter decide.",
        ("Children are likely to be a source of pride; education and values come through strongly."
         if a["stars"] >= 4 else "Children matters may need patience or extra care at times; "
                                  "Jupiter periods and transits through the 5th are the supportive times."),
    ]
    a["houses"] = {5}
    areas["Children"] = a

    # ---- Marriage
    mk = ac.manglik(ch)
    extra = []
    if P["Rahu"]["house"] in (1, 7) or P["Ketu"]["house"] in (1, 7):
        extra.append((-1, f"Rahu/Ketu across houses 1 and 7: restlessness or misunderstanding in partnership"))
    if mk["from_asc"]:
        extra.append((-0.5, f"Mars in house {mk['houses'][0]} (Mars dosha from the Ascendant)"))
    d9 = ac.varga_chart(ch, 9)
    sex = getattr(ch, "sex", "") or ""
    # Classical spouse significator: Venus for a man's wife, Jupiter for a woman's husband
    spouse_k = "Jupiter" if sex == "female" else "Venus"
    vd9 = ac.dignity(spouse_k, d9[spouse_k])
    extra.append((0.5 if vd9 in ("Exalted", "Own sign", "Friendly sign") else -0.5 if vd9 in ("Debilitated", "Enemy sign") else 0,
                  f"In the marriage chart (D9), {spouse_k} is {vd9.lower()}"))
    a = _area(ch, {7: 2, 2: 0.5, 4: 0.3}, ["Jupiter", "Venus"] if sex == "female" else ["Venus"], extra)
    s7 = (ch.asc_sign + 6) % 12
    lord7 = ch.lord_of_house(7)
    a["details"] = [
        f"Partner's nature ({ac.SIGNS[s7]} on the 7th): {ac.LAGNA_TRAITS[s7]}",
        f"7th lord {lord7} is in house {P[lord7]['house']}: the relationship is linked to "
        f"{ac.HOUSE_THEMES[P[lord7]['house']]}.",
        f"Darakaraka (spouse significator): {ac.chara_karakas(ch)[6][1]}.",
        "Mars dosha: " + ("present from the Ascendant" if mk["from_asc"] else "not from the Ascendant")
        + (", present from the Moon" if mk["from_moon"] else "") + ".",
        _spouse_line(ch, sex),
    ]
    a["houses"] = {7}
    areas["Marriage"] = a

    for name, a in areas.items():
        good, bad = _period_table(ch, periods, a["houses"], now_jd)
        a["good_periods"], a["hard_periods"] = good, bad

    events = periods + milestones(ch) + eclipse_hits(ch, now_jd)
    events.sort(key=lambda e: e["start"])
    return dict(summary=summary, areas=areas, events=events, chain=chain, strengths=strengths)
