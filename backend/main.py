from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "applications.db"
UPLOAD_DIR = BASE_DIR / "uploaded_documents"
DB_PATH.parent.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

OCR_ENGINE = RapidOCR()

DOCUMENT_DEFINITIONS = {
    "identity_proof": {
        "keywords": ["aadhaar", "aadhar", "identity card", "passport", "government id", "id proof", "identity proof", "uid", "driving license", "voter id"],
    },
    "student_id": {
        "keywords": ["student id", "roll number", "enrollment number", "college id", "student identity", "student no", "bonafide"],
    },
    "bonafide_certificate": {
        "keywords": ["bonafide", "bonafide certificate", "student of", "certified that", "college certificate"],
    },
    "marksheet": {
        "keywords": ["marksheet", "mark sheet", "cgpa", "sgpa", "percentage", "semester", "grade point average", "grade card", "exam result"],
    },
    "income_certificate": {
        "keywords": ["annual family income", "family income", "income certificate", "salary certificate", "net annual income", "monthly income", "income declaration"],
    },
    "address_proof": {
        "keywords": ["address proof", "residence", "utility bill", "house no", "flat no", "village", "district", "state", "domicile"],
    },
    "domicile_certificate": {
        "keywords": ["domicile", "domicile certificate", "residence certificate", "district", "state", "local address"],
    },
    "bank_proof": {
        "keywords": ["bank", "account number", "ifsc", "passbook", "bank statement", "branch", "bank account"],
    },
    "category_certificate": {
        "keywords": ["caste", "category certificate", "reservation", "community", "minority", "caste certificate"],
    },
    "photograph": {
        "keywords": ["passport photo", "photograph", "student photo", "recent photo", "passport size"],
    },
    "student_employment_proof": {
        "keywords": ["employment", "student employment", "id card", "employee", "work certificate", "company"],
    },
    "supporting_eligibility_document": {
        "keywords": ["eligibility", "supporting evidence", "verification", "supporting document", "certificate"],
    },
    "transfer_certificate": {
        "keywords": ["transfer certificate", "leaving certificate", "school leaving certificate", "tc"],
    },
    "admission_certificate": {
        "keywords": ["admission letter", "seat allotment", "student certificate", "admission certificate", "admission proof"],
    },
    "category_domicile_certificate": {
        "keywords": ["category certificate", "domicile certificate", "community certificate", "resident proof", "locality"],
    },
}

APPLICATION_TYPE_CONFIG = {
    "scholarship": {
        "required_documents": [
            "identity_proof",
            "student_id",
            "marksheet",
            "income_certificate",
            "address_proof",
            "bank_proof",
        ],
        "required_fields": [
            "applicant_name",
            "date_of_birth",
            "email",
            "phone",
            "address",
            "institution",
            "course",
            "academic_year",
            "scholarship_type",
            "annual_income",
            "academic_score",
        ],
    },
    "transport_pass": {
        "required_documents": [
            "identity_proof",
            "address_proof",
            "student_employment_proof",
            "photograph",
        ],
        "required_fields": [
            "applicant_name",
            "date_of_birth",
            "phone",
            "address",
            "pass_type",
        ],
    },
    "college_admission": {
        "required_documents": [
            "identity_proof",
            "marksheet",
            "transfer_certificate",
            "admission_certificate",
            "photograph",
        ],
        "required_fields": [
            "applicant_name",
            "date_of_birth",
            "email",
            "phone",
            "institution",
            "course",
            "academic_year",
        ],
    },
}

DEFAULT_REQUIRED_FIELDS = [
    "applicant_name",
    "date_of_birth",
    "email",
    "phone",
    "address",
    "institution",
    "course",
    "academic_year",
    "scholarship_type",
]


def get_application_type_config(application_type: str | None) -> dict[str, Any]:
    normalized = (application_type or "scholarship").strip().lower()
    return APPLICATION_TYPE_CONFIG.get(normalized, APPLICATION_TYPE_CONFIG["scholarship"])

app = FastAPI(title="ScholarVerify API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s/.-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_name(value: str | None) -> str:
    return normalize_text(value).replace(" ", "")


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", value)
    try:
        return float(cleaned)
    except ValueError:
        return None


def mask_value(value: str | None, keep_last: int = 4) -> str:
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)
    if len(digits) <= keep_last:
        return value
    masked = "X" * (len(digits) - keep_last) + digits[-keep_last:]
    return masked


def safe_read_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        pages = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            pages.append(extracted)
        return "\n".join(pages)
    except Exception:
        return ""


