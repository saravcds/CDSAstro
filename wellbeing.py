"""
Happiness guide and What-to-avoid guide.

Happiness: what truly feeds this person (Moon, 4th, 5th, 9th, 11th), the best day and hour to use,
the soul's lesson (Atmakaraka), the Ishta Devata, and a gentle remedies ladder
(behaviour -> service and charity -> mantra -> gemstone, the last only for strong functional benefics).

Avoid: difficult periods ahead, Saturn phases, habits linked to weak or troublesome planets,
simple decision rules, and relationships among saved profiles that need extra patience.
"""
from __future__ import annotations

import astro_core as ac
import life
import pastlife
import shadbala
import simple_text as T

MOON_JOY = [
    "action, sport and being first at something new",        # Aries
    "good food, music, nature and a comfortable home",        # Taurus
    "conversation, reading, short trips and learning",        # Gemini
    "family, home cooking and caring for loved ones",         # Cancer
    "recognition, creative self-expression and generosity",   # Leo
    "being useful, order, health routines and craft",         # Virgo
    "beauty, art, harmony and good company",                  # Libra
    "depth: research, privacy and a few trusted bonds",       # Scorpio
    "travel, philosophy, teaching and open spaces",           # Sagittarius
    "achievement, structure and steady progress",             # Capricorn
    "friends, causes, ideas and freedom",                     # Aquarius
    "music, prayer, imagination and helping others quietly",  # Pisces
]
HOUSE_JOY = {
    4: ("Home and inner peace", "a calm home, time with mother or family, and owning your own space"),
    5: ("Creativity and children", "creative hobbies, children, learning, play and romance"),
    9: ("Meaning and faith", "pilgrimage, teachers, study of wisdom and long journeys"),
    11: ("Friends and goals", "a circle of friends, community and reaching goals you set"),
}
HORA_TXT = "the hour ruled by {p} (see the Daily tab for today's hours)"
MANTRA = {"Sun": "Om Suryaya Namah", "Moon": "Om Chandraya Namah", "Mars": "Om Mangalaya Namah",
          "Mercury": "Om Budhaya Namah", "Jupiter": "Om Gurave Namah", "Venus": "Om Shukraya Namah",
          "Saturn": "Om Shanaischaraya Namah", "Rahu": "Om Rahave Namah", "Ketu": "Om Ketave Namah"}
BEHAVIOUR = {
    "Sun": "Keep your word, wake early, and give respect to father figures and seniors.",
    "Moon": "Protect your sleep, drink enough water, and call your mother or an elder often.",
    "Mars": "Exercise regularly and pause for a breath before reacting.",
    "Mercury": "Write things down, keep accounts clean, and speak kindly and precisely.",
    "Jupiter": "Respect teachers, read something wise daily, and keep promises to family.",
    "Venus": "Keep your surroundings clean and beautiful; appreciate your partner openly.",
    "Saturn": "Be punctual, finish what you start, and treat workers and staff fairly.",
    "Rahu": "Avoid shortcuts and intoxicants; stay honest even when it costs you.",
    "Ketu": "Spend a few quiet minutes daily; let go of what you cannot control.",
}
CHARITY = {
    "Sun": "Donate wheat or jaggery on Sundays, or support a father figure in need.",
    "Moon": "Give rice, milk or water to those in need on Mondays.",
    "Mars": "Donate red lentils, or give blood when you can.",
    "Mercury": "Feed birds, or donate books and green gram to students.",
    "Jupiter": "Support a teacher or a temple, or give yellow food on Thursdays.",
    "Venus": "Help women in need, or donate clothes or sweets on Fridays.",
    "Saturn": "Feed the poor, help elderly people and labourers on Saturdays.",
    "Rahu": "Donate to people with disabilities or to hospitals.",
    "Ketu": "Feed stray dogs, or support spiritual or healing causes.",
}
HABIT_AVOID = {
    "Sun": "Ego battles with bosses or officials, and skipping breakfast or sunlight.",
    "Moon": "Late nights, emotional decisions, and bottling up feelings.",
    "Mars": "Arguments, rash driving, and acting in anger.",
    "Mercury": "Signing without reading, gossip, and overthinking small things.",
    "Jupiter": "Over-promising, overeating, and ignoring advice from elders.",
    "Venus": "Overspending on luxury, and neglecting your partner's feelings.",
    "Saturn": "Delaying duties, cutting corners, and isolating yourself.",
    "Rahu": "Get-rich-quick schemes, intoxicants, and half-truths.",
    "Ketu": "Withdrawing from people, and ignoring small health signals.",
}
REL_TXT = {h: "your Moons sit 6 and 8 signs apart. You see things differently and misunderstandings come "
              "easily; patience, clear agreements and paperwork for money matters help." for h in (6, 8)}


