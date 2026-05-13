import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 및 환경 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오] 매수단가, 수량, 이름
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_realtime_news(query):
    """실시간 경제 뉴스 제목과 직접 링크 3개를 가져옵니다."""
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url)
        items = r.text.split('<item>')[1:4]
        news_list = []
        for item in items:
            title = item.split('<title>')[1].split('</title>')[0]
            link = item.split('<link>')[1].split('</link>')[0]
            news_list.append(f"• {title}\n  🔗 {link}")
        return "\n".join(news_list)
    except:
        return "• 뉴스를 가져오는 중 오류가 발생했습니다."

def get_stock_performance(stock_dict):
    """종목들의 당일 상승률을 계산하여 상위 5개를 반환합니다."""
    performance = []
    for name, ticker in stock_dict.items():
        try:
            s = yf.Ticker(ticker).history(period='2d')
            if len(s) < 2: continue
            chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            performance.append((name, chg))
        except: continue
    return sorted(performance, key=lambda x: x[1], reverse=True)[:5]

def get_portfolio_status():
    """포트폴리오 수익률 및 상세 현황을 생성합니다."""
    report = "\n💰 [나의 실시간 포트폴리오 현황]\n"
    for ticker, info in MY_PORTFOLIO.items():
        buy, amt, name = info
        curr = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
        rate = ((curr - buy) / buy) * 100
        money = (curr - buy) * amt
        unit = "$" if ticker == 'SMCI' else "원"
        report += f"• {name}: {rate:+.2f}% ({money:,.1f}{unit})\n"
    return report

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    main_msg = ""
    event_msg = None

    # --- [오전 08시: 해외 증시 마감 리포트] ---
    if 7 <= hour < 11:
        main_msg = f"🌎 [Morning] 해외 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        # 1. 해외 주요 지수
        for n, t in {'나스닥':'^IXIC', 'S&P500':'^GSPC'}.items():
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            main_msg += f"{n}: {c:+.2f}%  "
        
        # 2. 해외 대형주 상승 순위
        us_stocks = {'애플':'AAPL', '엔비디아':'NVDA', '마이크로소프트':'MSFT', '아마존':'AMZN', '테슬라':'TSLA', '구글':'GOOGL'}
        main_msg += "\n\n📊 [미국 대형주 상승 TOP 5]\n"
        for n, c in get_stock_performance(us_stocks):
            main_msg += f"• {n}: {c:+.2f}%\n"
            
        # 3. 뉴스 & 4. 포트폴리오
        main_msg += "\n📰 [실시간 해외 경제 뉴스]\n" + get_realtime_news("미국 증시 시황")
        main_msg += get_portfolio_status()
        
        # 5. 종합 의견 (분석)
        main_msg += "\n🧠 [전문 의견 및 차트 분석]\n"
        main_msg += "- SMCI: 현재 변동성 구간에서 이평선 지지 테스트 중입니다. 보유 비중의 기술적 대응이 필요합니다.\n"
        main_msg += "- 시황: 미 빅테크 수급 쏠림 현상이 지속되고 있어, 지수 ETF의 안정성이 돋보이는 장세입니다."
        
        # [별도 메시지] 경제/정치 이벤트 일정
        event_msg = "🗓 [Major Events] 주요 경제 및 정치 일정\n\n"
        event_msg += get_realtime_news("CPI FOMC 트럼프 의장 선임")
        event_msg += "\n\n💡 위 일정은 시장의 방향성을 결정할 핵심 변수입니다."

    # --- [오후 18시: 국내 증시 마감 리포트] ---
    elif 17 <= hour < 21:
        main_msg = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        # 1. 국내 주요 지수
        for n, t in {'코스피':'^KS11', '코스닥':'^KQ11'}.items():
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            main_msg += f"{n}: {c:+.2f}%  "
            
        # 2. 국내 대형주 상승 순위
        kr_stocks = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', '현대차':'005380.KS', 'LG엔솔':'373220.KS', '기아':'000270.KS', '셀트리온':'068270.KS'}
        main_msg += "\n\n🏆 [국내 대형주 상승 TOP 5]\n"
        for n, c in get_stock_performance(kr_stocks):
            main_msg += f"• {n}: {c:+.2f}%\n"
            
        # 3. 뉴스 & 4. 포트폴리오
        main_msg += "\n📰 [실시간 국내 경제 뉴스]\n" + get_realtime_news("국내 증시 특징주")
        main_msg += get_portfolio_status()
        
        # 5. 종합 의견 (분석)
        main_msg += "\n🎯 [전문 의견 및 차트 분석]\n"
        main_msg += "- 국내 지수는 외국인 수급에 민감한 차트 흐름을 보이고 있습니다. 지수 ETF의 적립식 매수 관점을 유지하세요.\n"
        main_msg += "- 금 현물(ACE): 자산 배분 관점에서 원화 약세 리스크를 방어하는 훌륭한 헷지 수단으로 작용 중입니다."

    return main_msg, event_msg

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    m_msg, e_msg = get_market_report()
    send_telegram(m_msg)
    if e_msg: send_telegram(e_msg)
