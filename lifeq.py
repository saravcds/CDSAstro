"""
Life Questions: when is something likely to happen?

Three classical layers, all of which must agree for a strong window:
1. Promise   - is the matter shown in the birth chart? (house, its lord, the karaka, the divisional chart)
2. Activation - does the running Vimshottari dasha connect to that matter?
3. Trigger   - do Jupiter and Saturn both touch the house or its lord by transit (the double transit,
               as taught by B.V. Raman and K.N. Rao), refined by Ashtakavarga points.
Double transit sets the year and the theme, not the week; the dasha says whether that year is ripe.
"""
from __future__ import annotations

import astro_core as ac
import life

JUP_ASP = (1, 5, 7, 9)      # Jupiter: its own sign and 5th, 7th, 9th from it
SAT_ASP = (1, 3, 7, 10)     # Saturn: own sign and 3rd, 7th, 10th
NODE_ASP = (1, 5, 7, 9)

TOPICS = {
    "marriage": dict(title="Marriage or a committed relationship", houses=[7], support=[2, 11],
                     karakas=["Venus"], varga=9, kind="good",
                     do="Meet families, propose, fix the engagement or wedding date (pick the day with the Muhurta finder).",
                     avoid="Rushing a decision under family pressure; hiding facts from the other side.",
                     happened="If already married, these windows bring important developments in the marriage: "
                              "a deeper bond, a move, or a family event."),
    "career": dict(title="Career rise, promotion or job change", houses=[10], support=[6, 11],
                   karakas=["Sun", "Saturn"], varga=10, kind="good",
                   do="Ask for the promotion, apply for the role, take on visible responsibility.",
                   avoid="Quitting in anger before the new role is confirmed in writing.",
                   happened=""),
    "business": dict(title="Business growth and new clients", houses=[7, 10], support=[11, 3],
                     karakas=["Mercury"], varga=10, kind="good",
                     do="Pitch, sign new clients, open a new line or location, raise funds.",
                     avoid="Partnerships without written terms; over-expanding on borrowed money.",
                     happened=""),
    "wealth": dict(title="Money, savings and gains", houses=[2, 11], support=[5, 9],
                   karakas=["Jupiter"], varga=None, kind="good",
                   do="Collect dues, invest for the long term, negotiate fees or salary.",
                   avoid="Speculation and lending large sums without security.",
                   happened=""),
    "property": dict(title="Property, home or vehicle", houses=[4], support=[11, 2],
                     karakas=["Mars", "Venus", "Moon"], varga=4, kind="good",
                     do="Buy or register property, start construction, move house, buy a vehicle.",
                     avoid="Skipping legal checks on title and approvals; stretching the loan.",
                     happened=""),
    "children": dict(title="Children (conception, birth, their milestones)", houses=[5], support=[9],
                     karakas=["Jupiter"], varga=7, kind="good",
                     do="Plan for a child, medical consultations, children's admissions and milestones.",
                     avoid="Stress and irregular routines; ignoring medical advice.",
                     happened="If you already have children, these windows bring good news through them."),
    "foreign": dict(title="Foreign travel or settling abroad", houses=[12, 9], support=[3, 7],
                    karakas=["Rahu"], varga=None, kind="good",
                    do="Apply for visas, foreign assignments, overseas clients or a move abroad.",
                    avoid="Incomplete paperwork; leaving family matters unsettled before a long move.",
                    happened=""),
    "education": dict(title="Higher studies, learning and qualifications", houses=[4, 5, 9], support=[],
                      karakas=["Mercury", "Jupiter"], varga=None, kind="good",
                      do="Enrol in a course, sit exams, start research or a certification.",
                      avoid="Taking on too many courses at once.",
                      happened=""),
    "health": dict(title="Health: periods to take extra care", houses=[6, 8], support=[1],
                   karakas=["Sun"], varga=None, kind="care",
                   do="Regular check-ups, a steady routine, rest and lighter food.",
                   avoid="Ignoring symptoms, risky sports, rash driving, alcohol.",
                   happened=""),
}
LEVEL_ORDER = {"Strong": 3, "Good": 2, "Possible": 1}


def _sign_of_house(ch: ac.Chart, h: int, from_moon: bool = False) -> int:
    base = ch.moon_sign if from_moon else ch.asc_sign
    return (base + h - 1) % 12


def _touch(sign_pl: int, offsets: tuple, targets: set) -> bool:
    return any((sign_pl + o - 1) % 12 in targets for o in offsets)


def _karakas(ch: ac.Chart, key: str) -> list[str]:
    k = list(TOPICS[key]["karakas"])
    if key == "marriage" and getattr(ch, "sex", "") == "female":
        k = ["Jupiter", "Venus"]
    return k


