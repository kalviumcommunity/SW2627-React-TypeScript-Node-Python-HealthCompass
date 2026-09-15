"""Tests for document chunking strategies."""

import pytest

from healthcompass.ingestion import clean_page, load_document
from healthcompass.ingestion.chunking import (
    Chunk,
    calculate_chunk_stats,
    chunk_document,
    fixed_size_chunks,
    paragraph_chunks,
)
from healthcompass.ingestion.loader import DocumentPage


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return DocumentPage(
        document_id="test-id",
        source="test.txt",
        filename="test.txt",
        page_number=None,
        text="This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three.",
        metadata={"version": "1"},
    )


@pytest.fixture
def vaccination_guidance():
    """Load the vaccination guidance fixture."""
    path = "tests/fixtures/vaccination_guidance.txt"
    pages = load_document(path)
    return clean_page(pages[0])


def test_fixed_size_creates_multiple_chunks(sample_document):
    """Test that fixed-size chunking creates multiple chunks."""
    chunks = fixed_size_chunks(
        sample_document.text,
        sample_document.source,
        sample_document.filename,
        chunk_size=30,
        overlap=5,
    )
    assert len(chunks) > 1
    assert all(isinstance(chunk, Chunk) for chunk in chunks)


def test_overlap_is_present_between_chunks(sample_document):
    """Test that overlap is actually present between neighboring chunks."""
    chunks = fixed_size_chunks(
        sample_document.text,
        sample_document.source,
        sample_document.filename,
        chunk_size=30,
        overlap=10,
    )

    if len(chunks) >= 2:
        # Check that chunk 1's end overlaps with chunk 2's start
        chunk1_end = chunks[0].text[-10:]
        chunk2_start = chunks[1].text[:10]
        assert chunk1_end == chunk2_start


def test_paragraph_chunking_preserves_boundaries(sample_document):
    """Test that paragraph chunking preserves paragraph boundaries."""
    chunks = paragraph_chunks(
        sample_document.text, sample_document.source, sample_document.filename
    )

    # Should have 3 chunks for 3 paragraphs
    assert len(chunks) == 3

    # Each chunk should be a complete paragraph
    assert chunks[0].text == "This is paragraph one."
    assert chunks[1].text == "This is paragraph two."
    assert chunks[2].text == "This is paragraph three."


def test_both_strategies_work_on_same_document(vaccination_guidance):
    """Test that both strategies work on the same document."""
    fixed_chunks = chunk_document(
        vaccination_guidance, strategy="fixed", chunk_size=500, overlap=100
    )
    paragraph_chunks = chunk_document(vaccination_guidance, strategy="paragraph")

    assert len(fixed_chunks) > 0
    assert len(paragraph_chunks) > 0

    # Both should preserve source information
    assert all(chunk.source == vaccination_guidance.source for chunk in fixed_chunks)
    assert all(chunk.source == vaccination_guidance.source for chunk in paragraph_chunks)

    # Both should preserve filename
    assert all(chunk.filename == vaccination_guidance.filename for chunk in fixed_chunks)
    assert all(chunk.filename == vaccination_guidance.filename for chunk in paragraph_chunks)


def test_empty_text_is_handled_safely():
    """Test that empty text is handled safely."""
    chunks = fixed_size_chunks("", "test.txt", "test.txt")
    assert len(chunks) == 0

    chunks = paragraph_chunks("", "test.txt", "test.txt")
    assert len(chunks) == 0


def test_very_short_text_is_handled_safely():
    """Test that very short text is handled safely."""
    short_text = "Short"
    chunks = fixed_size_chunks(short_text, "test.txt", "test.txt", chunk_size=500, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].text == short_text

    chunks = paragraph_chunks(short_text, "test.txt", "test.txt")
    assert len(chunks) == 1
    assert chunks[0].text == short_text


def test_source_metadata_is_preserved():
    """Test that source metadata is preserved in chunks."""
    text = "This is a test document."
    metadata = {"version": "2", "region": "District A"}

    chunks = fixed_size_chunks(text, "test.txt", "test.txt", metadata=metadata)
    assert len(chunks) > 0
    assert chunks[0].metadata == metadata

    chunks = paragraph_chunks(text, "test.txt", "test.txt", metadata=metadata)
    assert len(chunks) > 0
    assert chunks[0].metadata == metadata


def test_statistics_are_calculated_correctly():
    """Test that statistics are calculated correctly."""
    chunks = [
        Chunk(text="a" * 100, source="test.txt", filename="test.txt", chunk_id=0, metadata={}),
        Chunk(text="b" * 200, source="test.txt", filename="test.txt", chunk_id=1, metadata={}),
        Chunk(text="c" * 300, source="test.txt", filename="test.txt", chunk_id=2, metadata={}),
    ]

    stats = calculate_chunk_stats(chunks)

    assert stats.chunk_count == 3
    assert stats.avg_chunk_size == 200.0
    assert stats.min_chunk_size == 100
    assert stats.max_chunk_size == 300


def test_empty_chunks_statistics():
    """Test statistics calculation with empty chunks."""
    stats = calculate_chunk_stats([])

    assert stats.chunk_count == 0
    assert stats.avg_chunk_size == 0.0
    assert stats.min_chunk_size == 0
    assert stats.max_chunk_size == 0


