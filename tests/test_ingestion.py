"""Offline intake contract tests using synthetic documents."""

import json
from pathlib import Path

import pymupdf
import pytest

from healthcompass.ingestion import DocumentLoadError, load_document
from healthcompass.ingestion.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "guidance.txt"


def test_txt_preserves_text_metadata_and_identity(tmp_path):
    metadata = {"version": "2", "region": "District A"}
    page = load_document(FIXTURE, metadata=metadata)[0]
    assert page.text == FIXTURE.read_text(encoding="utf-8")
    assert page.page_number is None
    assert page.source == str(FIXTURE.resolve())
    assert page.filename == "guidance.txt"
    metadata["version"] = "3"
    assert page.metadata["version"] == "2"
    copy = tmp_path / "copy.TXT"
    copy.write_bytes(FIXTURE.read_bytes())
    assert load_document(copy)[0].document_id == page.document_id
    copy.write_text("Changed guidance", encoding="utf-8")
    assert load_document(copy)[0].document_id != page.document_id


def test_pdf_preserves_blank_pages_and_positions(tmp_path):
    path = tmp_path / "guidance.PDF"
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "First section")
        doc.new_page()
        doc.new_page().insert_text((72, 72), "Third section")
        doc.save(path)
    pages = load_document(path, metadata={"version": "2"})
    assert [page.page_number for page in pages] == [1, 2, 3]
    assert "First section" in pages[0].text
    assert pages[1].text == ""
    assert "Third section" in pages[2].text
    assert len({page.document_id for page in pages}) == 1
    pages[0].metadata["version"] = "changed"
    assert pages[2].metadata["version"] == "2"


@pytest.mark.parametrize(
    "name,content,message",
    [
        ("empty.txt", b"", "empty"),
        ("blank.txt", b" \n\t", "no extractable text"),
        ("invalid.txt", b"\xff", "UTF-8"),
        ("broken.pdf", b"not a PDF", "invalid or damaged"),
        ("other.csv", b"a,b", "Unsupported file type"),
    ],
)
def test_invalid_documents(tmp_path, name, content, message):
    path = tmp_path / name
    path.write_bytes(content)
    with pytest.raises(DocumentLoadError, match=message):
        load_document(path)


def test_missing_file_and_directory(tmp_path):
    with pytest.raises(DocumentLoadError, match="Cannot read"):
        load_document(tmp_path / "missing.txt")
    directory = tmp_path / "directory.txt"
    directory.mkdir()
    with pytest.raises(DocumentLoadError, match="Cannot read"):
        load_document(directory)


def test_utf8_bom(tmp_path):
    path = tmp_path / "bom.txt"
    path.write_bytes(b"\xef\xbb\xbfGuidance")
    assert load_document(path)[0].text == "Guidance"


@pytest.mark.parametrize("encrypted", [False, True])
def test_unusable_pdf(tmp_path, encrypted):
    path = tmp_path / "document.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        kwargs = (
            {"encryption": pymupdf.PDF_ENCRYPT_AES_256, "owner_pw": "owner", "user_pw": "reader"}
            if encrypted
            else {}
        )
        doc.save(path, **kwargs)
    with pytest.raises(DocumentLoadError, match="Password-protected" if encrypted else "OCR"):
        load_document(path)


def test_cli_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["healthcompass-load", str(FIXTURE), "--metadata", '{"region":"District A"}']
    )
    assert main() == 0
    output = capsys.readouterr()
    assert json.loads(output.out)[0]["metadata"] == {"region": "District A"}
    assert output.err == ""


@pytest.mark.parametrize("metadata", ["{", "[]", '{"version":2}'])
def test_cli_invalid_metadata(monkeypatch, capsys, metadata):
    monkeypatch.setattr("sys.argv", ["healthcompass-load", str(FIXTURE), "--metadata", metadata])
    assert main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Document loading error" in output.err
