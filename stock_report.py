import yfinance as yf
import requests
import os
import feedparser
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =========================================================
# 텔레그램 설정 (GitHub Secrets 환경변수)
# =========================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# =========================================================
# 포트폴리오 설정
# [매수가, 수량, 종목명]
# =========================================================
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    '035420.KS': [35.9671, 17, '네이버'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

US_LARGE_CAPS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'V']
KR_LARGE_CAPS = [
    ('005930.KS', '삼성전자'), ('000660.KS', 'SK하이닉스'), ('373220.KS', 'LG에너지솔루션'),
    ('207940.KS', '삼성바이오로직스'), ('005380.KS', '현대차'), ('000270.KS', '기아'),
    ('006400.KS', '삼성SDI'), ('035420.KS', 'NAVER'), ('051910.KS', 'LG화학'), ('035720.KS', '카카오')
]

# =========================================================
# 분석 및 유틸리티 함수
# =========================================================
def safe_history(ticker, period='2d'):
    try:
        data = yf.Ticker(ticker).history(period=period)
        return data if not data.empty else None
    except:
        return None

def get_usdkrw():
    try:
        data = yf.Ticker("KRW=X").history(period='1d')
        return data['Close'].iloc[-1]
    except:
        return 1350  # 예외 발생 시 기본 환율

def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 오류: 토큰이나 ID가 없습니다.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': CHAT_ID,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            },
            timeout=20
        )
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def get_ai_analysis(ticker, data):
    """주가 데이터를 바탕으로 AI 차트 분석 의견 생성"""
    try:
        if data is None or len(data) < 20:
            return "💡 AI 분석: 데이터 축적 중입니다."

        curr_price = data['Close'].iloc[-1]
        ma20 = data['Close'].rolling(window=20).mean().iloc[-1]
        std = data['Close'].rolling(window=20).std().iloc[-1]
        
        distance = ((curr_price - ma20) / ma20) * 100
        volatility = "높음" if (std / ma20) > 0.02 else "안정적"

        if distance > 5:
            chart_opinion = "단기 과열 양상, 추격 매수 주의"
        elif distance < -5:
            chart_opinion = "과매도 구간 진입, 기술적 반등 기대"
        else:
            chart_opinion = "이평선 부근 수렴, 방향성 탐색 중"

        return f"💡 AI 분석: {chart_opinion} (변동성 {volatility})"
    except:
        return "💡 AI 분석: 시황 데이터 분석 엔진 오류"

def build_news_section(title, feeds, max_items=5):
    result = f"<b>{title}</b>\n\n"
    news_items = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:
                news_items.append((entry.title, entry.link))
        except: continue
    
    seen = set()
    count = 0
    for news_title, link in news_items:
        if news_title in seen: continue
        seen.add(news_title)
        result += f'• <a href="{link}">{escape_html(news_title[:70])}</a>\n'
        count += 1
        if count >= max_items: break
    return result

def get_macro_indicators():
    indicators = {'VIX': '^VIX', '미국채10년물': '^TNX', '달러인덱스': 'DX-Y.NYB'}
    result = "🌐 <b>[거시지표]</b>\n\n"
    for name, ticker in indicators.items():
        data = safe_history(ticker)
        if data is not None and len(data) >= 2:
            prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
            change = ((curr - prev) / prev) * 100
            emoji = "🔺" if change > 0 else "🔻"
            result += f"{emoji} {name}: {curr:,.2f} ({change:+.2f}%)\n"
    return result

def get_top_movers_us():
    changes = []
    for ticker in US_LARGE_CAPS:
        data = safe_history(ticker)
        if data is not None and len(data) >= 2:
            prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
            changes.append((ticker, ((curr - prev) / prev) * 100, curr))
    changes.sort(key=lambda x: x[1], reverse=True)
    result = "📈 <b>미국 상승 TOP5</b>\n"
    for t, p, c in changes[:5]: result += f"▲ {t}: {p:+.2f}% (${c:,.2f})\n"
    result += "\n📉 <b>미국 하락 TOP5</b>\n"
    for t, p, c in changes[-5:][::-1]: result += f"▼ {t}: {p:+.2f}% (${c:,.2f})\n"
    return result

