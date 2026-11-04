"""
AI question-and-answer support.

The app computes everything (positions, dashas, transits, daily factors) and
passes it to the language model as structured text. The model is instructed
to interpret only that data, so answers stay grounded in real calculations.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import astro_core as ac

MODELS = ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"]

SYSTEM_PROMPT = """You are an experienced Vedic (Jyotish) astrologer working inside the CDS Astro app.
You answer questions about the people whose charts are provided in CHART DATA.

Ground rules:
1. Every position, date, dasha period, transit and daily factor in CHART DATA was computed by the app
   (Swiss Ephemeris, settings stated in the data). Use only that data for factual statements. Never invent
   planetary positions, dates or periods. If the data needed is not present, say so plainly and point to the
   app tab that shows it (Birth chart, Dashas, Yogas & Jaimini, Transits & key dates, Daily, Muhurta finder,
   Compatibility).
2. Show your reasoning briefly: name the factors behind each conclusion, with dates
   (for example: "Jupiter enters your 10th house on 26 Jun 2027").
3. Be balanced and honest. Astrology describes tendencies and timing, not certainties. Avoid fear-based
   or fatalistic predictions and never guarantee outcomes. Mention both supportive and challenging factors.
4. Do not give medical diagnoses, legal advice, or specific investment instructions. Give the astrological
   view and recommend a qualified professional where relevant.
5. Do not predict death, the timing of serious illness, or similarly distressing outcomes. Redirect gently
   to what the person can do.
6. Treat other people's charts with respect. Keep relationship readings constructive and private.
7. Write in plain, concise language without idioms. Use short headings, bullet points and small tables with
   dates when they help. Reply in the language the user writes in.
