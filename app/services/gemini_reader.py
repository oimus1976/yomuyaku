from __future__ import annotations

import base64
import json
import os

from google import genai
from google.genai import types

from app.models import DocumentFacts


READER_PROMPT = """
あなたは行政通知の文書読解担当です。

入力文書に明記された情報だけを抽出してください。
推測、一般常識、制度知識による補完は禁止です。

次の項目を指定されたJSONスキーマで返してください。

- title: 文書の題名
- target: 対象者・対象世帯
- deadline: 申請期限や提出期限
- actions: 読み手が実際に行う手続を、文書に書かれた順番で配列化
- required_documents: 提出・添付・提示が必要な書類
- submission_method: 郵送、窓口、オンラインなどの提出方法
- contact: 問い合わせ先
- fee: 費用や手数料
- cautions: 注意事項
- evidence_notes: 重要な抽出結果の根拠や記載なし項目

actionsについては、特に次を守ってください。

1. 「申請方法」「手続方法」「提出方法」などの見出しを重点的に確認する。
2. 番号付き手順、箇条書き、命令形の文章を行動として抽出する。
3. 「記入してください」「添付してください」「提出してください」などを、
   読み手が実行する具体的な行動へ変換する。
4. 文書に明記された順序を維持する。
5. 郵送または窓口提出など、選択肢が明記されている場合は選択肢を保持する。
6. actionsとrequired_documentsは別々に抽出する。
7. 文書に行動が明記されている場合、actionsを空配列にしない。

例えば、
「申請書に記入し、本人確認書類を添付して、返信用封筒で郵送してください」
と書かれている場合は、次のように抽出します。

actions:
- 申請書に必要事項を記入する
- 本人確認書類を添付する
- 返信用封筒で郵送する

記載がない項目はnullまたは空配列にしてください。
JSON以外の文章やMarkdownコードフェンスは出力しないでください。
"""


def read_document(content: bytes, mime_type: str) -> DocumentFacts:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY が設定されていません。")

    client = genai.Client(api_key=api_key)
    encoded = base64.b64encode(content).decode("ascii")

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
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
