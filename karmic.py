"""
Karmic synastry: traditional past-life indicators between two charts, written in plain language.

Signals used: shared rising or Moon sign; Jupiter, Saturn and the nodes (Rahu/Ketu) of one person
falling on the other's key points; Saturn on each other's rising sign; where each person's planets
fall in the other's houses (3rd, 4th, 5th, 6th, 10th and 12th in particular); each person's soul
planet (Atmakaraka); the star (Tara) match; and the Moon-sign relationship. Symbolic, not provable.
"""
from __future__ import annotations

import astro_core as ac

ORB = 6.0
AK_ROLE = {"Sun": "the leader or ruler", "Moon": "the caregiver and nurturer", "Mars": "the warrior and leader",
           "Mercury": "the merchant, scholar or messenger", "Jupiter": "the teacher and adviser",
           "Venus": "the artist or diplomat", "Saturn": "the dutiful worker or ascetic"}
POINT_NAME = {"Asc": "rising sign", "Moon": "Moon", "Sun": "Sun", "Venus": "Venus", "Mars": "Mars",
              "Mercury": "Mercury", "Jupiter": "Jupiter", "Saturn": "Saturn", "Rahu": "Rahu", "Ketu": "Ketu"}
HOUSE_AREA = {1: "self", 2: "family and money", 3: "helpers, siblings, execution", 4: "home, inner circle",
              5: "affection and past merit", 6: "rivalry and service", 7: "partnership", 8: "secrets and sudden change",
              9: "luck and guidance", 10: "career", 11: "gains and shared goals", 12: "past lives"}
TARA_PLAIN = {"Janma": "same-star", "Sampat": "prosperity", "Vipat": "obstacle", "Kshema": "well-being",
              "Pratyak": "opposition", "Sadhana": "achievement", "Naidhana": "danger", "Mitra": "friend",
              "Parama Mitra": "best friend"}
HARD = {"Mars", "Saturn", "Rahu", "Sun"}


def _pts(ch: ac.Chart) -> dict:
    d = {p: ch.planets[p]["lon"] for p in ac.PLANETS}
    d["Asc"] = ch.asc
    return d


def _sep(a: float, b: float) -> float:
    x = abs(a - b) % 360
    return min(x, 360 - x)


