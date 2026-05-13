import yfinance as yf
import requests
import os
from datetime import datetime, timedelta
import feedparser

# =========================
# 보안 설정
# =========================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# =========================
# 포트폴리오 정보
# =========================
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

# =========================
# 해외 대형주
# =========================
US_LARGE_CAPS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'META', 'TSLA', 'BRK-B', 'JPM', 'V'
]

# =========================
# 국내 대형주
# =========================
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


# =========================
# 안전한 데이터 조회 함수
# =========================
def safe_history(ticker, period='2d'):
    try:
        data = yf.Ticker(ticker).history(period=period)

        if data.empty:
            print(f"[데이터 없음] {ticker}")
            return None

        return data

    except Exception as e:
        print(f"[조회 실패] {ticker}: {e}")
        return None


# =========================
# 해외 상승/하락 TOP
# =========================
def get_top_movers_us():

    changes = []

    for ticker in US_LARGE_CAPS:

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            pct = ((curr - prev) / prev) * 100

            changes.append((ticker, pct, curr))

    if not changes:
        return "📈 해외 데이터 조회 실패\n"

    changes.sort(key=lambda x: x[1], reverse=True)

    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]

    result = "📈 [해외 대형주 상승 TOP 5]\n"

    for t, p, c in top5:
        result += f"• {t}: {p:+.2f}% (${c:,.2f})\n"

    result += "\n📉 [해외 대형주 하락 TOP 5]\n"

    for t, p, c in bottom5:
        result += f"• {t}: {p:+.2f}% (${c:,.2f})\n"

    return result


# =========================
# 국내 상승/하락 TOP
# =========================
def get_top_movers_kr():

    changes = []

    for ticker, name in KR_LARGE_CAPS:

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            pct = ((curr - prev) / prev) * 100

            changes.append((name, pct, curr))

    if not changes:
        return "📉 국내 데이터 조회 실패\n"

    changes.sort(key=lambda x: x[1], reverse=True)

    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]

    result = "📈 [국내 대형주 상승 TOP 5]\n"

    for n, p, c in top5:
        result += f"• {n}: {p:+.2f}% ({c:,.0f}원)\n"

    result += "\n📉 [국내 대형주 하락 TOP 5]\n"

    for n, p, c in bottom5:
        result += f"• {n}: {p:+.2f}% ({c:,.0f}원)\n"

    return result


# =========================
# 글로벌 뉴스
# =========================
def get_global_news():

    feeds = [
        'https://news.google.com/rss/search?q=미국+증시&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=글로벌+경제&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=연준+금리&hl=ko&gl=KR&ceid=KR:ko'
    ]

    news_items = []

    for url in feeds:

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:2]:
                news_items.append((entry.title, entry.link))

        except Exception as e:
            print(f"뉴스 오류: {e}")

    seen = set()

    result = "🌐 [글로벌 주요 뉴스]\n"

    count = 0

    for title, link in news_items:

        if title not in seen:

            seen.add(title)

            short_title = title[:50] + "..." if len(title) > 50 else title

            result += f"• {short_title}\n{link}\n\n"

            count += 1

        if count >= 5:
            break

    return result


# =========================
# 국내 뉴스
# =========================
def get_kr_market_news():

    feeds = [
        'https://news.google.com/rss/search?q=코스피+주도주&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=반도체+주가&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=2차전지+주가&hl=ko&gl=KR&ceid=KR:ko'
    ]

    news_items = []

    for url in feeds:

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:2]:
                news_items.append((entry.title, entry.link))

        except Exception as e:
            print(f"뉴스 오류: {e}")

    seen = set()

    result = "🏭 [국내 주도섹터 및 이슈]\n"

    count = 0

    for title, link in news_items:

        if title not in seen:

            seen.add(title)

            short_title = title[:50] + "..." if len(title) > 50 else title

            result += f"• {short_title}\n{link}\n\n"

            count += 1

        if count >= 5:
            break

    return result