def _good_planets(ch):
    return [p for p in ac.PLANETS[:7] if ac.functional_nature(ch, p).startswith(("Benefic", "Yogakaraka"))]


def happiness_guide(ch: ac.Chart, md_list: list, now_jd: float) -> dict:
    P = ch.planets
    sb = shadbala.cached(ch)["planets"]
    moon = P["Moon"]
    joys = [f"Your Moon in {ac.SIGNS[moon['sign']]} is fed by {MOON_JOY[moon['sign']]}."]
    hs = sorted(((life.house_strength(ch, h)[0], h) for h in HOUSE_JOY), reverse=True)
    for s, h in hs[:2]:
        t, txt = HOUSE_JOY[h]
        joys.append(f"{t}: your chart supports joy through {txt}.")
    low_s, low_h = hs[-1]
    if low_s < 0:
        t, txt = HOUSE_JOY[low_h]
        joys.append(f"{t} needs conscious effort; small regular steps here bring lasting contentment.")
    if moon["house"] in (6, 8, 12) or moon["dignity"] == "Debilitated":
        joys.append("Your mind is sensitive: rest, routine and good company matter more for you than for most.")

    goods = _good_planets(ch) or [ch.lord_of_house(1)]
    best = max(goods, key=lambda p: sb[p]["ratio"])
    best_day = dict(planet=best, day=T.DAYNAME[best], hora=HORA_TXT.format(p=best),
                    why=f"{best} is your most helpful planet and also strong in your chart.")

    ak = ac.chara_karakas(ch)[0][1]
    lesson = pastlife.AK_LESSON[ak]
    ishta = pastlife.past_life_report(ch)["ishta"][1]

    chain = ac.current_chain(md_list, now_jd)
    weak = min(ac.PLANETS[:7], key=lambda p: life.planet_strength(ch, p))
    focus = list(dict.fromkeys([chain[0].lord, chain[1].lord, weak])) if len(chain) > 1 else [weak]
    ladder = [
        ("1. Daily behaviour (always first)", [f"{p}: {BEHAVIOUR[p]}" for p in focus]),
        ("2. Service and charity", [f"{p}: {CHARITY[p]}" for p in focus]),
        ("3. Mantra", [f"{p}: chant \"{MANTRA[p]}\" 108 times on {T.DAYNAME.get(p, 'any day')}s"
                       if p in T.DAYNAME else f"{p}: chant \"{MANTRA[p]}\" 108 times on Saturdays"
                       for p in focus]),
    ]
    gem = []
    for p in sorted(goods, key=lambda p: -sb[p]["ratio"]):
        fn = ac.functional_nature(ch, p)
        if P[p]["house"] in (6, 8, 12) or P[p]["dignity"] == "Debilitated":
            continue
        if p == ch.lord_of_house(1) or fn.startswith("Yogakaraka") or {5, 9} & set(ch.houses_owned(p)):
            gem.append(f"{p}: {T.STONE[p]}")
        if len(gem) == 2:
            break
    l1 = ch.lord_of_house(1)
    if l1 in ac.PLANETS[:7] and not any(g.startswith(l1 + ":") for g in gem):
        gem.append(f"{T.STONE[l1].capitalize()} is the traditional stone for your Ascendant lord {l1}, but {l1} is not "
                   f"comfortably placed in your chart, so wear it only after a personal consultation.")
    ladder.append(("4. Gemstone (optional, last step)",
                   (gem or ["No gemstone is clearly indicated; the first three steps are enough."]) +
                   ["Only stones for helpful planets are listed. Test for a few weeks and consult an "
                    "experienced astrologer before wearing one."]))
    return dict(joys=joys, best_day=best_day, lesson=f"Soul lesson ({ak}): {lesson}.", ishta=ishta,
                ladder=ladder)


