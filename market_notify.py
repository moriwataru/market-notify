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


def get_usdjpy():
    """USD/JPYをYahoo Finance APIから取得"""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDJPY%3DX?interval=1d&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = fetch_json(url, headers)
    result = data["chart"]["result"][0]
    meta = result["meta"]
    price = meta.get("regularMarketPrice") or meta.get("previousClose")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose", price)
    change_pct = ((price - prev) / prev) * 100 if prev else 0
    return price, change_pct


def get_btc():
    """BitcoinをCoinGeckoから取得（24h変化率含む）"""
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
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
    prev = meta.get("chartPreviousClose") or meta.get("previousClose", price)
    change_pct = ((price - prev) / prev) * 100 if prev else 0
    return price, change_pct


def trend_icon(value):
    return "🟢" if value >= 0 else "🔴"


def fmt(n, decimals=2):
    return f"{n:,.{decimals}f}"


def pct(value):
    sign = "+" if value >= 0 else ""
    return f"{sign}{fmt(value)}%"


def build_message(now):
    time_str = now.strftime("%H:%M JST  %Y/%m/%d")
    lines = [f"*相場情報 - {time_str}*\n"]

    # USD/JPY（Yahoo Finance）
    try:
        usdjpy, usdjpy_pct = get_usdjpy()
        lines.append(
            f"{trend_icon(usdjpy_pct)} *USD/JPY* ({pct(usdjpy_pct)})\n{fmt(usdjpy)} 円\n"
        )
    except Exception as e:
        lines.append(f"🟡 *USD/JPY*\n取得失敗 ({e})")

    # Bitcoin（CoinGecko）
    try:
        cg = get_btc()
        btc_usd = float(cg["bitcoin"]["usd"])
        btc_pct = float(cg["bitcoin"].get("usd_24h_change") or 0.0)
        lines.append(
            f"{trend_icon(btc_pct)} *Bitcoin* ({pct(btc_pct)})\n${fmt(btc_usd, 0)}\n"
        )
    except Exception as e:
        lines.append(f"🟡 *Bitcoin*\n取得失敗 ({e})")

    # 日経平均（Yahoo Finance）
    try:
        price, change_pct = get_nikkei()
        lines.append(
            f"{trend_icon(change_pct)} *日経平均* ({pct(change_pct)})\n{fmt(price)} 円\n"
        )
    except Exception as e:
        lines.append(f"🟡 *日経平均*\n取得失敗 ({e})")

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