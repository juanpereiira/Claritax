
"""Service for submitting documents to the processing pipeline."""

import logging
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class PipelineSubmissionError(Exception):
    """Raised when a document cannot be submitted to the pipeline."""


class PipelineService:
    """Submit uploaded documents to the processing pipeline."""

    def submit_document(
        self,
        document: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """
        Schedule a stored document for processing.

        The document must already be validated and saved.
        """

        required_fields = (
            "document_id",
            "original_filename",
            "stored_filename",
            "content_type",
        )

        for field in required_fields:
            if not document.get(field):
                raise PipelineSubmissionError(
                    f"Missing required document field: {field}"
                )

        file_path = document.get("file_path")

        if not file_path:
            raise PipelineSubmissionError(
                "Stored document path is missing."
            )

        if not Path(file_path).is_file():
            raise PipelineSubmissionError(
                "Stored document file does not exist."
            )

        # Schedule pipeline execution after the API response.
        background_tasks.add_task(
            self.process_document,
            document,
        )

        logger.info(
            "Document submitted to processing pipeline: %s",
            document["document_id"],
        )

        return {
            "document_id": document["document_id"],
            "pipeline_status": "queued",
            "message": "Document submitted for processing.",
        }

    async def process_document(
        self,
        document: dict[str, Any],
    ) -> None:
        """
        Pipeline execution entry point.

        The detection and extraction stages will be connected
        here when their implementation is available.
        """

        document_id = document["document_id"]

        logger.info(
            "Processing pipeline received document: %s",
            document_id,
        )

        # TODO:
        # 1. Detect document type.
        # 2. Extract document content.
        # 3. Store processing results.
        # 4. Update final processing status.
