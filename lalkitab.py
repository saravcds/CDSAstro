"""
Lal Kitab layer: planet-in-house readings and simple remedies (original text).

In Lal Kitab every planet keeps its house from the birth chart, and the 1st house is always
treated as Aries. Whether a planet is helpful or troubled is judged from Lal Kitab's own tables
(exaltation, debilitation, permanent house) and from enemy planets sharing the same house.
This is a separate system: it does not change the main ratings. Fear-based statements and
unsafe or wasteful remedies from the old texts are deliberately left out.
"""
from __future__ import annotations

import astro_core as ac

EXALT = {"Sun": {1}, "Moon": {2}, "Mars": {10}, "Mercury": {6}, "Jupiter": {4}, "Venus": {12},
         "Saturn": {7}, "Rahu": {3, 6}, "Ketu": {9, 12}}
DEBIL = {"Sun": {7}, "Moon": {8}, "Mars": {4}, "Mercury": {12}, "Jupiter": {10}, "Venus": {6},
         "Saturn": {1}, "Rahu": {8, 9}, "Ketu": {3, 6}}
PAKKA = {"Sun": {1}, "Moon": {4}, "Mars": {3, 8}, "Mercury": {7}, "Jupiter": {2}, "Venus": {7},
         "Saturn": {8}, "Rahu": {12}, "Ketu": {6}}
ENEMY = {"Sun": {"Venus", "Saturn", "Rahu"}, "Moon": {"Rahu", "Ketu"}, "Mars": {"Mercury", "Ketu"},
         "Mercury": {"Moon"}, "Jupiter": {"Venus", "Mercury", "Rahu"}, "Venus": {"Sun", "Moon", "Rahu"},
         "Saturn": {"Sun", "Moon", "Mars"}, "Rahu": {"Sun", "Venus", "Mars"}, "Ketu": {"Moon", "Mars"}}
RELATION = {"Sun": "father and seniors", "Moon": "mother", "Mars": "brothers", "Mercury": "sisters, daughters and aunts",
            "Jupiter": "teachers and elders", "Venus": "spouse", "Saturn": "workers and the elderly",
            "Rahu": "in-laws", "Ketu": "children and maternal uncles"}

# Safe, simple remedies per planet (original wording of traditional Lal Kitab ideas)
REMEDIES = {
    "Sun": ["Offer water to the rising Sun each morning.", "Respect your father and seniors, and seek their blessings.",
            "Donate wheat or jaggery on Sundays.", "Keep your word at work; avoid taking favours you cannot return.",
            "Start important work after eating something sweet and drinking water."],
    "Moon": ["Take your mother's blessings before important work.", "Keep a small piece of silver with you.",
             "Donate milk or rice on Mondays.", "Drink water from a silver or steel glass and keep a jug of clean water near your bed.",
             "Spend quiet time near water, and avoid making decisions when upset."],
    "Mars": ["Pray to Hanuman on Tuesdays.", "Share sweets with others on Tuesdays.",
             "Keep good relations with your brothers.", "Donate red lentils (masoor dal) on Tuesdays.",
             "Count to ten before reacting in anger; avoid arguments over property."],
    "Mercury": ["Feed green fodder to cows on Wednesdays.", "Respect your sisters, daughters and aunts and give them small gifts.",
                "Donate green moong dal on Wednesdays.", "Keep your teeth and mouth clean, and speak kindly.",
                "Keep promises in business and keep your accounts in order."],
    "Jupiter": ["Apply a small turmeric or saffron tilak on your forehead.", "Respect teachers, elders and spiritual people.",
                "Donate chana dal or yellow items on Thursdays.", "Visit a temple or place of worship on Thursdays.",
                "Keep your conduct honest and avoid gossip."],
    "Venus": ["Donate curd, rice or white clothes on Fridays.", "Respect your spouse and spend quality time together.",
              "Feed a cow on Fridays.", "Keep yourself and your home clean, and use a light perfume.",
              "Keep your promises to your partner and keep the relationship open and honest."],
    "Saturn": ["Help workers, cleaners and elderly people.", "Feed crows or a black dog on Saturdays.",
               "Donate mustard oil on Saturdays.", "Avoid alcohol and stay honest in all dealings.",
               "Light a sesame oil lamp on Saturday evenings."],
    "Rahu": ["Keep a solid silver ball or a small silver item with you.", "Avoid alcohol and shortcuts.",
             "Keep good relations with your in-laws.", "Donate barley or blue cloth to someone in need.",
             "Keep the area near the main door clean and uncluttered."],
    "Ketu": ["Feed dogs, especially on Saturdays.", "Respect your maternal uncles and children.",
             "Donate a black and white blanket to someone in need.", "Pray to Ganesha before starting new work.",
             "Spend a few minutes in silence or meditation each day."],
}

