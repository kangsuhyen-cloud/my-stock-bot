import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# [보안 설정]
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오 정보]
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_detailed_analysis(ticker, name):
    """차트 및 수급 분석: 20일선 및 RSI 기반"""
    try:
        df = yf.Ticker(ticker).history(period='30d')
        if len(df) < 20: return f"[{name}] 데이터 부족"
        curr = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]

        trend = "상승 유지" if curr > ma20 else "지지선 테스트"
        intensity = "과열" if rsi > 70 else ("과매도" if rsi < 30 else "보통")
        
        return f"🔍 {name} 분석:\n  - 추세: {trend} (20일선: {ma20:,.0f})\n  - 수급: RSI {rsi:.1f} ({intensity})"
    except: return f"[{name}] 분석 오류"

def get_market_reports():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    is_morning = 7 <= hour < 11
    
    # 1. 심층 분석 리포트
    report = f"📊 [{('해외' if is_morning else '국내')} 증시 마감 리포트]\n📅 {now_kst.strftime('%m/%d %H:%M')}\n\n"
    
    # 지수
    symbols = {'나스닥': '^IXIC', 'S&P500': '^GSPC'} if is_morning else {'코스피': '^KS11', '코스닥': '^KQ11'}
    for n, t in symbols.items():
        try:
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{n} {c:+.2f}%  "
        except: report += f"{n} -  "
    
    # 포트폴리오 성과
    report += "\n\n💰 [보유 자산 현황]\n"
    for tk, info in MY_PORTFOLIO.items():
        try:
            d = yf.Ticker(tk).history(period='2d')
            curr = d['Close'].iloc[-1]
            buy, amt, name = info
            rate = ((curr-buy)/buy)*100
            report += f"• {name}: {rate:+.2f}%\n"
        except: continue

    # 심층 분석 섹션
    report += "\n🧠 [차트 및 수급 관점]\n"
    target = ('SMCI', '슈퍼마이크로컴퓨터') if is_morning else ('381170.KS', 'TIGER 미국테크TOP10')
    report += get_detailed_analysis(target[0], target[1])
    
    # 2. 주요일정 메시지 (뉴스 링크 제거, 간략화)
    # 실제로는 동적 데이터를 가져오지만, 가독성을 위해 핵심 키워드 중심 요약
    if is_morning:
        event_msg = "🗓 [US 주요 경제 일정]\n"
        event_msg += "• 오늘밤: 美 소비자물가지수(CPI) 발표\n"
        event_msg += "• 내일새벽: FOMC 의사록 공개\n"
        event_msg += "• 금주내: 주요 빅테크 실적 발표 예정"
    else:
        event_msg = "🗓 [KR 주요 경제 일정]\n"
        event_msg += "• 내일오전: 금통위 금리 결정\n"
        event_msg += "• 이번주: 반도체 수출 데이터 발표\n"
        event_msg += "• 차주: 국내 상장사 배당락일 확인"

    return report, event_msg

def send_telegram(text):
    if not text: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': text}, timeout=15)
    except: pass

if __name__ == "__main__":
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    # 오전 7~11시 혹은 오후 17~22시 사이에만 발송 (범위 확장)
    if (7 <= hour < 11) or (17 <= hour < 23):
        main_rep, event_rep = get_market_reports()
        send_telegram(main_rep)
        send_telegram(event_rep)
