"""Word 文档文本提取模块"""
from docx import Document
import io


def extract_text_from_docx(docx_file) -> str:
    """
    从上传的 Word 文档中提取文本内容

    Args:
        docx_file: 上传的 Word 文件对象 (FastAPI UploadFile)

    Returns:
        提取的文本内容
    """
    content = docx_file.file.read()
    docx_file.file.seek(0)

    stream = io.BytesIO(content)
    doc = Document(stream)

    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n\n'.join(paragraphs)