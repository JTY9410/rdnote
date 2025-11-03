# 빠른 문제 해결 가이드

## 🔍 현재 오류 확인

배포된 URL의 `/debug` 엔드포인트 접속:
```
https://rdnote-83ozlpdrw-jeong-tai-youngs-projects.vercel.app/debug
```

또는 스크립트 실행:
```bash
./CHECK_DEPLOYMENT.sh
```

## ✅ 환경변수 빠른 설정

### 방법 1: 스크립트 사용 (가장 빠름)

```bash
./QUICK_ENV_SETUP.sh
```

스크립트가 안내에 따라 진행합니다.

### 방법 2: 수동 설정

#### 1단계: DATABASE_URL 추가

```bash
vercel env add DATABASE_URL
```

프롬프트에:
- Value: `postgresql://user:pass@host:port/db?sslmode=require`
- Environment: `production`, `preview`, `development` 모두 선택

#### 2단계: SECRET_KEY 생성 및 추가

```bash
# 키 생성
openssl rand -hex 32

# 생성된 키를 복사한 후
vercel env add SECRET_KEY
```

프롬프트에:
- Value: [생성된 키 붙여넣기]
- Environment: 모두 선택

#### 3단계: 재배포

```bash
vercel --prod
```

## 📋 PostgreSQL 서비스 선택 (아직 없다면)

### Supabase (추천)

1. https://supabase.com 접속
2. "Start your project" → GitHub 로그인
3. "New Project" 생성
4. Settings → Database → Connection string 복사
5. 끝에 `?sslmode=require` 추가

### Neon

1. https://neon.tech 접속
2. 프로젝트 생성
3. Connection string 복사

## ✅ 확인

재배포 후:
```
https://your-app.vercel.app/health
```

성공 응답:
```json
{
  "status": "ok",
  "database": "connected"
}
```

## 🆘 여전히 안되면

1. 로그 확인:
   ```bash
   vercel logs --follow
   ```

2. `/debug` 엔드포인트에서 구체적인 오류 확인

3. `TROUBLESHOOT_VERCEL.md` 참조