def _ord(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def _and(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def contacts(a: ac.Chart, b: ac.Chart, orb: float = ORB) -> list[dict]:
    """Close conjunctions/oppositions from a's Jupiter, Saturn and nodes to b's key points."""
    A, B = _pts(a), _pts(b)
    out = []
    for k in ("Jupiter", "Saturn", "Rahu", "Ketu"):
        for j, v in B.items():
            s = _sep(A[k], v)
            if s <= orb:
                out.append(dict(frm=a.name, planet=k, to=b.name, point=j, kind="on", orb=s))
            elif abs(s - 180) <= orb and k in ("Saturn",) and j in ("Rahu", "Ketu"):
                out.append(dict(frm=a.name, planet=k, to=b.name, point=j, kind="opposite", orb=abs(180 - s)))
    return out


def overlays(a: ac.Chart, b: ac.Chart) -> dict[int, list[str]]:
    """House of a's chart in which each of b's planets falls."""
    out: dict[int, list[str]] = {}
    for p in ac.PLANETS:
        if p == "Ketu":
            continue
        h = a.house_of_sign(b.planets[p]["sign"])
        out.setdefault(h, []).append(p)
    return out


def _overlay_lines(a: ac.Chart, b: ac.Chart) -> tuple[list[str], int, int]:
    """Plain sentences for b's planets in a's houses; returns (lines, ally points, rivalry points)."""
    ov = overlays(a, b)
    lines, ally, rival = [], 0, 0
    A, B = a.name, b.name

    def nm(ps):
        return f"{B}'s " + _and(ps)

    if ov.get(10):
        ps = ov[10]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 10th house (career).** {B} is linked to "
                     f"{A}'s career and status: a boss, patron or someone who raises {A}'s standing.")
        ally += 1
    if ov.get(4):
        ps = ov[4]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 4th house (home, inner circle).** "
                     f"{A} treats {B} like family and trusts {B} at a personal level.")
        ally += 1
    if ov.get(3):
        ps = ov[3]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 3rd house (helpers, siblings, execution).** "
                     f"{B} acts as {A}'s right hand: the one who gets things done and communicates.")
        ally += 1
    if ov.get(5):
        ps = ov[5]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 5th house (affection and past merit).** "
                     f"Real fondness carried over from before, not bad blood.")
        ally += 1
    if [p for p in ov.get(9, []) if p in ("Sun", "Moon", "Jupiter", "Venus")]:
        ps = ov[9]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 9th house (luck and guidance).** "
                     f"{B} brings {A} luck, advice or a sense of direction.")
        ally += 1
    if [p for p in ov.get(11, []) if p in ("Sun", "Moon", "Jupiter", "Venus", "Mercury")]:
        ps = ov[11]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 11th house (gains).** "
                     f"Working together brings income and fulfils shared goals.")
        ally += 1
    if [p for p in ov.get(7, []) if p in ("Moon", "Venus", "Sun", "Mars")]:
        ps = ov[7]
        lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 7th house (partnership).** "
                     f"A strong pull to work or live as partners.")
    if ov.get(6):
        ps = ov[6]
        hard = [p for p in ps if p in HARD or p == "Moon"]
        if hard:
            lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 6th house (conflict and competition).** "
                         + (f"{B}'s moods can feel to {A} like opposition." if hard == ["Moon"] else
                            f"This is the rivalry thread: {B} can feel like an opponent to {A} at times, "
                            f"and power struggles are possible."))
            rival += len(hard)
        else:
            lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 6th house (service).** "
                         f"{B} helps {A} solve problems and handle daily pressures.")
    if ov.get(8):
        ps = ov[8]
        hard = [p for p in ps if p in HARD]
        if hard:
            lines.append(f"**{nm(ps)} fall{'s' if len(ps) == 1 else ''} in {A}'s 8th house (secrets and sudden change).** "
                         f"The bond is intense and can unsettle {A}; keep things transparent.")
            rival += 1
    return lines[:4], ally, rival


