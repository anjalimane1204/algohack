from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "applications.db"
UPLOAD_DIR = BASE_DIR / "uploaded_documents"
DB_PATH.parent.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_DOC_TYPES = {"id_proof", "address_proof", "photograph", "other_document"}
REQUIRED_DOCS = ["id_proof", "address_proof", "photograph"]
REQUIRED_FIELDS = ["name", "dob", "address", "phone", "pass_type"]

ocr_engine = RapidOCR()

app = FastAPI(title="Smart Application Verification API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s/.-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_name_from_text(text: str) -> str:
    patterns = [
        r"name\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]+)",
        r"applicant\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_dob_from_text(text: str) -> str:
    match = re.search(r"\b(?:0?[1-9]|[12][0-9]|3[01])[/-](?:0?[1-9]|1[0-2])[/-](?:\d{2,4})\b", text)
    if match:
        return match.group(0)
    return ""


def extract_phone_from_text(text: str) -> str:
    match = re.search(r"\+?\d{10,15}", text)
    if match:
        return match.group(0)
    return ""


def extract_address_from_text(text: str) -> str:
    match = re.search(r"address\s*[:\-]?\s*([A-Za-z0-9 ,./#-]+)", text, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).strip()[:180]


def extract_pass_type_from_text(text: str) -> str:
    for keyword in ["daily", "monthly", "student", "senior citizen", "general", "concession", "commuter"]:
        if keyword.lower() in text.lower():
            return keyword
    return ""


def safe_read_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception:
        return ""


def extract_text_from_file(file_path: Path) -> str:
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        text = safe_read_pdf(file_path)
        if text.strip():
            return text
    try:
        result, _ = ocr_engine(str(file_path))
        if result:
            lines = []
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    lines.append(str(item[1]))
            text = "\n".join(lines)
            if text.strip():
                return text
    except Exception:
        pass
    return ""


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            name TEXT,
            dob TEXT,
            address TEXT,
            phone TEXT,
            pass_type TEXT,
            status TEXT,
            created_at TEXT,
            extracted_data TEXT,
            validation_results TEXT,
            inconsistencies TEXT,
            missing_documents TEXT,
            documents_received TEXT,
            required_action TEXT,
            raw_documents TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def append_error(errors: list[str], message: str) -> None:
    if message and message not in errors:
        errors.append(message)


def save_application(application: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO applications (
            id, name, dob, address, phone, pass_type, status, created_at,
            extracted_data, validation_results, inconsistencies, missing_documents,
            documents_received, required_action, raw_documents
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            application["id"],
            application["name"],
            application["dob"],
            application["address"],
            application["phone"],
            application["pass_type"],
            application["status"],
            application["created_at"],
            json.dumps(application["extracted_data"]),
            json.dumps(application["validation_results"]),
            json.dumps(application["inconsistencies"]),
            json.dumps(application["missing_documents"]),
            json.dumps(application["documents_received"]),
            application["required_action"],
            json.dumps(application["raw_documents"]),
        ),
    )
    conn.commit()
    conn.close()


def fetch_history() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM applications ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def normalize_name(value: str) -> str:
    return normalize_text(value).replace(" ", "")


def compare_string_values(app_value: str, doc_value: str) -> bool:
    app_norm = normalize_name(app_value)
    doc_norm = normalize_name(doc_value)
    if not app_norm or not doc_norm:
        return True
    if app_norm == doc_norm:
        return True
    if app_norm in doc_norm or doc_norm in app_norm:
        return True
    return False


def verify_application(form_data: dict, uploaded_docs: dict[str, Path]) -> dict:
    validation_results: list[str] = []
    inconsistencies: list[str] = []
    missing_documents: list[str] = []
    documents_received: list[str] = []
    extracted_data: dict[str, str] = {
        "name": "",
        "dob": "",
        "address": "",
        "phone": "",
        "pass_type": "",
    }

    for key in REQUIRED_DOCS:
        if uploaded_docs.get(key):
            documents_received.append(key)
        else:
            missing_documents.append(key)

    for field in REQUIRED_FIELDS:
        if not form_data.get(field, "").strip():
            validation_results.append(f"Missing required field: {field}")

    for doc_key, file_path in uploaded_docs.items():
        if not file_path or not file_path.exists():
            continue
        extracted_text = extract_text_from_file(file_path)
        if not extracted_text.strip():
            inconsistencies.append(f"Document unreadable or not recognized: {doc_key}")
            continue
        extracted_data["name"] = extracted_data["name"] or extract_name_from_text(extracted_text)
        extracted_data["dob"] = extracted_data["dob"] or extract_dob_from_text(extracted_text)
        extracted_data["address"] = extracted_data["address"] or extract_address_from_text(extracted_text)
        extracted_data["phone"] = extracted_data["phone"] or extract_phone_from_text(extracted_text)
        extracted_data["pass_type"] = extracted_data["pass_type"] or extract_pass_type_from_text(extracted_text)

    # field-level consistency checks
    if form_data.get("name") and extracted_data.get("name"):
        if not compare_string_values(form_data["name"], extracted_data["name"]):
            inconsistencies.append("Name mismatch detected between application and uploaded document.")

    if form_data.get("dob") and extracted_data.get("dob"):
        if normalize_text(form_data["dob"]) != normalize_text(extracted_data["dob"]):
            inconsistencies.append("Date of birth mismatch detected between application and uploaded document.")

    if form_data.get("address") and extracted_data.get("address"):
        if normalize_text(form_data["address"]) not in normalize_text(extracted_data["address"]) and normalize_text(extracted_data["address"]) not in normalize_text(form_data["address"]):
            inconsistencies.append("Address mismatch detected between application and uploaded document.")

    if form_data.get("phone") and extracted_data.get("phone"):
        if normalize_text(form_data["phone"]) not in normalize_text(extracted_data["phone"]) and normalize_text(extracted_data["phone"]) not in normalize_text(form_data["phone"]):
            inconsistencies.append("Phone number mismatch detected between application and uploaded document.")

    if form_data.get("pass_type") and extracted_data.get("pass_type"):
        if normalize_text(form_data["pass_type"]) != normalize_text(extracted_data["pass_type"]):
            inconsistencies.append("Pass type inconsistency detected between application and uploaded document.")

    if any(doc_key in uploaded_docs and uploaded_docs[doc_key] for doc_key in REQUIRED_DOCS):
        validation_results.append("Required documents available for review.")

    if inconsistencies:
        status = "NEEDS_CORRECTION"
    elif (missing_documents or any(msg.startswith("Missing required field") for msg in validation_results)):
        status = "NEEDS_CORRECTION"
    elif any("Document unreadable" in issue for issue in inconsistencies):
        status = "MANUAL_REVIEW"
    else:
        status = "COMPLETE"

    if status == "COMPLETE":
        required_action = "No correction required. Application is ready for processing."
    elif status == "MANUAL_REVIEW":
        required_action = "Please upload clearer documents or resubmit for manual review."
    else:
        required_action = "Please fix the listed missing information or mismatches and resubmit."

    application_record = {
        "id": str(uuid.uuid4())[:8].upper(),
        "name": form_data.get("name", ""),
        "dob": form_data.get("dob", ""),
        "address": form_data.get("address", ""),
        "phone": form_data.get("phone", ""),
        "pass_type": form_data.get("pass_type", ""),
        "status": status,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "extracted_data": extracted_data,
        "validation_results": validation_results,
        "inconsistencies": inconsistencies,
        "missing_documents": missing_documents,
        "documents_received": documents_received,
        "required_action": required_action,
        "raw_documents": sorted(uploaded_docs.keys()),
    }

    if status == "MANUAL_REVIEW":
        application_record["status"] = "MANUAL_REVIEW"

    save_application(application_record)
    return application_record


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/applications")
def list_applications():
    return {"results": fetch_history()}


@app.post("/api/applications/verify")
async def verify_application_endpoint(
    name: str = Form(""),
    dob: str = Form(""),
    address: str = Form(""),
    phone: str = Form(""),
    pass_type: str = Form(""),
    id_proof: UploadFile | None = File(None),
    address_proof: UploadFile | None = File(None),
    photograph: UploadFile | None = File(None),
    other_document: UploadFile | None = File(None),
):
    form_data = {
        "name": name,
        "dob": dob,
        "address": address,
        "phone": phone,
        "pass_type": pass_type,
    }

    uploaded_docs: dict[str, Path] = {}
    for label, file in {
        "id_proof": id_proof,
        "address_proof": address_proof,
        "photograph": photograph,
        "other_document": other_document,
    }.items():
        if not file:
            continue
        file_extension = Path(file.filename or "file").suffix.lower()
        if file_extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file type for {label}: {file.filename}")
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename or 'document'}"
        contents = await file.read()
        file_path.write_bytes(contents)
        uploaded_docs[label] = file_path

    result = verify_application(form_data, uploaded_docs)
    return result


@app.get("/")
def root():
    return {"message": "Smart Application Verification API is running"}
