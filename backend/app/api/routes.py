
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.services.document_service import (
    DocumentService,
    UploadValidationError,
)

router = APIRouter()

document_service = DocumentService(
    upload_dir=settings.upload_dir,
    max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
)


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
