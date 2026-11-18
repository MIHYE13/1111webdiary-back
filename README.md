# 다음 장 백엔드

프론트엔드에서 전달한 오늘의 일기와 할 일을 Firestore에 저장하고, 내일 계획 대화를 제공하는 FastAPI 백엔드입니다.

## 현재 구현 범위

- `GET /health`: 서버와 외부 연동 준비 상태 확인
- `POST /api/v1/diaries`: 일기와 오늘 할 일을 `diary_entries` 컬렉션에 저장
- `POST /api/v1/conversations/{diary_id}/messages`: 저장된 일기를 바탕으로 천사·악마 관점의 내일 계획 대화 생성
- 일반 OpenAI Responses API의 구조화된 응답 사용(Agents 및 Skill 미사용)
- 대화와 확정된 내일 계획을 해당 일기 문서 아래에 저장
- 일기 원문을 API 응답이나 애플리케이션 로그에 노출하지 않는 기본 동작
- 이메일 주소를 입력받거나 사용하는 필드 없음
- 지정한 프론트엔드 Origin만 `/api/` 요청 허용
- 요청 필드 및 길이 검증 테스트

`POST /api/v1/diaries`는 입력 형식을 검증한 뒤 Firestore에 저장하고 `202 Accepted`를 반환합니다. 응답에는 일기 원문을 포함하지 않습니다.

AI 요청에는 `store=false`를 지정합니다. 일기와 대화 원문은 애플리케이션 로그나 API 응답 오류에 포함하지 않습니다.

## 아직 구현하지 않은 범위

- 프론트엔드 대화창과 대화 API 연결
- 이메일 발송

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
FIRESTORE_DATABASE_ID=(default)
CORS_ORIGINS=https://1111webdiary.netlify.app
```

- `APP_ENV`는 `development`, `test`, `production` 중 하나만 사용합니다.
- `CORS_ORIGINS`는 쉼표로 여러 주소를 구분할 수 있지만, 와일드카드(`*`)는 허용하지 않습니다.
- 운영 환경에서는 Google SDK가 Cloud Run의 프로젝트(`webdiary-75b29`)와 서비스 계정을 자동으로 인식합니다. 별도 프로젝트 ID나 로컬 서비스 계정 JSON 파일을 컨테이너에 넣지 않습니다.
- Cloud Run 서비스 계정에는 대상 Firestore 데이터베이스에 문서를 생성할 수 있는 IAM 권한이 필요합니다.
- `/api/`는 등록된 `Origin` 헤더가 없는 요청도 거부합니다. `/health`는 Cloud Run 상태 확인을 위해 예외로 둡니다.
- Origin 제한은 브라우저 출처 제한이며 사용자 인증을 대신하지 않습니다.

### Firestore 문서 구조

`diary_entries/{documentId}`에 다음 필드를 저장합니다.

- `diary`: 사용자가 작성한 일기 원문
- `today_tasks`: 오늘 할 일 목록
- `created_at`: Firestore 서버 시간
- `schema_version`: 현재 `1`
- `updated_at`: 마지막 대화 저장 시각
- `tomorrow_plan`: 확정된 최신 내일 계획

각 대화 턴은 `diary_entries/{documentId}/conversation/{turnId}`에 저장합니다.

- `user_message`: 사용자의 대화 메시지
- `reply`: 천사, 악마, 진행자 발화와 구조화된 계획
- `created_at`: 대화 저장 시각

일기 원문은 민감정보이므로 애플리케이션 로그와 API 응답에는 포함하지 않습니다.

### Firestore 보안 규칙

`firestore.rules`는 브라우저 및 모바일 Firebase SDK의 모든 읽기와 쓰기를 기본 거부합니다. 이 앱은 Firestore를 직접 호출하지 않고 Cloud Run 백엔드를 통해서만 저장합니다. Cloud Run 서버 SDK 요청은 Firestore Security Rules가 아니라 서비스 계정 IAM 권한으로 검사됩니다.

규칙을 배포하기 전에 대상 프로젝트와 로그인 계정을 확인한 후 다음 명령을 사용합니다.

```powershell
npx -y firebase-tools@latest deploy --only firestore:rules --project webdiary-75b29
```

## 테스트

```powershell
python -m unittest discover -s tests -v
```
