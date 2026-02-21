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

## [추가] VS Code에서 서버 접속하기 (Remote - SSH)
매번 웹 브라우저로 접속하는 것보다 VS Code의 **Remote - SSH** 확장을 사용하면 훨씬 편리하게 개발할 수 있습니다.

### 1단계: 키 파일(.pem) 준비
1. Lightsail 콘솔의 **'계정(Account)' -> 'SSH 키(SSH Keys)'** 메뉴로 이동합니다.
2. 사용 중인 리전(주로 Seoul)의 기본 키를 **다운로드**하여 본인 컴퓨터의 안전한 곳(예: `C:\Users\이호준\.ssh\`)에 저장합니다.

### 2단계: VS Code 설정
1. VS Code에서 **'Remote - SSH'** 확장을 설치합니다.
2. 왼쪽 하단의 파란색 **'><' (Open a Remote Window)** 아이콘을 클릭합니다.
3. **'Connect to Host...'** -> **'Configure SSH Hosts...'** -> 첫 번째 경로(주로 `config`)를 선택합니다.
4. 아래 형식을 참고하여 입력하고 저장합니다:
   ```text
   Host samsung-monitor
       HostName [본인의 Lightsail 고정 IP]
       User ubuntu
       IdentityFile C:\Users\이호준\.ssh\LightsailDefaultKey-ap-northeast-2.pem
   ```

### 3단계: 접속
1. 다시 파란색 아이콘 클릭 -> **'Connect to Host...'** -> **'samsung-monitor'**를 선택합니다.
2. 새 창이 열리면서 서버에 연결됩니다. 이제 **'Open Folder'**를 눌러 `/home/ubuntu/scartch` 폴더를 열어 작업하세요!

---
**축하합니다!** 이제 AWS 서버가 당신을 대신해 24시간 실적을 감시하고 보고합니다.
