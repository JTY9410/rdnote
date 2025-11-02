#!/usr/bin/env python3
"""
실시간 로그인 테스트 스크립트
실제 웹 서버에 요청을 보내서 로그인을 테스트합니다.
"""
import requests
import sys

def test_login(base_url='http://localhost:5501'):
    """실제 서버에 로그인 요청 전송"""
    print(f"Testing login at: {base_url}")
    print("=" * 60)
    
    # 1. 로그인 페이지 접근
    try:
        response = requests.get(f"{base_url}/auth/login", timeout=5)
        print(f"✓ Login page: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.text[:200]}")
            return
    except Exception as e:
        print(f"✗ Cannot reach login page: {e}")
        print(f"  Make sure server is running at {base_url}")
        return
    
    # 2. 로그인 POST 요청
    login_data = {
        'email': 'jty9410@wecar-m.co.kr',
        'password': '#jeong07209'
    }
    
    session = requests.Session()
    try:
        response = session.post(
            f"{base_url}/auth/login",
            data=login_data,
            allow_redirects=False,
            timeout=10
        )
        
        print(f"✓ Login POST: {response.status_code}")
        
        # 쿠키 확인
        cookies = session.cookies
        if 'session' in cookies:
            print(f"✓ Session cookie created: {cookies['session'][:50]}...")
        else:
            print("✗ No session cookie created!")
        
        # 리다이렉트 확인
        if response.status_code == 302:
            print(f"✓ Redirect location: {response.headers.get('Location', 'None')}")
            
            # 리다이렉트 후 페이지 접근
            if response.headers.get('Location'):
                redirect_url = response.headers['Location']
                if redirect_url.startswith('/'):
                    redirect_url = f"{base_url}{redirect_url}"
                
                try:
                    redirect_response = session.get(redirect_url, timeout=5)
                    print(f"✓ Redirect page: {redirect_response.status_code}")
                    
                    if 'dashboard' in redirect_url.lower() or redirect_response.status_code == 200:
                        print("✓ Login successful! Dashboard accessible.")
                    else:
                        print(f"✗ Redirect page issue: {redirect_response.status_code}")
                except Exception as e:
                    print(f"✗ Error accessing redirect page: {e}")
        else:
            print(f"✗ Login failed - Status: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("✗ Login request timeout")
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {base_url}")
        print("  Make sure server is running")
    except Exception as e:
        print(f"✗ Login request error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5501'
    test_login(base_url)