def karmic_synastry(a: ac.Chart, b: ac.Chart) -> dict:
    A, B = a.name, b.name
    bond, roles_lines, cautions = [], [], []
    ally = rival = duty = 0

    # Shared signs
    if a.asc_sign == b.asc_sign:
        bond.append(f"**The same rising sign ({ac.SIGNS[a.asc_sign]}).** {A} and {B} see the world the same way and "
                    f"recognise each other quickly. A shared rising sign is one of the classic signs of a bond carried "
                    f"over from before.")
        ally += 2
    if a.moon_sign == b.moon_sign:
        bond.append(f"**The same Moon sign ({ac.SIGNS[a.moon_sign]}).** Their emotional rhythms match, which reads as "
                    f"an old, familiar closeness.")
        ally += 1

    # Contacts both ways
    cs = contacts(a, b) + contacts(b, a)
    for c in sorted(cs, key=lambda c: c["orb"]):
        f, t, pl, pt, o = c["frm"], c["to"], c["planet"], c["point"], c["orb"]
        tgt = a if t == A else b
        if pl == "Jupiter" and pt in ("Asc", "Moon", "Sun"):
            bond.append(f"**{f}'s Jupiter sits within {o:.0f}° of {t}'s {POINT_NAME[pt]}.** Jupiter is the guide and "
                        f"protector. In this life {f} opens doors for {t}, and traditionally that means {f} was "
                        f"{t}'s patron or protector before.")
            ally += 2
        elif pl == "Saturn" and pt == "Asc":
            pass  # handled as a pair below
        elif pl == "Saturn" and pt in ("Rahu", "Ketu"):
            h = tgt.house_of_sign(tgt.planets["Rahu"]["sign"])
            extra = (f" Being in {t}'s 12th house, the house of past lives, suggests the bond formed away from home: "
                     f"in another land, a court, or a temple or ashram setting." if h == 12 or
                     tgt.house_of_sign(tgt.planets["Ketu"]["sign"]) == 12 else "")
            if not any("past-life axis" in x for x in bond):
                bond.append(f"**Saturn tied to the past-life axis.** {f}'s Saturn sits within {o:.0f}° of {t}'s "
                            f"{'Rahu, opposite ' + t + chr(39) + 's Ketu' if pt == 'Rahu' else 'Ketu, opposite ' + t + chr(39) + 's Rahu'}"
                            f" (Ketu is the past-life point). Saturn here means a duty or debt between them that this "
                            f"life is settling.{extra}")
                duty += 2
        elif pl == "Saturn" and pt in ("Mars", "Sun", "Moon", "Venus"):
            meaning = {"Mars": f"{f} brings structure and restraint to {t}'s drive: the voice that says \"plan it first\".",
                       "Sun": f"{f} disciplines {t}'s ego and authority; respect can feel like pressure.",
                       "Moon": f"{f} can make {t} feel judged or weighed down emotionally; warmth helps.",
                       "Venus": f"a serious, loyal attachment, though affection may be shown sparingly."}[pt]
            roles_lines.append(f"**{f}'s Saturn sits on {t}'s {pt} ({o:.0f}°).** {meaning[0].upper() + meaning[1:]}")
            duty += 1
        elif pl in ("Rahu", "Ketu") and pt in ("Asc", "Moon", "Sun", "Venus"):
            word = "Rahu (the future and desire)" if pl == "Rahu" else "Ketu (the past)"
            bond.append(f"**{f}'s {word} sits within {o:.0f}° of {t}'s {POINT_NAME[pt]}.** "
                        + ("A magnetic, fated pull: they are drawn together to finish something."
                           if pl == "Rahu" else "A strong feeling of having known each other before."))
            duty += 1

    sat_asc = [c for c in cs if c["planet"] == "Saturn" and c["point"] == "Asc"]
    if sat_asc:
        if len(sat_asc) == 2:
            o1, o2 = sorted(c["orb"] for c in sat_asc)
            bond.append(f"**Saturn on each other's rising sign, both ways** (within {o1:.0f}° and {o2:.0f}°). Two-way "
                        f"Saturn contacts this close are rare. Traditionally they mean unfinished business from a past "
                        f"life: a debt or duty they came back to settle. The relationship can feel heavy and serious "
                        f"at times, but it rarely breaks easily.")
            duty += 3
            cautions.append("Each can feel controlled or judged by the other; warmth and appreciation balance the "
                            "Saturn weight.")
        else:
            c = sat_asc[0]
            bond.append(f"**{c['frm']}'s Saturn sits on {c['to']}'s rising sign ({c['orb']:.0f}°).** A sense of duty and "
                        f"commitment; {c['frm']} feels responsible for {c['to']}.")
            duty += 2

    # 12th house links
    for x, y in ((a, b), (b, a)):
        h_asc = x.house_of_sign(y.asc_sign)
        h_ketu = x.house_of_sign(y.planets["Ketu"]["sign"])
        if h_asc == 12 or h_ketu == 12:
            what = _and([w for w, h in (("rising sign", h_asc), ("Ketu (the past-life point)", h_ketu)) if h == 12])
            bond.append(f"**{y.name}'s {what} fall{'s' if ' and ' not in what else ''} in {x.name}'s 12th house, the "
                        f"house of past lives.** A connection from before, possibly hidden or involving sacrifice for "
                        f"each other.")
            duty += 1

    # Soul planets
    aka, bka = ac.chara_karakas(a)[0][1], ac.chara_karakas(b)[0][1]
    roles_lines.insert(0, f"**Soul planets (Atmakaraka):** {A}'s is {aka}, {AK_ROLE[aka]}. {B}'s is {bka}, "
                          f"{AK_ROLE[bka]}.")

    # Overlays both ways
    l1, al1, rv1 = _overlay_lines(a, b)
    l2, al2, rv2 = _overlay_lines(b, a)
    roles_lines += l1 + l2
    ally += al1 + al2
    rival += rv1 + rv2

    # Tara and Moon relation
    sy = ac.synastry(a, b, 5.0)
    ta, tb = sy["tara_a_to_b"][0], sy["tara_b_to_a"][0]
    good_t = sum(1 for t in (ta, tb) if t in ("Sampat", "Kshema", "Sadhana", "Mitra", "Parama Mitra"))
    star_line = (f"**The star match:** \"{TARA_PLAIN.get(ta, ta)}\" ({ta}) from {A}'s side and "
                 f"\"{TARA_PLAIN.get(tb, tb)}\" ({tb}) from {B}'s side"
                 + (", two of the best possible." if good_t == 2 else "." if good_t == 1 else
                    ", which asks for patience with each other."))
    roles_lines.append(star_line)
    ally += good_t
    mr = sy["moon_relation"]
    if mr.startswith("2/12"):
        cautions.insert(0, "Their Moon signs are 2/12 apart: mixing money casually can cause friction, so keep "
                           "financial arrangements, roles and shares clearly written, even with high trust.")
    elif mr.startswith("6/8"):
        cautions.insert(0, "Their Moon signs are 6/8 apart: emotional misunderstandings come easily, so agree "
                           "things clearly and do not let small hurts pile up.")
        rival += 1
    if rival >= 2:
        cautions.append("The rivalry thread shows up as arguments and each trying to win. They do better as a team "
                        "than as opponents.")

    # Verdict and story
    ov_ab, ov_ba = overlays(a, b), overlays(b, a)
    W = {"Sun": 2, "Mars": 1, "Venus": 1}
    # ov_ab = b's planets in a's houses; ov_ba = a's planets in b's houses
    lead_a = sum(W.get(p, 0) for p in ov_ba.get(10, []))  # a's planets in b's 10th: a leads b
    lead_b = sum(W.get(p, 0) for p in ov_ab.get(10, []))
    leader = (A, B) if lead_a > lead_b else (B, A) if lead_b > lead_a else None
    guide = None
    for x, y, ov in ((a, b, ov_ba), (b, a, ov_ab)):  # ov = x's planets in y's houses
        if "Jupiter" in ov.get(10, []) or any(c["frm"] == x.name and c["planet"] == "Jupiter" and c["point"] == "Asc"
                                              for c in cs):
            guide = (x.name, y.name)
    sib = any(p in ("Sun", "Mars", "Mercury") for p in ov_ab.get(3, []) + ov_ba.get(3, []))
    fam = bool(ov_ab.get(4) or ov_ba.get(4))
    love = any(p in ("Venus", "Moon") for p in ov_ab.get(7, []) + ov_ba.get(7, []) + ov_ab.get(5, []) + ov_ba.get(5, []))
    parts = []
    if leader:
        x, y = leader
        parts.append(f"a leader or ruler ({x}) and a trusted adviser or minister ({y})")
    elif guide:
        x, y = guide
        parts.append(f"a teacher or guide ({x}) and a student or follower ({y})")
    if sib or fam:
        parts.append("two brothers or close kin who served together" if sib else "members of the same household")
    if love and not parts:
        parts.append("partners or companions with real affection")
    if rival >= 2:
        parts.append("people who were once on opposite sides")
    if rival >= 2 and duty >= 3:
        parts = ["rivals, or people on opposite sides, tied together by an unfinished duty"]
    story = ("The likely past-life story: " + (", or ".join(parts) if parts else "two people bound by shared work and duty")
             + (". There was a duty left unfinished" if duty >= 2 and not (rival >= 2 and duty >= 3) else "")
             + (", possibly connected to a foreign place or an institution" if any("12th house" in x for x in bond) else "")
             + ", and they have come back to " + ("build something together again." if rival < 2 else
                                                  "turn old rivalry into partnership."))
    if rival >= 2 and duty >= 3:
        verdict, tone = "Bound by duty, with a thread of rivalry", "mixed"
        headline = (f"By the traditional past-life signs, {A} and {B} were mainly bound by duty, not enemies. "
                    f"There is one thread of rivalry, and that is what shows up as their arguments.")
    elif rival >= 2 and ally <= rival + 1:
        verdict, tone = "Old rivals, now bound by duty", "mixed"
        headline = (f"By the traditional past-life signs, {A} and {B} carry a thread of rivalry from before, held "
                    f"together by a strong sense of duty. The bond is real; the friction is the part to work on.")
    elif duty >= 3 and ally < 4:
        verdict, tone = "Bound by duty", "mixed"
        headline = (f"By the traditional past-life signs, {A} and {B} were mainly bound by duty, not enmity: "
                    f"a debt or responsibility they came back to settle.")
    else:
        verdict, tone = "Allies from before", "good"
        headline = (f"By the traditional past-life signs, {A} and {B} were allies"
                    + (f", most likely {parts[0]}" if parts else "") + ". There is little sign of enmity.")
    detail = past_life_story(a, b)
    story = "The likely past-life story: " + detail["text"]
    return dict(verdict=verdict, tone=tone, headline=headline, bond=bond, roles=roles_lines, story=story,
                story_detail=detail,
                cautions=cautions, scores=dict(ally=ally, duty=duty, rival=rival), contacts=cs,
                overlays=dict(a_in_b=ov_ab, b_in_a=ov_ba))