# =========================
# 포트폴리오 총괄
# =========================
def get_portfolio_summary():

    total_invest = 0
    total_value = 0

    result = "\n💼 [포트폴리오 현황]\n"

    for ticker, info in MY_PORTFOLIO.items():

        buy_price, qty, name = info

        data = safe_history(ticker, '1d')

        if data is None:
            continue

        curr = data['Close'].iloc[-1]

        invest = buy_price * qty
        value = curr * qty

        profit = value - invest
        rate = (profit / invest) * 100

        total_invest += invest
        total_value += value

        result += (
            f"• {name}\n"
            f"  현재가: {curr:,.2f}\n"
            f"  수익률: {rate:+.2f}%\n"
            f"  평가손익: {profit:+,.0f}\n\n"
        )

    if total_invest > 0:

        total_profit = total_value - total_invest
        total_rate = (total_profit / total_invest) * 100

        result += (
            "━━━━━━━━━━━━━━\n"
            f"총 투자금: {total_invest:,.0f}\n"
            f"총 평가금: {total_value:,.0f}\n"
            f"총 수익률: {total_rate:+.2f}%\n"
        )

    return result


# =========================
# 메인 리포트
# =========================
def get_market_reports():

    now_kst = datetime.utcnow() + timedelta(hours=9)

    hour = now_kst.hour

    is_morning = 7 <= hour < 11

    market_type = "🌙 해외" if is_morning else "🌞 국내"

    report = (
        f"{'═' * 30}\n"
        f"{market_type} 증시 마감 리포트\n"
        f"📅 {now_kst.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"{'═' * 30}\n\n"
    )

    # 주요지수
    report += "📊 [주요 지수]\n"

    symbols = (
        {'나스닥': '^IXIC', 'S&P500': '^GSPC', '다우': '^DJI'}
        if is_morning
        else {'코스피': '^KS11', '코스닥': '^KQ11'}
    )

    for name, ticker in symbols.items():

        data = safe_history(ticker)

        if data is not None and len(data) >= 2:

            prev = data['Close'].iloc[-2]
            curr = data['Close'].iloc[-1]

            change = ((curr - prev) / prev) * 100

            report += f"• {name}: {curr:,.2f} ({change:+.2f}%)\n"

    report += "\n"

    # 상승하락 TOP
    if is_morning:
        report += get_top_movers_us()
    else:
        report += get_top_movers_kr()

    report += "\n"

    # 뉴스
    if is_morning:
        report += get_global_news()
    else:
        report += get_kr_market_news()

    report += "\n"

    # 포트폴리오
    report += get_portfolio_summary()

    return report


# =========================
# 텔레그램 전송
# =========================
def send_telegram(text):

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN 없음")
        return

    if not CHAT_ID:
        print("❌ CHAT_ID 없음")
        return

    max_len = 3500

    messages = [
        text[i:i + max_len]
        for i in range(0, len(text), max_len)
    ]

    for idx, msg in enumerate(messages):

        try:

            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    'chat_id': CHAT_ID,
                    'text': msg
                },
                timeout=20
            )

            print(f"[Telegram {idx+1}] 상태코드:", response.status_code)
            print(response.text)

        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")


# =========================
# 실행
# =========================
if __name__ == "__main__":

    print("===== 프로그램 시작 =====")

    print("TOKEN 존재 여부:", bool(TELEGRAM_TOKEN))
    print("CHAT_ID 존재 여부:", bool(CHAT_ID))

    now_kst = datetime.utcnow() + timedelta(hours=9)

    hour = now_kst.hour

    print(f"현재 시간: {hour}시")

    if (7 <= hour < 11) or (17 <= hour < 23):

        print("리포트 생성 시작")

        report = get_market_reports()

        print(report)

        print("텔레그램 전송 시작")

        send_telegram(report)

    else:

        print("현재는 발송 시간이 아닙니다.")
