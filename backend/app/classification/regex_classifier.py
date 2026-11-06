import re


PATTERNS = {
    "FORM_16A": [
        r"\bform\s*16\s*a\b",
    ],
    "FORM_16": [
        r"\bform\s*16\b(?!\s*a\b)",
    ],
    "FORM_26AS": [
        r"\bform\s*26as\b",
    ],
    "AIS": [
        r"\bannual\s+information\s+statement\b",
    ],
    "TIS": [
        r"\btaxpayer\s+information\s+summary\b",
    ],
    "ITR": [
        r"\bITR[- ]?[1-4]\b",
    ],
    "PAN": [
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    ],
}


def classify_by_regex(text: str) -> dict:
    results = {}

    for document_type, patterns in PATTERNS.items():
        matches = []

        for pattern in patterns:
            found = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            if found:
                matches.extend(found)

        if matches:
            results[document_type] = {
                "matched_patterns": matches
            }

    return results