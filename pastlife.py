"""
Past life (karmic) report from traditional Vedic indicators.

Indicators used
- Ketu: skills and identity carried over from past lives (house, sign, star).
- Rahu: the direction the soul is learning in this life.
- Atmakaraka (Jaimini soul planet) and Karakamsa (its Navamsa sign):
  the soul's central lesson and nature; Ishta Devata from the 12th from Karakamsa.
- 5th and 9th houses (Purva Punya): merit carried forward.
- Saturn and retrograde planets: karmic work and unfinished matters.
- Karmic debts (Rinas): classical affliction patterns to the Sun, Moon,
  Venus, Jupiter and Mars.
- 12th house and Ketu: pull towards liberation (moksha).

These are symbolic, traditional interpretations, not verifiable facts.
"""
from __future__ import annotations

import astro_core as ac
import life

KETU_HOUSE = {
    1: "Lived as a strong, self-reliant individual, possibly a seeker, warrior or ascetic. Carries an instinctive "
       "sense of self, but can feel detached from or unsure of personal identity now.",
    2: "Past life tied to family lineage, wealth or speech, perhaps as a teacher, priest or keeper of tradition. "
       "Now less attached to accumulating, and speech can be blunt or minimal.",
    3: "Past life of courage, craft or communication: messenger, writer, soldier or artisan. These skills come "
       "naturally now, though motivation to use them can be low.",
    4: "Past life rooted in home, land and mother. Deep emotional memory; home may feel unsettled or hard to "
       "fully enjoy in this life.",
    5: "Past life of learning, creativity or spiritual practice: scholar, artist or practitioner of mantra. "
       "Intelligence comes easily; matters of children carry karma.",
    6: "Past life of service, healing or battle: healer, soldier or servant. Strong instinct for problem-solving; "
       "old debts and rivalries tend to resolve in this life.",
    7: "Past life centred on partnership, marriage or trade. The soul gave much to others and is now learning "
       "balance and independence within relationships.",
    8: "Past life touched mysticism, the occult or hidden knowledge, or ended suddenly. Strong intuition and "
       "research ability; little fear of the unknown.",
    9: "Past life as a teacher, priest, pilgrim or philosopher. Carries wisdom and a sense of dharma, but may "
       "question beliefs and teachers now.",
    10: "Past life of authority, rule or public duty. Career skills feel natural, but real satisfaction lies "
        "beyond status and titles.",
    11: "Past life rich in networks, gains and fulfilled desires. The soul is now less driven by wanting more "
        "and more by meaning.",
    12: "Past life of renunciation, spiritual practice, or life in a monastery or foreign land. Strong pull "
        "towards spirituality, solitude and liberation.",
}
RAHU_HOUSE = {
    1: "build a strong personal identity and lead from the front",
    2: "build wealth, family stability and a voice of influence",
    3: "develop courage, communication, media and self-made initiative",
    4: "create a stable home, emotional security and property",
    5: "express creativity and intelligence, and learn through children and investments",
    6: "master work, service, health routines and competition through discipline",
    7: "learn partnership, cooperation, and dealing with the public and foreign partners",
    8: "explore transformation, research, shared resources and the hidden side of life",
    9: "seek higher knowledge, travel, philosophy and personal beliefs",
    10: "rise in career, status and public responsibility",
    11: "build large networks and fulfil big ambitions through groups",
    12: "explore foreign lands, spirituality and imagination, and learn to let go",
}
SIGN_FLAVOUR = ["pioneering and fiery", "steady and comfort-seeking", "curious and communicative",
                "emotional and nurturing", "proud and leadership-oriented", "analytical and service-minded",
                "harmonious and partnership-minded", "intense and secretive", "philosophical and freedom-loving",
                "dutiful and ambitious", "independent and humanitarian", "spiritual and compassionate"]
AK_LESSON = {
    "Sun": "ego and authority: learning humility and leadership with integrity",
    "Moon": "emotions and care: learning emotional balance and compassion without attachment",
    "Mars": "action and conflict: learning to use courage and energy without aggression",
    "Mercury": "speech and intellect: learning truthful communication and clear judgement",
    "Jupiter": "wisdom and dharma: learning to guide others and to honour teachers",
    "Venus": "desire and relationships: learning pure love and balance in pleasures",
    "Saturn": "duty and hardship: learning patience, service and freedom from fear",
}
KARAKAMSA = [
    "fiery independence and leadership; lessons around anger and impulsiveness",
    "comfort, arts and wealth; lessons around attachment to possessions",
    "trade, learning and communication; lessons around scattered attention",
    "nurturing, home and emotional bonds; lessons around dependence",
    "authority, government and leadership; lessons around pride",
    "service, analysis, healing and commerce; lessons around worry and criticism",
    "balance, partnership and business; lessons around indecision",
    "research, transformation and hidden knowledge; lessons around control",
    "teaching, law and religion; lessons around rigid beliefs",
    "duty, industry and structure; lessons around rigidity",
    "service to society and innovation; lessons around detachment",
    "spirituality, compassion and liberation; lessons around escapism",
]
DEITY = {"Sun": "Shiva or Surya", "Moon": "Parvati (Gauri) or Krishna", "Mars": "Murugan or Hanuman",
         "Mercury": "Vishnu", "Jupiter": "Dakshinamurthy (Shiva as teacher)", "Venus": "Lakshmi",
         "Saturn": "Venkateswara or Hanuman", "Rahu": "Durga", "Ketu": "Ganesha"}
