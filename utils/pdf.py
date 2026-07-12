"""Small dependency-light Markdown-to-PDF renderer for OpenReview submission."""
import html
import os
import re
import xml.etree.ElementTree as ET

import markdown
from pypdf import PdfReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer


def _register_font():
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path) and path.lower().endswith(".ttf"):
            pdfmetrics.registerFont(TTFont("SubmissionFont", path))
            return "SubmissionFont"
    return "Helvetica"


def _plain(text):
    return re.sub(r"\s+", " ", "".join(text.itertext())).strip()


def render_pdf(markdown_text, pdf_path, title="Auto Research Submission", max_pages=4):
    """Render a generated paper into a readable A4 PDF and return its path."""
    font = _register_font()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("SubmissionTitle", parent=styles["Title"], fontName=font, alignment=TA_CENTER, fontSize=18, leading=22, spaceAfter=12))
    styles.add(ParagraphStyle("SubmissionH1", parent=styles["Heading1"], fontName=font, fontSize=14, leading=17, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle("SubmissionH2", parent=styles["Heading2"], fontName=font, fontSize=11, leading=14, spaceBefore=7, spaceAfter=3))
    styles.add(ParagraphStyle("SubmissionBody", parent=styles["BodyText"], fontName=font, fontSize=9.5, leading=13, spaceAfter=5))
    styles.add(ParagraphStyle("SubmissionCode", parent=styles["Code"], fontName="Courier", fontSize=7.5, leading=9, leftIndent=8, rightIndent=8, spaceAfter=5))

    body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])
    root = ET.fromstring(f"<root>{body}</root>")
    story = [Paragraph(html.escape(title), styles["SubmissionTitle"]), Spacer(1, 3 * mm)]

    for node in root:
        tag = node.tag.lower()
        text = html.escape(_plain(node))
        if not text:
            continue
        if tag in {"h1", "h2", "h3"}:
            style = styles["SubmissionH1"] if tag == "h1" else styles["SubmissionH2"]
            story.append(Paragraph(text, style))
        elif tag == "pre":
            story.append(Paragraph(text.replace("\n", "<br/>"), styles["SubmissionCode"]))
        elif tag in {"ul", "ol"}:
            items = []
            for li in node.findall("li"):
                items.append(ListItem(Paragraph(html.escape(_plain(li)), styles["SubmissionBody"])))
            story.append(ListFlowable(items, bulletType="1" if tag == "ol" else "bullet", leftIndent=18))
        elif tag == "hr":
            story.append(Spacer(1, 4 * mm))
        else:
            story.append(Paragraph(text, styles["SubmissionBody"]))

    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=title, author="Auto Research")
    doc.build(story)
    page_count = len(PdfReader(str(pdf_path)).pages)
    if page_count > max_pages:
        raise ValueError(f"Generated PDF has {page_count} pages; maximum allowed is {max_pages}.")
    return pdf_path
