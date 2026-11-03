
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from app.services.pipeline_service import (
    PipelineService,
    PipelineSubmissionError,
)


@pytest.fixture
def stored_document(tmp_path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"%PDF-1.4 test")

    return {
        "document_id": "test-document-001",
        "original_filename": "sample.pdf",
        "stored_filename": "test-document-001.pdf",
        "file_path": str(file_path),
        "content_type": "application/pdf",
    }


def test_submit_document_adds_background_task(stored_document):
    service = PipelineService()
    background_tasks = BackgroundTasks()

    result = service.submit_document(
        document=stored_document,
        background_tasks=background_tasks,
    )

    assert result["document_id"] == "test-document-001"
    assert result["pipeline_status"] == "queued"
    assert len(background_tasks.tasks) == 1


def test_submit_document_rejects_missing_file(tmp_path):
    service = PipelineService()
    background_tasks = BackgroundTasks()

    document = {
        "document_id": "missing-document",
        "original_filename": "missing.pdf",
        "stored_filename": "missing.pdf",
        "file_path": str(tmp_path / "missing.pdf"),
        "content_type": "application/pdf",
    }

    with pytest.raises(PipelineSubmissionError):
        service.submit_document(
            document=document,
            background_tasks=background_tasks,
        )

    assert len(background_tasks.tasks) == 0


def test_submit_document_rejects_missing_metadata(tmp_path):
    service = PipelineService()
    background_tasks = BackgroundTasks()

    document = {
        "document_id": "incomplete-document",
        "file_path": str(tmp_path / "sample.pdf"),
    }

    with pytest.raises(PipelineSubmissionError):
        service.submit_document(
            document=document,
            background_tasks=background_tasks,
        )



def test_process_document_receives_document(stored_document):
    import anyio

    service = PipelineService()

    anyio.run(
        service.process_document,
        stored_document,
    )

    assert stored_document["document_id"] == "test-document-001"