def test_no_chunk_contains_empty_text(sample_document):
    """Test that no chunk unexpectedly contains empty text."""
    chunks = fixed_size_chunks(
        sample_document.text,
        sample_document.source,
        sample_document.filename,
        chunk_size=30,
        overlap=5,
    )

    for chunk in chunks:
        assert chunk.text.strip(), f"Chunk {chunk.chunk_id} is empty"

    chunks = paragraph_chunks(
        sample_document.text, sample_document.source, sample_document.filename
    )

    for chunk in chunks:
        assert chunk.text.strip(), f"Chunk {chunk.chunk_id} is empty"


def test_chunk_ids_are_sequential():
    """Test that chunk IDs are sequential starting from 0."""
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

    fixed_chunks = fixed_size_chunks(text, "test.txt", "test.txt", chunk_size=20, overlap=5)
    assert [chunk.chunk_id for chunk in fixed_chunks] == list(range(len(fixed_chunks)))

    paragraph_chunks_list = paragraph_chunks(text, "test.txt", "test.txt")
    assert [chunk.chunk_id for chunk in paragraph_chunks_list] == list(
        range(len(paragraph_chunks_list))
    )


def test_fixed_size_with_zero_overlap():
    """Test fixed-size chunking with zero overlap."""
    text = "This is a test document for chunking without overlap."

    chunks = fixed_size_chunks(text, "test.txt", "test.txt", chunk_size=20, overlap=0)

    # Check that chunks don't overlap
    for i in range(len(chunks) - 1):
        chunk_end = chunks[i].text[-5:]
        chunk_start = chunks[i + 1].text[:5]
        assert chunk_end != chunk_start, "Chunks should not overlap when overlap is 0"


def test_paragraph_chunking_with_single_paragraph():
    """Test paragraph chunking with a single paragraph."""
    text = "This is a single paragraph."

    chunks = paragraph_chunks(text, "test.txt", "test.txt")

    assert len(chunks) == 1
    assert chunks[0].text == text


def test_paragraph_chunking_with_extra_newlines():
    """Test paragraph chunking handles extra newlines correctly."""
    text = "Paragraph one.\n\n\nParagraph two.\n\n\nParagraph three."

    chunks = paragraph_chunks(text, "test.txt", "test.txt")

    # Should still produce 3 chunks despite extra newlines
    assert len(chunks) == 3
    assert "Paragraph one." in chunks[0].text
    assert "Paragraph two." in chunks[1].text
    assert "Paragraph three." in chunks[2].text


def test_chunk_document_with_invalid_strategy(sample_document):
    """Test that chunk_document raises error for invalid strategy."""
    with pytest.raises(ValueError, match="Unknown strategy"):
        chunk_document(sample_document, strategy="invalid")


def test_chunk_sizes_match_configuration():
    """Test that fixed-size chunks match the configured size."""
    text = "a" * 1000  # 1000 characters
    chunks = fixed_size_chunks(text, "test.txt", "test.txt", chunk_size=200, overlap=50)

    # All chunks except possibly the last should be exactly chunk_size
    for i, chunk in enumerate(chunks[:-1]):
        assert len(chunk.text) == 200, f"Chunk {i} should be exactly 200 characters"


def test_metadata_isolation():
    """Test that metadata changes in one chunk don't affect others."""
    text = "Paragraph one.\n\nParagraph two."
    metadata = {"version": "1"}

    chunks = paragraph_chunks(text, "test.txt", "test.txt", metadata=metadata)

    # Modify metadata in first chunk
    chunks[0].metadata["version"] = "2"

    # Other chunks should still have original metadata
    assert chunks[1].metadata["version"] == "1"


def test_vaccination_guidance_fixed_size_results(vaccination_guidance):
    """Test actual results on vaccination guidance with fixed-size chunking."""
    chunks = chunk_document(vaccination_guidance, strategy="fixed", chunk_size=500, overlap=100)

    assert len(chunks) > 0
    stats = calculate_chunk_stats(chunks)

    # Check that chunks are reasonably sized
    assert stats.max_chunk_size <= 500
    assert stats.min_chunk_size >= 300  # Last chunk can be smaller due to text length
    assert stats.avg_chunk_size > 0


def test_vaccination_guidance_paragraph_results(vaccination_guidance):
    """Test actual results on vaccination guidance with paragraph chunking."""
    chunks = chunk_document(vaccination_guidance, strategy="paragraph")

    assert len(chunks) > 0
    stats = calculate_chunk_stats(chunks)

    # Check that we have multiple paragraphs
    assert stats.chunk_count > 5  # Should have many paragraphs

    # Check that no paragraph is empty
    assert stats.min_chunk_size > 0


@pytest.mark.parametrize("size,overlap", [(0, 0), (-1, 0), (10, 10), (10, 11), (10, -1), (True, 0)])
def test_invalid_overlap_or_size_cannot_create_nonadvancing_loop(size, overlap):
    with pytest.raises(ValueError):
        fixed_size_chunks(
            "long enough text", "guide.txt", "guide.txt", chunk_size=size, overlap=overlap
        )