8. Unless stated otherwise, dates and times are in the person's birth time zone, and daily factors are
   computed for their birthplace."""


def _d(jd: float, tz: str) -> str:
    return ac.jd_to_local(jd, tz).strftime("%d %b %Y")


def _chart_block(ch: ac.Chart, md_list: list, now_jd: float, detailed: bool = True) -> list[str]:
    tz = ch.tz
    P = ch.planets
    L = [f"PERSON: {ch.name}",
         f"Birth: {ch.dt_local.strftime('%d %b %Y %H:%M')} at {ch.place or ''} "
         f"({ch.lat:.4f}, {ch.lon:.4f}), time zone {tz}",
         f"Settings: {ch.ayanamsa} ayanamsa ({ch.ayan_value:.4f} deg), {ch.node} node, whole-sign houses",
         f"Ascendant: {ac.SIGNS[ch.asc_sign]} {ac.fmt_deg(ch.asc)} ({ac.NAKSHATRAS[ac.nak_of(ch.asc)]})",
         f"Moon sign: {ac.SIGNS[ch.moon_sign]}; birth star: {ac.NAKSHATRAS[ch.moon_nak]} pada {P['Moon']['pada']}"]
    chain = ac.current_chain(md_list, now_jd)
    if chain:
        L.append("Current Vimshottari: " + " > ".join(
            f"{p.lord} ({_d(p.start, tz)} to {_d(p.end, tz)})" for p in chain))
    if not detailed:
        return L
    L.append("PLANETS (sign, degree, nakshatra-pada, house, dignity, flags, KP star/sub lord, D9 sign, D10 sign):")
    d9, d10 = ac.varga_chart(ch, 9), ac.varga_chart(ch, 10)
    for p in ac.PLANETS:
        d = P[p]
        flags = ",".join(x for x, ok in (("retrograde", d["retro"]), ("combust", d["combust"])) if ok) or "-"
        L.append(f"- {p}: {ac.SIGNS[d['sign']]} {ac.fmt_deg(d['lon'])}, {ac.NAKSHATRAS[d['nak']]}-{d['pada']}, "
                 f"house {d['house']}, {d['dignity']}, {flags}, star {d['star_lord']}/sub {d['sub_lord']}, "
                 f"D9 {ac.SIGNS[d9[p]]}, D10 {ac.SIGNS[d10[p]]}; aspects houses "
                 f"{', '.join(map(str, ac.aspected_houses(p, d['house'])))}; "
                 f"function: {ac.functional_nature(ch, p)}")
    L.append(f"D9 Ascendant: {ac.SIGNS[d9['Asc']]}; D10 Ascendant: {ac.SIGNS[d10['Asc']]}")
    L.append("HOUSE LORDS: " + "; ".join(
        f"{h}: {ch.lord_of_house(h)} in {P[ch.lord_of_house(h)]['house']}" for h in range(1, 13)))
    yogas = [y for y in ac.detect_yogas(ch) if y["present"]]
    L.append("YOGAS PRESENT: " + ("; ".join(f"{y['name']} ({y['detail']})" for y in yogas) or "none detected"))
    L.append("JAIMINI KARAKAS: " + "; ".join(f"{k.split(' (')[0]} = {p}" for k, p, _ in ac.chara_karakas(ch)))
    # dasha detail
    if chain:
        md = chain[0]
        L.append(f"ANTARDASHAS in {md.lord} Mahadasha: " + "; ".join(
            f"{md.lord}-{a.lord} {_d(a.start, tz)} to {_d(a.end, tz)}" for a in md.children))
        idx = md_list.index(md)
        if idx + 1 < len(md_list):
            nxt = md_list[idx + 1]
            L.append(f"NEXT MAHADASHA: {nxt.lord} {_d(nxt.start, tz)} to {_d(nxt.end, tz)}")
        if len(chain) > 1:
            ad = chain[1]
            L.append(f"PRATYANTARS in {md.lord}-{ad.lord}: " + "; ".join(
                f"{q.lord} {_d(q.start, tz)} to {_d(q.end, tz)}" for q in ad.children))
            ai = md.children.index(ad)
            if ai + 1 < len(md.children):
                ad2 = md.children[ai + 1]
                L.append(f"PRATYANTARS in next antardasha {md.lord}-{ad2.lord}: " + "; ".join(
                    f"{q.lord} {_d(q.start, tz)} to {_d(q.end, tz)}" for q in ad2.children))
        L.append(f"Mahadasha {md.lord} meaning for this chart: {ac.dasha_interpretation(ch, md.lord)}")
        if len(chain) > 1:
            L.append(f"Antardasha {chain[1].lord} meaning: {ac.dasha_interpretation(ch, chain[1].lord)}")
    yd = ac.yogini_dasha(ch, 365.25, 3)
    yc = ac.current_chain(yd, now_jd)
    if yc:
        L.append(f"YOGINI DASHA: {yc[0].lord} ({ac.YOGINI_LORD[yc[0].lord]}) {_d(yc[0].start, tz)} to "
                 f"{_d(yc[0].end, tz)}" + (f"; sub-period {yc[1].lord} until {_d(yc[1].end, tz)}" if len(yc) > 1 else ""))
    ss = [s for s in ac.sade_sati(ch, 95) if s["end"] > now_jd][:6]
    L.append("SATURN CYCLES (current and upcoming): " + "; ".join(
        f"{s['phase']} {_d(s['start'], tz)} to {_d(s['end'], tz)}" for s in ss))
    return L


def build_context(ch: ac.Chart, md_list: list, today: date, others: list | None = None,
                  months: int = 24, days: int = 14) -> str:
    tz = ch.tz
    now_jd = ac.to_jd(datetime(today.year, today.month, today.day, 12), tz)
    L = [f"TODAY: {today.strftime('%A %d %b %Y')}", "", "=== MAIN CHART ==="]
    L += _chart_block(ch, md_list, now_jd, detailed=True)

    L.append("")
    L.append(f"TRANSITS ON {today.strftime('%d %b %Y')} (house from Ascendant / from Moon, classical result):")
    for r in ac.gochara(ch, now_jd):
        L.append(f"- {r['planet']}: {r['sign']} {r['degree']} {r['nakshatra']}{' R' if r['retro'] else ''}, "
                 f"house {r['house_from_asc']} / {r['house_from_moon']}, {r['result']}")

    L.append("")
    L.append(f"KEY DATES, next {months} months:")
    for e in ac.key_events(ch, now_jd, months, md_list):
        if e["category"] == "Dasha change (sub-sub)" and e["jd"] > now_jd + 365:
            continue
        L.append(f"- {_d(e['jd'], tz)}: {e['event']}")

    L.append("")
    L.append(f"DAILY OUTLOOK, next {days} days (birthplace; score 0-100 from traditional rules):")
    for k in range(days):
        d = today + timedelta(days=k)
        f = ac.daily_forecast(ch, d, ch.lat, ch.lon, tz)
        pc = f["panchang"]
        naks = ", ".join(f"{ac.NAKSHATRAS[v]} from {ac.jd_to_local(s, tz).strftime('%H:%M')}"
                         for s, e, v in pc["nakshatra"])
        tithi = ac.tithi_name(pc["tithi"][0][2])
        rk = pc["rahu_kalam"]
        win = ", ".join(f"{ac.jd_to_local(a, tz).strftime('%H:%M')}-{ac.jd_to_local(b, tz).strftime('%H:%M')}"
                        for a, b in f["good_windows"]) or "none"
        L.append(f"- {d.strftime('%a %d %b')}: score {f['score']}, tara {f['tara']}, Moon {ac.SIGNS[f['moon_sign']]} "
                 f"(house {f['house_from_asc']} from Asc, {f['house_from_moon']} from Moon), stars: {naks}; "
                 f"tithi at sunrise {tithi}; Rahu Kalam {ac.jd_to_local(rk[0], tz).strftime('%H:%M')}-"
                 f"{ac.jd_to_local(rk[1], tz).strftime('%H:%M')}; good windows {win}")

    for och, omd in (others or []):
        L.append("")
        L.append(f"=== OTHER CHART: {och.name} ===")
        L += _chart_block(och, omd, now_jd, detailed=True)
        sy = ac.synastry(ch, och, 5.0)
        L.append(f"RELATIONSHIP {ch.name} & {och.name}: {och.name} is {sy['tara_a_to_b'][0]} tara for {ch.name}; "
                 f"{ch.name} is {sy['tara_b_to_a'][0]} tara for {och.name}; Ascendants {sy['asc_relation']}; "
                 f"Moon signs {sy['moon_relation']}")
        L.append("Overlays: " + "; ".join(f"{k} {v}" for k, v in sy["overlays"].items()))
        L.append("Contacts: " + "; ".join(f"{c['contact']} ({c['orb']} deg): {c['reading']}"
                                          for c in sy["contacts"][:12]))
        ak = ac.ashtakoota(ch, och)
        L.append(f"Ashtakoota (if {ch.name} is groom): {sum(r['score'] for r in ak):g}/36 - " +
                 ", ".join(f"{r['koota'].split(' (')[0]} {r['score']:g}/{r['max']}" for r in ak))
    return "\n".join(L)


def stream_answer(api_key: str, model: str, context: str, messages: list[dict], max_tokens: int = 2500):
    """Yield text chunks from Claude. Context is cached between turns to save cost."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {"type": "text", "text": "CHART DATA\n" + context, "cache_control": {"type": "ephemeral"}},
        ],
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
