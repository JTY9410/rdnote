from app import db
from datetime import datetime

class Workspace(db.Model):
    __tablename__ = 'workspaces'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('WorkspaceMember', backref='workspace_rel', lazy='dynamic', cascade='all, delete-orphan')
    research_notes = db.relationship('ResearchNote', back_populates='workspace', lazy='dynamic', cascade='all, delete-orphan')
    owner = db.relationship('User', foreign_keys=[owner_user_id])
    
    @property
    def notes_count(self):
        """Returns the count of non-deleted notes in this workspace."""
        return self.research_notes.filter_by(deleted_at=None).count()
    
    def __repr__(self):
        return f'<Workspace {self.name}>'

class WorkspaceMember(db.Model):
    __tablename__ = 'workspace_members'
    
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), default='MEMBER', nullable=False)  # OWNER, MEMBER
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('workspace_id', 'user_id', name='_workspace_user_uc'),)
    
    # Relationship
    user = db.relationship('User', backref='workspace_memberships')
    
    def __repr__(self):
        return f'<WorkspaceMember {self.workspace_id} - {self.user_id}>'

