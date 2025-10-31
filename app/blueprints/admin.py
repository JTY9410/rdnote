from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.research_note import ResearchNote, ResearchNoteMember
from app.models.file import File
from app.models.download_history import DownloadHistory
from app.models.audit_log import AuditLog
from app.models.system_settings import SystemSettings
from app.utils.auth import hash_password, log_audit
from app.utils.permissions import is_admin
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc, distinct
import os

admin_bp = Blueprint('admin', __name__)

def require_admin(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.before_request
@login_required
def require_login():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('dashboard.index'))

@admin_bp.route('/')
def dashboard():
    # Get statistics
    total_users = User.query.count()
    pending_users = User.query.filter_by(status='pending').count()
    suspended_users = User.query.filter_by(status='suspended').count()
    
    total_workspaces = Workspace.query.count()
    
    total_notes = ResearchNote.query.filter(ResearchNote.deleted_at.is_(None)).count()
    
    # Today's uploads
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_uploads = File.query.filter(File.uploaded_at >= today_start, File.is_deleted == False).count()
    
    # Today's downloads
    today_downloads = DownloadHistory.query.filter(DownloadHistory.created_at >= today_start).count()
    
    # Security risks
    # Top 5 downloaders in last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    top_downloaders = db.session.query(
        User.id, User.name, User.email, func.count(DownloadHistory.id).label('count')
    ).join(DownloadHistory).filter(
        DownloadHistory.created_at >= last_24h
    ).group_by(User.id).order_by(desc('count')).limit(5).all()
    
    # Suspended login attempts
    suspended_attempts = AuditLog.query.filter(
        AuditLog.action_type == 'USER_LOGIN_DENIED',
        AuditLog.created_at >= last_24h
    ).order_by(AuditLog.created_at.desc()).limit(20).all()
    
    # Operational risks - notes with no uploads in 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stale_notes = db.session.query(ResearchNote).outerjoin(File).filter(
        ResearchNote.deleted_at.is_(None),
        or_(File.id.is_(None), File.uploaded_at < thirty_days_ago)
    ).distinct().all()
    
    # 사후 일괄 등록 의심 탐지
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    fourteen_days_ago_date = (datetime.utcnow() - timedelta(days=14)).date()
    
    bulk_upload_suspicious = db.session.query(
        ResearchNote.id, ResearchNote.title, ResearchNote.owner_user_id,
        func.count(File.id).label('old_files_count'),
        func.max(File.uploaded_at).label('last_upload')
    ).join(File).filter(
        File.uploaded_at >= twenty_four_hours_ago,
        File.created_date <= fourteen_days_ago_date,
        File.is_deleted == False
    ).group_by(ResearchNote.id, ResearchNote.title, ResearchNote.owner_user_id).having(
        func.count(File.id) >= 10
    ).all()
    
    # Quality risks - notes without reviewer or without reviewer approval
    notes_without_reviewer = ResearchNote.query.filter(
        ResearchNote.deleted_at.is_(None),
        or_(ResearchNote.reviewer_user_id.is_(None),
            ~ResearchNote.reviewer_user_id.in_(
                db.session.query(ResearchNoteMember.user_id).filter_by(
                    note_id=ResearchNote.id, role='REVIEWER'
                )
            )
        )
    ).all()
    
    # Build tag
    build_tag = SystemSettings.get('build_tag', 'N/A')
    
    return render_template('admin/dashboard.html',
                         bulk_upload_suspicious=bulk_upload_suspicious,
                         total_users=total_users,
                         pending_users=pending_users,
                         suspended_users=suspended_users,
                         total_workspaces=total_workspaces,
                         total_notes=total_notes,
                         today_uploads=today_uploads,
                         today_downloads=today_downloads,
                         top_downloaders=top_downloaders,
                         suspended_attempts=suspended_attempts,
                         stale_notes=stale_notes,
                         notes_without_reviewer=notes_without_reviewer,
                         build_tag=build_tag)

@admin_bp.route('/users')
def users():
    users_list = User.query.order_by(User.created_at.desc()).all()
    # compute role label: 관리자 / 연구책임자(OWNER) / 연구원
    users_with_roles = []
    for u in users_list:
        role_label = '연구원'
        if u.is_admin:
            role_label = '관리자'
        else:
            owner_count = ResearchNote.query.filter_by(owner_user_id=u.id).count()
            if owner_count > 0:
                role_label = '연구책임자'
        users_with_roles.append({'user': u, 'role_label': role_label})
    return render_template('admin/users.html', users_with_roles=users_with_roles)

