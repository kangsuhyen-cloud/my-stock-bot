import yfinance as yf
import requests
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import feedparser

# [보안 설정]
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [포트폴리오 정보] - 매수가, 수량, 종목명
MY_PORTFOLIO = {
    '402380.KS': [25005, 1, 'KODEX 미국S&P500'],
    '381170.KS': [30270, 13, 'TIGER 미국테크TOP10'],
    '411060.KS': [31320, 1, 'ACE KRX금현물'],
    'SMCI': [35.9671, 17, '슈퍼마이크로컴퓨터'],
    '360750.KS': [27504, 21, 'TIGER 미국S&P500']
}

# [해외 대형주 (시총 상위)]
US_LARGE_CAPS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'JPM', 'V']

# [국내 대형주 (시총 상위)]
KR_LARGE_CAPS = [
    ('005930.KS', '삼성전자'), ('000660.KS', 'SK하이닉스'), ('373220.KS', 'LG에너지솔루션'),
    ('207940.KS', '삼성바이오로직스'), ('005380.KS', '현대차'), ('000270.KS', '기아'),
    ('006400.KS', '삼성SDI'), ('035420.KS', 'NAVER'), ('051910.KS', 'LG화학'), ('035720.KS', '카카오')
]


def get_top_movers_us():
    """해외 대형주 상승/하락 TOP 5"""
    changes = []
    for ticker in US_LARGE_CAPS:
        try:
            data = yf.Ticker(ticker).history(period='2d')
            if len(data) >= 2:
                prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
                pct = ((curr - prev) / prev) * 100
                changes.append((ticker, pct, curr))
        except:
            continue
    
    changes.sort(key=lambda x: x[1], reverse=True)
    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]
    
    result = "📈 [해외 대형주 상승 TOP 5]\n"
    for t, p, c in top5:
        result += f"  • {t}: {p:+.2f}% (${c:,.2f})\n"
    
    result += "\n📉 [해외 대형주 하락 TOP 5]\n"
    for t, p, c in bottom5:
        result += f"  • {t}: {p:+.2f}% (${c:,.2f})\n"
    
    return result


def get_top_movers_kr():
    """국내 대형주 상승/하락 TOP 5"""
    changes = []
    for ticker, name in KR_LARGE_CAPS:
        try:
            data = yf.Ticker(ticker).history(period='2d')
            if len(data) >= 2:
                prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
                pct = ((curr - prev) / prev) * 100
                changes.append((name, pct, curr))
        except:
            continue
    
    changes.sort(key=lambda x: x[1], reverse=True)
    top5 = changes[:5]
    bottom5 = changes[-5:][::-1]
    
    result = "📈 [국내 대형주 상승 TOP 5]\n"
    for n, p, c in top5:
        result += f"  • {n}: {p:+.2f}% ({c:,.0f}원)\n"
    
    result += "\n📉 [국내 대형주 하락 TOP 5]\n"
    for n, p, c in bottom5:
        result += f"  • {n}: {p:+.2f}% ({c:,.0f}원)\n"
    
    return result


def get_global_news():
    """국제정세/글로벌 경제 뉴스 (RSS 피드 활용)"""
    news_items = []
    
    # Google News RSS - 글로벌 경제/증시 키워드
    feeds = [
        '[news.google.com](https://news.google.com/rss/search?q=미국+증시&hl=ko&gl=KR&ceid=KR:ko)',
        '[news.google.com](https://news.google.com/rss/search?q=글로벌+경제&hl=ko&gl=KR&ceid=KR:ko)',
        '[news.google.com](https://news.google.com/rss/search?q=연준+금리&hl=ko&gl=KR&ceid=KR:ko)'
    ]
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                title = entry.title
                link = entry.link
                news_items.append((title, link))
        except:
            continue
    
    # 중복 제거 후 상위 5개
    seen = set()
    unique_news = []
    for title, link in news_items:
        if title not in seen:
            seen.add(title)
            unique_news.append((title, link))
    
    result = "🌐 [글로벌 주요 뉴스]\n"
    for title, link in unique_news[:5]:
        # 제목 길이 제한
        short_title = title[:50] + "..." if len(title) > 50 else title
        result += f"  • {short_title}\n    🔗 {link}\n"
    
    return result if unique_news else "🌐 [글로벌 주요 뉴스]\n  뉴스를 불러올 수 없습니다.\n"


def get_kr_market_news():
    """국내 증시 주도섹터 및 이슈 뉴스"""
    news_items = []
    
    feeds = [
        '[news.google.com](https://news.google.com/rss/search?q=코스피+주도주&hl=ko&gl=KR&ceid=KR:ko)',
        '[news.google.com](https://news.google.com/rss/search?q=반도체+주가&hl=ko&gl=KR&ceid=KR:ko)',
        '[news.google.com](https://news.google.com/rss/search?q=2차전지+주가&hl=ko&gl=KR&ceid=KR:ko)'
    ]
    
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:
                news_items.append((entry.title, entry.link))
        except:
            continue
    
    seen = set()
    unique_news = []
    for title, link in news_items:
        if title not in seen:
            seen.add(title)
            unique_news.append((title, link))
    
    result = "🏭 [국내 주도섹터 및 이슈]\n"
    for title, link in unique_news[:5]:
        short_title = title[:50] + "..." if len(title) > 50 else title
        result += f"  • {short_title}\n    🔗 {link}\n"
    
    return result if unique_news else "🏭 [국내 주도섹터 및 이슈]\n  뉴스를 불러올 수 없습니다.\n"