# ---------------------------------------------------------------------------
# Detailed past-life story built from each pair's own signals
# ---------------------------------------------------------------------------
ROLE_NOUN = {"Sun": "a ruler or royal official", "Moon": "a caretaker or keeper of the household",
             "Mars": "a commander or warrior", "Mercury": "a merchant, scribe or messenger",
             "Jupiter": "a teacher, priest or counsellor", "Venus": "an artist, courtier or companion",
             "Saturn": "a loyal servant, labourer or ascetic"}
SETTING = {12: "away from home: in a foreign land, a temple or ashram, or a large institution",
           10: "in a royal court or seat of government",
           9: "around a temple, a school of learning or a pilgrimage",
           4: "in the same home or homeland",
           6: "in an army, a hospital or a life of service",
           8: "in a hidden world of secrets, healing or inheritance",
           7: "in a marriage or a trading partnership",
           5: "in a school, a place of art or around children",
           3: "on the road: soldiers, messengers or travelling traders",
           11: "in a guild, trade network or circle of patrons",
           2: "in a family business or one family line",
           1: "in the same family or clan"}
UNFINISHED = {1: "a promise about each other's well-being", 2: "a family or money obligation",
              3: "a task or campaign they started together", 4: "a duty to a home or family",
              5: "a duty to children or students", 6: "a debt or a dispute that was never settled",
              7: "a partnership or marriage vow", 8: "a secret or an inheritance left unresolved",
              9: "a vow to a teacher, faith or father figure", 10: "a public duty or a mission at work",
              11: "a shared goal that was never reached", 12: "a sacrifice or a journey left incomplete"}


