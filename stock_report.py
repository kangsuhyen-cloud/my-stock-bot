import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 보안 설정
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
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url, timeout=10)
        items = r.text.split('<item>')[1:4]
        return "\n".join([f"• {i.split('<title>')[1].split('</title>')[0]}\n  🔗 {i.split('<link>')[1].split('</link>')[0]}" for i in items])
    except: return "• 뉴스 데이터를 가져올 수 없습니다."

def get_safe_history(ticker, days='7d'):
    """데이터가 없을 때를 대비해 최근 데이터를 안전하게 가져옵니다."""
    try:
        data = yf.Ticker(ticker).history(period=days)
        if data.empty or len(data) < 1:
            return None
        return data
    except:
        return None

def get_analysis(ticker, name):
    data = get_safe_history(ticker, '30d')
    if data is None or len(data) < 15: return f"- {name}: 시장 휴장 또는 분석 데이터 부족"
    
    curr = data['Close'].iloc[-1]
    ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
    
    if curr > ma20:
        return f"- {name}: 20일선 위 강세 흐름. 지지선 {ma20:,.0f}원/달러 확인."
    else:
        return f"- {name}: 20일선 아래 약세 국면. 지지 매수세 확인 필요."

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    main_msg = ""
    event_msg = None

    # 오전 리포트 (해외 전용)
    if 7 <= hour < 11:
        main_msg = f"🌎 [Morning] 해외 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n📈 [미국 주요 지수]\n"
        for n, t in {'나스닥': '^IXIC', 'S&P500': '^GSPC'}.items():
            d = get_safe_history(t)
            if d is not None and len(d) >= 2:
                c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                main_msg += f"{n} {c:+.2f}%  "
            else: main_msg += f"{n} 휴장  "
        
        us_stocks = {'엔비디아':'NVDA', '테슬라':'TSLA', '애플':'AAPL', '메타':'META', '아마존':'AMZN'}
        perf = []
        for n, t in us_stocks.items():
            d = get_safe_history(t)
            if d is not None and len(d) >= 2:
                ch = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                perf.append((n, ch))
        
        main_msg += "\n\n📊 [미국 대형주 상승 TOP]\n"
        for n, c in sorted(perf, key=lambda x: x[1], reverse=True)[:5]:
            main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += "\n📰 [해외 경제 뉴스]\n" + get_realtime_news("미국 증시 시황")
        
        main_msg += "\n💰 [나의 포트폴리오]\n"
        for tk, info in MY_PORTFOLIO.items():
            d = get_safe_history(tk)
            if d is not None:
                curr = d['Close'].iloc[-1]
                buy, amt, name = info
                main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f})\n"
        
        main_msg += "\n🧠 [전문가 차트 분석]\n" + get_analysis('SMCI', '슈퍼마이크로컴퓨터')
        event_msg = "🗓 [Major Events] 주요 일정\n\n" + get_realtime_news("CPI FOMC 금리")

    # 오후 리포트 (국내 전용)
    elif 17 <= hour < 21:
        main_msg = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n📉 [국내 주요 지수]\n"
        for n, t in {'코스피': '^KS11', '코스닥': '^KQ11'}.items():
            d = get_safe_history(t)
            if d is not None and len(d) >= 2:
                c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                main_msg += f"{n} {c:+.2f}%  "
            else: main_msg += f"{n} 휴장  "
            
        kr_stocks = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', '현대차':'005380.KS', '기아':'000270.KS', '셀트리온':'068270.KS'}
        perf = []
        for n, t in kr_stocks.items():
            d = get_safe_history(t)
            if d is not None and len(d) >= 2:
                ch = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
                perf.append((n, ch))
        
        main_msg += "\n\n🏆 [국내 대형주 상승 TOP]\n"
        for n, c in sorted(perf, key=lambda x: x[1], reverse=True)[:5]:
            main_msg += f"• {n}: {c:+.2f}%\n"

        main_msg += "\n📰 [국내 경제 뉴스]\n" + get_realtime_news("국내 증시 특징주")

        main_msg += "\n💰 [나의 포트폴리오]\n"
        for tk, info in MY_PORTFOLIO.items():
            d = get_safe_history(tk)
            if d is not None:
                curr = d['Close'].iloc[-1]
                buy, amt, name = info
                main_msg += f"• {name}: {((curr-buy)/buy)*100:+.2f}% ({(curr-buy)*amt:,.1f}원)\n"
            
        main_msg += "\n🎯 [전문가 차트 분석]\n" + get_analysis('381170.KS', 'TIGER 미국테크TOP10')

    return main_msg, event_msg

def send_telegram(text):
    if not text: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': text}, timeout=10)
    except: print("메시지 전송 실패")

if __name__ == "__main__":
    try:
        m_msg, e_msg = get_market_report()
        if m_msg: send_telegram(m_msg)
        if e_msg: send_telegram(e_msg)
    except Exception as e:
        print(f"최종 오류: {e}")
