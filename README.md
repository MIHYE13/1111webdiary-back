# 다음 장 백엔드

프론트엔드에서 전달할 오늘의 일기와 할 일 형식을 검증하는 FastAPI 백엔드입니다.

## 현재 구현 범위

- `GET /health`: 서버와 외부 연동 준비 상태 확인
- `POST /api/v1/diaries`: 일기와 오늘 할 일의 입력 형식 검증
- 일기 원문을 응답, 로그 또는 저장소에 남기지 않는 기본 동작
- 이메일 주소를 입력받거나 사용하는 필드 없음
- 요청 필드 및 길이 검증 테스트

`POST /api/v1/diaries`는 현재 입력 형식만 확인하고 `202 Accepted`를 반환합니다. 데이터는 저장하지 않으며 OpenAI 에이전트도 호출하지 않습니다.

## 아직 구현하지 않은 범위

- 프론트엔드와 API 연결 및 CORS 설정
- OpenAI 에이전트 호출
- Firebase Firestore 저장
- 이메일 발송
- Google Cloud 배포 설정

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

## 테스트

```powershell
python -m unittest discover -s tests -v
```
