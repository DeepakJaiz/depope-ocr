from app.models import ContainerInfo, ExtractionResponse, HealthResponse, ErrorResponse


class TestContainerInfo:
    def test_defaults(self):
        c = ContainerInfo(number="FFAU6029848")
        assert c.number == "FFAU6029848"
        assert c.type_size is None

    def test_full(self):
        c = ContainerInfo(number="HASU1493470", type_size="40' HC")
        assert c.number == "HASU1493470"
        assert c.type_size == "40' HC"


class TestExtractionResponse:
    def test_minimal(self):
        r = ExtractionResponse()
        assert r.depot is None
        assert r.validity_date is None
        assert r.shipping_line is None
        assert r.containers is None
        assert r.raw_text is None
        assert r.error is None

    def test_full(self):
        r = ExtractionResponse(
            depot="DP World",
            validity_date="25-Jul-2026",
            shipping_line="MAERSK",
            containers=[ContainerInfo(number="FFAU6029848")],
            raw_text="some text",
        )
        assert r.depot == "DP World"
        assert r.validity_date == "25-Jul-2026"
        assert r.shipping_line == "MAERSK"
        assert len(r.containers) == 1
        assert r.containers[0].number == "FFAU6029848"
        assert r.raw_text == "some text"

    def test_error(self):
        r = ExtractionResponse(error="Something went wrong")
        assert r.error == "Something went wrong"


class TestHealthResponse:
    def test_ok(self):
        h = HealthResponse(status="ok", ocr_loaded=True)
        assert h.status == "ok"
        assert h.ocr_loaded is True


class TestErrorResponse:
    def test_minimal(self):
        e = ErrorResponse(error="bad")
        assert e.error == "bad"
        assert e.detail is None

    def test_full(self):
        e = ErrorResponse(error="bad", detail="something broke")
        assert e.detail == "something broke"
