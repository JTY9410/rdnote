from app import db
from datetime import datetime

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize default system settings"""
        defaults = {
            'allowed_extensions': '.pdf,.jpg,.png,.jpeg,.csv,.xlsx,.zip,.txt,.doc,.docx',
            'max_file_size_mb': '500',
            'daily_download_limit': '100',
            'session_timeout_min': '30',
            'build_tag': f'wecar-rnd:{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}'
        }
        
        for key, value in defaults.items():
            if not cls.query.filter_by(key=key).first():
                setting = cls(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
    
    @classmethod
    def get(cls, key, default=None):
        """Get setting value"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set(cls, key, value):
        """Set setting value"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
        return setting
    
    def __repr__(self):
        return f'<SystemSettings {self.key}={self.value}>'

