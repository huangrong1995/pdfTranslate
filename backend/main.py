"""FastAPI 主服务 - PDF 翻译工具"""
import os
import uuid
import asyncio
import json
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .pdf_processor import extract_text_from_pdf
from .translator import translate_text_structured

app = FastAPI(title="PDF Translator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

TRANSLATED_DIR = Path("translated")
TRANSLATED_DIR.mkdir(exist_ok=True)


class ParagraphPair(BaseModel):
    original: str
    translated: str


class TranslateResponse(BaseModel):
    success: bool
    original_text: str
    translated_text: str
    paragraphs: List[ParagraphPair]
    download_filename: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_pdf(
    file: UploadFile = File(...),
    direction: str = "en2zh"
):
    """
    翻译上传的 PDF 文件

    Args:
        file: PDF 文件
        direction: 翻译方向 (en2zh 或 zh2en)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    if direction not in ("en2zh", "zh2en"):
        raise HTTPException(status_code=400, detail="direction 必须是 en2zh 或 zh2en")

    try:
        # 1. 提取 PDF 文本
        original_text = extract_text_from_pdf(file)

        if not original_text.strip():
            raise HTTPException(status_code=400, detail="PDF 中没有提取到文本内容")

        # 2. 翻译（返回段落对照列表）
        paragraphs = await translate_text_structured(original_text, direction)

        # 合并所有译文用于下载
        translated_text = "\n\n".join(p["translated"] for p in paragraphs)

        # 3. 保存翻译结果到文件（对比格式）
        download_filename = f"{uuid.uuid4().hex}.txt"
        download_path = TRANSLATED_DIR / download_filename

        with open(download_path, "w", encoding="utf-8") as f:
            for i, p in enumerate(paragraphs):
                f.write(f"=== 段落 {i+1} ===\n")
                f.write(f"【原文】\n{p['original']}\n\n")
                f.write(f"【译文】\n{p['translated']}\n\n")
                f.write("-" * 40 + "\n\n")

        return TranslateResponse(
            success=True,
            original_text=original_text,
            translated_text=translated_text,
            paragraphs=paragraphs,
            download_filename=download_filename
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def progress_callback(completed: int, total: int, result: dict, queue: asyncio.Queue):
    """将进度信息放入队列"""
    await queue.put({
        "completed": completed,
        "total": total,
        "percent": int(completed / total * 100),
        "paragraph": result
    })


@app.post("/api/translate/stream")
async def translate_pdf_stream(
    file: UploadFile = File(...),
    direction: str = "en2zh"
):
    """
    翻译上传的 PDF 文件（SSE 流式进度）

    Args:
        file: PDF 文件
        direction: 翻译方向 (en2zh 或 zh2en)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    if direction not in ("en2zh", "zh2en"):
        raise HTTPException(status_code=400, detail="direction 必须是 en2zh 或 zh2en")

    try:
        # 1. 提取 PDF 文本
        original_text = extract_text_from_pdf(file)

        if not original_text.strip():
            raise HTTPException(status_code=400, detail="PDF 中没有提取到文本内容")

        # 创建进度队列
        queue = asyncio.Queue()

        async def wrapped_translate():
            from .pdf_processor import split_into_chunks
            chunks = split_into_chunks(original_text)
            total = len(chunks)

            # 发送总段落数
            await queue.put({"type": "start", "total": total, "original_text": original_text})

            for i, chunk in enumerate(chunks):
                from .translator import translate_chunk
                translated = await translate_chunk(chunk, direction)
                result = {"original": chunk, "translated": translated}
                await queue.put({
                    "type": "progress",
                    "completed": i + 1,
                    "total": total,
                    "percent": int((i + 1) / total * 100),
                    "paragraph": result
                })

            # 发送完成信号
            await queue.put({"type": "done"})

        async def event_generator():
            # 启动翻译任务
            translate_task = asyncio.create_task(wrapped_translate())

            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=60.0)

                    if data.get("type") == "done":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
                        break

                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"

            await translate_task

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载翻译结果文件"""
    file_path = TRANSLATED_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=f"translation_{filename}",
        media_type="text/plain"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
