from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)

PPTX_PATH = OUT / "AI_Capital_Intelligence_Presentation.pptx"
PDF_PATH = OUT / "AI_Capital_Intelligence_Project_Report.pdf"

NAVY = RGBColor(20, 35, 62)
BLUE = RGBColor(42, 105, 170)
TEAL = RGBColor(20, 145, 145)
PALE = RGBColor(238, 244, 250)
WHITE = RGBColor(255, 255, 255)
DARK = RGBColor(45, 55, 70)
GREY = RGBColor(105, 117, 132)

# ---------------- POWERPOINT ----------------

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_text(slide, text, x, y, w, h, size=18,
             color=DARK, bold=False, align=None):
    shape = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = "Aptos"
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.space_after = Pt(9)
        if align is not None:
            p.alignment = align
    return shape

def add_box(slide, text, x, y, w, h, fill=PALE,
            size=15, color=NAVY, line=BLUE):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.text_frame.clear()
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    shape.text_frame.word_wrap = True
    p = shape.text_frame.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Aptos"
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = color
    return shape

def add_arrow(slide, x1, y1, x2, y2, color=TEAL):
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    line.line.color.rgb = color
    line.line.width = Pt(2)

def new_slide(title, subtitle=None, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY if dark else WHITE

    if title:
        add_text(slide, title, 0.65, 0.35, 12.0, 0.65,
                 27, WHITE if dark else NAVY, True)
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0.67), Inches(1.08), Inches(0.85), Inches(0.055)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = TEAL
        bar.line.fill.background()

    if subtitle:
        add_text(slide, subtitle, 0.68, 1.22, 11.9, 0.5,
                 13, GREY if not dark else WHITE)

    add_text(slide, "AI CAPITAL INTELLIGENCE  |  PROJECT PORTFOLIO",
             0.68, 7.12, 11.8, 0.2, 8,
             GREY if not dark else WHITE)
    add_text(slide, f"{len(prs.slides):02d}", 12.35, 7.10,
             0.35, 0.2, 9, GREY if not dark else WHITE)
    return slide

def bullets(slide, items, x=0.9, y=1.85, w=11.5,
            size=19, color=DARK, gap=0.64):
    for i, item in enumerate(items):
        add_text(slide, "•  " + item, x, y + i * gap,
                 w, gap, size, color)

# 1
s = new_slide(None, dark=True)
add_text(s, "AI CAPITAL\nINTELLIGENCE", 0.85, 1.25, 11.5, 1.8,
         38, WHITE, True)
add_text(s, "End-to-End Financial Data Engineering\nand AI Analytics Platform",
         0.9, 3.35, 10.8, 1.0, 23, RGBColor(170, 220, 225))
add_text(s, "Python  |  AWS S3  |  Snowflake  |  dbt  |  Airflow  |  Power BI  |  RAG",
         0.9, 5.05, 11.8, 0.55, 14, WHITE)
add_text(s, "Technical Project Portfolio  •  27–28 November 2026",
         0.9, 6.2, 11.8, 0.35, 11, WHITE)

# 2
s = new_slide("Executive Summary", "An integrated financial data platform")
bullets(s, [
    "Extracts public company financial facts from SEC EDGAR.",
    "Analyzes Amazon, Microsoft, Alphabet and Meta.",
    "Combines Python ingestion, S3 delivery and Snowflake loading.",
    "Uses dbt for modular transformations and automated data tests.",
    "Uses Airflow to orchestrate ingestion, validation and dbt execution.",
    "Provides Power BI reporting and a local retrieval-augmented AI assistant."
], size=18, gap=0.72)

# 3
s = new_slide("Business Problem", "Why build a unified financial intelligence workflow?")
bullets(s, [
    "Financial information is distributed across regulatory reporting.",
    "Reporting periods and source conventions require careful alignment.",
    "Manual data preparation is repetitive and difficult to audit.",
    "Analysts need trusted, reusable datasets rather than isolated extracts.",
    "Pipeline failures and data-quality problems need operational visibility."
], size=20, gap=0.85)

