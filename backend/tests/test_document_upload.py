import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.document_service import DocumentService, UploadValidationError

client = TestClient(app)


def png_bytes():
    image = Image.new("RGB", (2, 2), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_png_accepted_and_queued(tmp_path, monkeypatch):
    queue = tmp_path / "queue.jsonl"
    monkeypatch.setenv("CLARITAX_PIPELINE_QUEUE_PATH", str(queue))
    # Route service uses configured storage; override for test isolation.
    from app.api import routes
    routes.document_service = DocumentService(str(tmp_path / "uploads"), 1024 * 1024)
    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("sample.png", png_bytes(), "image/png"))],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == 1
    item = body["results"][0]
    assert item["pipeline_status"] == "queued"
    assert Path(tmp_path / "uploads" / item["stored_filename"]).exists()
    record = json.loads(queue.read_text().strip())
    assert record["document_id"] == item["document_id"]


def test_unsupported_file_rejected(tmp_path):
    service = DocumentService(str(tmp_path / "uploads"))
    with pytest.raises(UploadValidationError) as exc:
        service.validate_extension("report.docx")
    assert exc.value.code == "unsupported_file_type"
    assert exc.value.status_code == 415


def test_multiple_uploads_supported(tmp_path, monkeypatch):
    from app.api import routes
    routes.document_service = DocumentService(str(tmp_path / "uploads"), 1024 * 1024)
    monkeypatch.setenv("CLARITAX_PIPELINE_QUEUE_PATH", str(tmp_path / "queue.jsonl"))
    response = client.post(
        "/api/v1/documents/upload",
        files=[
            ("files", ("one.png", png_bytes(), "image/png")),
            ("files", ("two.png", png_bytes(), "image/png")),
        ],
    )
    assert response.status_code == 200
    assert response.json()["uploaded"] == 2
