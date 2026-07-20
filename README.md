# ヨムヤク（YomuYaku）

行政通知を、行動できる案内へ。

行政通知の原文を残したまま、対象者・期限・必要書類・提出方法を抽出し、
住民向けの行動チェックリストと、職員向けの文書改善候補を表示する実証Webアプリです。

## MVPの特徴

- URLを開くだけで使えるレスポンシブWeb UI
- APIキーがなくても動く固定サンプルデモ
- PDF / PNG / JPEGの任意アップロード
- Geminiによる文書読解
- ADKによる住民向け整理、根拠確認、職員向け文書点検
- ファイルを永続保存しない構成
- Cloud Run向けDockerfile

## 構成

1. `Document Reader`：Geminiのマルチモーダル入力で文書を構造化
2. `Action Organizer`：ADK Agentで住民の行動順に再構成
3. `Grounding Reviewer`：ADK Agentで根拠のない断定を検査
4. `Document Coach`：ADK Agentで不足・曖昧表現を点検

固定サンプルは外部APIを呼ばず、審査時のデモ安定性を確保します。

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .envにGOOGLE_API_KEYを設定
uvicorn app.main:app --reload
```

ブラウザで `http://localhost:8000` を開きます。

## テスト

```bash
pytest
```

## Cloud Runへデプロイ

```bash
gcloud run deploy yomuyaku \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_MODEL=gemini-3.5-flash \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

事前にSecret ManagerへAPIキーを登録してください。

```bash
printf '%s' 'YOUR_API_KEY' | \
  gcloud secrets create GOOGLE_API_KEY --data-file=-
```

既にシークレットがある場合は、新しいバージョンを追加します。

```bash
printf '%s' 'YOUR_API_KEY' | \
  gcloud secrets versions add GOOGLE_API_KEY --data-file=-
```

## 提出前確認

- シークレットや個人情報がGit履歴に入っていない
- シークレットモードまたは未ログイン端末でCloud Run URLが開く
- 「サンプルで試す」が安定して完走する
- 任意アップロード失敗時にもサンプルデモへ戻れる
- README、画面ショット、プレゼン、フォームの説明が実装内容と一致する

## 制約

- 実証用であり、正式な行政判断を行うものではありません。
- 原文にない情報は補わず、不明点として表示します。
- 入力ファイルはメモリ上で処理し、アプリ側では永続保存しません。
- Cloud Runや外部API側のログ・保持設定は別途確認が必要です。
