# Vercel 배포 가이드

이 문서는 WECar 연구개발일지 Flask 애플리케이션을 Vercel에 배포하는 방법을 안내합니다.

## ⚠️ 중요 사항

Vercel은 서버리스(serverless) 플랫폼입니다. 다음 제한사항을 이해하세요:

1. **파일 저장소**: `/tmp` 디렉토리만 사용 가능하며, 함수 실행 후 삭제됩니다
   - 업로드된 파일과 생성된 PDF는 함수 종료 후 사라집니다
   - **해결책**: 프로덕션에서는 S3, Cloudflare R2 같은 객체 스토리지 사용 권장

2. **실행 시간 제한**: 
   - 무료 플랜: 10초
   - Pro 플랜: 60초 (현재 설정됨)

3. **Cold Start**: 첫 요청 시 2-5초 소요 가능

4. **데이터베이스**: 외부 PostgreSQL 데이터베이스 필요 (Vercel은 DB 제공 안 함)

## 📋 사전 요구사항

1. **Vercel 계정**: https://vercel.com 에서 생성
2. **Vercel CLI**: 설치 필요
3. **PostgreSQL 데이터베이스**: 
   - Railway, Supabase, Neon, 또는 다른 PostgreSQL 호스팅 서비스
4. **GitHub/GitLab/Bitbucket 저장소**: 코드가 있어야 함

## 🚀 배포 단계

### 1. Vercel CLI 설치

```bash
npm i -g vercel
```

또는

```bash
brew install vercel-cli
```

### 2. 프로젝트 디렉토리에서 로그인

```bash
cd /Users/USER/dev/r&d
vercel login
```

### 3. 환경 변수 설정

Vercel 대시보드 또는 CLI로 환경 변수를 설정해야 합니다:

#### 필수 환경 변수

```bash
# 데이터베이스 연결
DATABASE_URL=postgresql://user:password@host:port/database

# Flask 시크릿 키 (랜덤 문자열)
SECRET_KEY=your-very-secret-key-change-this-in-production

# 업로드/내보내기 경로 (Vercel에서는 /tmp 사용)
UPLOAD_FOLDER=/tmp/uploads
EXPORT_FOLDER=/tmp/exports
```

#### CLI로 환경 변수 설정

```bash
vercel env add DATABASE_URL
# 프롬프트에 따라 값 입력 (production, preview, development 선택)

vercel env add SECRET_KEY
vercel env add UPLOAD_FOLDER
vercel env add EXPORT_FOLDER
```

또는 Vercel 대시보드에서:
1. 프로젝트 선택
2. Settings → Environment Variables
3. 변수 추가

### 4. 데이터베이스 마이그레이션

Vercel은 서버리스 환경이므로 마이그레이션을 수동으로 실행해야 합니다:

#### 옵션 1: 로컬에서 마이그레이션 실행

```bash
# 로컬 환경 설정
export DATABASE_URL="your-postgres-url"
export FLASK_APP=wsgi.py

# 마이그레이션 실행
alembic upgrade head
```

#### 옵션 2: Vercel Function으로 마이그레이션 엔드포인트 생성 (권장하지 않음)

프로덕션에서는 안전하지 않으므로 로컬 또는 CI/CD에서 실행 권장.

### 5. 배포

#### 첫 배포 (프로젝트 연결)

```bash
vercel
```

프롬프트에 따라:
- Set up and deploy? → **Yes**
- Which scope? → 본인 계정 선택
- Link to existing project? → **No** (첫 배포)
- Project name? → `wecar-rnd` (원하는 이름)
- Directory? → **.** (현재 디렉토리)

#### 프로덕션 배포

```bash
vercel --prod
```

### 6. 배포 확인

배포 완료 후 출력되는 URL로 접속하여 확인:
- 예: `https://wecar-rnd.vercel.app`

## 🔧 문제 해결

### DEPLOYMENT_NOT_FOUND 오류

이 오류는 다음 경우에 발생합니다:

1. **배포가 완료되지 않음**: 
   ```bash
   vercel --prod
   ```
   재배포 시도

2. **프로젝트가 연결되지 않음**:
   ```bash
   vercel link
   ```

3. **환경 변수 누락**:
   - Vercel 대시보드에서 환경 변수 확인
   - 특히 `DATABASE_URL` 필수

### 데이터베이스 연결 오류

- `DATABASE_URL` 형식 확인: `postgresql://user:pass@host:port/dbname`
- 데이터베이스 서버가 인터넷에서 접근 가능한지 확인
- 방화벽 설정 확인 (Vercel IP 화이트리스트 필요할 수 있음)

### 파일 업로드 오류

- `/tmp` 디렉토리는 함수 실행 중에만 존재합니다
- 업로드된 파일은 함수 종료 후 삭제됩니다
- **해결책**: 객체 스토리지(S3, Cloudflare R2) 사용 필수

### Cold Start 지연

- 첫 요청 후 다음 요청은 빠릅니다 (warm start)
- 중요 기능은 워밍업 엔드포인트 생성 고려

## 📁 파일 구조

배포에 필요한 파일:

```
.
├── vercel.json          # Vercel 설정
├── wsgi.py              # Vercel 진입점
├── app/                 # Flask 애플리케이션
├── requirements.txt     # Python 의존성
└── migrations/          # Alembic 마이그레이션
```

## 🔄 업데이트 배포

코드 수정 후:

```bash
# 개발 환경에 배포
vercel

# 프로덕션에 배포
vercel --prod
```

## 🌐 커스텀 도메인 설정

1. Vercel 대시보드 → 프로젝트 → Settings → Domains
2. 도메인 추가
3. DNS 설정 (A 레코드 또는 CNAME)

## ⚡ 성능 최적화

1. **연결 풀링**: 
   - 현재 설정된 `SQLALCHEMY_ENGINE_OPTIONS`로 연결 재사용 최적화

2. **캐싱**:
   - Redis 같은 외부 캐시 서비스 사용 권장

3. **정적 파일**:
   - Vercel은 정적 파일을 자동으로 CDN에 배포

## 🔒 보안 고려사항

1. **SECRET_KEY**: 강력한 랜덤 문자열 사용
2. **DATABASE_URL**: 환경 변수로 관리 (코드에 노출 금지)
3. **HTTPS**: Vercel이 자동으로 제공
4. **CORS**: 필요시 설정 추가

## 📊 모니터링

- Vercel 대시보드에서 로그 확인
- Functions 탭에서 실행 시간 및 에러 확인
- Analytics 탭에서 트래픽 모니터링

## 🆘 지원

문제 발생 시:
1. Vercel 대시보드 로그 확인
2. `vercel logs` 명령으로 로그 확인
3. Vercel 문서: https://vercel.com/docs

## 📝 주의사항

**파일 저장소 문제 해결을 위한 권장 사항**:

현재 설정은 `/tmp`를 사용하지만, 프로덕션에서는 다음 중 하나를 구현해야 합니다:

1. **AWS S3** + `boto3`
2. **Cloudflare R2** + `boto3` (S3 호환 API)
3. **Google Cloud Storage**
4. **Azure Blob Storage**

예시 코드 (S3):

```python
import boto3
from flask import current_app

s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

def upload_file_to_s3(file, bucket, key):
    s3.upload_fileobj(file, bucket, key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def download_file_from_s3(bucket, key):
    return s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=3600)
```

이 변경사항을 적용하면 Vercel에서도 파일 저장이 안정적으로 작동합니다.

