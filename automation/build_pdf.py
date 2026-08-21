#!/usr/bin/env python3
"""Assemble the 14 chapters into a single print-ready PDF.

No native binaries required: uses the already-installed `markdown` and
`reportlab` libraries. Run from the project root:

    python automation/build_pdf.py
    # -> writes dist/book.pdf and exports assets/*.svg for the web edition
"""
import os
import re
import html
import markdown as mdlib
from xml.etree import ElementTree as ET

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents

import book_graphics as bg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAP_DIR = os.path.join(ROOT, "chapters")

# Fixed, ordered list of chapter files (ch01 -> ch14).
CHAPTERS = [
    f"ch{ i:02d}-{ name}.md"
    for i, name in enumerate([
        "the-original-sin", "the-pwc-precedent", "the-whistleblower",
        "the-lendlease-breach", "the-cast-of-characters", "the-hoggett-decision",
        "the-chairmans-conflict", "the-faircall-hypocrisy", "asic-enters",
        "the-governments-27.4m-problem", "the-limited-liability-shield",
        "the-billing-fraud-whistleblower", "epilogue-the-fire-sale",
        "optus-data-breach",
    ], start=1)]

TITLE = "Going Concern"
SUBTITLE = "An open book about the KPMG Australia audit scandal"
LICENSE_LINES = [
    "This text is licensed under the Creative Commons Attribution 4.0 International License.",
    "https://creativecommons.org/licenses/by/4.0/",
]

# Figures: chapters embed ![alt](../assets/<key>.svg); the builder maps the
# filename to a vector drawing from book_graphics and prints the alt as caption.
GREY_RGB = colors.HexColor("#6B6B70")


def figure_flowables(draw_fn, caption, styles, number):
    """A vector figure from book_graphics plus its numbered caption."""
    d = draw_fn()
    return [Spacer(1, 10), d, Spacer(1, 2),
            Paragraph(html.escape(f"Figure {number}. {caption}"),
                      styles["FigCaption"]),
            Spacer(1, 10)]


# --- markdown -> reportlab flowables --------------------------------------

TAG_MAP = {
    "strong": "b", "b": "b",
    "em": "i", "i": "i",
    "a": "a",
}
VOID = {"br", "img"}


def inline_to_markup(el):
    """Render an element's text/tail + children as reportlab markup (a string)."""
    out = []
    if el.text:
        out.append(html.escape(el.text))
    for child in el:
        tag = TAG_MAP.get(child.tag, child.tag)
        if tag == "img":
            # images are handled at block level; keep only surrounding text
            if child.tail:
                out.append(html.escape(child.tail))
            continue
        if tag == "a":
            out.append(f'<a href="{child.get("href", "")}">')
            close = "</a>"
        elif tag == "br":
            out.append("<br/>")
            close = ""
        elif tag in VOID:
            out.append(f"<{tag}>")
            close = ""
        else:
            out.append(f"<{tag}>")
            close = f"</{tag}>"
        out.append(inline_to_markup(child))
        out.append(close)
        if child.tail:
            out.append(html.escape(child.tail))
    return "".join(out)


def strip_inline(el):
    """Drop inline tags, keep escaped text."""
    out = []
    if el.text:
        out.append(html.escape(el.text))
    for child in el:
        out.append(strip_inline(child))
        if child.tail:
            out.append(html.escape(child.tail))
    return "".join(out)


def blocks_from_html(html_text, styles):
    """Yield (style_name, text) for top-level blocks."""
    root = ET.fromstring(f"<div>{html_text}</div>")
    for el in root:
        if el.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = int(el.tag[1])
            txt = strip_inline(el)
            yield ("h%d" % lvl, txt)
        elif el.tag == "p":
            imgs = [c for c in el if c.tag == "img"]
            if imgs and not strip_inline(el).strip():
                # a standalone image: hand it to the figure machinery
                yield ("img", imgs[0].get("src", ""), imgs[0].get("alt", ""))
            else:
                yield ("p", inline_to_markup(el))
        elif el.tag in ("ul", "ol"):
            for li in el:
                if li.tag != "li":
                    continue
                yield ("li", inline_to_markup(li))
        elif el.tag == "hr":
            yield ("hr", "")
        elif el.tag == "table":
            rows = []
            for tr in el.iter("tr"):
                cells = [strip_inline(td) for td in tr if td.tag in ("td", "th")]
                if cells:
                    rows.append(cells)
            yield ("table", rows)
        # ignore code blocks / blockquotes for the typed PDF


