# Vercel 환경변수 설정 완벽 가이드

## 방법 1: Vercel 웹 대시보드에서 설정 (권장)

### 단계별 안내

#### 1단계: Vercel 대시보드 접속
1. 브라우저에서 https://vercel.com 접속
2. 로그인 (GitHub 계정으로 로그인)
3. 대시보드에서 **rdnote** 프로젝트 클릭

#### 2단계: 환경변수 설정 페이지 이동
1. 프로젝트 페이지 상단 메뉴에서 **Settings** 클릭
2. 좌측 사이드바에서 **Environment Variables** 클릭

#### 3단계: 환경변수 추가

##### 필수 변수 1: DATABASE_URL
```
Key: DATABASE_URL
Value: postgresql://username:password@host:port/database?sslmode=require
```

**값 구성 예시:**
```
# Supabase 예시
postgresql://postgres.xxxxxxxxxxxx:your-password@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require

# Neon 예시
postgresql://user:password@ep-xxxx-xxxx.ap-southeast-2.aws.neon.tech/dbname?sslmode=require

# 일반 PostgreSQL 예시
postgresql://dbuser:dbpass@dbhost.example.com:5432/wecar_db?sslmode=require
```

**환경 선택:**
- ☑ Production
- ☑ Preview  
- ☑ Development

**추가 버튼 클릭**

##### 필수 변수 2: SECRET_KEY
```
Key: SECRET_KEY
Value: [랜덤 문자열 생성]
```

**랜덤 키 생성 방법:**

**macOS/Linux:**
```bash
openssl rand -hex 32
```

**또는 Python:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**또는 온라인 도구:**
- https://www.random.org/strings 사용

**예시 값:**
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**환경 선택:**
- ☑ Production
- ☑ Preview
- ☑ Development

**추가 버튼 클릭**

##### 선택 변수 3: FLASK_ENV (선택사항)
```
Key: FLASK_ENV
Value: production
```

**환경 선택:**
- ☑ Production
- ☑ Preview
- ☑ Development

##### 선택 변수 4: GITHUB_WEBHOOK_SECRET (GitHub 연동 사용 시)
```
Key: GITHUB_WEBHOOK_SECRET
Value: your-github-webhook-secret-here
```

#### 4단계: 저장 확인
- 추가한 모든 환경변수가 목록에 표시되는지 확인
- 각 변수의 Value가 마스킹(****)되어 표시됨 (보안상 정상)

#### 5단계: 재배포
환경변수는 **자동으로 새 배포에 적용**됩니다. 즉시 적용하려면:

1. **Deployments** 탭 클릭
2. 최신 배포 우측 **"..."** 메뉴 클릭
3. **Redeploy** 선택
4. 확인

또는 CLI로:
```bash
vercel --prod
```

---

## 방법 2: Vercel CLI로 설정

### 사전 준비

```bash
# Vercel CLI 설치 확인
vercel --version

# 로그인 확인
vercel whoami
```

### 환경변수 추가

#### DATABASE_URL 추가
```bash
vercel env add DATABASE_URL
```

**프롬프트 응답:**
```
? What’s the value of DATABASE_URL? 
> postgresql://user:pass@host:port/db?sslmode=require

? Add DATABASE_URL to which Environments (select multiple)?
> Production
> Preview
> Development
```

#### SECRET_KEY 추가
```bash
# 먼저 랜덤 키 생성
openssl rand -hex 32

# 생성된 키를 복사한 후
vercel env add SECRET_KEY
```

**프롬프트 응답:**
```
? What’s the value of SECRET_KEY? 
> [생성된 키 붙여넣기]

? Add SECRET_KEY to which Environments (select multiple)?
> Production
> Preview
> Development
```

#### FLASK_ENV 추가
```bash
vercel env add FLASK_ENV production production preview development
```

### 환경변수 확인

```bash
# 모든 환경변수 목록 보기
vercel env ls

# 특정 환경변수 확인
vercel env pull .env.local
cat .env.local
```

### 환경변수 삭제

```bash
vercel env rm DATABASE_URL
```

---

## 방법 3: 프로젝트 루트에 .env 파일 사용 (로컬 개발용)

⚠️ **주의**: `.env` 파일은 Git에 커밋하면 안 됩니다!

### .env 파일 생성

```bash
cd /Users/USER/dev/r&d
cat > .env << EOF
DATABASE_URL=postgresql://user:pass@localhost:5432/wecar_db
SECRET_KEY=dev-secret-key-local-only
FLASK_ENV=development
EOF
```

### .env.local (Vercel용 - Git에 커밋하지 않음)

