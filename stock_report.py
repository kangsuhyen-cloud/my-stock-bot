import yfinance as yf
import requests
import os
from datetime import datetime, timedelta

# 1. 보안 설정 (Secrets에 저장한 값을 가져옴)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def get_market_report():
    # 한국 시간 설정 (깃허브 서버 시간 UTC에 9시간을 더함)
    now_kst = datetime.utcnow() + timedelta(hours=9)
    hour = now_kst.hour
    
    report = ""

    # --- [오전 07~10시: 해외 증시 브리핑] ---
    if 7 <= hour < 11:
        report = f"🌎 [Morning] 글로벌 증시 브리핑 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 주요 지수 정리
        indices = {'나스닥': '^IXIC', 'S&P500': '^GSPC', '필라델피아반도체': '^SOX'}
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{'🔺' if chg > 0 else '🔻'} {name}: {chg:+.2f}%\n"
        
        # 관심 종목 상승/하락률
        report += "\n📊 주요 기술주 현황\n"
        stocks = {'엔비디아': 'NVDA', 'IonQ': 'IONQ', 'SOXL(3배)': 'SOXL'}
        for name, tk in stocks.items():
            s = yf.Ticker(tk).history(period='2d')
            s_chg = ((s['Close'].iloc[-1] - s['Close'].iloc[-2]) / s['Close'].iloc[-2]) * 100
            report += f"• {name}: {s_chg:+.2f}%\n"
            
        report += "\n📰 글로벌 헤드라인\n- 미 빅테크 실적 발표 및 인플레이션 지표 주시\n- 국제 유가 및 금리 변동성 확대\n🔗 상세: https://finance.yahoo.com\n"
        report += "\n💡 종합 의견 & 방향성\n기술주 중심의 수급 확인이 필요합니다. 장기적인 자산 목표 달성을 위해 변동성에 일희일비하지 않는 전략이 유효합니다."

    # --- [오후 17~20시: 국내 증시 마감] ---
    elif 17 <= hour < 21:
        report = f"🇰🇷 [Evening] 국내 증시 마감 리포트 ({now_kst.strftime('%m/%d %H:%M')})\n\n"
        
        # 전체 지수 정리
        indices = {'코스피': '^KS11', '코스닥': '^KQ11'}
        for name, tk in indices.items():
            d = yf.Ticker(tk).history(period='2d')
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            report += f"{'🚀' if chg > 0 else '📉'} {name}: {chg:+.2f}%\n"

        # 주도 테마 및 상승 종목
        report += "\n🔥 오늘자 주도 테마 & 급등주\n"
        report += "📍 자율주행/전장: 현대오토에버, 모트렉스 (거래량 동반)\n"
        report += "📍 반도체/소부장: 한미반도체, HPSP (기관 매수)\n"
        
        report += "\n🔗 주요 뉴스 링크\n- 국내 주요 기업 수출 지표 호조 발표\n🔗 상세: https://finance.naver.com\n"
        report += "\n🎯 종합 의견 & 방향성\n거래량이 실린 주도 섹터의 흐름이 견고합니다. 카페 운영 등 본업에 집중하시되, 주도 테마의 대장주 위주로 관찰하세요."
    
    # 그 외 시간 (테스트용 알림)
    else:
        report = f"🔔 [알림] 현재 시간 {now_kst.strftime('%H:%M')}입니다.\n정기 보고 시간(08시, 18시)이 아니므로 일반 알림을 보냅니다!"

    return report

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(url, json=params)

if __name__ == "__main__":
    content = get_market_report()
    send_telegram(content)
