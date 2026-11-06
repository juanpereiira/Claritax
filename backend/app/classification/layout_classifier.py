import fitz


def analyze_pdf_layout(file_path: str) -> dict:
    document = fitz.open(file_path)

    page_count = len(document)
    total_tables_or_blocks = 0
    page_details = []

    for page in document:
        blocks = page.get_text("blocks")

        total_tables_or_blocks += len(blocks)

        page_details.append({
            "page_number": page.number + 1,
            "block_count": len(blocks),
            "text_length": len(page.get_text().strip())
        })

    document.close()

    return {
        "page_count": page_count,
        "block_count": total_tables_or_blocks,
        "pages": page_details
    }