def _house_in(target: ac.Chart, lon: float) -> int:
    return target.house_of_sign(ac.sign_of(lon))


def past_life_story(a: ac.Chart, b: ac.Chart) -> dict:
    """A specific story for this pair: roles, relationship, setting, debts and this life's task."""
    A, B = a.name, b.name
    aka, bka = ac.chara_karakas(a)[0][1], ac.chara_karakas(b)[0][1]
    adk, bdk = ac.chara_karakas(a)[-1][1], ac.chara_karakas(b)[-1][1]
    ov_ab, ov_ba = overlays(a, b), overlays(b, a)   # b's planets in a's houses; a's planets in b's houses
    cs = contacts(a, b) + contacts(b, a)
    house_votes: dict[int, float] = {}

    def vote(h, w):
        house_votes[h] = house_votes.get(h, 0) + w

    # 1. Roles from soul planets
    roles = (f"{A} was {ROLE_NOUN[aka]} (soul planet {aka}), and {B} was {ROLE_NOUN[bka]} (soul planet {bka})."
             if aka != bka else f"Both {A} and {B} were {ROLE_NOUN[aka].replace('a ', '', 1)}s at heart (both have "
             f"soul planet {aka})." if False else
             f"{A} and {B} share the same soul planet, {aka}: both carry the nature of {ROLE_NOUN[aka]}.")

    # 2. Nature of the bond, from where the personal planets fall
    def falls(x_ov, planets, houses):
        return [p for h in houses for p in x_ov.get(h, []) if p in planets]
    kind, why = None, ""
    love = falls(ov_ab, {"Venus", "Moon", "Mars"}, (5, 7)) + falls(ov_ba, {"Venus", "Moon", "Mars"}, (5, 7))
    heart = "Venus" in love and len(set(love)) >= 2   # needs Venus plus another personal planet
    dk_link = (a.planets[adk]["sign"] in (b.planets["Moon"]["sign"], b.planets["Venus"]["sign"], b.asc_sign) or
               b.planets[bdk]["sign"] in (a.planets["Moon"]["sign"], a.planets["Venus"]["sign"], a.asc_sign))
    lead_a = falls(ov_ba, {"Sun", "Mars", "Venus"}, (10,))   # a's planets in b's 10th
    lead_b = falls(ov_ab, {"Sun", "Mars", "Venus"}, (10,))
    sib = falls(ov_ab, {"Mars", "Mercury", "Sun"}, (3, 11)) + falls(ov_ba, {"Mars", "Mercury", "Sun"}, (3, 11))
    fam_ab, fam_ba = falls(ov_ab, {"Sun", "Moon"}, (4, 9)), falls(ov_ba, {"Sun", "Moon"}, (4, 9))
    guide = [x for x, y in ((A, B), (B, A)) if any(c["frm"] == x and c["planet"] == "Jupiter"
                                                    and c["point"] in ("Asc", "Moon", "Sun") for c in cs)]
    guide += [x.name for x, ov in ((a, ov_ba), (b, ov_ab))      # x's Jupiter in the other's 9th or 10th
              if any(p == "Jupiter" for h in (9, 10) for p in ov.get(h, [])) and x.name not in guide]
    if heart and dk_link:
        kind = "a bond of the heart: close family or the dearest of companions"
        why = (f"({_and(sorted(set(love)))} fall in each other's houses of love and partnership, "
               f"and the partner planet links them)")
        vote(7, 2)
    elif lead_a or lead_b:
        x, y = (A, B) if len(lead_a) >= len(lead_b) else (B, A)
        ps = lead_a if x == A else lead_b
        kind = f"a leader and a trusted right hand, with {x} in charge"
        why = f"({x}'s {_and(ps)} fall{'s' if len(ps) == 1 else ''} in {y}'s 10th house of career and authority)"
        vote(10, 2)
    elif guide:
        x = guide[0]
        y = B if x == A else A
        kind = f"a teacher and a student, with {x} as the guide"
        why = f"({x}'s Jupiter, the planet of the guru, is tied to {y}'s chart)"
        vote(9, 2)
    elif fam_ab or fam_ba:
        kind = "parent and child, or an elder and the one they raised"
        why = "(the Sun or Moon of one falls in the other's 4th or 9th house)"
        vote(4, 2)
    elif sib:
        kind = "brothers, or comrades who fought and worked side by side"
        why = f"({_and(sorted(set(sib)))} link{'s' if len(set(sib)) == 1 else ''} their 3rd and 11th houses of siblings and allies)"
        vote(3, 2)
    elif love:
        kind = "close companions with real affection"
        why = (f"({_and(sorted(set(love)))} fall{'s' if len(set(love)) == 1 else ''} in each other's houses of "
               f"affection and partnership)")
        vote(5, 1)
    else:
        kind = "co-workers bound by a shared duty"
        why = ""
    bond = f"They were most likely {kind} {why}".strip() + "."

    # 3. Setting, from where the strongest links fall
    for c in cs:
        tgt = a if c["to"] == A else b
        if c["planet"] in ("Saturn", "Rahu", "Ketu", "Jupiter"):
            vote(_house_in(tgt, _pts(tgt)[c["point"]]), 1.5)
    for h, ps in list(ov_ab.items()) + list(ov_ba.items()):
        for p in ps:
            vote(h, 1.0 if p in ("Sun", "Moon", "Saturn", "Jupiter", "Rahu") else 0.5)
    for x, y in ((a, b), (b, a)):
        if x.house_of_sign(y.asc_sign) == 12 or x.house_of_sign(y.planets["Ketu"]["sign"]) == 12:
            vote(12, 2)
    top = sorted(house_votes, key=lambda h: -house_votes[h])
    setting = f"The bond played out {SETTING[top[0]]}"
    if len(top) > 1 and house_votes[top[1]] >= house_votes[top[0]] * 0.75 and top[1] != top[0]:
        setting += f", with ties {SETTING[top[1]].split(':')[0].replace('away from home', 'far from home')}"
    setting += "."

    # 4. Inner circle and protection
    extra = []
    for x, y, ov in ((a, b, ov_ab), (b, a, ov_ba)):   # ov: y's planets in x's houses
        inner = [p for p in ov.get(4, []) if p in ("Sun", "Moon", "Venus", "Jupiter")]
        if inner:
            extra.append(f"{y.name} was treated as part of {x.name}'s household, not as hired help "
                         f"({y.name}'s {_and(inner)} in {x.name}'s 4th house).")
    for c in cs:
        if c["planet"] == "Jupiter" and c["point"] in ("Asc", "Moon", "Sun"):
            extra.append(f"{c['frm']} protected and sponsored {c['to']} ({c['frm']}'s Jupiter on "
                         f"{c['to']}'s {POINT_NAME[c['point']]}).")
            break

    # 5. What was left unfinished, from Saturn and Ketu links
    unfinished = None
    for c in sorted(cs, key=lambda c: c["orb"]):
        if c["planet"] == "Saturn":
            tgt = a if c["to"] == A else b
            h = _house_in(tgt, _pts(tgt)[c["point"]])
            unfinished = (f"Saturn links them in {c['to']}'s {_ord(h)} house, which points to {UNFINISHED[h]}: "
                          f"this life is the chance to settle it.")
            break
    if not unfinished:
        for c in sorted(cs, key=lambda c: c["orb"]):
            if c["planet"] == "Ketu":
                unfinished = (f"{c['frm']}'s Ketu on {c['to']}'s {POINT_NAME[c['point']]} gives a strong sense "
                              f"of having known each other before; the old bond picks up where it left off.")
                break

    # 6. Friction
    hard6 = [p for p in ov_ab.get(6, []) + ov_ba.get(6, []) if p in HARD]
    friction = ("At times they were on opposite sides, and that rivalry can still flare up "
                f"({_and(sorted(set(hard6)))} in each other's 6th house of conflict)." if len(hard6) >= 2 else None)

    # 7. This life
    rahu = [c for c in cs if c["planet"] == "Rahu"]
    task = ("In this life the pull is forward: they are drawn together to build something new, "
            f"not only to repeat the past ({rahu[0]['frm']}'s Rahu on {rahu[0]['to']}'s {POINT_NAME[rahu[0]['point']]})."
            if rahu else "In this life they meet again to complete the work and strengthen the bond.")

    parts = [roles, bond, setting] + extra + ([unfinished] if unfinished else []) + ([friction] if friction else []) + [task]
    return dict(text=" ".join(parts), roles=roles, bond=bond, setting=setting, extra=extra,
                unfinished=unfinished, friction=friction, task=task, setting_house=top[0])
