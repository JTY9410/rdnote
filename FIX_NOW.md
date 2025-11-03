# 🚨 즉시 수정 가이드

## 현재 문제
환경변수가 설정되지 않아서 애플리케이션이 초기화되지 않습니다.

## ✅ 해결 방법 (5분 안에 완료)

### 1단계: PostgreSQL 데이터베이스 준비

**아직 없으시다면 Supabase 사용 (무료):**

1. https://supabase.com 접속
2. "Start your project" → GitHub 로그인
3. "New Project" 클릭
4. 프로젝트 이름: `rdnote` (또는 원하는 이름)
5. 비밀번호 설정 (기억해두세요!)
6. Region: 가장 가까운 지역 선택
7. "Create new project" 클릭
8. 1-2분 대기

**연결 문자열 복사:**
1. 좌측 메뉴에서 **Settings** (톱니바퀴 아이콘) 클릭
2. **Database** 메뉴 클릭
3. **Connection string** 섹션에서 **URI** 탭 선택
4. 연결 문자열 복사
5. **중요**: 끝에 `?sslmode=require` 추가!

**예시:**
```
원본: postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:6543/postgres
추가: postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

### 2단계: SECRET_KEY 생성

터미널에서:
```bash
openssl rand -hex 32
```

생성된 키를 복사해두세요 (예: `a1b2c3d4e5f6...`)

### 3단계: Vercel 환경변수 추가

**방법 A: CLI 사용 (추천)**

```bash
cd '/Users/USER/dev/r&d'

# DATABASE_URL 추가
vercel env add DATABASE_URL
# 프롬프트에 위에서 복사한 연결 문자열 붙여넣기
# 환경 선택: production, preview, development 모두 선택

# SECRET_KEY 추가
vercel env add SECRET_KEY
# 프롬프트에 위에서 생성한 키 붙여넣기
# 환경 선택: 모두 선택
```

**방법 B: 웹 대시보드 사용**

1. https://vercel.com 접속
2. 로그인 후 **rdnote** 프로젝트 클릭
3. **Settings** 클릭
4. **Environment Variables** 클릭
5. **Add New** 버튼 클릭

**DATABASE_URL 추가:**
- Key: `DATABASE_URL`
- Value: `postgresql://...?sslmode=require` (위에서 복사한 것)
- Environment: Production, Preview, Development 모두 체크
- Save 클릭

**SECRET_KEY 추가:**
- Key: `SECRET_KEY`
- Value: `a1b2c3d4...` (위에서 생성한 것)
- Environment: 모두 체크
- Save 클릭

### 4단계: 재배포

```bash
cd '/Users/USER/dev/r&d'
vercel --prod
```

### 5단계: 확인

배포 완료 후:
```
https://your-app.vercel.app/health
```

성공하면:
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

## ⚡ 빠른 복사/붙여넣기 명령어

```bash
cd '/Users/USER/dev/r&d'

# 1. SECRET_KEY 생성 및 복사
SECRET_KEY=$(openssl rand -hex 32)
echo "생성된 SECRET_KEY: $SECRET_KEY"
echo "이 키를 복사하세요!"

# 2. 환경변수 추가 (위에서 복사한 값 사용)
vercel env add DATABASE_URL
# [연결 문자열 붙여넣기, production/preview/development 선택]

vercel env add SECRET_KEY
# [생성된 키 붙여넣기, 모두 선택]

# 3. 재배포
vercel --prod

# 4. 로그 확인
vercel logs --follow
```

---

## 🔍 문제 해결

### "DATABASE_URL must be set" 오류
→ 환경변수가 추가되지 않았거나 재배포되지 않음
→ 해결: 위의 3단계와 4단계 다시 실행

### 연결 실패
→ DATABASE_URL 형식 확인
→ `?sslmode=require` 포함 여부 확인
→ PostgreSQL 서버가 실행 중인지 확인

### 여전히 안되면
```bash
# 로그 확인
vercel logs --follow

# 환경변수 다시 확인
vercel env ls
```

