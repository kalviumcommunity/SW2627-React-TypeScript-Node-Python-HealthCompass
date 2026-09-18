"""Tests for token-aware chunking functionality."""

import pytest

from healthcompass.ingestion import calculate_token_chunk_stats, token_chunks


class TestTokenChunking:
    """Test token-based chunking with tiktoken."""

    def test_empty_text_returns_no_chunks(self):
        """Empty text should return no chunks."""
        chunks = token_chunks("", source="test.txt", filename="test.txt")
        assert len(chunks) == 0

    def test_whitespace_only_returns_no_chunks(self):
        """Whitespace-only text should return no chunks."""
        chunks = token_chunks("   \n\n  ", source="test.txt", filename="test.txt")
        assert len(chunks) == 0

    def test_short_text_produces_one_chunk(self):
        """Short text should produce one chunk."""
        text = "Short text example."
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=100)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_id == 0

    def test_chunk_size_measured_in_tokens(self):
        """Chunk size should be measured in tokens, not characters."""
        text = "This is a test sentence with multiple words. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=0)
        assert len(chunks) > 1
        # First chunk should have exactly 50 tokens (or less if text is shorter)
        assert chunks[0].token_count <= 50
        # All chunks except possibly the last should respect the size
        for i, chunk in enumerate(chunks[:-1]):
            assert chunk.token_count == 50, f"Chunk {i} has {chunk.token_count} tokens, expected 50"

    def test_every_chunk_respects_token_size_except_final(self):
        """Every chunk should respect the configured token size, except the final chunk."""
        text = "This is a test sentence with multiple words. " * 30
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=40, overlap=0)
        assert len(chunks) > 1
        # All chunks except the last should have exactly 40 tokens
        for i, chunk in enumerate(chunks[:-1]):
            assert chunk.token_count == 40, f"Chunk {i} has {chunk.token_count} tokens, expected 40"
        # Final chunk can be smaller
        assert chunks[-1].token_count <= 40

    def test_overlap_is_actually_applied(self):
        """Overlap should be applied between adjacent chunks."""
        text = "This is a test sentence with multiple words. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=10)
        assert len(chunks) > 1
        # Adjacent chunks should share some text - check if any significant overlap exists
        overlap_found = False
        for i in range(len(chunks) - 1):
            # Check if the end of chunk i appears anywhere in chunk i+1
            if chunks[i].text[-30:] in chunks[i+1].text:
                overlap_found = True
                break
        assert overlap_found, "No overlap found between adjacent chunks"

    def test_overlap_smaller_than_chunk_size(self):
        """Overlap must be smaller than chunk size."""
        text = "Test text for overlap validation."
        with pytest.raises(ValueError, match="overlap must satisfy"):
            token_chunks(text, source="test.txt", filename="test.txt", size=10, overlap=10)

    def test_adjacent_chunks_share_boundary_tokens(self):
        """Adjacent chunks should share the expected boundary tokens."""
        text = "This is a test sentence with multiple words. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=15)
        assert len(chunks) > 1
        # The end of chunk 0 should overlap with the start of chunk 1
        overlap_text = chunks[0].text[-50:]
        assert overlap_text in chunks[1].text

        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        first_tokens = encoding.encode(chunks[0].text)
        second_tokens = encoding.encode(chunks[1].text)
        assert first_tokens[-15:] == second_tokens[:15]

    def test_zero_overlap_works(self):
        """Zero overlap should work correctly."""
        text = "This is a test sentence with multiple words. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=0)
        assert len(chunks) > 1
        # Adjacent chunks should not overlap
        assert chunks[0].text[-20:] not in chunks[1].text[:20]

    def test_source_metadata_preserved(self):
        """Source metadata should be preserved in chunks."""
        text = "Test text for metadata preservation."
        metadata = {"key1": "value1", "key2": "value2"}
        chunks = token_chunks(
            text, source="test.txt", filename="test.txt", metadata=metadata
        )
        assert len(chunks) == 1
        assert chunks[0].source == "test.txt"
        assert chunks[0].filename == "test.txt"
        assert chunks[0].metadata == metadata

    def test_no_infinite_loop(self):
        """Chunking should not cause an infinite loop."""
        text = "Test text. " * 1000
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=100, overlap=10)
        assert len(chunks) > 0
        assert len(chunks) < 100  # Should complete in reasonable number of chunks

    def test_chunk_ids_are_sequential(self):
        """Chunk IDs should be sequential starting from 0."""
        text = "This is a test sentence with multiple words. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=10)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i

    def test_negative_chunk_size_raises_error(self):
        """Negative chunk size should raise an error."""
        text = "Test text."
        with pytest.raises(ValueError, match="size must be a positive integer"):
            token_chunks(text, source="test.txt", filename="test.txt", size=-10)

    def test_negative_overlap_raises_error(self):
        """Negative overlap should raise an error."""
        text = "Test text."
        with pytest.raises(ValueError, match="overlap must satisfy"):
            token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=-5)

    def test_metadata_isolation(self):
        """Metadata should be isolated between chunks."""
        text = "Test text for metadata isolation. " * 20
        metadata = {"key": "value"}
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=30, overlap=5, metadata=metadata)
        assert len(chunks) >= 2, "Need at least 2 chunks to test isolation"
        # Modify metadata in first chunk
        chunks[0].metadata["key"] = "modified"
        # Second chunk should have original metadata
        assert chunks[1].metadata["key"] == "value"

    def test_vaccination_guidance_no_overlap(self):
        """Test vaccination guidance document with no overlap."""
        text = """Vaccination Guidelines for Public Health Response

This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Section 1: Core Vaccination Principles

Vaccination guidance should always be checked against the latest approved official version. Public health officials recommend following current guidelines from authoritative sources such as the CDC and WHO. Regular updates ensure that vaccination policies reflect the most recent scientific evidence and epidemiological data."""
        chunks = token_chunks(text, source="vaccination_guidance.txt", filename="vaccination_guidance.txt", size=100, overlap=0)
        assert len(chunks) >= 2
        stats = calculate_token_chunk_stats(chunks)
        assert stats.chunk_count == len(chunks)
        assert stats.total_tokens > 0
        assert stats.avg_token_count > 0

    def test_vaccination_guidance_with_overlap(self):
        """Test vaccination guidance document with overlap."""
        text = """Vaccination Guidelines for Public Health Response

This document provides current approved guidance for vaccination protocols in public health emergencies. HealthCompass stores official public-health documents with versions, effective dates, geographic applicability, and approval status. Active and approved guidance should be preferred over superseded or expired documents.

Section 1: Core Vaccination Principles

Vaccination guidance should always be checked against the latest approved official version. Public health officials recommend following current guidelines from authoritative sources such as the CDC and WHO. Regular updates ensure that vaccination policies reflect the most recent scientific evidence and epidemiological data."""
        chunks = token_chunks(text, source="vaccination_guidance.txt", filename="vaccination_guidance.txt", size=100, overlap=20)
        assert len(chunks) >= 2
        stats = calculate_token_chunk_stats(chunks)
        assert stats.chunk_count == len(chunks)
        assert stats.total_tokens > 0
        assert stats.avg_token_count > 0

    def test_boundary_context_demonstration(self):
        """Test the boundary context demonstration scenario."""
        text = """
Vaccination protocols require strict adherence to approved guidelines. 
Healthcare providers must verify that all vaccination protocols are followed 
according to the latest approved official version from public health authorities. 
Regular updates ensure that vaccination policies reflect the most recent scientific 
evidence and epidemiological data available from the CDC and WHO.
    """.strip()

        # Without overlap
        chunks_no_overlap = token_chunks(text, source="demo.txt", filename="demo.txt", size=40, overlap=0)
        assert len(chunks_no_overlap) == 2

        # With overlap
        chunks_with_overlap = token_chunks(text, source="demo.txt", filename="demo.txt", size=40, overlap=10)
        assert len(chunks_with_overlap) == 2

        # Verify overlap preserves context - check if end of chunk 0 appears in chunk 1
        overlap_found = chunks_with_overlap[0].text[-30:] in chunks_with_overlap[1].text
        assert overlap_found, "Overlap should preserve context across boundary"

    def test_custom_encoding_name(self):
        """Test custom encoding name parameter."""
        text = "Test text for custom encoding."
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=0, encoding_name="cl100k_base")
        assert len(chunks) == 1
        assert chunks[0].token_count > 0

    def test_calculate_token_chunk_stats_empty(self):
        """Test stats calculation with empty chunk list."""
        stats = calculate_token_chunk_stats([])
        assert stats.chunk_count == 0
        assert stats.total_tokens == 0
        assert stats.avg_token_count == 0.0
        assert stats.min_token_count == 0
        assert stats.max_token_count == 0

    def test_calculate_token_chunk_stats_single_chunk(self):
        """Test stats calculation with single chunk."""
        chunks = [token_chunks("Test text.", source="test.txt", filename="test.txt", size=100)[0]]
        stats = calculate_token_chunk_stats(chunks)
        assert stats.chunk_count == 1
        assert stats.total_tokens == chunks[0].token_count
        assert stats.avg_token_count == chunks[0].token_count
        assert stats.min_token_count == chunks[0].token_count
        assert stats.max_token_count == chunks[0].token_count

    def test_calculate_token_chunk_stats_multiple_chunks(self):
        """Test stats calculation with multiple chunks."""
        text = "Test text for stats calculation. " * 20
        chunks = token_chunks(text, source="test.txt", filename="test.txt", size=50, overlap=10)
        stats = calculate_token_chunk_stats(chunks)
        assert stats.chunk_count == len(chunks)
        assert stats.total_tokens == sum(c.token_count for c in chunks)
        assert stats.min_token_count <= stats.avg_token_count <= stats.max_token_count
