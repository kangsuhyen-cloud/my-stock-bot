import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오 설정] 매수단가, 보유수량, 이름 순서입니다.
# 국내 종목 티커: KODEX S&P500(402380), TIGER 테크TOP10(381170), ACE 금현물(411060), TIGER S&P500(360750)
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

def get_portfolio_status():
    status_report = "\n💰 [나의 실시간 포트폴리오 현황]\n"
    total_profit_sum = 0
    
    for ticker, info in MY_PORTFOLIO.items():
        buy_price, amount, name = info
        stock = yf.Ticker(ticker)
        # 실시간 가격 가져오기 (데이터 지연 가능성 고려)
        hist = stock.history(period='1d')
        if hist.empty: continue
        current_price = hist['Close'].iloc[-1]
        
        profit_rate = ((current_price - buy_price) / buy_price) * 100
        profit_money = (current_price - buy_price) * amount
        
        currency = "$" if ticker == 'SMCI' else "원"
        status_report += f"• {name}: {profit_rate:+.2f}% ({profit_money:,.1f}{currency})\n"
        
    return status_report

def get_realtime_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url)
        items = r.text.split('<item>')[1:4]
        return "\n".join([f"• {item.split('<title>')[1].split('</title>')[0]}\n  🔗 {item.split('<link>')[1].split('</link>')[0]}" for item in items])
    except:
        return "• 실시간 뉴스를 가져오지 못했습니다."

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    report = ""

    # 시장 지수 데이터
    indices = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '코스피': '^KS11'}
    idx_str = ""
    for name, tk in indices.items():
        d = yf.Ticker(tk).history(period='2d')
        chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
        idx_str += f"{name} {chg:+.2f}%  "

    if 7 <= hour < 11:
        report = f"🌎 [Morning] 증시 & 포트폴리오 분석 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        report += f"📈 [주요 지수]\n{idx_str}\n"
        report += get_portfolio_status()
        report += "\n📰 [주요 뉴스]\n" + get_realtime_news("미국 증시 반도체 S&P500")
        report += "\n\n🧠 [보유 종목 분석 및 종합 의견]\n"
        report += "- SMCI 코멘트: 현재 인공지능 인프라 수요가 견조함에 따라 고성장세를 유지 중이나, 기술적 변동성이 큰 종목입니다. 매수 단가 대비 리스크 관리가 필요합니다.\n"
        report += "- 지수 ETF 코멘트: S&P500 비중이 높으신 편입니다. 이는 장기적으로 시장 평균 수익률을 추종하는 안정적인 전략이며, 자산 1억 달성 가시성을 높여줍니다.\n"
        report += "- 전략: 금 현물을 통해 인플레이션 및 환율 리스크를 헤지하고 계신 점이 인상적입니다. 현재 포트폴리오는 '안정성 7 : 공격성 3'의 균형 잡힌 구조입니다."

    elif 17 <= hour < 21:
        report = f"🇰🇷 [Evening] 국내 증시 & 포트폴리오 분석 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        report += f"📉 [지수 현황]\n{idx_str}\n"
        report += get_portfolio_status()
        report += "\n🔥 [실시간 이슈]\n" + get_realtime_news("국내 증시 특징주")
        report += "\n\n🎯 [보유 종목 분석 및 종합 의견]\n"
        report += "- 국내 상장 해외 ETF는 환율의 영향을 받습니다. 최근 환율 추이를 고려할 때 원화 자산 가치 방어 측면에서 긍정적입니다.\n"
        report += "- TOP10 ETF는 빅테크 수급에 민감하므로 미 증시 개장 전 기술주 선물 지수를 체크하는 습관이 도움이 됩니다.\n"
        report += "- 종합: 오늘 하루 고생하셨습니다. 카페 운영 등 본업에 집중하시면서, 현재의 우량 자산 중심 포트폴리오를 장기 보유하시는 것을 추천드립니다."
    
    return report

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    content = get_market_report()
    send_telegram(content)
