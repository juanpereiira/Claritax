import os
import logging
from datetime import datetime, timezone
from typing import Optional
import numpy as np

# Prevent Windows oneDNN/MKLDNN PIR crashes
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_onednn"] = "0"

from paddleocr import PaddleOCR
from app.schemas.ocr_schema import FormattedOCROutput, ExtractedLine, BoundingBox

logger = logging.getLogger(__name__)


def _to_polygon(box) -> list:
    """Converts bounding box representations (NumPy arrays, lists) to a 4-point list."""
    try:
        arr = np.array(box, dtype=float)
        if arr.size == 4 and arr.ndim == 1:
            x1, y1, x2, y2 = arr
            return [[float(x1), float(y1)], [float(x2), float(y1)], [float(x2), float(y2)], [float(x1), float(y2)]]
        if arr.size == 8:
            return arr.reshape(4, 2).astype(float).tolist()
        if arr.ndim == 2 and arr.shape == (4, 2):
            return arr.astype(float).tolist()
        return arr.tolist()
    except Exception:
        return [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]


class PaddleOCRService:
    _instance: Optional["PaddleOCRService"] = None

    def __init__(self):
        self.engine = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            enable_mkldnn=False,
        )

    @classmethod
    def get_instance(cls) -> "PaddleOCRService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def extract_text(
        self,
        file_path: str,
        document_id: str,
        original_filename: str,
        confidence_threshold: float = 0.85,
    ) -> FormattedOCROutput:
        """Reads a stored image and extracts text across all PaddleOCR output formats."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Stored file does not exist: {file_path}")

        raw_result = self.engine.ocr(file_path)

        lines: list[ExtractedLine] = []
        text_lines: list[str] = []
        total_confidence = 0.0

        if raw_result is not None:
            elements = raw_result if isinstance(raw_result, list) else [raw_result]

            for element in elements:
                if element is None:
                    continue

                # Case 1: PaddleOCR 3.x Dictionary Output
                if isinstance(element, dict):
                    boxes = element.get("rec_boxes")
                    if boxes is None:
                        boxes = element.get("dt_polys")
                    if boxes is None:
                        boxes = []

                    texts = element.get("rec_texts")
                    if texts is None:
                        texts = []

                    scores = element.get("rec_scores")
                    if scores is None:
                        scores = []

                    num_items = len(texts) if hasattr(texts, "__len__") else 0

                    for idx in range(num_items):
                        cleaned_text = str(texts[idx]).strip()
                        if not cleaned_text:
                            continue

                        score = float(scores[idx]) if idx < len(scores) else 1.0
                        raw_box = boxes[idx] if idx < len(boxes) else []
                        poly_coords = _to_polygon(raw_box)

                        lines.append(
                            ExtractedLine(
                                line_number=len(lines) + 1,
                                text=cleaned_text,
                                confidence=round(score, 4),
                                bbox=BoundingBox(points=poly_coords),
                            )
                        )
                        text_lines.append(cleaned_text)
                        total_confidence += score

                # Case 2: Classic Nested List Output: [ [ [box_coords], (text, score) ], ... ]
                elif isinstance(element, (list, tuple)):
                    for item in element:
                        if not isinstance(item, (list, tuple)) or len(item) < 2:
                            continue

                        raw_box = item[0]
                        content = item[1]
                        poly_coords = _to_polygon(raw_box)

                        if isinstance(content, (list, tuple)) and len(content) >= 2:
                            cleaned_text = str(content[0]).strip()
                            score = float(content[1])
                        else:
                            cleaned_text = str(content).strip()
                            score = 1.0

                        if cleaned_text:
                            lines.append(
                                ExtractedLine(
                                    line_number=len(lines) + 1,
                                    text=cleaned_text,
                                    confidence=round(score, 4),
                                    bbox=BoundingBox(points=poly_coords),
                                )
                            )
                            text_lines.append(cleaned_text)
                            total_confidence += score

        avg_conf = round(total_confidence / len(lines), 4) if len(lines) > 0 else 0.0
        full_text = "\n".join(text_lines)
        needs_review = (avg_conf < confidence_threshold) or (len(lines) == 0)

        return FormattedOCROutput(
            document_id=document_id,
            original_filename=original_filename,
            stored_file_path=file_path,
            full_text=full_text,
            total_lines=len(lines),
            average_confidence=avg_conf,
            needs_human_review=needs_review,
            processed_at=datetime.now(timezone.utc).isoformat(),
            lines=lines,
        )