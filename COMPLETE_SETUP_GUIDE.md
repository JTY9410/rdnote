# 완전한 환경 설정 가이드 (순서대로 따라하기)

## 🎯 목표
PostgreSQL 데이터베이스 생성부터 Vercel 배포까지 완전한 설정

---

## 📌 1단계: PostgreSQL 데이터베이스 준비

### 옵션 A: Supabase 사용 (추천, 무료)

#### 1-1. Supabase 가입
1. 브라우저에서 **https://supabase.com** 접속
2. **"Start your project"** 클릭
3. GitHub 계정으로 로그인

#### 1-2. 프로젝트 생성
1. **"New Project"** 버튼 클릭
2. **Organization** 선택 (또는 새로 생성)
3. **Project details** 입력:
   - **Name**: `rdnote` (원하는 이름)
   - **Database Password**: 비밀번호 설정 (⚠️ 반드시 기록해두세요!)
   - **Region**: 가장 가까운 지역 선택 (예: `Southeast Asia (Singapore)`)
4. **"Create new project"** 클릭
5. **1-2분 대기** (프로젝트 생성 중)

#### 1-3. 연결 문자열 복사
1. 프로젝트가 생성되면 대시보드로 이동
2. 좌측 사이드바에서 **Settings** (톱니바퀴 아이콘) 클릭
3. **Database** 메뉴 클릭
4. **Connection string** 섹션으로 스크롤
5. **URI** 탭 클릭
6. 연결 문자열 복사 (예: `postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:6543/postgres`)
7. ⚠️ **중요**: 끝에 `?sslmode=require` 추가!

**최종 형식:**
```
postgresql://postgres.xxxxx:your-password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

**비밀번호에 특수문자가 있으면 URL 인코딩 필요:**
- `@` → `%40`
- `#` → `%23`
- `/` → `%2F`
- 등등

---

### 옵션 B: Neon 사용 (무료, 서버리스)

#### 1-1. Neon 가입
1. **https://neon.tech** 접속
2. **"Sign Up"** 클릭
3. GitHub 계정으로 로그인

#### 1-2. 프로젝트 생성
1. **"Create a project"** 클릭
2. **Project name**: `rdnote`
3. **Region**: 가장 가까운 지역
4. **PostgreSQL version**: 15 또는 16
5. **"Create Project"** 클릭

#### 1-3. 연결 문자열 복사
1. 프로젝트 대시보드에서 **"Connection string"** 버튼 클릭
2. 연결 문자열 복사
3. 이미 `?sslmode=require`가 포함되어 있을 수 있음
4. 없으면 수동으로 추가

---

## 🔧 2단계: Vercel 환경변수 추가

### 준비물
- ✅ PostgreSQL 연결 문자열 (위에서 복사한 것)
- ✅ SECRET_KEY: `a149467f009e36e85458a03e386803bde2becccd9a06b5dea820485324d0b850`

### 터미널에서 실행

```bash
# 프로젝트 디렉토리로 이동
cd '/Users/USER/dev/r&d'

# DATABASE_URL 추가
vercel env add DATABASE_URL
```

**프롬프트 응답:**
```
? What's the value of DATABASE_URL? 
> [위에서 복사한 연결 문자열 붙여넣기]
   예: postgresql://postgres.xxxxx:password@host:port/db?sslmode=require

? Add DATABASE_URL to which Environments (select multiple)? 
> Production
> Preview  
> Development
```

**모든 환경 선택 방법:**
- 방향키로 이동하고 **스페이스바**로 선택
- Production, Preview, Development 모두 선택
- **Enter**로 확인

---

```bash
# SECRET_KEY 추가
vercel env add SECRET_KEY
```

**프롬프트 응답:**
```
? What's the value of SECRET_KEY? 
> a149467f009e36e85458a03e386803bde2becccd9a06b5dea820485324d0b850

? Add SECRET_KEY to which Environments (select multiple)? 
> Production
> Preview
> Development
```

**모두 선택 후 Enter**

---

### 확인

```bash
# 환경변수 목록 확인
vercel env ls
```

다음이 표시되어야 합니다:
```
DATABASE_URL
  Production, Preview, Development

SECRET_KEY
  Production, Preview, Development
```

---

## 🚀 3단계: 재배포

```bash
cd '/Users/USER/dev/r&d'
vercel --prod
```

**예상 출력:**
```
Vercel CLI 48.8.0
Retrieving project…
Deploying jeong-tai-youngs-projects/rdnote
...
Production: https://your-app.vercel.app
```

---

## ✅ 4단계: 확인

### Health Check

브라우저에서 접속:
```
https://your-app.vercel.app/health
```

**성공 응답:**
```json
{
  "status": "ok",
  "application": "running",
  "database": "connected"
}
```

✅ **"database": "connected"** 가 보이면 성공!

### 로그인 페이지 확인

```
https://your-app.vercel.app/
```

로그인 페이지가 표시되면 정상 작동 중입니다.

---

## 🔍 문제 해결

### "database": "disconnected"

**가능한 원인:**
1. DATABASE_URL이 잘못됨
2. 비밀번호가 틀림
3. PostgreSQL 서버에 접근 불가

**해결:**
1. 연결 문자열 재확인
2. `?sslmode=require` 포함 여부 확인
3. Supabase/Neon 대시보드에서 연결 상태 확인
4. 로그 확인: `vercel logs --follow`

### 여전히 "Application failed to initialize"

**디버그 엔드포인트 확인:**
```
https://your-app.vercel.app/debug
```

이 엔드포인트에서:
- 어떤 환경변수가 누락되었는지
- 구체적인 오류 메시지
- 전체 스택 트레이스

를 확인할 수 있습니다.

---

## 📋 완료 체크리스트

- [ ] PostgreSQL 프로젝트 생성 완료 (Supabase 또는 Neon)
- [ ] 연결 문자열 복사 및 `?sslmode=require` 추가
- [ ] `vercel env add DATABASE_URL` 실행 완료
- [ ] `vercel env add SECRET_KEY` 실행 완료
- [ ] `vercel env ls`로 환경변수 확인 완료
- [ ] `vercel --prod`로 재배포 완료
- [ ] `/health` 엔드포인트에서 `"database": "connected"` 확인
- [ ] 로그인 페이지 접속 가능 확인

---

## 🎉 완료!

모든 단계를 완료하면 애플리케이션이 정상 작동합니다!

**다음 단계:**
1. 데이터베이스 마이그레이션 실행
2. 관리자 계정 생성
3. 애플리케이션 사용 시작

---

## 💡 팁

- **연결 문자열은 절대 공유하지 마세요** (비밀번호 포함)
- `.env` 파일은 Git에 커밋하지 마세요
- 환경변수는 Production/Preview/Development 모두에 설정하는 것을 권장
- 정기적으로 백업하세요

