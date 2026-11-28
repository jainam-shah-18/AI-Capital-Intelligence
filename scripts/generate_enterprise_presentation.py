"""
AI Capital Intelligence — Recruiter-Facing Engineering Case Study
Creates an editable 16-slide PowerPoint using native PowerPoint shapes and text.
Run from the project root:
    .\.venv\Scripts\python.exe scripts\generate_enterprise_presentation.py

Design goals:
- Large, presentation-readable typography
- One clear message per slide
- Editable architecture, data-flow, orchestration and evidence visuals
- Explicit distinction between verified implementation and remaining work
- No fabricated customer outcomes, screenshots, or financial ROI
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
OUT.mkdir(exist_ok=True)
DEST = OUT / "AI_Capital_Intelligence_Presentation.pptx"

# Restrained technical palette
NAVY = RGBColor(10, 25, 47)
NAVY2 = RGBColor(17, 43, 72)
BLUE = RGBColor(37, 111, 190)
CYAN = RGBColor(20, 174, 196)
TEAL = RGBColor(0, 143, 136)
MINT = RGBColor(220, 244, 239)
ICE = RGBColor(231, 242, 251)
PAPER = RGBColor(247, 249, 252)
WHITE = RGBColor(255, 255, 255)
INK = RGBColor(25, 42, 61)
MUTED = RGBColor(91, 109, 129)
LINE = RGBColor(211, 222, 232)
GREEN = RGBColor(31, 139, 94)
AMBER = RGBColor(194, 127, 26)
RED = RGBColor(184, 69, 67)
PALE_GREEN = RGBColor(230, 245, 237)
PALE_AMBER = RGBColor(250, 243, 226)
PALE_RED = RGBColor(250, 235, 234)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

def shape(slide, x, y, w, h, fill=WHITE, border=None, radius=0.12, transparency=0):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    obj = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    obj.fill.solid()
    obj.fill.fore_color.rgb = fill
    if transparency:
        obj.fill.transparency = transparency
    obj.line.color.rgb = border or fill
    obj.line.width = Pt(0.8)
    if radius:
        try:
            obj.adjustments[0] = radius
        except Exception:
            pass
    return obj

def text(slide, value, x, y, w, h, size=16, color=INK, bold=False,
         align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE, margin=0.04,
         font="Aptos", italic=False):
    obj = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = obj.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    lines = str(value).split("\n")
    for i, item in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.alignment = align
        p.font.name = font
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = color
        p.space_after = Pt(5)
    return obj

def connector(slide, x1, y1, x2, y2, color=CYAN, width=2, arrow=True):
    obj = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    obj.line.color.rgb = color
    obj.line.width = Pt(width)
    if arrow:
        obj.line.end_arrowhead = True
    return obj

def label(slide, value, x, y, w, color=TEAL):
    shape(slide, x, y, w, 0.30, color, color, 0.15)
    text(slide, value.upper(), x+0.06, y+0.015, w-0.12, 0.26, 9, WHITE, True, PP_ALIGN.CENTER)

def brand(slide, dark=False):
    fg = WHITE if dark else NAVY
    # Simple geometric monogram; intentionally not a corporate logo claim.
    shape(slide, 11.92, 0.25, 0.10, 0.28, TEAL, TEAL, 0)
    shape(slide, 12.08, 0.16, 0.10, 0.37, CYAN, CYAN, 0)
    shape(slide, 12.24, 0.08, 0.10, 0.45, BLUE, BLUE, 0)
    text(slide, "ACI", 12.42, 0.11, 0.50, 0.26, 15, fg, True)
    text(slide, "PROJECT", 12.42, 0.36, 0.50, 0.14, 6.5, fg, True)

def footer(slide, n, dark=False):
    fg = RGBColor(174, 191, 207) if dark else MUTED
    text(slide, "AI CAPITAL INTELLIGENCE  /  ENGINEERING CASE STUDY",
         0.48, 7.17, 8.8, 0.17, 8, fg, True)
    text(slide, f"{n:02d}  /  16", 12.15, 7.14, 0.65, 0.20, 8, fg, True, PP_ALIGN.RIGHT)

def new_slide(title, subtitle="", section="", dark=False):
    s = prs.slides.add_slide(BLANK)
    bg = NAVY if dark else PAPER
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    if not dark:
        shape(s, 0, 0, 13.333, 0.075, CYAN, CYAN, 0)
    text(s, title, 0.58, 0.32, 10.8, 0.57, 29, WHITE if dark else NAVY, True)
    if subtitle:
        text(s, subtitle, 0.62, 0.94, 10.8, 0.36, 14,
             RGBColor(187, 207, 224) if dark else MUTED)
    if section:
        text(s, section.upper(), 0.62, 1.39, 5.2, 0.20, 9,
             CYAN if dark else TEAL, True)
    brand(s, dark)
    footer(s, len(prs.slides), dark)
    return s

def panel(slide, x, y, w, h, title, body="", accent=TEAL, fill=WHITE,
          title_size=17, body_size=13):
    shape(slide, x, y, w, h, fill, LINE, 0.10)
    shape(slide, x, y, 0.07, h, accent, accent, 0)
    text(slide, title, x+0.22, y+0.16, w-0.42, 0.38, title_size, NAVY, True)
    if body:
        text(slide, body, x+0.22, y+0.66, w-0.42, h-0.78,
             body_size, MUTED, False, valign=MSO_ANCHOR.TOP)

def node(slide, x, y, w, h, title, subtitle="", accent=BLUE, fill=WHITE,
         title_size=15, sub_size=11, title_color=NAVY):
    shape(slide, x, y, w, h, fill, LINE, 0.10)
    shape(slide, x, y, w, 0.075, accent, accent, 0)
    text(slide, title, x+0.12, y+0.16, w-0.24, 0.35, title_size,
         title_color, True, PP_ALIGN.CENTER)
    if subtitle:
        text(slide, subtitle, x+0.14, y+0.57, w-0.28, h-0.66,
             sub_size, MUTED, False, PP_ALIGN.CENTER)

def stat(slide, x, y, w, value, caption, accent=TEAL, fill=WHITE):
    shape(slide, x, y, w, 1.12, fill, LINE, 0.10)
    text(slide, value, x+0.08, y+0.10, w-0.16, 0.55, 29, accent, True, PP_ALIGN.CENTER)
    text(slide, caption, x+0.10, y+0.69, w-0.20, 0.27, 10, MUTED, True, PP_ALIGN.CENTER)

def bullet_line(slide, value, x, y, w, size=15, color=INK, accent=TEAL):
    shape(slide, x, y+0.12, 0.11, 0.11, accent, accent, 0.1)
    text(slide, value, x+0.25, y, w-0.25, 0.48, size, color, False, valign=MSO_ANCHOR.TOP)

# 01 — Cover
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = NAVY
# Subtle technical grid and data-column motif
for i in range(9):
    connector(s, 7.2+i*0.62, 0.7, 7.2+i*0.62, 6.7, NAVY2, 0.55, False)
for i in range(5):
    connector(s, 7.0, 1.0+i*1.1, 12.8, 1.0+i*1.1, NAVY2, 0.55, False)
for i, h in enumerate([0.75, 1.25, 1.0, 1.8, 1.45, 2.25, 1.9, 2.65]):
    shape(s, 7.65+i*0.58, 5.9-h, 0.28, h, [BLUE, TEAL, CYAN][i%3], None, 0)
text(s, "ACI  /  PROJECT PORTFOLIO", 0.86, 0.72, 4.2, 0.28, 11, CYAN, True)
text(s, "AI CAPITAL\nINTELLIGENCE", 0.82, 1.55, 7.2, 1.72, 39, WHITE, True)
text(s, "Financial data platform engineering\nfrom SEC facts to analytics and grounded AI",
     0.88, 3.58, 7.0, 0.92, 21, RGBColor(190, 214, 230))
label(s, "END-TO-END ENGINEERING CASE STUDY", 0.9, 5.02, 3.55, TEAL)
text(s, "SEC EDGAR   •   PYTHON   •   AWS S3   •   SNOWFLAKE   •   dbt   •   AIRFLOW   •   POWER BI   •   RAG",
     0.9, 5.72, 11.8, 0.32, 10, WHITE, True)
text(s, "Implementation evidence through 27 November 2026",
     0.9, 6.55, 7.0, 0.25, 10, RGBColor(174, 191, 207))
footer(s, 1, True)

# 02 — Executive brief
s = new_slide("A connected financial data engineering platform",
              "One project integrating ingestion, warehouse engineering, orchestration, analytics and AI-assisted exploration.",
              "01  /  executive brief")
panel(s, 0.72, 1.78, 5.65, 2.08, "WHAT WAS BUILT",
      "A repeatable pipeline that extracts public company facts, normalizes financial observations, delivers files to object storage, loads Snowflake directly, and builds dbt analytics models.",
      BLUE, WHITE, 18, 14)
panel(s, 6.68, 1.78, 5.88, 2.08, "WHAT IT DEMONSTRATES",
      "End-to-end data flow design • SQL analytics engineering • scheduled orchestration • test-backed transformations • BI and hybrid retrieval integration • explicit operational limitations.",
      TEAL, WHITE, 18, 14)
stat(s, 0.82, 4.45, 2.75, "4", "PUBLIC COMPANIES", BLUE)
stat(s, 3.78, 4.45, 2.75, "20", "DBT SQL MODELS", TEAL)
stat(s, 6.74, 4.45, 2.75, "72", "DBT DATA TESTS", BLUE)
stat(s, 9.70, 4.45, 2.75, "3 / 3", "AIRFLOW TASKS SUCCESS", GREEN)
text(s, "Scope is company-wide reported financial data — not AI-specific revenue, spend or ROI.",
     1.0, 6.02, 11.2, 0.35, 13, AMBER, True, PP_ALIGN.CENTER)

# 03 — Business context
s = new_slide("The engineering problem is data trust and repeatability",
              "Public financial facts are accessible; turning them into consistent, reusable analysis is the harder problem.",
              "02  /  problem framing")
items = [
    ("SOURCE FRAGMENTATION", "Company facts span taxonomies, tags, units and reporting periods.", BLUE),
    ("PERIOD SEMANTICS", "Fiscal periods and comparative periods must be interpreted consistently.", TEAL),
    ("REPEATABLE PREPARATION", "Manual extraction and reconciliation are difficult to reproduce and audit.", BLUE),
    ("OPERATIONAL VISIBILITY", "A pipeline needs observable runs, validation and failure boundaries.", TEAL),
]
for i, (h, b, c) in enumerate(items):
    x = 0.78 + (i%2)*6.08
    y = 1.88 + (i//2)*1.82
    panel(s, x, y, 5.55, 1.42, h, b, c, WHITE, 16, 13)
shape(s, 1.10, 6.05, 11.15, 0.55, NAVY, NAVY, 0.1)
text(s, "DESIGN OBJECTIVE     Reliable source facts  →  governed models  →  observable execution  →  useful analysis",
     1.28, 6.14, 10.8, 0.30, 13, WHITE, True, PP_ALIGN.CENTER)

# 04 — Scope and use cases
s = new_slide("Defined analytical scope",
              "Four issuers and a focused set of reported financial measures create a bounded, explainable dataset.",
              "03  /  scope")
companies = [("AMZN", "Amazon"), ("MSFT", "Microsoft"), ("GOOGL", "Alphabet"), ("META", "Meta Platforms")]
for i, (ticker, name) in enumerate(companies):
    x = 0.78 + i*3.08
    shape(s, x, 1.95, 2.72, 1.25, WHITE, LINE, 0.12)
    text(s, ticker, x+0.12, 2.10, 2.48, 0.48, 27, BLUE if i%2==0 else TEAL, True, PP_ALIGN.CENTER)
    text(s, name, x+0.12, 2.62, 2.48, 0.27, 13, MUTED, True, PP_ALIGN.CENTER)
text(s, "CORE FINANCIAL MEASURES", 0.85, 3.72, 4.5, 0.25, 10, TEAL, True)
metrics = ["Revenue", "Operating income", "Net income", "Capital expenditure", "Operating cash flow"]
for i, item in enumerate(metrics):
    x = 0.85 + (i%3)*4.05
    y = 4.20 + (i//3)*0.92
    shape(s, x, y, 3.62, 0.62, ICE if i%2==0 else MINT, LINE, 0.12)
    text(s, item, x+0.12, y+0.10, 3.38, 0.40, 15, NAVY, True, PP_ALIGN.CENTER)
text(s, "Use cases: company performance • peer comparison • cash-flow analysis • forecasting • anomaly and risk review • pipeline monitoring",
     0.95, 6.25, 11.3, 0.38, 12, MUTED, False, PP_ALIGN.CENTER)

# 05 — Capability map
s = new_slide("Platform capabilities map to an engineering lifecycle",
              "Each layer has a defined responsibility; orchestration coordinates execution rather than replacing the data flow.",
              "04  /  solution design")
caps = [
    ("INGEST", "SEC Company Facts", BLUE),
    ("PROCESS", "Python + Pandas", TEAL),
    ("DELIVER", "S3 files + direct Snowflake load", BLUE),
    ("TRANSFORM", "dbt staging / intermediate / marts", TEAL),
    ("SERVE", "Power BI + structured / semantic RAG", BLUE),
]
for i, (h, b, c) in enumerate(caps):
    x = 0.62 + i*2.55
    node(s, x, 2.35, 2.12, 1.55, h, b, c, WHITE, 15, 12)
    if i < 4:
        connector(s, x+2.15, 3.12, x+2.47, 3.12, CYAN, 2.3, True)
shape(s, 1.02, 4.72, 11.25, 0.76, NAVY, NAVY, 0.12)
text(s, "APACHE AIRFLOW  /  schedule • dependency control • retries • task timeouts • execution logs",
     1.25, 4.91, 10.8, 0.34, 15, WHITE, True, PP_ALIGN.CENTER)
text(s, "Important boundary: S3 and Snowflake are parallel delivery destinations. Snowflake is loaded directly by the Python pipeline.",
     1.0, 5.92, 11.2, 0.48, 13, AMBER, True, PP_ALIGN.CENTER)

# 06 — System context architecture
s = new_slide("System context | the actual data paths",
              "The architecture deliberately separates file delivery from warehouse loading.",
              "05  /  architecture")
node(s, 4.75, 1.72, 3.35, 0.92, "SEC EDGAR", "Company Facts API", BLUE, ICE, 17, 12)
connector(s, 6.42, 2.65, 6.42, 2.98, CYAN, 2.2)
node(s, 4.45, 2.98, 3.95, 0.92, "PYTHON INGESTION", "Extract • normalize • validate", TEAL, WHITE, 17, 12)
# two distinct branches
connector(s, 5.15, 3.92, 2.72, 4.48, BLUE, 2.3)
connector(s, 7.72, 3.92, 10.55, 4.48, TEAL, 2.3)
node(s, 0.72, 4.48, 4.05, 1.00, "AWS S3 FILE DELIVERY", "CSV / Parquet • Boto3", BLUE, ICE, 16, 12)
node(s, 8.55, 4.48, 4.05, 1.00, "SNOWFLAKE WAREHOUSE", "Direct connector • write_pandas()", TEAL, MINT, 16, 12)
connector(s, 10.58, 5.48, 10.58, 5.82, TEAL, 2.1)
node(s, 8.68, 5.82, 3.82, 0.76, "dbt ANALYTICS MODELS", "Staging → intermediate → marts", BLUE, WHITE, 14, 11)
text(s, "POWER BI + LOCAL AI / RAG", 0.92, 5.88, 4.0, 0.30, 15, NAVY, True, PP_ALIGN.CENTER)
text(s, "Consume approved analytical outputs", 0.92, 6.22, 4.0, 0.24, 11, MUTED, False, PP_ALIGN.CENTER)
label(s, "Airflow coordinates the pipeline", 4.88, 6.40, 3.35, NAVY2)

# 07 — DFD level 0
s = new_slide("Data flow diagram | Level 0",
              "System boundary view: source, processing platform, storage destinations and consumers.",
              "06  /  data flow")
node(s, 0.58, 2.70, 2.42, 1.08, "SEC EDGAR", "External data source", BLUE, ICE, 16, 12)
shape(s, 4.25, 2.12, 4.40, 2.20, NAVY, NAVY, 0.14)
text(s, "ACI PLATFORM", 4.55, 2.48, 3.8, 0.48, 25, WHITE, True, PP_ALIGN.CENTER)
text(s, "Extract • transform • validate\norchestrate • publish analytical data",
     4.62, 3.05, 3.65, 0.75, 15, RGBColor(196, 216, 232), False, PP_ALIGN.CENTER)
node(s, 10.25, 1.65, 2.48, 0.98, "AWS S3", "CSV / Parquet files", AMBER, PALE_AMBER, 15, 11)
node(s, 10.25, 3.20, 2.48, 0.98, "SNOWFLAKE", "Warehouse + dbt marts", TEAL, MINT, 15, 11)
node(s, 4.72, 5.18, 3.45, 0.95, "CONSUMERS", "Power BI • AI assistant", BLUE, WHITE, 15, 11)
connector(s, 3.02, 3.24, 4.20, 3.24, BLUE, 2.5)
connector(s, 8.68, 2.80, 10.18, 2.12, AMBER, 2.3)
connector(s, 8.68, 3.55, 10.18, 3.67, TEAL, 2.3)
connector(s, 6.45, 4.35, 6.45, 5.12, BLUE, 2.3)
text(s, "Company facts", 3.05, 2.88, 1.12, 0.22, 10, MUTED)
text(s, "File objects", 8.92, 2.05, 1.05, 0.22, 10, MUTED)
text(s, "Direct load", 8.95, 3.77, 1.10, 0.22, 10, MUTED)
text(s, "S3 and Snowflake are separate outputs — there is no S3 → Snowflake load dependency.",
     1.10, 6.45, 11.1, 0.28, 12, AMBER, True, PP_ALIGN.CENTER)

# 08 — DFD level 1
s = new_slide("Data flow diagram | Level 1",
              "Decomposition of the pipeline into independently understandable processing and delivery stages.",
              "07  /  data flow")
stages = [
    ("01  EXTRACT", "SEC API", BLUE),
    ("02  NORMALIZE", "Python / Pandas", TEAL),
    ("03A  FILE PATH", "CSV / Parquet", AMBER),
    ("03B  WAREHOUSE", "write_pandas()", TEAL),
    ("04  TRANSFORM", "dbt models", BLUE),
]
xs = [0.55, 3.05, 5.55, 8.05, 10.55]
for x, (h, b, c) in zip(xs, stages):
    node(s, x, 1.95, 2.18, 1.10, h, b, c, WHITE, 14, 11)
connector(s, 2.76, 2.50, 3.00, 2.50, CYAN, 2.0)
connector(s, 5.26, 2.50, 5.50, 2.50, CYAN, 2.0)
# no connection from file branch to warehouse branch
connector(s, 4.20, 3.08, 6.60, 3.78, AMBER, 2.0)
connector(s, 9.12, 3.08, 9.12, 3.75, TEAL, 2.0)
node(s, 5.55, 3.78, 2.15, 0.82, "AWS S3", "Object storage", AMBER, PALE_AMBER, 14, 10)
node(s, 8.05, 3.78, 2.15, 0.82, "SNOWFLAKE", "Source tables", TEAL, MINT, 14, 10)
connector(s, 10.25, 4.18, 11.55, 3.10, TEAL, 2.0)
node(s, 10.55, 4.60, 2.18, 0.88, "CONSUMPTION", "Power BI / AI", BLUE, ICE, 14, 10)
text(s, "Airflow schedules and coordinates the execution tasks; it is not a data store.",
     1.0, 6.10, 11.3, 0.34, 14, NAVY, True, PP_ALIGN.CENTER)

# 09 — Data engineering
s = new_slide("Ingestion engineering | from facts to reusable observations",
              "The Python pipeline is responsible for source extraction, normalization, file outputs and direct warehouse loading.",
              "08  /  ingestion")
steps = [
    ("SOURCE", "SEC Company Facts\nAMZN • MSFT • GOOGL • META"),
    ("TRANSFORM", "Python + Pandas\nExtract and normalize"),
    ("VALIDATE", "Pipeline checks\nRun-level output validation"),
]
for i, (h, b) in enumerate(steps):
    x = 0.78 + i*4.18
    node(s, x, 1.95, 3.55, 1.38, h, b, [BLUE, TEAL, BLUE][i], WHITE, 17, 13)
    if i < 2:
        connector(s, x+3.58, 2.63, x+4.08, 2.63, CYAN, 2.4)
# outputs
node(s, 1.28, 4.35, 4.65, 1.10, "FILE OUTPUT", "Local CSV + Parquet → configured S3 upload", AMBER, PALE_AMBER, 16, 12)
node(s, 7.38, 4.35, 4.65, 1.10, "WAREHOUSE OUTPUT", "Direct Snowflake load via write_pandas()", TEAL, MINT, 16, 12)
connector(s, 2.55, 3.35, 3.58, 4.28, AMBER, 2.2)
connector(s, 6.95, 3.35, 9.60, 4.28, TEAL, 2.2)
text(s, "Engineering considerations", 0.90, 5.88, 3.2, 0.28, 13, NAVY, True)
text(s, "Company identifiers • fiscal periods • units • source tags • missing-value semantics",
     3.45, 5.88, 8.8, 0.30, 13, MUTED)

# 10 — Warehouse / dbt
s = new_slide("Analytics engineering | modular dbt model layers",
              "Snowflake hosts the modeled data; dbt separates source standardization, reusable logic and consumption marts.",
              "09  /  warehouse")
layers = [
    ("STAGING", "2 SQL models", "Source-aligned standardization", BLUE),
    ("INTERMEDIATE", "9 SQL models", "Reusable transformations and business logic", TEAL),
    ("MARTS", "9 SQL models", "Consumption-oriented analytical outputs", NAVY2),
]
for i, (h, n, b, c) in enumerate(layers):
    x = 0.78 + i*4.20
    shape(s, x, 2.05, 3.55, 2.05, WHITE, LINE, 0.12)
    shape(s, x, 2.05, 3.55, 0.48, c, c, 0.10)
    text(s, h, x+0.12, 2.12, 3.31, 0.28, 14, WHITE, True, PP_ALIGN.CENTER)
    text(s, n, x+0.12, 2.82, 3.31, 0.48, 25, c, True, PP_ALIGN.CENTER)
    text(s, b, x+0.22, 3.42, 3.11, 0.42, 12, MUTED, False, PP_ALIGN.CENTER)
    if i < 2:
        connector(s, x+3.62, 3.06, x+4.08, 3.06, CYAN, 2.4)
stat(s, 1.0, 4.75, 2.45, "20", "SQL MODELS", BLUE)
stat(s, 3.95, 4.75, 2.45, "2", "SEEDS", TEAL)
stat(s, 6.90, 4.75, 2.45, "2", "SOURCES", BLUE)
stat(s, 9.85, 4.75, 2.45, "72", "DATA TESTS", TEAL)
text(s, "Model counts: 2 staging + 9 intermediate + 9 marts. The 72 count refers to data tests.",
     1.0, 6.20, 11.2, 0.32, 12, MUTED, False, PP_ALIGN.CENTER)

# 11 — Airflow
s = new_slide("Orchestration | three explicit tasks, one observable DAG",
              "DAG: aci_sec_financial_pipeline  •  verified manual run: 27 November 2026",
              "10  /  operations")
dag = [
    ("run_sec_pipeline", "SEC extraction\nand delivery"),
    ("validate_pipeline_outputs", "Validate generated\npipeline outputs"),
    ("run_dbt_build", "Execute dbt\nbuild"),
]
for i, (h, b) in enumerate(dag):
    x = 0.82 + i*4.23
    node(s, x, 2.08, 3.30, 1.48, h, b, [BLUE, TEAL, NAVY2][i], WHITE, 15, 12)
    shape(s, x+0.94, 3.83, 1.42, 0.36, PALE_GREEN, PALE_GREEN, 0.16)
    text(s, "SUCCESS", x+1.02, 3.88, 1.26, 0.24, 10, GREEN, True, PP_ALIGN.CENTER)
    if i < 2:
        connector(s, x+3.34, 2.82, x+4.12, 2.82, CYAN, 2.5)
panel(s, 0.90, 4.75, 3.55, 1.10, "RETRY POLICY", "2 retries configured", BLUE, WHITE, 15, 12)
panel(s, 4.88, 4.75, 3.55, 1.10, "TASK TIMEOUTS", "Task-level execution limits", TEAL, WHITE, 15, 12)
panel(s, 8.86, 4.75, 3.55, 1.10, "DAG TIMEOUT", "70-minute DAG timeout", BLUE, WHITE, 15, 12)
text(s, "The verified run completed all three tasks successfully; this is execution evidence, not proof of long-term SLA performance.",
     0.95, 6.22, 11.4, 0.38, 12, MUTED, False, PP_ALIGN.CENTER)

# 12 — Execution evidence
s = new_slide("Execution evidence | successful end-to-end manual run",
              "Observed Airflow and dbt results from 27 November 2026.",
              "11  /  validation")
stat(s, 0.78, 1.92, 2.78, "3 / 3", "AIRFLOW TASKS SUCCESS", GREEN)
stat(s, 3.78, 1.92, 2.78, "94", "DBT BUILD STEPS PASSED", BLUE)
stat(s, 6.78, 1.92, 2.78, "72", "DBT DATA TESTS", TEAL)
stat(s, 9.78, 1.92, 2.78, "0", "WARNINGS / ERRORS", GREEN)
text(s, "DBT BUILD SUMMARY", 0.92, 3.68, 3.0, 0.30, 12, NAVY, True)
# status rail with explicit components
bar_x, bar_y, bar_w = 0.92, 4.18, 11.45
shape(s, bar_x, bar_y, bar_w, 0.48, PALE_GREEN, PALE_GREEN, 0.12)
text(s, "PASS 94", bar_x+0.15, bar_y+0.08, 2.0, 0.28, 14, GREEN, True)
text(s, "WARN 0     ERROR 0     SKIP 0     NO-OP 0",
     bar_x+4.10, bar_y+0.08, 6.9, 0.28, 14, NAVY, True, PP_ALIGN.CENTER)
panel(s, 1.0, 5.25, 5.35, 0.92, "HOW TO READ THIS",
      "94 is the successful dbt build-step total; 72 is the data-test count.", BLUE, WHITE, 14, 11)
panel(s, 6.72, 5.25, 5.35, 0.92, "WHAT IT PROVES",
      "The recorded manual run completed the defined pipeline tasks and dbt build without reported warnings or errors.", TEAL, WHITE, 14, 11)

# 13 — BI report and honest status
s = new_slide("Analytics layer | seven-page Power BI report",
              "The report design covers financial analysis and operational monitoring; semantic-model validation remains in progress.",
              "12  /  analytics")
pages = [
    "Company performance", "Peer comparison", "Cash-flow analysis",
    "Revenue forecasting", "Financial anomalies", "Risk indicators",
    "Settings & information"
]
for i, item in enumerate(pages):
    col = i % 4
    row = i // 4
    x = 0.78 + col*3.12
    y = 1.92 + row*1.02
    fill = ICE if i%2==0 else MINT
    shape(s, x, y, 2.78, 0.72, fill, LINE, 0.10)
    text(s, f"{i+1:02d}", x+0.12, y+0.15, 0.42, 0.35, 15, TEAL, True, PP_ALIGN.CENTER)
    text(s, item, x+0.62, y+0.12, 2.00, 0.42, 13, NAVY, True)
panel(s, 0.85, 5.35, 5.55, 0.90, "IMPLEMENTED ARTIFACT",
      "A seven-page Power BI report exists in the project workspace.", BLUE, WHITE, 14, 11)
panel(s, 6.75, 5.35, 5.55, 0.90, "KNOWN BLOCKER",
      "A semantic-model cyclic-reference issue remains unresolved; publication is not verified.", AMBER, PALE_AMBER, 14, 11)
text(s, "No live dashboard screenshot or successful cloud publication is claimed in this deck.",
     1.0, 6.55, 11.2, 0.26, 11, MUTED, False, PP_ALIGN.CENTER)

# 14 — AI/RAG
s = new_slide("AI layer | hybrid retrieval with local inference",
              "The assistant combines structured analytical retrieval and semantic context before generating a response.",
              "13  /  applied ai")
node(s, 0.58, 2.55, 2.25, 1.12, "USER QUERY", "Natural-language question", BLUE, WHITE, 15, 11)
node(s, 3.35, 2.55, 2.45, 1.12, "ACI AI ROUTER", "HYBRID_SNOWFLAKE_CHROMADB", TEAL, ICE, 14, 10)
connector(s, 2.87, 3.10, 3.30, 3.10, CYAN, 2.2)
node(s, 6.55, 1.55, 2.55, 1.05, "SNOWFLAKE", "Approved analytical marts", TEAL, MINT, 15, 11)
node(s, 6.55, 3.75, 2.55, 1.05, "CHROMADB", "Semantic retrieval context", BLUE, ICE, 15, 11)
connector(s, 5.84, 2.86, 6.50, 2.15, TEAL, 2.1)
connector(s, 5.84, 3.38, 6.50, 4.25, BLUE, 2.1)
node(s, 10.05, 2.55, 2.55, 1.12, "OLLAMA", "Local LLM inference", NAVY2, WHITE, 15, 11)
connector(s, 9.15, 2.15, 10.00, 2.80, TEAL, 2.1)
connector(s, 9.15, 4.25, 10.00, 3.45, BLUE, 2.1)
node(s, 9.85, 4.55, 2.95, 0.78, "GROUNDED ANSWER", "Retrieved context → response", TEAL, MINT, 14, 10)
connector(s, 11.32, 3.72, 11.32, 4.50, CYAN, 2.0)
shape(s, 0.90, 5.75, 11.5, 0.62, PALE_AMBER, PALE_AMBER, 0.12)
text(s, "GUARDRAIL  /  Use approved marts and retrieved context; do not invent unsupported figures or infer AI-specific ROI.",
     1.12, 5.89, 11.05, 0.30, 13, AMBER, True, PP_ALIGN.CENTER)

# 15 — Governance and maturity
s = new_slide("Engineering judgement | what is verified and what is not",
              "A credible portfolio distinguishes implemented capabilities from open validation and deployment work.",
              "14  /  governance")
rows = [
    ("DATA INTERPRETATION", "Company-wide reported facts; not AI-specific ROI.", TEAL, MINT),
    ("MISSING VALUES", "Missing values are not treated as zero by default.", BLUE, ICE),
    ("FREE CASH FLOW", "FREE_CASH_FLOW remains NULL where approved basis is unavailable.", BLUE, ICE),
    ("POWER BI", "Cyclic-reference issue remains; refresh and publication are not verified.", AMBER, PALE_AMBER),
    ("AI DEPLOYMENT", "AI app and Ollama inference are local; public hosting is not verified.", RED, PALE_RED),
]
for i, (h, b, c, fill) in enumerate(rows):
    y = 1.78 + i*0.88
    shape(s, 0.82, y, 2.75, 0.62, fill, LINE, 0.10)
    text(s, h, 0.98, y+0.12, 2.42, 0.34, 12, c, True)
    text(s, b, 3.88, y+0.10, 8.3, 0.40, 14, INK)
text(s, "Transparent limitations are part of the engineering evidence, not a footnote.",
     1.0, 6.45, 11.2, 0.30, 13, NAVY, True, PP_ALIGN.CENTER)

# 16 — Roadmap / close
s = new_slide("Next engineering milestones",
              "Prioritized work to move from an integrated local project toward a more production-ready service.",
              "15  /  roadmap", dark=True)
roadmap = [
    ("01", "Resolve Power BI dependencies", "Fix cyclic references; validate refresh and report visuals.", CYAN),
    ("02", "Verify operational reliability", "Exercise scheduled runs; validate S3 objects and retention.", TEAL),
    ("03", "Harden security controls", "Least-privilege access, secrets handling and auditability.", BLUE),
    ("04", "Operationalize delivery", "CI/CD, alerting, runbooks, backup and recovery tests.", CYAN),
    ("05", "Deploy AI services", "Host the application and inference; validate endpoints and access.", TEAL),
]
for i, (n, h, b, c) in enumerate(roadmap):
    y = 1.82 + i*0.86
    shape(s, 0.88, y, 0.56, 0.48, c, c, 0.12)
    text(s, n, 0.94, y+0.08, 0.44, 0.30, 12, WHITE, True, PP_ALIGN.CENTER)
    text(s, h, 1.72, y+0.01, 4.05, 0.34, 15, WHITE, True)
    text(s, b, 5.90, y+0.01, 6.25, 0.40, 13, RGBColor(190, 208, 224))
text(s, "AI CAPITAL INTELLIGENCE", 0.95, 6.45, 6.0, 0.34, 19, WHITE, True)
text(s, "Financial data engineering  •  Analytics  •  Grounded AI",
     0.98, 6.82, 8.0, 0.22, 10, CYAN, True)
footer(s, 16, True)

prs.save(DEST)
print(f"Created: {DEST}")
print(f"Slides: {len(prs.slides)}")
print(f"Size: {DEST.stat().st_size:,} bytes")
print("All slides use editable PowerPoint shapes and text.")
