"""Chunk coverage, limits and provenance are contracts independent of strategy."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import pymupdf
import pytest

from healthcompass.ingestion import (
    DocumentPage,
    chunk_document,
    chunk_page,
    clean_page,
    load_document,
    tag_chunks,
)
from healthcompass.ingestion.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "chunking_guidance.txt"


def page(text):
    return DocumentPage("doc-id", "/example/guide.txt", "guide.txt", None, text, {"version": "1"})


@pytest.mark.parametrize("strategy", ["fixed", "paragraph"])
@pytest.mark.parametrize("limit", [1, 2, 13, 80, 1000])
def test_chunks_cover_every_nonwhitespace_character_with_correct_offsets(strategy, limit):
    source = load_document(FIXTURE)[0]
    chunks = chunk_page(source, strategy=strategy, max_chars=limit)
    covered = set()
    previous_end = 0
    for index, chunk in enumerate(chunks):
        assert 0 < len(chunk.text) <= limit
        assert chunk.text == source.text[chunk.start_char : chunk.end_char]
        assert chunk.start_char >= previous_end
        assert chunk.chunk_index == index
        assert chunk.document_id == source.document_id
        assert chunk.source == source.source
        covered.update(range(chunk.start_char, chunk.end_char))
        previous_end = chunk.end_char
    assert all(
        position in covered for position, char in enumerate(source.text) if not char.isspace()
    )
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_paragraph_strategy_avoids_splitting_fitting_paragraph():
    source = page("First one.\n\nSecond one.\n\nThird one.")
    paragraphs = chunk_page(source, strategy="paragraph", max_chars=20)
    fixed = chunk_page(source, strategy="fixed", max_chars=20)
    assert [chunk.text for chunk in paragraphs] == [
        "First one.\n\n",
        "Second one.\n\n",
        "Third one.",
    ]
    assert "".join(chunk.text for chunk in fixed) == source.text
    assert fixed[0].text.endswith("Second o")


def test_oversized_paragraph_makes_progress_without_losing_text():
    source = page("x" * 35)
    assert [len(c.text) for c in chunk_page(source, max_chars=10)] == [10, 10, 10, 5]


@pytest.mark.parametrize("strategy", ["fixed", "paragraph"])
def test_blank_pages_and_empty_corpus(strategy):
    assert chunk_document([], strategy=strategy) == []
    assert chunk_page(page(" \n\t"), strategy=strategy, max_chars=1) == []


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "10"])
def test_invalid_size_rejected_even_for_empty_input(limit):
    with pytest.raises(ValueError, match="max_chars"):
        chunk_document([], max_chars=limit)


def test_invalid_strategy():
    with pytest.raises(ValueError, match="strategy"):
        chunk_page(page("text"), strategy="unknown")


def test_ids_stable_but_distinguish_source_input_and_configuration():
    source = page("Café\n\nहिन्दी and dose 0.5 mg")
    before = asdict(source)
    chunks = chunk_page(source, max_chars=10)
    assert chunks == chunk_page(source, max_chars=10)
    assert chunks[0].chunk_id != chunk_page(source, strategy="fixed", max_chars=10)[0].chunk_id
    assert (
        chunks[0].chunk_id != chunk_page(replace(source, text="changed"), max_chars=10)[0].chunk_id
    )
    assert (
        chunks[0].chunk_id
        != chunk_page(replace(source, document_id="other"), max_chars=10)[0].chunk_id
    )
    assert asdict(source) == before
    chunks[0].metadata["version"] = "changed"
    assert source.metadata["version"] == "1"
    assert chunks[1].metadata["version"] == "1"


def test_cleaned_offsets_reference_cleaned_input():
    original = page("  Café\t   guide\r\n\r\nSecond paragraph")
    cleaned = clean_page(original)
    for chunk in chunk_page(cleaned, max_chars=12):
        assert chunk.input_kind == "cleaned"
        assert chunk.text == cleaned.text[chunk.start_char : chunk.end_char]
    assert cleaned.original_text == original.text


def test_pdf_page_positions_remain_distinct(tmp_path):
    path = tmp_path / "guide.pdf"
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "Same passage")
        doc.new_page()
        doc.new_page().insert_text((72, 72), "Same passage")
        doc.save(path)
    chunks = chunk_document(load_document(path))
    assert [chunk.page_number for chunk in chunks] == [1, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 0]
    assert chunks[0].chunk_id != chunks[1].chunk_id


def test_cli_chunking_is_opt_in(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE)])
    assert main() == 0
    assert "chunk_id" not in json.loads(capsys.readouterr().out)[0]
    monkeypatch.setattr(
        "sys.argv", ["load", str(FIXTURE), "--clean", "--chunk", "--max-chars", "80"]
    )
    assert main() == 0
    chunks = json.loads(capsys.readouterr().out)
    assert all(c["input_kind"] == "cleaned" and len(c["text"]) <= 80 for c in chunks)


def test_cli_rejects_invalid_limit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE), "--chunk", "--max-chars", "0"])
    assert main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "positive integer" in output.err


def test_cli_requires_chunk_flag_for_options(monkeypatch):
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE), "--max-chars", "20"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_comparison_reports_actual_paragraph_splits(tmp_path):
    from experiments.chunking_comparison import compare

    path = tmp_path / "paragraphs.txt"
    path.write_text("First one.\n\nSecond one.\n\nThird one.", encoding="utf-8")
    report = compare(path, max_chars=20)
    fixed, paragraph = report["measurements"]
    assert fixed["paragraph_count"] == paragraph["paragraph_count"] == 3
    assert fixed["split_paragraphs"] == 1
    assert paragraph["split_paragraphs"] == 0
    assert fixed["chunk_count"] == 2
    assert paragraph["chunk_count"] == 3


def test_paragraph_boundaries_support_crlf_without_changing_input():
    source = page("First one.\r\n\r\nSecond one.")
    chunks = chunk_page(source, max_chars=20)
    assert [chunk.text for chunk in chunks] == ["First one.\r\n\r\n", "Second one."]
    assert "".join(chunk.text for chunk in chunks) == source.text


def test_tag_chunks_keeps_source_metadata_next_to_text():
    tagged = tag_chunks(
        "refund-policy.pdf",
        [("Refunds are available within 30 days.", 12), ("Exceptions apply.", 58)],
        metadata={"section": "Eligibility", "effective_date": "2026-01-01"},
    )

    assert tagged == [
        {
            "text": "Refunds are available within 30 days.",
            "metadata": {
                "source": "refund-policy.pdf",
                "chunk_index": 0,
                "char_start": 12,
                "section": "Eligibility",
                "effective_date": "2026-01-01",
            },
        },
        {
            "text": "Exceptions apply.",
            "metadata": {
                "source": "refund-policy.pdf",
                "chunk_index": 1,
                "char_start": 58,
                "section": "Eligibility",
                "effective_date": "2026-01-01",
            },
        },
    ]


def test_tag_chunks_supports_missing_offsets_and_isolates_metadata():
    metadata = {"page": 3}
    tagged = tag_chunks("guide.md", ["First", "Second"], metadata=metadata)

    assert [chunk["metadata"]["char_start"] for chunk in tagged] == [None, None]
    tagged[0]["metadata"]["page"] = 4
    assert metadata["page"] == 3


@pytest.mark.parametrize(
    "chunks",
    [[("text", -1)], [("text", "1")], [("text",)], [3]],
)
def test_tag_chunks_rejects_invalid_chunks(chunks):
    with pytest.raises(ValueError):
        tag_chunks("guide.md", chunks)
