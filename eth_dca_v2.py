import os
import time
import requests
import pyupbit
import google.generativeai as genai
import subprocess
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
    log_msg = f"{now} [ETH-DCA] {message}"
    print(log_msg, flush=True)
    log_path = os.path.join(os.path.dirname(__file__), "eth_dca.log")
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

def push_to_github(filename):
    """실제 매수/매도 이벤트 발생 시에만 GitHub로 로그를 푸시하여 Streamlit 앱에 반영"""
    post_log(f"GitHub로 {filename} 동기화 시도 중...")
    try:
        # 파일이 없을 수 있으므로 경로 확인 후 추가
        log_path = os.path.join(os.path.dirname(__file__), filename)
        subprocess.run(["git", "add", log_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", f"Auto-update crypto logs: {timestamp}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", "origin", "master"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            post_log(f"✅ {filename} GitHub 업로드 성공! Streamlit 대시보드 스냅샷이 갱신됩니다.")
        else:
            post_log("새로운 변경 사항이 없어 GitHub 업로드를 건너뜁니다.")
    except Exception as e:
        post_log(f"GitHub 자동 업로드 실패: {e}")

def check_balance_defense(required_amount):
    """[방어 코드] 업비트 원화(KRW) 잔고 확인"""
    try:
        current_cash = upbit.get_balance("KRW")
        if current_cash is None: current_cash = 0
        
        if current_cash < required_amount:
            msg = f"⚠️ [방어] 예수금 부족 (잔고: {int(current_cash):,}원 / 필요: {required_amount:,}원)"
            post_log(msg)
            send_telegram(msg + "\n매수 주문을 건너뜁니다.")
            return False
        return True
    except Exception as e:
        post_log(f"잔고 조회 중 에러: {e}")
        return False

def get_eth_market_info():
    """업비트 실시간 시세 및 전일 종가 대비 변동률 계산"""
    try:
        current_price = pyupbit.get_current_price("KRW-ETH")
        df = pyupbit.get_ohlcv("KRW-ETH", interval="day", count=2)
        yesterday_close = df.iloc[0]['close']
        change_pct = ((current_price - yesterday_close) / yesterday_close) * 100
        return current_price, round(change_pct, 2)
    except Exception as e:
        post_log(f"시세 데이터 수집 실패: {e}")
        return None, None

def analyze_and_decide(change_pct):
    """하락 폭에 따른 매수 전략 결정 (박사님 맞춤 조건)"""
    strategies = [
        (-10.0, 500000, "🚨 폭락 감지: 50만원 공격적 매수 조건 충족"),
        (-3.0, 110000, "📉 조정 감지: 11만원 정기 매수 조건 충족"),
    ]
    for threshold, amount, message in strategies:
        if change_pct <= threshold:
            return amount, message
    return 0, f"시세 안정 (변동률: {change_pct}%): 관망 모드"

def main():
    post_log("🚀 이더리움 실전 DCA 봇 가동 시작 (Upbit + Gemini)")

    while True:
        try:
            # 1. 시세 확인
            price, change_pct = get_eth_market_info()
            
            if price:
                # 2. 전략 및 금액 판단
                order_amount, strategy_text = analyze_and_decide(change_pct)

                if order_amount > 0:
                    # 3. 예수금 방어 확인
                    if check_balance_defense(order_amount):
                        # 4. 종합 변수를 고려한 Gemini 분석
                        prompt = (
                            f"이더리움 현재가 {price:,.0f}원, 전일대비 {change_pct}% 하락 상황입니다. "
                            f"이번 회차에 {order_amount:,}원을 매수하기로 결정했습니다. "
                            f"최신 뉴스, 시장 테마 등을 고려하여 투자 조언을 3줄로 작성해줘."
                        )
                        ai_analysis = model.generate_content(prompt, request_options={'timeout': 60}).text
                        
                        # [실전 주문 실행]
                        upbit.buy_market_order("KRW-ETH", order_amount)
                        
                        # 5. 주문 결과 즉시 보고
                        final_report = (
                            f"🔔 [ETH 실시간 매수 알림]\n\n"
                            f"✅ 주문체결: {order_amount:,}원 매수 완료\n"
                            f"현재가: {price:,.0f}원\n"
                            f"변동률: {change_pct}%\n\n"
                            f"🤖 Gemini 시장 분석:\n{ai_analysis}"
                        )
                        send_telegram(final_report)
                        post_log(f"✅ {order_amount:,}원 매수 주문 체결 및 알림 전송 완료")
                        
                        # 앱 화면상에 보이기 위해 GitHub로 데이터 푸시 (매수 시 1회만)
                        push_to_github("eth_dca.log")
                else:
                    post_log(f"💤 {strategy_text}")

            # 체크 주기: 24시간 (또는 변동성 체크를 위해 1시간 추천)
            time.sleep(86400)

        except Exception as e:
            error_msg = f"❌ 메인 루프 치명적 에러: {e}"
            post_log(error_msg)
            send_telegram(error_msg)
            time.sleep(600)

if __name__ == "__main__":
    main()