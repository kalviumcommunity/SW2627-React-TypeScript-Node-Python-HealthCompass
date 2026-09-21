from pathlib import Path

import pytest

from healthcompass.ingestion import IngestionResult, ingest


def test_ingest_runs_all_stages_and_reconciles_files(tmp_path):
    (tmp_path / "guide.txt").write_text(
        "Header\n\nPage 1 of 1\n\nA vaccination recommendation.", encoding="utf-8"
    )
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "guide.md").write_text("# Advice\n\nUse the approved source.", encoding="utf-8")
    (tmp_path / "unsupported.csv").write_text("name,value", encoding="utf-8")

    result = ingest(tmp_path, size=20, overlap=2, metadata={"region": "north"})

    assert isinstance(result, IngestionResult)
    assert result.total_files == 3
    assert result.docs == 2
    assert len(result.failures) == 1
    assert result.docs + len(result.failures) == result.total_files
    assert result.chunks
    first = result.chunks[0]
    assert first["text"]
    assert first["metadata"]["source"] == "guide.txt"
    assert first["metadata"]["region"] == "north"
    assert first["metadata"]["token_count"] > 0


def test_ingest_can_be_unpacked(tmp_path):
    path = tmp_path / "guide.txt"
    path.write_text("Short guidance.", encoding="utf-8")

    files, docs, chunks, failures = ingest(tmp_path)

    assert files == [Path(path)]
    assert docs == 1
    assert chunks[0]["text"] == "Short guidance."
    assert failures == []


def test_ingest_keeps_bad_file_isolated(tmp_path):
    (tmp_path / "good.txt").write_text("Good guidance.", encoding="utf-8")
    (tmp_path / "bad.txt").write_bytes(b"\xff")

    result = ingest(tmp_path)

    assert result.docs == 1
    assert result.failures[0][0] == "bad.txt"
    assert "UTF-8" in result.failures[0][1]


def test_ingest_rejects_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="Directory does not exist"):
        ingest(tmp_path / "missing")