# 데이터베이스 연결 해결 가이드

## 문제 해결 방법

데이터베이스 연결 오류가 발생한 경우, 다음 방법 중 하나를 선택하세요:

### 방법 1: SQLite 사용 (가장 간단, Docker 불필요)

애플리케이션이 자동으로 SQLite를 사용합니다. 별도 설정 불필요.

```bash
# 환경변수 없이 실행
python run.py
```

SQLite 데이터베이스는 `instance/wecar_db.sqlite`에 자동 생성됩니다.

### 방법 2: PostgreSQL 사용 (Docker 필요)

```bash
# Docker Compose로 PostgreSQL 시작
docker compose up -d db

# 환경변수 설정
export DATABASE_URL="postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db"

# 애플리케이션 실행
python run.py
```

### 방법 3: 환경변수 파일 사용

`.env` 파일 생성:

```bash
# PostgreSQL 사용 시
DATABASE_URL=postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db

# 또는 SQLite 사용 시 (설정 없음 = 자동으로 SQLite 사용)
```

## 데이터베이스 초기화

```bash
# SQLite 또는 PostgreSQL 상관없이 동일한 명령
python init_db.py
```

## 연결 상태 확인

애플리케이션이 실행 중이면 다음 URL로 건강 상태 확인:

```
http://localhost:5000/health
```

응답 예시:
```json
{
  "status": "ok",
  "application": "running",
  "database": "connected"
}
```

## 문제가 계속되면

1. 로그 확인: 애플리케이션 로그에서 구체적인 오류 메시지 확인
2. 데이터베이스 서비스 확인: PostgreSQL이 실행 중인지 확인
3. 방화벽 확인: 포트 5432가 열려있는지 확인 (PostgreSQL 사용 시)

