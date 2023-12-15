import hashlib
from io import BytesIO
from typing import List

import fitz  # pymupdf importing name

__version__ = '1.4.0'
__changelog__ = """
1.4.0 2023.11.06
get_text_all_pages: updated pymupdf deprecated property (pageCount to page_count)
1.3.0 2023.10.24
_get_text_from_page: updated pymupdf deprecated methods
1.2.0
_get_text_from_page: "html" data format support
1.1.0
get_text_all_pages
"""

FLAGS_DEFAULT = fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE


def _get_text_from_page(
        pdf: fitz.Document,
        page_ix: int,
        data_format='',
        flags=FLAGS_DEFAULT) -> str:
    text_page = pdf.load_page(page_ix).get_displaylist().get_textpage(flags)
    if data_format == "json":
        text = text_page.extractJSON()
    elif data_format == "dict":
        text = text_page.extractDICT()
    elif data_format == "html":
        text = text_page.extractHTML()
    else:
        text = text_page.extractText()
    return text


def get_text(pdf_content: bytes, data_format: str = '') -> str:
    """Extracts text from the _first_ page of PDF document (fast)
    :param pdf_content:
    :param data_format: '' or 'json' or 'dict'
    """
    if not pdf_content:
        return ''
    pdf = fitz.Document(stream=pdf_content, filetype="pdf")
    text = _get_text_from_page(pdf, 0, data_format=data_format)
    return text


def get_text_all_pages(pdf_contents: List[bytes], data_format: str = '') -> List[str]:
    """Extracts text from _all_ pages of PDF document (fast)
    :param pdf_contents: [pdf_content] -- from all pdf resps (suitable for multi-file PDF)
    :param data_format: '' or 'json' or 'dict'
    """
    if not pdf_contents:
        return []
    texts_all_pages = []  # type: List[str]
    for pdf_content in pdf_contents:
        pdf = fitz.Document(stream=pdf_content, filetype="pdf")
        for page_ix in range(pdf.page_count):
            text = _get_text_from_page(pdf, page_ix, data_format=data_format)
            texts_all_pages.append(text)
    return texts_all_pages


def calc_checksum(pdf_content: bytes) -> str:
    hash_md5 = hashlib.md5()
    f = BytesIO(pdf_content)
    for chunk in iter(lambda: f.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()
