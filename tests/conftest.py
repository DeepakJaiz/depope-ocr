from pathlib import Path

import pytest
from fpdf import FPDF


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="INVOICE #INV-001", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Date: 2024-06-01", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Vendor: Acme Corp", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Item A  2  $10.00  $20.00", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Item B  1  $15.00  $15.00", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Subtotal: $35.00", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Tax: $3.50", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Total: $38.50", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"


@pytest.fixture
def invoice_text() -> str:
    return (
        "INVOICE #INV-001\n"
        "Date: 2024-06-01\n"
        "Vendor: Acme Corp\n"
        "Item A  2  $10.00  $20.00\n"
        "Item B  1  $15.00  $15.00\n"
        "Subtotal: $35.00\n"
        "Tax (10%): $3.50\n"
        "Grand Total: $38.50\n"
    )
