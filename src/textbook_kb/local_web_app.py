from __future__ import annotations

import base64
import json
import mimetypes
import re
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from textbook_kb.controlled_extraction import (
    extract_single_section_local,
    list_controlled_sections,
    load_local_section_sources_json,
    select_controlled_section,
)
from textbook_kb.knowledge_export import (
    validate_private_knowledge_output_path,
)
from textbook_kb.knowledge_quality import (
    review_knowledge_json,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
    openai_runtime_is_configured,
)
from textbook_kb.metadata import (
    TextbookMetadata,
    save_section_manifest,
)
from textbook_kb.openai_model_client import (
    OpenAIStructuredKnowledgeModelClient,
)
from textbook_kb.section_source_export import (
    build_section_sources_from_pdf,
    save_section_sources_json,
)
from textbook_kb.structure_manifest import (
    generate_section_manifest_from_pdf,
)


MAX_UPLOAD_BYTES = 80 * 1024 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


@dataclass(frozen=True)
class UploadedTextbookPaths:
    pdf_path: Path
    manifest_path: Path
    section_sources_path: Path

    def to_public_dict(
        self,
        project_root: Path,
    ) -> dict[str, str]:
        return {
            "pdf_path": _display_path(
                self.pdf_path,
                project_root,
            ),
            "manifest_path": _display_path(
                self.manifest_path,
                project_root,
            ),
            "section_sources_path": _display_path(
                self.section_sources_path,
                project_root,
            ),
        }


def _display_path(
    path: Path,
    project_root: Path,
) -> str:
    try:
        return path.resolve().relative_to(
            project_root.resolve()
        ).as_posix()
    except ValueError:
        return str(
            path.resolve()
        )


def _slugify_filename_stem(
    value: str,
) -> str:
    stem = Path(
        value
    ).stem

    ascii_stem = stem.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        ascii_stem,
    ).strip("_")

    if not slug:
        slug = "textbook"

    return slug[:80]


def safe_uploaded_pdf_name(
    filename: str,
) -> str:
    if (
        not isinstance(filename, str)
        or not filename.strip()
    ):
        raise ValueError(
            "filename must be a non-empty string."
        )

    suffix = Path(
        filename
    ).suffix.lower()

    if suffix != ".pdf":
        raise ValueError(
            "Uploaded file must use the .pdf extension."
        )

    return (
        f"{_slugify_filename_stem(filename)}.pdf"
    )


def _require_json_string(
    data: dict[str, Any],
    key: str,
) -> str:
    value = data.get(
        key
    )

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{key} must be a non-empty string."
        )

    return value.strip()


def _resolve_project_path(
    project_root: Path,
    relative_path: str,
) -> Path:
    if (
        not isinstance(relative_path, str)
        or not relative_path.strip()
    ):
        raise ValueError(
            "path must be a non-empty string."
        )

    path = Path(
        relative_path
    )

    if path.is_absolute():
        resolved = path.resolve()
    else:
        resolved = (
            project_root
            / path
        ).resolve()

    try:
        resolved.relative_to(
            project_root.resolve()
        )
    except ValueError as exc:
        raise ValueError(
            "Path must remain inside the project."
        ) from exc

    return resolved


def _ensure_within_local_data(
    project_root: Path,
    path: Path,
    child: str,
) -> None:
    allowed_root = (
        project_root
        / "data"
        / child
    ).resolve()

    try:
        path.resolve().relative_to(
            allowed_root
        )
    except ValueError as exc:
        raise ValueError(
            f"Path must remain under data/{child}."
        ) from exc


def _decode_pdf_payload(
    payload: str,
) -> bytes:
    try:
        data = base64.b64decode(
            payload,
            validate=True,
        )
    except ValueError as exc:
        raise ValueError(
            "PDF upload payload is not valid base64."
        ) from exc

    if not data:
        raise ValueError(
            "PDF upload payload is empty."
        )

    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(
            "PDF upload exceeds the local size limit."
        )

    if not data.startswith(
        b"%PDF"
    ):
        raise ValueError(
            "Uploaded file does not look like a PDF."
        )

    return data


