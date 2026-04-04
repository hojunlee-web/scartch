import os
import time
import requests
import pyupbit
import google.generativeai as genai
import subprocess
from datetime import datetime, timezone, timedelta
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
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    model = None

# KST 시간대 설정
KST = timezone(timedelta(hours=9))

def post_log(message):
    """실시간 로그 기록 (터미널 출력 + 파일 저장)"""
    now = datetime.now(KST).strftime('[%Y-%m-%d %H:%M:%S]')
    log_msg = f"{now} [UPBIT-MONITOR] {message}"
    print(log_msg, flush=True)
    log_path = os.path.join(os.path.dirname(__file__), "upbit_monitor.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def send_telegram(message):
    """박사님 개인 텔레그램으로 전송 (POST 방식)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": MY_PRIVATE_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload, timeout=10).raise_for_status()
    except Exception as e:
        post_log(f"텔레그램 전송 실패: {e}")

def push_to_github(filename):
    """GitHub로 로그를 푸시하여 Streamlit 앱에 반영"""
    post_log(f"GitHub로 {filename} 동기화 시도 중...")
    try:
        log_path = os.path.join(os.path.dirname(__file__), filename)
        subprocess.run(["git", "add", log_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            timestamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
            subprocess.run(["git", "commit", "-m", f"Auto-update crypto monitor log: {timestamp}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", "origin", "master"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            post_log(f"✅ {filename} GitHub 업로드 성공! Streamlit 대시보드가 갱신됩니다.")
        else:
            post_log("새로운 변경 사항이 없어 GitHub 업로드를 건너뜁니다.")
    except Exception as e:
        post_log(f"GitHub 자동 업로드 실패: {e}")

def get_upbit_snapshot():
    """업비트 잔고 스냅샷 및 총 자산 계산"""
    try:
        balances = upbit.get_balances()
        if not balances:
            return None, "잔고를 불러오지 못했습니다."

        total_krw_value = 0
        asset_details = []

        for b in balances:
            currency = b['currency']
            balance = float(b['balance'])
            locked = float(b['locked'])
            total_balance = balance + locked
            avg_buy_price = float(b['avg_buy_price'])

            if total_balance == 0:
                continue

            if currency == "KRW":
                total_krw_value += total_balance
                asset_details.append({
                    "currency": "KRW",
                    "balance": total_balance,
                    "krw_value": total_balance,
                    "avg_buy_price": 1,
                    "return_rate": 0
                })
            else:
                ticker = f"KRW-{currency}"
                current_price = pyupbit.get_current_price(ticker)
                
                # 원화 마켓에 없는 코인일 경우 None 반환
                if current_price is None:
                    continue

                krw_value = total_balance * current_price
                total_krw_value += krw_value
                
                if avg_buy_price > 0:
                    return_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100
                else:
                    return_rate = 0

                asset_details.append({
                    "currency": currency,
                    "balance": total_balance,
                    "krw_value": krw_value,
                    "current_price": current_price,
                    "avg_buy_price": avg_buy_price,
                    "return_rate": return_rate
                })

        # 가치 순으로 정렬 (KRW 자산 제외하고 코인 가치 높은 순)
        asset_details = sorted(asset_details, key=lambda x: x['krw_value'], reverse=True)

        return total_krw_value, asset_details
    except Exception as e:
        post_log(f"잔고 스냅샷 생성 실패: {e}")
        return None, str(e)

def generate_report():
    """스냅샷 리포트 생성 및 전송"""
    post_log("업비트 잔고 스냅샷 생성 중...")
    total_val, details = get_upbit_snapshot()
    
    if total_val is None:
        send_telegram(f"❌ 스냅샷 생성 실패\n오류: {details}")
        return

    # 리포트 메시지 포맷팅
    report_lines = [
        "📊 <b>[주간 단위 Upbit 자산 스냅샷]</b>",
        f"🗓 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M KST')}",
        f"💰 <b>총 추정 자산: {total_val:,.0f} 원</b>",
        "────────────────────"
    ]

    for item in details:
        if item['currency'] == 'KRW':
            report_lines.append(f"💵 <b>KRW (현금)</b>: {item['krw_value']:,.0f} 원")
        else:
            report_lines.append(
                f"🪙 <b>{item['currency']}</b>: {item['balance']:.4f} 개\n"
                f"   • 평가금액: {item['krw_value']:,.0f} 원\n"
                f"   • 현재가: {item['current_price']:,.0f} 원\n"
                f"   • 평단가: {item['avg_buy_price']:,.0f} 원\n"
                f"   • 수익률: {item['return_rate']:+.2f}%"
            )

    report_msg = "\n".join(report_lines)

    # Gemini 분석이 가능한 경우
    if model:
        try:
            prompt = (
                f"다음은 투자자의 현재 업비트 가상화폐 포트폴리오입니다.\n"
                f"총 자산 가치는 약 {total_val:,.0f}원입니다.\n"
                f"포트폴리오 구성: {details}\n\n"
                f"현재 가상화폐 시장 동향과 이 포트폴리오 비중을 고려하여, 한 주간의 투자 조언을 3줄로 간결하게 작성해줘."
            )
            ai_analysis = model.generate_content(prompt, request_options={'timeout': 60}).text
            report_msg += f"\n────────────────────\n🤖 <b>Gemini 주간 분석:</b>\n{ai_analysis}"
        except Exception as e:
            post_log(f"Gemini 분석 생성 실패: {e}")

    send_telegram(report_msg)
    post_log(f"✅ 주간 스냅샷 전송 완료 (총 자산: {total_val:,.0f}원)")
    
    # Github 푸시 (UI 갱신용)
    push_to_github("upbit_monitor.log")

def main():
    post_log("🚀 주간 Upbit 잔고 자동 스냅샷 봇 가동 시작 (매주 일요일 08:00 KST)")
    
    while True:
        try:
            now = datetime.now(KST)
            
            # 매주 일요일(weekday=6) 08시 00분
            if now.weekday() == 6 and now.hour == 8 and now.minute == 0:
                generate_report()
                
                # 중복 실행 방지를 위해 1분 대기 (61초)
                time.sleep(61)
            else:
                # 30초마다 시간 체크
                time.sleep(30)
                
        except Exception as e:
            error_msg = f"❌ 메인 루프 치명적 에러: {e}"
            post_log(error_msg)
            send_telegram(error_msg)
            time.sleep(600)

if __name__ == "__main__":
    # 처음 실행 시 바로 리포트 전송을 테스트하고 싶다면 아래 주석을 해제하세요.
    # generate_report() 
    main()
