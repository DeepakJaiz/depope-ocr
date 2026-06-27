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