# 4
s = new_slide("Proposed Solution", "From regulatory source data to analytical consumption")
stages = [
    ("01  EXTRACT", "SEC EDGAR\nCompany Facts"),
    ("02  PROCESS", "Python\nNormalization"),
    ("03  DELIVER", "S3 + Snowflake\nSeparate paths"),
    ("04  TRANSFORM", "dbt Models\nand Tests"),
    ("05  CONSUME", "Power BI +\nAI / RAG")
]
for i, (head, body) in enumerate(stages):
    x = 0.55 + i * 2.58
    add_box(s, head + "\n\n" + body, x, 2.65, 2.25, 1.65,
            fill=PALE, size=14)
    if i < len(stages) - 1:
        add_arrow(s, x + 2.27, 3.48, x + 2.53, 3.48)

add_text(s, "Apache Airflow orchestrates the pipeline execution and dependencies.",
         1.0, 5.15, 11.3, 0.6, 18, TEAL, True, PP_ALIGN.CENTER)

# 5
s = new_slide("System Architecture", "Verified implementation-level data paths")
add_box(s, "SEC EDGAR\nCompany Facts API", 4.9, 1.85, 3.1, 0.75)
add_arrow(s, 6.45, 2.62, 6.45, 2.95)
add_box(s, "Python ingestion and transformation", 4.2, 2.95, 4.5, 0.75)
add_arrow(s, 5.25, 3.7, 3.1, 4.15)
add_arrow(s, 7.65, 3.7, 9.95, 4.15)
add_box(s, "Local CSV / Parquet\nBoto3 upload", 1.25, 4.15, 3.7, 0.85)
add_box(s, "Snowflake FINANCIAL_METRICS\nDirect write_pandas() load",
        8.0, 4.15, 4.1, 0.85)
add_arrow(s, 10.05, 5.0, 6.55, 5.35)
add_box(s, "dbt: Staging → Intermediate → Marts",
        4.25, 5.35, 4.6, 0.75, fill=RGBColor(230, 245, 240),
        line=TEAL)
add_text(s, "S3 and Snowflake are separate delivery destinations; Snowflake is not loaded from S3.",
         1.0, 6.35, 11.3, 0.35, 12, GREY, False, PP_ALIGN.CENTER)

# 6
s = new_slide("Data Engineering", "Source ingestion, processing and delivery")
bullets(s, [
    "Source: SEC EDGAR Company Facts API.",
    "Companies: AMZN, MSFT, GOOGL and META.",
    "Python and Pandas process reported financial observations.",
    "Pipeline artifacts include CSV and Parquet files.",
    "Boto3 uploads configured files to AWS S3.",
    "Snowflake receives a direct load through the Snowflake connector write_pandas() function."
], size=18, gap=0.72)

# 7
s = new_slide("Snowflake and dbt", "A layered analytics engineering design")
for i, (title, desc) in enumerate([
    ("STAGING", "2 models\nSource standardization"),
    ("INTERMEDIATE", "9 models\nCanonicalization and business logic"),
    ("MARTS", "9 models\nAnalytics-ready datasets")
]):
    x = 0.9 + i * 4.15
    add_box(s, title + "\n\n" + desc, x, 2.35, 3.45, 1.85,
            fill=PALE if i != 2 else RGBColor(230, 245, 240),
            line=BLUE if i != 2 else TEAL)
    if i < 2:
        add_arrow(s, x + 3.48, 3.27, x + 4.05, 3.27)
add_text(s, "20 SQL models  •  2 seeds  •  2 sources  •  72 data tests",
         1.0, 5.15, 11.3, 0.6, 21, TEAL, True, PP_ALIGN.CENTER)

# 8
s = new_slide("Airflow Orchestration", "Three-task DAG: aci_sec_financial_pipeline")
for i, (name, desc) in enumerate([
    ("TASK 1", "run_sec_pipeline\nSEC extraction and delivery"),
    ("TASK 2", "validate_pipeline_outputs\nOutput validation"),
    ("TASK 3", "run_dbt_build\ndbt build execution")
]):
    x = 0.85 + i * 4.25
    add_box(s, name + "\n\n" + desc, x, 2.5, 3.45, 1.8,
            fill=PALE, size=15)
    if i < 2:
        add_arrow(s, x + 3.48, 3.4, x + 4.15, 3.4)
bullets(s, [
    "Configured retries and task execution timeouts.",
    "Run-specific logs support operational troubleshooting."
], x=1.0, y=5.15, size=16, gap=0.55)

# 9
s = new_slide("Verified Execution Evidence", "Latest verified manual run — 27 November 2026")
metrics = [
    ("3 / 3", "Airflow tasks\nsuccessful"),
    ("94", "Successful dbt\nbuild steps"),
    ("72", "dbt data\ntests"),
    ("0", "Warnings and\nerrors")
]
for i, (value, label) in enumerate(metrics):
    x = 0.7 + i * 3.15
    add_box(s, value + "\n\n" + label, x, 2.35, 2.65, 1.75,
            fill=RGBColor(230, 245, 240), line=TEAL, size=21)
