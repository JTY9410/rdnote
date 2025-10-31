# Docker로 WECar 연구개발일지 실행하기

## 빠른 시작

### 1단계: Docker Desktop 실행
macOS에서 Docker Desktop을 실행합니다.

### 2단계: 애플리케이션 시작

```bash
# 스크립트 사용 (권장)
./docker-start.sh

# 또는 직접 실행
docker-compose up -d --build
```

### 3단계: 접속
브라우저에서 http://localhost:5001 접속

## 주요 명령어

```bash
# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down

# 재시작
docker-compose restart

# 재빌드
docker-compose up -d --build
```

## 접속 정보

- **애플리케이션**: http://localhost:5001
- **데이터베이스**: localhost:5432
  - 사용자: wecar_user
  - 비밀번호: wecar_pass
  - 데이터베이스: wecar_db

## 파일 위치

- 업로드 파일: `./uploads/`
- PDF 내보내기: `./exports/`

자세한 내용은 `DOCKER_DEPLOYMENT.md`를 참고하세요.

