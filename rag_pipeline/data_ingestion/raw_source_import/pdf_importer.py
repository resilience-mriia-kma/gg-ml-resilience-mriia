from pypdf import PdfReader

from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter
from rag_pipeline.data_ingestion.raw_source_import.dtos import RawChunk
from rag_pipeline.data_ingestion.raw_source_import.protocols import ISourceImporter

THEME_TO_FACTOR = {
    "family support": "family_support",
    "optimism": "optimism",
    "persistence": "goal_directedness",
    "physical activity": "health",
    "prosocial behaviour": "social_connections",
    "prosocial behavior": "social_connections",
}

COLUMN_HEADERS = {
    "effective interventions": "interventions",
    "active ingredients": "active_ingredients",
    "key evidence base": "evidence_base",
    "open manuals": "resources",
}


class PdfImporter(ISourceImporter):
    def __init__(self, splitter: ChunkSplitter) -> None:
        self.splitter = splitter

    def import_source(self, source: str, *, resilience_factor: str = "") -> list[RawChunk]:
        reader = PdfReader(source)

        if resilience_factor:
            return self._plain_chunking(reader, resilience_factor)

        chunks = self._heading_detection(reader)
        if chunks:
            return chunks

        return self._plain_chunking(reader, resilience_factor="")

    def _plain_chunking(self, reader: PdfReader, resilience_factor: str) -> list[RawChunk]:
        chunks: list[RawChunk] = []
        chunk_index = 0

        for page in reader.pages:
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            for text in self.splitter.split(page_text):
                chunks.append(RawChunk(
                    content=text,
                    resilience_factor=resilience_factor,
                    category="",
                    token_count=self.splitter.token_count(text),
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

        return chunks

    def _heading_detection(self, reader: PdfReader) -> list[RawChunk]:
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        chunks: list[RawChunk] = []
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
            for chunk_text in self.splitter.split(text):
                chunks.append(RawChunk(
                    content=chunk_text,
                    resilience_factor=current_factor,
                    category=current_category,
                    token_count=self.splitter.token_count(chunk_text),
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

        for line in full_text.split("\n"):
            stripped = line.strip()
            lower = stripped.lower()

            matched_factor = self._match_factor(lower)
            if matched_factor is not None:
                flush_block()
                current_factor = matched_factor
                current_category = ""
                current_block = []
                continue

            matched_category = self._match_category(lower)
            if matched_category is not None:
                flush_block()
                current_category = matched_category
                current_block = []
                continue

            if stripped:
                current_block.append(stripped)

        flush_block()
        return chunks

    def _match_factor(self, lower_line: str) -> str | None:
        return next(
            (factor for theme, factor in THEME_TO_FACTOR.items() if lower_line.startswith(theme)),
            None,
        )

    def _match_category(self, lower_line: str) -> str | None:
        return next(
            (cat for header, cat in COLUMN_HEADERS.items() if lower_line.startswith(header)),
            None,
        )