def avoid_guide(ch: ac.Chart, md_list: list, now_jd: float, others: list | None = None) -> dict:
    tz = "Asia/Kolkata"
    periods = [p for p in life.dasha_periods(ch, md_list)
               if p["end"] > now_jd and p["start"] < now_jd + 365.25 * 12 and p["rating"] == "Challenging"][:3]
    per_rows = [dict(when=f"{ac.jd_to_local(max(p['start'], now_jd), tz):%b %Y} – "
                          f"{ac.jd_to_local(p['end'], tz):%b %Y}",
                     what=f"{p['md']} – {p['ad']} period",
                     care=p["guidance"].replace("Be careful about: ", "Be careful about ")) for p in periods]
    segs = [x for x in ac.sade_sati(ch, years_ahead=int((now_jd - ch.jd) / 365.25) + 13)
            if x["end"] > now_jd and x["start"] < now_jd + 365.25 * 12
            and ("Sade" in x["phase"] or "Ashtama" in x["phase"])]
    spans = []
    for x in segs:   # Saturn's retrograde loops split a phase; join pieces less than a year apart
        kind = "Sade Sati" if "Sade" in x["phase"] else "Ashtama Shani (8th from Moon)"
        if spans and spans[-1]["kind"] == kind and x["start"] - spans[-1]["end"] < 365:
            spans[-1]["end"] = x["end"]
        else:
            spans.append(dict(kind=kind, start=x["start"], end=x["end"]))
    sat_rows = []
    for sp in spans:
        now_phase = next(({"phase 1 (rising)": "rising phase", "phase 2 (peak)": "peak phase",
                           "phase 3 (setting)": "setting phase"}[x["phase"].split(" - ")[1]] for x in segs
                          if x["start"] <= now_jd <= x["end"] and "Sade" in x["phase"]), "")
        care = ("Saturn tests patience: avoid big risks, debt and shortcuts; keep health, sleep and "
                "commitments steady. Hard work done now pays back later.")
        sat_rows.append(dict(when=f"{ac.jd_to_local(max(sp['start'], now_jd), tz):%b %Y} – "
                                  f"{ac.jd_to_local(sp['end'], tz):%b %Y}",
                             what=sp["kind"] + (f" (now in its {now_phase})" if now_phase and sp["start"] <= now_jd
                                                and sp["kind"] == "Sade Sati" else ""),
                             care=care))

    chain = ac.current_chain(md_list, now_jd)
    weak2 = sorted(ac.PLANETS[:7], key=lambda p: life.planet_strength(ch, p))[:2]
    dl = [c.lord for c in chain[:2]]
    habits = []
    for p in dict.fromkeys(dl + weak2):
        why = ("running period" if p in dl else "weaker planet in your chart")
        habits.append(f"{p} ({why}): {HABIT_AVOID[p]}")

    rules = ["Do not sign, launch or travel far during your Chandrashtama days (see Next 90 days).",
             "Keep Rahu Kalam and Yamagandam free of new starts; use them for routine work.",
             "Do not make a big commitment in the few days around a change of sub-period."]
    P = ch.planets
    if P["Mars"]["house"] in (1, 4, 7, 8, 12) or life.planet_strength(ch, "Mars") < 0 or "Mars" in weak2:
        rules.append("Sleep on any decision made in anger; Mars in your chart reacts fast.")
    if P["Mercury"]["combust"] or life.planet_strength(ch, "Mercury") < 0 or "Mercury" in weak2:
        rules.append("Have a second person read contracts before you sign.")
    if P["Moon"]["house"] in (6, 8, 12) or life.planet_strength(ch, "Moon") < 0 or "Moon" in weak2:
        rules.append("Avoid big money or relationship decisions when you feel low; wait for a calmer day.")
    if P["Saturn"]["house"] in (1, 7, 10) or "Saturn" in weak2:
        rules.append("Avoid rushing: delays in your chart turn into lasting results if you stay patient.")

    rels = []
    for name, oc in (others or []):
        h = (oc.moon_sign - ch.moon_sign) % 12 + 1
        if h in REL_TXT:
            rels.append(f"{name}: {REL_TXT[h]}")
    return dict(periods=per_rows, saturn=sat_rows, habits=habits, rules=rules, relations=rels)