def _build_uploaded_textbook_paths(
    project_root: Path,
    safe_pdf_name: str,
) -> UploadedTextbookPaths:
    stem = Path(
        safe_pdf_name
    ).stem

    return UploadedTextbookPaths(
        pdf_path=(
            project_root
            / "data"
            / "raw"
            / safe_pdf_name
        ),
        manifest_path=(
            project_root
            / "data"
            / "intermediate"
            / f"{stem}_sections.json"
        ),
        section_sources_path=(
            project_root
            / "data"
            / "intermediate"
            / f"{stem}_section_sources.json"
        ),
    )


def _section_infos_to_dicts(
    section_sources,
) -> list[dict[str, Any]]:
    return [
        info.__dict__
        for info
        in list_controlled_sections(
            section_sources
        )
    ]


def create_textbook_from_upload(
    project_root: Path,
    request_data: dict[str, Any],
) -> dict[str, Any]:
    original_filename = _require_json_string(
        request_data,
        "filename",
    )

    safe_pdf_name = safe_uploaded_pdf_name(
        original_filename
    )

    pdf_bytes = _decode_pdf_payload(
        _require_json_string(
            request_data,
            "pdf_base64",
        )
    )

    metadata = TextbookMetadata(
        grade=_require_json_string(
            request_data,
            "grade",
        ),
        course_id=_require_json_string(
            request_data,
            "course_id",
        ),
        course_name=_require_json_string(
            request_data,
            "course_name",
        ),
        textbook=_require_json_string(
            request_data,
            "textbook",
        ),
        source_file=safe_pdf_name,
    )

    paths = _build_uploaded_textbook_paths(
        project_root=project_root,
        safe_pdf_name=safe_pdf_name,
    )

    paths.pdf_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.pdf_path.write_bytes(
        pdf_bytes
    )

    manifest = generate_section_manifest_from_pdf(
        paths.pdf_path
    )

    save_section_manifest(
        manifest=manifest,
        output_path=paths.manifest_path,
    )

    section_sources = build_section_sources_from_pdf(
        pdf_path=paths.pdf_path,
        textbook_metadata=metadata,
        section_manifest=manifest,
    )

    save_section_sources_json(
        section_sources=section_sources,
        output_path=paths.section_sources_path,
    )

    return {
        "paths": paths.to_public_dict(
            project_root
        ),
        "section_count": len(
            section_sources
        ),
        "sections": (
            _section_infos_to_dicts(
                section_sources
            )
        ),
    }


def list_sections_from_file(
    project_root: Path,
    request_data: dict[str, Any],
) -> dict[str, Any]:
    section_sources_path = _resolve_project_path(
        project_root,
        _require_json_string(
            request_data,
            "section_sources_path",
        ),
    )

    _ensure_within_local_data(
        project_root,
        section_sources_path,
        "intermediate",
    )

    section_sources = load_local_section_sources_json(
        section_sources_path
    )

    return {
        "section_count": len(
            section_sources
        ),
        "sections": (
            _section_infos_to_dicts(
                section_sources
            )
        ),
    }


def extract_selected_section_from_file(
    project_root: Path,
    request_data: dict[str, Any],
) -> dict[str, Any]:
    if request_data.get(
        "confirm_api_call"
    ) is not True:
        raise ValueError(
            "confirm_api_call must be true for extraction."
        )

    section_sources_path = _resolve_project_path(
        project_root,
        _require_json_string(
            request_data,
            "section_sources_path",
        ),
    )

    _ensure_within_local_data(
        project_root,
        section_sources_path,
        "intermediate",
    )

    section_index = request_data.get(
        "section_index"
    )

    if (
        not isinstance(section_index, int)
        or isinstance(section_index, bool)
    ):
        raise ValueError(
            "section_index must be an integer."
        )

    section_sources = load_local_section_sources_json(
        section_sources_path
    )

    selected = select_controlled_section(
        section_sources=section_sources,
        section_index=section_index,
    )

    if not openai_runtime_is_configured():
        raise ValueError(
            "OpenAI API key is not configured."
        )

    stem = section_sources_path.stem.replace(
        "_section_sources",
        "",
    )

    output_path = (
        project_root
        / "data"
        / "processed"
        / (
            f"{stem}_section_{section_index}_"
            "knowledge.json"
        )
    )

    config = OpenAIKnowledgeConfig.from_environment()

    result = extract_single_section_local(
        section_source=selected,
        model_client=(
            OpenAIStructuredKnowledgeModelClient(
                config=config
            )
        ),
        config=config,
        output_path=output_path,
        project_root=project_root,
    )

    review = review_knowledge_json(
        output_path
    )

    return {
        "extraction": result.to_public_dict(),
        "review": review.to_public_dict(),
        "download_path": _display_path(
            output_path,
            project_root,
        ),
    }


