"""Tests for context injection and prompt augmentation."""

from healthcompass.rag import (
    assemble_context,
    build_augmented_prompt,
    count_tokens,
    format_chunk_with_source,
)
from healthcompass.vector_store import RetrievalResult


class TestFormatChunkWithSource:
    """Tests for formatting chunks with source markers."""

    def test_format_chunk_with_source(self):
        """Test that chunk is formatted with correct source marker."""
        result = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample chunk text",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        formatted = format_chunk_with_source(result)

        assert "[1]" in formatted
        assert "test.txt#0" in formatted
        assert "Sample chunk text" in formatted

    def test_format_chunk_without_chunk_id(self):
        """Test formatting when chunk_id is not in metadata."""
        result = RetrievalResult(
            rank=2,
            chunk_id="chunk_2",
            distance=0.3,
            text="Another chunk",
            metadata={"source": "doc.pdf"},
        )

        formatted = format_chunk_with_source(result)

        assert "[2]" in formatted
        assert "doc.pdf#2" in formatted  # Should use rank as fallback
        assert "Another chunk" in formatted

    def test_format_chunk_without_source(self):
        """Test formatting when source is not in metadata."""
        result = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample text",
            metadata={},
        )

        formatted = format_chunk_with_source(result)

        assert "[1]" in formatted
        assert "unknown#1" in formatted  # Should use 'unknown' as fallback
        assert "Sample text" in formatted


class TestCountTokens:
    """Tests for token counting."""

    def test_count_tokens_simple_text(self):
        """Test counting tokens in simple text."""
        text = "Hello, world!"
        tokens = count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_count_tokens_empty_text(self):
        """Test counting tokens in empty text."""
        tokens = count_tokens("")
        assert tokens == 0

    def test_count_tokens_none(self):
        """Test counting tokens with None."""
        tokens = count_tokens(None)
        assert tokens == 0

    def test_count_tokens_longer_text(self):
        """Test counting tokens in longer text."""
        text = "This is a longer text that should have more tokens than the simple example."
        tokens = count_tokens(text)
        assert tokens > 0