SATURN_WORK = {
    1: "self-discipline, health and a mature sense of identity",
    2: "family responsibilities, honest speech and money discipline",
    3: "steady effort, courage and responsibility towards siblings",
    4: "home, mother and inner emotional security",
    5: "patience with children, learning and creative work",
    6: "service, health routines and clearing debts",
    7: "commitment and fairness in marriage and partnerships",
    8: "facing fears, handling shared resources and accepting change",
    9: "faith, ethics and the relationship with father and teachers",
    10: "career duty and public responsibility",
    11: "earning honestly and keeping loyal friendships",
    12: "letting go, charity and spiritual practice",
}
RETRO_THEME = {"Mercury": "unfinished matters in communication, learning or trade",
               "Venus": "unfinished matters in love, marriage or pleasures",
               "Mars": "unfinished matters of conflict, property or courage",
               "Jupiter": "unfinished matters with teachers, children or wisdom",
               "Saturn": "unfinished duties and karmic debts to be completed patiently"}


def _with(ch, p, others):
    s = ch.planets[p]["sign"]
    return [o for o in others if ch.planets[o]["sign"] == s]


def karmic_debts(ch: ac.Chart) -> list[dict]:
    P = ch.planets
    nodes_sat = ["Rahu", "Ketu", "Saturn"]
    out = []

    def add(name, cond, why, remedy):
        if cond:
            out.append(dict(debt=name, why=why, remedy=remedy))

    w = _with(ch, "Sun", nodes_sat)
    nh9 = [n for n in ("Rahu", "Ketu") if P[n]["house"] == 9]
    l9 = ch.lord_of_house(9)
    add("Pitru Rina (ancestral)", bool(w or nh9 or P[l9]["house"] in (6, 8, 12)),
        "; ".join(filter(None, [f"Sun with {', '.join(w)}" if w else "", f"{', '.join(nh9)} in the 9th" if nh9 else "",
                                f"9th lord {l9} in house {P[l9]['house']}" if P[l9]["house"] in (6, 8, 12) else ""])),
        "Offerings to ancestors (tarpan) on Amavasya; respect and care for father and elders.")
    w = _with(ch, "Moon", nodes_sat)
    nh4 = [n for n in ("Rahu", "Ketu") if P[n]["house"] == 4]
    add("Matru Rina (mother)", bool(w or nh4),
        "; ".join(filter(None, [f"Moon with {', '.join(w)}" if w else "", f"{', '.join(nh4)} in the 4th" if nh4 else ""])),
        "Serve and care for mother and elderly women; Monday prayers to Parvati.")
    w = _with(ch, "Venus", nodes_sat)
    nh7 = [n for n in ("Rahu", "Ketu") if P[n]["house"] == 7]
    add("Stree Rina (spouse / partner)", bool(w or nh7 or (P["Venus"]["retro"] and P["Venus"]["combust"])),
        "; ".join(filter(None, [f"Venus with {', '.join(w)}" if w else "", f"{', '.join(nh7)} in the 7th" if nh7 else "",
                                "Venus retrograde and combust" if P["Venus"]["retro"] and P["Venus"]["combust"] else ""])),
        "Respect and support the spouse; Friday Lakshmi prayers; charity to women in need.")
    w = _with(ch, "Jupiter", ["Rahu", "Ketu"])
    add("Guru Rina (teacher)", bool(w), f"Jupiter with {', '.join(w)}" if w else "",
        "Honour teachers; Thursday prayers to Dakshinamurthy; support education.")
    w = _with(ch, "Mars", nodes_sat)
    nh3 = [n for n in ("Rahu", "Ketu") if P[n]["house"] == 3]
    add("Bhratru Rina (siblings)", bool(w or nh3),
        "; ".join(filter(None, [f"Mars with {', '.join(w)}" if w else "", f"{', '.join(nh3)} in the 3rd" if nh3 else ""])),
        "Help siblings and colleagues; Tuesday Murugan or Hanuman prayers.")
    return out


