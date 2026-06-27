# Depope OCR

FastAPI service that extracts text and structured invoice data from PDF files using Tesseract OCR.

## Features

- Upload a PDF, get back raw OCR text per page
- Automatic invoice field extraction (number, date, vendor, totals, line items)
- Regex-based parser works offline — no external API calls
- Ready for AI augmentation (drop in an LLM API key for smarter extraction)

## Quick Start

### Using Docker (recommended)

```bash
docker build -t depope-ocr .
docker run -p 8000:8000 depope-ocr
```

Server starts at `http://localhost:8000`.

### Local development

```bash
# 1. System dependencies
sudo apt install tesseract-ocr poppler-utils

# 2. Python env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env

# 4. Run
python run.py
```

## API

### `POST /ocr`

Upload a PDF and get extracted text + structured invoice data.

```bash
curl -X POST http://localhost:8000/ocr \
  -F "file=@invoice.pdf"
```

**Response:**

```json
{
  "filename": "invoice.pdf",
  "total_pages": 1,
  "full_text": "INVOICE #INV-001\n...",
  "pages": [
    {
      "page_number": 1,
      "raw_text": "INVOICE #INV-001\n..."
    }
  ],
  "invoice": {
    "invoice_number": "INV-001",
    "date": "2024-06-01",
    "vendor_name": null,
    "subtotal": null,
    "tax": null,
    "total": 150.0,
    "line_items": []
  }
}
```

### `GET /health`

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Project Structure

```
├── app/
│   ├── main.py       # FastAPI app & routes
│   ├── models.py     # Pydantic schemas
│   ├── ocr.py        # PDF → images → OCR pipeline
│   └── parser.py     # Regex invoice field extraction
├── uploads/          # Uploaded files (if saved to disk)
├── .env.example      # Config template
├── requirements.txt
└── run.py            # Dev server launcher
```

## Configuration

All settings in `.env`:

| Variable          | Default | Description              |
|-------------------|---------|--------------------------|
| `HOST`            | 0.0.0.0 | Server bind address      |
| `PORT`            | 8000    | Server port              |
| `RELOAD`          | true    | Auto-reload on changes   |
| `OCR_DPI`         | 300     | PDF rendering resolution |
| `OCR_LANG`        | eng     | Tesseract language        |
| `MAX_FILE_SIZE_MB`| 50      | Max upload size           |

## Extending with AI

For higher accuracy on complex invoices, set `LLM_API_KEY` in `.env` to use an LLM (Gemini/OpenAI) for semantic extraction instead of regex. The OCR text feeds into the LLM prompt for structured JSON output — the same pattern used by the [RaftLabs invoice-scan](https://dev.to/raftlabs/building-next-gen-invoice-scanning-with-ai-and-llms-4nkb) pipeline.
