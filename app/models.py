from pydantic import BaseModel


class ContainerInfo(BaseModel):
    number: str
    type_size: str | None = None


class ExtractionResponse(BaseModel):
    depot: str | None = None
    validity_date: str | None = None
    shipping_line: str | None = None
    containers: list[ContainerInfo] | None = None
    raw_text: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    ocr_loaded: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
