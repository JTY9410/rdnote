# 데이터베이스 설정 가이드

## ✅ 설정 완료된 환경 변수

다음 환경 변수들이 설정되었습니다:
- ✅ `SECRET_KEY` - Flask 시크릿 키
- ✅ `UPLOAD_FOLDER` - `/tmp/uploads`
- ✅ `EXPORT_FOLDER` - `/tmp/exports`

## ⚠️ DATABASE_URL 설정 필요

Vercel은 데이터베이스를 제공하지 않으므로, 외부 PostgreSQL 데이터베이스가 필요합니다.

## 무료 PostgreSQL 호스팅 옵션

### 1. Supabase (추천)
- **URL**: https://supabase.com
- **무료 티어**: 500MB 데이터베이스, 2개 프로젝트
- **설정 방법**:
  1. 계정 생성 후 프로젝트 생성
  2. Settings → Database → Connection string 복사
  3. 형식: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`

### 2. Railway
- **URL**: https://railway.app
- **무료 티어**: $5 무료 크레딧/월
- **설정 방법**:
  1. New Project → PostgreSQL 추가
  2. PostgreSQL 서비스 → Variables 탭
  3. `DATABASE_URL` 복사

### 3. Neon
- **URL**: https://neon.tech
- **무료 티어**: 0.5GB 무료
- **설정 방법**:
  1. 프로젝트 생성
  2. Connection string 복사

### 4. Render
- **URL**: https://render.com
- **무료 티어**: 90일 무료 (신용카드 필요)
- **설정 방법**:
  1. New → PostgreSQL 생성
  2. Internal Database URL 복사

## DATABASE_URL 설정 방법

### 방법 1: CLI로 설정

```bash
vercel env add DATABASE_URL production
```

프롬프트가 나타나면 PostgreSQL 연결 문자열을 입력하세요:
```
postgresql://user:password@host:port/database
```

### 방법 2: Vercel 대시보드에서 설정

1. https://vercel.com/jeong-tai-youngs-projects/wecar-rnd 접속
2. Settings → Environment Variables
3. "Add New" 클릭
4. Name: `DATABASE_URL`
5. Value: PostgreSQL 연결 문자열
6. Environment: `Production` 선택
7. Save

## 데이터베이스 마이그레이션

DATABASE_URL 설정 후, 로컬에서 마이그레이션을 실행해야 합니다:

```bash
# 환경 변수 설정
export DATABASE_URL="your-postgresql-url-here"

# 마이그레이션 실행
alembic upgrade head

# 초기 데이터 설정 (관리자 계정 생성)
python init_db.py
```

초기 관리자 계정:
- `jty9410@wecar-m.co.kr` / `#jeong07209`
- `wecar@wecar-m.co.kr` / `#wecarm1004`

## 환경 변수 설정 후 재배포

모든 환경 변수 설정이 완료되면:

```bash
vercel --prod
```

배포가 완료되면 애플리케이션이 정상 작동합니다!

