from app import db
from datetime import datetime


class Mention(db.Model):
    __tablename__ = 'mentions'

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    notified_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


