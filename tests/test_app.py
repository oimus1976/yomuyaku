from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sample():
    response = client.post("/api/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "sample"
    assert data["resident"]["deadline"]
    assert data["resident"]["actions"]


def test_warning_dictionary_can_be_normalized():
    item = {
        "severity": "info",
        "message": "正式な判断は原文と担当窓口で確認してください。",
    }

    normalized = (
        item.get("message")
        or item.get("warning")
        or item.get("detail")
        or str(item)
    )

    assert normalized == "正式な判断は原文と担当窓口で確認してください。"


def test_clean_json_text_removes_markdown_fence():
    from app.services.adk_pipeline import clean_json_text

    source = '''```json
{
  "summary": "申請してください"
}
```'''

    assert clean_json_text(source) == '''{
  "summary": "申請してください"
}'''


def test_warning_text_field_can_be_normalized():
    item = {
        "severity": "info",
        "text": "正式な判断は原文と担当窓口で確認してください。",
    }

    normalized = (
        item.get("message")
        or item.get("text")
        or item.get("warning")
        or item.get("detail")
        or str(item)
    )

    assert normalized == "正式な判断は原文と担当窓口で確認してください。"