@admin_bp.route('/users/new', methods=['POST'])
def create_user():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    org_name = request.form.get('org_name')
    department = request.form.get('department')
    is_admin_flag = request.form.get('is_admin') == 'on'

    if not name or not email or not password or not password_confirm:
        flash('필수 항목을 모두 입력하세요.', 'error')
        return redirect(url_for('admin.users'))

    if password != password_confirm:
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return redirect(url_for('admin.users'))

    if User.query.filter_by(email=email).first():
        flash('이미 등록된 이메일입니다.', 'error')
        return redirect(url_for('admin.users'))

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        org_name=org_name or None,
        department=department or None,
        status='active',
        is_admin=is_admin_flag,
        created_at=datetime.utcnow()
    )
    db.session.add(user)
    db.session.commit()

    log_audit(current_user.id, 'ADMIN_CREATE_USER', meta_json={'user_id': user.id, 'email': email, 'is_admin': is_admin_flag})
    flash('사용자가 추가되었습니다.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/status', methods=['POST'])
def update_user_status(user_id):
    user = User.query.get_or_404(user_id)
    new_status = request.form.get('status')
    
    old_status = user.status
    user.status = new_status
    db.session.commit()
    
    log_audit(current_user.id, 'ADMIN_USER_STATUS_CHANGE', meta_json={
        'user_id': user_id, 'old_status': old_status, 'new_status': new_status
    })
    
    flash('User status updated.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/admin', methods=['POST'])
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    log_audit(current_user.id, 'ADMIN_TOGGLE_ADMIN', meta_json={
        'target_user_id': user_id, 'is_admin': user.is_admin
    })
    
    flash(f'Admin status {"granted" if user.is_admin else "revoked"}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/update', methods=['POST'])
def update_user_details():
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)
    name = request.form.get('name')
    email = request.form.get('email')
    org_name = request.form.get('org_name')
    department = request.form.get('department')
    is_admin_flag = request.form.get('is_admin') == 'on'

    if not name or not email:
        flash('이름과 이메일은 필수입니다.', 'error')
        return redirect(url_for('admin.users'))

    # 이메일 중복 검사 (자기 자신 제외)
    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        flash('이미 사용 중인 이메일입니다.', 'error')
        return redirect(url_for('admin.users'))

    user.name = name
    user.email = email
    user.org_name = org_name or None
    user.department = department or None
    user.is_admin = is_admin_flag
    db.session.commit()

    log_audit(current_user.id, 'ADMIN_UPDATE_USER', meta_json={'user_id': user.id, 'email': user.email, 'is_admin': user.is_admin})
    flash('사용자 정보가 수정되었습니다.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/workspaces')
def workspaces_list():
    workspaces_list = Workspace.query.order_by(Workspace.created_at.desc()).all()
    return render_template('admin/workspaces.html', workspaces=workspaces_list)

@admin_bp.route('/workspaces/<int:workspace_id>/member-role', methods=['POST'])
def workspace_member_role(workspace_id):
    """Admin update workspace member role"""
    member_id = request.form.get('member_id')
    new_role = request.form.get('role')
    
    member = WorkspaceMember.query.get_or_404(member_id)
    
    if member.workspace_id != workspace_id:
        flash('Invalid request.', 'error')
        return redirect(url_for('admin.workspaces_list'))
    
    old_role = member.role
    member.role = new_role
    db.session.commit()
    
    log_audit(current_user.id, 'ADMIN_WORKSPACE_MEMBER_CHANGE', workspace_id=workspace_id,
              meta_json={'member_id': member_id, 'old_role': old_role, 'new_role': new_role})
    
    flash('Member role updated.', 'success')
    return redirect(url_for('admin.workspaces_list'))

@admin_bp.route('/notes/<int:note_id>/force-settings', methods=['POST'])
def force_note_settings(note_id):
    """Admin force update note settings"""
    note = ResearchNote.query.get_or_404(note_id)
    
    allow_writer_delete = request.form.get('allow_writer_delete') == 'on'
    allow_member_download = request.form.get('allow_member_download') == 'on'
    
    note.allow_writer_delete = allow_writer_delete
    note.allow_member_download = allow_member_download
    note.updated_at = datetime.utcnow()
    db.session.commit()
    
    log_audit(current_user.id, 'ADMIN_NOTE_SETTINGS_FORCE', note_id=note_id,
              meta_json={'allow_writer_delete': allow_writer_delete, 
                        'allow_member_download': allow_member_download})
    
    flash('Settings force updated.', 'success')
    return redirect(url_for('admin.notes_list'))

