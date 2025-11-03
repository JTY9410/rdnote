"""
데이터베이스 연결 헬퍼 유틸리티
SQLite를 기본값으로 사용하고, PostgreSQL 연결 실패 시 자동으로 SQLite로 폴백
"""
import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, DisconnectionError
import logging

logger = logging.getLogger(__name__)

def get_database_url():
    """
    환경변수에서 데이터베이스 URL을 가져오거나, SQLite 기본값 반환
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL URL인 경우
        if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
            # 연결 테스트
            try:
                engine = create_engine(database_url, pool_pre_ping=True, connect_args={'connect_timeout': 5})
                with engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                logger.info("PostgreSQL connection successful")
                return database_url
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}. Falling back to SQLite.")
                # PostgreSQL 연결 실패 시 SQLite로 폴백
                return get_sqlite_url()
        else:
            return database_url
    
    # 기본값: SQLite
    return get_sqlite_url()

def get_sqlite_url():
    """SQLite 데이터베이스 경로 반환"""
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'wecar_db.sqlite')
    return f'sqlite:///{db_path}'

def create_sqlite_if_not_exists():
    """SQLite 데이터베이스 파일이 없으면 생성"""
    db_url = get_sqlite_url()
    db_path = db_url.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        # SQLite 파일 생성
        conn = sqlite3.connect(db_path)
        conn.close()
        logger.info(f"Created SQLite database at: {db_path}")
    
    return db_path

