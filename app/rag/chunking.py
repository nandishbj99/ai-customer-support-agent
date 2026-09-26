import re
from typing import Any, Dict, List, Optional


class DocumentChunk:
    """Represents a discrete text chunk with associated metadata."""

    def __init__(
        self,
        text: str,
        chunk_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.chunk_id = chunk_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": self.metadata,
        }


class RecursiveTextChunker:
    """Splits documents recursively by section, paragraph, sentence, and word."""

    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", " "]

    def split_text(self, text: str) -> List[str]:
        """Recursively split text into bounded chunks."""
        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text] if text else []

        chunks: List[str] = []
        raw_pieces = self._recursive_split(text, self.separators)

        # Merge raw small pieces into target chunk size with overlap
        current_chunk = ""
        for piece in raw_pieces:
            if not piece.strip():
                continue
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap from the end of the previous chunk
                overlap_text = current_chunk[-self.chunk_overlap :] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + piece

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return [text]

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep)
        result = []
        for i, part in enumerate(parts):
            part_with_sep = part + (sep if i < len(parts) - 1 else "")
            if len(part_with_sep) > self.chunk_size and remaining_seps:
                result.extend(self._recursive_split(part_with_sep, remaining_seps))
            else:
                result.append(part_with_sep)

        return result

    def chunk_document(
        self,
        doc_id: str,
        text: str,
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """Split a full document into identified DocumentChunks."""
        text_chunks = self.split_text(text)
        doc_chunks = []
        meta = base_metadata or {}

        for idx, chunk_text in enumerate(text_chunks):
            c_id = f"{doc_id}_chunk_{idx:03d}"
            chunk_meta = dict(meta)
            chunk_meta["doc_id"] = doc_id
            chunk_meta["chunk_index"] = idx
            doc_chunks.append(
                DocumentChunk(
                    text=chunk_text,
                    chunk_id=c_id,
                    metadata=chunk_meta,
                )
            )

        return doc_chunks
