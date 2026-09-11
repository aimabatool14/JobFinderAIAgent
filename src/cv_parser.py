"""
CV Parser module for JobFinder AI.
Safely extracts clean plain text from PDF, DOCX, TXT, and Markdown files.
Designed for Streamlit UploadedFile objects, in-memory stream processing,
strict validation, and user-friendly error messages without raw tracebacks.
"""

import os
import io
import re
import logging
from typing import Tuple, Union, Any

logger = logging.getLogger("JobFinderAI.CVParser")

# Allowed CV formats
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

# File size limits (10 MB maximum, 1 byte minimum)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MIN_EXTRACTED_WORDS = 10


class CVParserError(Exception):
    """
    Application-level exception for CV parsing errors.
    Always provides friendly, actionable guidance rather than exposing raw tracebacks.
    """
    pass


def clean_extracted_text(text: str) -> str:
    """
    Normalize line endings, collapse excessive whitespace, and strip unprintable characters.
    """
    if not text:
        return ""
    # Normalize carriage returns and non-breaking spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    # Collapse 3 or more consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove unprintable non-ASCII control codes (preserve \t and \n)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Decode plain text or markdown file bytes with progressive fallback encodings.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return file_bytes.decode(enc).strip()
        except UnicodeDecodeError:
            continue

    raise CVParserError(
        "Could not decode the text file. Please save your file as standard UTF-8 encoded text and try again."
    )


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF using pypdf / PyPDF2 with pure-Python stream fallback.
    Detects empty pages, scanned image PDFs without OCR, and corrupt files.
    """
    # 1. Try modern pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        if len(reader.pages) == 0:
            raise CVParserError("The uploaded PDF file contains no pages.")

        extracted_pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_pages.append(t.strip())

        full_text = "\n\n".join(extracted_pages).strip()
        if not full_text:
            raise CVParserError(
                "The PDF appears to be a scanned image or contains no selectable text. "
                "Please upload a text-searchable PDF, Word document (.docx), or plain text file."
            )
        return full_text
    except CVParserError:
        raise
    except ImportError:
        pass
    except Exception as e:
        logger.error("pypdf error reading PDF: %s", e)
        raise CVParserError(
            "Unable to read this PDF file (it may be corrupted or password-protected). "
            "Please ensure the document is not password-protected or try converting it to DOCX or TXT."
        )

    # 2. Try legacy PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
        full_text = "\n\n".join(extracted_pages).strip()
        if not full_text:
            raise CVParserError(
                "The PDF contains no selectable text. Please upload a text-based document."
            )
        return full_text
    except CVParserError:
        raise
    except ImportError:
        pass
    except Exception as e:
        logger.error("PyPDF2 error: %s", e)
        raise CVParserError(
            "Could not parse this PDF file. Please verify it is a valid, readable PDF."
        )

    # 3. Fallback: Standard library basic text stream scanner
    try:
        raw_str = file_bytes.decode("latin-1", errors="ignore")
        # Extract text within standard PDF text blocks (BT ... ET)
        text_matches = re.findall(r"\(([^\(\)\\]+)\)\s*Tj", raw_str)
        if text_matches:
            full_text = " ".join(text_matches).strip()
            if len(full_text.split()) >= 10:
                return full_text
    except Exception:
        pass

    raise CVParserError(
        "PDF extraction library is not available in the current environment. "
        "Please upload your CV as a Word Document (.docx) or plain text (.txt) file."
    )


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX using python-docx with pure-Python zipfile/XML fallback.
    Reads both paragraph bodies and table contents.
    """
    # 1. Try python-docx
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Also extract table cells
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    paragraphs.append(row_text)

        full_text = "\n".join(paragraphs).strip()
        if not full_text:
            raise CVParserError("The uploaded Word document contains no readable text.")
        return full_text
    except CVParserError:
        raise
    except ImportError:
        pass
    except Exception as e:
        logger.error("python-docx reading error: %s", e)
        raise CVParserError(
            "The Word document (.docx) could not be read (it may be corrupted or in legacy .doc binary format). "
            "Please save as modern .docx or export as PDF/TXT."
        )

    # 2. Pure-Python fallback using zipfile and XML parsing (zero external dependencies)
    try:
        import zipfile
        import xml.etree.ElementTree as ET

        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            xml_content = zf.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            text_parts = []
            for node in tree.iter():
                if node.tag.endswith("t") and node.text:
                    text_parts.append(node.text)
            full_text = " ".join(text_parts).strip()
            if not full_text:
                raise CVParserError("The Word document (.docx) contains no readable text.")
            return full_text
    except CVParserError:
        raise
    except Exception as ex:
        logger.error("DOCX XML extraction error: %s", ex)
        raise CVParserError(
            "The Word document could not be read. Please ensure it is a valid .docx file, or upload as PDF or TXT."
        )


