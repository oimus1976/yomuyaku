from __future__ import annotations

import json
import re
import os
import uuid

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.models import AnalysisResult, DocumentFacts, ResidentView, StaffView


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
APP_NAME = "yomuyaku"


def clean_json_text(text: str) -> str:
    """ADKが返すMarkdownコードフェンス付きJSONを正規化する。"""
    value = text.strip()

    # ```json ... ``` または ``` ... ``` を除去
    match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        value = match.group(1).strip()

    return value

organizer_agent = Agent(
    name="action_organizer",
    model=MODEL,
    description="行政通知の抽出結果を、住民が行動できる案内へ整理する。",
    instruction="""
入力は行政通知から抽出済みのJSONです。
原文にない内容を追加せず、住民向けの短い要約、期限、行動順のチェックリスト、
必要書類、不明点、問い合わせ先をJSONで返してください。
不明点は「〜は文書から確認できません」と明記してください。
JSON以外は出力しないでください。
""",
)

reviewer_agent = Agent(
    name="grounding_reviewer",
    model=MODEL,
    description="住民向け案内に原文にない推測が混ざっていないか確認する。",
    instruction="""
document と resident のJSONを比較してください。
document に根拠がない断定、矛盾、過度な言い換えを検出し、
warnings のJSON配列だけを返してください。
問題がなくても、正式判断は原文と担当窓口で確認する旨を1件含めてください。
JSON以外は出力しないでください。
""",
)

coach_agent = Agent(
    name="document_coach",
    model=MODEL,
    description="行政通知の不足情報、曖昧表現、改善候補を整理する。",
    instruction="""
行政通知の抽出結果を職員向けに点検し、
improvement_points、ambiguous_expressions、missing_information を持つJSONを返してください。
文書の法的正否を断定せず、読み手が行動しやすくなる観点に限定してください。
JSON以外は出力しないでください。
""",
)


async def _run_agent(agent: Agent, payload: dict, output_model):
    session_service = InMemorySessionService()
    user_id = "demo-user"
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))],
    )
    final_text = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)
    if not final_text:
        raise RuntimeError(f"{agent.name} から応答がありません。")
    return output_model.model_validate_json(clean_json_text(final_text))


class WarningList(AnalysisResult):
    pass


async def organize_and_review(document: DocumentFacts) -> AnalysisResult:
    resident = await _run_agent(
        organizer_agent,
        document.model_dump(),
        ResidentView,
    )

    warning_payload = {
        "document": document.model_dump(),
        "resident": resident.model_dump(),
    }

    # Reviewerの出力は簡単な辞書として受け、形を厳格化する。
    class WarningsModel(ResidentView):
        pass

    # ADK出力の揺れを抑えるため、レビューと職員向け点検はJSON辞書として取得する。
    async def run_raw(agent: Agent, payload: dict) -> dict:
        session_service = InMemorySessionService()
        user_id = "demo-user"
        session_id = str(uuid.uuid4())
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
        message = types.Content(
            role="user",
            parts=[types.Part(text=json.dumps(payload, ensure_ascii=False))],
        )
        final_text = None
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = "".join(part.text or "" for part in event.content.parts)
        if not final_text:
            raise RuntimeError(f"{agent.name} から応答がありません。")
        return json.loads(clean_json_text(final_text))

    warnings_data = await run_raw(reviewer_agent, warning_payload)
    staff_data = await run_raw(coach_agent, document.model_dump())

    def normalize_warning(item):
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return (
                item.get("message")
                or item.get("warning")
                or item.get("detail")
                or str(item)
            )
        return str(item)

    if isinstance(warnings_data, list):
        warnings = [normalize_warning(item) for item in warnings_data]
    elif isinstance(warnings_data, dict):
        raw_warnings = warnings_data.get("warnings", [])
        if isinstance(raw_warnings, list):
            warnings = [normalize_warning(item) for item in raw_warnings]
        else:
            warnings = [normalize_warning(raw_warnings)]
    else:
        warnings = [
            "正式な判断は原文と担当窓口で確認してください。"
        ]

    staff = StaffView.model_validate(staff_data)

    return AnalysisResult(
        document=document,
        resident=resident,
        staff=staff,
        warnings=warnings,
        mode="ai",
    )
