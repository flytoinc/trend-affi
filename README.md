# Trend-Affi 🎬

自律型エンタメアフィリエイト・マーケター

Google Trends と X の2つの情報源からトレンドを取得し、メルカリの関連商品を選定（意味的マッチング付き）、Gemini AIで最適化された投稿をXに自動投稿するシステム。

## 機能

1. **情報収集**: Google Trends / X トレンドから交互に取得（1日4回、2回ずつ）
2. **商品選定**: キーワードからメルカリ商品を検索（Gemini APIで意味的な関連性を検証）
3. **AI投稿生成**: Gemini APIで反応の良い投稿文を生成
4. **自律学習**: 過去の高反応投稿パターンを分析し、プロンプトに反映
5. **自動投稿**: X APIで投稿、結果をスプレッドシートに記録
6. **重複防止**: 過去72時間内の投稿済みトレンドは自動スキップ

## セットアップ

### 1. GitHub Secrets設定

リポジトリの `Settings > Secrets and variables > Actions` で以下を設定:

| Secret名 | 説明 |
|----------|------|
| `GEMINI_API_KEY` | Google Gemini API Key |
| `X_API_KEY` | X API Key |
| `X_API_SECRET` | X API Secret |
| `X_ACCESS_TOKEN` | X Access Token |
| `X_ACCESS_TOKEN_SECRET` | X Access Token Secret |
| `GOOGLE_CREDENTIALS_JSON` | GCP サービスアカウントJSON |
| `GOOGLE_SHEET_KEY` | スプレッドシートID |

### 2. スプレッドシート準備

以下のシートが自動作成されます:
- `trendnews`: トレンド/ニュース記録（sourceカラム付き）
- `posts`: 投稿記録
- `config`: 設定

### 3. X API設定

X Developer PortalでApp作成、必要な権限を付与:
- Read and Write
- OAuth 1.0a

### 4. Google Cloud設定

1. サービスアカウント作成
2. Sheets API有効化
3. スプレッドシートをサービスアカウントに共有

## ファイル構成

```
trend-affi/
├── main.py                     # メインエントリーポイント
├── requirements.txt            # 依存パッケージ
├── README.md
├── .github/
│   └── workflows/
│       └── main.yml            # GitHub Actions設定
└── src/
    ├── __init__.py
    ├── google_trends_scraper.py # Google Trendsスクレイパー
    ├── x_trends_scraper.py     # Xトレンドスクレイパー（NEW）
    ├── trend_researcher.py     # トレンド理由調査
    ├── mercari_search.py       # メルカリ商品検索（意味マッチング付き）
    ├── ai_generator.py         # Gemini AI投稿生成
    ├── learning.py             # 学習システム
    ├── x_poster.py             # X投稿
    └── sheets_manager.py       # スプレッドシート管理
```

## スケジュール

GitHub Actionsで1日4回自動実行（情報源を交互に使用）:
- 7:55 JST → Google Trends
- 11:55 JST → X Trends
- 14:55 JST → Google Trends
- 17:55 JST → X Trends

## 手動実行

GitHub Actions → workflow_dispatch で手動実行可能
情報源を `google_trends` / `x_trends` から選択可能

## ドライラン

投稿せずにテストする場合:
```bash
python main.py --dry-run
```

## 注意事項

- X APIの利用規約を遵守してください
- メルカリのスクレイピングは適度な頻度で実行してください
- アフィリエイトリンクは実際のメルカリアンバサダーURLに変更してください

## ライセンス

Private
