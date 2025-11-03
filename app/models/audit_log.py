from app import db
from datetime import datetime
from sqlalchemy import JSON
import os

# JSONB는 PostgreSQL 전용이므로, SQLite를 지원하기 위해 조건부로 사용
try:
    from sqlalchemy.dialects.postgresql import JSONB
    # PostgreSQL 사용 여부 확인
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
        JSON_TYPE = JSONB
    else:
        JSON_TYPE = JSON
except ImportError:
    JSON_TYPE = JSON

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True)
    note_id = db.Column(db.Integer, db.ForeignKey('research_notes.id', ondelete='CASCADE'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=True)
    action_type = db.Column(db.String(100), nullable=False)
    meta_json = db.Column(JSON_TYPE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action_type} by {self.user_id}>'

