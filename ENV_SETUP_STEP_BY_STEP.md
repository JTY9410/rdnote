# 환경변수 설정 단계별 가이드 (초보자용)

## 🎯 목표
Vercel에 배포된 애플리케이션이 데이터베이스에 연결할 수 있도록 환경변수를 설정합니다.

---

## 📋 사전 준비

### 1. PostgreSQL 데이터베이스 준비

아직 없으시다면 다음 중 하나를 선택하세요:

#### 옵션 A: Supabase 사용 (무료, 추천)

1. **Supabase 가입**
   - https://supabase.com 접속
   - "Start your project" 클릭
   - GitHub 계정으로 로그인

2. **프로젝트 생성**
   - "New Project" 클릭
   - 프로젝트 이름 입력 (예: `rdnote`)
   - 데이터베이스 비밀번호 설정 (기억해두세요!)
   - Region 선택 (가장 가까운 지역)
   - "Create new project" 클릭
   - 1-2분 대기 (프로젝트 생성 중)

3. **연결 정보 복사**
   - 좌측 메뉴에서 **Settings** (톱니바퀴 아이콘) 클릭
   - **Database** 메뉴 클릭
   - **Connection string** 섹션 찾기
   - **URI** 탭 선택
   - 연결 문자열 복사
   - 형식: `postgresql://postgres.[xxxxx]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`
   - **중요**: 끝에 `?sslmode=require` 추가!
   - 최종 형식: `postgresql://postgres.[xxxxx]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres?sslmode=require`

#### 옵션 B: Neon 사용 (무료, 서버리스)

1. **Neon 가입**
   - https://neon.tech 접속
   - "Sign Up" 클릭
   - GitHub 계정으로 로그인

2. **프로젝트 생성**
   - "Create a project" 클릭
   - 프로젝트 이름 입력
   - Region 선택
   - PostgreSQL 버전 선택 (15 권장)
   - "Create Project" 클릭

3. **연결 정보 복사**
   - 프로젝트 대시보드에서 **Connection string** 복사
   - 이미 `?sslmode=require`가 포함되어 있을 수 있음

---

## 🔧 Vercel 환경변수 설정 (웹 대시보드)

### 1단계: Vercel 대시보드 접속

1. 브라우저에서 https://vercel.com 접속
2. 로그인 (GitHub 계정)
3. 대시보드에서 **rdnote** 프로젝트 클릭

### 2단계: 환경변수 페이지 이동

1. 프로젝트 페이지 상단 메뉴에서 **Settings** 클릭
   ![Settings 메뉴 위치](https://vercel.com/docs/concepts/projects/environment-variables#adding-environment-variables)
   
2. 좌측 사이드바에서 **Environment Variables** 클릭
   - 또는 URL 직접 접속: `https://vercel.com/[your-username]/rdnote/settings/environment-variables`

### 3단계: DATABASE_URL 추가

1. **"Add New"** 또는 **"Add"** 버튼 클릭

2. **Key** 입력란에:
   ```
   DATABASE_URL
   ```

3. **Value** 입력란에:
   - 위에서 복사한 PostgreSQL 연결 문자열 붙여넣기
   - 예시:
   ```
   postgresql://postgres.xxxxx:mypassword@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require
   ```

4. **Environment** 선택:
   - ☑ Production
   - ☑ Preview
   - ☑ Development
   
   (모두 선택하는 것을 권장)

5. **"Save"** 또는 **"Add"** 버튼 클릭

### 4단계: SECRET_KEY 추가

1. **"Add New"** 버튼 다시 클릭

2. **Key** 입력:
   ```
   SECRET_KEY
   ```

3. **Value 생성 방법:**

   **터미널(Mac/Linux)에서:**
   ```bash
   openssl rand -hex 32
   ```
   
   생성된 문자열을 복사 (예: `a1b2c3d4e5f6...`)
   
   **또는 온라인:**
   - https://www.random.org/strings 접속
   - Length: 64, Character set: Hex 선택
   - Generate 클릭
   - 생성된 문자열 복사

4. **Value** 입력란에 생성된 키 붙여넣기

5. **Environment** 선택:
   - ☑ Production
   - ☑ Preview
   - ☑ Development

6. **"Save"** 버튼 클릭

### 5단계: FLASK_ENV 추가 (선택사항)

1. **"Add New"** 버튼 클릭

2. **Key**: `FLASK_ENV`
3. **Value**: `production`
4. **Environment**: 모두 선택
5. **"Save"** 클릭

### 6단계: 확인

환경변수 목록에 다음이 표시되어야 합니다:
- ✅ DATABASE_URL (값은 ****로 마스킹됨)
- ✅ SECRET_KEY (값은 ****로 마스킹됨)
- ✅ FLASK_ENV (선택사항)

---

## 🚀 재배포

환경변수는 새 배포에만 적용됩니다. 즉시 적용하려면:

### 방법 A: 웹 대시보드에서

1. 프로젝트 페이지에서 **Deployments** 탭 클릭
2. 최신 배포 항목의 우측 **"..."** (세 점) 클릭
3. **"Redeploy"** 선택
4. 확인 대화상자에서 **"Redeploy"** 클릭

### 방법 B: CLI에서

```bash
cd /Users/USER/dev/r&d
vercel --prod
```

---

## ✅ 검증

### 1. 로그 확인

```bash
vercel logs --follow
```

정상이라면 데이터베이스 연결 메시지가 보입니다.

### 2. Health Check

브라우저에서 접속:
```
https://rdnote-fpfpzf9yw-jeong-tai-youngs-projects.vercel.app/health
```

응답 예시:
```json
{
  "status": "ok",
  "application": "running",
  "database": "connected"
}
```

**"database": "connected"** 가 보이면 성공! ✅

---

## 🔍 문제 해결

### 문제: "DATABASE_URL must be set" 오류

**해결:**
1. 환경변수가 실제로 추가되었는지 확인
2. Production 환경에 추가되었는지 확인
3. 재배포 실행 (`vercel --prod`)

### 문제: "database": "disconnected" 응답

**가능한 원인:**
1. DATABASE_URL이 잘못됨
2. PostgreSQL 서버에 접근 불가
3. 비밀번호가 틀림

**해결:**
1. DATABASE_URL 재확인 (특히 비밀번호)
2. `?sslmode=require` 포함 여부 확인
3. PostgreSQL 서버가 실행 중인지 확인
4. Supabase/Neon 대시보드에서 연결 상태 확인

### 문제: 연결 타임아웃

**해결:**
1. 네트워크 연결 확인
2. PostgreSQL 서비스 제공업체 상태 페이지 확인
3. 다른 연결 문자열 시도 (pooler vs direct)

---

## 📞 추가 도움

- Vercel 문서: https://vercel.com/docs
- Supabase 문서: https://supabase.com/docs
- Neon 문서: https://neon.tech/docs

---

## 🎉 완료!

환경변수 설정이 완료되었습니다. 이제 애플리케이션이 정상 작동할 것입니다!