@admin_bp.route('/notes/<int:note_id>/force-transfer-owner', methods=['POST'])
def force_transfer_owner(note_id):
    """Admin force transfer note ownership"""
    note = ResearchNote.query.get_or_404(note_id)
    new_owner_id = request.form.get('new_owner_id')
    
    if not new_owner_id:
        flash('New owner ID is required.', 'error')
        return redirect(url_for('admin.notes_list'))
    
    old_owner_id = note.owner_user_id
    old_owner = User.query.get(old_owner_id)
    new_owner = User.query.get(int(new_owner_id))
    
    note.owner_user_id = int(new_owner_id)
    
    # Update member role
    old_owner_member = ResearchNoteMember.query.filter_by(note_id=note_id, user_id=old_owner_id).first()
    new_owner_member = ResearchNoteMember.query.filter_by(note_id=note_id, user_id=int(new_owner_id)).first()
    
    if old_owner_member:
        old_owner_member.role = 'READER'
    
    if new_owner_member:
        new_owner_member.role = 'OWNER'
    else:
        new_owner_member = ResearchNoteMember(
            note_id=note_id,
            user_id=int(new_owner_id),
            role='OWNER'
        )
        db.session.add(new_owner_member)
    
    db.session.commit()
    
    log_audit(current_user.id, 'ADMIN_NOTE_FORCE_OWNER_TRANSFER', note_id=note_id,
              meta_json={'old_owner': old_owner.email if old_owner else 'N/A',
                        'new_owner': new_owner.email if new_owner else 'N/A'})
    
    flash('Ownership force transferred successfully.', 'success')
    return redirect(url_for('admin.notes_list'))

@admin_bp.route('/notes')
def notes_list():
    from app.models.folder import Folder
    
    # Get notes with file counts
    notes_query = ResearchNote.query.filter(ResearchNote.deleted_at.is_(None)).order_by(ResearchNote.created_at.desc()).all()
    
    # Enrich notes with additional data
    enriched_notes = []
    for note in notes_query:
        # Count all files in this note
        file_count = File.query.join(Folder).filter(
            Folder.note_id == note.id,
            File.is_deleted == False
        ).count()
        
        # Get latest file upload date
        latest_file = File.query.join(Folder).filter(
            Folder.note_id == note.id,
            File.is_deleted == False
        ).order_by(File.uploaded_at.desc()).first()
        
        latest_upload = latest_file.uploaded_at if latest_file else None
        
        # Get member count
        member_count = note.members.count()
        
        enriched_notes.append({
            'note': note,
            'file_count': file_count,
            'latest_upload': latest_upload,
            'member_count': member_count
        })
    
    return render_template('admin/notes.html', notes_data=enriched_notes)

