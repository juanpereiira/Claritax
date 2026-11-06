
from app.services.document_classifier import classify_document

sample_text = """
salary slip
Certificate under Section 203
Assessment Year: 2025-26
Employer Name: ABC Technologies
Employee Name: John
TDS Details
"""

result = classify_document(sample_text)

print("\nDOCUMENT CLASSIFICATION RESULT")
print("--------------------------------")

for key, value in result.items():
    print(f"{key}: {value}")
