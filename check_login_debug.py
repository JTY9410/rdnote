#!/usr/bin/env python3
"""
로그인 디버깅 도구
브라우저 쿠키, 서버 로그, 환경 변수 등을 확인합니다.
"""
import os
import sys
from app import create_app

def check_environment():
    """환경 변수 확인"""
    print("=" * 60)
    print("1. 환경 변수 확인")
    print("=" * 60)
    
    secret_key = os.environ.get('SECRET_KEY')
    database_url = os.environ.get('DATABASE_URL')
    
    if secret_key:
        if secret_key == 'dev-secret-key-change-in-production':
            print("⚠️  SECRET_KEY: 기본값 사용 중 (프로덕션에서는 변경 필요)")
        else:
            print(f"✓ SECRET_KEY: 설정됨 (길이: {len(secret_key)}자)")
    else:
        print("✗ SECRET_KEY: 설정되지 않음 (기본값 사용)")
    
    if database_url:
        # URL에서 비밀번호 부분 숨기기
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
                if ':' in user_pass:
                    user = user_pass.split(':')[0]
                    print(f"✓ DATABASE_URL: 설정됨 (사용자: {user})")
                else:
                    print(f"✓ DATABASE_URL: 설정됨")
            else:
                print(f"✓ DATABASE_URL: 설정됨")
        else:
            print(f"✓ DATABASE_URL: 설정됨")
    else:
        print("✗ DATABASE_URL: 설정되지 않음 (기본값 사용)")
    
    print()