def review_local_knowledge_file(
    project_root: Path,
    request_data: dict[str, Any],
) -> dict[str, Any]:
    input_path = _resolve_project_path(
        project_root,
        _require_json_string(
            request_data,
            "input_path",
        ),
    )

    _ensure_within_local_data(
        project_root,
        input_path,
        "processed",
    )

    validate_private_knowledge_output_path(
        output_path=input_path,
        project_root=project_root,
    )

    return review_knowledge_json(
        input_path
    ).to_public_dict()


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Textbook Knowledge Builder</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #627083;
      --line: #d9e0e8;
      --blue: #246bfe;
      --teal: #0f8b8d;
      --amber: #b7791f;
      --red: #b42318;
      --green: #287d3c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 3;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
    }
    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      min-height: 28px;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--teal);
    }
    main {
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(360px, 1fr) minmax(300px, 420px);
      gap: 14px;
      padding: 14px;
      min-height: calc(100vh - 62px);
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
      overflow: hidden;
    }
    .panel-head {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    h2 {
      margin: 0;
      font-size: 14px;
      font-weight: 700;
    }
    .panel-body {
      padding: 16px;
    }
    label {
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin: 0 0 6px;
    }
    input[type="text"], input[type="file"] {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: white;
      color: var(--ink);
      font: inherit;
      padding: 10px;
      min-height: 40px;
    }
    .field {
      margin-bottom: 12px;
    }
    button, .download {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 38px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: var(--blue);
      color: white;
      font-weight: 700;
      font-size: 13px;
      padding: 8px 12px;
      cursor: pointer;
      text-decoration: none;
    }
    button.secondary {
      color: var(--ink);
      background: white;
      border-color: var(--line);
    }
    button.warning {
      background: var(--amber);
    }
    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }
    .section-list {
      height: calc(100vh - 140px);
      overflow: auto;
    }
    .row {
      display: grid;
      grid-template-columns: 48px 1fr 92px;
      gap: 10px;
      align-items: center;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      cursor: pointer;
    }
    .row:hover, .row.selected {
      background: #eef5ff;
    }
    .idx {
      color: var(--muted);
      font-variant-numeric: tabular-nums;
    }
    .title {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: 650;
    }
    .pages {
      color: var(--muted);
      font-size: 12px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    .meta {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 14px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px;
      background: #fbfcfe;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 4px;
    }
    .metric strong {
      display: block;
      font-size: 16px;
    }
    .check {
      display: flex;
      gap: 9px;
      align-items: flex-start;
      margin: 12px 0;
      color: var(--ink);
      font-size: 13px;
    }
    .check input {
      margin-top: 2px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      color: #273444;
      background: #f4f6f8;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      max-height: 260px;
      overflow: auto;
    }
    .ok { color: var(--green); }
    .warn { color: var(--amber); }
    .bad { color: var(--red); }
    @media (max-width: 980px) {
      main {
        grid-template-columns: 1fr;
      }
      .section-list {
        height: 420px;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>Textbook Knowledge Builder</h1>
    <div class="status"><span class="dot"></span><span id="status">Ready</span></div>
  </header>
  <main>
    <section>
      <div class="panel-head"><h2>Textbook</h2></div>
      <div class="panel-body">
        <div class="field">
          <label for="pdf">PDF</label>
          <input id="pdf" type="file" accept="application/pdf">
        </div>
        <div class="field">
          <label for="grade">Grade</label>
          <input id="grade" type="text" value="11">
        </div>
        <div class="field">
          <label for="course_id">Course ID</label>
          <input id="course_id" type="text" value="MCR3U">
        </div>
        <div class="field">
          <label for="course_name">Course Name</label>
          <input id="course_name" type="text" value="Functions">
        </div>
        <div class="field">
          <label for="textbook">Textbook</label>
          <input id="textbook" type="text" value="MCR3U Functions">
        </div>
        <button id="upload">Build Sections</button>
      </div>
    </section>

    <section>
      <div class="panel-head">
        <h2>Sections</h2>
        <button id="reload" class="secondary" disabled>Reload</button>
      </div>
      <div id="sections" class="section-list"></div>
    </section>

    <section>
      <div class="panel-head"><h2>Extraction</h2></div>
      <div class="panel-body">
        <div class="meta">
          <div class="metric"><span>Selected</span><strong id="selected">None</strong></div>
          <div class="metric"><span>Records</span><strong id="records">0</strong></div>
          <div class="metric"><span>Definitions</span><strong id="definitions">0</strong></div>
          <div class="metric"><span>Formulas</span><strong id="formulas">0</strong></div>
        </div>
        <label class="check">
          <input id="confirm" type="checkbox">
          <span>I approve one model call for the selected section.</span>
        </label>
        <button id="extract" class="warning" disabled>Extract Selected</button>
        <a id="download" class="download" href="#" style="display:none; margin-left:8px;">Download JSON</a>
        <div style="height:12px"></div>
        <pre id="log">No output yet.</pre>
      </div>
    </section>
  </main>
  <script>
    const state = { sectionSourcesPath: null, sections: [], selectedIndex: null };
    const $ = (id) => document.getElementById(id);

    function setStatus(text, cls = "") {
      $("status").textContent = text;
      $("status").className = cls;
    }

    function log(value) {
      $("log").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }

    function fileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = String(reader.result || "");
          resolve(result.split(",", 2)[1] || "");
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    async function postJson(path, body) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || response.statusText);
      }
      return data.data;
    }

    function renderSections() {
      const root = $("sections");
      root.innerHTML = "";
      state.sections.forEach((section) => {
        const row = document.createElement("div");
        row.className = "row" + (section.index === state.selectedIndex ? " selected" : "");
        row.onclick = () => {
          state.selectedIndex = section.index;
          $("selected").textContent = String(section.index);
          $("extract").disabled = false;
          renderSections();
        };
        row.innerHTML = `
          <div class="idx">${section.index}</div>
          <div class="title" title="${section.section}">${section.section}</div>
          <div class="pages">${section.page_start}-${section.page_end}</div>
        `;
        root.appendChild(row);
      });
    }

    $("upload").onclick = async () => {
      try {
        const file = $("pdf").files[0];
        if (!file) throw new Error("Choose a PDF first.");
        setStatus("Building local section sources...", "warn");
        $("upload").disabled = true;
        const pdf_base64 = await fileToBase64(file);
        const data = await postJson("/api/upload", {
          filename: file.name,
          pdf_base64,
          grade: $("grade").value,
          course_id: $("course_id").value,
          course_name: $("course_name").value,
          textbook: $("textbook").value,
        });
        state.sectionSourcesPath = data.paths.section_sources_path;
        state.sections = data.sections;
        state.selectedIndex = null;
        $("records").textContent = String(data.section_count);
        $("selected").textContent = "None";
        $("reload").disabled = false;
        $("extract").disabled = true;
        renderSections();
        log(data);
        setStatus("Sections ready", "ok");
      } catch (error) {
        log(error.message);
        setStatus("Build failed", "bad");
      } finally {
        $("upload").disabled = false;
      }
    };

    $("reload").onclick = async () => {
      try {
        if (!state.sectionSourcesPath) return;
        setStatus("Reloading sections...", "warn");
        const data = await postJson("/api/list-sections", {
          section_sources_path: state.sectionSourcesPath,
        });
        state.sections = data.sections;
        renderSections();
        log(data);
        setStatus("Sections ready", "ok");
      } catch (error) {
        log(error.message);
        setStatus("Reload failed", "bad");
      }
    };

    $("extract").onclick = async () => {
      try {
        if (state.selectedIndex === null) throw new Error("Choose a section.");
        if (!$("confirm").checked) throw new Error("Confirm one model call.");
        setStatus("Extracting selected section...", "warn");
        $("extract").disabled = true;
        const data = await postJson("/api/extract", {
          section_sources_path: state.sectionSourcesPath,
          section_index: state.selectedIndex,
          confirm_api_call: true,
        });
        const summary = data.review.record_summaries[0];
        $("records").textContent = String(data.review.record_count);
        $("definitions").textContent = String(summary.definition_count);
        $("formulas").textContent = String(summary.formula_count);
        $("download").href = "/download?path=" + encodeURIComponent(data.download_path);
        $("download").style.display = "inline-flex";
        log(data);
        setStatus("Extraction complete", "ok");
      } catch (error) {
        log(error.message);
        setStatus("Extraction failed", "bad");
      } finally {
        $("extract").disabled = state.selectedIndex === null;
      }
    };
  </script>
