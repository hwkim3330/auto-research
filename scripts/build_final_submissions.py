"""Build polished, verified Ralphthon submission PDFs from final Markdown."""
from pathlib import Path
import html
import re
import xml.etree.ElementTree as ET

import markdown
from pypdf import PdfReader
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2673B8")
TEAL = colors.HexColor("#2A9D8F")
LIGHT = colors.HexColor("#EEF4F8")
GRAY = colors.HexColor("#5F6B76")


def text_of(node):
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()


def page_decor(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D5DEE6"))
    canvas.line(16 * mm, 13 * mm, width - 16 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(16 * mm, 8.5 * mm, doc.track_label)
    canvas.drawRightString(width - 16 * mm, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def results_chart(track):
    drawing = Drawing(470, 155)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 52, 35, 380, 95
    if track == 1:
        chart.data = [(100.0, 0.0, 1.0), (100.0, 77.22, 100.0)]
        chart.categoryAxis.categoryNames = ["No gate", "Exact", "Normalized"]
        chart.bars[0].fillColor = colors.HexColor("#D95D39")
        chart.bars[1].fillColor = TEAL
        title = "Unsupported acceptance vs. supported recall (%)"
    else:
        chart.data = [(100.0, 100.0, 0.0)]
        chart.categoryAxis.categoryNames = ["Direct", "Paraphrased", "Clean FP"]
        chart.bars[0].fillColor = BLUE
        title = "Lexical injection pre-scan detection rate (%)"
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.valueAxis.labelTextFormat = "%d"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontSize = 7
    drawing.add(chart)
    drawing.add(String(235, 142, title, textAnchor="middle", fontName="Helvetica-Bold", fontSize=9, fillColor=NAVY))
    if track == 1:
        drawing.add(String(120, 10, "orange: unsupported accepted", fontSize=7, fillColor=colors.HexColor("#D95D39")))
        drawing.add(String(275, 10, "green: supported recall", fontSize=7, fillColor=TEAL))
    return drawing


def build(md_path, pdf_path, track, title):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("PaperTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=NAVY, alignment=TA_CENTER, spaceAfter=5))
    styles.add(ParagraphStyle("Venue", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, textColor=GRAY, alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle("H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle("H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=9.5, leading=11, textColor=BLUE, spaceBefore=6, spaceAfter=3, keepWithNext=True))
    styles.add(ParagraphStyle("Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11.4, alignment=TA_JUSTIFY, spaceAfter=4))
    styles.add(ParagraphStyle("Abstractx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11.3, alignment=TA_JUSTIFY, leftIndent=7, rightIndent=7, borderColor=colors.HexColor("#B8CAD9"), borderWidth=0.6, borderPadding=8, backColor=LIGHT, spaceAfter=8))
    styles.add(ParagraphStyle("Codex", parent=styles["Code"], fontName="Courier", fontSize=7.2, leading=8.8, leftIndent=8, rightIndent=8, backColor=colors.HexColor("#F6F8FA"), borderPadding=5, spaceAfter=5))
    styles.add(ParagraphStyle("Refx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9.3, leftIndent=10, firstLineIndent=-10, spaceAfter=2))
    styles.add(ParagraphStyle("TableHeader", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.3, leading=10, textColor=colors.white))

    raw = md_path.read_text()
    rendered = markdown.markdown(raw, extensions=["tables", "fenced_code"])
    root = ET.fromstring(f"<root>{rendered}</root>")
    story = [Paragraph(html.escape(title), styles["PaperTitle"]), Paragraph(f"Ralphthon @ ICML 2026 - Track {track} {'Submission' if track == 1 else 'Technical Report'}", styles["Venue"])]
    abstract_next = False
    chart_added = False
    in_refs = False

    for node in root:
        tag = node.tag.lower()
        text = text_of(node)
        if tag == "h1":
            continue
        if tag == "h2":
            abstract_next = text.lower() == "abstract"
            in_refs = text.lower() == "references"
            if not abstract_next:
                story.append(Paragraph(html.escape(text), styles["H1x"]))
            continue
        if tag == "h3":
            story.append(Paragraph(html.escape(text), styles["H2x"]))
            continue
        if tag == "p":
            style = styles["Abstractx"] if abstract_next else (styles["Refx"] if in_refs else styles["Bodyx"])
            story.append(Paragraph(html.escape(text), style))
            abstract_next = False
            continue
        if tag in {"ol", "ul"}:
            items = [ListItem(Paragraph(html.escape(text_of(li)), styles["Bodyx"]), leftIndent=10) for li in node.findall("li")]
            story.append(ListFlowable(items, bulletType="1" if tag == "ol" else "bullet", leftIndent=18, bulletFontSize=7.5, spaceAfter=4))
            continue
        if tag == "pre":
            story.append(Paragraph(html.escape("\n".join(node.itertext())).replace("\n", "<br/>"), styles["Codex"]))
            continue
        if tag == "table":
            rows = []
            for row_index, tr in enumerate(node.findall(".//tr")):
                cell_style = styles["TableHeader"] if row_index == 0 else styles["Bodyx"]
                cells = [Paragraph(html.escape(text_of(cell)), cell_style) for cell in list(tr)]
                if cells:
                    rows.append(cells)
            if rows:
                table = Table(rows, repeatRows=1, hAlign="CENTER")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8CAD9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(KeepTogether([table, Spacer(1, 3 * mm)]))
                if not chart_added:
                    story.append(results_chart(track))
                    chart_added = True

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=15 * mm, bottomMargin=17 * mm, title=title, author="Ralphthon ICML 2026")
    doc.track_label = f"Ralphthon ICML 2026 / Track {track}"
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    pages = len(PdfReader(str(pdf_path)).pages)
    if pages > 4:
        raise RuntimeError(f"{pdf_path.name} has {pages} pages (limit: 4)")
    return pages


if __name__ == "__main__":
    jobs = [
        (OUT / "track1_submission.md", OUT / "track1_submission.pdf", 1, "Evidence-Locked Scientific Writing for Autonomous Research Agents"),
        (OUT / "track2_submission.md", OUT / "track2_submission.pdf", 2, "CalibratedBatchReview: A Secure Local Review Agent for Timed Paper Assessment"),
    ]
    for md_path, pdf_path, track, title in jobs:
        print(pdf_path.name, build(md_path, pdf_path, track, title), "pages")
