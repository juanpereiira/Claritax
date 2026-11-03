
"""Document validation, storage, and pipeline submission."""

import hashlib
import io
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, UploadFile
from PIL import Image
from pypdf import PdfReader

from app.services.pipeline_service import (
    PipelineService,
    PipelineSubmissionError,
)


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class UploadValidationError(Exception):
    """Raised when an uploaded document fails validation."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentService:
    """Validate, store, and submit documents for processing."""

    def __init__(
        self,
        upload_dir: str = "storage/uploads",
        max_size_bytes: int = 10 * 1024 * 1024,
        pipeline_service: PipelineService | None = None,
    ):
        self.upload_dir = Path(upload_dir).resolve()
        self.max_size_bytes = max_size_bytes
        self.pipeline_service = (
            pipeline_service or PipelineService()
        )

    def validate_extension(self, filename: str) -> str:
        safe_filename = (filename or "document").replace("\\", "/")
        extension = Path(safe_filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise UploadValidationError(
                "unsupported_file_type",
                "Only PDF, JPG, JPEG, and PNG files are supported.",
                415,
            )

        return extension

    def validate_mime_type(
        self,
        extension: str,
        content_type: str,
    ) -> None:
        expected_type = MIME_TYPES.get(extension)

        if (content_type or "").lower() != expected_type:
            raise UploadValidationError(
                "mime_type_mismatch",
                "File content type does not match its extension.",
                415,
            )

    @staticmethod
    def detect_file_type(data: bytes) -> str | None:
        if data.startswith(b"%PDF-"):
            return ".pdf"

        if data.startswith(b"\xff\xd8\xff"):
            return ".jpg"

        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"

        return None

    def validate_file_signature(
        self,
        data: bytes,
        extension: str,
    ) -> None:
        detected_type = self.detect_file_type(data)

        valid_jpeg = (
            extension in {".jpg", ".jpeg"}
            and detected_type == ".jpg"
        )

        if detected_type != extension and not valid_jpeg:
            raise UploadValidationError(
                "invalid_file_content",
                "File content does not match its extension.",
            )

    @staticmethod
    def validate_file_integrity(
        data: bytes,
        extension: str,
    ) -> None:
        try:
            if extension in {".jpg", ".jpeg", ".png"}:
                with Image.open(io.BytesIO(data)) as image:
                    image.verify()

            elif extension == ".pdf":
                reader = PdfReader(
                    io.BytesIO(data),
                    strict=True,
                )

                if len(reader.pages) == 0:
                    raise ValueError("PDF contains no pages")

        except Exception as exc:
            raise UploadValidationError(
                "corrupted_file",
                "The uploaded file is corrupted or unreadable.",
            ) from exc

    def validate_file_size(self, data: bytes) -> None:
        if not data:
            raise UploadValidationError(
                "empty_file",
                "The uploaded file is empty.",
            )

        if len(data) > self.max_size_bytes:
            max_size_mb = self.max_size_bytes / (1024 * 1024)

            raise UploadValidationError(
                "file_too_large",
                f"File exceeds the {max_size_mb:g} MB limit.",
                413,
            )

    def validate_document(
        self,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> str:
        extension = self.validate_extension(filename)
        self.validate_file_size(data)

        self.validate_mime_type(
            extension,
            content_type,
        )

        self.validate_file_signature(
            data,
            extension,
        )

        self.validate_file_integrity(
            data,
            extension,
        )

        return extension

    async def save_upload(self, upload: UploadFile) -> dict[str, Any]:
        """Validate and store one uploaded document."""

        original_filename = (
            (upload.filename or "document")
            .replace("\\", "/")
            .split("/")[-1]
        )

        extension = self.validate_extension(original_filename)
        content_type = (upload.content_type or "").lower()

        data = await upload.read(self.max_size_bytes + 1)

        self.validate_document(
            filename=original_filename,
            content_type=content_type,
            data=data,
        )

        document_id = str(uuid.uuid4())
        stored_filename = f"{document_id}{extension}"

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = self.upload_dir / stored_filename

        try:
            with destination.open("xb") as file:
                file.write(data)
        except OSError as exc:
            raise RuntimeError(
                "Unable to store the uploaded document."
            ) from exc

        return {
            "document_id": document_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_path": str(destination),
            "content_type": content_type,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "status": "uploaded",
            "pipeline_status": "pending",
        }

    async def save_and_submit(
        self,
        upload: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """Save a document and submit it to the processing pipeline."""

        document = await self.save_upload(upload)

        try:
            submission = self.pipeline_service.submit_document(
                document=document,
                background_tasks=background_tasks,
            )

        except PipelineSubmissionError as exc:
            document["pipeline_status"] = "failed"
            document["pipeline_error"] = str(exc)
            return document

        document["pipeline_status"] = submission["pipeline_status"]
        document["pipeline_message"] = submission["message"]

        return document
