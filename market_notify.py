"""
market_notify.py
為替(USD/JPY)・日経平均・Bitcoinの相場をSlackに通知するスクリプト
"""

import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())


def get_market_data():
    """CoinGeckoから為替・Bitcoinを一括取得"""
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,usd&vs_currencies=jpy&include_24hr_change=true"
    )
    return fetch_json(url)


def get_nikkei():
    """日経平均を取得（Yahoo Finance API）"""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EN225?interval=1d&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = fetch_json(url, headers)
    result = data["chart"]["result"][0]
    meta = result["meta"]
    price = meta.get("regularMarketPrice") or meta.get("previousClose")
    prev = meta.get("previousClose", price)
    change = price - prev
    change_pct = (change / prev) * 100 if prev else 0
    return price, change, change_pct


def arrow(value):
    return "🔺" if value >= 0 else "🔻"


def fmt(n, decimals=2):
    return f"{n:,.{decimals}f}"


def build_message(now):
    time_str = now.strftime("%H:%M JST  %Y/%m/%d")
    lines = [f"📊 *相場情報 - {time_str}*\n"]

    # CoinGeckoで為替・BTC一括取得
    try:
        cg = get_market_data()

        # USD/JPY
        usdjpy = cg["usd"]["jpy"]
        lines.append(f"💴 *USD/JPY*：¥{fmt(usdjpy)} 円")

        # Bitcoin
        btc = cg["bitcoin"]["jpy"]
        btc_pct = cg["bitcoin"].get("jpy_24h_change", 0)
        sign = "+" if btc_pct >= 0 else ""
        lines.append(
            f"{arrow(btc_pct)} *Bitcoin（BTC/JPY）*：¥{fmt(btc, 0)}  "
            f"({sign}{fmt(btc_pct)}% 24h)"
        )
    except Exception as e:
        lines.append(f"💴 *USD/JPY*：取得失敗 ({e})")
        lines.append(f"₿ *Bitcoin*：取得失敗 ({e})")

    # 日経平均
    try:
        price, change, change_pct = get_nikkei()
        sign = "+" if change >= 0 else ""
        lines.append(
            f"{arrow(change)} *日経平均*：{fmt(price)} 円  "
            f"({sign}{fmt(change)} / {sign}{fmt(change_pct)}%)"
        )
    except Exception as e:
        lines.append(f"📈 *日経平均*：取得失敗 ({e})")

    return "\n".join(lines)


def post_to_slack(message):
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.read().decode()


def main():
    now = datetime.now(JST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S JST')}] 相場取得開始")
    message = build_message(now)
    print("送信メッセージ:")
    print(message)
    result = post_to_slack(message)
    print(f"Slack送信結果: {result}")


if __name__ == "__main__":
    main()