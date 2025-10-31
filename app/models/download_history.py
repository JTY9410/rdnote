from app import db
from datetime import datetime

class DownloadHistory(db.Model):
    __tablename__ = 'download_history'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('research_notes.id', ondelete='CASCADE'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    download_type = db.Column(db.String(20), nullable=False)  # RAW_FILE, PDF_EXPORT
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='download_histories')
    file = db.relationship('File', backref='download_histories')
    
    def __repr__(self):
        return f'<DownloadHistory {self.user_id} - {self.download_type}>'

