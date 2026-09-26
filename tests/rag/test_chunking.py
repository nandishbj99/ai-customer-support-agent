from app.rag.chunking import RecursiveTextChunker


def test_chunker_short_text():
    chunker = RecursiveTextChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.split_text("Short policy description.")
    assert len(chunks) == 1
    assert chunks[0] == "Short policy description."


def test_chunker_long_text_splitting():
    chunker = RecursiveTextChunker(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "Section 1: General provisions.\n\n"
        "All customer disputes must be filed within 30 days of transaction date.\n\n"
        "Section 2: High value transactions.\n\n"
        "Transactions exceeding ₹50,000 are subject to additional verification."
    )
    chunks = chunker.split_text(sample_text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 150  # Allows slight margin for atomic words


def test_chunker_document_chunk_metadata():
    chunker = RecursiveTextChunker(chunk_size=200, chunk_overlap=30)
    text = "Paragraph one with some details.\n\nParagraph two with more details."
    doc_chunks = chunker.chunk_document(
        doc_id="doc_pol_01",
        text=text,
        base_metadata={"category": "compliance", "version": "1.0"},
    )

    assert len(doc_chunks) >= 1
    for idx, c in enumerate(doc_chunks):
        assert c.chunk_id == f"doc_pol_01_chunk_{idx:03d}"
        assert c.metadata["category"] == "compliance"
        assert c.metadata["doc_id"] == "doc_pol_01"
        assert c.metadata["chunk_index"] == idx
