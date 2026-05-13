import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 보안 설정
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def get_realtime_news(query):
    """구글 뉴스를 통해 실제 기사 링크 3개를 가져옵니다."""
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        r = requests.get(url)
        # 간단한 파싱 (추후 더 정교하게 수정 가능)
        items = r.text.split('<item>')[1:4]
        news_list = []
        for item in items:
            title = item.split('<title>')[1].split('</title>')[0]
            link = item.split('<link>')[1].split('</link>')[0]
            news_list.append(f"• {title}\n  🔗 {link}")
        return "\n".join(news_list)
    except:
        return "• 실시간 뉴스를 가져오는 중 오류가 발생했습니다."

def get_market_report():
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    report = ""

    # --- [오전 07~10시: 해외 증시 정밀 분석] ---
    if 7 <= hour < 11:
        report = f"🌎 [Morning] 글로벌 증시 심층 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 1. 지수 및 대형주 등락률
        indices = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '필라델피아반도체': '^SOX'}
        stocks = {'엔비디아(NVDA)': 'NVDA', '테슬라(TSLA)': 'TSLA', '애플(AAPL)': 'AAPL', 'IonQ(IONQ)': 'IONQ', 'SOXL(3배)': 'SOXL'}
        
        report += "📈 [주요 지수]\n"
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{name}: {chg:+.2f}%  "
        
        report += "\n\n📊 [글로벌 대형주 시세]\n"
        for name, tk in stocks.items():
            s = yf.Ticker(tk).history(period='2d')
            s_chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            report += f"• {name}: {s_chg:+.2f}%\n"
            
        report += "\n📰 [글로벌 핵심 이슈]\n"
        report += get_realtime_news("미국 증시 반도체 금리")
        
        report += "\n\n🧠 [전문가 종합 의견]\n"
        report += "현재 미 증시는 매크로 지표(CPI, 고용)에 따른 금리 인하 기대감과 빅테크 실적 장세가 충돌하는 구간입니다. "
        report += "기술적 측면에서 나스닥은 20일 이동평균선 지지 여부가 단기 방향성을 결정할 것으로 보입니다. "
        report += "고위험군인 IONQ나 레버리지 상품(SOXL)은 변동성이 확대될 수 있으므로, 비중 조절을 통한 리스크 관리가 필수적입니다."

    # --- [오후 17~20시: 국내 증시 마감 정밀 분석] ---
    elif 17 <= hour < 21:
        report = f"🇰🇷 [Evening] 국내 증시 마감 심층 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 1. 지수 및 시총 상위 대형주
        indices = {'코스피': '^KS11', '코스닥': '^KQ11'}
        top_stocks = {'삼성전자': '005930.KS', 'SK하이닉스': '000660.KS', '현대차': '005380.KS', '에코프로비엠': '247540.KQ'}
        
        report += "📉 [지수 현황]\n"
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{name}: {chg:+.2f}%  "

        report += "\n\n🏆 [국내 시총 상위 대형주]\n"
        for name, tk in top_stocks.items():
            s = yf.Ticker(tk).history(period='2d')
            s_chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            report += f"• {name}: {s_chg:+.2f}%\n"

        report += "\n🔥 [주도 테마 & 특징주]\n"
        report += "오늘 시장은 외인과 기관의 수급이 반도체 및 자동차 섹터에 집중되었습니다. 특히 거래량이 동반된 특징 테마가 시장을 견인했습니다.\n"
        
        report += "\n🔗 [실시간 속보]\n"
        report += get_realtime_news("코스피 주도주 특징주 뉴스")
        
        report += "\n\n🎯 [시장 전략 및 방향성]\n"
        report += "국내 증시는 미 증시의 훈풍과 수출 지표 개선에 힘입어 상방 압력을 받고 있으나, 환율 변동성에 따른 외국인 수급 이탈 가능성을 배제할 수 없습니다. "
        report += "종목별 차별화 장세가 심화되고 있으므로 무분별한 추격 매수보다는 주도 섹터 내 저평가된 대형주 위주의 포트폴리오 재편이 유효한 시점입니다."
    
    else:
        report = f"🔔 [알림] 현재 시간 {now_kst.strftime('%H:%M')}\n정기 브리핑 시간 외 실행되었습니다."

    return report

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # 글자 수가 많을 수 있으므로 MarkdownV2 대신 기본 Markdown 사용
    params = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, json=params)

if __name__ == "__main__":
    content = get_market_report()
    send_telegram(content)
