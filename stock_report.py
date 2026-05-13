# =========================================================
# 필요한 패키지
# pip install yfinance requests feedparser beautifulsoup4
# =========================================================

import yfinance as yf
import requests
import os
import feedparser
from bs4 import BeautifulSoup
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

    except:
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
# 미국채 금리 / 달러 / VIX
# =========================================================
def get_macro_indicators():

    indicators = {
        'VIX': '^VIX',
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

            result += (
                f"• {name}: "
                f"{curr:,.2f} "
                f"({change:+.2f}%)\n"
            )

    return result


# =========================================================
# 상승/하락 종목
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

    result = "📈 [미국 대형주 TOP]\n"

    for t, p, c in top5:
        result += f"▲ {t}: {p:+.2f}% (${c:,.2f})\n"

    result += "\n📉 [미국 대형주 하락]\n"

    for t, p, c in bottom5:
        result += f"▼ {t}: {p:+.2f}% (${c:,.2f})\n"

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

    result = "📈 [국내 대형주 TOP]\n"

    for n, p, c in top5:
        result += f"▲ {n}: {p:+.2f}% ({c:,.0f}원)\n"

    result += "\n📉 [국내 대형주 하락]\n"

    for n, p, c in bottom5:
        result += f"▼ {n}: {p:+.2f}% ({c:,.0f}원)\n"

    return result


# =========================================================
# 뉴스
# =========================================================
def get_news(is_morning):

    if is_morning:

        feeds = [
            'https://news.google.com/rss/search?q=미국증시',
            'https://news.google.com/rss/search?q=엔비디아',
            'https://news.google.com/rss/search?q=연준'
        ]

    else:

        feeds = [
            'https://news.google.com/rss/search?q=코스피',
            'https://news.google.com/rss/search?q=반도체',
            'https://news.google.com/rss/search?q=2차전지'
        ]

    result = "📰 [주요 뉴스]\n"

    news_items = []

    for url in feeds:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:2]:
                news_items.append(entry.title)

        except:
            continue

    seen = set()

    for title in news_items:

        if title not in seen:

            seen.add(title)

            result += f"• {title[:80]}\n"

    return result


# =========================================================
# 특수 이벤트
# =========================================================
def get_special_events():

    feeds = [
        'https://news.google.com/rss/search?q=트럼프+중국방문',
        'https://news.google.com/rss/search?q=미중정상회담',
        'https://news.google.com/rss/search?q=FOMC',
        'https://news.google.com/rss/search?q=CPI',
        'https://news.google.com/rss/search?q=연준'
    ]

    result = "🌎 [글로벌 특수 이벤트]\n"

    collected = []

    for url in feeds:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:1]:
                collected.append(entry.title)

        except:
            continue

    seen = set()

    for title in collected:

        if title not in seen:

            seen.add(title)

            result += f"• {title[:80]}\n"

    return result


# =========================================================
# 실적 발표 일정
# =========================================================
def get_earnings_schedule():

    earnings = [
        ("NVDA", "엔비디아"),
        ("AAPL", "애플"),
        ("TSLA", "테슬라"),
        ("MSFT", "마이크로소프트")
    ]

    result = "📌 [주요 실적 일정]\n"

    now = datetime.utcnow() + timedelta(hours=9)

    for idx, (ticker, name) in enumerate(earnings):

        date = (
            now + timedelta(days=idx + 1)
        ).strftime('%m/%d')

        result += (
            f"• {date} "
            f"{name}({ticker}) "
            f"실적발표 예정\n"
        )

    return result


# =========================================================
# AI 느낌 시장 요약
# =========================================================
def get_ai_market_comment(is_morning):

    if is_morning:

        return (
            "💡 [AI 시황 코멘트]\n"
            "• 미국 기술주 중심 상승세 지속 여부 주목\n"
            "• 반도체 및 AI 관련주 변동성 확대 가능성\n"
            "• 금리 민감주 중심 수급 변화 체크 필요\n"
        )

    else:

        return (
            "💡 [AI 시황 코멘트]\n"
            "• 외국인 수급과 환율 방향성 중요 구간\n"
            "• 반도체 중심 코스피 변동성 확대 가능성\n"
            "• 미국 선물지수 흐름 체크 필요\n"
        )


