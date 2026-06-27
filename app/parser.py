import re
from app.models import ExtractedInvoice, ExtractedLineItem


_INVOICE_NUM_PATTERNS = [
    re.compile(r"(?:invoice\s*(?:#|no|number|num))[\s:#]*(\S+)", re.IGNORECASE),
    re.compile(r"\binv(?!oice)[\s:#]+(\S+)", re.IGNORECASE),
    re.compile(r"\b(inv(?!oice)[-\w]+)", re.IGNORECASE),
]

_DATE_PATTERNS = [
    re.compile(r"(?:invoice\s*)?date[\s:#]*(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4})", re.IGNORECASE),
    re.compile(r"(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4})"),
]

_VENDOR_PATTERNS = [
    re.compile(r"(?:vendor|seller|supplier|from|bill\s*from)[\s:.#-]*(.+)", re.IGNORECASE),
]

_TOTAL_PATTERNS = [
    re.compile(r"\b(?:grand\s*)?total\b[\s:#]*[₹$€£]?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE),
    re.compile(r"amount\s*(?:due|paid|total)[\s:#]*[₹$€£]?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE),
]

_SUBTOTAL_PATTERNS = [
    re.compile(r"\bsub[\s-]*total\b[\s:#]*[₹$€£]?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE),
]

_TAX_PATTERNS = [
    re.compile(r"\b(?:tax|vat|gst)\b[\s:#]*[₹$€£]?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE),
    re.compile(r"\b(?:tax|vat|gst)\b\s*(?:\d+%)?\s*[₹$€£]?\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE),
]

_LINE_ITEM_PATTERN = re.compile(
    r"^(.+?)\s+(\d+)\s+[₹$€£]?\s*(\d+(?:[.,]\d+)?)\s+[₹$€£]?\s*(\d+(?:[.,]\d+)?)$",
    re.MULTILINE,
)


def _first_match(patterns: list[re.Pattern], text: str) -> str | None:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(1).strip()
    return None


def _parse_float(val: str | None) -> float | None:
    if val is None:
        return None
    val = val.replace(",", "")
    try:
        return float(val)
    except ValueError:
        return None


def parse_invoice(text: str) -> ExtractedInvoice:
    invoice_num = _first_match(_INVOICE_NUM_PATTERNS, text)
    date = _first_match(_DATE_PATTERNS, text)
    vendor = _first_match(_VENDOR_PATTERNS, text)
    total = _parse_float(_first_match(_TOTAL_PATTERNS, text))
    subtotal = _parse_float(_first_match(_SUBTOTAL_PATTERNS, text))
    tax = _parse_float(_first_match(_TAX_PATTERNS, text))

    line_items = []
    for m in _LINE_ITEM_PATTERN.finditer(text):
        line_items.append(
            ExtractedLineItem(
                description=m.group(1).strip(),
                quantity=_parse_float(m.group(2)),
                unit_price=_parse_float(m.group(3)),
                total=_parse_float(m.group(4)),
            )
        )

    return ExtractedInvoice(
        invoice_number=invoice_num,
        date=date,
        vendor_name=vendor,
        subtotal=subtotal,
        tax=tax,
        total=total,
        line_items=line_items,
    )