def flowable_for(block, styles):
    kind, data = block
    if kind == "hr":
        return Paragraph("<i>—</i>", styles["BodyText"])
    if kind == "table":
        # render as simple indented rows to keep the PDF tidy
        out = []
        for row in data:
            out.append(Paragraph(" &nbsp; ".join(row), styles["BodyText"]))
            out.append(Spacer(1, 4))
        return out
    style = {
        "h1": "ChapterTitle",
        "h2": "Hdg2",
        "h3": "Hdg3",
        "p": "BodyText",
        "li": "BulletText",
    }[kind]
    text = data if kind != "li" else "&#8226;&nbsp;" + (data or "")
    para = Paragraph(text, styles[style])
    return para


# --- PDF build ------------------------------------------------------------

class NumberedDoc(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(path, pagesize=A4, **kw)
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="all", frames=[frame],
                                            onPage=self.on_page)])

    def on_page(self, canvas, doc):
        page = self.page
        if page == 1:
            # full-bleed cover art, drawn straight onto the page
            bg.cover().drawOn(canvas, 0, 0)
            return
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            self.pagesize[0] - self.leftMargin,
            self.bottomMargin / 2,
            str(page),
        )
        canvas.restoreState()


def build_chapter_story():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ChapterTitle", parent=styles["Title"], fontSize=18, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="Hdg2", parent=styles["Heading2"], fontSize=13,
        spaceBefore=14, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(name="Hdg3", parent=styles["Heading3"],
                              fontSize=11, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="BulletText", parent=styles["BodyText"],
                              leftIndent=18, bulletIndent=6, firstLineIndent=-6))
    styles.add(ParagraphStyle(name="SmallNote", parent=styles["BodyText"],
                              fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="FigCaption", parent=styles["BodyText"],
                              fontSize=8, leading=11, textColor=GREY_RGB,
                              alignment=TA_CENTER))

    story = []

    # --- cover: full-bleed art drawn by NumberedDoc.on_page on page 1 ---
    story.append(Spacer(1, 1))
    story.append(PageBreak())

    # --- table of contents ---
    toc_entries = []
    for path in CHAPTERS:
        with open(os.path.join(CHAP_DIR, path), encoding="utf-8") as fh:
            text = fh.read()
        html_text = mdlib.markdown(text, extensions=["extra", "sane_lists"])
        # h1 of chapter = title
        m = re.search(r"<h1>(.*?)</h1>", html_text, re.S)
        title_el = ET.fromstring(f"<d>{m.group(1)}</d>") if m else ET.fromstring(f"<d>{path}</d>")
        toc_entries.append(strip_inline(title_el))

    story.append(Paragraph("Contents", styles["Title"]))
    story.append(Spacer(1, 16))
    for idx, label in enumerate(toc_entries, 1):
        story.append(Paragraph(html.escape(label), styles["BodyText"]))
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 24))
    for line in LICENSE_LINES:
        story.append(Paragraph(html.escape(line), styles["SmallNote"]))
    story.append(PageBreak())

    # --- chapters ---
    fig_no = 0
    for idx, path in enumerate(CHAPTERS, 1):
        with open(os.path.join(CHAP_DIR, path), encoding="utf-8") as fh:
            text = fh.read()
        html_text = mdlib.markdown(text, extensions=["extra", "sane_lists", "tables"])
        for b in blocks_from_html(html_text, styles):
            if b[0] == "img":
                _, src, alt = b
                key = os.path.splitext(os.path.basename(src))[0]
                draw_fn = bg.FIGURES.get(key)
                if draw_fn is not None:
                    fig_no += 1
                    story.extend(figure_flowables(draw_fn, alt, styles, fig_no))
                continue
            f = flowable_for(b, styles)
            if isinstance(f, list):
                story.extend(f)
            else:
                story.append(f)
        story.append(Spacer(1, 10))
    return story, styles


def main():
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    exported = bg.export_assets(os.path.join(ROOT, "assets"))
    print("SVG assets ->", ", ".join(f"{n}.svg" for n in exported))
    story, styles = build_chapter_story()
    pdf_path = os.path.join(ROOT, "dist", "book.pdf")
    doc = NumberedDoc(pdf_path, title=TITLE, author="Going Concern")

    # insert page breaks so each chapter starts on its own page
    spaced = []
    for i, flow in enumerate(story):
        if isinstance(flow, Paragraph) and flow.style.name == "ChapterTitle":
            if spaced:
                spaced.append(PageBreak())
        spaced.append(flow)

    doc.build(spaced)
    print("PDF ->", pdf_path)


if __name__ == "__main__":
    main()
