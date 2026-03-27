"""
market_notify.py
為替(USD/JPY)・日経平均・Bitcoinの相場をSlackに通知するスクリプト
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())


def get_usdjpy():
    """USD/JPY レートを取得（Frankfurter API - 無料・登録不要）"""
    try:
        data = fetch_json("https://api.frankfurter.app/latest?from=USD&to=JPY")
        rate = data["rates"]["JPY"]
        return rate, None
    except Exception as e:
        return None, str(e)


def get_nikkei():
    """日経平均を取得（Yahoo Finance API）"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EN225?interval=1d&range=2d"
        headers = {"User-Agent": "Mozilla/5.0"}
        data = fetch_json(url, headers)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        prev = meta.get("previousClose", price)
        change = price - prev
        change_pct = (change / prev) * 100 if prev else 0
        return price, change, change_pct, None
    except Exception as e:
        return None, None, None, str(e)


def get_bitcoin():
    """BTC/JPY レートを取得（CoinGecko API - 無料・登録不要）"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=jpy&include_24hr_change=true"
        data = fetch_json(url)
        price = data["bitcoin"]["jpy"]
        change_pct = data["bitcoin"].get("jpy_24h_change", 0)
        return price, change_pct, None
    except Exception as e:
        return None, None, str(e)


def arrow(value):
    return "🔺" if value >= 0 else "🔻"


def fmt_num(n, decimals=2):
    return f"{n:,.{decimals}f}"


def build_message(now):
    time_str = now.strftime("%H:%M JST  %Y/%m/%d")

    lines = [f"📊 *相場情報 - {time_str}*\n"]

    # USD/JPY
    rate, err = get_usdjpy()
    if rate:
        lines.append(f"💴 *USD/JPY*：¥{fmt_num(rate)} 円")
    else:
        lines.append(f"💴 *USD/JPY*：取得失敗 ({err})")

    # 日経平均
    price, change, change_pct, err = get_nikkei()
    if price:
        sign = "+" if change >= 0 else ""
        lines.append(
            f"{arrow(change)} *日経平均*：{fmt_num(price)} 円  "
            f"({sign}{fmt_num(change)} / {sign}{fmt_num(change_pct)}%)"
        )
    else:
        lines.append(f"📈 *日経平均*：取得失敗 ({err})")

    # Bitcoin
    btc, btc_pct, err = get_bitcoin()
    if btc:
        sign = "+" if btc_pct >= 0 else ""
        lines.append(
            f"{arrow(btc_pct)} *Bitcoin（BTC/JPY）*：¥{fmt_num(btc, 0)}  "
            f"({sign}{fmt_num(btc_pct)}% 24h)"
        )
    else:
        lines.append(f"₿ *Bitcoin*：取得失敗 ({err})")

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