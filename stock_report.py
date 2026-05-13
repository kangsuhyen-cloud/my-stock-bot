import requests
import os

# 깃허브 세팅에서 가져오는 부분
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text}
    # 실제로 전송을 시도하고 결과를 출력합니다
    response = requests.post(url, json=payload)
    print(f"전송 결과: {response.status_code}")
    print(f"응답 내용: {response.text}")

if __name__ == "__main__":
    # 시간 조건 없이 '무조건' 메시지를 보냅니다
    test_message = "✅ 깃허브 액션 연결 성공! 이제 시간만 맞추면 됩니다."
    send_telegram(test_message)
