from app import db
from datetime import datetime

class ResearchNote(db.Model):
    __tablename__ = 'research_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    project_code = db.Column(db.String(100), index=True)
    manager_name = db.Column(db.String(100))
    start_date = db.Column(db.Date, index=True)
    end_date = db.Column(db.Date, index=True)
    allow_writer_delete = db.Column(db.Boolean, default=True)
    allow_member_download = db.Column(db.Boolean, default=True)
    approval_stage = db.Column(db.String(20), default='DRAFT', index=True)  # DRAFT, REVIEWED, APPROVED
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = db.relationship('Workspace', back_populates='research_notes')
    members = db.relationship('ResearchNoteMember', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    folders = db.relationship('Folder', backref='note', lazy='dynamic', cascade='all, delete-orphan')
    owner_user = db.relationship('User', foreign_keys=[owner_user_id], backref='owner_research_notes')
    reviewer_user = db.relationship('User', foreign_keys=[reviewer_user_id], backref='reviewer_research_notes')
    
    def __repr__(self):
        return f'<ResearchNote {self.title}>'

class ResearchNoteMember(db.Model):
    __tablename__ = 'research_note_members'
    
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('research_notes.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # OWNER, WRITER, READER, REVIEWER
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('note_id', 'user_id', name='_note_user_uc'),)
    
    # Relationship
    user = db.relationship('User', backref='note_memberships')
    
    def __repr__(self):
        return f'<ResearchNoteMember {self.note_id} - {self.user_id} ({self.role})>'