def extract_text_from_file(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        text = safe_read_pdf(file_path)
        if text.strip():
            return text
    try:
        result, _ = OCR_ENGINE(str(file_path))
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


def detect_document_type(raw_text: str, file_name: str) -> dict[str, Any]:
    text = normalize_text(raw_text)
    file_name_l = file_name.lower()
    scores: dict[str, int] = {doc_type: 0 for doc_type in DOCUMENT_DEFINITIONS}
    scores["unknown"] = 0
    for doc_type, config in DOCUMENT_DEFINITIONS.items():
        for keyword in config["keywords"]:
            if keyword in text:
                scores[doc_type] += 2
        if doc_type.replace("_", " ") in file_name_l:
            scores[doc_type] += 3
    for doc_type, score in scores.items():
        if doc_type == "unknown":
            continue
        if score > 0:
            scores[doc_type] += 1
    best_doc = max(scores, key=scores.get)
    best_score = scores[best_doc]
    if best_score <= 0:
        return {"document_type": "unknown", "confidence": 0.22}
    confidence = min(0.99, 0.45 + (best_score * 0.12))
    return {"document_type": best_doc, "confidence": round(confidence, 2)}


def extract_name_from_text(text: str) -> str:
    patterns = [
        r"name\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]+)",
        r"applicant\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]+)",
        r"student\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_dob_from_text(text: str) -> str:
    for pattern in [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    ]:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def extract_email_from_text(text: str) -> str:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if match:
        return match.group(0)
    return ""


def extract_phone_from_text(text: str) -> str:
    match = re.search(r"\+?\d{10,12}", text)
    if match:
        return match.group(0)
    return ""


def extract_address_from_text(text: str) -> str:
    pattern = r"^\s*address(?:\s+proof)?(?:\s*[:\-]\s*|\s+)(.+)$"
    for line in text.splitlines():
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match and match.group(1).strip().lower() not in {"proof", "proof of address", "domicile proof"}:
            return match.group(1).strip()[:200]
    return ""


def extract_institution_from_text(text: str) -> str:
    patterns = [
        r"institution\s*[:\-]?\s*([A-Za-z0-9 .,'-]+)",
        r"college\s*[:\-]?\s*([A-Za-z0-9 .,'-]+)",
        r"university\s*[:\-]?\s*([A-Za-z0-9 .,'-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_course_from_text(text: str) -> str:
    for keyword in ["computer science", "mechanical", "electronics", "civil", "btech", "b.tech", "mba", "mtech", "bca", "mca", "bsc", "msc"]:
        if keyword.lower() in text.lower():
            return keyword.title()
    return ""


def extract_academic_year_from_text(text: str) -> str:
    match = re.search(r"(?:202[0-9]|20[0-9][0-9])", text)
    if match:
        return match.group(0)
    return ""


def extract_annual_income_from_text(text: str) -> str:
    patterns = [
        r"annual\s*income\s*[:\-]?\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)",
        r"family\s*income\s*[:\-]?\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)",
        r"income\s*[:\-]?\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
    return ""


def extract_percentage_from_text(text: str) -> str:
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%", text)
    if match:
        return match.group(1) + "%"
    match = re.search(r"cgpa\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def extract_bank_name_from_text(text: str) -> str:
    match = re.search(r"bank\s*[:\-]?\s*([A-Za-z0-9 .,'-]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_ifsc_from_text(text: str) -> str:
    match = re.search(r"IFSC\s*[:\-]?\s*([A-Z0-9]{11})", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def extract_document_fields(doc_type: str, text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    if doc_type in {"identity_proof", "address_proof", "domicile_certificate"}:
        name = extract_name_from_text(text)
        if name:
            data["name"] = name
        dob = extract_dob_from_text(text)
        if dob:
            data["dob"] = dob
        address = extract_address_from_text(text)
        if address:
            data["address"] = address
    if doc_type == "student_id":
        name = extract_name_from_text(text)
        institution = extract_institution_from_text(text)
        course = extract_course_from_text(text)
        if name:
            data["name"] = name
        if institution:
            data["institution"] = institution
        if course:
            data["course"] = course
    if doc_type == "bonafide_certificate":
        name = extract_name_from_text(text)
        institution = extract_institution_from_text(text)
        course = extract_course_from_text(text)
        year = extract_academic_year_from_text(text)
        if name:
            data["name"] = name
        if institution:
            data["institution"] = institution
        if course:
            data["course"] = course
        if year:
            data["academic_year"] = year
    if doc_type == "marksheet":
        name = extract_name_from_text(text)
        institution = extract_institution_from_text(text)
        percentage = extract_percentage_from_text(text)
        year = extract_academic_year_from_text(text)
        if name:
            data["name"] = name
        if institution:
            data["institution"] = institution
        if percentage:
            data["percentage"] = percentage
        if year:
            data["academic_year"] = year
    if doc_type == "income_certificate":
        name = extract_name_from_text(text)
        income = extract_annual_income_from_text(text)
        if name:
            data["name"] = name
        if income:
            data["annual_income"] = income
    if doc_type == "bank_proof":
        name = extract_name_from_text(text)
        bank_name = extract_bank_name_from_text(text)
        ifsc = extract_ifsc_from_text(text)
        if name:
            data["name"] = name
        if bank_name:
            data["bank_name"] = bank_name
        if ifsc:
            data["ifsc"] = ifsc
    if doc_type == "category_certificate":
        name = extract_name_from_text(text)
        if name:
            data["name"] = name
    if not data:
        data["raw_text_summary"] = text[:150]
    return data


def compare_field(app_value: str | None, doc_value: str | None, field_name: str) -> str | None:
    if not app_value or not doc_value:
        return None
    if normalize_name(app_value) == normalize_name(doc_value):
        return None
    if normalize_name(app_value) in normalize_name(doc_value) or normalize_name(doc_value) in normalize_name(app_value):
        return None
    return f"{field_name} does not match the uploaded document."


def is_acceptable_document_match(doc_type: str, required_doc_key: str) -> bool:
    if not doc_type or doc_type == "unknown":
        return False
    if required_doc_key == doc_type:
        return True
    if doc_type in {"identity_proof", "address_proof", "domicile_certificate"} and required_doc_key in {"identity_proof", "address_proof", "domicile_certificate"}:
        return True
    if doc_type in {"student_id", "bonafide_certificate"} and required_doc_key in {"student_id", "bonafide_certificate"}:
        return True
    return False


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            application_type TEXT,
            applicant_name TEXT,
            date_of_birth TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            institution TEXT,
            course TEXT,
            academic_year TEXT,
            scholarship_type TEXT,
            scholarship_category TEXT,
            annual_income TEXT,
            academic_score TEXT,
            status TEXT,
            overall_status TEXT,
            created_at TEXT,
            extracted_information TEXT,
            validation_results TEXT,
            issues TEXT,
            recommended_actions TEXT,
            missing_documents TEXT,
            detected_documents TEXT,
            documents_received TEXT,
            raw_documents TEXT,
            document_count INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS application_documents (
            id TEXT PRIMARY KEY,
            application_id TEXT,
            key_name TEXT,
            file_name TEXT,
            detected_document_type TEXT,
            confidence REAL,
            status TEXT,
            extracted_fields TEXT,
            created_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS application_sequences (
            year INTEGER PRIMARY KEY,
            next_number INTEGER NOT NULL
        )
        """
    )

    existing_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(applications)").fetchall()
    }
    expected_columns = {
        "application_type": "TEXT",
        "applicant_name": "TEXT",
        "date_of_birth": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "address": "TEXT",
        "institution": "TEXT",
        "course": "TEXT",
        "academic_year": "TEXT",
        "scholarship_type": "TEXT",
        "scholarship_category": "TEXT",
        "annual_income": "TEXT",
        "academic_score": "TEXT",
        "status": "TEXT",
        "overall_status": "TEXT",
        "created_at": "TEXT",
        "extracted_information": "TEXT",
        "validation_results": "TEXT",
        "issues": "TEXT",
        "recommended_actions": "TEXT",
        "missing_documents": "TEXT",
        "detected_documents": "TEXT",
        "documents_received": "TEXT",
        "raw_documents": "TEXT",
        "document_count": "INTEGER",
        "review_decision": "TEXT",
        "reviewed_at": "TEXT",
        "review_note": "TEXT",
    }
    for column_name, column_type in expected_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE applications ADD COLUMN {column_name} {column_type}")
    conn.commit()
    conn.close()


init_db()


def generate_application_id() -> str:
    year = datetime.utcnow().year
    prefix = f"APP-{year}-"
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing_ids = conn.execute(
            "SELECT id FROM applications WHERE id LIKE ?",
            (f"{prefix}%",),
        ).fetchall()
        existing_numbers = [
            int(row[0][len(prefix):])
            for row in existing_ids
            if re.fullmatch(rf"APP-{year}-\d+", row[0])
        ]
        sequence = conn.execute(
            "SELECT next_number FROM application_sequences WHERE year = ?",
            (year,),
        ).fetchone()
        number = max(max(existing_numbers, default=0) + 1, sequence[0] if sequence else 1)
        conn.execute(
            """
            INSERT INTO application_sequences (year, next_number) VALUES (?, ?)
            ON CONFLICT(year) DO UPDATE SET next_number = excluded.next_number
            """,
            (year, number + 1),
        )
        conn.commit()
        return f"{prefix}{number:05d}"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_application_record(report: dict[str, Any]) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO applications (
            id, application_type, applicant_name, date_of_birth, email, phone, address, institution,
            course, academic_year, scholarship_type, scholarship_category, annual_income,
            academic_score, status, overall_status, created_at, extracted_information,
            validation_results, issues, recommended_actions, missing_documents,
            detected_documents, documents_received, raw_documents, document_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report["application_id"],
            report.get("application_type", "scholarship"),
            report.get("applicant_name", ""),
            report.get("date_of_birth", ""),
            report.get("email", ""),
            report.get("phone", ""),
            report.get("address", ""),
            report.get("institution", ""),
            report.get("course", ""),
            report.get("academic_year", ""),
            report.get("scholarship_type", ""),
            report.get("scholarship_category", ""),
            report.get("annual_income", ""),
            report.get("academic_score", ""),
            report.get("status", "NEEDS_CORRECTION"),
            report.get("overall_status", report.get("status", "NEEDS_CORRECTION")),
            report["created_at"],
            json.dumps(report.get("extracted_information", {})),
            json.dumps(report.get("validation_results", [])),
            json.dumps(report.get("issues", [])),
            json.dumps(report.get("recommended_actions", [])),
            json.dumps(report.get("missing_documents", [])),
            json.dumps(report.get("detected_documents", [])),
            json.dumps(report.get("documents_received", [])),
            json.dumps(report.get("raw_documents", [])),
            len(report.get("detected_documents", [])),
        ),
    )
    for doc in report.get("documents", []):
        conn.execute(
            """
            INSERT INTO application_documents (
                id, application_id, key_name, file_name, detected_document_type,
                confidence, status, extracted_fields, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4())[:8],
                report["application_id"],
                doc.get("key_name", "unknown"),
                doc.get("file_name", ""),
                doc.get("detected_document_type", "unknown"),
                doc.get("confidence", 0.0),
                doc.get("status", "unknown"),
                json.dumps(doc.get("extracted_fields", {})),
                report["created_at"],
            ),
        )
    conn.commit()
    conn.close()


def get_application_by_id(application_id: str) -> dict[str, Any] | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    data = dict(row)
    data["extracted_information"] = json.loads(data.get("extracted_information") or "{}")
    data["validation_results"] = json.loads(data.get("validation_results") or "[]")
    data["issues"] = json.loads(data.get("issues") or "[]")
    data["recommended_actions"] = json.loads(data.get("recommended_actions") or "[]")
    data["missing_documents"] = json.loads(data.get("missing_documents") or "[]")
    data["detected_documents"] = json.loads(data.get("detected_documents") or "[]")
    data["documents_received"] = json.loads(data.get("documents_received") or "[]")
    data["raw_documents"] = json.loads(data.get("raw_documents") or "[]")
    return data


def fetch_history() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM applications ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    result = []
    for row in rows:
        data = dict(row)
        data["extracted_information"] = json.loads(data.get("extracted_information") or "{}")
        data["issues"] = json.loads(data.get("issues") or "[]")
        data["validation_results"] = json.loads(data.get("validation_results") or "[]")
        data["missing_documents"] = json.loads(data.get("missing_documents") or "[]")
        data["detected_documents"] = json.loads(data.get("detected_documents") or "[]")
        result.append(data)
    return result


def ensure_required_doc(name: str | None) -> str:
    return name.strip() if name else ""


def process_application(form_data: dict[str, Any], uploaded_docs: dict[str, Path]) -> dict[str, Any]:
    application_type = str(form_data.get("application_type") or "scholarship").strip().lower()
    config = get_application_type_config(application_type)
    required_documents = config.get("required_documents", [])
    required_fields = config.get("required_fields", DEFAULT_REQUIRED_FIELDS)

    validation_results: list[str] = []
    issues: list[str] = []
    recommended_actions: list[str] = []
    detected_documents: list[dict[str, Any]] = []
    documents_received: list[str] = []
    missing_documents: list[str] = []
    extracted_information: dict[str, Any] = {}
    fulfilled_required_documents: set[str] = set()

    for field in required_fields:
        value = str(form_data.get(field, "") or "").strip()
        if not value:
            validation_results.append(f"Missing required field: {field}")
        else:
            extracted_information[field] = value

    for doc_key, file_path in uploaded_docs.items():
        if not file_path or not file_path.exists():
            continue
        text = extract_text_from_file(file_path)
        if not text.strip():
            detected_documents.append(
                {
                    "key_name": doc_key,
                    "file_name": file_path.name,
                    "detected_document_type": "unknown",
                    "confidence": 0.0,
                    "status": "MANUAL_REVIEW",
                    "extracted_fields": {},
                    "reason": "OCR could not reliably read the uploaded document.",
                }
            )
            issues.append(f"Document could not be read reliably: {doc_key.replace('_', ' ')}.")
            recommended_actions.append("Upload a clearer scan or a different document.")
            continue

        detection = detect_document_type(text, file_path.name)
        doc_type = detection["document_type"]
        confidence = detection["confidence"]
        extracted_fields = extract_document_fields(doc_type, text)

        acceptable_required_keys = [
            required_key for required_key in required_documents if is_acceptable_document_match(doc_type, required_key)
        ]
        if not acceptable_required_keys and doc_key in required_documents:
            acceptable_required_keys = [doc_key]

        if acceptable_required_keys:
            fulfilled_required_documents.update(acceptable_required_keys)

        if doc_key in required_documents and (doc_type == "unknown" or confidence < 0.55):
            if not acceptable_required_keys:
                status = "MANUAL_REVIEW"
                issues.append(f"Document type could not be confidently identified for {doc_key.replace('_', ' ')}.")
                recommended_actions.append("Upload a clearer document or a valid supporting document.")
            else:
                status = "VALID"
        elif doc_key in required_documents and not acceptable_required_keys:
            status = "WRONG_DOCUMENT"
            issues.append(f"Uploaded file for {doc_key.replace('_', ' ')} matches {doc_type.replace('_', ' ')} instead of the expected document type.")
            recommended_actions.append(f"Upload the correct {doc_key.replace('_', ' ')} document.")
        else:
            status = "VALID"

        doc_entry = {
            "key_name": doc_key,
            "file_name": file_path.name,
            "detected_document_type": doc_type,
            "confidence": confidence,
            "status": status,
            "extracted_fields": extracted_fields,
            "reason": "" if status == "VALID" else "Low OCR confidence or unrecognized document type.",
        }
        extracted_information.update({f"{doc_key}_extracted": extracted_fields})
        detected_documents.append(doc_entry)

    for doc_key in required_documents:
        if doc_key in fulfilled_required_documents:
            documents_received.append(doc_key)
        else:
            missing_documents.append(doc_key)
            issues.append(f"{doc_key.replace('_', ' ').title()} is missing.")
            recommended_actions.append(f"Upload the missing {doc_key.replace('_', ' ')} document.")

    applicant_name = str(form_data.get("applicant_name", "") or "")
    if applicant_name:
        for doc in detected_documents:
            name_value = doc.get("extracted_fields", {}).get("name")
            if name_value and normalize_name(applicant_name) != normalize_name(name_value):
                issues.append(f"Applicant name does not match the uploaded {doc['key_name'].replace('_', ' ')}.")
                recommended_actions.append("Correct the applicant name or upload the matching identity document.")
                break

    dob = str(form_data.get("date_of_birth", "") or "")
    for doc in detected_documents:
        dob_value = doc.get("extracted_fields", {}).get("dob")
        if dob and dob_value and normalize_text(dob) != normalize_text(dob_value):
            issues.append("Date of birth does not match the uploaded document.")
            recommended_actions.append("Verify the date of birth and upload a matching document.")
            break

    institution = str(form_data.get("institution", "") or "")
    for doc in detected_documents:
        institution_value = doc.get("extracted_fields", {}).get("institution")
        normalized_institution = normalize_text(institution)
        normalized_document_institution = normalize_text(institution_value)
        if institution and institution_value and normalized_institution not in normalized_document_institution and normalized_document_institution not in normalized_institution:
            issues.append("Institution does not match the uploaded academic document.")
            recommended_actions.append("Update the institution field or upload the correct student certificate.")
            break

    course = str(form_data.get("course", "") or "")
    for doc in detected_documents:
        course_value = doc.get("extracted_fields", {}).get("course")
        normalized_course = normalize_text(course)
        normalized_document_course = normalize_text(course_value)
        if course and course_value and normalized_course not in normalized_document_course and normalized_document_course not in normalized_course:
            issues.append("Course does not match the uploaded document.")
            recommended_actions.append("Verify the course value and upload the matching certificate.")
            break

    address = str(form_data.get("address", "") or "")
    for doc in detected_documents:
        address_value = doc.get("extracted_fields", {}).get("address")
        normalized_address = normalize_text(address)
        normalized_document_address = normalize_text(address_value)
        if address and address_value and normalized_address not in normalized_document_address and normalized_document_address not in normalized_address:
            issues.append(f"Address does not match the uploaded {doc['key_name'].replace('_', ' ')}.")
            recommended_actions.append("Verify the address and upload a matching identity or residence document.")
            break

    annual_income = str(form_data.get("annual_income", "") or "")
    for doc in detected_documents:
        income_value = doc.get("extracted_fields", {}).get("annual_income")
        if annual_income and income_value and safe_float(annual_income) and safe_float(income_value) and safe_float(annual_income) != safe_float(income_value):
            issues.append("Annual income differs from the income certificate.")
            recommended_actions.append("Recheck the annual income and upload a valid income certificate.")
            break

    academic_score = str(form_data.get("academic_score", "") or "")
    for doc in detected_documents:
        score_value = doc.get("extracted_fields", {}).get("percentage")
        if academic_score and score_value and safe_float(academic_score) is not None and safe_float(score_value) is not None and safe_float(academic_score) != safe_float(score_value):
            issues.append("Academic score differs from the uploaded marksheet.")
            recommended_actions.append("Verify the academic score and upload a matching marksheet.")
            break

    if not issues and not validation_results and not missing_documents:
        status = "COMPLETE"
    elif any("could not be read reliably" in issue.lower() or "could not be confidently identified" in issue.lower() for issue in issues):
        status = "MANUAL_REVIEW"
    elif issues or validation_results or missing_documents:
        status = "NEEDS_CORRECTION"
    else:
        status = "COMPLETE"

    if status == "COMPLETE":
        recommended_actions = ["No correction required. Application is ready for review."]
    elif not recommended_actions:
        recommended_actions = ["Please review the highlighted issues and resubmit a corrected application."]

    report = {
        "application_id": str(uuid.uuid4())[:8].upper(),
        "application_type": application_type,
        "overall_status": status,
        "status": status,
        "applicant_name": form_data.get("applicant_name", ""),
        "applicant": {"name": form_data.get("applicant_name", "")},
        "date_of_birth": form_data.get("date_of_birth", ""),
        "email": form_data.get("email", ""),
        "phone": form_data.get("phone", ""),
        "address": form_data.get("address", ""),
        "institution": form_data.get("institution", ""),
        "course": form_data.get("course", ""),
        "academic_year": form_data.get("academic_year", ""),
        "scholarship_type": form_data.get("scholarship_type", ""),
        "scholarship_category": form_data.get("scholarship_category", ""),
        "annual_income": form_data.get("annual_income", ""),
        "academic_score": form_data.get("academic_score", ""),
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "documents": [
            {
                "key_name": doc["key_name"],
                "file_name": doc["file_name"],
                "detected_document_type": doc["detected_document_type"],
                "confidence": doc["confidence"],
                "status": doc["status"],
                "extracted_fields": doc["extracted_fields"],
                "reason": doc.get("reason", ""),
            }
            for doc in detected_documents
        ],
        "detected_documents": detected_documents,
        "documents_received": documents_received,
        "missing_documents": missing_documents,
        "issues": issues,
        "recommended_actions": recommended_actions,
        "validation_results": validation_results,
        "extracted_information": extracted_information,
        "raw_documents": sorted(uploaded_docs.keys()),
    }
    return report


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ScholarVerify API is running"}


@app.get("/api/applications")
def list_applications() -> dict[str, Any]:
    return {"results": fetch_history()}


@app.get("/api/applications/{application_id}")
def get_application(application_id: str) -> dict[str, Any]:
    record = get_application_by_id(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return record


@app.delete("/api/applications/{application_id}")
def delete_application(application_id: str) -> dict[str, str]:
    record = get_application_by_id(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Application not found")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM application_documents WHERE application_id = ?", (application_id,))
        conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        conn.commit()
    finally:
        conn.close()

    return {"status": "deleted", "application_id": application_id}


@app.post("/api/applications/{application_id}/review")
def review_application(application_id: str, action: str = Form(...)) -> dict[str, Any]:
    record = get_application_by_id(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if str(record.get("status") or record.get("overall_status") or "").upper() != "MANUAL_REVIEW":
        raise HTTPException(status_code=409, detail="Application is not awaiting manual review")

    normalized_action = action.strip().lower()
    if normalized_action == "verified":
        status = "COMPLETE"
        review_note = "Application marked as verified by a reviewer."
        recommended_actions = ["No correction required. Reviewer verified this application."]
    elif normalized_action == "correction":
        status = "NEEDS_CORRECTION"
        review_note = "Correction requested. Please upload a clearer document for review."
        existing_actions = record.get("recommended_actions") or []
        if not isinstance(existing_actions, list):
            existing_actions = []
        recommended_actions = list(dict.fromkeys([
            *existing_actions,
            "Upload a clearer document and resubmit it for review.",
        ]))
    else:
        raise HTTPException(status_code=400, detail="Action must be verified or correction")

    reviewed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            UPDATE applications
            SET status = ?, overall_status = ?, review_decision = ?, reviewed_at = ?, review_note = ?, recommended_actions = ?
            WHERE id = ?
            """,
            (status, status, normalized_action, reviewed_at, review_note, json.dumps(recommended_actions), application_id),
        )
        conn.commit()
    finally:
        conn.close()

    updated_record = get_application_by_id(application_id)
    if updated_record is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated_record


@app.get("/api/applications/{application_id}/report")
def get_application_report(application_id: str) -> dict[str, Any]:
    record = get_application_by_id(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return {
        "application_id": record["id"],
        "applicant_name": record.get("applicant_name", ""),
        "scholarship_type": record.get("scholarship_type", ""),
        "status": record.get("status", ""),
        "documents": record.get("detected_documents", []),
        "missing_documents": record.get("missing_documents", []),
        "issues": record.get("issues", []),
        "recommended_actions": record.get("recommended_actions", []),
        "validation_results": record.get("validation_results", []),
        "extracted_information": record.get("extracted_information", {}),
    }


@app.post("/api/applications")
async def create_application(
    application_type: str = Form("scholarship"),
    applicant_name: str = Form(""),
    date_of_birth: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    institution: str = Form(""),
    course: str = Form(""),
    academic_year: str = Form(""),
    scholarship_type: str = Form(""),
    scholarship_category: str = Form(""),
    annual_income: str = Form(""),
    academic_score: str = Form(""),
    pass_type: str = Form(""),
    route: str = Form(""),
    identity_proof: UploadFile | None = File(None),
    student_id: UploadFile | None = File(None),
    bonafide_certificate: UploadFile | None = File(None),
    marksheet: UploadFile | None = File(None),
    income_certificate: UploadFile | None = File(None),
    address_proof: UploadFile | None = File(None),
    domicile_certificate: UploadFile | None = File(None),
    bank_proof: UploadFile | None = File(None),
    category_certificate: UploadFile | None = File(None),
    photograph: UploadFile | None = File(None),
    student_employment_proof: UploadFile | None = File(None),
    supporting_eligibility_document: UploadFile | None = File(None),
    transfer_certificate: UploadFile | None = File(None),
    admission_certificate: UploadFile | None = File(None),
    category_domicile_certificate: UploadFile | None = File(None),
):
    form_data = {
        "application_type": application_type,
        "applicant_name": applicant_name,
        "date_of_birth": date_of_birth,
        "email": email,
        "phone": phone,
        "address": address,
        "institution": institution,
        "course": course,
        "academic_year": academic_year,
        "scholarship_type": scholarship_type,
        "scholarship_category": scholarship_category,
        "annual_income": annual_income,
        "academic_score": academic_score,
        "pass_type": pass_type,
        "route": route,
    }

    uploaded_docs: dict[str, Path] = {}
    for label, file in {
        "identity_proof": identity_proof,
        "student_id": student_id,
        "bonafide_certificate": bonafide_certificate,
        "marksheet": marksheet,
        "income_certificate": income_certificate,
        "address_proof": address_proof,
        "domicile_certificate": domicile_certificate,
        "bank_proof": bank_proof,
        "category_certificate": category_certificate,
        "photograph": photograph,
        "student_employment_proof": student_employment_proof,
        "supporting_eligibility_document": supporting_eligibility_document,
        "transfer_certificate": transfer_certificate,
        "admission_certificate": admission_certificate,
        "category_domicile_certificate": category_domicile_certificate,
    }.items():
        if not file:
            continue
        file_name = file.filename or "uploaded_document"
        extension = Path(file_name).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file format for {label}: {file_name}")
        safe_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file_name}"
        safe_path.write_bytes(await file.read())
        uploaded_docs[label] = safe_path

    result = process_application(form_data, uploaded_docs)
    result["application_id"] = generate_application_id()
    result["created_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    save_application_record(result)
    return result


@app.post("/api/applications/verify")
async def verify_application_legacy(
    application_type: str = Form("scholarship"),
    applicant_name: str = Form(""),
    date_of_birth: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    institution: str = Form(""),
    course: str = Form(""),
    academic_year: str = Form(""),
    scholarship_type: str = Form(""),
    scholarship_category: str = Form(""),
    annual_income: str = Form(""),
    academic_score: str = Form(""),
    pass_type: str = Form(""),
    route: str = Form(""),
    identity_proof: UploadFile | None = File(None),
    student_id: UploadFile | None = File(None),
    bonafide_certificate: UploadFile | None = File(None),
    marksheet: UploadFile | None = File(None),
    income_certificate: UploadFile | None = File(None),
    address_proof: UploadFile | None = File(None),
    domicile_certificate: UploadFile | None = File(None),
    bank_proof: UploadFile | None = File(None),
    category_certificate: UploadFile | None = File(None),
    photograph: UploadFile | None = File(None),
    student_employment_proof: UploadFile | None = File(None),
    supporting_eligibility_document: UploadFile | None = File(None),
    transfer_certificate: UploadFile | None = File(None),
    admission_certificate: UploadFile | None = File(None),
    category_domicile_certificate: UploadFile | None = File(None),
):
    form_data = {
        "application_type": application_type,
        "applicant_name": applicant_name,
        "date_of_birth": date_of_birth,
        "email": email,
        "phone": phone,
        "address": address,
        "institution": institution,
        "course": course,
        "academic_year": academic_year,
        "scholarship_type": scholarship_type,
        "scholarship_category": scholarship_category,
        "annual_income": annual_income,
        "academic_score": academic_score,
        "pass_type": pass_type,
        "route": route,
    }

    uploaded_docs: dict[str, Path] = {}
    for label, file in {
        "identity_proof": identity_proof,
        "student_id": student_id,
        "bonafide_certificate": bonafide_certificate,
        "marksheet": marksheet,
        "income_certificate": income_certificate,
        "address_proof": address_proof,
        "domicile_certificate": domicile_certificate,
        "bank_proof": bank_proof,
        "category_certificate": category_certificate,
        "photograph": photograph,
        "student_employment_proof": student_employment_proof,
        "supporting_eligibility_document": supporting_eligibility_document,
        "transfer_certificate": transfer_certificate,
        "admission_certificate": admission_certificate,
        "category_domicile_certificate": category_domicile_certificate,
    }.items():
        if not file:
            continue
        file_name = file.filename or "uploaded_document"
        extension = Path(file_name).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file format for {label}: {file_name}")
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file_name}"
        file_path.write_bytes(await file.read())
        uploaded_docs[label] = file_path

    result = process_application(form_data, uploaded_docs)
    result["application_id"] = generate_application_id()
    result["created_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    save_application_record(result)
    return result


@app.post("/api/applications/{application_id}/documents")
async def add_document(application_id: str, key_name: str = Form(...), document: UploadFile = File(...)):
    if document.filename is None:
        raise HTTPException(status_code=400, detail="A file is required")
    if not get_application_by_id(application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    extension = Path(document.filename).suffix.lower()
    if extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    storage_path = UPLOAD_DIR / f"{uuid.uuid4()}_{document.filename}"
    storage_path.write_bytes(await document.read())
    text = extract_text_from_file(storage_path)
    detection = detect_document_type(text, storage_path.name)
    extracted_fields = extract_document_fields(detection["document_type"], text)
    payload = {
        "application_id": application_id,
        "key_name": key_name,
        "file_name": document.filename,
        "detected_document_type": detection["document_type"],
        "confidence": detection["confidence"],
        "status": "VALID" if detection["confidence"] >= 0.55 and detection["document_type"] != "unknown" else "MANUAL_REVIEW",
        "extracted_fields": extracted_fields,
    }
    return payload


@app.post("/api/applications/{application_id}/verify")
async def verify_application_by_id(application_id: str, document: UploadFile | None = File(None)):
    record = get_application_by_id(application_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if document is None:
        return record
    file_name = document.filename or "document"
    extension = Path(file_name).suffix.lower()
    if extension not in {".png", ".jpg", ".jpeg", ".pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file_name}"
    file_path.write_bytes(await document.read())
    text = extract_text_from_file(file_path)
    detection = detect_document_type(text, file_name)
    extracted = extract_document_fields(detection["document_type"], text)
    return {
        "application_id": application_id,
        "detected_document_type": detection["document_type"],
        "confidence": detection["confidence"],
        "status": "VALID" if detection["confidence"] >= 0.55 else "MANUAL_REVIEW",
        "extracted_fields": extracted,
    }