def get_top_movers_kr():
    changes = []
    for ticker, name in KR_LARGE_CAPS:
        data = safe_history(ticker)
        if data is not None and len(data) >= 2:
            prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
            changes.append((name, ((curr - prev) / prev) * 100, curr))
    changes.sort(key=lambda x: x[1], reverse=True)
    result = "📈 <b>국내 상승 TOP5</b>\n"
    for n, p, c in changes[:5]: result += f"▲ {n}: {p:+.2f}% ({c:,.0f}원)\n"
    result += "\n📉 <b>국내 하락 TOP5</b>\n"
    for n, p, c in changes[-5:][::-1]: result += f"▼ {n}: {p:+.2f}% ({c:,.0f}원)\n"
    return result

def get_portfolio_summary():
    usdkrw = get_usdkrw()
    total_buy, total_eval = 0, 0
    result = "💼 <b>[전문가 포트폴리오 진단]</b>\n"
    result += f"💱 기준 환율: 1$ = {usdkrw:,.1f}원\n\n"

    for ticker, info in MY_PORTFOLIO.items():
        buy_price, qty, name = info
        # 분석을 위해 데이터 기간을 1개월(1mo)로 가져옴
        data = safe_history(ticker, period='1mo') 
        
        if data is None or data.empty:
            continue

        curr = data['Close'].iloc[-1]
        is_us = not ticker.endswith('.KS')
        
        if is_us:
            b_krw, c_krw = buy_price * usdkrw, curr * usdkrw
            t_buy, t_eval = b_krw * qty, c_krw * qty
            cur_txt = f"${curr:,.2f} ({c_krw:,.0f}원)"
        else:
            t_buy, t_eval = buy_price * qty, curr * qty
            cur_txt = f"{curr:,.0f}원"

        profit = t_eval - t_buy
        rate = (profit / t_buy) * 100
        total_buy += t_buy
        total_eval += t_eval

        # AI 분석 호출
        ai_opinion = get_ai_analysis(ticker, data)

        result += (
            f"<b>{name}</b> ({ticker})\n"
            f"수익률: {rate:+.2f}% / 평가: {cur_txt}\n"
            f"{ai_opinion}\n"
            f"──────────────────\n"
        )
    
    t_profit = total_eval - total_buy
    t_rate = (t_profit / total_buy) * 100
    summary_opinion = "강력 홀딩" if t_rate > 0 else "비중 조절 검토"
    
    result += (
        f"\n📊 <b>종합 수익률: {t_rate:+.2f}%</b>\n"
        f"총 평가손익: {t_profit:+,.0f}원\n"
        f"🎯 AI 종합 전략: <b>{summary_opinion}</b>"
    )
    return result

# =========================================================
# 메인 실행 로직
# =========================================================
if __name__ == "__main__":
    # 한국 시간 설정
    now_kst = datetime.utcnow() + timedelta(hours=9)
    current_hour = now_kst.hour
    
    print(f"실행 시각(KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")

    # 오전 브리핑 (00:00 ~ 11:59 실행 시)
    if current_hour < 12:
        send_telegram(f"🌙 <b>해외증시 브리핑</b> ({now_kst.strftime('%m/%d %H:%M')})")
        send_telegram(get_macro_indicators())
        send_telegram(get_top_movers_us())
        
        us_news = build_news_section("📰 미국 주요 뉴스", [
            'https://news.google.com/rss/search?q=미국증시&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=엔비디아&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=S&P500&hl=ko&gl=KR&ceid=KR:ko'
        ])
        send_telegram(us_news)
        send_telegram(get_portfolio_summary())

    # 오후 브리핑 (12:00 ~ 23:59 실행 시)
    else:
        send_telegram(f"🌞 <b>국내증시 브리핑</b> ({now_kst.strftime('%m/%d %H:%M')})")
        send_telegram(get_macro_indicators())
        send_telegram(get_top_movers_kr())
        
        kr_news = build_news_section("📰 국내 주요 뉴스", [
            'https://news.google.com/rss/search?q=코스피&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=반도체&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=환율전망&hl=ko&gl=KR&ceid=KR:ko'
        ])
        send_telegram(kr_news)
        send_telegram(get_portfolio_summary())