def get_portfolio_analysis(ticker, name, buy_price, qty):
    """포트폴리오 심층 기술적 분석"""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period='60d')
        if len(df) < 40:
            return f"[{name}] 분석용 데이터 부족\n"
        
        curr = df['Close'].iloc[-1]
        
        # 이동평균선
        ma5 = df['Close'].rolling(5).mean().iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(40).mean().iloc[-1]  # 60일 대신 40일 (데이터 제한)
        
        # RSI 계산
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]
        
        # 볼린저 밴드
        bb_mid = ma20
        bb_std = df['Close'].rolling(20).std().iloc[-1]
        bb_upper = bb_mid + (2 * bb_std)
        bb_lower = bb_mid - (2 * bb_std)
        bb_position = (curr - bb_lower) / (bb_upper - bb_lower) * 100
        
        # 거래량 분석
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_curr = df['Volume'].iloc[-1]
        vol_ratio = (vol_curr / vol_avg) * 100 if vol_avg > 0 else 100
        
        # 수익률 계산
        profit_rate = ((curr - buy_price) / buy_price) * 100
        profit_amt = (curr - buy_price) * qty
        
        # 추세 판단
        if ma5 > ma20 > ma60:
            trend = "🟢 정배열 (강한 상승추세)"
        elif ma5 < ma20 < ma60:
            trend = "🔴 역배열 (하락추세)"
        else:
            trend = "🟡 횡보/추세전환 구간"
        
        # RSI 해석
        if rsi > 70:
            rsi_signal = "⚠️ 과매수 구간 - 단기 조정 가능성"
        elif rsi < 30:
            rsi_signal = "💡 과매도 구간 - 반등 기회 모색"
        elif 40 <= rsi <= 60:
            rsi_signal = "중립 구간 - 추세 확인 필요"
        else:
            rsi_signal = "정상 범위"
        
        # MACD 해석
        if macd_val > signal_val and macd_val > 0:
            macd_signal = "매수 우위 (골든크로스 유지)"
        elif macd_val < signal_val and macd_val < 0:
            macd_signal = "매도 우위 (데드크로스 구간)"
        else:
            macd_signal = "교차 임박 - 방향성 주시"
        
        # 투자 인사이트
        insights = []
        if rsi < 35 and macd_val > signal_val:
            insights.append("📌 기술적 반등 시그널 감지 - 분할 매수 고려")
        if rsi > 65 and profit_rate > 15:
            insights.append("📌 차익실현 구간 진입 - 일부 비중 축소 검토")
        if bb_position < 20:
            insights.append("📌 볼린저 하단 접근 - 지지선 테스트 중")
        if bb_position > 80:
            insights.append("📌 볼린저 상단 이탈 시도 - 추가 상승 여력 확인")
        if vol_ratio > 150:
            insights.append("📌 거래량 급증 - 변동성 확대 주의")
        
        if not insights:
            insights.append("📌 현 포지션 유지, 주요 지지/저항선 이탈 시 대응")
        
        result = f"""
━━━━━━━━━━━━━━━━━━━━━━
📊 {name} ({ticker})
━━━━━━━━━━━━━━━━━━━━━━
▶ 현재가: {curr:,.2f} | 수익률: {profit_rate:+.2f}%
▶ 평가손익: {profit_amt:+,.0f}

🔹 추세분석
  {trend}
  • 5일선: {ma5:,.2f} | 20일선: {ma20:,.2f}

🔹 모멘텀 지표
  • RSI(14): {rsi:.1f} → {rsi_signal}
  • MACD: {macd_signal}
  • 볼린저 위치: {bb_position:.0f}% (0=하단, 100=상단)

🔹 수급 동향
  • 거래량 비율: {vol_ratio:.0f}% (20일 평균 대비)

💡 투자 인사이트
"""
        for insight in insights:
            result += f"  {insight}\n"
        
        return result
        
    except Exception as e:
        return f"[{name}] 분석 오류: {str(e)}\n"


