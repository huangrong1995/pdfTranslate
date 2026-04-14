"""FastAPI 主服务 - PDF 翻译工具"""
import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .pdf_processor import extract_text_from_pdf
from .translator import translate_text

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


class TranslateRequest(BaseModel):
    direction: str = "en2zh"


class TranslateResponse(BaseModel):
    success: bool
    original_text: str
    translated_text: str
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

        # 2. 翻译
        translated_text = await translate_text(original_text, direction)

        # 3. 保存翻译结果到文件
        download_filename = f"{uuid.uuid4().hex}.txt"
        download_path = TRANSLATED_DIR / download_filename

        with open(download_path, "w", encoding="utf-8") as f:
            f.write(f"=== 原文 ===\n{original_text}\n\n=== 译文 ===\n{translated_text}")

        return TranslateResponse(
            success=True,
            original_text=original_text,
            translated_text=translated_text,
            download_filename=download_filename
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
