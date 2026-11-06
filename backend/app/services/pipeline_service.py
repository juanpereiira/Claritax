import json
import os
from pathlib import Path
from datetime import datetime, timezone

from app.services.document_dispatcher import dispatch_document


BACKEND_DIR = Path(__file__).resolve().parents[2]


def get_queue_path() -> Path:
    configured_path = os.getenv("CLARITAX_PIPELINE_QUEUE_PATH")

    if configured_path:
        path = Path(configured_path)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        return path

    return BACKEND_DIR / "storage" / "processing_queue.jsonl"


def enqueue_document(
    *,
    document_id: str,
    file_path: str,
    original_filename: str,
    content_type: str
) -> dict:

    queue_path = get_queue_path()
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "document_id": document_id,
        "file_path": str(Path(file_path).resolve()),
        "original_filename": original_filename,
        "content_type": content_type,
        "status": "queued",
        "queued_at": datetime.now(timezone.utc).isoformat()
    }

    with queue_path.open("a", encoding="utf-8") as queue_file:
        queue_file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )

    return record


def process_queued_documents() -> list:
    """
    Read queued document records and classify/route each document.

    This function does not delete queue records or execute OCR/text extraction.
    """

    queue_path = get_queue_path()

    if not queue_path.exists():
        return []

    results = []

    with queue_path.open("r", encoding="utf-8") as queue_file:
        for line_number, line in enumerate(queue_file, start=1):

            if not line.strip():
                continue

            try:
                document_record = json.loads(line)

                if document_record.get("status") != "queued":
                    continue

                result = dispatch_document(document_record)
                results.append(result)

            except json.JSONDecodeError:
                results.append({
                    "status": "failed",
                    "reason": "Invalid JSON in queue record",
                    "queue_line": line_number
                })

            except Exception as error:
                results.append({
                    "status": "failed",
                    "reason": str(error),
                    "queue_line": line_number
                })

    return results