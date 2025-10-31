from flask import Blueprint, render_template, g, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.research_note import ResearchNote, ResearchNoteMember
from app.models.file import File
from app.models.download_history import DownloadHistory
from app.models.audit_log import AuditLog
from app.models.system_settings import SystemSettings
from datetime import datetime, timedelta
from sqlalchemy import or_

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.before_request
@login_required
def require_login():
    pass

@dashboard_bp.route('/')
def index():
    # Get user's workspaces
    from app.models.workspace import WorkspaceMember as WSMember
    workspaces = db.session.query(Workspace).join(
        WSMember,
        (Workspace.id == WSMember.workspace_id) &
        (WSMember.user_id == current_user.id)
    ).all()
    
    # Get user's notes  
    from app.models.research_note import ResearchNoteMember as RNMember
    notes = db.session.query(ResearchNote).join(
        RNMember,
        (ResearchNote.id == RNMember.note_id) &
        (RNMember.user_id == current_user.id)
    ).filter(ResearchNote.deleted_at.is_(None)).all()
    
    # Get recent uploads
    recent_uploads = File.query.filter_by(
        uploader_user_id=current_user.id,
        is_deleted=False
    ).order_by(File.uploaded_at.desc()).limit(5).all()
    
    # Get recent downloads (최근 20건 - 요구사항 4.13, 37)
    recent_downloads = DownloadHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(DownloadHistory.created_at.desc()).limit(20).all()
    
    # Get recent audit logs for user's notes
    note_ids = [note.id for note in notes]
    recent_logs = AuditLog.query.filter(
        AuditLog.note_id.in_(note_ids)
    ).order_by(AuditLog.created_at.desc()).limit(10).all()
    
    # Get today's download count
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_downloads = DownloadHistory.query.filter(
        DownloadHistory.user_id == current_user.id,
        DownloadHistory.created_at >= today_start
    ).count()
    
    daily_limit = int(SystemSettings.get('daily_download_limit', '100'))
    
    # Progress per note (created/uploaded/reviewer/approved)
    from app.models.research_note import ResearchNoteMember as RNMember
    note_progress = {}
    for n in notes:
        files_cnt = File.query.filter_by(note_id=n.id, is_deleted=False).count()
        has_files = files_cnt > 0
        has_reviewer = getattr(n, 'reviewer_user_id', None) is not None
        is_approved = getattr(n, 'approval_stage', 'DRAFT') == 'APPROVED'
        note_progress[n.id] = {
            'has_files': has_files,
            'has_reviewer': has_reviewer,
            'is_approved': is_approved
        }

    # Favorites
    from app.models.favorite import Favorite
    fav_note_ids = [f.note_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
    favorites = [n for n in notes if n.id in fav_note_ids]

    # Get warnings
    warnings = []
    
    # Check for unsigned owner/note pairs
    for note in notes:
        member = ResearchNoteMember.query.filter_by(
            note_id=note.id,
            user_id=current_user.id
        ).first()
        if member and member.role == 'OWNER' and not current_user.signature_path:
            warnings.append(f"Missing signature for note: {note.title}")
    
    # Check download limit
    if today_downloads >= daily_limit * 0.8:
        warnings.append("Approaching daily download limit")
    
    return render_template('dashboard/index.html',
                         workspaces=workspaces,
                         notes=notes,
                         favorites=favorites,
                         note_progress=note_progress,
                         recent_uploads=recent_uploads,
                         recent_downloads=recent_downloads,
                         recent_logs=recent_logs,
                         today_downloads=today_downloads,
                         daily_limit=daily_limit,
                         warnings=warnings,
                         datetime=datetime)

@dashboard_bp.route('/upload', methods=['POST'])
def quick_upload():
    """Quick upload endpoint selecting note only; forwards to files endpoint."""
    note_id = request.form.get('note_id')
    if not note_id:
        return jsonify({'error': 'note_id is required'}), 400
    from flask import redirect, url_for
    # Delegate to files upload_to_note
    return redirect(url_for('files.upload_to_note', note_id=int(note_id)), code=307)

