import fitz


def detect_pdf_type(file_path: str) -> dict:
    """
    Detect whether a PDF contains digital text, scanned images,
    a mixture of both, or pages that need manual review.
    """

    try:
        pdf = fitz.open(file_path)

        with pdf:
            if pdf.needs_pass:
                return {
                    "pdf_type": "PASSWORD_PROTECTED",
                    "pages": [],
                    "review_required": True,
                    "reason": "PDF requires a password"
                }

            if pdf.page_count == 0:
                return {
                    "pdf_type": "INVALID_PDF",
                    "pages": [],
                    "review_required": True,
                    "reason": "PDF contains no pages"
                }

            page_results = []

            for page_number, page in enumerate(pdf):
                text = page.get_text("text").strip()
                images = page.get_images(full=True)

                if len(text) > 30:
                    page_type = "DIGITAL"
                elif images:
                    page_type = "SCANNED"
                else:
                    page_type = "UNCLEAR"

                page_results.append({
                    "page": page_number + 1,
                    "type": page_type,
                    "text_length": len(text),
                    "image_count": len(images)
                })
    
        
        types = {page["type"] for page in page_results}

        if types == {"DIGITAL"}:
            overall_type = "DIGITAL_PDF"

        elif types == {"SCANNED"}:
            overall_type = "SCANNED_PDF"

        elif "DIGITAL" in types and "SCANNED" in types:
            overall_type = "HYBRID_PDF"

        else:
            overall_type = "NEEDS_REVIEW"

        return {
            "pdf_type": overall_type,
            "pages": page_results,
            "review_required": "UNCLEAR" in types
        }
            

    except fitz.FileDataError:
        return {
            "pdf_type": "INVALID_PDF",
            "pages": [],
            "review_required": True,
            "reason": "The PDF file is damaged or unreadable"
        }

    except Exception as error:
        return {
            "pdf_type": "INVALID_PDF",
            "pages": [],
            "review_required": True,
            "reason": str(error)
        }
        