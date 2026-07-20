# Changelog

## [Unreleased]

### Added

- FastAPIベースのWebアプリ初期構成
- 固定サンプルによる審査用デモ
- PDF / PNG / JPEGアップロードAPI
- Geminiによる文書構造化
- ADK Agentによる行動整理、根拠確認、文書改善点抽出
- レスポンシブな住民向け・職員向け結果画面
- Cloud Run用Dockerfile
- ヘルスチェックと基本テスト

### Changed

- Geminiの既定モデルを `gemini-2.5-flash` から `gemini-3.5-flash` へ更新

### Fixed

- 任意文書の解析失敗時にCloud Runログへ例外詳細を記録するよう修正

### Fixed

- ADKがMarkdownコードフェンス付きJSONを返した場合にも解析できるよう修正
- Grounding Reviewerの警告配列および警告オブジェクトを表示用文字列へ正規化
