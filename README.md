# 📊 market-notify

為替（USD/JPY）・日経平均・Bitcoinの相場を、毎日決まった時間にSlackへ自動通知するBotです。
GitHub Actionsで動くため、サーバー不要・完全無料で運用できます。

## 通知イメージ

```
📊 相場情報 - 10:00 JST  2026/03/28

💴 USD/JPY：¥149.87 円
🔻 日経平均：38,500.12 円  (-230.58 / -0.43%)
🔺 Bitcoin（BTC/JPY）：¥10,868,481  (+1.23% 24h)
```

## 通知スケジュール

| 時刻（JST） | UTC（GitHub Actions） |
|------------|----------------------|
| 10:00      | 01:00                |
| 12:00      | 03:00                |
| 15:00      | 06:00                |

## セットアップ

### 1. Slack Incoming Webhook を作成

1. https://api.slack.com/apps を開く
2. 「Create New App」→「From scratch」
3. アプリ名（例：`相場Bot`）とワークスペースを選択
4. 左メニュー「Incoming Webhooks」→ オンにする
5. 「Add New Webhook to Workspace」→ 通知したいチャンネルを選択
6. 表示された Webhook URL（`https://hooks.slack.com/services/...`）をコピー

### 2. GitHub Secrets に登録

リポジトリの `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Name | Value |
|------|-------|
| `SLACK_WEBHOOK_URL` | コピーした Webhook URL |

### 3. 動作確認

`Actions` タブ → `相場通知 to Slack` → `Run workflow` で手動実行できます。
Slackに通知が届けばセットアップ完了です🎉

## ファイル構成

```
.
├── README.md
├── market_notify.py                    # 相場取得・Slack通知スクリプト
└── .github/
    └── workflows/
        └── market_notify.yml           # GitHub Actions ワークフロー
```

## 使用API（すべて無料・登録不要）

| データ | API |
|--------|-----|
| USD/JPY | [Frankfurter API](https://www.frankfurter.app/) |
| 日経平均 | [Yahoo Finance API](https://finance.yahoo.com/) |
| Bitcoin | [CoinGecko API](https://www.coingecko.com/) |