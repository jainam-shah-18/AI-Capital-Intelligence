from pathlib import Path
from zipfile import ZipFile
from pptx import Presentation
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

PPTX = ROOT / "deliverables" / "AI_Capital_Intelligence_Presentation.pptx"
PDF = ROOT / "deliverables" / "AI_Capital_Intelligence_Project_Report.pdf"

REQUIRED_TERMS = [
    "Snowflake",
    "Airflow",
    "dbt",
    "SEC",
    "Production Readiness",
    "Power BI",
    "RAG",
]

def check_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing deliverable: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Empty deliverable: {path}")

print("=== POWERPOINT VALIDATION ===")
check_file(PPTX)

prs = Presentation(PPTX)
print(f"Slide count: {len(prs.slides)}")

ppt_text = []

for index, slide in enumerate(prs.slides, 1):
    texts = [
        shape.text.strip().replace("\n", " | ")
        for shape in slide.shapes
        if shape.has_text_frame and shape.text.strip()
    ]
    ppt_text.extend(texts)
    print(f"Slide {index:02}: {'; '.join(texts[:3])}")

ppt_content = "\n".join(ppt_text).casefold()

print("\n=== PDF VALIDATION ===")
check_file(PDF)

reader = PdfReader(str(PDF))
pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)

print("PDF header valid:", PDF.read_bytes().startswith(b"%PDF-"))
print("PDF pages:", len(reader.pages))
print("PDF encrypted:", reader.is_encrypted)
print("Extracted characters:", len(pdf_text))
print("File size:", PDF.stat().st_size, "bytes")

print("\n=== REQUIRED CONTENT ===")
print(f"{'Topic':25} {'PowerPoint':15} {'PDF'}")

for term in REQUIRED_TERMS:
    ppt_present = term.casefold() in ppt_content
    pdf_present = term.casefold() in pdf_text.casefold()

    print(f"{term:25} {str(ppt_present):15} {pdf_present}")

print("\n=== POWERPOINT PACKAGE ===")
with ZipFile(PPTX) as archive:
    integrity = archive.testzip()
    print("Package integrity:", integrity or "PASS")

print("\n=== FINAL SUMMARY ===")
print("PowerPoint slides:", len(prs.slides))
print("PDF pages:", len(reader.pages))
print("PDF text extracted:", len(pdf_text) > 0)
print("Validation completed.")
