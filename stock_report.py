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

def get_realtime_news(query, count=2):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url, timeout=5)
        items = r.text.split('<item>')[1:count+1]
        return "\n".join([f"• {i.split('<title>')[1].split('</title>')[0]}\n  🔗 {i.split('<link>')[1].split('</link>')[0]}" for i in items])
    except: return "• 일정 데이터를 불러오는 중입니다."

def get_detailed_analysis(ticker, name):
    """차트 및 수급 심층 분석 로직"""
    try:
        df = yf.Ticker(ticker).history(period='30d')
        if len(df) < 20: return f"[{name}] 분석 데이터 부족"
        curr = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        
        # RSI 계산
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]

        status = "상승 추세 유지" if curr > ma20 else "지지선 확인 필요"
        strength = "과열 주의" if rsi > 70 else ("과매도 반등 기대" if rsi < 30 else "안정적 흐름")
        
        return f"🔍 {name} 진단:\n  - 추세: {status} (20일선: {ma20:,.0f})\n  - 강도: RSI {rsi:.1f} ({strength})"
    except: return f"[{name}] 분석 일시 중단"

def get_market_reports():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    is_morning = 7 <= hour < 11
    market_name = "해외 증시" if is_morning else "국내 증시"
    
    # 1. 메인 리포트 생성
    report = f"📊 [{market_name} 심층 리포트]\n📅 {now_kst.strftime('%m/%d %H:%M')}\n\n"
    
    # 지수현황
    symbols = {'나스닥': '^IXIC', 'S&P500': '^GSPC'} if is_morning else {'코스피': '^KS11', '코스닥': '^KQ11'}
    for n, t in symbols.items():
        try:
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{n} {c:+.2f}%  "
        except: report += f"{n} [휴장]  "
    
    # 포트폴리오
    report += "\n\n💰 [자산 현황]\n"
    for tk, info in MY_PORTFOLIO.items():
        try:
            d = yf.Ticker(tk).history(period='2d')
            curr = d['Close'].iloc[-1]
            buy, amt, name = info
            rate = ((curr-buy)/buy)*100
            report += f"• {name}: {rate:+.2f}%\n"
        except: continue

    # 심층 분석
    report += "\n🧠 [차트/수급 분석]\n"
    target = ('SMCI', '슈퍼마이크로컴퓨터') if is_morning else ('381170.KS', 'TIGER 미국테크TOP10')
    report += get_detailed_analysis(target[0], target[1])
    report += f"\n\n💡 한줄평: {'기술주 중심의 강한 홀딩 전략이 유효합니다.' if is_morning else '국내 증시 하방 경직성을 확보 중인 구간입니다.'}"

    # 2. 별도 일정 메시지 생성
    event_query = "미국 소비자물가지수 FOMC 금리 실적발표" if is_morning else "한국 금통위 수출지표 반도체 일정"
    event_msg = f"🗓 [Major Events] 향후 주목해야 할 일정\n\n{get_realtime_news(event_query, count=3)}"

    return report, event_msg

def send_telegram(text):
    if not text or len(text) < 10: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': text}, timeout=15)
    except: pass

if __name__ == "__main__":
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    # 아침 또는 저녁 시간대에만 작동
    if (7 <= hour < 11) or (17 <= hour < 22):
        main_report, event_report = get_market_reports()
        send_telegram(main_report) # 첫 번째 메시지: 분석 리포트
        send_telegram(event_report) # 두 번째 메시지: 일정 정보
