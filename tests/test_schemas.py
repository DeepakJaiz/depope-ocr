from app.schemas import ContainerInfo, ExtractionResponse, HealthResponse


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
        assert r.containers is None

    def test_full(self):
        r = ExtractionResponse(
            depot="DP World",
            validity_date="25-Jul-2026",
            shipping_line="MAERSK",
            containers=[ContainerInfo(number="FFAU6029848")],
            raw_text="some text",
        )
        assert r.depot == "DP World"
        assert r.raw_text == "some text"

    def test_error(self):
        r = ExtractionResponse(error="Something went wrong")
        assert r.error == "Something went wrong"


class TestHealthResponse:
    def test_ok(self):
        h = HealthResponse(status="ok", ocr_loaded=True)
        assert h.status == "ok"
        assert h.ocr_loaded is True