# =========================================================
# 포트폴리오
# =========================================================
def get_portfolio_summary():

    usdkrw = get_usdkrw()

    total_invest = 0
    total_value = 0

    result = "💼 [포트폴리오 현황]\n"

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
            curr_krw = curr * usdkrw

            invest = buy_price_krw * qty
            value = curr_krw * qty

            current_price = (
                f"${curr:,.2f} "
                f"/ {curr_krw:,.0f}원"
            )

        else:

            invest = buy_price * qty
            value = curr * qty

            current_price = f"{curr:,.0f}원"

        profit = value - invest

        rate = (
            (profit / invest) * 100
        )

        total_invest += invest
        total_value += value

        result += (
            f"• {name}\n"
            f"현재가: {current_price}\n"
            f"수익률: {rate:+.2f}%\n"
            f"평가손익: {profit:+,.0f}원\n\n"
        )

    total_profit = total_value - total_invest

    total_rate = (
        (total_profit / total_invest) * 100
    )

    result += (
        "━━━━━━━━━━━━━━\n"
        f"총 평가손익: {total_profit:+,.0f}원\n"
        f"총 수익률: {total_rate:+.2f}%\n"
    )

    return result


# =========================================================
# 국내 일정
# =========================================================
def get_kr_schedule():

    today = (
        datetime.utcnow() + timedelta(hours=9)
    ).date()

    result = (
        "🇰🇷 [국내 주요 일정]\n"
        "━━━━━━━━━━━━━━\n"
    )

    schedules = [

        (
            today.strftime('%m/%d'),
            "08:00",
            "한국 수출입 동향 발표"
        ),

        (
            (today + timedelta(days=1)).strftime('%m/%d'),
            "10:00",
            "한국은행 금통위"
        ),

        (
            (today + timedelta(days=2)).strftime('%m/%d'),
            "장마감",
            "코스피 변동성 체크"
        )

    ]

    for d, t, c in schedules:

        result += (
            f"📅 {d} {t}\n"
            f"• {c}\n\n"
        )

    return result


# =========================================================
# 해외 일정
# =========================================================
def get_global_schedule():

    today = (
        datetime.utcnow() + timedelta(hours=9)
    ).date()

    result = (
        "🌎 [해외 주요 일정]\n"
        "━━━━━━━━━━━━━━\n"
    )

    schedules = [

        (
            today.strftime('%m/%d'),
            "21:30",
            "미국 CPI 발표"
        ),

        (
            (today + timedelta(days=1)).strftime('%m/%d'),
            "03:00",
            "FOMC 의사록 공개"
        ),

        (
            (today + timedelta(days=2)).strftime('%m/%d'),
            "23:00",
            "연준 위원 연설"
        )

    ]

    for d, t, c in schedules:

        result += (
            f"📅 {d} {t}\n"
            f"• {c}\n\n"
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

    market_type = (
        "🌙 해외증시 브리핑"
        if is_morning
        else "🌞 국내증시 브리핑"
    )

    result = (
        f"{'═'*35}\n"
        f"{market_type}\n"
        f"📅 {now_kst.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"{'═'*35}\n\n"
    )

    # 주요지수
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

            result += (
                f"• {name}: "
                f"{curr:,.2f} "
                f"({change:+.2f}%)\n"
            )

    result += "\n"

    # 거시지표
    result += get_macro_indicators()
    result += "\n"

    # 상승하락
    if is_morning:
        result += get_top_movers_us()
    else:
        result += get_top_movers_kr()

    result += "\n"

    # 뉴스
    result += get_news(is_morning)
    result += "\n"

    # 특수 이벤트
    result += get_special_events()
    result += "\n"

    # 실적일정
    result += get_earnings_schedule()
    result += "\n"

    # AI 코멘트
    result += get_ai_market_comment(is_morning)
    result += "\n"

    # 포트폴리오
    result += get_portfolio_summary()

    return result


# =========================================================
# 텔레그램 전송
# =========================================================
def send_telegram(text):

    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 설정 오류")
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
            print(response.text)

        except Exception as e:

            print(e)


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

    # 오전
    if 7 <= hour < 11:

        report = get_market_report()

        send_telegram(report)

        send_telegram(
            get_kr_schedule()
        )

    # 오후
    elif 17 <= hour < 23:

        report = get_market_report()

        send_telegram(report)

        send_telegram(
            get_global_schedule()
        )

    else:

        print("발송 시간 아님")
