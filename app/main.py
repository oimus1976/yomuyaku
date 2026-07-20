from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.sample_data import SAMPLE_RESULT, SAMPLE_TEXT
from app.services.adk_pipeline import organize_and_review
from app.services.gemini_reader import read_document

logger = logging.getLogger("yomuyaku")

BASE_DIR = Path(__file__).resolve().parent
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))
ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}

app = FastAPI(title="ヨムヤク", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"sample_text": SAMPLE_TEXT},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sample")
async def sample():
    return SAMPLE_RESULT.model_dump()


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="PDF、PNG、JPEGのいずれかを選択してください。",
        )

    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ファイルサイズは10MB以下にしてください。")
    if not content:
        raise HTTPException(status_code=400, detail="ファイルが空です。")

    try:
        document = read_document(content, file.content_type)
        result = await organize_and_review(document)
        return result.model_dump()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document analysis failed")
        raise HTTPException(
            status_code=500,
            detail="文書の解析に失敗しました。サンプルでの動作確認もお試しください。",
        ) from exc
