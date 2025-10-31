import bcrypt
from app.models.audit_log import AuditLog

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password_hash, password):
    """Check if password matches hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def log_audit(user_id, action_type, workspace_id=None, note_id=None, file_id=None, meta_json=None):
    """Create audit log entry"""
    audit = AuditLog(
        user_id=user_id,
        action_type=action_type,
        workspace_id=workspace_id,
        note_id=note_id,
        file_id=file_id,
        meta_json=meta_json
    )
    from app import db
    db.session.add(audit)
    db.session.commit()
    return audit

