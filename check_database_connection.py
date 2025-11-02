#!/usr/bin/env python3
"""
데이터베이스 연결 상태 확인 스크립트
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DisconnectionError

def check_database():
    """데이터베이스 연결 상태 확인"""
    print("=" * 60)
    print("데이터베이스 연결 상태 확인")
    print("=" * 60)
    print()
    
    # 1. DATABASE_URL 확인
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = 'postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db'
        print("⚠️  DATABASE_URL 환경 변수가 설정되지 않았습니다.")
        print(f"   기본값 사용: {database_url.split('@')[0]}@...")
    else:
        # 비밀번호 마스킹
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split('://')
                if len(user_pass) == 2:
                    protocol = user_pass[0]
                    user_part = user_pass[1]
                    if ':' in user_part:
                        user = user_part.split(':')[0]
                        print(f"✓ DATABASE_URL: 설정됨 ({protocol}://{user}:***@{parts[1]})")
                    else:
                        print(f"✓ DATABASE_URL: 설정됨")
                else:
                    print(f"✓ DATABASE_URL: 설정됨")
            else:
                print(f"✓ DATABASE_URL: 설정됨")
        else:
            print(f"✓ DATABASE_URL: 설정됨")
    print()
    
    # 2. 연결 시도
    print("📡 데이터베이스 연결 시도 중...")
    try:
        # 연결 풀 설정
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # 연결 전 상태 확인
            pool_recycle=300,   # 5분마다 연결 재사용
            pool_size=1,
            max_overflow=0,
            connect_args={
                'connect_timeout': 10,  # 10초 타임아웃
            }
        )
        
        # 연결 테스트
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ 데이터베이스 연결: 성공")
            else:
                print("✗ 데이터베이스 연결: 응답 이상")
                return False
        
        # 데이터베이스 정보 조회
        with engine.connect() as conn:
            # PostgreSQL 버전 확인
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"  PostgreSQL 버전: {version.split(',')[0]}")
            
            # 현재 데이터베이스 이름
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"  현재 데이터베이스: {db_name}")
            
            # 연결 수 확인
            result = conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"))
            connections = result.fetchone()[0]
            print(f"  현재 연결 수: {connections}")
        
        print()
        print("✓ 모든 확인 완료!")
        return True
        
    except OperationalError as e:
        print(f"✗ 데이터베이스 연결 실패 (OperationalError)")
        print(f"  오류: {str(e)}")
        print()
        print("가능한 원인:")
        print("  1. 데이터베이스 서버가 실행 중이지 않음")
        print("  2. DATABASE_URL의 호스트/포트가 잘못됨")
        print("  3. 방화벽이 연결을 차단함")
        print("  4. 데이터베이스가 존재하지 않음")
        return False
        
    except DisconnectionError as e:
        print(f"✗ 데이터베이스 연결 끊김 (DisconnectionError)")
        print(f"  오류: {str(e)}")
        print()
        print("가능한 원인:")
        print("  1. 데이터베이스 서버가 일시적으로 중단됨")
        print("  2. 네트워크 연결이 불안정함")
        print("  3. 연결 타임아웃")
        return False
        
    except Exception as e:
        print(f"✗ 데이터베이스 연결 중 예상치 못한 오류")
        print(f"  오류 유형: {type(e).__name__}")
        print(f"  오류 메시지: {str(e)}")
        import traceback
        print(f"  상세:\n{traceback.format_exc()}")
        return False

def check_tables():
    """데이터베이스 테이블 확인"""
    print("=" * 60)
    print("테이블 존재 확인")
    print("=" * 60)
    print()
    
    database_url = os.environ.get('DATABASE_URL', 'postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db')
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✓ 발견된 테이블: {len(tables)}개")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠️  테이블이 없습니다. 마이그레이션을 실행하세요:")
                print("   flask db upgrade")
            print()
            
    except Exception as e:
        print(f"✗ 테이블 확인 실패: {e}")
        print()

if __name__ == '__main__':
    success = check_database()
    if success:
        check_tables()
    sys.exit(0 if success else 1)

