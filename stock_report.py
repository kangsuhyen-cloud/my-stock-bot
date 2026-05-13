import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오 설정] 매수단가, 보유수량, 이름
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_stock_performance(stock_dict):
    """주어진 종목 리스트의 당일 상승률을 계산하여 정렬된 리스트로 반환합니다."""
    performance = []
    for name, ticker in stock_dict.items():
        try:
            s = yf.Ticker(ticker).history(period='2d')
            if len(s) < 2: continue
            chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            performance.append((name, chg))
        except: continue
    # 상승률 높은 순으로 정렬
    return sorted(performance, key=lambda x: x[1], reverse=True)

def get_portfolio_status():
    status_report = "\n💰 [나의 실시간 포트폴리오 현황]\n"
    for ticker, info in MY_PORTFOLIO.items():
        buy_price, amount, name = info
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1d')
        if hist.empty: continue
        current_price = hist['Close'].iloc[-1]
        
        profit_rate = ((current_price - buy_price) / buy_price) * 100
        profit_money = (current_price - buy_price) * amount
        currency = "$" if ticker == 'SMCI' else "원"
        status_report += f"• {name}: {profit_rate:+.2f}% ({profit_money:,.1f}{currency})\n"
    return status_report

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    report = ""

    # --- [오전 07~11시: 해외 증시 마감 리포트] ---
    if 7 <= hour < 11:
        report = f"🌎 [Morning] 해외 증시 마감 & 포트폴리오 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 1. 미국 지수
        indices = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '필라델피아반도체': '^SOX'}
        report += "📈 [미국 주요 지수]\n"
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{name}: {chg:+.2f}%  "
        
        # 2. 미국 시총 상위 대형주 상승률 TOP 5
        us_top = {'애플':'AAPL', '마이크로소프트':'MSFT', '엔비디아':'NVDA', '구글':'GOOGL', '아마존':'AMZN', '메타':'META', '테슬라':'TSLA'}
        us_perf = get_stock_performance(us_top)[:5]
        report += "\n\n📊 [미국 대형주 상승 순위]\n"
        for name, chg in us_perf:
            report += f"• {name}: {chg:+.2f}%\n"

        report += get_portfolio_status()
        report += "\n🧠 [종합 의견]\n- 미국 대형 기술주들의 수급에 따라 포트폴리오 내 SMCI와 테크TOP10 ETF의 변동성이 동조화될 수 있습니다. S&P500 위주의 안정적 비중을 유지하세요."

    # --- [오후 17~21시: 국내 증시 마감 리포트] ---
    elif 17 <= hour < 21:
        report = f"🇰🇷 [Evening] 국내 증시 마감 & 포트폴리오 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 1. 국내 지수
        indices = {'코스피': '^KS11', '코스닥': '^KQ11'}
        report += "📉 [국내 주요 지수]\n"
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{name}: {chg:+.2f}%  "
        
        # 2. 국내 시총 상위 대형주 상승률 TOP 5
        kr_top = {'삼성전자':'005930.KS', 'SK하이닉스':'000660.KS', 'LG엔솔':'373220.KS', '삼성바이오':'207940.KS', '현대차':'005380.KS', '기아':'000270.KS', '셀트리온':'068270.KS'}
        kr_perf = get_stock_performance(kr_top)[:5]
        report += "\n\n🏆 [국내 대형주 상승 순위]\n"
        for name, chg in kr_perf:
            report += f"• {name}: {chg:+.2f}%\n"

        report += get_portfolio_status()
        report += "\n🎯 [종합 의견]\n- 오늘 국내 시장은 시총 상위 종목들의 선별적 강세가 돋보였습니다. 포트폴리오 내 금 현물은 시장 불확실성 속에서 자산의 하방 경직성을 확보해주는 역할을 합니다."
    
    else:
        report = f"🔔 [알림] 현재 시간 {now_kst.strftime('%H:%M')}\n정기 브리핑 시간 외 실행되었습니다."

    return report

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    content = get_market_report()
    send_telegram(content)
