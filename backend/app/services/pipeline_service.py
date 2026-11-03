"""Lightweight durable handoff queue for document processing.

The extraction worker can consume these JSONL records and dispatch them to the
Claritax detection/OCR/extraction pipeline. Queue path is configurable through
CLARITAX_PIPELINE_QUEUE_PATH; default is storage/processing_queue.jsonl.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone


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
