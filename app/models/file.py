from app import db
from datetime import datetime

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('research_notes.id', ondelete='CASCADE'), nullable=False, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id', ondelete='SET NULL'), nullable=True, index=True)
    uploader_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(500), nullable=False, index=True)
    display_name = db.Column(db.String(500), index=True)
    stored_filename = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100))
    size_bytes = db.Column(db.BigInteger)
    created_date = db.Column(db.Date, nullable=False, index=True)  # 실제 실험일
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    timestamp_certified_at = db.Column(db.DateTime, nullable=False)  # 시점인증
    version_number = db.Column(db.Integer, default=1)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    short_desc = db.Column(db.Text)  # 실험 목적/조건 요약
    file_hash = db.Column(db.String(64), index=True)  # SHA256 해시
    
    # Relationships
    tags = db.relationship('FileTag', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    uploader_user = db.relationship('User', backref='uploaded_files')
    
    @property
    def tags_list(self):
        """Returns a list of tag strings for this file."""
        return [tag.tag for tag in self.tags.all()]
    
    def __repr__(self):
        return f'<File {self.original_filename}>'

class FileTag(db.Model):
    __tablename__ = 'file_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), nullable=False, index=True)
    tag = db.Column(db.String(64), nullable=False, index=True)
    
    __table_args__ = (db.UniqueConstraint('file_id', 'tag', name='_file_tag_uc'),)
    
    def __repr__(self):
        return f'<FileTag {self.tag}>'

