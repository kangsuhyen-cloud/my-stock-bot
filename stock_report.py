# =========================================================
# 필요한 패키지
# pip install yfinance requests feedparser beautifulsoup4
# =========================================================

import yfinance as yf
import requests
import os
import feedparser
from datetime import datetime, timedelta

# =========================================================
# 텔레그램 설정
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
# 해외 대형주
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
# 안전한 데이터 조회
# =========================================================
def safe_history(ticker, period='2d'):

    try:

        data = yf.Ticker(ticker).history(period=period)

        if data.empty:
            return None

        return data

    except Exception as e:

        print(f"{ticker} 조회 실패: {e}")

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
# 링크 축약
# =========================================================
def shorten_link(link):

    try:

        if "news.google.com" in link:
            return "Google 뉴스 바로가기"

        return link[:50]

    except:
        return "링크 확인"


# =========================================================
# 거시지표
# =========================================================
def get_macro_indicators():

    indicators = {
        'VIX 공포지수': '^VIX',
        '미국채10년물': '^TNX',
        '달러인덱스': 'DX-Y.NYB'
    }

    result = "🌐 [거시지표]\n"

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
# 해외 상승/하락
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

    result = "📈 [미국 대형주 상승 TOP5]\n"

    for t, p, c in top5:

        result += (
            f"▲ {t}: "
            f"{p:+.2f}% "
            f"(${c:,.2f})\n"
        )

    result += "\n📉 [미국 대형주 하락 TOP5]\n"

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

    result = "📈 [국내 대형주 상승 TOP5]\n"

    for n, p, c in top5:

        result += (
            f"▲ {n}: "
            f"{p:+.2f}% "
            f"({c:,.0f}원)\n"
        )

    result += "\n📉 [국내 대형주 하락 TOP5]\n"

    for n, p, c in bottom5:

        result += (
            f"▼ {n}: "
            f"{p:+.2f}% "
            f"({c:,.0f}원)\n"
        )

    return result


# =========================================================
# 뉴스 공통
# =========================================================
def get_news(is_morning):

    if is_morning:

        feeds = [
            'https://news.google.com/rss/search?q=미국증시&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=엔비디아&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=연준금리&hl=ko&gl=KR&ceid=KR:ko'
        ]

    else:

        feeds = [
            'https://news.google.com/rss/search?q=코스피&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=반도체&hl=ko&gl=KR&ceid=KR:ko',
            'https://news.google.com/rss/search?q=2차전지&hl=ko&gl=KR&ceid=KR:ko'
        ]

    result = "📰 [주요 뉴스]\n"

    news_items = []

    for url in feeds:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:1]:

                news_items.append(
                    (entry.title, entry.link)
                )

        except:
            continue

    seen = set()

    for title, link in news_items:

        if title not in seen:

            seen.add(title)

            short = shorten_link(link)

            result += (
                f"• {title[:65]}\n"
                f"🔗 {short}\n\n"
            )

    return result


# =========================================================
# 특수 이벤트
# =========================================================
def get_special_events():

    feeds = [

        'https://news.google.com/rss/search?q=미국+CPI발표&hl=ko&gl=KR&ceid=KR:ko',

        'https://news.google.com/rss/search?q=FOMC회의&hl=ko&gl=KR&ceid=KR:ko',

        'https://news.google.com/rss/search?q=트럼프중국방문&hl=ko&gl=KR&ceid=KR:ko',

        'https://news.google.com/rss/search?q=엔비디아실적발표&hl=ko&gl=KR&ceid=KR:ko'
    ]

    result = "🌎 [글로벌 특수 이벤트]\n"

    items = []

    for url in feeds:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:1]:

                items.append(
                    (entry.title, entry.link)
                )

        except:
            continue

    seen = set()

    for title, link in items:

        if title not in seen:

            seen.add(title)

            short = shorten_link(link)

            result += (
                f"• {title[:65]}\n"
                f"🔗 {short}\n\n"
            )

    return result


# =========================================================
# 포트폴리오
# =========================================================
def get_portfolio_summary():

    usdkrw = get_usdkrw()

    total_buy = 0
    total_eval = 0

    result = "💼 [포트폴리오 현황]\n"

    result += (
        f"💱 환율: 1달러 = "
        f"{usdkrw:,.0f}원\n\n"
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
# 메인 리포트
# =========================================================
def get_market_report():

    now_kst = (
        datetime.utcnow() + timedelta(hours=9)
    )

    hour = now_kst.hour

    is_morning = 7 <= hour < 11

    title = (
        "🌙 해외증시 브리핑"
        if is_morning
        else "🌞 국내증시 브리핑"
    )

    result = (
        f"{'═'*35}\n"
        f"{title}\n"
        f"📅 {now_kst.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"{'═'*35}\n\n"
    )

    # 주요 지수
    result += "📊 [주요 지수]\n"

    if is_morning:

        symbols = {
            '나스닥': '^IXIC',
            'S&P500': '^GSPC',
            '다우': '^DJI'
        }

    else:

        symbols = {
            '코스피': '^KS11',
            '코스닥': '^KQ11'
        }

    for name, ticker in symbols.items():

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            change = (
                ((curr - prev) / prev) * 100
            )

            emoji = "🔺" if change > 0 else "🔻"

            result += (
                f"{emoji} {name}: "
                f"{curr:,.2f} "
                f"({change:+.2f}%)\n"
            )

    result += "\n"

    result += get_macro_indicators()
    result += "\n"

    if is_morning:
        result += get_top_movers_us()
    else:
        result += get_top_movers_kr()

    result += "\n"

    result += get_news(is_morning)
    result += "\n"

    result += get_special_events()
    result += "\n"

    result += get_portfolio_summary()

    return result


# =========================================================
# 텔레그램 전송
# =========================================================
def send_telegram(text):

    if not TELEGRAM_TOKEN or not CHAT_ID:

        print("텔레그램 TOKEN 또는 CHAT_ID 오류")

        return

    max_len = 3500

    messages = [
        text[i:i+max_len]
        for i in range(0, len(text), max_len)
    ]

    for msg in messages:

        try:

            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    'chat_id': CHAT_ID,
                    'text': msg
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

    if (7 <= hour < 11) or (17 <= hour < 23):

        report = get_market_report()

        print(report)

        send_telegram(report)

    else:

        print("현재는 발송 시간이 아닙니다.")
