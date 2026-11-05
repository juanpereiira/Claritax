
from app.services.pdf_extraction_service import PDFExtractionService


def test_pdf_extraction():
    service = PDFExtractionService()

    pdf_path = "storage/uploads/form16.pdf"  # Replace with the path to your test PDF file

    pages = service.extract_text_from_pdf(pdf_path)

    assert len(pages) > 0

    for page in pages:
        assert "page_number" in page
        assert "text" in page

        print(f"\nPAGE {page['page_number']}")
        print(page["text"])


if __name__ == "__main__":
    test_pdf_extraction()
