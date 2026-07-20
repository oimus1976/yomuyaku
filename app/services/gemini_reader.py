from __future__ import annotations

import base64
import json
import os

from google import genai
from google.genai import types

from app.models import DocumentFacts


READER_PROMPT = """
あなたは行政通知の文書読解担当です。
入力文書に明記された情報だけを抽出してください。推測や一般常識による補完は禁止です。
日付、対象者、必要書類、提出方法、問い合わせ先、費用、注意事項を、指定されたJSONスキーマで返してください。
記載がなければ null または空配列にしてください。
evidence_notes には、重要な判断の根拠または「記載なし」を簡潔に記録してください。
"""


def read_document(content: bytes, mime_type: str) -> DocumentFacts:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY が設定されていません。")

    client = genai.Client(api_key=api_key)
    encoded = base64.b64encode(content).decode("ascii")

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=[
            types.Part.from_bytes(data=base64.b64decode(encoded), mime_type=mime_type),
            READER_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentFacts,
            temperature=0,
        ),
    )
    if not response.text:
        raise RuntimeError("Geminiから空の応答が返されました。")
    return DocumentFacts.model_validate_json(response.text)