# (gift when helpful, what to watch when troubled) for each planet in each house
PIH = {
    "Sun": {
        1: ("Self-made success, authority and respect from the government or seniors.", "Ego clashes and pressure from seniors; avoid taking things for free."),
        2: ("Earnings through your own name and good family standing.", "Family disputes over money; speak gently."),
        3: ("Courage, a good name and help from siblings.", "Restlessness and strained ties with siblings."),
        4: ("A comfortable home and respect in society.", "Disturbance at home and with your mother; keep home life peaceful."),
        5: ("Intelligent children and success through ideas.", "Worries over children or investments; avoid risky bets."),
        6: ("Victory over rivals and success in service or government work.", "Health strain and disputes at work."),
        7: ("Gains through partnerships and a respected spouse.", "Ego clashes in marriage and partnerships; share decisions."),
        8: ("Protection in difficult times and a long, steady life.", "Sudden pressure from authority; stay honest with taxes and rules."),
        9: ("Luck through father and elders; a principled life.", "Distance from father or mentors; respect elders."),
        10: ("Rise in career and status, often with authority.", "Career ups and downs; avoid conflict with bosses."),
        11: ("Income through influential people and fulfilled ambitions.", "Gains come late; avoid relying on others' promises."),
        12: ("Success abroad or behind the scenes.", "Expenses and poor sleep; keep a regular routine."),
    },
    "Moon": {
        1: ("A kind nature, public liking and good health.", "Mood swings; protect your peace of mind."),
        2: ("Family wealth, good food and a pleasant voice.", "Money comes and goes; save in good months."),
        3: ("Imagination, travel and helpful siblings.", "Unsteady plans; finish what you begin."),
        4: ("Inner peace, a loving mother, home and vehicles.", "Worries at home; care for your mother's health."),
        5: ("Creative mind and happiness through children.", "Emotional decisions about money or children."),
        6: ("Care for others and success in service.", "Anxiety and stomach upsets; avoid emotional disputes."),
        7: ("A caring spouse and gains through partnerships.", "Moodiness in marriage; talk openly."),
        8: ("Strong intuition and protection through elders.", "Emotional ups and downs; seek support early."),
        9: ("Faith, travel and blessings from elders.", "Restless beliefs; keep a steady practice."),
        10: ("Public reputation and work with people.", "Changes in career; avoid rash job moves."),
        11: ("Income through friends and the public.", "Uneven income; budget carefully."),
        12: ("Peace through spirituality and travel.", "Sleeplessness and overspending; rest well."),
    },
    "Mars": {
        1: ("Courage, energy and leadership.", "Anger and accidents; slow down."),
        2: ("Earnings through property and hard work.", "Harsh words in the family; speak softly."),
        3: ("Bravery and support from brothers.", "Quarrels with siblings; settle them early."),
        4: ("Property and vehicles through effort.", "Tension at home and property issues; avoid arguments at home."),
        5: ("Sharp intellect and sporting talent.", "Impulsive investments; think before you act."),
        6: ("Victory over enemies and debts cleared.", "Overwork and minor injuries; rest enough."),
        7: ("An energetic spouse and active partnerships.", "Arguments in marriage; agree on roles."),
        8: ("Protection in crises and gains through research.", "Sudden events; drive carefully and get health checks."),
        9: ("Fighting spirit for your beliefs; luck through effort.", "Disagreements with elders; show respect."),
        10: ("Rise through bold action and leadership.", "Clashes at work; channel energy into results."),
        11: ("Income through property, technology or effort.", "Competitive friends; choose your circle wisely."),
        12: ("Strength abroad or in hospitals and institutions.", "Hidden expenses and anger; exercise regularly."),
    },
    "Mercury": {
        1: ("Quick wit and business sense.", "Overthinking and nervous strain; keep a calm routine."),
        2: ("Earnings through trade, accounts or speech.", "Broken promises can hurt your name; keep your word."),
        3: ("Good communication and helpful siblings.", "Scattered efforts; focus on one task at a time."),
        4: ("Education, comfort and work from home.", "Paperwork issues in property; check documents."),
        5: ("Intelligence and success in planning.", "Speculation losses; research before investing."),
        6: ("Problem-solving skill and success in service.", "Disputes over paperwork; keep records clean."),
        7: ("Smart partners and gains through trade.", "Contract issues; read carefully before signing."),
        8: ("Research ability and gains through insurance or tax work.", "Worry and nervousness; stay positive."),
        9: ("Learning, teaching and travel for education.", "Confused beliefs; learn from a good teacher."),
        10: ("Career through business, IT or communication.", "Too many directions at work; prioritise."),
        11: ("Income through networks and ideas.", "Unreliable friends; verify before trusting."),
        12: ("Foreign trade and research.", "Overspending and poor sleep; avoid late-night worry."),
    },
    "Jupiter": {
        1: ("Wisdom, respect and protection.", "Weight gain and over-confidence; stay disciplined."),
        2: ("Family wealth and wise speech.", "Family duties feel heavy; share them."),
        3: ("Good efforts rewarded and helpful siblings.", "Slow progress; stay patient."),
        4: ("A happy home, property and peace of mind.", "Too much comfort-seeking; keep giving back."),
        5: ("Wise children and good investments.", "Delays around children; keep faith and patience."),
        6: ("Overcoming problems through good conduct.", "Taking on others' debts; avoid standing guarantee."),
        7: ("A wise spouse and good business partners.", "Unequal partnership; set clear terms."),
        8: ("Help appears in hard times; long life.", "Hidden worries; speak to an elder."),
        9: ("Luck, faith and blessings from teachers.", "Rigid beliefs; stay open-minded."),
        10: ("Respect and authority through good work.", "Slow career growth; avoid shortcuts."),
        11: ("Strong income and helpful elder siblings.", "Gains go to others; protect your share."),
        12: ("Spiritual growth and charity.", "Overspending on others; budget your giving."),
    },
    "Venus": {
        1: ("Charm, comfort and attractive looks.", "Over-indulgence; keep balance."),
        2: ("Wealth, good food and a happy family.", "Spending on luxury; save regularly."),
        3: ("Creative talent and a pleasant social life.", "Distraction from goals; stay focused."),
        4: ("A beautiful home and vehicles.", "Expectations at home; show appreciation."),
        5: ("Romance, creativity and joy through children.", "Emotional decisions in love or money."),
        6: ("Success in health, beauty or service work.", "Small troubles in married life; be patient with your spouse."),
        7: ("A loving spouse and gains through partnerships.", "Over-dependence on your partner; keep your own interests."),
        8: ("Gains through marriage or inheritance.", "Secrets in relationships; stay transparent."),
        9: ("Luck in love and money; love of travel.", "Lavish travel; plan your budget."),
        10: ("Career in arts, design, finance or hospitality.", "Mixing work and romance; keep boundaries."),
        11: ("Income through friends, women and luxury trades.", "Easy come, easy go; save part of gains."),
        12: ("Comfort, rest and pleasures; good for foreign links.", "High spending on comforts; budget wisely."),
    },
    "Saturn": {
        1: ("Discipline and steady rise over time.", "Early struggles and low mood; keep going."),
        2: ("Wealth through steady work and saving.", "Family duties feel heavy; speak kindly."),
        3: ("Persistence and success in long projects.", "Delays in efforts; plan for the long term."),
        4: ("Property later in life.", "A heavy atmosphere at home; keep it clean and peaceful."),
        5: ("A serious, practical mind.", "Delays around children; take care and be patient."),
        6: ("Victory over rivals through patience.", "Long-standing disputes; settle them fairly."),
        7: ("A mature, loyal spouse and stable partnerships.", "Delay or coldness in marriage; show warmth."),
        8: ("Long life and gains through research or inheritance.", "Chronic stress; get regular health checks."),
        9: ("Luck after effort; traditional values.", "Formal relations with father; stay respectful."),
        10: ("A solid career and authority over time.", "Slow promotions; keep working steadily."),
        11: ("Lasting gains and influential older friends.", "Late income; avoid shortcuts."),
        12: ("Spiritual discipline and work abroad.", "Expenses on duties; guard your sleep."),
    },
    "Rahu": {
        1: ("Ambition and a modern outlook.", "Confusion about direction; stay grounded."),
        2: ("Gains from foreign or unusual sources.", "Unclear money dealings in the family; keep accounts clean."),
        3: ("Daring, success in media and technology.", "Taking too many risks; choose them carefully."),
        4: ("Property in new places.", "Restlessness at home; build a calm routine."),
        5: ("Unusual ideas and sharp intelligence.", "Speculation and quick-money schemes; avoid them."),
        6: ("Defeating rivals with clever strategy.", "Hidden opponents; keep your plans private."),
        7: ("Profitable dealings with foreigners.", "Misunderstandings in marriage; build trust."),
        8: ("Sudden gains through research or insurance.", "Sudden events and addictions; stay careful."),
        9: ("Learning from foreign cultures and travel.", "Doubts about beliefs; respect teachers."),
        10: ("Fast career rise in modern fields.", "Ethical shortcuts at work; stay honest."),
        11: ("Big gains and large networks.", "Wrong company; choose friends wisely."),
        12: ("Success abroad and spiritual insight.", "Unexpected expenses and worry at night; plan ahead."),
    },
    "Ketu": {
        1: ("Intuition and spiritual strength.", "Uncertainty about yourself; set clear goals."),
        2: ("Simple living and plain speech.", "Neglecting family money; save steadily."),
        3: ("Courage and technical skill.", "Distance from siblings; stay in touch."),
        4: ("Peace through spirituality.", "Frequent moves; create stability at home."),
        5: ("Deep, intuitive intelligence.", "Worries about children; give them time."),
        6: ("Victory over enemies and illness.", "Minor health issues; take care early."),
        7: ("A spiritual outlook in marriage.", "Detachment in partnerships; spend time together."),
        8: ("Strong intuition and research skill.", "Sudden changes; keep health checks regular."),
        9: ("Spiritual wisdom and pilgrimages.", "Questioning tradition too much; find a good guide."),
        10: ("Success through skill, not show.", "Career changes; build one strong skill."),
        11: ("Unexpected gains.", "Few friends; nurture a small circle."),
        12: ("Spiritual growth and peace.", "Expenses on health or travel; plan ahead."),
    },
}