add_text(s, "dbt summary: PASS=94  WARN=0  ERROR=0  SKIP=0",
         1.0, 4.75, 11.3, 0.45, 20, TEAL, True, PP_ALIGN.CENTER)
add_text(s, "Important: 94 represents successful build steps, not 94 tests. The build included 72 data tests.",
         1.0, 5.55, 11.3, 0.65, 14, GREY, False, PP_ALIGN.CENTER)

# 10
s = new_slide("Analytics and AI", "Business intelligence and grounded exploration")
add_box(s, "POWER BI\n\nSeven report pages\nPerformance • Comparisons\nForecasts • Anomalies • Risk",
        0.9, 2.2, 5.4, 2.5, fill=PALE)
add_box(s, "AI / RAG ASSISTANT\n\nSnowflake structured retrieval\nChromaDB semantic retrieval\nLocal Ollama inference",
        7.0, 2.2, 5.4, 2.5, fill=RGBColor(230, 245, 240), line=TEAL)
add_text(s, "AI responses should use approved marts and retrieved context; unsupported figures must not be invented.",
         1.0, 5.45, 11.3, 0.7, 15, GREY, False, PP_ALIGN.CENTER)

# 11
s = new_slide("Limitations and Production Readiness",
              "Clear boundaries are part of engineering quality")
bullets(s, [
    "Financial facts are company-wide; they do not measure AI-specific ROI.",
    "Forecasts are estimates; anomaly and risk flags require human review.",
    "A Power BI semantic-model cyclic-reference issue remains unresolved.",
    "Public dashboard and AI application hosting have not been verified.",
    "Production security, deployment automation, alerting and recovery need further work."
], size=18, gap=0.82)

# 12
s = new_slide("Conclusion and Roadmap", "A substantial integrated engineering portfolio")
bullets(s, [
    "Demonstrates ingestion, warehouse design, transformation and orchestration.",
    "Includes tested dbt models, BI reporting and AI-assisted exploration.",
    "Resolve and validate Power BI model dependencies.",
    "Strengthen least-privilege access and credential management.",
    "Add deployment automation, alerting, backup and recovery testing.",
    "Deploy and independently verify public application endpoints."
], size=18, gap=0.76)
add_text(s, "AI CAPITAL INTELLIGENCE",
         1.0, 6.25, 11.3, 0.4, 18, TEAL, True, PP_ALIGN.CENTER)

prs.save(PPTX_PATH)

# ---------------- PDF REPORT ----------------

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=25, leading=31,
    textColor=colors.HexColor("#14233E"), alignment=TA_CENTER,
    spaceAfter=12
))
styles.add(ParagraphStyle(
    name="SubTitleACI", parent=styles["Normal"],
    fontSize=12, leading=18, textColor=colors.HexColor("#438C9A"),
    alignment=TA_CENTER, spaceAfter=18
))
styles.add(ParagraphStyle(
    name="H1ACI", parent=styles["Heading1"],
    fontSize=17, leading=22, textColor=colors.HexColor("#14233E"),
    spaceBefore=14, spaceAfter=8
))
styles.add(ParagraphStyle(
    name="H2ACI", parent=styles["Heading2"],
    fontSize=12, leading=16, textColor=colors.HexColor("#2869AA"),
    spaceBefore=9, spaceAfter=5
))
styles.add(ParagraphStyle(
    name="BodyACI", parent=styles["BodyText"],
    fontSize=9.5, leading=14, spaceAfter=7
))
styles.add(ParagraphStyle(
    name="SmallACI", parent=styles["BodyText"],
    fontSize=8, leading=11, textColor=colors.HexColor("#687588")
))

def P(text, style="BodyACI"):
    return Paragraph(text, styles[style])

def bullet(text):
    return P("&#8226;&nbsp;&nbsp;" + text)

