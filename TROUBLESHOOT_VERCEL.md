# Vercel 초기화 오류 해결 가이드

## 🔍 오류 진단

### 1. 오류 메시지 확인

배포된 URL의 `/debug` 엔드포인트로 접속:
```
https://your-app.vercel.app/debug
```

이 엔드포인트에서 다음을 확인할 수 있습니다:
- 구체적인 오류 메시지
- 환경변수 설정 상태
- 전체 스택 트레이스

### 2. Vercel 로그 확인

```bash
# 실시간 로그 확인
vercel logs --follow

# 특정 배포의 로그
vercel logs [deployment-url]
```

또는 Vercel 대시보드에서:
- 프로젝트 → Deployments → 최신 배포 클릭 → Logs 탭

---

## 🛠️ 일반적인 해결 방법

### 문제 1: "DATABASE_URL must be set"

**증상:**
```json
{
  "error": "DATABASE_URL environment variable is not set"
}
```

**해결:**

1. **Vercel 대시보드에서 환경변수 확인**
   - https://vercel.com → 프로젝트 → Settings → Environment Variables
   - `DATABASE_URL`이 있는지 확인

2. **없다면 추가:**
   ```
   Key: DATABASE_URL
   Value: postgresql://user:pass@host:port/db?sslmode=require
   Environment: Production, Preview, Development 모두 선택
   ```

3. **재배포:**
   ```bash
   vercel --prod
   ```

### 문제 2: 데이터베이스 연결 실패

**증상:**
```json
{
  "database": "disconnected"
}
```

**해결:**

1. **DATABASE_URL 형식 확인:**
   ```
   ✅ 올바른 형식: postgresql://user:pass@host:port/db?sslmode=require
   ❌ 잘못된 형식: postgresql://user:pass@host:port/db
   ```

2. **SSL 모드 확인:**
   - 끝에 `?sslmode=require` 추가되었는지 확인
   - 일부 서비스는 `?sslmode=prefer`도 허용

3. **비밀번호 특수문자 확인:**
   - 비밀번호에 특수문자가 있으면 URL 인코딩 필요
   - 예: `@` → `%40`, `#` → `%23`

4. **연결 테스트 (로컬에서):**
   ```bash
   export DATABASE_URL="your-url"
   python3 << EOF
   from sqlalchemy import create_engine, text
   engine = create_engine("$DATABASE_URL")
   with engine.connect() as conn:
       conn.execute(text('SELECT 1'))
       print("✅ Connection OK")
   EOF
   ```

### 문제 3: 모듈 import 오류

**증상:**
로그에 `ModuleNotFoundError` 또는 `ImportError` 표시

**해결:**

1. **requirements.txt 확인:**
   ```bash
   cat requirements.txt
   ```

2. **필요한 패키지 모두 포함되어 있는지 확인**

3. **Vercel 빌드 로그 확인:**
   - Deployments → Build Logs
   - 패키지 설치 실패 여부 확인

### 문제 4: SECRET_KEY 오류

**증상:**
세션 관련 오류

**해결:**

1. **SECRET_KEY 생성 및 추가:**
   ```bash
   openssl rand -hex 32
   ```

2. **Vercel 환경변수에 추가:**
   ```
   Key: SECRET_KEY
   Value: [생성된 키]
   ```

---

## 📋 체크리스트

배포 전 확인사항:

- [ ] DATABASE_URL 설정됨
- [ ] SECRET_KEY 설정됨
- [ ] 환경변수가 모든 환경(Production/Preview/Development)에 설정됨
- [ ] DATABASE_URL에 `?sslmode=require` 포함
- [ ] PostgreSQL 서버 접근 가능
- [ ] requirements.txt에 모든 패키지 포함
- [ ] Git에 `.env` 파일 커밋되지 않음

---

## 🔧 즉시 수정 방법

### 빠른 수정 스크립트 실행

```bash
cd /Users/USER/dev/r&d

# 1. 환경변수 확인
vercel env ls

# 2. 없으면 추가
./QUICK_ENV_SETUP.sh

# 3. 재배포
vercel --prod

# 4. 로그 확인
vercel logs --follow
```

---

## 📞 상세 오류 분석

`/debug` 엔드포인트 응답 예시:

```json
{
  "error": "DATABASE_URL environment variable is not set",
  "traceback": [...],
  "env_check": {
    "DATABASE_URL": "NOT SET",
    "SECRET_KEY": "SET",
    "VERCEL": "1"
  }
}
```

이 정보를 바탕으로:
- 어떤 환경변수가 누락되었는지 확인
- 어디서 오류가 발생했는지 확인 (traceback)
- 다음 단계 결정

---

## 💡 예방 방법

1. **배포 전 로컬 테스트:**
   ```bash
   export DATABASE_URL="your-url"
   export SECRET_KEY="your-key"
   python run.py
   ```

2. **환경변수 템플릿 파일 유지:**
   - `.env.example` 파일에 예시 저장
   - Git에 커밋하여 팀원과 공유

3. **Vercel 환경변수 백업:**
   ```bash
   vercel env pull .env.local
   # .env.local은 Git에 커밋하지 않음
   ```

