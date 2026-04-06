import tiktoken

from rag_pipeline.constants import MAX_CHUNK_TOKENS

CHUNK_OVERLAP = 50

THEME_TO_FACTOR = {
    "family support": "family_support",
    "optimism": "optimism",
    "persistence": "goal_directedness",
    "physical activity": "health",
    "prosocial behaviour": "social_connections",
    "prosocial behavior": "social_connections",
}

COLUMN_TO_CATEGORY = {
    0: "theme",
    1: "interventions",
    2: "active_ingredients",
    3: "evidence_base",
    4: "resources",
}

_enc = tiktoken.encoding_for_model("text-embedding-3-small")


def _token_count(text: str) -> int:
    return len(_enc.encode(text))


def _split_into_chunks(text: str) -> list[str]:
    tokens = _enc.encode(text)
    if len(tokens) <= MAX_CHUNK_TOKENS:
        return [text]

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + MAX_CHUNK_TOKENS
        chunk_tokens = tokens[start:end]
        chunks.append(_enc.decode(chunk_tokens))
        if end >= len(tokens):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def _parse_docx(filepath: str) -> list[dict]:
    from docx import Document as DocxDocument

    doc = DocxDocument(filepath)
    table = doc.tables[0]
    chunks = []
    chunk_index = 0
    current_factor = ""

    for row_idx, row in enumerate(table.rows):
        if row_idx == 0:
            continue  # skip header row

        theme_text = row.cells[0].text.strip().lower()
        matched = next(
            (factor for theme, factor in THEME_TO_FACTOR.items() if theme_text.startswith(theme)),
            None,
        )
        if matched is not None:
            current_factor = matched

        for col_idx, cell in enumerate(row.cells):
            category = COLUMN_TO_CATEGORY.get(col_idx)
            if category == "theme":
                continue

            text = cell.text.strip()
            if not text:
                continue

            for chunk_text in _split_into_chunks(text):
                chunks.append(
                    {
                        "content": chunk_text,
                        "resilience_factor": current_factor,
                        "category": category,
                        "token_count": _token_count(chunk_text),
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

    return chunks


# Column section headers as they appear in PDF extracted text
_PDF_COLUMN_HEADERS = {
    "effective interventions": "interventions",
    "active ingredients": "active_ingredients",
    "key evidence base": "evidence_base",
    "open manuals": "resources",
}


def _parse_pdf(filepath: str) -> list[dict]:
    from pypdf import PdfReader

    reader = PdfReader(filepath)
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    chunks = []
    chunk_index = 0
    current_factor = ""
    current_category = ""
    current_block: list[str] = []

    def flush_block() -> None:
        nonlocal chunk_index
        if not current_block or not current_factor or not current_category:
            return
        text = " ".join(current_block).strip()
        if not text:
            return
        for chunk_text in _split_into_chunks(text):
            chunks.append(
                {
                    "content": chunk_text,
                    "resilience_factor": current_factor,
                    "category": current_category,
                    "token_count": _token_count(chunk_text),
                    "chunk_index": chunk_index,
                }
            )
            chunk_index += 1

    for line in full_text.split("\n"):
        stripped = line.strip()
        lower = stripped.lower()

        matched_factor = next(
            (factor for theme, factor in THEME_TO_FACTOR.items() if lower.startswith(theme)),
            None,
        )
        if matched_factor is not None:
            flush_block()
            current_factor = matched_factor
            current_category = ""
            current_block = []
            continue

        matched_category = next(
            (cat for header, cat in _PDF_COLUMN_HEADERS.items() if lower.startswith(header)),
            None,
        )
        if matched_category is not None:
            flush_block()
            current_category = matched_category
            current_block = []
            continue

        if stripped:
            current_block.append(stripped)

    flush_block()
    return chunks


def import_file(filepath: str) -> list[dict]:
    """
    Parse .docx or .pdf file and return list of chunks.

    Each chunk dict contains:
        content           – text of the chunk
        resilience_factor – e.g. "family_support"
        category          – e.g. "interventions"
        token_count       – number of tokens in this chunk
        chunk_index       – sequential index across all chunks in the file
    """
    if filepath.endswith(".docx"):
        return _parse_docx(filepath)
    if filepath.endswith(".pdf"):
        return _parse_pdf(filepath)
    raise ValueError(f"Unsupported file type: {filepath!r}. Expected .docx or .pdf.")