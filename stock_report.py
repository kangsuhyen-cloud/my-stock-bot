import yfinance as yf
import requests
import os
from datetime import datetime

# 깃허브 설정값에서 정보를 가져옵니다
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def get_market_report():
    now_hour = (datetime.now().hour + 9) % 24 # 한국 시간 기준 보정
    report = ""
    # (여기에 이전에 짜드린 국내/해외 리포트 생성 로직이 들어갑니다)
    # ... 중략 (이전 답변의 상세 로직을 그대로 사용하세요) ...
    return report

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(url, json=params)

if __name__ == "__main__":
    report_content = get_market_report()
    send_telegram(report_content)
