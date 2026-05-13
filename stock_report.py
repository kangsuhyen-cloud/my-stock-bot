# =========================================================
# 설치 필요 패키지
# pip install yfinance requests feedparser beautifulsoup4
# =========================================================

import yfinance as yf
import requests
import os
import feedparser
from datetime import datetime, timedelta

# =========================================================
# 텔레그램 설정
# GitHub Secrets 등록 필요
# TELEGRAM_TOKEN
# CHAT_ID
# =========================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# =========================================================
# 포트폴리오
# =========================================================
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

# =========================================================
# 미국 대형주
# =========================================================
US_LARGE_CAPS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'META', 'TSLA', 'BRK-B', 'JPM', 'V'
]

# =========================================================
# 국내 대형주
# =========================================================
KR_LARGE_CAPS = [
    ('005930.KS', '삼성전자'),
    ('000660.KS', 'SK하이닉스'),
    ('373220.KS', 'LG에너지솔루션'),
    ('207940.KS', '삼성바이오로직스'),
    ('005380.KS', '현대차'),
    ('000270.KS', '기아'),
    ('006400.KS', '삼성SDI'),
    ('035420.KS', 'NAVER'),
    ('051910.KS', 'LG화학'),
    ('035720.KS', '카카오')
]

# =========================================================
# 안전 조회
# =========================================================
def safe_history(ticker, period='2d'):

    try:

        data = yf.Ticker(ticker).history(period=period)

        if data.empty:
            return None

        return data

    except Exception as e:

        print(f"{ticker} 오류: {e}")

        return None


# =========================================================
# 환율 조회
# =========================================================
def get_usdkrw():

    try:

        data = yf.Ticker("KRW=X").history(period='1d')

        if data.empty:
            return 1350

        return data['Close'].iloc[-1]

    except:
        return 1350


# =========================================================
# HTML 특수문자 처리
# =========================================================
def escape_html(text):

    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    return text


# =========================================================
# 뉴스 섹션 생성
# =========================================================
def build_news_section(title, feeds, max_items=5):

    result = f"{title}\n\n"

    news_items = []

    for url in feeds:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:2]:

                news_items.append(
                    (entry.title, entry.link)
                )

        except:
            continue

    seen = set()

    count = 0

    for news_title, link in news_items:

        if news_title in seen:
            continue

        seen.add(news_title)

        safe_title = escape_html(news_title[:70])

        result += (
            f'• <a href="{link}">{safe_title}</a>\n'
        )

        count += 1

        if count >= max_items:
            break

    return result


# =========================================================
# 거시지표
# =========================================================
def get_macro_indicators():

    indicators = {
        'VIX 공포지수': '^VIX',
        '미국채10년물': '^TNX',
        '달러인덱스': 'DX-Y.NYB'
    }

    result = "🌐 [거시지표]\n\n"

    for name, ticker in indicators.items():

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            change = ((curr - prev) / prev) * 100

            emoji = "🔺" if change > 0 else "🔻"

            result += (
                f"{emoji} {name}: "
                f"{curr:,.2f} "
                f"({change:+.2f}%)\n"
            )

    return result


# =========================================================
# 미국 상승/하락
# =========================================================
def get_top_movers_us():

    changes = []

    for ticker in US_LARGE_CAPS:

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            pct = ((curr - prev) / prev) * 100

            changes.append((ticker, pct, curr))

    changes.sort(key=lambda x: x[1], reverse=True)

    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]

    result = "📈 [미국 대형주 상승 TOP5]\n\n"

    for t, p, c in top5:

        result += (
            f"▲ {t}: "
            f"{p:+.2f}% "
            f"(${c:,.2f})\n"
        )

    result += "\n📉 [미국 대형주 하락 TOP5]\n\n"

    for t, p, c in bottom5:

        result += (
            f"▼ {t}: "
            f"{p:+.2f}% "
            f"(${c:,.2f})\n"
        )

    return result


# =========================================================
# 국내 상승/하락
# =========================================================
def get_top_movers_kr():

    changes = []

    for ticker, name in KR_LARGE_CAPS:

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            pct = ((curr - prev) / prev) * 100

            changes.append((name, pct, curr))

    changes.sort(key=lambda x: x[1], reverse=True)

    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]

    result = "📈 [국내 대형주 상승 TOP5]\n\n"

    for n, p, c in top5:

        result += (
            f"▲ {n}: "
            f"{p:+.2f}% "
            f"({c:,.0f}원)\n"
        )

    result += "\n📉 [국내 대형주 하락 TOP5]\n\n"

    for n, p, c in bottom5:

        result += (
            f"▼ {n}: "
            f"{p:+.2f}% "
            f"({c:,.0f}원)\n"
        )

    return result


