"""Offline intake contract tests using synthetic documents."""

import json
from pathlib import Path

import pymupdf
import pytest

from healthcompass.ingestion import DocumentLoadError, load_document, ingest_corpus
from healthcompass.ingestion.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "guidance.txt"


def test_txt_preserves_text_metadata_and_identity(tmp_path):
    metadata = {"version": "2", "region": "District A"}
    page = load_document(FIXTURE, metadata=metadata)[0]
    # Normalize line endings for comparison
    expected_text = FIXTURE.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert page.text == expected_text
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


def test_markdown_loads_successfully(tmp_path):
    """Test that Markdown files load successfully."""
    md_file = tmp_path / "guideline.md"
    md_file.write_text("# Vaccination Guidelines\n\nVaccination guidance should be checked against latest version.", encoding="utf-8")
    pages = load_document(md_file, metadata={"version": "1"})
    assert len(pages) == 1
    assert pages[0].page_number is None
    assert "Vaccination guidance" in pages[0].text
    assert pages[0].filename == "guideline.md"
    assert pages[0].metadata["version"] == "1"


def test_html_loads_successfully(tmp_path):
    """Test that HTML files load successfully."""
    html_file = tmp_path / "advisory.html"
    html_file.write_text("<html><body><h1>Emergency Advisory</h1><p>Vaccination guidance should be checked.</p></body></html>", encoding="utf-8")
    pages = load_document(html_file, metadata={"region": "District A"})
    assert len(pages) == 1
    assert pages[0].page_number is None
    assert "Emergency Advisory" in pages[0].text
    assert "Vaccination guidance" in pages[0].text
    assert pages[0].filename == "advisory.html"
    assert pages[0].metadata["region"] == "District A"


def test_htm_extension_loads_successfully(tmp_path):
    """Test that .htm files load successfully."""
    htm_file = tmp_path / "advisory.htm"
    htm_file.write_text("<html><body><p>Public health guidance.</p></body></html>", encoding="utf-8")
    pages = load_document(htm_file)
    assert len(pages) == 1
    assert "Public health guidance" in pages[0].text
    assert pages[0].filename == "advisory.htm"


def test_unsupported_extension_raises_error(tmp_path):
    """Test that unsupported extensions raise controlled error."""
    unsupported = tmp_path / "data.xyz"
    unsupported.write_text("Unsupported format", encoding="utf-8")
    with pytest.raises(DocumentLoadError, match="Unsupported file type"):
        load_document(unsupported)


def test_corpus_ingestion_with_mixed_formats(tmp_path):
    """Test corpus ingestion with multiple file formats."""
    # Create test files
    (tmp_path / "doc1.txt").write_text("Text document content", encoding="utf-8")
    (tmp_path / "doc2.md").write_text("# Markdown\nContent", encoding="utf-8")
    (tmp_path / "doc3.html").write_text("<html><body>HTML content</body></html>", encoding="utf-8")
    (tmp_path / "doc4.xyz").write_text("Unsupported", encoding="utf-8")
    
    result = ingest_corpus(tmp_path)
    
    assert len(result.loaded) == 3  # 3 successful files
    assert len(result.skipped) == 1  # 1 unsupported file
    assert result.total_files == 4
    
    # Check that source filenames are preserved
    filenames = {page.filename for page in result.loaded}
    assert "doc1.txt" in filenames
    assert "doc2.md" in filenames
    assert "doc3.html" in filenames


def test_corpus_ingestion_continues_after_failure(tmp_path):
    """Test that corpus ingestion continues when one file fails."""
    # Create valid and invalid files
    (tmp_path / "valid.txt").write_text("Valid content", encoding="utf-8")
    (tmp_path / "corrupted.pdf").write_bytes(b"Not a PDF")
    (tmp_path / "another.txt").write_text("Another valid file", encoding="utf-8")
    
    result = ingest_corpus(tmp_path)
    
    # Should load 2 valid files and skip 1 corrupted file
    assert len(result.loaded) == 2
    assert len(result.skipped) == 1
    assert result.total_files == 3
    
    # Check that valid files were loaded despite corrupted file
    filenames = {page.filename for page in result.loaded}
    assert "valid.txt" in filenames
    assert "another.txt" in filenames


def test_empty_markdown_and_html(tmp_path):
    """Test that empty Markdown and HTML files are handled correctly."""
    # Empty Markdown
    empty_md = tmp_path / "empty.md"
    empty_md.write_text("", encoding="utf-8")
    with pytest.raises(DocumentLoadError, match="empty"):
        load_document(empty_md)
    
    # Empty HTML
    empty_html = tmp_path / "empty.html"
    empty_html.write_text("<html><body></body></html>", encoding="utf-8")
    with pytest.raises(DocumentLoadError, match="no extractable text"):
        load_document(empty_html)


def test_source_identity_preserved_in_corpus(tmp_path):
    """Test that source identity is preserved in corpus ingestion."""
    (tmp_path / "test.txt").write_text("Test content", encoding="utf-8")
    
    result = ingest_corpus(tmp_path)
    
    assert len(result.loaded) == 1
    page = result.loaded[0]
    assert page.filename == "test.txt"
    assert page.source.endswith("test.txt")
    assert page.document_id  # Should have a document ID