def status(ch: ac.Chart, p: str) -> tuple[str, str]:
    """('helpful' | 'mixed' | 'troubled', reason)"""
    h = ch.planets[p]["house"]
    mates = [q for q in ac.PLANETS if q != p and ch.planets[q]["house"] == h]
    enemies = [q for q in mates if q in ENEMY[p]]
    if h in DEBIL[p]:
        return "troubled", "this is a weak house for it in Lal Kitab"
    if enemies:
        return "troubled", f"it shares the house with {', '.join(enemies)}, which Lal Kitab treats as unfriendly"
    if h in EXALT[p]:
        return "helpful", "this is its strongest house in Lal Kitab"
    if h in PAKKA[p]:
        return "helpful", "this is its own permanent house in Lal Kitab"
    return "mixed", "results depend on how you use this planet's energy"


def reading(ch: ac.Chart) -> list[dict]:
    out = []
    for p in ac.PLANETS:
        h = ch.planets[p]["house"]
        st, why = status(ch, p)
        gift, watch = PIH[p][h]
        pool = REMEDIES[p]
        rem = [pool[(h - 1) % len(pool)], pool[h % len(pool)]]
        if st == "troubled":
            rem.append(pool[(h + 1) % len(pool)])
        out.append(dict(planet=p, house=h, status=st, why=why, gift=gift, watch=watch, remedies=rem,
                        relation=RELATION[p]))
    return out


def top_remedies(ch: ac.Chart, chain: list, n: int = 3) -> list[tuple[str, str]]:
    """Most useful remedies now: running period lords first, then troubled planets."""
    rd = {r["planet"]: r for r in reading(ch)}
    order = [p.lord for p in chain[:2]] + [r["planet"] for r in rd.values() if r["status"] == "troubled"]
    out, seen = [], set()
    for p in order:
        if p in seen:
            continue
        seen.add(p)
        out.append((p, REMEDIES[p][0]))
        if len(out) >= n:
            break
    return out
