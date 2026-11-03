from app.services.document_service import DocumentService


service = DocumentService()

pdf_path = "storage/uploads/form16.pdf"

pages = service.extract_text_from_pdf(pdf_path)

for page in pages:
    print(f"\n{'=' * 60}")
    print(f"PAGE {page['page_number']}")
    print(f"{'=' * 60}")
    print(page["text"])