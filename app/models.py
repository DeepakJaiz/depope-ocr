from pydantic import BaseModel
from typing import Optional


class ExtractedLineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class ExtractedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    customer_name: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    line_items: list[ExtractedLineItem] = []


class OcrPageResult(BaseModel):
    page_number: int
    raw_text: str


class OcrResponse(BaseModel):
    filename: str
    total_pages: int
    full_text: str
    pages: list[OcrPageResult]
    invoice: Optional[ExtractedInvoice] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