def past_life_report(ch: ac.Chart) -> dict:
    P = ch.planets
    k, r = P["Ketu"], P["Rahu"]
    ak = ac.chara_karakas(ch)[0][1]
    d9 = ac.varga_chart(ch, 9)
    kk = d9[ak]
    twelfth = (kk + 11) % 12
    in12 = [p for p in ac.PLANETS if d9[p] == twelfth]
    ishta_planet = in12[0] if in12 else ac.SIGN_LORD[twelfth]
    ketu_with = [p for p in ac.PLANETS if p != "Ketu" and P[p]["sign"] == k["sign"]]
    rahu_with = [p for p in ac.PLANETS if p != "Rahu" and P[p]["sign"] == r["sign"]]

    s5, _ = life.house_strength(ch, 5)
    s9, _ = life.house_strength(ch, 9)
    punya = (s5 + s9) / 2
    punya_stars = int(max(1, min(5, round(3 + punya / 2.5))))
    s12, n12 = life.house_strength(ch, 12)
    in_12 = [p for p in ac.PLANETS if P[p]["house"] == 12]
    moksha_pull = sum([k["house"] in (4, 8, 12), bool(in_12), "Jupiter" in ketu_with,
                       P[ak]["house"] in (4, 8, 12), d9["Ketu"] == kk])
    retro = [p for p in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn") if P[p]["retro"]]

    ketu_text = KETU_HOUSE[k["house"]]
    ketu_text += (f" The {ac.SIGNS[k['sign']]} placement suggests that past life was "
                  f"{SIGN_FLAVOUR[k['sign']]}, and the star {ac.NAKSHATRAS[k['nak']]} "
                  f"({life.NAK_TRAITS[k['nak']]}) colours those skills.")
    if ketu_with:
        ketu_text += f" Ketu with {', '.join(ketu_with)}: mastery of " + "; ".join(
            ac.PLANET_KEYWORDS[p].split(",")[0] for p in ketu_with) + " was developed before."

    rahu_text = (f"In this life the soul's direction is to {RAHU_HOUSE[r['house']]}. Rahu in {ac.SIGNS[r['sign']]} "
                 f"brings a {SIGN_FLAVOUR[r['sign']]} hunger for experience.")
    if rahu_with:
        rahu_text += f" Rahu with {', '.join(rahu_with)} amplifies " + ", ".join(
            ac.PLANET_KEYWORDS[p].split(",")[0] for p in rahu_with) + "."

    summary = [
        f"Past-life signature: Ketu in house {k['house']} ({ac.SIGNS[k['sign']]}). "
        f"Familiar ground: {ac.HOUSE_THEMES[k['house']]}.",
        f"This life's direction: Rahu in house {r['house']} ({ac.SIGNS[r['sign']]}). "
        f"Growth area: to {RAHU_HOUSE[r['house']]}.",
        f"Soul planet (Atmakaraka): {ak}: {AK_LESSON[ak]}.",
        f"Karakamsa (soul planet in Navamsa): {ac.SIGNS[kk]}: {KARAKAMSA[kk]}.",
        f"Merit carried forward (5th and 9th houses): {'★' * punya_stars}{'☆' * (5 - punya_stars)}.",
        f"Suggested Ishta Devata (from the 12th from Karakamsa, {ishta_planet}): {DEITY[ishta_planet]}.",
    ]
    punya_text = (
        "Strong merit from past lives: support from teachers, elders and luck tends to arrive when needed."
        if punya_stars >= 4 else
        "Moderate merit: good fortune comes, but often after effort and patience." if punya_stars == 3 else
        "Merit needs to be built in this life through service, learning and generosity; luck grows with effort.")
    return dict(
        summary=summary, ketu=ketu_text, rahu=rahu_text,
        axis=f"The Rahu–Ketu axis runs across houses {r['house']} and {k['house']}: the soul moves from "
             f"{ac.HOUSE_THEMES[k['house']]} (past) towards the need to {RAHU_HOUSE[r['house']]} (future). Balance "
             f"between the two is the main life task.",
        ak=ak, ak_text=AK_LESSON[ak], karakamsa=ac.SIGNS[kk], karakamsa_text=KARAKAMSA[kk],
        ishta=(ishta_planet, DEITY[ishta_planet]),
        punya_stars=punya_stars, punya_text=punya_text,
        saturn=f"Saturn in house {P['Saturn']['house']} ({ac.SIGNS[P['Saturn']['sign']]}): karmic work in "
               f"{SATURN_WORK[P['Saturn']['house']]}. Steady effort here repays old debts.",
        retro=[(p, RETRO_THEME[p]) for p in retro],
        debts=karmic_debts(ch),
        moksha=dict(score=moksha_pull, in12=in_12,
                    text=("A strong pull towards spirituality and liberation in this life."
                          if moksha_pull >= 3 else
                          "A balanced pull: worldly duties first, with spirituality growing later in life."
                          if moksha_pull >= 1 else
                          "A worldly focus in this life: the soul is here to build, act and experience.")),
    )
