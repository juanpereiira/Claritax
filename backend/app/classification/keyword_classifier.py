import re


KEYWORDS = {
    "FORM_16A": [
        "form 16a",
        "certificate under section 203",
    ],
    "FORM_16": [
        "form 16",
        "salary",
        "tax deducted at source",
    ],
    "AIS": [
        "annual information statement",
    ],
    "TIS": [
        "taxpayer information summary",
    ],
    "FORM_26AS": [
        "form 26as",
        "annual tax statement",
    ],
    "SALARY_SLIP": [
        "basic salary",
        "gross salary",
        "net pay",
        "hra",
        "earnings",
        "deductions",
    ],
    "BANK_STATEMENT": [
        "opening balance",
        "closing balance",
        "transaction date",
        "debit",
        "credit",
    ],
    "INVESTMENT_STATEMENT": [
        "folio number",
        "nav",
        "units",
        "mutual fund",
    ],
    "CAPITAL_GAINS_STATEMENT": [
        "sale consideration",
        "cost of acquisition",
        "capital gains",
    ],
    "RECEIPT": [
        "receipt number",
        "amount paid",
        "payment received",
    ],
    "ITR_ACKNOWLEDGEMENT": [
        "itr-v",
        "acknowledgement number",
        "return filing",
    ],
    "ITR": [
        "income tax return",
        "itr-1",
        "itr-2",
        "itr-3",
        "itr-4",
    ],
}


def classify_by_keywords(text: str) -> dict:
    normalized_text = re.sub(r"\s+", " ", text.lower())

    scores = {}

    for document_type, keywords in KEYWORDS.items():
        matched = [
            keyword
            for keyword in keywords
            if keyword in normalized_text
        ]

        if matched:
            scores[document_type] = {
                "score": len(matched) / len(keywords),
                "matched_keywords": matched,
            }

    return scores