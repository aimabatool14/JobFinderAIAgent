"""
Comprehensive unit tests for the CV upload and parsing system.
Tests:
- Valid PDF (with mocked/real reader)
- Valid DOCX (generated in-memory)
- Valid TXT (UTF-8)
- Unsupported file extensions
- Empty file (0 bytes)
- File size limit (> 10MB)
- Extraction failure (corrupt or unreadable file)
- Empty extraction (no selectable text)
- Streamlit UploadedFile interface compatibility
"""

import io
import zipfile
import unittest
from unittest.mock import patch, MagicMock

from src.cv_parser import (
    parse_cv,
    parse_cv_file,
    parse_cv_file_detailed,
    extract_text_from_txt,
    extract_text_from_docx,
    extract_text_from_pdf,
    clean_extracted_text,
    CVParserError,
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
)


class MockUploadedFile:
    """Emulates a Streamlit UploadedFile object."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data
        self.size = len(data)

    def getvalue(self) -> bytes:
        return self._data

    def read(self) -> bytes:
        return self._data


def create_in_memory_docx(text_content: str) -> bytes:
    """Helper to construct a valid in-memory DOCX file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>'
            f"{text_content}"
            "</w:t></w:r></w:p></w:body></w:document>"
        )
        zf.writestr("word/document.xml", xml)
    return buf.getvalue()


class TestCVParser(unittest.TestCase):

    def test_valid_txt_parsing(self):
        """Test parsing valid TXT with parse_cv."""
        content = (
            "Jane Smith\n"
            "Full Stack Developer\n"
            "Over 4 years of experience delivering robust web applications.\n"
            "Skills: Python, React, TypeScript, Docker, PostgreSQL.\n"
            "Education: B.S. in Computer Science, 2020.\n"
            "Experience: Software Engineer at AcroTech from 2020 to Present."
        )
        mock_file = MockUploadedFile("jane_resume.txt", content.encode("utf-8"))
        extracted = parse_cv(mock_file)
        self.assertIn("Jane Smith", extracted)
        self.assertIn("Full Stack Developer", extracted)
        self.assertIn("PostgreSQL", extracted)

    def test_valid_docx_parsing(self):
        """Test parsing valid DOCX generated in memory."""
        sample_body = (
            "Alex Morgan Senior Software Engineer with eight years of Python, "
            "Docker, microservices architecture, and cloud infrastructure experience."
        )
        docx_bytes = create_in_memory_docx(sample_body)
        mock_file = MockUploadedFile("alex_resume.docx", docx_bytes)
        extracted = parse_cv(mock_file)
        self.assertIn("Alex Morgan", extracted)
        self.assertIn("microservices architecture", extracted)

    def test_valid_pdf_parsing_mocked(self):
        """Test parsing valid PDF using mocked reader to test integration."""
        sample_pdf_text = (
            "Jordan Lee\n"
            "Machine Learning Engineer with 5 years experience in PyTorch, "
            "Transformer architectures, NLP pipelines, and distributed model training."
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = sample_pdf_text

        mock_reader_cls = MagicMock()
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_cls.return_value = mock_reader_instance

        with patch.dict("sys.modules", {"pypdf": MagicMock(PdfReader=mock_reader_cls)}):
            mock_file = MockUploadedFile("jordan_cv.pdf", b"%PDF-1.4 mock bytes")
            extracted = parse_cv(mock_file)
            self.assertIn("Jordan Lee", extracted)
            self.assertIn("Transformer architectures", extracted)

    def test_unsupported_file_extension(self):
        """Test rejection of unsupported file extensions."""
        mock_file = MockUploadedFile("malicious.exe", b"binary content")
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_file)
        self.assertIn("Unsupported file extension", str(ctx.exception))

        mock_png = MockUploadedFile("resume.png", b"image data")
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_png)
        self.assertIn("Unsupported file extension", str(ctx.exception))

    def test_empty_file_zero_bytes(self):
        """Test rejection of 0-byte uploaded files."""
        mock_file = MockUploadedFile("empty.txt", b"")
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_file)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_file_exceeds_maximum_size(self):
        """Test rejection of files exceeding the 10 MB limit."""
        huge_bytes = b"a" * (MAX_FILE_SIZE_BYTES + 1024)
        mock_file = MockUploadedFile("oversized.txt", huge_bytes)
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_file)
        self.assertIn("exceeds the maximum allowed size", str(ctx.exception))

    def test_extraction_failure_corrupt_docx(self):
        """Test extraction failure on corrupted DOCX binary bytes."""
        mock_file = MockUploadedFile("corrupted.docx", b"not a valid zip file")
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_file)
        self.assertIn("Word document could not be read", str(ctx.exception))

    def test_empty_extraction_scanned_pdf(self):
        """Test detection of scanned PDF with no extractable text."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # No OCR text

        mock_reader_cls = MagicMock()
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_cls.return_value = mock_reader_instance

        with patch.dict("sys.modules", {"pypdf": MagicMock(PdfReader=mock_reader_cls)}):
            mock_file = MockUploadedFile("scanned.pdf", b"%PDF-1.4 mock")
            with self.assertRaises(CVParserError) as ctx:
                parse_cv(mock_file)
            self.assertIn("scanned image or contains no selectable text", str(ctx.exception))

    def test_extraction_too_few_words(self):
        """Test document containing too few words to be a legitimate CV."""
        mock_file = MockUploadedFile("too_short.txt", b"Hello World only four words")
        with self.assertRaises(CVParserError) as ctx:
            parse_cv(mock_file)
        self.assertIn("contains only 5 word(s)", str(ctx.exception))

    def test_clean_extracted_text_whitespace(self):
        """Test whitespace cleaning and control code stripping."""
        messy = "Title\r\n\r\n\r\n\r\nSubtitle\x00\x08 with \u00a0 special spaces"
        cleaned = clean_extracted_text(messy)
        self.assertIn("Title\n\nSubtitle", cleaned)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\r", cleaned)

    def test_parse_cv_file_tuple_interface(self):
        """Test backwards compatibility with parse_cv_file(name, bytes)."""
        content = (
            "Taylor Swift\n"
            "Creative Lead and Technical Director with 10 years experience "
            "managing cross-functional production teams and high-scale releases."
        )
        text, format_name = parse_cv_file("taylor.txt", content.encode("utf-8"))
        self.assertIn("Taylor Swift", text)
        self.assertEqual(format_name, "Text Document")


if __name__ == "__main__":
    unittest.main()
