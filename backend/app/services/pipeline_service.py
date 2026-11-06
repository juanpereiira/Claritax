
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from app.services.document_dispatcher import dispatch_document
from app.services.ocr_service import PaddleOCRService
from app.schemas.ocr_schema import FormattedOCROutput


BACKEND_DIR = Path(__file__).resolve().parents[2]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


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
    Routes queued documents through the document dispatcher.

    The dispatcher handles document-level processing and routing.
    This function does not modify or delete queue records.
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


def process_single_queued_document(
    record: dict
) -> Optional[FormattedOCROutput]:
    """
    Runs PaddleOCR on a single queued image and saves formatted JSON.
    """

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

    results_dir = BACKEND_DIR / "storage" / "ocr_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"{record['document_id']}.json"

    with output_file.open("w", encoding="utf-8") as file:
        file.write(formatted_result.model_dump_json(indent=2))

    return formatted_result


def process_all_queued_documents() -> List[FormattedOCROutput]:
    """
    Processes queued image records using PaddleOCR.

    Non-image records remain queued for the document dispatcher.
    """

    queue_path = get_queue_path()

    if not queue_path.exists():
        return []

    lines = queue_path.read_text(encoding="utf-8").splitlines()

    updated_records = []
    ocr_results: List[FormattedOCROutput] = []

    for line_number, line in enumerate(lines, start=1):

        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            updated_records.append({
                "status": "failed",
                "error": "Invalid JSON in queue record",
                "queue_line": line_number
            })
            continue

        if record.get("status") == "queued":

            file_path = record.get("file_path", "")
            extension = Path(file_path).suffix.lower()

            if extension in IMAGE_EXTENSIONS:
                try:
                    result = process_single_queued_document(record)

                    if result:
                        ocr_results.append(result)

                        record["status"] = "ocr_completed"
                        record["average_confidence"] = (
                            result.average_confidence
                        )
                        record["needs_human_review"] = (
                            result.needs_human_review
                        )

                except Exception as error:
                    record["status"] = "ocr_failed"
                    record["error"] = str(error)

                record["processed_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )

        updated_records.append(record)

    with queue_path.open("w", encoding="utf-8") as file:
        for record in updated_records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    return ocr_results
