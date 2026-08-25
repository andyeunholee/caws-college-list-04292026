"""Headless worker: Google Forms response sheet → college-list reports → email.

Runs on GitHub Actions (see .github/workflows/survey-worker.yml). For every
response row that has not been processed yet, it:

  1. joins every "Question: Answer" pair of the row into one text block,
  2. runs the same pipeline the Streamlit app uses (src.pipeline.run_pipeline),
  3. emails the EN + KR .docx files to the configured recipients,
  4. writes "SENT <timestamp>" (or "ERROR …") into a status column on the
     sheet so the row is never processed twice.

Environment variables (all provided as GitHub Secrets / Variables):
  ANTHROPIC_API_KEY            Claude API key
  GOOGLE_SERVICE_ACCOUNT_JSON  full JSON key of a service account that has
                               Editor access to the sheet
  SHEET_ID                     spreadsheet id from the URL
  SHEET_GID                    worksheet gid from the URL (default: first sheet)
  GMAIL_USER                   sender Gmail address
  GMAIL_APP_PASSWORD           16-char Gmail App Password for GMAIL_USER
  REPORT_RECIPIENTS            comma-separated recipients
  STATUS_COLUMN                header of the status column (default "Report Status")
  MAX_ROWS_PER_RUN             safety cap per run (default 3)
  DISABLE_GROUNDING            "1" (default) = Claude knowledge only, "0" = use Elite dataset
  RESEARCH_MODEL               optional model override for the generation step
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import smtplib
import sys
import traceback
from email.message import EmailMessage
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline  # noqa: E402

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
DOCX_MIME = (
    "application",
    "vnd.openxmlformats-officedocument.wordprocessingml.document",
)


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if default is not None:
        return default
    raise SystemExit(f"Missing required environment variable: {name}")


def _log(msg: str) -> None:
    stamp = _dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {msg}", flush=True)


# ────────────────────────── Google Sheets ──────────────────────────


def _open_worksheet() -> gspread.Worksheet:
    sa_json = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds = Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(_env("SHEET_ID"))
    gid = os.environ.get("SHEET_GID", "").strip()
    if gid:
        for ws in spreadsheet.worksheets():
            if str(ws.id) == gid:
                return ws
        raise SystemExit(f"Worksheet with gid={gid} not found in spreadsheet")
    return spreadsheet.sheet1


def _ensure_status_column(ws: gspread.Worksheet, headers: list[str], name: str) -> int:
    """Return 1-based column index of the status column, creating it if needed."""
    if name in headers:
        return headers.index(name) + 1
    col = len(headers) + 1
    ws.update_cell(1, col, name)
    _log(f"Created status column '{name}' at column {col}")
    return col


def _row_to_text(headers: list[str], row: list[str], status_col: int) -> str:
    """Join every answered question into a free-form text the extractor understands."""
    lines: list[str] = []
    for idx, header in enumerate(headers, start=1):
        if idx == status_col:
            continue
        value = row[idx - 1].strip() if idx - 1 < len(row) else ""
        if not header.strip() or not value:
            continue
        lines.append(f"{header.strip()}: {value}")
    return "\n".join(lines)


# ────────────────────────── Email ──────────────────────────


def _send_email(files: dict[str, Path], subject: str, body: str) -> None:
    user = _env("GMAIL_USER")
    password = _env("GMAIL_APP_PASSWORD")
    recipients = [r.strip() for r in _env("REPORT_RECIPIENTS").split(",") if r.strip()]
    if not recipients:
        raise SystemExit("REPORT_RECIPIENTS is empty")

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)
    for lang_code in ("en", "ko"):
        path = files.get(lang_code)
        if path is None:
            continue
        msg.add_attachment(
            path.read_bytes(),
            maintype=DOCX_MIME[0],
            subtype=DOCX_MIME[1],
            filename=path.name,
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    _log(f"Email sent to {', '.join(recipients)} with {len(msg.get_payload()) - 1} attachment(s)")


# ────────────────────────── Main ──────────────────────────


def main() -> int:
    ws = _open_worksheet()
    status_name = os.environ.get("STATUS_COLUMN", "").strip() or "Report Status"
    max_rows = int(os.environ.get("MAX_ROWS_PER_RUN", "3") or "3")
    disable_grounding = os.environ.get("DISABLE_GROUNDING", "1").strip() != "0"
    research_model = os.environ.get("RESEARCH_MODEL", "").strip() or None

    values = ws.get_all_values()
    if not values:
        _log("Sheet is empty — nothing to do")
        return 0
    headers = values[0]
    status_col = _ensure_status_column(ws, headers, status_name)
    if status_col > len(headers):
        headers = headers + [status_name]

    pending: list[int] = []  # 1-based sheet row numbers
    for sheet_row, row in enumerate(values[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        status = row[status_col - 1].strip() if status_col - 1 < len(row) else ""
        if status.startswith("SENT"):
            continue
        pending.append(sheet_row)

    if not pending:
        _log("No new survey responses")
        return 0
    _log(f"{len(pending)} pending row(s): {pending[:10]}{' …' if len(pending) > 10 else ''}")
    if len(pending) > max_rows:
        _log(f"Processing first {max_rows} this run (MAX_ROWS_PER_RUN)")
        pending = pending[:max_rows]

    output_root = PROJECT_ROOT / "output"
    failures = 0
    for sheet_row in pending:
        row = values[sheet_row - 1]
        text = _row_to_text(headers, row, status_col)
        if len(text) < 40:
            ws.update_cell(sheet_row, status_col, "SKIPPED (empty response)")
            _log(f"Row {sheet_row}: skipped, too little content")
            continue

        ws.update_cell(sheet_row, status_col, f"PROCESSING {_dt.datetime.now():%Y-%m-%d %H:%M}")
        _log(f"Row {sheet_row}: starting pipeline")
        try:
            files = run_pipeline(
                text,
                "both",
                _log,
                disable_grounding=disable_grounding,
                research_model=research_model,
                output_root=output_root,
            )
            student = files["en"].name.split("_college_list_")[0].replace("_", " ")
            today = _dt.date.today().isoformat()
            _send_email(
                files,
                subject=f"[CAWS] College List Report — {student} ({today})",
                body=(
                    f"Automatically generated college list report for {student}.\n\n"
                    f"Attached: English (.docx) and Korean (.docx).\n"
                    f"Source: Google Form response, sheet row {sheet_row}.\n"
                ),
            )
            ws.update_cell(sheet_row, status_col, f"SENT {_dt.datetime.now():%Y-%m-%d %H:%M}")
            _log(f"Row {sheet_row}: done ({student})")
        except Exception as e:  # noqa: BLE001 — record any failure on the sheet
            failures += 1
            err = f"ERROR {_dt.datetime.now():%Y-%m-%d %H:%M} — {type(e).__name__}: {e}"[:480]
            ws.update_cell(sheet_row, status_col, err)
            _log(f"Row {sheet_row}: FAILED\n{traceback.format_exc()}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