def promise(ch: ac.Chart, key: str) -> dict:
    t = TOPICS[key]
    hs, notes = [], []
    for h in t["houses"]:
        s, n = life.house_strength(ch, h)
        hs.append(s)
        notes += n
    ks = [life.planet_strength(ch, k) for k in _karakas(ch, key)]
    vpts, vtxt = 0.0, ""
    if t["varga"]:
        v = ac.varga_chart(ch, t["varga"])
        lord = ch.lord_of_house(t["houses"][0])
        dg = ac.dignity(lord, v[lord])
        vpts = 1 if dg in ("Exalted", "Own sign", "Friendly sign") else -1 if dg in ("Debilitated", "Enemy sign") else 0
        vtxt = f"In the D{t['varga']} chart, the {ordinal(t['houses'][0])} lord {lord} is {dg.lower()}."
    score = 50 + 4 * (sum(hs) / len(hs)) + 5 * (sum(ks) / len(ks)) + 6 * vpts
    if t["kind"] == "care":  # for health, a strong 6th/8th means fewer problems
        score = 100 - score
    score = int(max(5, min(95, score)))
    pos = [x for _, x in sorted([n for n in notes if n[0] > 0], key=lambda n: -n[0])][:3]
    neg = [x for _, x in sorted([n for n in notes if n[0] < 0], key=lambda n: n[0])][:2]
    if vtxt:
        (pos if vpts > 0 else neg if vpts < 0 else pos).append(vtxt)
    kd = ", ".join(f"{k} ({_strength_word(s)})" for k, s in zip(_karakas(ch, key), ks))
    if t["kind"] == "care":
        label = "Low risk" if score >= 65 else "Moderate" if score >= 45 else "Needs attention"
    else:
        label = "Strong promise" if score >= 65 else "Moderate promise" if score >= 45 else "Weak: needs effort"
    return dict(score=score, label=label, helps=pos, hinders=neg, karakas=kd)


def _strength_word(s: float) -> str:
    return "strong" if s >= 2 else "weak" if s <= -1 else "average"


def ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def significators(ch: ac.Chart, key: str) -> tuple[set, set]:
    t = TOPICS[key]
    prim, sup = set(), set()
    for h in t["houses"]:
        prim.add(ch.lord_of_house(h))
        prim |= {p for p in ac.PLANETS if ch.planets[p]["house"] == h}
    prim |= set(_karakas(ch, key))
    for h in t["support"]:
        sup.add(ch.lord_of_house(h))
    for n in ("Rahu", "Ketu"):   # a node gives the results of the lord of the sign it occupies
        if ac.SIGN_LORD[ch.planets[n]["sign"]] in prim:
            sup.add(n)
    return prim, sup - prim


def _activation(ch, key, prim, sup, chain) -> tuple[float, bool, list[str]]:
    """Returns (score, sub-period lord directly linked?, reasons)."""
    t = TOPICS[key]
    md, ad = chain[0].lord, chain[1].lord
    act, why = 0.0, []
    for L, w, name in ((md, 1.0, "main period"), (ad, 1.5, "sub-period")):
        if L in prim:
            act += 2 * w
            why.append(f"{L} {name} is directly linked to this matter")
        elif L in sup:
            act += 1 * w
            why.append(f"{L} {name} supports this matter")
    if len(chain) > 2 and chain[2].lord in prim:
        act += 0.5
    if t["kind"] == "good" and ad not in prim:
        rel = (ch.planets[ad]["house"] - t["houses"][0]) % 12 + 1
        if rel in (6, 8, 12):
            act -= 1
    return act, (ad in prim or ad in sup), why


