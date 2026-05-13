import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오]
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_realtime_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url)
        items = r.text.split('<item>')[1:4]
        return "\n".join([f"• {i.split('<title>')[1].split('</title>')[0]}\n  🔗 {i.split('<link>')[1].split('</link>')[0]}" for i in items])
    except: return "• 뉴스 데이터를 가져올 수 없습니다."

def get_analysis(ticker, name):
    """차트 데이터를 분석하여 전문적인 기술적 의견을 생성합니다."""
    try:
        data = yf.Ticker(ticker).history(period='20d')
        if len(data) < 15: return f"- {name}: 데이터 부족으로 분석 불가"
        
        curr = data['Close'].iloc[-1]
        ma20 = data['Close'].mean()
        diff = ((curr - ma20) / ma20) * 100
        
        if curr > ma20:
            return f"- {name}: 현재 20일 이동평균선 상단에서 강세 흐름 유지 중입니다. 단기 지지선은 {ma20:,.0f}원/달러 구간입니다."
        else:
            return f"- {name}: 20일선 아래에서 저항을 받는 모습입니다. 과매도 구간 진입 여부를 모니터링하며 분할 매수 관점이 유효합니다."
    except: return f"- {name}: 분석 중 오류 발생"

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    main_msg = ""
    event_msg = None

    # --- [오전 07~11시: 해외 증시 전용] ---
    if 7 <= hour < 11:
        main_msg = f"🌎 [Morning] 해외 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        # 1. 지수 (해외만)
        main_msg += "📈 [미국 주요 지수]\n"
        for n, t in {'나스닥': '^IXIC', 'S&P500': '^GSPC'}.items():
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            main_msg += f"{n} {c:+.2f}%  "
        
        # 2. 대형주 순위 (미국만)
        us_stocks = {'엔비디아':'NVDA', '테슬라':'TSLA', '애플':'AAPL', '메타':'META', '아마존':'AMZN'}
        perf = []
        for n, t in us_stocks.items():
            s = yf.Ticker(t).history(period='2d')
            ch = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            perf.append((n, ch))
        perf = sorted(perf, key=lambda x: x[1], reverse=True)[:5]
        main_msg += "\n\n📊 [미국 대형주 상승 TOP 5]\n"
        for n, c in perf: main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += "\n📰 [해외 경제 뉴스]\n" + get_realtime_news("미국 증시 시황")
        
        # 3. 포트폴리오 및 심층 분석
        main_msg += "\n💰 [나의 포트폴리오 & 차트 분석]\n"
        for tk, info in MY_PORTFOLIO.items():
            buy, amt, name = info
            curr = yf.Ticker(tk).history(period='1d')['Close'].iloc[-1]
            main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f})\n"
        
        main_msg += "\n🧠 [전문가 차트 분석 의견]\n"
        main_msg += get_analysis('SMCI', '슈퍼마이크로컴퓨터') + "\n"
        main_msg += "- 해외 시황: 나스닥 기술주 중심의 수급 쏠림이 강합니다. 지수 ETF 비중을 유지하며 변동성에 대비하세요."

        event_msg = "🗓 [Major Events] 주요 경제 및 정치 일정\n\n" + get_realtime_news("CPI FOMC 트럼프 금리")

    # --- [오후 17~21시: 국내 증시 전용] ---
    elif 17 <= hour < 21:
        main_msg = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        # 1. 지수 (국내만)
        main_msg += "📉 [국내 주요 지수]\n"
        for n, t in {'코스피': '^KS11', '코스닥': '^KQ11'}.items():
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            main_msg += f"{n} {c:+.2f}%  "
            
        # 2. 대형주 순위 (국내만)
        kr_stocks = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', '현대차':'005380.KS', '기아':'000270.KS', '셀트리온':'068270.KS'}
        perf = []
        for n, t in kr_stocks.items():
            s = yf.Ticker(t).history(period='2d')
            ch = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            perf.append((n, ch))
        perf = sorted(perf, key=lambda x: x[1], reverse=True)[:5]
        main_msg += "\n\n🏆 [국내 대형주 상승 TOP 5]\n"
        for n, c in perf: main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += "\n📰 [국내 경제 뉴스]\n" + get_realtime_news("국내 증시 특징주")

        # 3. 포트폴리오 및 심층 분석
        main_msg += "\n💰 [나의 포트폴리오 & 차트 분석]\n"
        for tk, info in MY_PORTFOLIO.items():
            buy, amt, name = info
            curr = yf.Ticker(tk).history(period='1d')['Close'].iloc[-1]
            main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f}원)\n"
            
        main_msg += "\n🎯 [전문가 차트 분석 의견]\n"
        main_msg += get_analysis('381170.KS', 'TIGER 미국테크TOP10') + "\n"
        main_msg += "- 국내 시황: 외인 수급이 대형주 위주로 유입되었습니다. 환율 변동에 따른 금 현물 자산의 가치 방어력을 확인하세요."

    return main_msg, event_msg

def send_telegram(text):
    if not text: return
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    m_msg, e_msg = get_market_report()
    send_telegram(m_msg)
    if e_msg: send_telegram(e_msg)
