#!/usr/bin/env python3
"""Original artwork for *Going Concern*.

Every visual is built once as a reportlab Drawing and used twice: embedded
as a vector flowable in dist/book.pdf, and exported to assets/*.svg (via
reportlab.graphics.renderSVG) for the markdown edition on GitHub.

Design language: ink black on paper, one alarm-red accent, Helvetica only.
All figures are original and licensed CC BY 4.0 like the rest of the book.

Run from the project root:

    python automation/build_pdf.py     # exports assets/ and builds the PDF
"""
import os
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, PolyLine, Circle, Polygon,
)
from reportlab.pdfbase.pdfmetrics import stringWidth

# --- palette ---------------------------------------------------------------
INK = HexColor("#16161A")       # near-black
RED = HexColor("#C8102E")       # the alarm accent
GREY = HexColor("#6B6B70")      # secondary text
GREY_L = HexColor("#9A9AA0")    # secondary text on dark
LIGHT = HexColor("#DDDDD8")     # rules and borders
FAINT = HexColor("#F2F2EE")     # card fills
GRID = HexColor("#26262C")      # grid lines on the dark cover
PAPER = HexColor("#FFFFFF")

FONT = "Helvetica"
BOLD = "Helvetica-Bold"
OBLIQUE = "Helvetica-Oblique"

# A4, to the point
PAGE_W, PAGE_H = 595.27, 841.89


# --- small helpers ---------------------------------------------------------

def T(d, x, y, s, size=8, font=FONT, fill=INK, anchor="start"):
    d.add(String(x, y, s, fontName=font, fontSize=size, fillColor=fill,
                 textAnchor=anchor))


