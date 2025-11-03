# Vercel 배포 가이드

## 필수 환경변수 설정

Vercel 대시보드에서 다음 환경변수를 설정해야 합니다:

### 필수 변수

1. **DATABASE_URL** (필수)
   ```
   postgresql://username:password@host:port/database?sslmode=require
   ```
   - PostgreSQL 데이터베이스 연결 URL
   - Vercel에서는 Supabase, Neon, 또는 다른 PostgreSQL 서비스를 사용 권장
   - SSL 모드 필수

2. **SECRET_KEY** (필수)
   ```
   your-very-secret-key-change-in-production
   ```
   - Flask 세션 암호화 키
   - 긴 랜덤 문자열 권장

### 선택 변수

3. **FLASK_ENV**
   ```
   production
   ```

4. **GITHUB_WEBHOOK_SECRET** (GitHub 연동 사용 시)
   ```
   your-github-webhook-secret
   ```

## Vercel 설정 방법

### 1. 프로젝트 연결

```bash
vercel
```

또는 Vercel 대시보드에서 GitHub 저장소를 연결

### 2. 환경변수 설정

Vercel 대시보드:
- Settings → Environment Variables
- 위의 환경변수들을 추가

또는 CLI로:

```bash
vercel env add DATABASE_URL
vercel env add SECRET_KEY
```

### 3. 배포

```bash
vercel --prod
```

## 데이터베이스 마이그레이션

Vercel에서는 자동으로 마이그레이션이 실행되지 않으므로, 별도로 실행해야 합니다:

### 방법 1: 로컬에서 마이그레이션 실행

```bash
export DATABASE_URL="your-postgresql-url"
alembic upgrade head
```

### 방법 2: Vercel CLI로 원격 실행

```bash
vercel env pull .env.local
export $(cat .env.local | xargs)
alembic upgrade head
```

## 제한사항

1. **파일 저장**: Vercel은 임시 파일 시스템만 제공 (`/tmp`)
   - 업로드된 파일은 함수 실행 후 삭제됨
   - **권장**: S3, Cloudflare R2, 또는 다른 객체 스토리지 사용

2. **실행 시간**: 기본 10초 (Pro 플랜에서 최대 60초)
   - 큰 파일 처리나 PDF 생성 시 타임아웃 가능
   - **해결**: 백그라운드 작업을 별도 서비스로 분리

3. **메모리**: 기본 1024MB
   - WeasyPrint 등 메모리 많이 사용하는 라이브러리 주의

## 문제 해결

### 오류: FUNCTION_INVOCATION_FAILED

1. **환경변수 확인**
   - DATABASE_URL이 설정되어 있는지 확인
   - Vercel 로그에서 구체적인 오류 메시지 확인

2. **데이터베이스 연결 확인**
   - PostgreSQL 서버가 실행 중인지
   - 방화벽에서 Vercel IP 허용되었는지
   - SSL 인증서가 유효한지

3. **의존성 확인**
   - `requirements.txt`에 모든 패키지가 포함되어 있는지
   - 빌드 로그에서 패키지 설치 오류 확인

### 데이터베이스 연결 오류

```python
# 연결 테스트
import psycopg2
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("SELECT 1")
print("Connection successful!")
```

## 프로덕션 최적화

1. **CDN 캐싱**: 정적 파일은 Vercel Edge Network 활용
2. **이미지 최적화**: Vercel Image Optimization 사용
3. **모니터링**: Vercel Analytics 활성화
4. **알람**: Vercel에서 오류 알림 설정

## 백업 및 복구

- 데이터베이스는 정기적으로 백업 필요
- Vercel 배포는 자동으로 이전 버전 유지 (프로젝트 설정에서 확인)

