
from typing import Any

from app.classification.keyword_classifier import classify_by_keywords
from app.classification.regex_classifier import classify_by_regex


SUPPORTED_DOCUMENT_TYPES = {
    "FORM_16",
    "FORM_16A",
    "SALARY_SLIP",
    "AIS",
    "TIS",
    "FORM_26AS",
    "BANK_STATEMENT",
    "INVESTMENT_STATEMENT",
    "CAPITAL_GAINS_STATEMENT",
    "RECEIPT",
    "ITR",
    "ITR_ACKNOWLEDGEMENT",
    "UNKNOWN",
}

# Initial thresholds. These should be calibrated using test documents.
CONFIDENCE_THRESHOLD = 0.60
REVIEW_THRESHOLD = 0.40
MIN_SCORE_MARGIN = 0.10


def _get_layout_score(
    document_type: str,
    layout_evidence: dict | None
) -> float | None:

    if not layout_evidence:
        return None

    scores = (
        layout_evidence.get("type_scores")
        or layout_evidence.get("scores")
    )

    if not isinstance(scores, dict):
        return None

    score = scores.get(document_type)

    if score is None:
        return None

    return max(0.0, min(float(score), 1.0))


def _calculate_confidence(
    keyword_score: float,
    regex_count: int,
    layout_score: float | None
) -> float:

    # Regex evidence strength
    regex_score = 1.0 if regex_count > 0 else 0.0

    # Use only available evidence sources.
    components = [
        (keyword_score, 0.45),
        (regex_score, 0.45),
    ]

    if layout_score is not None:
        components.append((layout_score, 0.10))

    total_weight = sum(weight for _, weight in components)

    confidence = sum(
        score * weight for score, weight in components
    ) / total_weight

    return round(confidence, 3)


def classify_document(
    extracted_text: str,
    layout_evidence: dict | None = None
) -> dict[str, Any]:

    if not extracted_text or not extracted_text.strip():
        return {
            "document_type": "UNKNOWN",
            "confidence": 0.0,
            "review_required": True,
            "matched_keywords": [],
            "matched_patterns": [],
            "reason": "No extracted text available."
        }

    # Step 1: Run keyword classification
    keyword_results = classify_by_keywords(extracted_text)

    # Step 2: Run regex classification
    regex_results = classify_by_regex(extracted_text)

    candidates = set(keyword_results.keys()) | set(regex_results.keys())

    # Step 3: Consider only supported document types
    candidates &= SUPPORTED_DOCUMENT_TYPES

    results = {}

    # Step 4: Combine classification evidence
    for document_type in candidates:

        keyword_data = keyword_results.get(document_type, {})
        regex_data = regex_results.get(document_type, {})

        keyword_score = float(keyword_data.get("score", 0.0))

        matched_keywords = keyword_data.get(
            "matched_keywords", []
        )

        matched_patterns = regex_data.get(
            "matched_patterns", []
        )

        layout_score = _get_layout_score(
            document_type,
            layout_evidence
        )

        # Step 5: Calculate combined confidence
        confidence = _calculate_confidence(
            keyword_score=keyword_score,
            regex_count=len(matched_patterns),
            layout_score=layout_score
        )

        results[document_type] = {
            "confidence": confidence,
            "matched_keywords": matched_keywords,
            "matched_patterns": matched_patterns,
            "keyword_score": round(keyword_score, 3),
            "layout_score": layout_score
        }

    # Step 6: Handle documents with no classification evidence
    if not results:
        return {
            "document_type": "UNKNOWN",
            "confidence": 0.0,
            "review_required": True,
            "matched_keywords": [],
            "matched_patterns": [],
            "reason": "No supported document type detected."
        }

    # Step 7: Rank document types by confidence
    ranked_results = sorted(
        results.items(),
        key=lambda item: item[1]["confidence"],
        reverse=True
    )

    best_type, best_result = ranked_results[0]

    confidence = best_result["confidence"]

    second_score = (
        ranked_results[1][1]["confidence"]
        if len(ranked_results) > 1
        else 0.0
    )

    score_margin = confidence - second_score

    # Step 8: Determine whether human review is required
    review_required = (
        confidence < CONFIDENCE_THRESHOLD
        or score_margin < MIN_SCORE_MARGIN
    )

    if confidence < REVIEW_THRESHOLD:
        document_type = "UNKNOWN"
        reason = "Classification confidence is too low."

    elif review_required:
        document_type = best_type
        reason = "Classification requires manual verification."

    else:
        document_type = best_type
        reason = "Document classified successfully."

    # Step 9: Return final classification
    return {
        "document_type": document_type,
        "confidence": confidence,
        "review_required": review_required,
        "matched_keywords": best_result["matched_keywords"],
        "matched_patterns": best_result["matched_patterns"],
        "keyword_score": best_result["keyword_score"],
        "layout_score": best_result["layout_score"],
        "score_margin": round(score_margin, 3),
        "reason": reason
    }
