from typing import List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    # PaddleOCR 4 corner coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    points: List[List[float]]


class ExtractedLine(BaseModel):
    line_number: int
    text: str
    confidence: float
    bbox: BoundingBox


class FormattedOCROutput(BaseModel):
    document_id: str
    original_filename: str
    stored_file_path: str
    full_text: str
    total_lines: int
    average_confidence: float
    needs_human_review: bool
    processed_at: str
    lines: List[ExtractedLine] = Field(default_factory=list)