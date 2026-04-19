from docx import Document as DocxDocument

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

COLUMN_TO_CATEGORY = {
    0: "theme",
    1: "interventions",
    2: "active_ingredients",
    3: "evidence_base",
    4: "resources",
}


class DocxImporter(ISourceImporter):
    def __init__(self, splitter: ChunkSplitter) -> None:
        self.splitter = splitter

    def import_source(self, source: str, *, resilience_factor: str = "") -> list[RawChunk]:
        doc = DocxDocument(source)
        table = doc.tables[0]

        chunks: list[RawChunk] = []
        chunk_index = 0
        current_factor = resilience_factor

        for row_idx, row in enumerate(table.rows):
            if row_idx == 0:
                continue

            if not resilience_factor:
                current_factor = self._detect_factor(row, current_factor)

            for col_idx, cell in enumerate(row.cells):
                category = COLUMN_TO_CATEGORY.get(col_idx)
                if category == "theme":
                    continue

                text = cell.text.strip()
                if not text:
                    continue

                for chunk_text in self.splitter.split(text):
                    chunks.append(RawChunk(
                        content=chunk_text,
                        resilience_factor=current_factor,
                        category=category or "",
                        token_count=self.splitter.token_count(chunk_text),
                        chunk_index=chunk_index,
                    ))
                    chunk_index += 1

        return chunks

    def _detect_factor(self, row, current_factor: str) -> str:
        theme_text = row.cells[0].text.strip().lower()
        matched = next(
            (factor for theme, factor in THEME_TO_FACTOR.items() if theme_text.startswith(theme)),
            None,
        )
        return matched if matched is not None else current_factor
