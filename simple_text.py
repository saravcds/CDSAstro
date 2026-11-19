"""
Plain-language readings for everyday users.

Every function here turns the app's calculations into short "you" sentences
grouped by life topic, without technical terms. All text is original to this
app and follows traditional Vedic rules; it describes tendencies, not certainties.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import astro_core as ac
import life
import predict as pr

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
ASC = [  # personality, strengths, work on, career, health, love
    dict(p="You are direct, energetic and quick to act. You like to lead, start new things and face challenges head-on.",
         s="Courage, honesty, initiative and the ability to get things moving.",
         w="Impatience, a quick temper and losing interest once the excitement fades.",
         c="You do well where you can lead, compete or build something new: management, engineering, sports, defence or your own business.",
         h="Look after your head and eyes. Headaches and fevers usually come from overwork and stress; regular exercise helps you release energy.",
         l="You are passionate and protective in relationships, and you need a partner who gives you space and matches your energy."),
    dict(p="You are calm, patient and practical. You value comfort, stability and the good things in life, and you build slowly but surely.",
         s="Reliability, patience, good taste and good financial sense.",
         w="Stubbornness, resistance to change and overindulgence.",
         c="Finance, banking, real estate, food, arts, design and luxury goods suit you, as does any work that builds lasting value.",
         h="Your throat and neck are sensitive. Watch weight and sugar through balanced food and regular activity.",
         l="Loyal and affectionate, you look for a steady, long-term partner and show love through care and comfort."),
    dict(p="You are curious, quick-witted and sociable. You learn fast, love conversation and enjoy variety.",
         s="Communication, adaptability, intelligence and humour.",
         w="Restlessness, scattered focus and changing your mind too often.",
         c="Writing, media, sales, IT, teaching, consulting and trading suit you: anything built on ideas and networks.",
         h="Your nerves, lungs and shoulders need care. A busy mind can disturb sleep, so calming routines help.",
         l="You need a mental connection and good conversation. A partner who is also a friend suits you best."),
    dict(p="You are caring, sensitive and protective. Home and family matter deeply to you, and you remember how people make you feel.",
         s="Empathy, loyalty, intuition and looking after others.",
         w="Mood swings, holding on to hurt and worrying too much.",
         c="Healthcare, hospitality, food, education, real estate and public service suit your caring nature.",
         h="Your chest and stomach are sensitive. Emotional stress affects digestion, so a calm routine helps.",
         l="Deeply devoted, you look for emotional security and a partner who values family."),
    dict(p="You are confident, warm and generous. You like to lead, be recognised and bring energy into any room.",
         s="Leadership, courage, generosity and creativity.",
         w="Pride, needing praise and finding criticism hard to accept.",
         c="Leadership roles, government, management, politics and entertainment suit you: any role with authority.",
         h="Look after your heart, spine and blood pressure. Regular exercise and rest balance your intensity.",
         l="Loyal and romantic, you enjoy a partner who admires you and shares your pride in life."),
    dict(p="You are practical, analytical and helpful. You notice details that others miss and like doing things properly.",
         s="Precision, discipline, problem-solving and service.",
         w="Over-thinking, self-criticism and being too critical of others.",
         c="Analytics, accounting, healthcare, IT, quality, research and editing suit your eye for detail.",
         h="Your digestion is sensitive. Worry shows up in the stomach, so regular meals and rest matter.",
         l="You show love through practical care, and you need a partner who is sincere and appreciates your effort."),
    dict(p="You are diplomatic, charming and fair-minded. You look for balance, beauty and good relationships.",
         s="Tact, a sense of justice, social skills and good taste.",
         w="Indecision, avoiding conflict and depending on others' approval.",
         c="Law, business partnerships, design, fashion, HR and client-facing roles suit you.",
         h="Your kidneys, lower back and skin need care. Drink enough water and keep a balanced lifestyle.",
         l="Partnership is central to your happiness. You do best in a fair, respectful and peaceful relationship."),
    dict(p="You are intense, private and determined. You see beneath the surface and do not give up easily.",
         s="Willpower, depth, loyalty, research ability and strength in a crisis.",
         w="Suspicion, holding grudges and keeping too much to yourself.",
         c="Research, investigation, finance, medicine, engineering and strategy suit you, as do roles that handle crises or confidential matters.",
         h="Your reproductive and urinary systems need care. Manage stress, because you tend to hold emotions inside.",
         l="Deeply loyal and passionate, you need complete trust. Betrayal is very hard for you to forgive."),
    dict(p="You are optimistic, honest and freedom-loving. You enjoy learning, travel and big ideas.",
         s="Enthusiasm, wisdom, generosity and a sense of fairness.",
         w="Impatience with details, over-promising and speaking too bluntly.",
         c="Teaching, law, consulting, travel, publishing, finance and international work suit you.",
         h="Your hips, thighs and liver need care. Avoid excess and stay active.",
         l="You need a partner who shares your values and gives you freedom to grow."),
    dict(p="You are ambitious, disciplined and responsible. You plan for the long term and build success step by step.",
         s="Patience, hard work, reliability and organisation.",
         w="Being too serious, rigid or reserved with your feelings.",
         c="Management, administration, engineering, operations, government and finance suit you, especially in long-standing organisations.",
         h="Your knees, bones and joints need care. Regular movement and calcium-rich food help.",
         l="Steady and loyal, you show love through commitment and responsibility more than words."),
    dict(p="You are independent, original and forward-thinking. You care about people and ideas that make the world better.",
         s="Innovation, friendliness, fairness and big-picture thinking.",
         w="Detachment, stubbornness about your ideas and difficulty expressing feelings.",
         c="Technology, science, research, social causes and innovative businesses suit you.",
         h="Your circulation, ankles and nerves need care. Regular movement and rest for the mind help.",
         l="You need friendship and freedom in love. A partner who respects your independence suits you."),
    dict(p="You are compassionate, imaginative and intuitive. You feel deeply and are drawn to art, spirituality and helping others.",
         s="Kindness, creativity, intuition and adaptability.",
         w="Escaping from problems, trusting too easily and difficulty setting boundaries.",
         c="Healing, medicine, arts, music, charity, spiritual work and work abroad suit you.",
         h="Your feet and immune system need care. Enough sleep and avoiding excess matter.",
         l="Romantic and devoted, you give a lot in love and need a partner who is gentle and sincere."),
]
MOON_TXT = [
    "Emotionally you react quickly and recover fast. You are happiest when you are active and have a goal to chase. Learning to pause before reacting brings you more peace.",
    "Emotionally you are steady and calm. Comfort, good food, nature and financial security make you happy. Try not to hold on too tightly to people and things.",
    "Your mind is lively and always busy. Conversation, learning and variety make you happy. A calm routine helps your restless mind settle.",
    "You feel things deeply and care for others naturally. A warm home and close family bring you the most happiness. Protect yourself from taking on everyone's worries.",
    "Emotionally you are warm and generous, and you need to feel appreciated. Recognition and creative expression lift your mood. Do not let others' opinions decide your self-worth.",
    "You handle feelings by thinking them through and organising things. Being useful makes you happy. Be kinder to yourself when things are not perfect.",
    "You need harmony and good company to feel at peace. Beauty, art and fair relationships make you happy. Practise making decisions without waiting for everyone's approval.",
    "Your emotions run deep and you keep them private. Trust and loyal relationships give you security. Letting go of past hurts is the key to lasting peace.",
    "You are emotionally optimistic and need freedom. Travel, learning and a sense of purpose make you happy. Stay patient when life feels slow.",
    "You are emotionally reserved and responsible. Achievement and security help you feel settled. Make time to rest and to share your feelings with people close to you.",
    "You handle feelings with a cool, rational mind. Friends, ideas and helping society make you happy. Allow yourself to express emotions, not only think about them.",
    "You are sensitive, kind and intuitive. Music, spirituality and helping others bring you peace. Quiet time alone helps you recharge.",
]
PLANET_PLAIN = {"Sun": "the Sun (confidence and authority)", "Moon": "the Moon (mind and emotions)",
                "Mars": "Mars (energy and courage)", "Mercury": "Mercury (intelligence and communication)",
                "Jupiter": "Jupiter (wisdom, luck and growth)", "Venus": "Venus (love, comfort and beauty)",
                "Saturn": "Saturn (discipline and hard work)", "Rahu": "Rahu (ambition and change)",
                "Ketu": "Ketu (detachment and spirituality)"}
HOUSE_PLAIN = {1: "personality", 2: "money and family", 3: "courage and communication", 4: "home and happiness",
               5: "intelligence and children", 6: "work and health", 7: "marriage and partnerships",
               8: "sudden changes", 9: "luck and higher learning", 10: "career", 11: "income and friends",
               12: "expenses and spirituality"}
YOGA_PLAIN = {"Gaja Kesari": "a combination for respect, wisdom and protection",
              "Budha-Aditya": "a combination for sharp intelligence and good communication",
              "Chandra-Mangala": "a combination for drive to earn money",
              "Raja Yoga": "a combination for status and success",
              "Dhana Yoga": "a combination for building wealth",
              "Vipareeta": "a combination where difficulties turn into advantages",
              "Neecha Bhanga": "a combination where early struggles turn into later success",
              "Ruchaka": "strong courage and leadership", "Bhadra": "a sharp business mind",
              "Hamsa": "wisdom and good character", "Malavya": "charm, comfort and artistic talent",
              "Sasa": "discipline and the ability to lead large organisations"}
COLOUR = {"Sun": "orange or gold", "Moon": "white or silver", "Mars": "red or maroon", "Mercury": "green",
          "Jupiter": "yellow", "Venus": "white or light pink", "Saturn": "dark blue or black"}
DAYNAME = {"Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday", "Mercury": "Wednesday",
           "Jupiter": "Thursday", "Venus": "Friday", "Saturn": "Saturday"}
NUMBER = {"Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4, "Mercury": 5, "Venus": 6, "Ketu": 7, "Saturn": 8, "Mars": 9}
STONE = {"Sun": "ruby", "Moon": "pearl", "Mars": "red coral", "Mercury": "emerald",
         "Jupiter": "yellow sapphire", "Venus": "diamond or white sapphire", "Saturn": "blue sapphire"}
REMEDY = {"Sun": "Offer water to the rising Sun on Sundays, and respect your father and seniors.",
          "Moon": "Pray to Shiva on Mondays, spend time near water, and respect your mother.",
          "Mars": "Pray to Hanuman or Murugan on Tuesdays, and practise patience before reacting.",
          "Mercury": "Pray to Ganesha or Vishnu on Wednesdays, and feed birds or donate green gram.",
          "Jupiter": "Pray to Guru or Dakshinamurthy on Thursdays, respect teachers, and donate yellow items.",
          "Venus": "Pray to Lakshmi on Fridays, respect women, and keep your home clean and pleasant.",
          "Saturn": "Light a sesame oil lamp on Saturdays, and help elderly people and workers.",
          "Rahu": "Pray to Durga, avoid alcohol and shortcuts, and keep your word.",
          "Ketu": "Pray to Ganesha, feed stray dogs, and spend some quiet time each day."}
STARS_SENT = {5: "This is one of the strongest areas of your chart.", 4: "This area is well supported in your chart.",
              3: "This area is steady, with some ups and downs.", 2: "This area needs extra care and patience.",
              1: "This area is challenging and needs conscious effort."}

DAY = {  # Moon's house from Ascendant: theme, work, money, love, health
    1: ("Today is about you: your energy and confidence.", "Take the lead on your own priorities; people notice your initiative.",
        "Money is steady. Avoid impulse buying.", "You make a good impression today.", "Energy is good; do not overdo it."),
    2: ("Money, family and food are in focus today.", "A good day for financial work, pricing and budgets.",
        "Good for collections, savings and checking accounts.", "Family conversations come up; choose your words gently.",
        "Watch what and when you eat."),
    3: ("A day for effort, courage and communication.", "Calls, emails, pitches and follow-ups get results.",
        "Your own effort brings gains.", "Reach out to siblings and friends.", "You feel active and energetic."),
    4: ("Home, comfort and peace of mind are in focus.", "A steady day, good for internal work and planning.",
        "You may spend on home, family or comfort.", "Time with family and your mother brings happiness.",
        "Rest well; emotions may run high."),
    5: ("A creative day for ideas, children and planning.", "Good for strategy, learning and creative work.",
        "Think long term and avoid risky bets.", "A warm day for romance and time with children.", "You feel generally well."),
    6: ("A practical day for solving problems.", "Clear pending work and handle difficult people calmly.",
        "Settle dues and avoid taking new loans.", "Avoid arguments and keep things practical.",
        "Look after your digestion and stress levels."),
    7: ("Partners, clients and your spouse are in focus.", "Good for meetings, negotiations and client work.",
        "Gains can come through partners.", "A good day for your spouse or partner; plan some time together.",
        "Balanced; nothing special to watch."),
    8: ("A sensitive day. Keep things simple.", "Avoid big decisions; do checks and research instead.",
        "Be careful with money, documents and passwords.", "Stay calm and patient; misunderstandings are possible.",
        "Rest more and take care while travelling."),
    9: ("Luck and blessings support you today.", "Good for advice from seniors, learning and travel plans.",
        "Fortune supports planned moves.", "Spend time with elders, teachers or your father.", "You feel well."),
    10: ("Career and reputation are in focus.", "Strong for leadership, important meetings and visible work.",
         "Gains come through work and recognition.", "Work may take time away from family; balance it.",
         "A busy day; pace yourself."),
    11: ("A day for gains, friends and wishes coming true.", "Good for closing deals, networking and results.",
         "Good for income and receiving payments.", "Friends and groups are supportive.", "You feel good."),
    12: ("A quiet day for rest and planning.", "Good for planning and behind-the-scenes work, not for launches.",
         "Expenses are likely; keep a check.", "Quiet time together is better than crowds.", "Sleep and rest well."),
}
AREA_SENT = {
    "Career": {"Supportive": "Work goes well; a good time for growth and visibility.",
               "Mixed / steady": "Work is steady; progress comes through consistent effort.",
               "Challenging": "Work may feel slow or demanding; avoid hasty changes."},
    "Money": {"Supportive": "Money flow is good; a good time to save and plan investments.",
              "Mixed / steady": "Money is stable; keep spending planned.",
              "Challenging": "Be careful with spending and financial commitments."},
    "Relationships": {"Supportive": "Relationships feel warm and supportive.",
                      "Mixed / steady": "Relationships are steady; small misunderstandings are possible.",
                      "Challenging": "Relationships need patience and clear communication."},
    "Home & family": {"Supportive": "Home life is happy and supportive.", "Mixed / steady": "Home life is steady.",
                      "Challenging": "Family matters may need your attention."},
    "Health": {"Supportive": "Health is good; keep up healthy routines.", "Mixed / steady": "Health is fine; avoid overwork.",
               "Challenging": "Look after your health; rest and check-ups help."},
}
FLAG_SENT = {"Chandrashtama": "you may feel low or misunderstood", "Naidhana tara": "plans may not work out as hoped",
             "Rikta tithi": "avoid new starts", "Amavasya": "energy is low (new moon)",
             "Full moon": "emotions run high (full moon)"}
GOODFOR_PLAIN = {"business / signing": "business and signing", "money matters": "money matters",
                 "relationships": "relationships", "travel / outreach": "travel and outreach",
                 "rest, review, clearing backlog": "rest and catching up"}
TRANSIT_PLAIN = {"Jupiter": "brings growth and opportunities to", "Saturn": "asks for patience and hard work in",
                 "Rahu": "brings ambition and sudden changes to", "Ketu": "brings detachment and change to",
                 "Mars": "adds energy, and some friction, to", "Sun": "puts the spotlight on",
                 "Mercury": "brings activity and discussion to", "Venus": "brings comfort and pleasant moments to"}
RETRO_PLAIN = {"Mercury": ("double-check messages, contracts and travel plans", "delayed paperwork and talks start moving again"),
               "Venus": ("old relationship matters may resurface; avoid big purchases", "relationships and money feel easier"),
               "Mars": ("energy feels blocked; avoid rash actions and disputes", "energy and drive return"),
               "Jupiter": ("growth slows down; review rather than expand", "growth and opportunities pick up again"),
               "Saturn": ("old responsibilities return; be patient with delays", "stuck matters start moving again")}


def _verdict(score: int) -> str:
    return ("A good day" if score >= 65 else "A mixed day" if score >= 45 else "A day to go slow")


def _fmt(d) -> str:
    return d.strftime("%a %d %b")


def _house(ch, sign):
    return ch.house_of_sign(sign)


# ---------------------------------------------------------------------------
# My report
# ---------------------------------------------------------------------------

def _and(xs):
    xs = list(dict.fromkeys(xs))
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def _home_line(ch):
    lord = ch.lord_of_house(4)
    h = ch.planets[lord]["house"]
    if h in (1, 4, 5, 7, 9, 10, 11):
        return "Home life and inner peace are well supported; a settled home is a real source of happiness for you."
    if h in (6, 8, 12):
        return "Peace at home can feel unsettled at times; keep work worries out of the house and plan time with family."
    return "Home life is steady; small efforts to keep the family together pay back well."


HOUSE_SHORT = {1: "personality", 2: "money", 3: "courage", 4: "home", 5: "children", 6: "health",
               7: "marriage", 8: "sudden changes", 9: "luck", 10: "career", 11: "income", 12: "expenses"}

def _money_lines(ch):
    P = ch.planets
    l11, l2, l4 = ch.lord_of_house(11), ch.lord_of_house(2), ch.lord_of_house(4)
    SRC = {1: "your own efforts and reputation", 2: "family business, savings and good speech",
           3: "your own initiative, sales, media and short travel", 4: "property, vehicles or home-based work",
           5: "ideas, creativity, investments and advisory work", 6: "service, competition and solving problems",
           7: "partnerships, clients and business deals", 8: "research, insurance or other people's money",
           9: "teaching, advice, long-distance work and mentors", 10: "your career, status and position",
           11: "networks, friends, large organisations and steady gains", 12: "foreign connections and distant places"}
    h11, h2 = P[l11]["house"], P[l2]["house"]
    out = [f"Money comes mainly through {SRC[h11]}." + (f" Savings grow through {SRC[h2]}." if h2 != h11 else "")]
    d4 = P[l4]["dignity"]
    out.append("Owning a home or property is well supported in your chart." if d4 in ("Exalted", "Own sign")
               or P[l4]["house"] in (1, 4, 10, 11) else
               "Be careful with property deals: check papers twice and avoid hurry." if d4 == "Debilitated"
               or P[l4]["house"] in (6, 8, 12) and d4 not in ("Exalted", "Own sign") else
               "Property comes with steady effort and planning.")
    risky = any(P[x]["house"] in (2, 5, 8, 11) and P[x]["dignity"] in ("Debilitated", "Enemy sign")
                for x in ("Mars", "Saturn", "Rahu"))
    out.append("Long-term investing suits you better than quick trading or speculation." if risky else
               "Measured investments can work for you; avoid putting everything in one place.")
    return out


NUM_MEAN = {1: "a natural leader; independent and ambitious", 2: "a peacemaker; sensitive and cooperative",
            3: "creative and expressive; a good teacher or advisor", 4: "practical and hard-working; builds slowly and solidly",
            5: "quick, adaptable and good at business and communication", 6: "caring and responsible; family and beauty matter",
            7: "thoughtful and spiritual; a researcher at heart", 8: "ambitious and patient; success comes with persistence",
            9: "energetic and generous; a fighter for causes"}


def _root(n):
    while n > 9:
        n = sum(int(c) for c in str(n))
    return n


def numerology(ch) -> str:
    d = ch.dt_local
    b = _root(d.day)
    dest = _root(sum(int(c) for c in d.strftime("%d%m%Y")))
    return (f"Birth number {b}: {NUM_MEAN[b]}. Destiny number {dest}: {NUM_MEAN[dest]}.")


def strongest_areas(ch, n: int = 3) -> list[int]:
    """Houses with the most Sarva Ashtakavarga points."""
    sav = ac.ashtakavarga(ch)["sav"]
    by_house = {h: sav[(ch.asc_sign + h - 1) % 12] for h in range(1, 13)}
    return sorted(by_house, key=lambda h: -by_house[h])[:n]


def planet_lines(ch) -> list[tuple[str, str, str]]:
    """(planet, plain sentence, tone) for each planet."""
    out = []
    for p in ac.PLANETS:
        d = ch.planets[p]
        dig = d["dignity"]
        where = HOUSE_PLAIN[d["house"]]
        rules = [HOUSE_SHORT[h] for h in ch.houses_owned(p) if h != d["house"]]
        if dig == "Exalted" and p in ("Rahu", "Ketu"):
            q, t = "is well placed here", "good"
        elif dig == "Exalted":
            q, t = "is very strong here and gives excellent results", "good"
        elif dig == "Own sign":
            q, t = "is strong here, in its own sign", "good"
        elif dig == "Debilitated":
            q, t = "is weak here; results come after effort, and remedies help", "bad"
        elif dig.startswith("Friendly"):
            q, t = "is comfortable here", "good"
        elif dig.startswith("Enemy"):
            q, t = "is uncomfortable here, so results can be uneven", "mixed"
        else:
            q, t = "gives average results here", ""
        txt = f"{PLANET_PLAIN[p][0].upper() + PLANET_PLAIN[p][1:]} sits in your area of {where} and {q}."
        if rules:
            txt += f" It also looks after your {_and(rules)}."
        if d["retro"]:
            txt += " It is retrograde, so its results tend to come later or after a second attempt."
        if d["combust"]:
            txt += " It is very close to the Sun, so its strength is partly hidden."
        out.append((p, txt, t))
    return out


SKY_MEAN = {"Jupiter": "brings growth, guidance and opportunities", "Saturn": "asks for patience and steady work",
            "Rahu": "brings ambition, sudden changes and new experiences", "Ketu": "brings detachment and inner change"}


def sky_now(ch, jd) -> list[tuple[str, str, str]]:
    """Slow planets now: (title, sentence, tone)."""
    out = []
    for r in ac.gochara(ch, jd):
        if r["planet"] not in SKY_MEAN:
            continue
        good = r["result"].startswith("Favourable")
        txt = (f"{r['planet']} is in {r['sign']}, your area of {HOUSE_PLAIN[r['house_from_asc']]}. "
               + (f"It {SKY_MEAN[r['planet']]} there, and the position is supportive for you." if good else
                  f"It usually {SKY_MEAN[r['planet']]}, but from your Moon sign this position is testing, "
                  "so results come more slowly and need patience.")
               + (" It is moving backward (retrograde) now, so review before you push." if r["retro"] else ""))
        b = r.get("bav")
        if r.get("vedha"):
            txt += f" Its good effect is partly blocked by {', '.join(r['vedha'])} right now."
        if b is not None:
            txt += (f" Your chart gives {r['planet']} strong support in this sign ({b} of 8 points)." if b >= 5 else
                    f" Your chart gives {r['planet']} little support in this sign ({b} of 8 points), so go carefully."
                    if b <= 2 else "")
        good = good and not r.get("vedha")
        out.append((r["planet"], txt, "good" if good else "bad"))
    return out


def yoga_simple(ch) -> list[str]:
    out = []
    for y in ac.detect_yogas(ch):
        if not y["present"]:
            continue
        key = next((k for k in YOGA_PLAIN if y["name"].startswith(k)), None)
        out.append(f"**{y['name']}**: {YOGA_PLAIN[key] if key else y['meaning']}.")
    return out


def report_html(ch, rep) -> str:
    import html as _h
    parts = [f"<html><head><meta charset='utf-8'><title>{_h.escape(ch.name)} report</title>"
             "<style>body{font-family:Georgia,serif;max-width:760px;margin:40px auto;padding:0 16px;line-height:1.6;color:#222}"
             "h1{margin-bottom:0}h2{border-bottom:1px solid #ddd;padding-bottom:4px;margin-top:28px;color:#7c2d12}"
             "table{border-collapse:collapse}td{padding:4px 12px 4px 0;vertical-align:top}</style></head><body>",
             f"<h1>{_h.escape(ch.name)}</h1><p>Born {ch.dt_local.strftime('%d %b %Y, %H:%M')}, {_h.escape(ch.place or '')}</p>"]
    for t, body in rep["sections"]:
        parts.append(f"<h2>{_h.escape(t)}</h2><p>{_h.escape(' '.join(body))}</p>")
    parts.append("<h2>Lucky for you</h2><table>" + "".join(
        f"<tr><td><b>{_h.escape(k)}</b></td><td>{_h.escape(v)}</td></tr>" for k, v in rep["lucky"]) + "</table>")
    parts.append("<p style='color:#777;font-size:.9em;margin-top:32px'>Traditional astrology for reflection and planning. "
                 "Not medical, legal or financial advice.</p></body></html>")
    return "".join(parts)


def kaal_sarp(ch: ac.Chart) -> bool:
    r = ch.planets["Rahu"]["lon"]
    side = [((ch.planets[p]["lon"] - r) % 360) < 180 for p in ac.PLANETS[:7]]
    return all(side) or not any(side)


def lucky(ch: ac.Chart) -> list[tuple[str, str]]:
    l1, l5, l9 = ch.lord_of_house(1), ch.lord_of_house(5), ch.lord_of_house(9)
    lords = list(dict.fromkeys([l1, l9, l5]))
    root = sum(int(c) for c in str(ch.dt_local.day))
    while root > 9:
        root = sum(int(c) for c in str(root))
    return [("Lucky days", ", ".join(DAYNAME[p] for p in lords)),
            ("Lucky colours", "; ".join(COLOUR[p] for p in lords[:2])),
            ("Lucky numbers", ", ".join(str(NUMBER[p]) for p in lords) + f" (birth-date number {root})"),
            ("Numerology", numerology(ch)),
            ("Helpful planets", ", ".join(p for p in ac.PLANETS[:7]
                                          if ac.functional_nature(ch, p).startswith(("Benefic", "Yogakaraka")))),
            ("Traditional stone", f"{STONE[l1]} (for your Ascendant lord {l1}); consult an astrologer before wearing any stone"),
            ("Ishta Devata (traditional)", __import__("pastlife").past_life_report(ch)["ishta"][1])]


def my_report(ch: ac.Chart, md_list: list, now_jd: float) -> dict:
    P = ch.planets
    asc, mo = ASC[ch.asc_sign], ch.moon_sign
    lr = life.life_reading(ch, md_list, now_jd)
    A = lr["areas"]
    tz = ch.tz
    strong = [p for _, p in lr["strengths"][:2]]
    weak = lr["strengths"][-1][1]
    yogas = [y for y in ac.detect_yogas(ch) if y["present"]]

    def periods(area, kind):
        rows = [p for p in A[area]["good_periods" if kind == "good" else "hard_periods"]
                if p["start"] < now_jd + 365.25 * 30][:3]
        return [f"{ac.jd_to_local(p['start'], tz).strftime('%b %Y')} to {ac.jd_to_local(p['end'], tz).strftime('%b %Y')}"
                for p in rows]

    S = []
    S.append(("About you", [
        asc["p"], MOON_TXT[mo],
        f"Your birth star is {ac.NAKSHATRAS[ch.moon_nak]}. People born under it are usually {life.NAK_TRAITS[ch.moon_nak]}.",
    ]))
    st = [asc["s"]]
    for p in strong:
        st.append(f"{PLANET_PLAIN[p][0].upper() + PLANET_PLAIN[p][1:]} is strong in your chart, in your area of "
                  f"{HOUSE_PLAIN[P[p]['house']]}. This is a natural source of success for you.")
    for y in yogas:
        key = next((k for k in YOGA_PLAIN if y["name"].startswith(k)), None)
        if key and f"Your chart has {YOGA_PLAIN[key]}." not in st:
            st.append(f"Your chart has {YOGA_PLAIN[key]}.")
    top = strongest_areas(ch)
    st.append("Areas where your efforts give the best results: " + _and([HOUSE_SHORT[h] for h in top]) + ".")
    S.append(("Your strengths", st))
    S.append(("Things to work on", [
        asc["w"],
        f"{PLANET_PLAIN[weak][0].upper() + PLANET_PLAIN[weak][1:]} is the weakest planet in your chart. It looks after your "
        f"{_and([HOUSE_SHORT[h] for h in (ch.houses_owned(weak) or [P[weak]['house']])])}, so these need more patience. {REMEDY[weak]}",
    ]))
    S.append(("Happiness and fulfilment", [
        MOON_TXT[mo].split(". ")[1] + "." if ". " in MOON_TXT[mo] else MOON_TXT[mo],
        "Luck and support from elders tend to come when you need them." if A["Life"]["stars"] >= 4 else
        "Good fortune comes, but usually after steady effort.",
        _home_line(ch),
    ]))
    c = A["Career"]
    S.append(("Career", [
        asc["c"], STARS_SENT[c["stars"]], c["details"][0], c["details"][-1],
        ("Best career periods ahead: " + "; ".join(periods("Career", "good")) + ".") if periods("Career", "good") else "",
        ("Periods to be careful at work: " + "; ".join(periods("Career", "bad")) + ".") if periods("Career", "bad") else "",
    ]))
    w = A["Wealth"]
    S.append(("Money and property", [
        STARS_SENT[w["stars"]], *_money_lines(ch),
        ("Best periods for money: " + "; ".join(periods("Wealth", "good")) + ".") if periods("Wealth", "good") else "",
    ]))
    m = A["Marriage"]
    mk = ac.manglik(ch)
    S.append(("Love and marriage", [
        asc["l"], STARS_SENT[m["stars"]], m["details"][0],
        ac.manglik_text(ch),
        ("Good periods for relationships: " + "; ".join(periods("Marriage", "good")) + ".") if periods("Marriage", "good") else "",
        ("Periods that need care in relationships: " + "; ".join(periods("Marriage", "bad")) + ".") if periods("Marriage", "bad") else "",
    ]))
    h = A["Health"]
    S.append(("Health", [
        asc["h"], STARS_SENT[h["stars"]], h["details"][0], h["details"][2],
        ("Periods to look after your health: " + "; ".join(periods("Health", "bad")) + ".") if periods("Health", "bad") else "",
        "These are traditional indications only, not medical advice.",
    ]))
    k = A["Children"]
    S.append(("Children and family", [STARS_SENT[k["stars"]], k["details"][-1],
                                      ("Supportive periods for children and family: " + "; ".join(periods("Children", "good")) + ".")
                                      if periods("Children", "good") else ""]))
    # current period
    chain = lr["chain"]
    cur = []
    if len(chain) >= 2:
        md, ad = chain[0], chain[1]
        row = next((r for r in life.dasha_periods(ch, md_list) if r["md"] == md.lord and r["ad"] == ad.lord
                    and abs(r["start"] - ad.start) < 1), None)
        cur.append(f"Until {ac.jd_to_local(ad.end, tz).strftime('%d %b %Y')}, you are in the {ad.lord} phase of your "
                   f"{md.lord} main period (which runs until {ac.jd_to_local(md.end, tz).strftime('%b %Y')}).")
        if row:
            cur.append(f"This phase is {row['rating'].lower()} overall and touches {row['areas'].lower()}. {row['guidance']}")
        nxt = next((r for r in life.dasha_periods(ch, md_list) if r["start"] >= ad.end - 1), None)
        if nxt:
            cur.append(f"Next phase: {nxt['ad']} (from {ac.jd_to_local(nxt['start'], tz).strftime('%d %b %Y')}), "
                       f"which looks {nxt['rating'].lower()}. {nxt['guidance']}")
    S.append(("Your current period", cur))
    # doshas
    ds = []
    ss = [s for s in ac.sade_sati(ch, 95) if "Sade Sati" in s["phase"] and s["end"] > now_jd]
    if ss and ss[0]["start"] <= now_jd:
        end = max(s["end"] for s in ss if s["start"] - ss[0]["start"] < 365.25 * 9)
        ds.append(f"You are in Sade Sati (Saturn's 7½-year phase) until about {ac.jd_to_local(end, tz).strftime('%b %Y')}. "
                  "It brings pressure and slower results but builds maturity. " + REMEDY["Saturn"])
    elif ss:
        ds.append(f"Your next Sade Sati (Saturn's 7½-year phase) begins around {ac.jd_to_local(ss[0]['start'], tz).strftime('%b %Y')}.")
    ds.append("Kaal Sarp yoga is present: all planets sit on one side of Rahu and Ketu, which can bring ups and downs "
              "before steady success. " + REMEDY["Rahu"] if kaal_sarp(ch) else "No Kaal Sarp yoga in your chart.")
    S.append(("Doshas (special conditions)", ds))
    rem = list(dict.fromkeys([weak] + [p.lord for p in chain[:2]]))
    S.append(("Simple remedies for you", [f"{PLANET_PLAIN[p].split(' (')[0].capitalize()}: {REMEDY[p]}" for p in rem]))
    import re as _re
    S = [(t, [_re.sub(r" \(\w+ on the 7th\)", "", x).replace("transits through the 5th", "Jupiter passing through your children area")
              for x in body if x]) for t, body in S]
    return dict(sections=S, lucky=lucky(ch))


# ---------------------------------------------------------------------------
# Today
# ---------------------------------------------------------------------------

def day_reading(ch: ac.Chart, md_list: list, d: date, lat: float, lon: float, tz: str) -> dict:
    fc = ac.daily_forecast(ch, d, lat, lon, tz)
    pc = fc["panchang"]
    h = fc["house_from_asc"]
    theme, work, money, love, health = DAY[h]
    tara, tq = fc["tara"], fc["tara_quality"]
    tithi = pc["tithi"][0][2] if len(pc["tithi"]) == 1 else pc["tithi"][min(1, len(pc["tithi"]) - 1)][2]
    hm = lambda j: ac.jd_to_local(j, tz).strftime("%I:%M %p").lstrip("0")
    notes = []
    if tq == "good":
        work += " The stars are friendly for you today, so it is a good day to start something important."
    elif tara == "Naidhana":
        work += " Avoid risks and important decisions today; plans may not go as expected."
    elif tara == "Janma":
        notes.append("It is your birth-star day: keep calm and look after your health.")
    else:
        work += " The day's star is not friendly for you, so finish pending work rather than starting something new."
    if fc["house_from_moon"] == 8:
        love = "The Moon is in a sensitive position for you, so feelings can be hurt easily. Avoid arguments and big decisions."
    if tithi in ac.RIKTA_TITHIS:
        money += " Avoid starting new ventures or big purchases today."
    if tithi == 15:
        notes.append("Full moon: emotions are strong; good for prayer and gratitude.")
    if tithi == 30:
        notes.append("New moon: energy is low; good for rest and prayers for ancestors.")
    if tithi in (11, 26):
        notes.append("Ekadashi: good for fasting, prayer and simple food.")
    vl = ac.WEEKDAY_LORD[d.weekday()]
    wins = fc["good_windows"][:3]
    fallback = False
    if not wins:  # no friendly-star window: use safe hours ruled by helpful planets, plus Abhijit
        bad = [pc["rahu_kalam"], pc["yamagandam"], pc["gulika"]]
        ok_lords = {"Jupiter", "Venus", "Mercury", "Moon"} | {
            p for p in ac.PLANETS[:7] if ac.functional_nature(ch, p).startswith(("Benefic", "Yogakaraka"))}
        cand = [(h["start"], h["end"]) for h in pc["horas"] if h["day"] and h["lord"] in ok_lords]
        if d.weekday() != 2:
            cand.append(pc["abhijit"])
        cand = [(a, b) for a, b in sorted(cand) if not any(not (b <= x0 or a >= x1) for x0, x1 in bad)]
        merged = []
        for a, b in cand:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
            else:
                merged.append((a, b))
        wins, fallback = merged[:3], True
    best = ", ".join(f"{hm(a)}–{hm(b)}" for a, b in wins) or "keep to routine work today"
    if fallback and wins:
        notes.append("The day's star is not ideal for new starts, so these are the safest hours for important work.")
    avoid = (f"{hm(pc['rahu_kalam'][0])}–{hm(pc['rahu_kalam'][1])} (Rahu Kalam), "
             f"{hm(pc['yamagandam'][0])}–{hm(pc['yamagandam'][1])} (Yamagandam)")
    return dict(score=fc["score"], verdict=_verdict(fc["score"]), theme=theme,
                areas=[("Work", work), ("Money", money), ("Love and family", love), ("Health", health)],
                notes=notes, colour=COLOUR[vl], best=best, avoid=avoid)


# ---------------------------------------------------------------------------
# Plain events and period readings
# ---------------------------------------------------------------------------

def plain_events(ch: ac.Chart, md_list: list, j0: float, j1: float, include_pd: bool = True) -> list[tuple]:
    out = []
    tz = ch.tz
    for p in ("Jupiter", "Saturn", "Rahu", "Mars", "Sun", "Venus", "Mercury"):
        if p in ("Sun", "Venus", "Mercury") and j1 - j0 > 120:
            continue
        for s, e, sg in ac._scan_segments(p, ch, j0, j1, step=0.5 if p in ("Sun", "Venus", "Mercury") else 1)[1:]:
            hh = ch.house_of_sign(sg)
            good = hh in pr.GOOD_FROM_LAGNA.get(p, {1, 2, 4, 5, 7, 9, 10, 11})
            out.append((s, f"{p} moves into your area of {HOUSE_PLAIN[hh]}. It {TRANSIT_PLAIN[p]} your "
                           f"{HOUSE_PLAIN[hh]}.", "good" if good else "care"))
            if p == "Rahu":
                kh = ch.house_of_sign((sg + 6) % 12)
                out.append((s, f"Ketu moves into your area of {HOUSE_PLAIN[kh]}. It {TRANSIT_PLAIN['Ketu']} your "
                               f"{HOUSE_PLAIN[kh]}.", "care"))
    for p in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        t, prev = j0, ac.sidereal_lon(j0, p, ch.ayanamsa)[1] < 0
        while t < j1:
            t += 1
            r = ac.sidereal_lon(t, p, ch.ayanamsa)[1] < 0
            if r != prev:
                out.append((t, f"{p} turns {'backward (retrograde)' if r else 'forward (direct)'}: "
                               f"{RETRO_PLAIN[p][0 if r else 1]}.", "care" if r else "good"))
            prev = r
    rows = {(r["md"], r["ad"], round(r["start"])): r for r in life.dasha_periods(ch, md_list)}
    for md in md_list:
        for ad in md.children:
            if j0 <= ad.start < j1:
                r = rows.get((md.lord, ad.lord, round(ad.start)))
                txt = f"A new life phase begins: {ad.lord} period" + (f" ({r['rating'].lower()}). {r['guidance']}" if r else ".")
                out.append((ad.start, txt, "good" if r and r["rating"] == "Good" else "care"))
            if include_pd:
                for q in ad.children:
                    if j0 <= q.start < j1:
                        nat = life._nature(ch, q.lord)
                        out.append((q.start, f"A short sub-phase of {q.lord} begins "
                                             f"({'supportive' if nat > 0 else 'needs care' if nat < 0 else 'neutral'}).",
                                    "good" if nat > 0 else "care"))
    for e in life.eclipse_hits(ch, j0, max(1, int((j1 - j0) / 365.25) + 1)):
        if e["start"] < j1:
            out.append((e["start"], f"{e['event'].split(' on ')[0]} touches a sensitive point in your chart. "
                                    f"Avoid big irreversible decisions in the two weeks around it.", "care"))
    out.sort(key=lambda x: x[0])
    return [(ac.jd_to_local(t, tz).date(), txt, tone) for t, txt, tone in out]


def range_reading(ch: ac.Chart, md_list: list, d0: date, ndays: int, tz: str) -> dict:
    r = pr.predict_range(ch, md_list, d0, ndays, tz)
    days = r["days"]
    rating = r["rating"]["rating"]
    intro = (f"Overall this {'week' if ndays <= 7 else 'month'} looks "
             f"{'favourable' if rating >= 60 else 'mixed' if rating >= 45 else 'demanding'} ({rating}/100).")
    best = sorted(days, key=lambda x: -x["score"])[: 2 if ndays <= 7 else 5]
    worst = sorted(days, key=lambda x: x["score"])[: 1 if ndays <= 7 else 3]
    best_txt = [f"{_fmt(x['date'])}: good for {', '.join(GOODFOR_PLAIN.get(g, g) for g in x['good_for'] if 'rest' not in g) or 'routine work'}."
                for x in sorted(best, key=lambda x: x["date"])]
    worst_txt = [f"{_fmt(x['date'])}: {', '.join(FLAG_SENT[f] for f in x['flags'] if f in FLAG_SENT) or 'a slower day'}; "
                 f"keep it light." for x in sorted(worst, key=lambda x: x["date"])]
    areas = [(a["area"], AREA_SENT[a["area"]][a["verdict"]]) for a in r["areas"]]
    j0 = ac.to_jd(datetime(d0.year, d0.month, d0.day), tz)
    events = plain_events(ch, md_list, j0, j0 + ndays, include_pd=True)
    daily = [dict(date=_fmt(x["date"]), score=x["score"], theme=DAY[x["house_from_asc"]][0],
                  note=", ".join(FLAG_SENT[f] for f in x["flags"] if f in FLAG_SENT))
             for x in days]
    return dict(rating=rating, intro=intro, best=best_txt, careful=worst_txt, areas=areas, events=events, daily=daily)


def year_reading(ch: ac.Chart, md_list: list, d0: date, tz: str) -> dict:
    y = pr.predict_year(ch, md_list, d0, tz)
    months = []
    ranked = sorted(m["rating"] for m in y["months"])
    lo_cut, hi_cut = ranked[2], ranked[-3]
    for m in y["months"]:
        r = m["rating"]
        tone = ("Favourable" if r >= max(hi_cut, 50) or r >= 57 else
                "Needs care" if r <= min(lo_cut, 49) or r < 45 else "Steady")
        line = {"Favourable": "a good month to push important plans",
                "Steady": "a steady month; keep up consistent effort",
                "Needs care": "go carefully; avoid big risks"}[tone]
        months.append(dict(month=m["month"].strftime("%B %Y"), rating=r, tone=tone,
                           text=f"{line}. Best dates: {', '.join(x.strftime('%d %b') for x in m['best_days'])}."
                                + (f" {m['notes'][0]}." if m["notes"] else "")))
    j0 = ac.to_jd(datetime(d0.year, d0.month, 1), tz)
    events = plain_events(ch, md_list, j0, j0 + 366, include_pd=False)
    areas = [(a["area"], AREA_SENT[a["area"]][a["verdict"]]) for a in y["areas"]]
    best = [m["month"].strftime("%B") for m in y["best"]]
    worst = [m["month"].strftime("%B") for m in y["worst"]]
    intro = (f"Overall the coming year looks {'favourable' if y['rating'] >= 57 else 'mixed' if y['rating'] >= 47 else 'demanding'} "
             f"({y['rating']}/100). Your best months are {', '.join(best)}; take more care in {', '.join(worst)}.")
    return dict(intro=intro, months=months, areas=areas, events=events)


def matching_reading(a: ac.Chart, b: ac.Chart) -> dict:
    rows = ac.ashtakoota(a, b)
    total = sum(r["score"] for r in rows)
    verdict = ("an excellent match" if total >= 28 else "a good match" if total >= 24 else
               "an acceptable match" if total >= 18 else "below the traditional minimum of 18")
    get = {r["koota"].split(" (")[0]: r for r in rows}

    def q(name, good, mid):
        s = get[name]["score"] / get[name]["max"]
        return good if s >= 0.75 else mid if s >= 0.4 else None

    pts = [f"Overall score {total:g} out of 36: {verdict}."]
    pts.append(q("Graha Maitri", "Your minds work well together.", "Mental wavelength is average; talk things through.")
               or "You think differently; patience and clear communication help.")
    pts.append(q("Gana", "Your natures are compatible.", "Your natures are somewhat different.")
               or "Your temperaments differ; give each other space.")
    pts.append(q("Bhakoot", "Love, family life and finances are well supported.", "Family and money matters need some care.")
               or "Family and money matters need extra care and agreement.")
    pts.append("Health and children factor (Nadi) is fine." if get["Nadi"]["score"] else
               "Nadi factor is not matched, but the dosha is cancelled by a classical exception." if "cancelled" in get["Nadi"]["detail"]
               else "Nadi factor is not matched; traditionally remedies are suggested, so consult an astrologer.")
    if not get["Bhakoot"]["score"] and "cancelled" in get["Bhakoot"]["detail"]:
        pts.append("The Bhakoot mismatch is cancelled because the Moon-sign lords are the same or friends.")
    sy = ac.synastry(a, b, 5.0)
    pts.append(f"As friends or colleagues: {b.name} is a '{ac.TARA_MEANING[sy['tara_a_to_b'][0]]}' influence for "
               f"{a.name}, and {a.name} is a '{ac.TARA_MEANING[sy['tara_b_to_a'][0]]}' influence for {b.name}.")
    return dict(total=total, verdict=verdict, points=pts)