def apply_audit_filters(query):
    """Apply filters to audit query"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    action_type = request.args.get('action_type')
    user_email = request.args.get('user_email')
    note_id = request.args.get('note_id')
    
    if from_date:
        query = query.filter(AuditLog.created_at >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(AuditLog.created_at <= datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1))
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if user_email:
        user = User.query.filter_by(email=user_email).first()
        if user:
            query = query.filter(AuditLog.user_id == user.id)
    if note_id:
        query = query.filter(AuditLog.note_id == note_id)
    
    return query

@admin_bp.route('/audit')
def audit():
    # Get filters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    query = AuditLog.query
    query = apply_audit_filters(query)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    
    # Log admin access
    log_audit(current_user.id, 'ADMIN_VIEW_AUDIT', meta_json={
        'from_date': from_date, 'to_date': to_date
    })
    
    return render_template('admin/audit.html', logs=logs)

@admin_bp.route('/audit/export/csv')
def audit_csv():
    """Export audit logs to CSV"""
    from flask import Response
    
    query = AuditLog.query
    query = apply_audit_filters(query)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()
    
    # Generate CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['시간', '사용자', '이메일', '액션', '연구과제ID', '워크스페이스ID', '파일ID', '상세'])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.name if log.user else '-',
            log.user.email if log.user else '-',
            log.action_type,
            log.note_id or '-',
            log.workspace_id or '-',
            log.file_id or '-',
            str(log.meta_json) if log.meta_json else '-'
        ])
    
    # Log admin export
    log_audit(current_user.id, 'ADMIN_EXPORT_AUDIT_CSV', meta_json={'count': len(logs)})
    
    # Create response
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=audit_logs_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )
    
    return response

@admin_bp.route('/downloads')
def downloads():
    # Get filters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    user_email = request.args.get('user_email')
    
    query = DownloadHistory.query
    
    if from_date:
        query = query.filter(DownloadHistory.created_at >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(DownloadHistory.created_at <= datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1))
    if user_email:
        user = User.query.filter_by(email=user_email).first()
        if user:
            query = query.filter(DownloadHistory.user_id == user.id)
    
    downloads_list = query.order_by(DownloadHistory.created_at.desc()).limit(200).all()
    
    # Detect bulk downloads - users with >10 downloads today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bulk_downloaders = db.session.query(
        User.id, User.name, User.email, func.count(DownloadHistory.id).label('count')
    ).join(DownloadHistory).filter(
        DownloadHistory.created_at >= today_start
    ).group_by(User.id, User.name, User.email).having(
        func.count(DownloadHistory.id) > 10
    ).order_by(desc('count')).all()
    
    # Log admin access
    log_audit(current_user.id, 'ADMIN_VIEW_DOWNLOADS')
    
    return render_template('admin/downloads.html', 
                         downloads=downloads_list,
                         bulk_downloaders=bulk_downloaders)

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Update settings
        allowed_exts = request.form.get('allowed_extensions')
        max_size = request.form.get('max_file_size_mb')
        daily_limit = request.form.get('daily_download_limit')
        session_timeout = request.form.get('session_timeout_min')
        
        if allowed_exts:
            SystemSettings.set('allowed_extensions', allowed_exts)
        if max_size:
            SystemSettings.set('max_file_size_mb', max_size)
        if daily_limit:
            SystemSettings.set('daily_download_limit', daily_limit)
        if session_timeout:
            SystemSettings.set('session_timeout_min', session_timeout)
        
        log_audit(current_user.id, 'ADMIN_UPDATE_SETTINGS')
        flash('Settings updated.', 'success')
        return redirect(url_for('admin.settings'))
    
    # Get current settings
    allowed_exts = SystemSettings.get('allowed_extensions')
    max_size = SystemSettings.get('max_file_size_mb')
    daily_limit = SystemSettings.get('daily_download_limit')
    session_timeout = SystemSettings.get('session_timeout_min')
    build_tag = SystemSettings.get('build_tag', 'v1.0.0')
    
    # Get DB migration status
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from alembic import command
        
        alembic_cfg = Config('alembic.ini')
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current version
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        
        # Get head version
        heads = script.get_revisions('heads')
        head_rev = str(heads[0].revision) if heads else 'unknown'
        
        db_status = {
            'current_rev': current_rev,
            'head_rev': head_rev,
            'is_uptodate': current_rev == head_rev
        }
    except Exception as e:
        db_status = {
            'current_rev': 'unknown',
            'head_rev': 'unknown',
            'is_uptodate': True,
            'error': str(e)
        }
    
    # Get system statistics
    total_files = File.query.filter(File.is_deleted == False).count()
    total_size = db.session.query(func.sum(File.file_size)).filter(File.is_deleted == False).scalar() or 0
    total_size_mb = round(total_size / (1024 * 1024), 2) if total_size else 0
    
    return render_template('admin/settings.html',
                         allowed_exts=allowed_exts,
                         max_size=max_size,
                         daily_limit=daily_limit,
                         session_timeout=session_timeout,
                         build_tag=build_tag,
                         db_status=db_status,
                         total_files=total_files,
                         total_size_mb=total_size_mb)

@admin_bp.route('/jobs/nightly-sync', methods=['POST'])
@login_required
def nightly_sync():
    if not is_admin(current_user):
        flash('Admin only.', 'error')
        return redirect(url_for('admin.index'))
    # stub: would enqueue nightly sync here
    log_audit(current_user.id, 'ADMIN_NIGHTLY_SYNC_TRIGGER', meta_json={'at': datetime.utcnow().isoformat()})
    flash('Nightly sync triggered.', 'success')
    return redirect(url_for('admin.index'))