# =========================================================
# 포트폴리오
# =========================================================
def get_portfolio_summary():

    usdkrw = get_usdkrw()

    total_buy = 0
    total_eval = 0

    result = "💼 [포트폴리오 현황]\n\n"

    result += (
        f"💱 환율: "
        f"1달러 = {usdkrw:,.0f}원\n\n"
    )

    for ticker, info in MY_PORTFOLIO.items():

        buy_price, qty, name = info

        data = safe_history(ticker, '1d')

        if data is None:
            continue

        curr = data['Close'].iloc[-1]

        is_us = not ticker.endswith('.KS')

        if is_us:

            buy_price_krw = buy_price * usdkrw
            curr_price_krw = curr * usdkrw

            total_buy_price = buy_price_krw * qty
            total_eval_price = curr_price_krw * qty

            current_price_text = (
                f"${curr:,.2f} "
                f"({curr_price_krw:,.0f}원)"
            )

        else:

            total_buy_price = buy_price * qty
            total_eval_price = curr * qty

            current_price_text = (
                f"{curr:,.0f}원"
            )

        profit = (
            total_eval_price - total_buy_price
        )

        rate = (
            (profit / total_buy_price) * 100
        )

        total_buy += total_buy_price
        total_eval += total_eval_price

        result += (
            f"━━━━━━━━━━━━━━\n"
            f"{name}\n"
            f"현재가: {current_price_text}\n"
            f"수익률: {rate:+.2f}%\n"
            f"총매수금액: {total_buy_price:,.0f}원\n"
            f"현재평가금액: {total_eval_price:,.0f}원\n"
            f"평가손익: {profit:+,.0f}원\n\n"
        )

    total_profit = total_eval - total_buy

    total_rate = (
        (total_profit / total_buy) * 100
    )

    result += (
        "══════════════\n"
        f"총매수금액: {total_buy:,.0f}원\n"
        f"총평가금액: {total_eval:,.0f}원\n"
        f"총평가손익: {total_profit:+,.0f}원\n"
        f"총수익률: {total_rate:+.2f}%\n"
    )

    return result


# =========================================================
# 텔레그램 전송
# =========================================================
def send_telegram(text):

    if not TELEGRAM_TOKEN or not CHAT_ID:

        print("텔레그램 TOKEN 또는 CHAT_ID 없음")

        return

    try:

        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                'chat_id': CHAT_ID,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            },
            timeout=20
        )

        print(response.status_code)

    except Exception as e:

        print(f"텔레그램 전송 실패: {e}")


# =========================================================
# 실행
# =========================================================
if __name__ == "__main__":

    now_kst = (
        datetime.utcnow() + timedelta(hours=9)
    )

    hour = now_kst.hour

    print("프로그램 시작")
    print(f"현재 시간: {hour}시")

    is_morning = 7 <= hour < 11
    is_evening = 17 <= hour < 23

    if is_morning or is_evening:

        # =================================================
        # 헤더
        # =================================================
        now_text = now_kst.strftime('%Y-%m-%d %H:%M')

        if is_morning:

            header = (
                f"🌙 해외증시 브리핑\n"
                f"📅 {now_text} KST"
            )

        else:

            header = (
                f"🌞 국내증시 브리핑\n"
                f"📅 {now_text} KST"
            )

        send_telegram(header)

        # =================================================
        # 시장 요약
        # =================================================
        market_report = "📊 시장 요약\n\n"

        market_report += get_macro_indicators()

        if is_morning:
            market_report += get_top_movers_us()
        else:
            market_report += get_top_movers_kr()

        send_telegram(market_report)

        # =================================================
        # 주요 뉴스
        # =================================================
        if is_morning:

            news_report = build_news_section(
                "📰 미국 주요 뉴스",
                [
                    'https://news.google.com/rss/search?q=미국증시&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=엔비디아&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=연준금리&hl=ko&gl=KR&ceid=KR:ko'
                ]
            )

        else:

            news_report = build_news_section(
                "📰 국내 주요 뉴스",
                [
                    'https://news.google.com/rss/search?q=코스피&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=반도체&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=2차전지&hl=ko&gl=KR&ceid=KR:ko'
                ]
            )

        send_telegram(news_report)

        # =================================================
        # 글로벌 이벤트
        # =================================================
        event_report = build_news_section(
            "🌎 글로벌 특수 이벤트",
            [
                'https://news.google.com/rss/search?q=미국+CPI발표&hl=ko&gl=KR&ceid=KR:ko',
                'https://news.google.com/rss/search?q=FOMC회의&hl=ko&gl=KR&ceid=KR:ko',
                'https://news.google.com/rss/search?q=트럼프중국방문&hl=ko&gl=KR&ceid=KR:ko',
                'https://news.google.com/rss/search?q=엔비디아실적발표&hl=ko&gl=KR&ceid=KR:ko'
            ]
        )

        send_telegram(event_report)

        # =================================================
        # 포트폴리오
        # =================================================
        portfolio_report = get_portfolio_summary()

        send_telegram(portfolio_report)

        # =================================================
        # 일정
        # =================================================
        if is_morning:

            kr_schedule = build_news_section(
                "🇰🇷 국내 주요 일정",
                [
                    'https://news.google.com/rss/search?q=한국은행+금통위&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=한국+수출입동향&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=코스피+일정&hl=ko&gl=KR&ceid=KR:ko'
                ]
            )

            send_telegram(kr_schedule)

        else:

            global_schedule = build_news_section(
                "🌎 해외 주요 일정",
                [
                    'https://news.google.com/rss/search?q=미국+CPI발표&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=FOMC회의&hl=ko&gl=KR&ceid=KR:ko',
                    'https://news.google.com/rss/search?q=미국+금리발표&hl=ko&gl=KR&ceid=KR:ko'
                ]
            )

            send_telegram(global_schedule)

    else:

        print("현재는 발송 시간이 아닙니다.")
