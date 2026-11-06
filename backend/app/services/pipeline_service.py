"""Lightweight durable handoff queue for document processing.

The extraction worker can consume these JSONL records and dispatch them to the
Claritax detection/OCR/extraction pipeline. Queue path is configurable through
CLARITAX_PIPELINE_QUEUE_PATH; default is storage/processing_queue.jsonl.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from app.services.ocr_service import PaddleOCRService
from app.schemas.ocr_schema import FormattedOCROutput

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def enqueue_document(
    *, document_id: str, file_path: str, original_filename: str, content_type: str
) -> dict:
    queue_path = Path(os.getenv("CLARITAX_PIPELINE_QUEUE_PATH", "storage/processing_queue.jsonl"))
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "document_id": document_id,
        "file_path": str(Path(file_path).resolve()),
        "original_filename": original_filename,
        "content_type": content_type,
        "status": "queued",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    # Append one complete JSON record per line for simple worker consumption.
    with queue_path.open("a", encoding="utf-8") as queue_file:
        queue_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
def process_single_queued_document(record: dict) -> Optional[FormattedOCROutput]:
    """Runs PaddleOCR on a single queued image and saves the formatted JSON result."""
    file_path = record["file_path"]
    ext = Path(file_path).suffix.lower()

    if ext not in IMAGE_EXTENSIONS:
        return None

    ocr_service = PaddleOCRService.get_instance()
    formatted_result = ocr_service.extract_text(
        file_path=file_path,
        document_id=record["document_id"],
        original_filename=record["original_filename"],
    )

    # Save formatted JSON to storage/ocr_results/<document_id>.json
    results_dir = Path("storage/ocr_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    output_file = results_dir / f"{record['document_id']}.json"

    with output_file.open("w", encoding="utf-8") as f:
        f.write(formatted_result.model_dump_json(indent=2))

    return formatted_result


def process_all_queued_documents() -> List[FormattedOCROutput]:
    """
    Consumes all pending records from storage/processing_queue.jsonl,
    extracts text from images, and updates their status in the queue file.
    """
    queue_path = Path(
        os.getenv("CLARITAX_PIPELINE_QUEUE_PATH", "storage/processing_queue.jsonl")
    )
    if not queue_path.exists():
        return []

    lines = queue_path.read_text(encoding="utf-8").splitlines()
    updated_records = []
    ocr_results: List[FormattedOCROutput] = []

    for line in lines:
        if not line.strip():
            continue

        record = json.loads(line)

        # Only process items that are queued
        if record.get("status") == "queued":
            try:
                res = process_single_queued_document(record)
                if res:
                    ocr_results.append(res)
                    record["status"] = "ocr_completed"
                    record["average_confidence"] = res.average_confidence
                    record["needs_human_review"] = res.needs_human_review
                else:
                    record["status"] = "skipped_non_image"
            except Exception as e:
                record["status"] = "ocr_failed"
                record["error"] = str(e)

            record["processed_at"] = datetime.now(timezone.utc).isoformat()

        updated_records.append(record)

    # Update queue file with the new statuses
    with queue_path.open("w", encoding="utf-8") as f:
        for rec in updated_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return ocr_results