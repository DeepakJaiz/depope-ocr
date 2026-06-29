from __future__ import annotations

from pydantic import BaseModel


class ContainerInfo(BaseModel):
    number: str
    type_size: str | None = None


class ExtractionResponse(BaseModel):
    do_number: str | None = None
    consignee: str | None = None
    depot: str | None = None
    validity_date: str | None = None
    shipping_line: str | None = None
    containers: list[ContainerInfo] | None = None
    raw_text: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    onnxruntime_version: str | None = None
    ocr_loaded: bool
