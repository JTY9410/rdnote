# 로그인 오류 디버깅 가이드

## 로그 확인 방법

### 1. 로컬 서버 실행 시
```bash
python run.py
```
터미널에 실시간 로그가 출력됩니다.

### 2. Docker 사용 시
```bash
docker-compose logs -f app
```

## 주요 로그 메시지

로그인 프로세스에서 다음 로그 메시지들을 확인하세요:

1. **로그인 시도**
   - `Attempting login for email: {email}`

2. **사용자 찾기**
   - `User found: {email}, status: {status}, has_hash: {bool}`
   - 또는 사용자가 없으면 이 메시지가 없음

3. **비밀번호 확인**
   - `Password check for {email}: {True/False}`

4. **로그인 성공**
   - `User {email} logged in successfully`
   - `Redirecting {email} to dashboard`
   - `Dashboard URL: {url}`

5. **오류 발생 시**
   - `Error checking password for {email}: {error}`
   - `Database error during login for {email}: {error}`
   - `Failed to login user {email}: {error}`
   - `Failed to redirect after login: {error}`

## 일반적인 오류 원인

### 1. 데이터베이스 연결 오류
**증상**: `Database error during login` 로그
**해결**: DATABASE_URL 환경 변수 확인

### 2. 세션 문제
**증상**: 로그인 후 즉시 로그아웃되거나 세션이 유지되지 않음
**해결**: SECRET_KEY 확인, 브라우저 쿠키 설정 확인

### 3. 비밀번호 해시 문제
**증상**: `Error checking password` 로그
**해결**: 사용자의 password_hash 필드 확인

### 4. 대시보드 접근 오류
**증상**: 로그인은 되지만 대시보드 로드 실패
**해결**: 대시보드 로그 확인, 데이터베이스 쿼리 오류 확인

## 관리자 계정 확인

다음 명령으로 관리자 계정 상태 확인:

```bash
python3 -c "
from app import create_app, db
from app.models.user import User
app = create_app()
with app.app_context():
    admins = User.query.filter_by(is_admin=True).all()
    for u in admins:
        print(f'{u.email}: status={u.status}, has_hash={bool(u.password_hash)}')
"
```

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
        print('Password updated')
"
```

