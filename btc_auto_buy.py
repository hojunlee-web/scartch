import os
import time
import requests
import pyupbit
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# [1] 설정 및 환경 변수 로드
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_PRIVATE_CHAT_ID = os.getenv("MY_PRIVATE_CHAT_ID")
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

# Upbit API 객체 생성
upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)

# Gemini API 설정 (모델: gemini-2.5-flash)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def post_log(message):
    """실시간 로그 기록 (터미널 출력 + 파일 저장)"""
    now = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    log_msg = f"{now} [BTC-AUTO] {message}"
    print(log_msg, flush=True)
    log_path = os.path.join(os.path.dirname(__file__), "btc_auto.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def send_telegram(message):
    """박사님 개인 텔레그램으로 보안 전송 (POST 방식)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": MY_PRIVATE_CHAT_ID, "text": message}
        requests.post(url, data=payload, timeout=10).raise_for_status()
    except Exception as e:
        post_log(f"텔레그램 전송 실패: {e}")

def check_balance_defense(required_amount):
    """[방어 코드] 업비트 원화(KRW) 잔고 확인"""
    try:
        current_cash = upbit.get_balance("KRW")
        if current_cash is None: current_cash = 0
        
        if current_cash < required_amount:
            msg = f"⚠️ [방어] 예수금 부족 (잔고: {int(current_cash):,}원 / 필요: {required_amount:,}원)"
            post_log(msg)
            send_telegram(msg + "\n비트코인 매수 주문을 건너뜁니다.")
            return False
        return True
    except Exception as e:
        post_log(f"잔고 조회 중 에러: {e}")
        return False

def get_btc_info():
    """업비트 실시간 시세 및 나의 평단가 대비 변동률 계산"""
    try:
        current_price = pyupbit.get_current_price("KRW-BTC")
        avg_buy_price = upbit.get_avg_buy_price("KRW-BTC")
        
        # 코인을 보유하지 않아 평단가가 0인 경우 처리
        if avg_buy_price == 0:
            return current_price, 0, 0
            
        # 평단가 대비 수익률 계산
        change_pct = ((current_price - avg_buy_price) / avg_buy_price) * 100
        return current_price, avg_buy_price, round(change_pct, 2)
    except Exception as e:
        post_log(f"데이터 수집 실패: {e}")
        return None, None, None

def analyze_and_decide(change_pct, avg_price):
    """평단가 대비 하락 폭에 따른 매수 전략 결정"""
    # 박사님 설정: 평단가 대비 5% 하락 시 50만원 매수
    threshold = -5.0
    amount = 500000

    if avg_price == 0:
        return 0, "보유 중인 비트코인이 없어 평단가를 계산할 수 없습니다. 관망합니다."

    if change_pct <= threshold:
        return amount, f"📉 평단가 대비 {change_pct}% 하락: 50만원 추가 매수 조건 충족"
    
    return 0, f"현재 수익률 {change_pct}%: 매수 기준(-5%) 미달로 관망합니다."

def main():
    post_log("🚀 비트코인 평단가 기준 자동 매수 봇 가동 시작")

    while True:
        try:
            # 1. 시세 및 내 평단가 확인
            price, avg_price, change_pct = get_btc_info()
            
            if price is not None:
                # 2. 매수 여부 판단
                order_amount, strategy_text = analyze_and_decide(change_pct, avg_price)

                if order_amount > 0:
                    # 3. 예수금 방어 확인
                    if check_balance_defense(order_amount):
                        # 4. Gemini 시장 분석
                        prompt = (
                            f"비트코인 현재가 {price:,.0f}원, 나의 평단가 {avg_price:,.0f}원입니다. "
                            f"현재 평단가 대비 {change_pct}% 하락하여 {order_amount:,}원을 추가 매수합니다. "
                            f"비트코인 시장의 주요 테마와 현재 하락의 기술적 분석을 포함해 투자 조언을 3줄로 작성해줘."
                        )
                        ai_analysis = model.generate_content(prompt, request_options={'timeout': 60}).text
                        
                        # [실전 주문 실행]
                        upbit.buy_market_order("KRW-BTC", order_amount)
                        
                        # 5. 주문 결과 즉시 보고
                        final_report = (
                            f"🔔 [BTC 실시간 매수 알림]\n\n"
                            f"✅ 주문체결: {order_amount:,}원 매수 완료\n"
                            f"현재가: {price:,.0f}원\n"
                            f"내 평단가: {avg_price:,.0f}원\n\n"
                            f"🤖 Gemini 시장 분석:\n{ai_analysis}"
                        )
                        send_telegram(final_report)
                        post_log(f"✅ {order_amount:,}원 매수 주문 체결 및 알림 전송 완료")
                else:
                    post_log(f"💤 {strategy_text}")

            # 체크 주기: 평단가 기준은 1시간마다
            time.sleep(3600)

        except Exception as e:
            error_msg = f"❌ 메인 루프 에러: {e}"
            post_log(error_msg)
            send_telegram(error_msg)
            time.sleep(600)

if __name__ == "__main__":
    main()