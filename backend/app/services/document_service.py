import pymupdf


class DocumentService:
    def validate_upload(self, filename: str) -> bool:
        allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
        suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return suffix in allowed_extensions

    def extract_text_from_pdf(self, pdf_path: str) -> list:
        """
        Extract text from a PDF page by page using PyMuPDF.

        Returns:
            A list containing the extracted text and page number
            for each page.
        """

        document = pymupdf.open(pdf_path)

        pages = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            pages.append({
                "page_number": page_number,
                "text": text.strip()
            })

        document.close()

        return pages