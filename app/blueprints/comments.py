from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.comment import Comment
from app.models.mention import Mention
from app.models.file import File
from app.utils.permissions import can_write_note
from app.utils.auth import log_audit


comments_bp = Blueprint('comments', __name__)


@comments_bp.post('/comments')
@login_required
def add_comment():
    d = request.json or {}
    if not d.get('file_id') or not d.get('body'):
        return {'error': 'invalid payload'}, 400
    # Load file and check permission (작성자/소유자만)
    file_obj = File.query.get(d['file_id'])
    if not file_obj:
        return {'error': 'file not found'}, 404
    if not can_write_note(current_user.id, file_obj.note_id):
        return {'error': 'Permission denied'}, 403
    # Validate body length ≤ 2000
    body = (d.get('body') or '').strip()
    if len(body) == 0:
        return {'error': '본문은 필수입니다.'}, 400
    if len(body) > 2000:
        return {'error': '코멘트는 최대 2000자까지 가능합니다.'}, 422
    # Validate page range
    page_from = int(d.get('page_from', 1) or 1)
    page_to = int(d.get('page_to', page_from) or page_from)
    if page_from < 1 or page_to < page_from:
        return {'error': '페이지 범위가 올바르지 않습니다.'}, 400
    c = Comment(
        file_id=d['file_id'],
        page_from=page_from,
        page_to=page_to,
        author_id=current_user.id,
        body=body
    )
    db.session.add(c)
    db.session.flush()
    # Mentions (optional list of user ids)
    mentioned = []
    for uid in d.get('mentions', []):
        try:
            uid_int = int(uid)
        except (TypeError, ValueError):
            continue
        db.session.add(Mention(comment_id=c.id, user_id=uid_int))
        mentioned.append(uid_int)
    db.session.commit()
    if mentioned:
        log_audit(current_user.id, 'NOTIFY_MENTION', note_id=file_obj.note_id,
                  file_id=file_obj.id, meta_json={'mentions': mentioned, 'comment_id': c.id})
    return {'ok': True, 'id': c.id}


@comments_bp.patch('/comments/<int:cid>/pin')
@login_required
def pin_comment(cid):
    c = Comment.query.get_or_404(cid)
    # Check permission: only writers/owners of the note may pin
    file_obj = File.query.get(c.file_id)
    if not file_obj or not can_write_note(current_user.id, file_obj.note_id):
        return {'error': 'Permission denied'}, 403
    c.pinned = True
    db.session.commit()
    return {'ok': True}


