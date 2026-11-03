# Document Upload Flow

## Supported files
- PDF (`application/pdf`)
- JPG/JPEG (`image/jpeg`)
- PNG (`image/png`)

The upload endpoint is `POST /api/v1/documents/upload` and accepts repeated
`files` multipart fields (multiple documents per request). Each file is checked
for extension, MIME type, binary signature, integrity, non-empty content, and
configured size limit before storage. Stored filenames use UUIDs.

Successful files are appended to the JSONL processing handoff queue. Configure
`CLARITAX_PIPELINE_QUEUE_PATH` to change the queue location; default is
`storage/processing_queue.jsonl`. Queue records include document ID, absolute
stored path, original filename, MIME type, queued status, and timestamp. The
detection/OCR/extraction worker should consume this queue and dispatch records
to the existing pipeline.

Per-file failures are returned in the `results` array with an error code and
message. Unsupported types return `unsupported_file_type`; corrupted files
return `corrupted_file`; oversize files return `file_too_large`.

## Run tests
From `backend/`: `pytest -q`
