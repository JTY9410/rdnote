# Vercel 배포 빠른 시작

## 즉시 배포하기

### 1. 환경변수 설정 (Vercel 대시보드)

Vercel 프로젝트 → Settings → Environment Variables에 다음 추가:

**필수:**
- `DATABASE_URL`: PostgreSQL 연결 URL (예: Supabase, Neon 등)
  ```
  postgresql://user:pass@host:port/db?sslmode=require
  ```
- `SECRET_KEY`: 랜덤 문자열 (예: `openssl rand -hex 32`)

### 2. 배포

```bash
vercel --prod
```

## 문제 해결

### 오류: DATABASE_URL must be set

→ Vercel 환경변수에 `DATABASE_URL` 설정 확인

### 오류: FUNCTION_INVOCATION_FAILED

→ Vercel 로그에서 구체적인 오류 확인:
```bash
vercel logs
```

### 데이터베이스 연결 실패

1. PostgreSQL 서버가 실행 중인지 확인
2. SSL 모드가 활성화되었는지 확인 (`?sslmode=require`)
3. 방화벽에서 Vercel IP 허용

## 추천 PostgreSQL 서비스

- **Supabase**: https://supabase.com (무료 티어 제공)
- **Neon**: https://neon.tech (서버리스 PostgreSQL)
- **Railway**: https://railway.app

## 데이터베이스 마이그레이션

배포 전에 마이그레이션을 실행하세요:

```bash
# 로컬에서 실행
export DATABASE_URL="your-postgresql-url"
alembic upgrade head
python init_db.py
```

## 성능 최적화

1. **파일 저장소**: `/tmp`는 임시이므로 S3/R2 사용 권장
2. **타임아웃**: 큰 파일 처리는 백그라운드 작업으로 분리
3. **캐싱**: Vercel Edge Network 활용

더 자세한 내용은 `VERCEL_DEPLOY.md` 참조

