import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_realtime_news(query):
    """뉴스 데이터 가져오기 (실패 시 빈 문자열 반환하여 전송 보장)"""
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url, timeout=5)
        items = r.text.split('<item>')[1:4]
        res = []
        for i in items:
            t = i.split('<title>')[1].split('</title>')[0]
            l = i.split('<link>')[1].split('</link>')[0]
            res.append(f"• {t}\n  🔗 {l}")
        return "\n".join(res)
    except: return "• 현재 뉴스를 불러올 수 없습니다."

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    main_msg = ""
    event_msg = None

    # [오전 리포트 - 해외 증시 전용]
    if 7 <= hour < 11:
        main_msg = f"🌎 [Morning] 해외 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n📈 [미국 주요 지수]\n"
        for n, t in {'나스닥': '^IXIC', 'S&P500': '^GSPC'}.items():
            try:
                d = yf.Ticker(t).history(period='5d')
                c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                main_msg += f"{n} {c:+.2f}%  "
            except: main_msg += f"{n} [휴장]  "
        
        main_msg += "\n\n📊 [미국 대형주 상승 TOP 5]\n"
        us_stocks = {'엔비디아':'NVDA', '테슬라':'TSLA', '애플':'AAPL', '메타':'META', '아마존':'AMZN'}
        perf = []
        for n, t in us_stocks.items():
            try:
                s = yf.Ticker(t).history(period='2d')
                ch = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
                perf.append((n, ch))
            except: continue
        for n, c in sorted(perf, key=lambda x: x[1], reverse=True)[:5]:
            main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += f"\n📰 [해외 경제 뉴스]\n{get_realtime_news('미국 증시 시황')}\n"
        
        main_msg += "\n💰 [나의 포트폴리오 현황]\n"
        for tk, info in MY_PORTFOLIO.items():
            try:
                d = yf.Ticker(tk).history(period='2d')
                curr = d['Close'].iloc[-1]
                buy, amt, name = info
                main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f})\n"
            except: main_msg += f"• {info[2]}: [데이터 없음]\n"
        
        main_msg += "\n🧠 [분석 의견]\n- SMCI: 20일선 부근 변동성 확대 주의\n- 시황: 빅테크 중심 수급 강세가 유지되고 있습니다."
        event_msg = f"🗓 [Major Events] 주요 일정\n\n{get_realtime_news('CPI FOMC 금리 트럼프')}"

    # [오후 리포트 - 국내 증시 전용]
    elif 17 <= hour < 22:
        main_msg = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n📉 [국내 주요 지수]\n"
        for n, t in {'코스피': '^KS11', '코스닥': '^KQ11'}.items():
            try:
                d = yf.Ticker(t).history(period='5d')
                c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                main_msg += f"{n} {c:+.2f}%  "
            except: main_msg += f"{n} [휴장]  "
            
        main_msg += "\n\n🏆 [국내 대형주 상승 TOP 5]\n"
        kr_stocks = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', '현대차':'005380.KS', '기아':'000270.KS', '셀트리온':'068270.KS'}
        perf = []
        for n, t in kr_stocks.items():
            try:
                s = yf.Ticker(t).history(period='2d')
                ch = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
                perf.append((n, ch))
            except: continue
        for n, c in sorted(perf, key=lambda x: x[1], reverse=True)[:5]:
            main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += f"\n📰 [국내 경제 뉴스]\n{get_realtime_news('국내 증시 특징주')}\n"

        main_msg += "\n💰 [나의 포트폴리오 현황]\n"
        for tk, info in MY_PORTFOLIO.items():
            try:
                d = yf.Ticker(tk).history(period='2d')
                curr = d['Close'].iloc[-1]
                buy, amt, name = info
                main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f}원)\n"
            except: main_msg += f"• {info[2]}: [데이터 없음]\n"
            
        main_msg += "\n🎯 [분석 의견]\n- TIGER 미국테크: 원/달러 환율 및 나스닥 선물 흐름과 동조화 중\n- 시황: 대형주 위주 외인 수급 체크가 필요합니다."

    return main_msg, event_msg

def send_telegram(text):
    if not text or len(text) < 10: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': text}, timeout=10)
    except Exception as e:
        print(f"전송 에러: {e}")

if __name__ == "__main__":
    m_msg, e_msg = get_market_report()
    if m_msg: send_telegram(m_msg)
    if e_msg: send_telegram(e_msg)
