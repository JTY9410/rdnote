# ✅ 환경 변수 설정 요약

## 현재 상태

### ✅ 설정 완료 (3개)
- `SECRET_KEY` - Flask 시크릿 키 (암호화됨)
- `UPLOAD_FOLDER` - `/tmp/uploads`
- `EXPORT_FOLDER` - `/tmp/exports`

### ⚠️ 설정 필요 (1개)
- `DATABASE_URL` - PostgreSQL 데이터베이스 연결 문자열

## DATABASE_URL 설정 방법

### 옵션 1: CLI로 설정 (가장 빠름)

```bash
vercel env add DATABASE_URL production
```

프롬프트에서 PostgreSQL 연결 문자열 입력:
```
postgresql://user:password@host:port/database
```

### 옵션 2: 스크립트 사용

```bash
./setup-database-url.sh
```

### 옵션 3: Vercel 대시보드

1. https://vercel.com/jeong-tai-youngs-projects/wecar-rnd
2. Settings → Environment Variables
3. Add New → DATABASE_URL 입력

## 데이터베이스가 없다면?

### 무료 PostgreSQL 호스팅 추천

#### 1. Supabase (가장 쉬움) ⭐
- **URL**: https://supabase.com
- **무료**: 500MB 데이터베이스
- **설정**:
  1. Sign up (GitHub으로 로그인 가능)
  2. New Project 클릭
  3. 프로젝트 이름 입력, 비밀번호 설정
  4. Settings → Database → Connection string 복사
  5. 형식: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`

#### 2. Railway
- **URL**: https://railway.app
- **무료**: $5 크레딧/월
- **설정**:
  1. GitHub로 로그인
  2. New Project → PostgreSQL 추가
  3. PostgreSQL → Variables 탭 → DATABASE_URL 복사

#### 3. Neon
- **URL**: https://neon.tech
- **무료**: 0.5GB 스토리지
- **설정**:
  1. Sign up
  2. Create project
  3. Connection string 복사

## DATABASE_URL 설정 후 할 일

### 1. 환경 변수 확인

```bash
vercel env ls
```

모든 환경 변수가 설정되었는지 확인합니다.

### 2. 데이터베이스 마이그레이션 (로컬에서)

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

### 3. 재배포

```bash
vercel --prod
```

### 4. 배포 확인

배포 완료 후:
1. 배포된 URL 접속
2. `/auth/login` 페이지 확인
3. 관리자 계정으로 로그인 테스트

## 현재 배포 정보

- **배포 URL**: https://wecar-f3tyo5mpo-jeong-tai-youngs-projects.vercel.app
- **프로젝트**: jeong-tai-youngs-projects/wecar-rnd
- **상태**: 배포 완료 (DATABASE_URL 설정 필요)

## 문제 해결

### DATABASE_URL 형식 오류

올바른 형식:
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

특수 문자 이스케이프:
- 비밀번호에 특수문자가 있으면 URL 인코딩 필요
- `@` → `%40`
- `:` → `%3A`
- `/` → `%2F`

### 데이터베이스 연결 실패

- 데이터베이스 서버가 공개 IP에서 접근 가능한지 확인
- 방화벽 설정 확인
- 연결 문자열 정확성 확인

## 다음 단계

1. ✅ DATABASE_URL 설정
2. ✅ 마이그레이션 실행
3. ✅ 재배포
4. ✅ 테스트

---

**도움이 필요하시면:**
- `VERCEL_DEPLOYMENT.md` - 상세 배포 가이드
- `QUICK_START_VERCEL.md` - 빠른 시작
- `DATABASE_SETUP.md` - 데이터베이스 설정 가이드

