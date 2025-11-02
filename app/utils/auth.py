import bcrypt
from app.models.audit_log import AuditLog

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password_hash, password):
    """Check if password matches hash"""
    try:
        if not password_hash or not password:
            return False
        if not isinstance(password_hash, str):
            return False
        # Check if it's a valid bcrypt hash format
        if not password_hash.startswith('$2'):
            return False
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in check_password: {e}")
        return False

def log_audit(user_id, action_type, workspace_id=None, note_id=None, file_id=None, meta_json=None):
    """Create audit log entry"""
    try:
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
    except Exception as e:
        # Log error but don't fail the request if audit logging fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return None

