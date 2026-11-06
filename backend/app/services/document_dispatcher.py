from pathlib import Path

from app.services.pdf_classifier import detect_pdf_type


def dispatch_document(document_record: dict) -> dict:
    document_id = document_record.get("document_id")
    filename = document_record.get("original_filename", "unknown.pdf")
    file_path = Path(document_record.get("file_path", ""))

    if not document_id:
        return {
            "status": "failed",
            "reason": "Missing document_id"
        }

    if not file_path.is_file():
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "failed",
            "reason": f"Uploaded PDF not found: {file_path}"
        }

    detection = detect_pdf_type(str(file_path))

    if detection["pdf_type"] in {
        "PASSWORD_PROTECTED",
        "INVALID_PDF"
    }:
        return {
            "document_id": document_id,
            "filename": filename,
            "pdf_type": detection["pdf_type"],
            "status": "review_required",
            "reason": detection.get("reason", "PDF cannot be processed"),
            "page_tasks": []
        }

    page_tasks = []

    for page in detection["pages"]:
        if page["type"] == "DIGITAL":
            processor = "PERSON_2_TEXT_EXTRACTION"

        elif page["type"] == "SCANNED":
            processor = "PERSON_1_OCR"

        else:
            processor = "MANUAL_REVIEW"

        page_tasks.append({
            "page_number": page["page"],
            "page_type": page["type"],
            "processor": processor,
            "text_length": page["text_length"],
            "image_count": page["image_count"]
        })

    has_manual_review = any(
        task["processor"] == "MANUAL_REVIEW"
        for task in page_tasks
    )

    return {
        "document_id": document_id,
        "filename": filename,
        "file_path": str(file_path.resolve()),
        "pdf_type": detection["pdf_type"],
        "page_count": len(page_tasks),
        "page_tasks": page_tasks,
        "status": (
            "review_required"
            if has_manual_review
            else "ready_for_processing"
        )
    }