class TestAssembleContext:
    """Tests for context assembly with token budget."""

    def test_assemble_context_empty_list(self):
        """Test assembling context with no chunks."""
        result = assemble_context([])

        assert result.context == ""
        assert result.context_tokens == 0
        assert result.chunks_used == 0
        assert result.sources_used == []
        assert result.chunks_excluded == 0

    def test_assemble_context_single_chunk(self):
        """Test assembling context with a single chunk."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample chunk text",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = assemble_context([chunk], max_context_tokens=1000)

        assert result.chunks_used == 1
        assert result.chunks_excluded == 0
        assert result.context_tokens > 0
        assert "Sample chunk text" in result.context
        assert len(result.sources_used) == 1

    def test_assemble_context_multiple_chunks(self):
        """Test assembling context with multiple chunks."""
        chunks = [
            RetrievalResult(
                rank=i + 1,
                chunk_id=f"chunk_{i}",
                distance=0.5 - (i * 0.1),
                text=f"Chunk text {i}",
                metadata={"source": f"doc{i}.txt", "chunk_id": str(i)},
            )
            for i in range(3)
        ]

        result = assemble_context(chunks, max_context_tokens=1000)

        assert result.chunks_used == 3
        assert result.chunks_excluded == 0
        assert len(result.sources_used) == 3

    def test_assemble_context_token_budget_respected(self):
        """Test that token budget is respected."""
        # Create chunks that will exceed the budget
        chunks = [
            RetrievalResult(
                rank=i + 1,
                chunk_id=f"chunk_{i}",
                distance=0.5,
                text="Sample text " * 100,  # Longer text
                metadata={"source": f"doc{i}.txt", "chunk_id": str(i)},
            )
            for i in range(5)
        ]

        # Set a small budget
        result = assemble_context(chunks, max_context_tokens=50)

        # Should exclude some chunks
        assert result.chunks_used < len(chunks)
        assert result.chunks_excluded > 0
        assert result.context_tokens <= 50

    def test_assemble_context_chunk_excluded_when_exceeds_budget(self):
        """Test that a chunk is excluded when it would exceed the budget."""
        # First chunk is small, second is large
        chunks = [
            RetrievalResult(
                rank=1,
                chunk_id="chunk_1",
                distance=0.5,
                text="Small chunk",
                metadata={"source": "doc1.txt", "chunk_id": "0"},
            ),
            RetrievalResult(
                rank=2,
                chunk_id="chunk_2",
                distance=0.3,
                text="Very large chunk " * 100,  # Will exceed budget
                metadata={"source": "doc2.txt", "chunk_id": "1"},
            ),
        ]

        result = assemble_context(chunks, max_context_tokens=20)

        # First chunk should be included, second excluded
        assert result.chunks_used == 1
        assert result.chunks_excluded == 1
        assert "Small chunk" in result.context
        assert "Very large chunk" not in result.context

    def test_assemble_context_correct_token_calculation(self):
        """Test that context token calculation is accurate."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Test text",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = assemble_context([chunk], max_context_tokens=1000)

        # Calculate expected tokens
        formatted = format_chunk_with_source(chunk)
        expected_tokens = count_tokens(formatted)

        assert result.context_tokens == expected_tokens

    def test_assemble_context_source_tracking(self):
        """Test that source metadata is tracked correctly."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample text",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = assemble_context([chunk], max_context_tokens=1000)

        assert len(result.sources_used) == 1
        source_info = result.sources_used[0]
        assert source_info["source"] == "test.txt"
        assert source_info["chunk_id"] == "chunk_1"
        assert source_info["rank"] == 1
        assert source_info["distance"] == 0.5

    def test_assemble_context_preserves_order(self):
        """Test that chunks are included in retrieval order."""
        chunks = [
            RetrievalResult(
                rank=i + 1,
                chunk_id=f"chunk_{i}",
                distance=0.5 - (i * 0.1),
                text=f"Text {i}",
                metadata={"source": f"doc{i}.txt", "chunk_id": str(i)},
            )
            for i in range(3)
        ]

        result = assemble_context(chunks, max_context_tokens=1000)

        # Check that sources are in the same order
        for i, source_info in enumerate(result.sources_used):
            assert source_info["rank"] == i + 1


class TestBuildAugmentedPrompt:
    """Tests for building augmented prompts."""

    def test_build_augmented_prompt_structure(self):
        """Test that augmented prompt has correct structure."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample context",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = build_augmented_prompt("Test question?", [chunk])

        assert "You are a grounded assistant" in result.prompt
        assert "Context:" in result.prompt
        assert "Question:" in result.prompt
        assert "Test question?" in result.prompt
        assert "Sample context" in result.prompt

    def test_build_augmented_prompt_custom_instruction(self):
        """Test building prompt with custom system instruction."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample context",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        custom_instruction = "Custom instruction"
        result = build_augmented_prompt(
            "Test question?", [chunk], system_instruction=custom_instruction
        )

        assert "Custom instruction" in result.prompt
        assert "grounded assistant" not in result.prompt

    def test_build_augmented_prompt_metadata_tracking(self):
        """Test that augmented prompt tracks metadata correctly."""
        chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Sample context",
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = build_augmented_prompt("Test question?", [chunk])

        assert result.chunks_used == 1
        assert result.context_tokens > 0
        assert len(result.sources_used) == 1
        assert result.sources_used[0]["source"] == "test.txt"

    def test_build_augmented_prompt_empty_chunks(self):
        """Test building prompt with no chunks."""
        result = build_augmented_prompt("Test question?", [])

        assert "Context:" in result.prompt
        assert "Question:" in result.prompt
        assert "Test question?" in result.prompt
        assert result.chunks_used == 0
        assert result.context_tokens == 0

    def test_build_augmented_prompt_single_large_chunk(self):
        """Test building prompt with a single very large chunk."""
        large_chunk = RetrievalResult(
            rank=1,
            chunk_id="chunk_1",
            distance=0.5,
            text="Large chunk " * 1000,
            metadata={"source": "test.txt", "chunk_id": "0"},
        )

        result = build_augmented_prompt("Test question?", [large_chunk], max_context_tokens=100)

        # Should exclude the large chunk
        assert result.chunks_used == 0
        assert result.chunks_excluded == 1
        assert result.context_tokens == 0