```bash
cat > .env.local << EOF
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
SECRET_KEY=production-secret-key
FLASK_ENV=production
EOF
```

### 로컬에서 환경변수 로드

```bash
# .env 파일 자동 로드 (python-dotenv 사용)
python run.py
```

---

## PostgreSQL 데이터베이스 서비스 선택 가이드

### 추천 서비스 비교

#### 1. Supabase (무료 티어 제공)
**장점:**
- 무료 티어 제공 (500MB, 무료 백업)
- 자동 백업
- Web UI 제공
- PostgreSQL 15

**설정 방법:**
1. https://supabase.com 접속
2. 새 프로젝트 생성
3. Settings → Database → Connection string 복사
4. `?sslmode=require` 추가

**DATABASE_URL 형식:**
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
```

#### 2. Neon (서버리스 PostgreSQL)
**장점:**
- 서버리스 (사용한 만큼만 과금)
- 빠른 스핀업/다운
- 무료 티어 제공

**설정 방법:**
1. https://neon.tech 접속
2. 새 프로젝트 생성
3. Connection string 복사

**DATABASE_URL 형식:**
```
postgresql://[user]:[password]@[endpoint]/[dbname]?sslmode=require
```

#### 3. Railway
**장점:**
- 간단한 설정
- 무료 크레딧 제공

**설정 방법:**
1. https://railway.app 접속
2. 새 프로젝트 → PostgreSQL 추가
3. Variables 탭에서 DATABASE_URL 복사

---

## 환경변수 설정 검증

### 로컬에서 테스트

```bash
# 환경변수 설정
export DATABASE_URL="your-postgresql-url"
export SECRET_KEY="your-secret-key"

# 연결 테스트
python3 << EOF
import os
from sqlalchemy import create_engine, text

url = os.environ.get('DATABASE_URL')
if url:
    engine = create_engine(url)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print("✅ Database connection successful!")
else:
    print("❌ DATABASE_URL not set")
EOF
```

### Vercel 배포 후 확인

1. 배포된 URL 접속: `https://your-app.vercel.app/health`
2. 응답 확인:
```json
{
  "status": "ok",
  "application": "running",
  "database": "connected"
}
```

### Vercel 로그 확인

```bash
# 실시간 로그
vercel logs --follow

# 특정 배포 로그
vercel logs [deployment-url]
```

---

## 문제 해결

### 오류: DATABASE_URL must be set

**원인:** 환경변수가 설정되지 않았거나 재배포되지 않음

**해결:**
1. Vercel 대시보드에서 환경변수 확인
2. 모든 환경(Production, Preview, Development)에 설정되었는지 확인
3. 재배포 실행:
```bash
vercel --prod
```

### 오류: connection refused / timeout

**원인:** 
- PostgreSQL 서버 접근 불가
- 방화벽 차단
- 잘못된 연결 정보

**해결:**
1. PostgreSQL 서버가 실행 중인지 확인
2. SSL 모드 확인 (`?sslmode=require` 필수)
3. Vercel IP 허용 (일부 서비스는 필요 없음)
4. 연결 문자열 재확인

### 오류: authentication failed

**원인:** 잘못된 사용자명/비밀번호

**해결:**
1. PostgreSQL 서버의 사용자명/비밀번호 확인
2. URL 인코딩 확인 (특수문자는 % 인코딩 필요)
3. 연결 문자열 재생성

---

## 보안 체크리스트

- [ ] SECRET_KEY는 충분히 긴 랜덤 문자열 (최소 32자)
- [ ] DATABASE_URL에 비밀번호가 포함되어 있으므로 절대 Git에 커밋하지 않음
- [ ] `.env` 파일은 `.gitignore`에 포함됨
- [ ] Production과 Development 환경변수 분리
- [ ] 정기적으로 SECRET_KEY 로테이션

---

## 빠른 시작 체크리스트

1. [ ] PostgreSQL 서비스 선택 (Supabase/Neon 추천)
2. [ ] PostgreSQL 프로젝트 생성 및 연결 정보 복사
3. [ ] Vercel 대시보드 → Settings → Environment Variables
4. [ ] DATABASE_URL 추가 (모든 환경)
5. [ ] SECRET_KEY 생성 및 추가 (모든 환경)
6. [ ] 재배포: `vercel --prod`
7. [ ] `/health` 엔드포인트로 연결 확인

---

## 추가 자료

- Vercel 환경변수 문서: https://vercel.com/docs/concepts/projects/environment-variables
- Supabase 설정: https://supabase.com/docs/guides/database/connecting-to-postgres
- Neon 설정: https://neon.tech/docs/connect/connect-from-any-app

