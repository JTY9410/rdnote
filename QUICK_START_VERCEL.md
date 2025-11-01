# Vercel 빠른 시작 가이드

## 🚀 5분 만에 배포하기

### 1단계: Vercel CLI 설치 및 로그인

```bash
# CLI 설치
npm i -g vercel

# 로그인
vercel login
```

### 2단계: 환경 변수 설정

```bash
# 데이터베이스 URL 설정 (예: Supabase, Railway, Neon 등)
vercel env add DATABASE_URL production

# Flask 시크릿 키 (랜덤 문자열 생성)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 생성된 키를 복사한 후:
vercel env add SECRET_KEY production
# 프롬프트에서 생성된 키 입력

# 업로드/내보내기 경로 (Vercel 서버리스용)
vercel env add UPLOAD_FOLDER production
# 값 입력: /tmp/uploads

vercel env add EXPORT_FOLDER production
# 값 입력: /tmp/exports
```

### 3단계: 데이터베이스 준비

PostgreSQL 데이터베이스가 필요합니다. 무료 옵션:

- **Supabase**: https://supabase.com (500MB 무료)
- **Railway**: https://railway.app (무료 크레딧)
- **Neon**: https://neon.tech (무료 티어)

데이터베이스 생성 후 연결 문자열:
```
postgresql://user:password@host:port/database
```

### 4단계: 데이터베이스 마이그레이션 (로컬에서)

```bash
# 로컬에서 환경 변수 설정
export DATABASE_URL="your-postgresql-url-here"

# 마이그레이션 실행
alembic upgrade head

# 초기 데이터 설정 (선택사항)
python init_db.py
```

### 5단계: 배포!

```bash
# 현재 디렉토리에서
vercel --prod
```

배포가 완료되면 URL이 표시됩니다! 🎉

## ✅ 배포 확인

1. 배포된 URL 접속
2. `/auth/login` 페이지 확인
3. 관리자 계정으로 로그인 테스트

## 🔧 문제 해결

### DEPLOYMENT_NOT_FOUND 오류

```bash
# 프로젝트 연결 확인
vercel link

# 재배포
vercel --prod
```

### 데이터베이스 연결 오류

- `DATABASE_URL` 형식 확인: `postgresql://user:pass@host:port/dbname`
- 데이터베이스 서버가 공개 IP에서 접근 가능한지 확인
- 방화벽 설정 확인

### 파일 업로드 문제

⚠️ **중요**: Vercel 서버리스에서는 `/tmp` 파일이 함수 종료 후 삭제됩니다.

**임시 해결책**: 개발/테스트 용도로만 사용

**프로덕션 해결책**: S3, Cloudflare R2 같은 객체 스토리지 사용 필요

## 📝 다음 단계

프로덕션 사용을 위해서는:

1. **파일 스토리지**: AWS S3 또는 Cloudflare R2 통합
2. **도메인 연결**: Vercel 대시보드에서 커스텀 도메인 설정
3. **모니터링**: Vercel Analytics 활성화
4. **백업**: 정기적인 데이터베이스 백업 설정

## 📚 상세 가이드

더 자세한 내용은 `VERCEL_DEPLOYMENT.md` 참고

