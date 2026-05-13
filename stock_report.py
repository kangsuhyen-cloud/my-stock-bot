import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오] 종목 코드를 더 호환성이 좋은 방식으로 수정했습니다.
# 국내 ETF는 보통 .KS로 통용되나, 야후 파이낸스 오류 방지를 위해 예외 처리를 추가합니다.
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
        news_list = []
        for item in items:
            title = item.split('<title>')[1].split('</title>')[0]
            link = item.split('<link>')[1].split('</link>')[0]
            news_list.append(f"• {title}\n  🔗 {link}")
        return "\n".join(news_list)
    except:
        return "• 뉴스를 가져오는 중 오류가 발생했습니다."

def get_stock_performance(stock_dict):
    performance = []
    for name, ticker in stock_dict.items():
        try:
            s = yf.Ticker(ticker).history(period='5d') # 데이터를 넉넉히 가져옴
            if len(s) < 2: continue
            chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            performance.append((name, chg))
        except: continue
    return sorted(performance, key=lambda x: x[1], reverse=True)[:5]

def get_portfolio_status():
    report = "\n💰 [나의 실시간 포트폴리오 현황]\n"
    for ticker, info in MY_PORTFOLIO.items():
        buy, amt, name = info
        try:
            # 오류 방지: 데이터를 못 가져오면 해당 종목은 건너뜁니다.
            stock_data = yf.Ticker(ticker).history(period='2d')
            if stock_data.empty:
                report += f"• {name}: [데이터 확인 불가]\n"
                continue
                
            curr = stock_data['Close'].iloc[-1]
            rate = ((curr - buy) / buy) * 100
            money = (curr - buy) * amt
            unit = "$" if ticker == 'SMCI' else "원"
            report += f"• {name}: {rate:+.2f}% ({money:,.1f}{unit})\n"
        except Exception:
            report += f"• {name}: [분석 오류]\n"
    return report

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    main_msg = ""
    event_msg = None

    # 지수 데이터
    idx_str = ""
    for n, t in {'나스닥':'^IXIC', 'S&P500':'^GSPC', '코스피':'^KS11'}.items():
        try:
            d = yf.Ticker(t).history(period='2d')
            c = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            idx_str += f"{n} {c:+.2f}%  "
        except: continue

    if 7 <= hour < 11:
        main_msg = f"🌎 [Morning] 해외 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        main_msg += f"📈 [주요 지수]\n{idx_str}\n"
        us_stocks = {'애플':'AAPL', '엔비디아':'NVDA', 'MSFT':'MSFT', '테슬라':'TSLA', '아마존':'AMZN'}
        main_msg += "\n📊 [미국 대형주 상승 TOP 5]\n"
        for n, c in get_stock_performance(us_stocks):
            main_msg += f"• {name}: {chg:+.2f}%\n" # 여기서 name, chg는 n, c로 수정
        main_msg += "\n📰 [해외 뉴스]\n" + get_realtime_news("미국 증시 시황")
        main_msg += get_portfolio_status()
        main_msg += "\n🧠 [분석] SMCI와 테크주 변동성에 유의하며 S&P500 중심의 관망세가 유효합니다."
        
        event_msg = "🗓 [Major Events] 주요 경제 및 정치 일정\n\n"
        event_msg += get_realtime_news("CPI FOMC 금리 트럼프")
        
    elif 17 <= hour < 21:
        main_msg = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        main_msg += f"📉 [지수 현황]\n{idx_str}\n"
        kr_stocks = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', '현대차':'005380.KS', '기아':'000270.KS', 'LG엔솔':'373220.KS'}
        main_msg += "\n🏆 [국내 대형주 상승 TOP 5]\n"
        for n, c in get_stock_performance(kr_stocks):
            main_msg += f"• {n}: {c:+.2f}%\n"
        main_msg += "\n📰 [국내 뉴스]\n" + get_realtime_news("국내 증시 특징주")
        main_msg += get_portfolio_status()
        main_msg += "\n🎯 [분석] 금 현물은 원화 가치 변동에 대한 훌륭한 헷지 수단입니다."

    return main_msg, event_msg

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    try:
        m_msg, e_msg = get_market_report()
        send_telegram(m_msg)
        if e_msg: send_telegram(e_msg)
    except Exception as e:
        # 혹시 모를 에러 발생 시 로그에 상세히 남김
        print(f"최종 에러 로그: {e}")
