# AWS Lightsail (Ubuntu) 자동화 설정 가이드

본 가이드는 삼성 실적 모니터링 스크립트를 AWS 서버에서 24시간 작동하게 하는 방법을 다룹니다.

## 1. 초기 환경 설정 (최초 1회)
서버 터미널에 접속하여 아래 명령어를 차례로 입력하세요.

```bash
# 시스템 업데이트 및 필수 도구 설치
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git -y

# 프로젝트 복제 (본인의 GitHub 저장소 주소 사용)
git clone https://github.com/hojunlee-web/scartch.git
cd scartch

# 파이썬 라이브러리 설치
pip3 install -r requirements.txt
```

## 2. API 키 설정
`.env` 파일을 생성하고 본인의 API 키를 입력합니다.

```bash
nano .env
```
아래 내용을 붙여넣으세요 (키 값은 본인의 것을 입력):
```env
GOOGLE_API_KEY=your_google_api_key
DART_API_KEY=your_dart_api_key
TELEGRAM_TOKEN=your_telegram_token
MY_PRIVATE_CHAT_ID=your_chat_id
```
*(Ctrl+O, Enter, Ctrl+X로 저장하고 나옵니다.)*

## 3. 자동 실행 설정 (Cron)
스크립트가 1시간마다 자동으로 실행되도록 설정합니다.

```bash
crontab -e
```
가장 아랫줄에 다음 내용을 추가합니다:
```cron
0 * * * * cd /home/ubuntu/scartch && python3 samsung_results_monitor.py
```
*(매시 0분에 스크립트 실행)*

## 4. GitHub 인증 설정 (자동 푸시용)
스크립트가 GitHub에 코드를 올릴 수 있도록 인증(Credential)을 한 번 받아두어야 합니다.

```bash
git config --global user.email "your-email@example.com"
git config --global user.name "your-username"
# 첫 번째 푸시 때 GitHub 아이디/토큰(Personal Access Token)을 입력하면 저장됩니다.
git push origin master
```

---
**축하합니다!** 이제 AWS 서버가 당신을 대신해 24시간 실적을 감시하고 보고합니다.
