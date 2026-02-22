# 🚀 통합 대시보드(Master Dashboard) 배포 가이드

이 문서는 개발 완료된 `samsung_dashboard`를 전 세계 어디서든 누구나 접속할 수 있도록 **GitHub**와 **Streamlit Cloud**를 이용해 무료로 배포(Hosting)하는 방법을 단계별로 설명합니다.

---

## 📌 사전 준비 단계

배포를 진행하기 전에 보안을 위해 **환경 변수 파일(`.env`)은 업로드 대상에서 제외**되어야 합니다.
`samsung_dashboard` 폴더 안에 있는 `.gitignore` 파일에 `.env`가 포함되어 있는지 확인하세요. (일반적으로 이미 설정되어 있습니다.)

## 🚀 1단계: GitHub에 코드 업로드하기

GitHub는 개발된 코드를 저장하는 온라인 저장소입니다.

1. **GitHub 로그인**: [GitHub.com](https://github.com/)에 접속하여 로그인합니다. (계정이 없다면 생성합니다.)
2. **새 저장소(Repository) 생성**:
    * 화면 우측 상단의 `+` 아이콘을 클릭하고 **[New repository]**를 선택합니다.
    * **Repository name**: `master-dashboard` (또는 원하는 이름)으로 입력합니다.
    * **Public**(공개) 또는 **Private**(비공개) 중 하나를 선택합니다. (URL을 아는 사람만 보려면 Public 권장)
    * 화면 맨 아래의 초록색 **[Create repository]** 버튼을 클릭합니다.
3. **코드 업로드**:
    * 새로 열린 화면 중간에 파란색 글씨인 **[uploading an existing file]** 링크를 클릭합니다.
    * 내 컴퓨터 탐색기를 열고 `C:\Users\이호준\.gemini\antigravity\scratch\samsung_dashboard` 폴더 안으로 들어갑니다.
    * `.env` 파일을 제외한 **모든 파일과 폴더**(`.gitignore`, `app.py`, JSON 파일들 등)를 드래그하여 브라우저에 놓습니다.
    * 업로드가 완료되면 하단의 초록색 **[Commit changes]** 버튼을 누릅니다.

> **선택 (VS Code 터미널 사용)**: Git이 설치되어 있다면 다음 명령어로 한 번에 업로드할 수 있습니다.
> ```bash
> git init
> git add .
> git commit -m "첫 번째 배포 버전 업로드"
> git branch -M main
> git remote add origin https://github.com/본인아이디/master-dashboard.git
> git push -u origin main
> ```

---

## 🚀 2단계: Streamlit Cloud 연동하기

Streamlit Cloud는 GitHub에 올려둔 파이썬 코드를 웹사이트 구조로 변환해 주는 무료 서버입니다.

1. **Streamlit 로그인**: [Streamlit Community Cloud](https://share.streamlit.io/)에 접속합니다.
2. **GitHub 연동**: 처음에 **Continue with GitHub**를 선택하여 조금 전 로그인한 깃허브 계정과 연동합니다. 권한 승인 창이 뜨면 허용해 줍니다.
3. **새 앱 만들기**: 우측 상단의 파란색 **[New app]** 버튼을 클릭합니다.

---

## 🚀 3단계: 배포 및 URL 생성

이제 깃허브에 올린 파일과 스트림릿 서버를 연결합니다.

1. **저장소 선택 (Repository)**: `Repository` 입력칸에서 방금 만든 `master-dashboard`를 찾아 선택합니다. (안 보이면 검색)
2. **브랜치 선택 (Branch)**: 보통 `main` 또는 `master`로 자동 설정됩니다. (그대로 둡니다.)
3. **메인 파일 지정 (Main file path)**: 빈칸에 `app.py` 라고 입력합니다.
4. **고급 설정 (Advanced settings - 매우 중요!)**:
    * 우리가 코드에 사용한 비밀번호나 API 키설정(`.env` 파일 내용)을 서버에 알려주어야 합니다.
    * `Advanced settings...` 파란색 글씨를 클릭합니다.
    * **Secrets** 박스에 `.env` 파일의 내용을 그대로 복사해서 붙여넣습니다.
      *(예: GOOGLE_API_KEY=AIzaSy...)*
    * 저장을 클릭합니다.
5. **배포 시작 (Deploy!)**: 화면 하단의 빨간색 **[Deploy!]** 버튼을 클릭합니다.

### 🎉 배포 완료!
약 1~3분 정도 애니메이션이 지나고 나면 짠! 하고 웹사이트가 열립니다.
브라우저 상단 주소창에 적힌 URL(예: `https://master-dashboard-xxxx.streamlit.app`)을 복사해서 스마트폰이나 다른 동료들에게 공유하시면 됩니다.

---

### 💡 (참고) 이후 코드/데이터 업데이트 방법
웹사이트 URL은 영구적으로 변하지 않습니다.

*   가정이나 사무실에서 차트 데이터를 변경했거나(`samsung_historical_data.json`), 뉴스가 새로 생성되면, `samsung_dashboard` 폴더의 파일을 GitHub 저장소 웹화면에 들어가서 `Add file` -> `Upload files`로 덮어쓰기만 해주면 됩니다.
*   **몇 분 뒤에 웹사이트가 자동으로 코드를 감지하고 최신 상태로 새로고침됩니다.**
