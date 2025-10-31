# Docker 배포 가이드

## 사전 요구사항

1. **Docker Desktop 설치**
   - macOS: [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Docker Desktop을 설치하고 실행해야 합니다.

2. **Docker Compose**
   - Docker Desktop에 포함되어 있습니다.

## 빠른 시작

### 1. Docker Desktop 시작
macOS에서 Docker Desktop을 실행합니다.

### 2. Docker 빌드 및 실행

```bash
# 방법 1: 스크립트 사용 (권장)
./docker-start.sh

# 방법 2: 직접 실행
docker-compose up -d --build
```

### 3. 접속 확인
브라우저에서 접속:
- **메인**: http://localhost:5001
- **로그인**: http://localhost:5001/auth/login

## 구조

### 서비스
- **app**: Flask 애플리케이션 (포트 5001)
- **db**: PostgreSQL 데이터베이스 (포트 5432)

### 포트 매핑
- 컨테이너 내부 5000 → 호스트 5001
- 컨테이너 내부 5432 → 호스트 5432

## 유용한 명령어

### 컨테이너 관리
```bash
# 로그 확인
docker-compose logs -f

# 로그 확인 (특정 서비스)
docker-compose logs -f app
docker-compose logs -f db

# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 중지
docker-compose down

# 컨테이너 재시작
docker-compose restart

# 컨테이너 재빌드
docker-compose up -d --build
```

### 데이터베이스 접속
```bash
# PostgreSQL 접속
docker-compose exec db psql -U wecar_user -d wecar_db

# 마이그레이션 실행
docker-compose exec app alembic upgrade head

# 새 마이그레이션 생성
docker-compose exec app alembic revision --autogenerate -m "migration message"
```

### 애플리케이션 쉘 접속
```bash
# 컨테이너 내부 쉘
docker-compose exec app /bin/bash

# Python 쉘
docker-compose exec app python3
```

## 환경 변수

`docker-compose.yml`에서 설정 가능한 환경 변수:

- `DATABASE_URL`: 데이터베이스 연결 URL
- `SECRET_KEY`: Flask 시크릿 키
- `FLASK_ENV`: Flask 환경 (production/development)
- `UPLOAD_FOLDER`: 파일 업로드 폴더
- `EXPORT_FOLDER`: PDF 내보내기 폴더

## 볼륨

- `./uploads`: 업로드된 파일들
- `./exports`: 생성된 PDF 파일들
- `postgres_data`: PostgreSQL 데이터

## 트러블슈팅

### 포트 충돌
포트 5001이나 5432가 이미 사용 중인 경우:

```bash
# 포트 사용 확인
lsof -i:5001
lsof -i:5432

# docker-compose.yml에서 포트 변경
ports:
  - "5002:5000"  # 5001 → 5002로 변경
```

### 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose logs

# 컨테이너 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 데이터베이스 연결 오류
```bash
# 데이터베이스가 준비될 때까지 대기
docker-compose up -d db
sleep 10
docker-compose up -d app
```

### 초기 마이그레이션
```bash
# 마이그레이션 실행
docker-compose exec app alembic upgrade head
```

## 프로덕션 배포

프로덕션 환경에서는 다음 사항을 변경하세요:

1. **시크릿 키 변경**
```yaml
environment:
  SECRET_KEY: "strong-random-secret-key-here"
```

2. **환경 변수 파일 사용**
```bash
# .env 파일 생성
echo "SECRET_KEY=your-secret-key" > .env
echo "DATABASE_URL=postgresql://..." >> .env

# docker-compose.yml에서 env_file 사용
env_file:
  - .env
```

3. **리버스 프록시 설정**
   - Nginx 또는 Traefik 사용
   - SSL/TLS 인증서 설정

## 정리

```bash
# 컨테이너 및 볼륨 삭제
docker-compose down -v

# 이미지까지 삭제
docker-compose down -v --rmi all
```

