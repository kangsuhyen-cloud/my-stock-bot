import os
import yfinance as yf
import requests
import feedparser
from datetime import datetime, timedelta

# =========================================================
# 텔레그램 설정
# =========================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# =========================================================
# 기본 함수
# =========================================================
def is_market_open(date):
    return date.weekday() < 5

def market_day_adjustment(date):
    while not is_market_open(date):
        date -= timedelta(days=1)
    return date

def safe_history(ticker, period='5d'):
    try:
        data = yf.Ticker(ticker).history(period=period)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"{ticker} 오류: {e}")
        return None

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 오류")
        return
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': CHAT_ID,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            },
            timeout=20
        )
        print(response.status_code)
    except Exception as e:
        print(f"텔레그램 오류: {e}")

# =========================================================
# 포트폴리오 요약
# =========================================================
def get_portfolio_summary():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    last_trading_day = market_day_adjustment(now_kst)

    result = "💼 포트폴리오 현황\n\n"
    result += f"📅 거래일: {last_trading_day.strftime('%Y-%m-%d')}\n\n"

    # 포트폴리오 데이터 처리 코드 추가

    return result

# =========================================================
# 메인 실행
# =========================================================
if __name__ == "__main__":
    now_kst = datetime.utcnow() + timedelta(hours=9)

    if is_market_open(now_kst):
        send_telegram(f"🌙 해외증시 브리핑\n📅 {now_kst.strftime('%Y-%m-%d %H:%M')} KST")
        send_telegram(get_portfolio_summary())
    else:
        print("오늘은 시장이 열지 않습니다.")
