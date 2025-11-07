# Docker 자동 업로드 가이드

파일 수정 시 Docker 컨테이너에 자동으로 반영되도록 설정되었습니다.

## 사용 방법

### 1. 개발 모드로 시작 (권장)

```bash
./docker-dev.sh
```

또는 직접 실행:

```bash
FLASK_ENV=development docker compose up --build
```

### 2. 프로덕션 모드로 시작

```bash
FLASK_ENV=production docker compose up --build
```

## 자동 반영 기능

### 개발 모드 (FLASK_ENV=development)
- ✅ **소스 코드 자동 반영**: `app/`, `api/`, `templates/`, `static/` 디렉토리의 변경사항이 즉시 반영됩니다
- ✅ **Flask Auto-Reload**: 파일 변경 시 Flask가 자동으로 재시작됩니다
- ✅ **실시간 반영**: 파일 저장 후 몇 초 내에 변경사항이 반영됩니다

### 반영되는 파일
- `app/` - 모든 Python 모듈
- `api/` - Vercel 서버리스 함수
- `templates/` - Jinja2 템플릿
- `static/` - CSS, JavaScript, 이미지
- `migrations/` - Alembic 마이그레이션
- `requirements.txt` - 변경 시 컨테이너 재빌드

### 반영되지 않는 파일
- `uploads/` - 업로드된 파일 (데이터만 공유)
- `exports/` - PDF 내보내기 (데이터만 공유)
- Python 패키지 설치: `requirements.txt` 변경 시 `docker compose up --build` 필요

## 개발 워크플로우

1. **Docker 시작**:
   ```bash
   ./docker-dev.sh
   ```

2. **파일 수정**: 
   - `app/` 디렉토리의 Python 파일 수정
   - `templates/` 디렉토리의 HTML 템플릿 수정
   - `static/` 디렉토리의 CSS/JS 수정

3. **자동 반영 확인**:
   - 브라우저에서 http://localhost:5501 접속
   - 파일 저장 후 자동으로 Flask가 재시작됨
   - 로그에서 "Detected change in..." 메시지 확인

4. **로그 확인**:
   ```bash
   docker compose logs -f app
   ```

## Docker Compose Watch 모드 (v2.22+)

Docker Compose의 `develop.watch` 기능이 활성화되어 있습니다:
- 파일 변경 시 자동 동기화
- `requirements.txt` 변경 시 자동 재빌드

## 문제 해결

### 파일 변경이 반영되지 않는 경우

1. **Flask가 재시작되지 않는 경우**:
   ```bash
   docker compose restart app
   ```

2. **볼륨 마운트 확인**:
   ```bash
   docker compose exec app ls -la /app/app
   ```

3. **수동 재시작**:
   ```bash
   docker compose down
   docker compose up --build
   ```

### 권한 문제

파일 권한 문제가 발생하면:
```bash
chmod -R 755 app/ templates/ static/
```

## 참고사항

- **개발 모드**: Flask의 내장 개발 서버 사용 (auto-reload 활성화)
- **프로덕션 모드**: Gunicorn 사용 (성능 최적화, auto-reload 없음)
- **데이터베이스**: 변경사항은 마이그레이션으로 관리
- **환경변수**: `.env` 파일 또는 `docker-compose.yml`에서 설정


