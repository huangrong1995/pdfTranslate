"""Ollama 翻译模块"""
import httpx
import asyncio
from typing import AsyncGenerator


OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b-instruct-q4_0"


def build_translate_prompt(text: str, direction: str) -> str:
    """
    构建翻译提示词

    Args:
        text: 待翻译文本
        direction: 翻译方向，en2zh 或 zh2en
    """
    if direction == "en2zh":
        return f"""你是一个专业的翻译官。请将以下英文文本翻译成中文，保持原文格式，只输出翻译结果，不要添加任何解释或注释。

原文：
{text}

中文翻译："""
    else:
        return f"""你是一个专业的翻译官。请将以下中文文本翻译成英文，保持原文格式，只输出翻译结果，不要添加任何解释或注释。

原文：
{text}

English translation："""


async def translate_chunk(chunk: str, direction: str) -> str:
    """
    翻译单个文本块

    Args:
        chunk: 待翻译文本块
        direction: 翻译方向

    Returns:
        翻译结果
    """
    prompt = build_translate_prompt(chunk, direction)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["response"].strip()


async def translate_text(text: str, direction: str) -> str:
    """
    翻译完整文本（自动分块）

    Args:
        text: 待翻译文本
        direction: 翻译方向

    Returns:
        翻译结果
    """
    from .pdf_processor import split_into_chunks

    chunks = split_into_chunks(text)
    translated_chunks = []

    for i, chunk in enumerate(chunks):
        translated = await translate_chunk(chunk, direction)
        translated_chunks.append(translated)

    return "\n\n".join(translated_chunks)


async def translate_text_stream(
    text: str,
    direction: str,
    progress_callback=None
) -> AsyncGenerator[tuple[int, str], None]:
    """
    流式翻译文本，带进度回调

    Args:
        text: 待翻译文本
        direction: 翻译方向
        progress_callback: 进度回调函数，接受 (已完成块数, 总块数, 翻译结果) 参数

    Yields:
        (chunk_index, translated_chunk) 元组
    """
    from .pdf_processor import split_into_chunks

    chunks = split_into_chunks(text)
    total = len(chunks)
    results = []

    for i, chunk in enumerate(chunks):
        translated = await translate_chunk(chunk, direction)
        results.append(translated)

        if progress_callback:
            await progress_callback(i + 1, total, translated)

        yield i, translated

    if progress_callback:
        await progress_callback(total, total, "\n\n".join(results))