</body>
</html>
"""


class TextbookKnowledgeRequestHandler(
    BaseHTTPRequestHandler
):
    project_root: Path

    server_version = (
        "TextbookKnowledgeBuilder/0.1"
    )

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        return

    def _send_bytes(
        self,
        status: HTTPStatus,
        body: bytes,
        content_type: str,
    ) -> None:
        self.send_response(
            status
        )
        self.send_header(
            "Content-Type",
            content_type,
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(
            body
        )

    def _send_json(
        self,
        status: HTTPStatus,
        payload: dict[str, Any],
    ) -> None:
        self._send_bytes(
            status,
            json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _read_json_body(
        self,
    ) -> dict[str, Any]:
        content_length = int(
            self.headers.get(
                "Content-Length",
                "0",
            )
        )

        if content_length <= 0:
            raise ValueError(
                "Request body is empty."
            )

        body = self.rfile.read(
            content_length
        )

        payload = json.loads(
            body.decode("utf-8")
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "JSON body must be an object."
            )

        return payload

    def do_GET(
        self,
    ) -> None:
        parsed = urlparse(
            self.path
        )

        if parsed.path == "/":
            self._send_bytes(
                HTTPStatus.OK,
                HTML.encode("utf-8"),
                "text/html; charset=utf-8",
            )
            return

        if parsed.path == "/download":
            self._download(
                parsed.query
            )
            return

        self._send_json(
            HTTPStatus.NOT_FOUND,
            {
                "ok": False,
                "error": "Not found.",
            },
        )

    def do_POST(
        self,
    ) -> None:
        routes = {
            "/api/upload": create_textbook_from_upload,
            "/api/list-sections": list_sections_from_file,
            "/api/extract": extract_selected_section_from_file,
            "/api/review": review_local_knowledge_file,
        }

        parsed = urlparse(
            self.path
        )

        handler = routes.get(
            parsed.path
        )

        if handler is None:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "ok": False,
                    "error": "Not found.",
                },
            )
            return

        try:
            data = handler(
                self.project_root,
                self._read_json_body(),
            )
        except Exception as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "data": data,
            },
        )

    def _download(
        self,
        query: str,
    ) -> None:
        values = parse_qs(
            query
        )

        raw_path = values.get(
            "path",
            [
                "",
            ],
        )[0]

        try:
            path = _resolve_project_path(
                self.project_root,
                raw_path,
            )
            _ensure_within_local_data(
                self.project_root,
                path,
                "processed",
            )
            validate_private_knowledge_output_path(
                output_path=path,
                project_root=self.project_root,
            )
        except ValueError as exc:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": str(exc),
                },
            )
            return

        if not path.is_file():
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "ok": False,
                    "error": "File not found.",
                },
            )
            return

        content_type = (
            mimetypes.guess_type(
                path.name
            )[0]
            or "application/octet-stream"
        )

        body = path.read_bytes()

        self.send_response(
            HTTPStatus.OK
        )
        self.send_header(
            "Content-Type",
            content_type,
        )
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{path.name}"',
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.end_headers()
        self.wfile.write(
            body
        )


def build_server(
    project_root: str | Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> ThreadingHTTPServer:
    root = Path(
        project_root
    ).resolve()

    if not root.is_dir():
        raise ValueError(
            f"project_root must be a directory: {root}"
        )

    class Handler(
        TextbookKnowledgeRequestHandler
    ):
        pass

    Handler.project_root = root

    return ThreadingHTTPServer(
        (
            host,
            port,
        ),
        Handler,
    )


def run_local_web_app(
    project_root: str | Path = ".",
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = False,
) -> None:
    server = build_server(
        project_root=project_root,
        host=host,
        port=port,
    )

    url = (
        f"http://{host}:{server.server_port}/"
    )

    print(
        f"Textbook Knowledge Builder UI: {url}"
    )

    print(
        "Press Ctrl+C to stop."
    )

    if open_browser:
        webbrowser.open(
            url
        )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
