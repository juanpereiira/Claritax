
import pymupdf


class PDFExtractionService:
    """Extract text from digital PDF documents."""

    def extract_text_from_pdf(self, pdf_path: str) -> list:
        """
        Extract text page by page using PyMuPDF.

        Returns page numbers along with extracted text.
        """

        pages = []

        with pymupdf.open(pdf_path) as document:

            for page_number, page in enumerate(document, start=1):

                text = page.get_text("text")

                pages.append({
                    "page_number": page_number,
                    "text": text.strip()
                })

        return pages
