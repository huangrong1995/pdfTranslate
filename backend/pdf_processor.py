"""PDF 文本提取模块"""
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import io


def extract_text_from_pdf(pdf_file) -> str:
    """
    从上传的 PDF 文件中提取文本内容

    Args:
        pdf_file: 上传的 PDF 文件对象 (FastAPI UploadFile)

    Returns:
        提取的文本内容
    """
    content = pdf_file.file.read()
    pdf_file.file.seek(0)

    pdf_stream = io.BytesIO(content)
    text = extract_text(pdf_stream, laparams=LAParams())

    return text


def split_into_chunks(text: str, chunk_size: int = 500) -> list[str]:
    """
    将长文本分割成小块，便于分批翻译

    Args:
        text: 待分割文本
        chunk_size: 每块最大字符数

    Returns:
        文本块列表
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_len = len(para)
        current_len = sum(len(c) for c in current_chunk)

        if current_len + para_len + len(current_chunk) > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []

        current_chunk.append(para)

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks
