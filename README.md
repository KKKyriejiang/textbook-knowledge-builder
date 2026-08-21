# Textbook Knowledge Builder

Textbook Knowledge Builder is a local-first pipeline and web UI for turning
textbook PDF sections into structured JSON knowledge records for downstream RAG
systems.

The app is designed for controlled extraction:

```text
PDF upload
    -> section detection
    -> local section source JSON
    -> one-section model extraction
    -> schema validation
    -> local knowledge JSON
```

## Current Version

This first version supports:

- Local browser UI for uploading a textbook PDF.
- Textbook metadata capture: grade, course ID, course name, textbook name.
- Automatic section manifest generation from PDF structure.
- Local-only section source JSON generation.
- Controlled single-section OpenAI extraction with explicit confirmation.
- Deterministic knowledge IDs and page trace IDs.
- Strict knowledge schema validation.
- Public-safe quality review summaries for generated knowledge JSON.
- Privacy-oriented `.gitignore` rules for raw PDFs and derived textbook data.

## Privacy Model

Real textbook PDFs and derived textbook artifacts must remain local.

Do not commit:

- `data/raw/`
- `data/intermediate/`
- `data/processed/*knowledge*.json`
- `.env`
- any real PDF, text dump, section source JSON, or generated real knowledge JSON

The final knowledge JSON intentionally excludes raw page text, prompts, raw
model responses, and source page objects.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

Create a local `.env` file:

```text
OPENAI_API_KEY=your_api_key_here
```

Optional runtime settings:

```text
TEXTBOOK_KB_OPENAI_MODEL=gpt-5.6-luna
TEXTBOOK_KB_OPENAI_MAX_OUTPUT_TOKENS=5000
TEXTBOOK_KB_OPENAI_TIMEOUT_SECONDS=90
TEXTBOOK_KB_OPENAI_MAX_RETRIES=2
```

## Run The Local Web UI

```powershell
.\.venv\Scripts\python.exe scripts\run_local_app.py --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

In the UI:

1. Upload a PDF.
2. Enter grade, course ID, course name, and textbook name.
3. Click `Build Sections`.
4. Select one section.
5. Confirm one model call.
6. Click `Extract Selected`.
7. Download the generated knowledge JSON.

## Command Line Workflow

Generate a section manifest:

```powershell
.\.venv\Scripts\python.exe scripts\generate_section_manifest.py data\raw\Your_Textbook.pdf --output data\intermediate\Your_Textbook_sections.json
```

Generate local-only section sources:

```powershell
.\.venv\Scripts\python.exe scripts\export_section_sources.py data\raw\Your_Textbook.pdf --manifest data\intermediate\Your_Textbook_sections.json --textbook-config config\textbooks.json --output data\intermediate\Your_Textbook_section_sources.json
```

List sections without an API call:

```powershell
.\.venv\Scripts\python.exe scripts\extract_single_section_knowledge.py --section-sources data\intermediate\Your_Textbook_section_sources.json --list-sections
```

Dry-run one section:

```powershell
.\.venv\Scripts\python.exe scripts\extract_single_section_knowledge.py --section-sources data\intermediate\Your_Textbook_section_sources.json --section-index 0
```

Run one controlled real extraction:

```powershell
.\.venv\Scripts\python.exe scripts\extract_single_section_knowledge.py --section-sources data\intermediate\Your_Textbook_section_sources.json --section-index 0 --output data\processed\controlled_section_knowledge.json --confirm-api-call
```

Review generated knowledge JSON:

```powershell
.\.venv\Scripts\python.exe scripts\review_knowledge_json.py data\processed\controlled_section_knowledge.json
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Notes

The app currently supports controlled single-section extraction. Multi-section
batch extraction should be added with an explicit queue, estimated API call
count, and user confirmation before sending any real textbook text to a model.
