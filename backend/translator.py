"""翻译模块 - 支持 Ollama 本地模型和阿里云百炼 API"""
import os
import httpx
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ollama 配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_0"

# 阿里云百炼 API 配置
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = "qwen-plus"


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


async def check_ollama_available() -> bool:
    """检查 Ollama 服务是否可用"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def translate_chunk_with_ollama(chunk: str, direction: str) -> str:
    """
    使用 Ollama 翻译单个文本块

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
                "model": OLLAMA_MODEL,
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


async def translate_chunk_with_dashscope(chunk: str, direction: str) -> str:
    """
    使用阿里云百炼 API 翻译单个文本块

    Args:
        chunk: 待翻译文本块
        direction: 翻译方向

    Returns:
        翻译结果
    """
    if not DASHSCOPE_API_KEY:
        raise ValueError("未设置 DASHSCOPE_API_KEY 环境变量，请设置阿里云百炼 API Key")

    prompt = build_translate_prompt(chunk, direction)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{DASHSCOPE_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DASHSCOPE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "top_p": 0.9,
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()


async def translate_chunk(chunk: str, direction: str) -> str:
    """
    翻译单个文本块（自动选择可用后端）

    优先使用 Ollama，如果 Ollama 不可用且配置了阿里云百炼 API Key，则使用百炼 API。

    Args:
        chunk: 待翻译文本块
        direction: 翻译方向

    Returns:
        翻译结果
    """
    if await check_ollama_available():
        return await translate_chunk_with_ollama(chunk, direction)
    elif DASHSCOPE_API_KEY:
        return await translate_chunk_with_dashscope(chunk, direction)
    else:
        raise RuntimeError(
            "Ollama 服务不可用，且未设置 DASHSCOPE_API_KEY 环境变量。\n"
            "请确保 Ollama 服务正在运行，或设置阿里云百炼 API Key：\n"
            "export DASHSCOPE_API_KEY='your-api-key'"
        )


async def translate_text_structured(text: str, direction: str, progress_callback=None) -> list[dict]:
    """
    翻译文本并返回段落对照结构

    Args:
        text: 待翻译文本
        direction: 翻译方向
        progress_callback: 进度回调函数，接受 (已完成数, 总数, 段落数据) 参数

    Returns:
        [{original: str, translated: str}, ...] 段落对照列表
    """
    from .pdf_processor import split_into_chunks

    chunks = split_into_chunks(text)
    total = len(chunks)
    results = []

    for i, chunk in enumerate(chunks):
        translated = await translate_chunk(chunk, direction)
        result = {
            "original": chunk,
            "translated": translated
        }
        results.append(result)

        if progress_callback:
            await progress_callback(i + 1, total, result)

    return results


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
