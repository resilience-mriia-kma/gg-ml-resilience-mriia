from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter
from rag_pipeline.data_ingestion.raw_source_import.docx_importer import DocxImporter
from rag_pipeline.data_ingestion.raw_source_import.dtos import RawChunk
from rag_pipeline.data_ingestion.raw_source_import.pdf_importer import PdfImporter
from rag_pipeline.data_ingestion.raw_source_import.protocols import ISourceImporter


class FileImporter:
    # TODO: possibly refactor as a strategy
    IMPORTERS: dict[str, type[ISourceImporter]] = {
        ".pdf": PdfImporter,
        ".docx": DocxImporter,
    }

    def __init__(self, splitter: ChunkSplitter) -> None:
        self.splitter = splitter

    def import_file(self, filepath: str, *, resilience_factor: str = "") -> list[RawChunk]:
        for ext, importer_cls in self.IMPORTERS.items():
            if filepath.endswith(ext):
                importer = importer_cls(self.splitter)
                return importer.import_source(filepath, resilience_factor=resilience_factor)

        supported = ", ".join(self.IMPORTERS)
        raise ValueError(f"Unsupported file type: {filepath!r}. Expected: {supported}")