def wrap(text, font, size, maxw):
    """Greedy word-wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if stringWidth(trial, font, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrapped(d, x, y, text, size, font, fill, maxw, leading, anchor="start",
            max_lines=None):
    lines = wrap(text, font, size, maxw)
    if max_lines:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        T(d, x, y - i * leading, ln, size, font, fill, anchor)
    return len(lines)


def chrome(d, title, source=None):
    """Shared figure furniture: title, rule, optional source note."""
    T(d, 0, d.height - 5, title.upper(), 9.5, BOLD, INK)
    d.add(Line(0, d.height - 11, d.width, d.height - 11, strokeColor=INK,
               strokeWidth=0.8))
    if source:
        T(d, 0, 5, source, 6.5, OBLIQUE, GREY)


def arrow(d, x1, y, x2, color=RED, width=1.1):
    """Horizontal arrow pointing left, from x1 to x2 (x2 < x1)."""
    d.add(Line(x1, y, x2 + 5, y, strokeColor=color, strokeWidth=width))
    d.add(Polygon(points=[x2, y, x2 + 6, y + 3, x2 + 6, y - 3],
                  fillColor=color, strokeColor=color))


# --- figure 1: timeline ----------------------------------------------------

_TIMELINE = [
    ("2024",         "Internal complaint dismissed; whistleblower later surveilled"),
    ("29 May 2026",  "CEO Yates resigns; head of audit goes"),
    ("Jun 2026",     "ASIC probe; federal-work ban; Sheppard resigns as chairman"),
    ("19 Jun 2026",  "First public hearing, Canberra"),
    ("2 Jul 2026",   "Sheppard and Thomas front the Westpac board"),
    ("6–12 Aug 2026", "Ebeid elected chair, unopposed"),
    ("14 Aug 2026",  "'KPMG Part Deux' hearing, Canberra"),
    ("16 Aug 2026",  "Ruling opens the partner shield to attack"),
    ("19 Aug 2026",  "500-role cull; ASIC whistleblower probe; $557m debt revealed"),
]


def timeline():
    d = Drawing(450, 205)
    chrome(d, "The affair on one page",
           "Dates and events as sourced in the chapter notes, chapters "
           "1–13.")
    spine_y = 102
    d.add(Line(20, spine_y, 430, spine_y, strokeColor=INK, strokeWidth=1))
    for i, (date, label) in enumerate(_TIMELINE):
        x = 45 + i * 45
        last = i == len(_TIMELINE) - 1
        dot_fill = RED if last else PAPER
        d.add(Circle(x, spine_y, 3.2, fillColor=dot_fill, strokeColor=INK,
                     strokeWidth=1))
        above = i % 2 == 0
        if above:
            d.add(Line(x, spine_y + 4, x, spine_y + 14, strokeColor=LIGHT,
                       strokeWidth=0.8))
            T(d, x, spine_y + 44, date, 7.5, BOLD, RED if last else INK,
              anchor="middle")
            wrapped(d, x, spine_y + 34, label, 6.3, FONT, GREY, 84, 8,
                    anchor="middle", max_lines=3)
        else:
            d.add(Line(x, spine_y - 4, x, spine_y - 14, strokeColor=LIGHT,
                       strokeWidth=0.8))
            T(d, x, spine_y - 24, date, 7.5, BOLD, RED if last else INK,
              anchor="middle")
            wrapped(d, x, spine_y - 34, label, 6.3, FONT, GREY, 84, 8,
                    anchor="middle", max_lines=3)
    return d


# --- figure 2: the breach flow ---------------------------------------------

def breach_flow():
    d = Drawing(450, 175)
    chrome(d, "How the papers travelled — as alleged",
           "Allegations made under parliamentary privilege; contested in part "
           "by the firm. See chapter 4 notes.")
    boxes = [
        (0,   "LENDLEASE BOARD PAPERS",
         "Confidential strategy, projections and deal terms of KPMG's audit client."),
        (158, "KPMG AUDIT TEAM",
         "Six partners alleged to have accessed rival proposals; a client-winning "
         "war room; 'no Chinese wall'."),
        (316, "RIVAL PITCHES",
         "Tenders at Optus, Telstra, Dexus and Westpac."),
    ]
    bw, bh, by = 134, 76, 40
    for x, title, body in boxes:
        hot = title == "KPMG AUDIT TEAM"
        d.add(Rect(x, by, bw, bh, fillColor=FAINT,
                   strokeColor=RED if hot else LIGHT,
                   strokeWidth=1.2 if hot else 0.8))
        T(d, x + 9, by + bh - 16, title, 8, BOLD, INK)
        wrapped(d, x + 9, by + bh - 30, body, 6.4, FONT, GREY, bw - 18, 8.5)
    for x1, x2 in ((bw, bw + 24), (bw + 158, bw + 182)):
        mid = by + bh / 2
        d.add(Line(x1, mid, x2 - 5, mid, strokeColor=INK, strokeWidth=1.1))
        d.add(Polygon(points=[x2, mid, x2 - 6, mid + 3.2, x2 - 6, mid - 3.2],
                      fillColor=INK, strokeColor=INK))
    return d


# --- figure 3: the cast -----------------------------------------------------

_CAST_COLS = [
    ("GONE", RED, [
        ("Andrew Yates", "CEO — resigned 29 May 2026"),
        ("Martin Sheppard", "chairman — resigned 23 Jun 2026"),
        ("Julian McPherson", "head of audit"),
        ("Eileen Hoggett", "COO — expelled from the partnership, Aug 2026"),
        ("Paul Rogers", "audit partner — named under privilege"),
        ("Kim Lawry", "audit partner — removed from Westpac audit"),
        ("Louise Capon", "general counsel — stepped down, Aug 2026"),
        ("Dorothy Hisgrove", "chief people officer — stepped down, Aug 2026"),
    ]),
    ("IN CHARGE NOW", INK, [
        ("Michael Ebeid", "chair — elected unopposed, 6–12 Aug 2026"),
        ("John Sams", "CEO since Aug 2026 — running the cull"),
        ("Gary Wingrove", "incoming global chair, KPMG International"),
        ("Bill Thomas", "outgoing global chair — fronted Westpac, 2 Jul"),
    ]),
    ("THE PRESSURE", GREY, [
        ("Sen. Deborah O'Neill", "chaired both the PwC and KPMG inquiries"),
        ("Sen. Barbara Pocock", "questions on notice that surfaced the ASIC probe"),
        ("ASIC", "investigating whistleblower-protection breaches"),
        ("The whistleblower", "unnamed in this book, by design"),
    ]),
]


def cast():
    d = Drawing(450, 310)
    chrome(d, "The cast at August 2026",
           "Names and roles as reported; see chapter 5 notes.")
    col_w = 146
    for ci, (header, hue, rows) in enumerate(_CAST_COLS):
        x = ci * 152
        d.add(Rect(x, 276, 6, 6, fillColor=hue, strokeColor=hue))
        T(d, x + 11, 277, header, 8, BOLD, hue)
        d.add(Line(x, 270, x + col_w, 270, strokeColor=LIGHT, strokeWidth=0.8))
        for ri, (name, role) in enumerate(rows):
            y = 252 - ri * 26
            T(d, x, y, name, 7.8, BOLD, INK)
            wrapped(d, x, y - 9.5, role, 6.4, FONT, GREY, col_w - 4, 7.5,
                    max_lines=2)
    return d


# --- figure 4: the shield ---------------------------------------------------

_SHIELD_BANDS = [  # bottom -> top
    ("THE CONDUCT", "alleged misuse of client board papers", FAINT, INK),
    ("THE LLP STRUCTURE", "the firm's liability, not the partner's", FAINT, INK),
    ("THE STATUTORY CAPS", "professional standards scheme, administered via CA ANZ", FAINT, INK),
    ("LEGAL PROFESSIONAL PRIVILEGE", "the investigation files stay sealed", INK, PAPER),
]

_SHIELD_ATTACKS = [  # (band index, label)
    (0, "parliamentary privilege — the allegations aired"),
    (2, "Lyon v CA ANZ — the caps challenged"),
    (3, "the 16 Aug ruling — secrecy opened to attack"),
]


def shield():
    d = Drawing(450, 250)
    chrome(d, "The shield — and where it is cracking",
           "See chapter 11; the 16 Aug 2026 ruling as reported by The Australian.")
    bw, bh, gap, x0 = 240, 40, 8, 0
    for bi, (title, sub, fill, txt) in enumerate(_SHIELD_BANDS):
        y = 16 + bi * (bh + gap)
        d.add(Rect(x0, y, bw, bh, fillColor=fill, strokeColor=LIGHT if fill == FAINT else INK,
                   strokeWidth=0.8))
        T(d, x0 + 10, y + bh - 15, title, 7.8, BOLD, txt)
        T(d, x0 + 10, y + bh - 27, sub, 6.4, FONT,
          GREY if txt == INK else GREY_L)
    for bi, label in _SHIELD_ATTACKS:
        y = 16 + bi * (bh + gap) + bh / 2
        arrow(d, 438, y, bw + 8)
        wrapped(d, 438, y + 8, label, 6.4, FONT, RED, 200, 8, anchor="end",
                max_lines=2)
    return d


# --- figure 5: the scoreboard -----------------------------------------------

_SCOREBOARD = [
    ("$1",      "agreed price of the defence unit; Capgemini assumes about $200m in entitlements", RED),
    ("$557m",   "partnership borrowings — 'record high personal borrowings' under former CEO Yates", INK),
    ("~$814k",  "implied personal liability per partner — 'a surprisingly large figure'", INK),
    ("$300k",   "debt-funded buy-in now facing anyone joining the partnership", INK),
    ("$442m",   "government contracts under reconsideration", INK),
    ("$2m",     "reported executive payouts ahead of the August inquiry", INK),
    ("50 + 450","partners and client-facing staff in the August cull", INK),
    ("<10,000", "staff remaining — 'a little less than 10,000', and shrinking further", INK),
]


def scoreboard():
    d = Drawing(450, 235)
    chrome(d, "The scoreboard, August 2026",
           "Figures as reported; see the notes in chapters 9-13.")
    cw, ch, gx, gy = 105, 88, 10, 12
    for i, (value, label, hue) in enumerate(_SCOREBOARD):
        row, col = divmod(i, 4)
        x = col * (cw + gx)
        y = 118 - row * (ch + gy)
        d.add(Rect(x, y, cw, ch, fillColor=FAINT, strokeColor=LIGHT,
                   strokeWidth=0.8))
        T(d, x + 9, y + ch - 22, value, 15, BOLD, hue)
        wrapped(d, x + 9, y + ch - 34, label, 6.3, FONT, GREY, cw - 18, 7.5,
                max_lines=6)
    return d


# --- the cover --------------------------------------------------------------

def cover():
    d = Drawing(PAGE_W, PAGE_H)
    d.add(Rect(0, 0, PAGE_W, PAGE_H, fillColor=INK, strokeColor=INK))

    # masthead
    d.add(Rect(48, 786, 26, 4, fillColor=RED, strokeColor=RED))
    T(d, 82, 787, "AN OPEN BOOK  ·  WRITTEN IN PUBLIC  ·  CC BY 4.0",
      7.5, BOLD, GREY_L)

    # the going-concern chart
    cx0, cx1, cy0, cy1 = 48, 547, 470, 740
    for i in range(9):  # vertical grid
        x = cx0 + i * (cx1 - cx0) / 8
        d.add(Line(x, cy0, x, cy1, strokeColor=GRID, strokeWidth=0.6))
    for j in range(7):  # horizontal grid
        y = cy0 + j * (cy1 - cy0) / 6
        d.add(Line(cx0, y, cx1, y, strokeColor=GRID, strokeWidth=0.6))

    thr = 560  # the threshold the firm falls through
    d.add(Line(cx0, thr, cx1, thr, strokeColor=RED, strokeWidth=1,
               strokeDashArray=[5, 4]))
    d.add(Rect(cx1 - 4, thr - 2, 4, 4, fillColor=RED, strokeColor=RED))

    pts = [(48, 700), (110, 692), (172, 700), (234, 664), (296, 672),
           (358, 628), (420, 600), (482, 586)]
    d.add(PolyLine([p for pt in pts for p in pt], strokeColor=PAPER,
                   strokeWidth=1.6))
    for px, py in pts:
        d.add(Rect(px - 2.2, py - 2.2, 4.4, 4.4, fillColor=PAPER,
                   strokeColor=PAPER))
    # the fall, below the threshold, off the chart
    d.add(PolyLine([482, 586, 512, 532, 536, 492], strokeColor=RED,
                   strokeWidth=1.6, strokeDashArray=[4, 3]))
    d.add(Circle(536, 492, 4, fillColor=RED, strokeColor=RED))

    # title block
    T(d, 48, 392, "GOING", 66, BOLD, PAPER)
    T(d, 48, 318, "CONCERN", 66, BOLD, PAPER)
    d.add(Rect(48, 298, 214, 5, fillColor=RED, strokeColor=RED))
    T(d, 48, 264, "The KPMG Australia audit scandal", 17, FONT, PAPER)
    T(d, 48, 234, "An open book, written as it happened — from the", 10, FONT,
      GREY_L)
    T(d, 48, 220, "whistleblower's complaint to the $1 fire sale.", 10, FONT,
      GREY_L)

    # footer
    d.add(Rect(48, 54, 5, 5, fillColor=RED, strokeColor=RED))
    T(d, 60, 55, "github.com/catchfu/going-concern-book", 8.5, FONT, GREY_L)
    T(d, PAGE_W - 48, 55, "AUGUST 2026  ·  DRAFT V0.2", 8.5, BOLD, GREY_L,
      anchor="end")
    T(d, 60, 42, "Licensed CC BY 4.0 — creativecommons.org/licenses/by/4.0",
      7, FONT, HexColor("#55555C"))
    return d


# --- export -----------------------------------------------------------------

FIGURES = {
    "cover": cover,
    "timeline": timeline,
    "breach": breach_flow,
    "cast": cast,
    "shield": shield,
    "scoreboard": scoreboard,
}


# --- SVG export -------------------------------------------------------------
# reportlab's renderSVG needs cairo (unavailable here), so serialise the few
# shape types this module uses directly. SVG's y axis points down; reportlab's
# points up, so every y is flipped via y' = height - y.

def _svg_color(c):
    if c is None:
        return "none"
    return "#%02x%02x%02x" % (round(c.red * 255), round(c.green * 255),
                              round(c.blue * 255))


def _dash(s):
    return f' stroke-dasharray="{",".join(str(v) for v in s.strokeDashArray)}"' \
        if s.strokeDashArray else ""


def _shape_svg(s, h):
    flip = lambda y: h - y  # noqa: E731
    if isinstance(s, Rect):
        return (f'<rect x="{s.x}" y="{flip(s.y) - s.height}" '
                f'width="{s.width}" height="{s.height}" '
                f'fill="{_svg_color(s.fillColor)}" '
                f'stroke="{_svg_color(s.strokeColor)}" '
                f'stroke-width="{s.strokeWidth}"{_dash(s)}/>')
    if isinstance(s, Line):
        return (f'<line x1="{s.x1}" y1="{flip(s.y1)}" x2="{s.x2}" '
                f'y2="{flip(s.y2)}" stroke="{_svg_color(s.strokeColor)}" '
                f'stroke-width="{s.strokeWidth}"{_dash(s)}/>')
    if isinstance(s, PolyLine):
        pts = " ".join(f"{x},{flip(y)}" for x, y in _pairs(s.points))
        return (f'<polyline points="{pts}" fill="none" '
                f'stroke="{_svg_color(s.strokeColor)}" '
                f'stroke-width="{s.strokeWidth}"{_dash(s)}/>')
    if isinstance(s, Polygon):
        pts = " ".join(f"{x},{flip(y)}" for x, y in _pairs(s.points))
        return (f'<polygon points="{pts}" fill="{_svg_color(s.fillColor)}" '
                f'stroke="{_svg_color(s.strokeColor)}" '
                f'stroke-width="{s.strokeWidth}"/>')
    if isinstance(s, Circle):
        return (f'<circle cx="{s.cx}" cy="{flip(s.cy)}" r="{s.r}" '
                f'fill="{_svg_color(s.fillColor)}" '
                f'stroke="{_svg_color(s.strokeColor)}" '
                f'stroke-width="{s.strokeWidth}"/>')
    if isinstance(s, String):
        return (f'<text x="{s.x}" y="{flip(s.y)}" '
                f'font-family="Helvetica, Arial, sans-serif" '
                f'font-size="{s.fontSize}" fill="{_svg_color(s.fillColor)}" '
                f'text-anchor="{s.textAnchor}">{escape(s.text)}</text>')
    raise TypeError(f"unsupported shape: {type(s).__name__}")


def _pairs(flat):
    it = iter(flat)
    return zip(it, it)


def drawing_to_svg(d, background="#ffffff"):
    body = "\n".join(_shape_svg(s, d.height) for s in d.contents)
    bg = (f'<rect width="{d.width}" height="{d.height}" fill="{background}"/>'
          if background else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{d.width}" '
            f'height="{d.height}" viewBox="0 0 {d.width} {d.height}">'
            f"\n{bg}\n{body}\n</svg>\n")


def export_assets(outdir, background="#ffffff"):
    """Write every figure to <outdir>/<name>.svg; returns the names."""
    os.makedirs(outdir, exist_ok=True)
    names = []
    for name, fn in FIGURES.items():
        # the cover paints its own dark ground; keep it transparent-free
        bgc = None if name == "cover" else background
        svg = drawing_to_svg(fn(), background=bgc)
        with open(os.path.join(outdir, f"{name}.svg"), "w",
                  encoding="utf-8") as fh:
            fh.write(svg)
        names.append(name)
    return names