def _resolve_file_input(uploaded_file: Any) -> Tuple[str, bytes]:
    """
    Safely extract filename and bytes from various input shapes:
    - Streamlit UploadedFile (has .name, .size, and .getvalue() or .read())
    - (filename, bytes) tuple
    - Object with .name and .getvalue()
    """
    if uploaded_file is None:
        raise CVParserError("No file provided. Please select a CV to upload.")

    # Shape 1: Tuple of (filename, bytes)
    if isinstance(uploaded_file, tuple) and len(uploaded_file) == 2:
        name, data = uploaded_file
        return str(name), bytes(data) if isinstance(data, (bytes, bytearray)) else bytes(data or b"")

    # Shape 2: Streamlit UploadedFile or file-like object
    name = getattr(uploaded_file, "name", None)
    if not name:
        raise CVParserError("Invalid file input: unable to determine filename.")

    # Get file bytes
    if hasattr(uploaded_file, "getvalue"):
        file_bytes = uploaded_file.getvalue()
    elif hasattr(uploaded_file, "read"):
        file_bytes = uploaded_file.read()
        # Reset pointer if seekable
        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
    else:
        raise CVParserError("Invalid file input: unable to read file contents.")

    if not isinstance(file_bytes, (bytes, bytearray)):
        file_bytes = bytes(file_bytes or b"")

    return str(name), file_bytes


def parse_cv(uploaded_file: Any) -> str:
    """
    Primary interface for parsing an uploaded CV file.
    Accepts a Streamlit UploadedFile or file-like object.
    
    Performs:
    1. File extension validation (.pdf, .docx, .txt, .md)
    2. File size validation (non-empty, <= 10MB)
    3. Safe in-memory text extraction without saving to disk
    4. Empty extraction detection
    5. Clean text whitespace normalization
    6. Application-level error handling without exposing Python tracebacks

    Returns:
        Clean extracted text string.

    Raises:
        CVParserError: On validation or extraction failure with user-friendly message.
    """
    clean_text, _ = parse_cv_file_detailed(uploaded_file)
    return clean_text


def parse_cv_file(file_name: str, file_bytes: bytes) -> Tuple[str, str]:
    """
    Convenience interface accepting (file_name, file_bytes).
    Returns (clean_text, format_label).
    """
    return parse_cv_file_detailed((file_name, file_bytes))


def parse_cv_file_detailed(uploaded_file: Any) -> Tuple[str, str]:
    """
    Internal detailed parser returning (clean_text, format_label).
    """
    file_name, file_bytes = _resolve_file_input(uploaded_file)

    # 1. Validate file size: minimum 1 byte
    if len(file_bytes) == 0:
        raise CVParserError("The uploaded file is empty (0 bytes). Please select a valid document.")

    # 2. Validate file size: maximum 10 MB
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        mb_size = len(file_bytes) / (1024 * 1024)
        raise CVParserError(
            f"The uploaded file ({mb_size:.1f} MB) exceeds the maximum allowed size of 10 MB. "
            f"Please compress or trim your resume and try again."
        )

    # 3. Validate file extension
    _, ext = os.path.splitext(file_name.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        supported_str = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise CVParserError(
            f"Unsupported file extension '{ext or 'none'}'. "
            f"JobFinder AI supports the following formats: {supported_str}."
        )

    # 4. Extract text safely according to format
    raw_text = ""
    format_label = "Document"

    try:
        if ext == ".pdf":
            raw_text = extract_text_from_pdf(file_bytes)
            format_label = "PDF Document"
        elif ext == ".docx":
            raw_text = extract_text_from_docx(file_bytes)
            format_label = "Word Document (.docx)"
        elif ext in {".txt", ".md"}:
            raw_text = extract_text_from_txt(file_bytes)
            format_label = "Text Document"
    except CVParserError:
        raise
    except Exception as exc:
        logger.error("Unexpected parsing error on %s: %s", file_name, exc)
        raise CVParserError(
            f"Could not read the contents of '{file_name}'. "
            f"Please check that the file is not corrupted or try uploading in TXT format."
        )

    # 5. Clean text
    clean_text = clean_extracted_text(raw_text)

    # 6. Detect empty extraction or insufficient content
    if not clean_text or len(clean_text.strip()) == 0:
        raise CVParserError(
            f"No text could be extracted from '{file_name}'. "
            f"If this is a scanned document or image PDF, please provide a text-searchable version or paste text directly."
        )

    word_count = len(clean_text.split())
    if word_count < MIN_EXTRACTED_WORDS:
        raise CVParserError(
            f"The document '{file_name}' contains only {word_count} word(s). "
            f"A valid CV should include your experience, education, or skills summary."
        )

    return clean_text, format_label