def make_table(rows, widths=None):
    data = [[P(str(c), "SmallACI") for c in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14233E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6DFE8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

story = []
story += [
    Spacer(1, 42*mm),
    P("AI CAPITAL INTELLIGENCE", "CoverTitle"),
    P("End-to-End Financial Data Engineering and AI Analytics Platform",
      "SubTitleACI"),
    Spacer(1, 12*mm),
    P("<b>Technical Project Report</b>", "H2ACI"),
    P("Python • AWS S3 • Snowflake • dbt • Apache Airflow • Power BI • RAG",
      "SubTitleACI"),
    Spacer(1, 30*mm),
    P("Prepared as a technical portfolio document", "SubTitleACI"),
    P("Project evidence verified through 27 November 2026. "
      "Documentation prepared 28 November 2026.", "SmallACI"),
    PageBreak()
]

story += [
    P("1. Executive Summary", "H1ACI"),
    P("AI Capital Intelligence (ACI) is an integrated financial data engineering "
      "and analytics platform. It extracts public company financial facts from "
      "SEC EDGAR, processes observations using Python, delivers data to AWS S3 "
      "and Snowflake, transforms warehouse data with dbt, and orchestrates "
      "execution through Apache Airflow. Power BI provides analytical reporting, "
      "while a local retrieval-augmented AI application supports natural-language "
      "exploration."),
    P("The current analysis scope includes Amazon (AMZN), Microsoft (MSFT), "
      "Alphabet (GOOGL), and Meta Platforms (META)."),
    P("2. Business Problem and Solution", "H1ACI"),
    P("Financial observations are distributed across regulatory reporting and "
      "require careful treatment of units, source definitions, and fiscal periods. "
      "Manual extraction and preparation can be repetitive, difficult to audit, "
      "and hard to monitor. ACI provides a repeatable workflow from source "
      "extraction to analytics-ready datasets."),
    make_table([
        ["Challenge", "Platform response"],
        ["Distributed financial facts", "Automated SEC EDGAR extraction"],
        ["Inconsistent source representations", "Python normalization and dbt models"],
        ["Manual analytical preparation", "Reusable Snowflake analytical marts"],
        ["Limited execution visibility", "Airflow orchestration and monitoring"],
        ["Difficult business exploration", "Power BI and grounded AI/RAG interface"],
    ], [48*mm, 112*mm]),
    P("3. System Architecture", "H1ACI"),
    P("The Python pipeline creates local CSV and Parquet outputs. It then has "
      "two separate delivery paths: configured files are uploaded to S3 using "
      "Boto3, while financial data is loaded directly into Snowflake through "
      "the Snowflake connector's write_pandas() function. Snowflake is not "
      "loaded from S3 in the current implementation."),
    make_table([
        ["Layer", "Technology / responsibility"],
        ["Source", "SEC EDGAR Company Facts API"],
        ["Ingestion", "Python, Pandas"],
        ["File artifacts", "CSV and Parquet"],
        ["Object storage", "AWS S3 via Boto3"],
        ["Warehouse", "Snowflake direct load"],
        ["Transformation", "dbt staging, intermediate and marts"],
        ["Orchestration", "Apache Airflow"],
        ["Consumption", "Power BI and local AI/RAG application"],
    ], [42*mm, 118*mm]),
    P("4. Data Engineering and Warehouse", "H1ACI"),
    P("The pipeline extracts company financial observations and normalizes them "
      "for downstream use. Core metric categories include revenue, operating "
      "income, net income, capital expenditure, and operating cash flow. "
      "Structured CSV and Parquet outputs support reproducibility and "
      "downstream delivery."),
    P("Snowflake serves as the analytical warehouse. dbt models separate "
      "source standardization from intermediate business logic and final "
      "analytical datasets."),
    make_table([
        ["dbt component", "Count"],
        ["Staging models", "2"],
        ["Intermediate models", "9"],
        ["Marts", "9"],
        ["Total SQL models", "20"],
        ["Seeds", "2"],
        ["Sources", "2"],
        ["Data tests", "72"],
    ], [90*mm, 70*mm]),
    P("5. Orchestration and Reliability", "H1ACI"),
    P("The Airflow DAG aci_sec_financial_pipeline contains three main tasks: "
      "run_sec_pipeline, validate_pipeline_outputs, and run_dbt_build. "
      "The workflow defines task dependencies, retries, execution timeouts, "
      "and run-specific logging. The latest verified manual run completed "
      "all three tasks successfully."),
    make_table([
        ["Task", "Responsibility", "Latest verified state"],
        ["run_sec_pipeline", "SEC ingestion and delivery", "SUCCESS"],
        ["validate_pipeline_outputs", "Validate generated outputs", "SUCCESS"],
        ["run_dbt_build", "Execute dbt build", "SUCCESS"],
    ], [43*mm, 77*mm, 40*mm]),
    P("6. Latest Verified Build Evidence", "H1ACI"),
    P("The dbt log for the manual Airflow run on 27 November 2026 reported "
      "2 seeds, 5 table models, 15 view models, and 72 data tests. The final "
      "summary was PASS=94, WARN=0, ERROR=0, SKIP=0. The 94 successful "
      "steps are the total build-step summary; they are not 94 data tests."),
    make_table([
        ["Evidence", "Verified result"],
        ["Airflow tasks", "3 of 3 successful"],
        ["dbt successful build steps", "94"],
        ["dbt data tests", "72"],
        ["Warnings", "0"],
        ["Errors", "0"],
        ["Skipped steps", "0"],
    ], [90*mm, 70*mm]),
    P("7. Analytics and AI", "H1ACI"),
    P("The Power BI report contains seven pages covering financial analytics "
      "and settings/information. The intended analytical areas include company "
      "performance, comparisons, cash flow, revenue forecasting, anomalies, "
      "risk indicators, and pipeline monitoring."),
    P("The AI application combines structured Snowflake retrieval with "
      "semantic retrieval through ChromaDB and local inference using Ollama. "
      "The application is intended to ground answers in approved analytical "
      "marts and retrieved context."),
    P("8. Data Governance and Interpretation", "H1ACI"),
    bullet("Company-wide financial facts must not be represented as AI-specific ROI."),
    bullet("Missing values must not automatically be treated as zero."),
    bullet("Forecast outputs are estimates, not reported actuals."),
    bullet("Anomaly and risk flags are review signals, not proof of misconduct or error."),
    bullet("FREE_CASH_FLOW remains NULL where its calculation basis is not approved."),
    bullet("FREE_CASH_FLOW_CANDIDATE is not an approved free-cash-flow measure."),
    P("9. Limitations and Production Readiness", "H1ACI"),
    P("The current implementation has been integrated and validated locally. "
      "It should not be represented as a fully deployed production service."),
    bullet("A Power BI semantic-model cyclic-reference issue remains unresolved."),
    bullet("Public Power BI Service publication has not been verified."),
    bullet("The AI application and Ollama inference are local; public hosting is not verified."),
    bullet("Production-grade access control, deployment automation, alerting, "
          "backup and recovery procedures require further work."),
    bullet("S3 delivery should be independently checked for current object "
          "availability and retention."),
    P("10. Security Considerations", "H1ACI"),
    P("Credentials should be stored outside source control, rotated if exposed, "
      "and managed using least-privilege service roles. Production deployments "
      "should separate development and production credentials, restrict network "
      "access, and audit access to warehouse and object-storage resources."),
    P("11. Roadmap", "H1ACI"),
    bullet("Resolve and retest Power BI semantic-model dependencies."),
    bullet("Validate scheduled Airflow execution and S3 object delivery."),
    bullet("Implement least-privilege Snowflake roles and credential rotation."),
    bullet("Add automated deployment, alerting, runbooks, and recovery tests."),
    bullet("Deploy the AI application and inference service, then independently "
          "verify public endpoints."),
    P("12. Conclusion", "H1ACI"),
    P("AI Capital Intelligence demonstrates an integrated approach to financial "
      "data ingestion, warehouse engineering, transformation testing, workflow "
      "orchestration, business intelligence, and AI-assisted exploration. "
      "Its verified local execution provides concrete evidence of integration, "
      "while the documented limitations and roadmap define the remaining work "
      "before production deployment."),
    Spacer(1, 8*mm),
    P("Document status: Portfolio technical report. Operational claims are "
      "limited to the evidence described above.", "SmallACI")
]

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D6DFE8"))
    canvas.line(18*mm, 15*mm, 192*mm, 15*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#687588"))
    canvas.drawString(18*mm, 10*mm, "AI Capital Intelligence | Technical Project Report")
    canvas.drawRightString(192*mm, 10*mm, f"Page {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(PDF_PATH), pagesize=A4,
    rightMargin=18*mm, leftMargin=18*mm,
    topMargin=18*mm, bottomMargin=22*mm,
    title="AI Capital Intelligence - Technical Project Report",
    author="AI Capital Intelligence Project"
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

print("Generated deliverables:")
for path in (PPTX_PATH, PDF_PATH):
    print(f"{path} | {path.stat().st_size:,} bytes")