def check_database():
    """데이터베이스 연결 및 사용자 확인"""
    print("=" * 60)
    print("2. 데이터베이스 연결 및 사용자 확인")
    print("=" * 60)
    
    try:
        app = create_app()
        with app.app_context():
            from app import db
            from app.models.user import User
            
            # 데이터베이스 연결 테스트
            try:
                user_count = User.query.count()
                print(f"✓ 데이터베이스 연결 성공 (사용자 수: {user_count})")
            except Exception as e:
                print(f"✗ 데이터베이스 연결 실패: {e}")
                return
            
            # 관리자 계정 확인
            admins = User.query.filter_by(is_admin=True).all()
            print(f"✓ 관리자 계정 수: {len(admins)}")
            
            for admin in admins:
                print(f"  - {admin.email}: status={admin.status}, has_password={bool(admin.password_hash)}")
            
            # 테스트 로그인 가능한 계정 확인
            test_user = User.query.filter_by(email='jty9410@wecar-m.co.kr').first()
            if test_user:
                print(f"\n✓ 테스트 계정 확인:")
                print(f"  이메일: {test_user.email}")
                print(f"  상태: {test_user.status}")
                print(f"  비밀번호 해시: {'있음' if test_user.password_hash else '없음'}")
                if test_user.password_hash:
                    print(f"  해시 형식: {test_user.password_hash[:20]}...")
            else:
                print("\n✗ 테스트 계정 없음")
                
    except Exception as e:
        print(f"✗ 데이터베이스 확인 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def check_session_config():
    """세션 설정 확인"""
    print("=" * 60)
    print("3. 세션 설정 확인")
    print("=" * 60)
    
    try:
        app = create_app()
        
        print(f"✓ PERMANENT_SESSION_LIFETIME: {app.config.get('PERMANENT_SESSION_LIFETIME')}초")
        print(f"✓ SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
        print(f"✓ SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
        print(f"✓ SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
        print(f"✓ Session Protection: {app.login_manager.session_protection}")
        
    except Exception as e:
        print(f"✗ 세션 설정 확인 중 오류: {e}")
    
    print()

def check_password_verification():
    """비밀번호 검증 테스트"""
    print("=" * 60)
    print("4. 비밀번호 검증 테스트")
    print("=" * 60)
    
    try:
        app = create_app()
        with app.app_context():
            from app.models.user import User
            from app.utils.auth import check_password
            
            test_user = User.query.filter_by(email='jty9410@wecar-m.co.kr').first()
            if test_user and test_user.password_hash:
                # 올바른 비밀번호 테스트
                result_correct = check_password(test_user.password_hash, '#jeong07209')
                print(f"✓ 올바른 비밀번호 검증: {result_correct}")
                
                # 잘못된 비밀번호 테스트
                result_wrong = check_password(test_user.password_hash, 'wrong_password')
                print(f"✓ 잘못된 비밀번호 검증: {not result_wrong} (예상: False)")
                
                if result_correct and not result_wrong:
                    print("✓ 비밀번호 검증 함수 정상 작동")
                else:
                    print("✗ 비밀번호 검증 함수에 문제가 있습니다")
            else:
                print("✗ 테스트할 사용자를 찾을 수 없습니다")
                
    except Exception as e:
        print(f"✗ 비밀번호 검증 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def check_login_process():
    """로그인 프로세스 시뮬레이션"""
    print("=" * 60)
    print("5. 로그인 프로세스 시뮬레이션")
    print("=" * 60)
    
    try:
        app = create_app()
        with app.app_context():
            from app.models.user import User
            
            # 1. 사용자 조회
            user = User.query.filter_by(email='jty9410@wecar-m.co.kr').first()
            if not user:
                print("✗ 사용자를 찾을 수 없습니다")
                return
            
            print(f"✓ 1단계: 사용자 조회 성공 ({user.email})")
            
            # 2. 비밀번호 확인
            from app.utils.auth import check_password
            if check_password(user.password_hash, '#jeong07209'):
                print("✓ 2단계: 비밀번호 확인 성공")
            else:
                print("✗ 2단계: 비밀번호 확인 실패")
                return
            
            # 3. 테스트 클라이언트로 로그인 시도
            with app.test_client() as client:
                with app.app_context():
                    from flask_login import login_user
                    from flask import session
                    
                    session.permanent = True
                    login_user(user, remember=False)
                    session.modified = True
                    
                    from flask_login import current_user
                    if current_user.is_authenticated:
                        print(f"✓ 3단계: 로그인 성공 (User ID: {current_user.id})")
                        print("✓ 모든 단계 성공!")
                    else:
                        print("✗ 3단계: 로그인 실패 (인증 상태 불일치)")
                        return
                
    except Exception as e:
        print(f"✗ 로그인 프로세스 시뮬레이션 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def print_browser_instructions():
    """브라우저 쿠키 확인 방법 안내"""
    print("=" * 60)
    print("6. 브라우저 쿠키 확인 방법")
    print("=" * 60)
    print("""
브라우저 개발자 도구에서 세션 쿠키를 확인하세요:

Chrome/Edge:
1. F12 또는 Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows)
2. Application 탭 클릭
3. 왼쪽 사이드바에서 Cookies → [사이트 URL] 선택
4. 다음 쿠키 확인:
   - session: Flask 세션 쿠키 (로그인 정보 포함)
   - remember_token: 'Remember Me' 사용 시

Firefox:
1. F12 또는 Cmd+Option+I (Mac) / Ctrl+Shift+I (Windows)
2. Storage 탭 클릭
3. Cookies → [사이트 URL] 선택
4. session 쿠키 확인

확인 사항:
✓ session 쿠키가 있는가?
✓ 쿠키 값이 비어있지 않은가?
✓ HttpOnly 플래그가 설정되어 있는가?
✓ SameSite 속성이 설정되어 있는가?

로그인 시도 후 쿠키가 생성되지 않는다면:
- 브라우저의 쿠키 차단 설정 확인
- 사설 브라우징 모드 비활성화
- 쿠키가 차단되는 확장 프로그램 확인
""")

def print_server_log_instructions():
    """서버 로그 확인 방법 안내"""
    print("=" * 60)
    print("7. 서버 로그 확인 방법")
    print("=" * 60)
    print("""
로그인 시도 시 다음 로그를 확인하세요:

1. 로컬 실행 시:
   python run.py
   
   터미널에 실시간 로그가 출력됩니다.

2. Docker 사용 시:
   docker-compose logs -f app

확인할 로그 메시지:
✓ "Attempting login for email: ..."
✓ "User found: ..., status: active, has_hash: True"
✓ "Password check for ...: True"
✓ "User ... logged in successfully (ID: ...)"
✓ "Redirecting ... to dashboard"
✓ "Dashboard access by user: ..."

오류 발생 시:
✗ "Error checking password for ...: ..."
✗ "Database error during login for ...: ..."
✗ "Failed to login user ...: ..."
✗ "Failed to redirect after login: ..."

오류 발생 시 전체 스택 트레이스를 확인하세요.
""")

def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("로그인 디버깅 도구")
    print("=" * 60 + "\n")
    
    check_environment()
    check_database()
    check_session_config()
    check_password_verification()
    check_login_process()
    print_browser_instructions()
    print_server_log_instructions()
    
    print("\n" + "=" * 60)
    print("체크 완료!")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()

