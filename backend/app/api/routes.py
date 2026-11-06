
from pathlib import Path
import json
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.services.document_service import (
    DocumentService,
    UploadValidationError,
)

from app.services.pipeline_service import (
    process_all_queued_documents,
    process_single_queued_document,
)
from app.services.ocr_service import PaddleOCRService
from app.schemas.ocr_schema import FormattedOCROutput

router = APIRouter()

document_service = DocumentService(
    upload_dir=settings.upload_dir,
    max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
)

# Supported image formats for PaddleOCR
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

@router.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "claritax-api",
    }


@router.post("/documents/upload", tags=["Documents"])
async def upload_documents(
    files: list[UploadFile] = File(...),
):
    # Validate batch size
    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "too_many_files",
                "message": (
                    f"Maximum {settings.max_upload_files} "
                    "files allowed per upload."
                ),
            },
        )

    results = []

    for uploaded_file in files:
        try:
            result = await document_service.save_and_submit(
                uploaded_file
            )
            results.append(result)

        except UploadValidationError as exc:
            results.append({
                "filename": uploaded_file.filename,
                "status": "rejected",
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            })

        except Exception:
            results.append({
                "filename": uploaded_file.filename,
                "status": "failed",
                "error": {
                    "code": "upload_failed",
                    "message": "An unexpected error occurred during upload.",
                },
            })

        finally:
            await uploaded_file.close()

    uploaded_count = sum(
        1 for result in results
        if result.get("status") == "uploaded"
    )

    rejected_count = sum(
        1 for result in results
        if result.get("status") == "rejected"
    )

    failed_count = sum(
        1 for result in results
        if result.get("status") == "failed"
    )

    return {
        "message": "Upload completed",
        "total_files": len(results),
        "uploaded": uploaded_count,
        "rejected": rejected_count,
        "failed": failed_count,
        "results": results,
    }


# --- OCR Endpoints ---

@router.post(
    "/ocr/process-queued",
    response_model=List[FormattedOCROutput],
    tags=["OCR Pipeline"],
)
def process_queued_ocr():
    """
    Reads all queued images from storage/processing_queue.jsonl,
    runs PaddleOCR on them, and saves formatted JSON results.
    """
    try:
        results = process_all_queued_documents()
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR execution failed: {str(exc)}",
        )


@router.get(
    "/ocr/results/{document_id}",
    response_model=FormattedOCROutput,
    tags=["OCR Pipeline"],
)
def get_document_ocr_result(document_id: str):
    """
    Retrieves formatted OCR output for an extracted document.
    If the OCR result JSON is not yet generated, it automatically searches
    for the file in the upload directory, runs PaddleOCR, saves the result,
    and returns it.
    """
    results_dir = Path("storage/ocr_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    result_file = results_dir / f"{document_id}.json"

    # 1. Return cached OCR result if it already exists
    if result_file.exists():
        return json.loads(result_file.read_text(encoding="utf-8"))

    # 2. Look for the uploaded image inside settings.upload_dir (storage/uploads/)
    upload_dir = Path(settings.upload_dir)
    matching_files = list(upload_dir.glob(f"{document_id}.*"))
    valid_images = [
        f for f in matching_files if f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not valid_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No uploaded image file found for document ID '{document_id}' inside {settings.upload_dir}.",
        )

    image_path = valid_images[0]

    # 3. Process the located image through PaddleOCR
    try:
        ocr_service = PaddleOCRService.get_instance()
        formatted_result = ocr_service.extract_text(
            file_path=str(image_path.resolve()),
            document_id=document_id,
            original_filename=image_path.name,
        )

        # 4. Save formatted result for future lookups
        result_file.write_text(
            formatted_result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return formatted_result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process OCR for image {image_path.name}: {str(exc)}",
        )