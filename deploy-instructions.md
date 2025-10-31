# WECar 연구개발일지 Docker 배포 가이드

## 📦 이미지 빌드 및 업로드 방법

### 1. 로컬 이미지 빌드
```bash
cd /Users/USER/dev/r&d
docker build -t wecar-rnd:latest -t wecar-rnd:v1.7 .
```

### 2. Docker Hub 업로드 (선택사항)

#### Docker Hub 계정이 있는 경우:
```bash
# Docker Hub 로그인
docker login

# 이미지 태그 지정
docker tag wecar-rnd:latest your-dockerhub-username/wecar-rnd:latest
docker tag wecar-rnd:v1.7 your-dockerhub-username/wecar-rnd:v1.7

# 업로드
docker push your-dockerhub-username/wecar-rnd:latest
docker push your-dockerhub-username/wecar-rnd:v1.7
```

#### 업로드 후 사용:
```bash
docker run -d \
  -p 5001:5000 \
  --name wecar-app \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/exports:/app/exports \
  your-dockerhub-username/wecar-rnd:latest
```

### 3. 로컬에서 실행

#### 현재 실행 중인 컨테이너:
```bash
cd /Users/USER/dev/r&d
docker-compose up -d
```

접속: http://localhost:5001

#### 컨테이너 상태 확인:
```bash
docker-compose ps
docker-compose logs -f app
```

### 4. 스탠드얼론 실행 (Dockerfile만 사용)

```bash
# 이미지 빌드
docker build -t wecar-rnd .

# DB 컨테이너 먼저 실행
docker run -d \
  --name wecar-db \
  -e POSTGRES_DB=wecar \
  -e POSTGRES_USER=wecar \
  -e POSTGRES_PASSWORD=wecar123 \
  -v wecar-db-data:/var/lib/postgresql/data \
  postgres:15

# App 컨테이너 실행
docker run -d \
  --name wecar-app \
  -p 5001:5000 \
  --link wecar-db:db \
  -e DATABASE_URL=postgresql://wecar:wecar123@db:5432/wecar \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/exports:/app/exports \
  wecar-rnd:latest
```

---

## 🚀 docker-compose 사용 (권장)

현재 실행 중인 방식입니다:

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "5001:5000"
    environment:
      - DATABASE_URL=postgresql://wecar:wecar123@db:5432/wecar
    volumes:
      - ./uploads:/app/uploads
      - ./exports:/app/exports
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=wecar
      - POSTGRES_USER=wecar
      - POSTGRES_PASSWORD=wecar123
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

실행:
```bash
docker-compose up -d
```

---

## 📝 현재 상태

### 빌드된 이미지
- `wecar-rnd:latest`
- `wecar-rnd:v1.7`

### 실행 중인 컨테이너
- `rd-app-1` (포트 5001)
- `rd-db-1` (PostgreSQL)

### 접속 정보
- **URL**: http://localhost:5001
- **관리자 계정**:
  - `jty9410@wecar-m.co.kr` / `#jeong07209`
  - `wecar@wecar-m.co.kr` / `#wecarm1004`

---

## 💾 데이터 백업

### PostgreSQL 백업
```bash
docker exec rd-db-1 pg_dump -U wecar wecar > backup.sql
```

### 파일 백업
```bash
tar -czf uploads-backup.tar.gz uploads/
tar -czf exports-backup.tar.gz exports/
```

### 복원
```bash
# DB 복원
docker exec -i rd-db-1 psql -U wecar wecar < backup.sql

# 파일 복원
tar -xzf uploads-backup.tar.gz
tar -xzf exports-backup.tar.gz
```

---

## 🔄 업데이트 방법

```bash
cd /Users/USER/dev/r&d

# 1. 코드 업데이트 후 빌드
docker-compose build

# 2. 컨테이너 재시작
docker-compose down
docker-compose up -d

# 3. 마이그레이션 (필요시)
docker-compose exec app alembic upgrade head
```

---

## 🌐 프로덕션 배포

### 요구사항
- Docker & Docker Compose
- 최소 2GB RAM
- 포트 5001 개방

### 배포 스크립트
```bash
#!/bin/bash
cd /Users/USER/dev/r&d
docker-compose pull
docker-compose up -d
docker-compose exec app alembic upgrade head
echo "✅ 배포 완료: http://localhost:5001"
```