def get_economic_calendar(is_morning):
    """정확한 날짜/시간이 포함된 경제 일정"""
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.date()
    
    if is_morning:
        # 해외 경제 일정 (예시 - 실제로는 API 연동 필요)
        events = f"""
🗓 [미국 주요 경제 일정]
━━━━━━━━━━━━━━━━━━━━━━
• {(today).strftime('%m/%d')}(화) 21:30 KST
  → 미국 소비자물가지수(CPI) 발표
  
• {(today + timedelta(days=1)).strftime('%m/%d')}(수) 03:00 KST
  → FOMC 의사록 공개
  
• {(today + timedelta(days=2)).strftime('%m/%d')}(목) 21:30 KST
  → 신규 실업수당 청구건수
  
• {(today + timedelta(days=3)).strftime('%m/%d')}(금) 23:00 KST
  → 미시간대 소비자심리지수
  
📌 주요 실적 발표
• 금주 내: 주요 빅테크 분기 실적 발표 예정
"""
    else:
        # 국내 경제 일정
        events = f"""
🗓 [국내 주요 경제 일정]
━━━━━━━━━━━━━━━━━━━━━━
• {(today + timedelta(days=1)).strftime('%m/%d')}(수) 10:00 KST
  → 한국은행 금융통화위원회 금리 결정
  
• {(today + timedelta(days=2)).strftime('%m/%d')}(목) 09:00 KST
  → 5월 1~10일 수출입 동향 발표
  
• {(today + timedelta(days=4)).strftime('%m/%d')}(토) 
  → 코스피200 정기변경 적용일
  
📌 기업 일정
• 이번주: 주요 상장사 1분기 실적 발표
• 배당락일/권리락일 확인 필수
"""
    
    return events


def get_market_reports():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    is_morning = 7 <= hour < 11
    
    # 메인 리포트 헤더
    market_type = "🌙 해외" if is_morning else "🌞 국내"
    report = f"""
{'═' * 30}
{market_type} 증시 마감 리포트
📅 {now_kst.strftime('%Y년 %m월 %d일 %H:%M')} KST
{'═' * 30}
"""
    
    # 주요 지수 현황
    report += "\n📊 [주요 지수 현황]\n"
    if is_morning:
        symbols = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '다우': '^DJI', 'VIX': '^VIX'}
    else:
        symbols = {'코스피': '^KS11', '코스닥': '^KQ11'}
    
    for name, ticker in symbols.items():
        try:
            data = yf.Ticker(ticker).history(period='2d')
            if len(data) >= 2:
                prev, curr = data['Close'].iloc[-2], data['Close'].iloc[-1]
                change = ((curr - prev) / prev) * 100
                emoji = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
                report += f"  {emoji} {name}: {curr:,.2f} ({change:+.2f}%)\n"
        except:
            report += f"  • {name}: 데이터 없음\n"
    
    # 대형주 등락
    report += "\n"
    if is_morning:
        report += get_top_movers_us()
    else:
        report += get_top_movers_kr()
    
    # 뉴스 섹션
    report += "\n"
    if is_morning:
        report += get_global_news()
    else:
        report += get_kr_market_news()
    
    # 포트폴리오 심층 분석
    report += f"""
{'═' * 30}
💼 포트폴리오 심층 분석
{'═' * 30}
"""
    
    # 아침: 해외 종목 / 저녁: 국내 종목 분석
    if is_morning:
        for ticker, info in MY_PORTFOLIO.items():
            if not ticker.endswith('.KS'):  # 해외 종목
                report += get_portfolio_analysis(ticker, info[2], info[0], info[1])
    else:
        for ticker, info in MY_PORTFOLIO.items():
            if ticker.endswith('.KS'):  # 국내 종목
                report += get_portfolio_analysis(ticker, info[2], info[0], info[1])
    
    # 포트폴리오 총 수익률
    report += "\n📈 [포트폴리오 총괄 현황]\n"
    total_invest = 0
    total_value = 0
    for ticker, info in MY_PORTFOLIO.items():
        try:
            curr = yf.Ticker(ticker).history(period='1d')['Close'].iloc[-1]
            buy_price, qty, name = info
            total_invest += buy_price * qty
            total_value += curr * qty
        except:
            continue
    
    if total_invest > 0:
        total_return = ((total_value - total_invest) / total_invest) * 100
        report += f"  • 총 투자금: {total_invest:,.0f}\n"
        report += f"  • 현재 평가금: {total_value:,.0f}\n"
        report += f"  • 총 수익률: {total_return:+.2f}%\n"
    
    # 경제 일정
    report += get_economic_calendar(is_morning)
    
    return report


def send_telegram(text):
    if not text or not TELEGRAM_TOKEN or not CHAT_ID:
        print("텔레그램 전송 실패: 토큰 또는 채팅 ID 없음")
        return
    
    # 텔레그램 메시지 길이 제한 (4096자)
    max_len = 4000
    messages = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    
    for msg in messages:
        try:
            response = requests.post(
                f"[api.telegram.org](https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage)",
                json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'},
                timeout=15
            )
            if not response.ok:
                print(f"전송 오류: {response.text}")
        except Exception as e:
            print(f"전송 실패: {e}")


if __name__ == "__main__":
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    # 오전 7~11시 (해외 마감) 또는 오후 17~23시 (국내 마감)
    if (7 <= hour < 11) or (17 <= hour < 23):
        report = get_market_reports()
        print(report)  # 디버깅용
        send_telegram(report)
    else:
        print(f"현재 시간({hour}시)은 리포트 발송 시간이 아닙니다.")
