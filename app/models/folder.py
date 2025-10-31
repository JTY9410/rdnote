from app import db
from datetime import datetime

class Folder(db.Model):
    __tablename__ = 'folders'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('research_notes.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    order_index = db.Column(db.Integer, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = db.relationship('File', backref='folder', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def file_count(self):
        """Returns the count of non-deleted files in this folder."""
        return self.files.filter_by(is_deleted=False).count()
    
    def __repr__(self):
        return f'<Folder {self.name}>'

