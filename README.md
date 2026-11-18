# 다음 장 백엔드

프론트엔드에서 전달할 오늘의 일기와 할 일 형식을 검증하는 FastAPI 백엔드입니다.

## 현재 구현 범위

- `GET /health`: 서버와 외부 연동 준비 상태 확인
- `POST /api/v1/diaries`: 일기와 오늘 할 일의 입력 형식 검증
- 일기 원문을 응답, 로그 또는 저장소에 남기지 않는 기본 동작
- 이메일 주소를 입력받거나 사용하는 필드 없음
- 지정한 프론트엔드 Origin만 `/api/` 요청 허용
- 요청 필드 및 길이 검증 테스트

`POST /api/v1/diaries`는 현재 입력 형식만 확인하고 `202 Accepted`를 반환합니다. 데이터는 저장하지 않으며 OpenAI 에이전트도 호출하지 않습니다.

## 아직 구현하지 않은 범위

- 프론트엔드와 API 연결
- OpenAI 에이전트 호출
- Firebase Firestore 저장
- 이메일 발송
- Google Cloud의 외부 서비스 연결 설정

## 설치

```powershell
python -m pip install -r requirements.txt
```

## 로컬 실행

이 디렉터리에서 다음 명령을 실행합니다.

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

서버 상태는 `http://127.0.0.1:8000/health`, API 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다.

## Cloud Run 배포 준비

루트의 `Dockerfile`은 Cloud Run이 제공하는 `PORT` 환경 변수를 사용하고, 모든 네트워크 인터페이스에서 FastAPI 서버를 실행합니다. 로컬에서 컨테이너를 확인하려면 다음 명령을 사용합니다.

```powershell
docker build -t webdiary-api .
docker run --rm -p 8080:8080 --env-file .env webdiary-api
```

실제 `.env` 파일은 Docker 빌드 컨텍스트와 Git에서 제외됩니다. 운영 비밀값은 이미지에 넣지 말고 Cloud Run 환경 변수 또는 Secret Manager로 설정합니다.

### Cloud Run 환경 변수

```dotenv
APP_ENV=production
OPENAI_API_KEY=Secret Manager에서 연결
OPENAI_MODEL=gpt-5.4
OPENAI_SKILL_ID=사용할 Skill ID
FIREBASE_PROJECT_ID=smwu0261111
CORS_ORIGINS=https://smwu261111.netlify.app
```

- `APP_ENV`는 `development`, `test`, `production` 중 하나만 사용합니다.
- `CORS_ORIGINS`는 쉼표로 여러 주소를 구분할 수 있지만, 와일드카드(`*`)는 허용하지 않습니다.
- 운영 환경에서는 Cloud Run 서비스 계정의 런타임 권한으로 Google Cloud와 Firestore에 접근합니다. 로컬 서비스 계정 JSON 파일을 컨테이너에 넣지 않습니다.
- `/api/`는 등록된 `Origin` 헤더가 없는 요청도 거부합니다. `/health`는 Cloud Run 상태 확인을 위해 예외로 둡니다.
- Origin 제한은 브라우저 출처 제한이며 사용자 인증을 대신하지 않습니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
```
