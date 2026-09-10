"""Cleaning must preserve guidance content and source traceability."""

from dataclasses import asdict
import json
from pathlib import Path

import pymupdf
import pytest

from healthcompass.ingestion import clean_page, clean_text, load_document
from healthcompass.ingestion.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "messy_guidance.txt"


def test_normalization_preserves_paragraphs_numbers_and_lists():
    page = load_document(FIXTURE, metadata={"version": "2"})[0]
    before = asdict(page)
    cleaned = clean_page(page, boilerplate_lines=["DRAFT HEADER", "DRAFT FOOTER"])
    assert cleaned.text == (
        "Café guidance\nKeep 0.5 mg; do not exceed 5 mg.\n\n"
        "- Region: District A\nVersion: 2.0")
    assert cleaned.original_text == page.text
    assert asdict(page) == before
    for field in ["document_id", "source", "filename", "page_number", "metadata"]:
        assert getattr(cleaned, field) == getattr(page, field)
    assert cleaned.removed_boilerplate_lines == ("DRAFT HEADER", "DRAFT FOOTER")
    assert cleaned.warnings == ()
    cleaned.metadata["version"] = "changed"
    assert page.metadata["version"] == "2"


def test_configured_line_is_not_removed_from_body_or_substrings():
    text = "HEADER\nTitle\nHEADER\nHEADER is meaningful here\nFOOTER"
    assert clean_text(text, boilerplate_lines=["HEADER", "FOOTER"]) == (
        "Title\nHEADER\nHEADER is meaningful here")
    assert clean_text(text).startswith("HEADER")


@pytest.mark.parametrize("text", [
    " a\t b\r\n\r\n\r\nc ", "Café\u00a0guide", "\ufeffa\x00b", "", "\r\n\t",
    "HEADER\nHEADER\n\nBody\nFOOTER\nFOOTER",
])
def test_cleaning_is_idempotent(text):
    once = clean_text(text, boilerplate_lines=["HEADER", "FOOTER"])
    assert clean_text(once, boilerplate_lines=["HEADER", "FOOTER"]) == once


def test_unicode_symbols_negation_and_word_boundaries_survive():
    text = "Do not use >5 mg/m²; ≤0.5 µg.\nहिन्दी\nnon-\nclinical\n5\x00mg"
    assert clean_text(text) == text.replace("\x00", " ")
    assert clean_text("a\u2028b\u2029c\fd") == "a\nb\n\nc\n\nd"


@pytest.mark.parametrize("entries", ["HEADER", [""], ["\n"], ["a\nb"], [3]])
def test_invalid_boilerplate_configuration(entries):
    with pytest.raises(ValueError):
        clean_text("body", boilerplate_lines=entries)


def test_pdf_pages_remain_traceable_including_empty_pages(tmp_path):
    path = tmp_path / "pages.pdf"
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "HEADER\nFirst  section\nFOOTER")
        doc.new_page()
        doc.new_page().insert_text((72, 72), "HEADER\nSecond section\nFOOTER")
        doc.save(path)
    raw = load_document(path)
    cleaned = [clean_page(page, boilerplate_lines=["HEADER", "FOOTER"]) for page in raw]
    assert [p.page_number for p in cleaned] == [1, 2, 3]
    assert [p.text for p in cleaned] == ["First section", "", "Second section"]
    assert cleaned[1].warnings == ("empty_after_cleaning",)
    assert [p.original_text for p in cleaned] == [p.text for p in raw]
    assert {p.document_id for p in cleaned} == {raw[0].document_id}


def test_entire_page_removed_is_flagged_and_can_be_recleaned(tmp_path):
    path = tmp_path / "header.txt"
    path.write_text("HEADER", encoding="utf-8")
    raw = load_document(path)[0]
    cleaned = clean_page(raw, boilerplate_lines=["HEADER"])
    assert cleaned.text == ""
    assert cleaned.warnings == ("empty_after_cleaning",)
    assert clean_page(cleaned).text == "HEADER"
    assert clean_page(cleaned).original_text == raw.text


def test_cli_cleaning_is_opt_in(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE)])
    assert main() == 0
    raw = json.loads(capsys.readouterr().out)[0]
    assert "original_text" not in raw
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE), "--clean",
                                    "--remove-boilerplate-line", "DRAFT HEADER"])
    assert main() == 0
    clean = json.loads(capsys.readouterr().out)[0]
    assert clean["original_text"] == raw["text"]
    assert clean["document_id"] == raw["document_id"]
    assert not clean["text"].startswith("DRAFT HEADER")
    assert clean["removed_boilerplate_lines"] == ["DRAFT HEADER"]


def test_cli_rejects_removal_without_clean(monkeypatch):
    monkeypatch.setattr("sys.argv", ["load", str(FIXTURE), "--remove-boilerplate-line", "HEADER"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