def _trigger(ch, key, jd) -> tuple[float, list[str], int]:
    """Returns (score, reasons, tier): tier 2 = double transit on the house itself,
    1 = double transit on house or lord, 0 = none."""
    t = TOPICS[key]
    h0 = t["houses"][0]
    js = ac.sign_of(ac.sidereal_lon(jd, "Jupiter", ch.ayanamsa)[0])
    ss = ac.sign_of(ac.sidereal_lon(jd, "Saturn", ch.ayanamsa)[0])
    rs = ac.sign_of(ac.sidereal_lon(jd, "Rahu", ch.ayanamsa, ch.node)[0])
    house_sg = {_sign_of_house(ch, h) for h in t["houses"]}
    lord_sg = {ch.planets[ch.lord_of_house(h)]["sign"] for h in t["houses"]}
    if t["kind"] == "care":
        hot = house_sg | {ch.asc_sign, ch.moon_sign}
        st2, rt = _touch(ss, SAT_ASP, hot), _touch(rs, NODE_ASP, hot)
        jp = _touch(js, JUP_ASP, {ch.asc_sign, ch.moon_sign})
        trig, why = 0.0, []
        if st2:
            trig += 1.2
            why.append("Saturn presses on your health points")
        if rt:
            trig += 0.8
            why.append("Rahu or Ketu stir your health points")
        if jp:
            trig -= 0.8
            why.append("Jupiter protects (softens the effect)")
        return trig, why, 2 if trig >= 2 else 1 if trig >= 1.2 else 0
    jh, sh = _touch(js, JUP_ASP, house_sg), _touch(ss, SAT_ASP, house_sg)
    jl, sl = _touch(js, JUP_ASP, lord_sg), _touch(ss, SAT_ASP, lord_sg)
    trig, why, tier = 0.0, [], 0
    names = " / ".join(ordinal(h) for h in t["houses"])
    if jh and sh:
        trig, tier = 2.0, 2
        why.append(f"Jupiter and Saturn both touch your {names} house (double transit)")
    elif (jh or jl) and (sh or sl):
        trig, tier = 1.3, 1
        why.append(f"Jupiter and Saturn both touch your {names} house or its lord")
    elif jh or jl:
        trig = 0.6
        why.append("Jupiter supports this area by transit")
    elif sh or sl:
        trig = 0.3
    moon_sg = {_sign_of_house(ch, h, True) for h in t["houses"]}
    if _touch(js, JUP_ASP, moon_sg) and _touch(ss, SAT_ASP, moon_sg):
        trig += 0.4
        if tier:
            why[-1] += "; confirmed from the Moon too"
    av = ac.ashtakavarga(ch)
    if jh or jl:
        b = av["bav"]["Jupiter"][js]
        trig += 0.4 if b >= 5 else 0.1 if b == 4 else -0.4
        if b >= 5:
            why.append(f"Jupiter transits a well-supported sign ({b} of 8 points)")
        elif b <= 3:
            why.append(f"Jupiter's transit sign is weakly supported ({b} of 8): results need more effort")
    if sh or sl:
        b = av["bav"]["Saturn"][ss]
        trig += 0.3 if b >= 4 else -0.3
    if key == "foreign" and _touch(rs, NODE_ASP, house_sg):
        trig += 0.5
        why.append("Rahu, the planet of foreign lands, touches this area")
    return trig, why, tier


def windows(ch: ac.Chart, md_list: list, key: str, now_jd: float, years: int = 10) -> list[dict]:
    prim, sup = significators(ch, key)
    months = []
    for i in range(years * 12):
        jd = now_jd + i * 30.44
        chain = ac.current_chain(md_list, jd)
        if len(chain) < 2:
            continue
        act, ad_linked, awhy = _activation(ch, key, prim, sup, chain)
        trig, twhy, tier = _trigger(ch, key, jd)
        lvl = None
        if ad_linked and act >= 3 and tier == 2 and trig >= 2:
            lvl = "Strong"
        elif ad_linked and act >= 2.5 and (tier >= 1 or trig >= 1):
            lvl = "Good"
        elif ad_linked and act >= 1.5 and trig >= 0.6:
            lvl = "Possible"
        months.append(dict(jd=jd, lvl=lvl, score=act * (0.5 + max(trig, 0)), ad=(chain[0].lord, chain[1].lord),
                           why=awhy + twhy))
    out, cur = [], None
    for m in months:
        same = cur and m["lvl"] and m["ad"] == cur["ad"] and m["jd"] - cur["end"] < 40
        if same:
            cur["end"] = m["jd"] + 15
            if m["score"] > cur["score"]:
                cur["score"], cur["peak"] = m["score"], m["jd"]
            cur["n"] += 1
            if LEVEL_ORDER[m["lvl"]] > LEVEL_ORDER[cur["level"]]:
                cur["level"], cur["why"] = m["lvl"], m["why"]
            continue
        if cur:
            out.append(cur)
        cur = dict(start=m["jd"] - 15, end=m["jd"] + 15, level=m["lvl"], score=m["score"], why=m["why"],
                   ad=m["ad"], n=1, peak=m["jd"]) if m["lvl"] else None
    if cur:
        out.append(cur)
    for w in out:
        w["chain"] = w.pop("ad")
    best = sorted(out, key=lambda w: (-LEVEL_ORDER[w["level"]], -w["score"], w["start"]))[:5]
    return sorted(best, key=lambda w: w["start"])


def answer(ch: ac.Chart, md_list: list, key: str, now_jd: float, years: int = 10) -> dict:
    t = TOPICS[key]
    pr = promise(ch, key)
    ws = windows(ch, md_list, key, now_jd, years)
    nxt = next((w for w in ws if w["level"] in ("Strong", "Good")), ws[0] if ws else None)
    return dict(key=key, title=t["title"], kind=t["kind"], promise=pr, windows=ws, next=nxt,
                do=t["do"], avoid=t["avoid"], happened=t["happened"])
