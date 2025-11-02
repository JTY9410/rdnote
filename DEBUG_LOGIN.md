# 로그인 오류 디버깅 가이드

## 빠른 진단 도구 실행

```bash
python3 check_login_debug.py
```

이 스크립트는 다음을 자동으로 확인합니다:
1. 환경 변수 설정
2. 데이터베이스 연결
3. 세션 설정
4. 비밀번호 검증
5. 로그인 프로세스 시뮬레이션

## 수동 확인 방법

### 1. 브라우저 쿠키 확인

#### Chrome/Edge
1. **개발자 도구 열기**
   - `F12` 또는 `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)

2. **Application 탭 선택**
   - 상단 탭 메뉴에서 "Application" 클릭

3. **Cookies 확인**
   - 왼쪽 사이드바: `Cookies` → `http://localhost:5501` (또는 사이트 URL)
   - 또는 `Cookies` → `https://[your-domain]` (프로덕션)

4. **확인할 쿠키**
   ```
   session
   ├── Name: session
   ├── Value: [암호화된 세션 데이터]
   ├── Domain: localhost (또는 실제 도메인)
   ├── Path: /
   ├── Expires: Session 또는 날짜
   ├── HttpOnly: ✓ 체크됨
   ├── Secure: 프로덕션에서만 체크
   └── SameSite: Lax
   ```

#### Firefox
1. **개발자 도구 열기**: `F12`
2. **Storage 탭 선택**
3. **Cookies** → 사이트 URL 선택
4. `session` 쿠키 확인

#### 확인 사항
- ✓ `session` 쿠키가 존재하는가?
- ✓ 쿠키 값이 비어있지 않은가? (로그인 후)
- ✓ `HttpOnly` 플래그가 설정되어 있는가?
- ✓ `SameSite` 속성이 `Lax` 또는 `Strict`인가?

#### 쿠키가 생성되지 않는 경우
1. **브라우저 설정 확인**
   - 쿠키 차단 설정 확인
   - 사설 브우징 모드 비활성화
   - 타사 쿠키 차단 해제

2. **확장 프로그램 확인**
   - 광고 차단기 비활성화
   - 프라이버시 확장 프로그램 확인

3. **도메인 확인**
   - `localhost`와 `127.0.0.1`은 다른 도메인으로 처리됨
   - 일관된 도메인 사용

### 2. 서버 로그 확인

#### 로컬 실행 시
```bash
python run.py
```
터미널에 실시간 로그가 출력됩니다.

#### Docker 사용 시
```bash
docker-compose logs -f app
```

#### 로그인 성공 시 예상 로그
```
INFO:app:Attempting login for email: jty9410@wecar-m.co.kr
INFO:app:User found: jty9410@wecar-m.co.kr, status: active, has_hash: True
INFO:app:Password check for jty9410@wecar-m.co.kr: True
INFO:app:User jty9410@wecar-m.co.kr logged in successfully (ID: 1)
INFO:app:Redirecting jty9410@wecar-m.co.kr (ID: 1) to dashboard
INFO:app:Dashboard URL: /dashboard
INFO:app:Dashboard access by user: jty9410@wecar-m.co.kr
```

#### 오류 발생 시 확인할 로그
- `ERROR:app:Error checking password for ...: ...`
  - 비밀번호 검증 오류
  - 비밀번호 해시 형식 문제 가능
  
- `ERROR:app:Database error during login for ...: ...`
  - 데이터베이스 연결 문제
  - 쿼리 실행 오류
  
- `ERROR:app:Failed to login user ...: ...`
  - `login_user()` 호출 실패
  - 세션 저장 실패 가능
  
- `ERROR:app:Failed to redirect after login: ...`
  - 리다이렉트 실패
  - 인증 상태 불일치 가능

#### 로그 레벨 조정
더 상세한 로그를 보려면 `app/__init__.py`에서:
```python
logging.basicConfig(level=logging.DEBUG)  # INFO → DEBUG
```

### 3. 환경 변수 확인

#### 현재 설정 확인
```bash
# 로컬 환경
echo $SECRET_KEY
echo $DATABASE_URL

# 또는 Python으로 확인
python3 -c "
import os
print('SECRET_KEY:', '설정됨' if os.environ.get('SECRET_KEY') else '기본값')
print('DATABASE_URL:', '설정됨' if os.environ.get('DATABASE_URL') else '기본값')
"
```

#### SECRET_KEY 확인
```bash
python3 -c "
from app import create_app
app = create_app()
print('SECRET_KEY 길이:', len(app.config['SECRET_KEY']))
print('SECRET_KEY 기본값 여부:', app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production')
"
```

#### 환경 변수 설정
**로컬 개발 환경:**
```bash
export SECRET_KEY="your-random-secret-key-here"
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
```

**Docker:**
`docker-compose.yml` 또는 `.env` 파일에서 설정

**Vercel:**
Vercel 대시보드 → Project Settings → Environment Variables

## 일반적인 문제 해결

### 문제 1: 로그인 후 즉시 로그아웃됨
**원인**: 세션 쿠키가 저장되지 않음
**해결**:
1. 브라우저 쿠키 설정 확인
2. `SECRET_KEY` 확인 (값이 변경되었는지)
3. 도메인/포트 일관성 확인

### 문제 2: "로그인 세션 생성에 실패했습니다"
**원인**: `login_user()` 호출 실패
**해결**:
1. 서버 로그에서 스택 트레이스 확인
2. 세션 저장소 확인 (파일 시스템 권한)
3. `session_protection` 설정 확인

### 문제 3: 데이터베이스 오류
**원인**: DB 연결 문제 또는 쿼리 오류
**해결**:
1. `DATABASE_URL` 확인
2. 데이터베이스 서버 실행 확인
3. 네트워크 연결 확인

### 문제 4: 비밀번호 확인 실패
**원인**: 비밀번호 해시 형식 문제
**해결**:
1. 사용자 계정의 `password_hash` 확인
2. 필요 시 비밀번호 재설정

## 비밀번호 재설정

관리자 계정 비밀번호를 재설정하려면:

```bash
python3 -c "
from app import create_app, db
from app.models.user import User
from app.utils.auth import hash_password
app = create_app()
with app.app_context():
    user = User.query.filter_by(email='jty9410@wecar-m.co.kr').first()
    if user:
        user.password_hash = hash_password('#jeong07209')
        db.session.commit()
        print('✓ 비밀번호 재설정 완료')
    else:
        print('✗ 사용자를 찾을 수 없습니다')
"
```

## 추가 지원

위의 방법으로도 문제가 해결되지 않으면:
1. 서버 로그의 전체 스택 트레이스 복사
2. 브라우저 개발자 도구의 Network 탭 스크린샷
3. `check_login_debug.py` 실행 결과
4. 발생한 정확한 오류 메시지

이 정보들을 함께 공유해주시면 더 정확한 진단이 가능합니다.

