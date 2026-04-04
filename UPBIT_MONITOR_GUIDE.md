# Upbit Crypto Monitor Bot 가이드

## 개요
이 문서는 매주 일요일 오전 08:00 (KST) 에 업비트 잔고를 스냅샷하여 Telegram으로 자동 브리핑해 주는 `upbit_crypto_monitor_bot.py` 의 동작 원리와 실행 방법을 정리한 가이드입니다. 

기존 운용 중인 DCA 봇(`eth_dca_v2.py`, `btc_auto_buy.py`)과 동일한 아키텍처를 기반으로 설계되었으며, 포트폴리오 비중에 대한 Gemini 요약 분석 내용이 함께 제공됩니다.

## 주요 기능 및 특징
1. **스케줄링**: `schedule` 라이브러리 대신 `datetime` 모듈을 사용한 가벼운 `while True` 루프로 설계되어, 메모리 점유율을 최소화합니다. 매주 일요일 오전 8시에 정확히 동작합니다.
2. **실시간 가격 환산**: 현금(KRW)을 제외한 암호화폐 자산에 대해 `pyupbit`을 사용하여 현재가 및 평단가 대비 수익률을 실시간으로 도출합니다.
3. **AI 브리핑 연동**: 포트폴리오 포지션을 Gemini 2.5 Flash 모델에 전달하여 3줄 분량의 주간 투자 분석과 조언을 자동 생성합니다.
4. **리포트 자동 동기화**: Streamlit 대시보드 표시를 위해 매 구동 시 생성된 로컬 로그(`upbit_monitor.log`)를 Github에 자동으로 푸시(push)합니다.

## 서버 환경 구축 및 배포
본 봇은 AWS Lightsail 서버 환경 배포에 최적화되어 있습니다. 다음 순서로 실행을 권장합니다.

### 1. 사전 요구사항 패키지 설치
최신 버전의 파이썬 라이브러리가 필요합니다. Lightsail 터미널에서 아래 명령어로 패키지를 설치합니다.
```bash
pip3 install pyupbit google-generativeai python-dotenv
```
*참고: `google-generativeai` 설치 시 출력되는 `FutureWarning`은 구글 패키지명 변경에 대한 단순 알림이므로 동작에는 영향을 미치지 않습니다.*

### 2. 백그라운드 봇 실행
서버의 저장소 경로(`~/scartch`)에서 봇을 백그라운드 데몬 형태로 실행합니다.
```bash
nohup python3 upbit_crypto_monitor_bot.py > upbit_monitor.out 2>&1 &
```

### 3. 정상 동작 및 모니터링 확인
다음 명령어를 통해 로그가 정상적으로 출력되고 봇이 상주하고 있는지 확인합니다.
```bash
tail -f upbit_monitor.out
```
*성공 시 `[UPBIT-MONITOR] 🚀 주간 Upbit 잔고 자동 스냅샷 봇 가동 시작` 메시지가 표시됩니다.*

## 수정 및 관리 가이드
* **시간 변경**: `upbit_crypto_monitor_bot.py` 에서 `now.weekday() == 6 and now.hour == 8` 조건문을 각 요일 식별자(월:0, 화:1 ...) 및 시간으로 변경
* **봇 강제 종료 (수정 전 필수)**:
  ```bash
  # 실행 중인 python 봇 프로세스 찾기
  ps aux | grep upbit_crypto_monitor_bot.py
  
  # 해당 프로그램 종료
  kill -9 [해당_PID]
  ```
