"""Printable PDF life report (reportlab). Plain-language content only; no degrees or tables of jargon."""
from __future__ import annotations

import io
import re
from datetime import datetime

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#9a3412")
SOFT = colors.HexColor("#fff7ed")
LINE = colors.HexColor("#e5e7eb")
TONE = {"good": colors.HexColor("#16a34a"), "mixed": colors.HexColor("#d97706"),
        "bad": colors.HexColor("#dc2626"), "care": colors.HexColor("#ea580c"), "": colors.HexColor("#9ca3af")}

S_TITLE = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=INK)
S_SUB = ParagraphStyle("s", fontName="Helvetica", fontSize=10.5, leading=14, textColor=MUTED)
S_H = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=ACCENT,
                     spaceBefore=10, spaceAfter=4)
S_H3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5, leading=13.5, textColor=INK, spaceBefore=4)
S_P = ParagraphStyle("p", fontName="Helvetica", fontSize=10, leading=14.2, textColor=INK, spaceAfter=4)
S_SMALL = ParagraphStyle("sm", fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTED)
S_CARD_L = ParagraphStyle("cl", fontName="Helvetica", fontSize=8, leading=10, textColor=MUTED)
S_CARD_V = ParagraphStyle("cv", fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=INK)
S_CARD_S = ParagraphStyle("cs", fontName="Helvetica", fontSize=8, leading=10, textColor=MUTED)


def _clean(t: str) -> str:
    """Make text safe for the built-in PDF font and for Paragraph markup."""
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿⬀-⯿]", "", t)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = t.replace("→", "to").replace("←", "").replace("▶", "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t).strip()


def _cards(items, width):
    cells = []
    for lab, val, sub, tone in items:
        cells.append([Paragraph(_clean(lab), S_CARD_L), Paragraph(_clean(val), S_CARD_V),
                      Paragraph(_clean(sub), S_CARD_S)])
    n = len(cells)
    w = width / n
    t = Table([[c for c in cells]], colWidths=[w] * n)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
             ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 7),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    for i, (_, _, _, tone) in enumerate(items):
        style += [("BOX", (i, 0), (i, 0), 0.6, LINE), ("BACKGROUND", (i, 0), (i, 0), colors.white),
                  ("LINEBEFORE", (i, 0), (i, 0), 3, TONE.get(tone, LINE))]
    t.setStyle(TableStyle(style))
    return t


def _stars(n: int) -> str:
    return f"{n} of 5"


def _strength_chart(rows, width):
    """rows: (planet, percent, level)"""
    h = 18 * len(rows) + 30
    d = Drawing(width, h)
    left, right = 62, width - 40
    maxv = max(160, max(r[1] for r in rows) + 10)
    sc = (right - left) / maxv
    col = {"Very strong": "#15803d", "Strong": "#22c55e", "Average": "#d97706", "Weak": "#dc2626"}
    y = h - 22
    for p, v, lev in rows:
        d.add(String(0, y + 3, p, fontName="Helvetica", fontSize=9, fillColor=INK))
        d.add(Rect(left, y, v * sc, 11, fillColor=colors.HexColor(col[lev]), strokeColor=None))
        d.add(String(left + v * sc + 4, y + 2, f"{v}%  {lev.lower()}", fontName="Helvetica", fontSize=8,
                     fillColor=MUTED))
        y -= 18
    x100 = left + 100 * sc
    d.add(Line(x100, 8, x100, h - 8, strokeColor=MUTED, strokeDashArray=[3, 3], strokeWidth=0.6))
    d.add(String(x100 - 18, 0, "100% = needed", fontName="Helvetica", fontSize=7, fillColor=MUTED))
    return d


def _footer(name):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, f"{name} - life report - traditional astrology for reflection "
                                            "and planning, not medical, legal or financial advice")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def build(name: str, born: str, cards: list, areas: list, sections: list, planets: list, strength: list,
          lucky: list, periods: list, year: dict | None) -> bytes:
    """
    cards: (label, value, sub, tone); areas: (name, stars, verdict);
    sections: (title, [sentences]); planets: (title, text, tone); strength: (planet, percent, level);
    lucky: (label, value); periods: (when, title, text, tone);
    year: dict(title, summary=[...], phases=[(when, title, text, tone)]) or None.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm, title=f"{name} - Life report", author="CDS Astro")
    W = A4[0] - 36 * mm
    f = []
    f.append(Paragraph(_clean(name), S_TITLE))
    f.append(Paragraph(_clean(born), S_SUB))
    f.append(Paragraph(f"Life report prepared {datetime.now().strftime('%d %b %Y')}", S_SUB))
    f.append(Spacer(1, 10))
    f.append(_cards(cards, W))
    f.append(Spacer(1, 10))
    f.append(Paragraph("Your life at a glance", S_H))
    rows = [[Paragraph(f"<b>{_clean(a)}</b>", S_P), Paragraph(_stars(sn), S_P), Paragraph(_clean(v), S_P)]
            for a, sn, v in areas]
    t = Table(rows, colWidths=[W * 0.3, W * 0.2, W * 0.5])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("BACKGROUND", (0, 0), (-1, -1), SOFT)]))
    f.append(t)
    for title, body in sections:
        f.append(KeepTogether([Paragraph(_clean(title), S_H), Paragraph(_clean(" ".join(body)), S_P)]))
    f.append(PageBreak())
    f.append(Paragraph("Your planets in simple words", S_H))
    for title, text, tone in planets:
        dot = f'<font color="{TONE.get(tone, LINE).hexval().replace("0x", "#")}">&#9632;</font> '
        f.append(KeepTogether([Paragraph(dot + _clean(title), S_H3), Paragraph(_clean(text), S_P)]))
    f.append(Paragraph("How strong each planet is", S_H))
    f.append(_strength_chart(strength, W))
    f.append(Paragraph("Classical six-fold strength (Shadbala). 100% is the minimum a planet needs to give its "
                       "full results.", S_SMALL))
    f.append(Paragraph("Lucky for you", S_H))
    lt = Table([[Paragraph(f"<b>{_clean(k)}</b>", S_P), Paragraph(_clean(v), S_P)] for k, v in lucky],
               colWidths=[W * 0.3, W * 0.7])
    lt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    f.append(lt)
    if year:
        f.append(PageBreak())
        f.append(Paragraph(_clean(year["title"]), S_H))
        for x in year["summary"]:
            f.append(Paragraph(_clean(x), S_P))
        f.append(Paragraph("The year in phases", S_H3))
        for when, title, text, tone in year["phases"]:
            dot = f'<font color="{TONE.get(tone, LINE).hexval().replace("0x", "#")}">&#9632;</font> '
            f.append(Paragraph(f"{dot}<b>{_clean(when)} - {_clean(title)}</b>: {_clean(text)}", S_P))
    f.append(Paragraph("Important periods in your life ahead", S_H))
    for when, title, text, tone in periods:
        dot = f'<font color="{TONE.get(tone, LINE).hexval().replace("0x", "#")}">&#9632;</font> '
        f.append(KeepTogether([Paragraph(f"{dot}<b>{_clean(when)}: {_clean(title)}</b>", S_H3),
                               Paragraph(_clean(text), S_P)]))
    doc.build(f, onFirstPage=_footer(name), onLaterPages=_footer(name))
    return buf.getvalue()
