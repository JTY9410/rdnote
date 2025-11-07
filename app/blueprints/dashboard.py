from flask import Blueprint, render_template, g, request, jsonify, current_app
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
    """Ensure user is logged in before accessing dashboard"""
    # login_required decorator handles authentication check
    # Additional verification can be done here if needed
    pass

@dashboard_bp.route('/')
def index():
    from flask_login import current_user
    from flask import current_app
    try:
        # Safe check for authenticated user
        user_info = 'anonymous'
        try:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                user_info = getattr(current_user, 'email', f'user_id_{getattr(current_user, "id", "unknown")}')
        except Exception:
            pass
        
        current_app.logger.info(f"Dashboard access by user: {user_info}")
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
        note_ids = [note.id for note in notes] if notes else []
        recent_logs = []
        if note_ids:
            recent_logs = AuditLog.query.filter(
                AuditLog.note_id.in_(note_ids)
            ).order_by(AuditLog.created_at.desc()).limit(10).all()
        
        # Get today's download count
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_downloads = DownloadHistory.query.filter(
            DownloadHistory.user_id == current_user.id,
            DownloadHistory.created_at >= today_start
        ).count()
        
        try:
            daily_limit = int(SystemSettings.get('daily_download_limit', '100'))
        except Exception:
            daily_limit = 100
        
        # Progress per note (created/uploaded/reviewer/approved)
        from app.models.research_note import ResearchNoteMember as RNMember
        note_progress = {}
        for n in notes:
            try:
                files_cnt = File.query.filter_by(note_id=n.id, is_deleted=False).count()
                has_files = files_cnt > 0
                has_reviewer = getattr(n, 'reviewer_user_id', None) is not None
                is_approved = getattr(n, 'approval_stage', 'DRAFT') == 'APPROVED'
                note_progress[n.id] = {
                    'has_files': has_files,
                    'has_reviewer': has_reviewer,
                    'is_approved': is_approved
                }
            except Exception:
                note_progress[n.id] = {
                    'has_files': False,
                    'has_reviewer': False,
                    'is_approved': False
                }

        # Favorites
        favorites = []
        try:
            from app.models.favorite import Favorite
            fav_note_ids = [f.note_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]
            favorites = [n for n in notes if n.id in fav_note_ids]
        except Exception:
            pass

        # Get warnings and alerts
        warnings = []
        alerts = []
        
        # Check for unsigned owner/note pairs
        try:
            for note in notes:
                member = ResearchNoteMember.query.filter_by(
                    note_id=note.id,
                    user_id=current_user.id
                ).first()
                if member and member.role == 'OWNER' and not current_user.signature_path:
                    warnings.append(f"전자서명 미등록: {note.title} - PDF 책임자 서명란 비어 있음")
        except Exception:
            pass
        
        # Check approval stages
        try:
            owner_notes_not_approved = 0
            reviewer_notes_pending = 0
            writer_notes_not_reviewed = 0
            
            for note in notes:
                member = ResearchNoteMember.query.filter_by(
                    note_id=note.id,
                    user_id=current_user.id
                ).first()
                if member:
                    approval_stage = getattr(note, 'approval_stage', None) or 'DRAFT'
                    if member.role == 'OWNER' and approval_stage != 'APPROVED':
                        owner_notes_not_approved += 1
                    elif member.role == 'REVIEWER' and approval_stage == 'DRAFT':
                        reviewer_notes_pending += 1
                    elif member.role == 'WRITER' and approval_stage not in ['REVIEWED', 'APPROVED']:
                        writer_notes_not_reviewed += 1
            
            if owner_notes_not_approved > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f"내가 OWNER인 과제 중 APPROVED가 아닌 과제: {owner_notes_not_approved}개"
                })
            if reviewer_notes_pending > 0:
                alerts.append({
                    'type': 'info',
                    'message': f"내가 REVIEWER인 과제 중 REVIEW 요청 대기: {reviewer_notes_pending}개"
                })
            if writer_notes_not_reviewed > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f"내가 WRITER인 과제 중 아직 REVIEWED 단계까지 안 간 과제: {writer_notes_not_reviewed}개 (검토 요청 필요)"
                })
        except Exception:
            pass
        
        # Check download limit
        try:
            download_percentage = (today_downloads / daily_limit * 100) if daily_limit > 0 else 0
            if download_percentage >= 80:
                alerts.append({
                    'type': 'danger' if download_percentage >= 100 else 'warning',
                    'message': f"오늘 {today_downloads}회 다운로드 / 한도 {daily_limit}회 / 초과 시 차단 및 감사 대상"
                })
        except Exception:
            pass
        
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
                             alerts=alerts,
                             datetime=datetime)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error in dashboard.index: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        # Return minimal dashboard on error
        return render_template('dashboard/index.html',
                             workspaces=[],
                             notes=[],
                             favorites=[],
                             note_progress={},
                             recent_uploads=[],
                             recent_downloads=[],
                             recent_logs=[],
                             today_downloads=0,
                             daily_limit=100,
                             warnings=['An error occurred loading dashboard data.'],
                             datetime=datetime)

@dashboard_bp.route('/upload', methods=['POST'])
@login_required
def quick_upload():
    """Quick upload endpoint - directly handles file upload."""
    from flask import flash, redirect, url_for
    from app.models.folder import Folder
    from app.models.file import File, FileTag
    from app.utils.permissions import can_write_note
    from app.utils.auth import log_audit
    from app.models.system_settings import SystemSettings
    import os
    import uuid
    import hashlib
    from werkzeug.utils import secure_filename
    
    try:
        note_id = request.form.get('note_id')
        if not note_id:
            flash('연구노트를 선택해주세요.', 'error')
            return redirect(url_for('dashboard.index'))
        
        note_id = int(note_id)
        note = ResearchNote.query.get_or_404(note_id)
        
        # Check permission
        if not can_write_note(current_user.id, note_id):
            flash('파일 업로드 권한이 없습니다.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Get folder (from request or create default)
        folder_id_param = request.form.get('folder_id')
        folder = None
        
        if folder_id_param:
            try:
                folder_id_int = int(folder_id_param)
                folder = Folder.query.filter_by(id=folder_id_int, note_id=note_id, deleted_at=None).first()
                if not folder:
                    flash('선택한 폴더를 찾을 수 없습니다.', 'error')
                    return redirect(url_for('dashboard.index'))
                folder_id = folder.id
            except (ValueError, TypeError):
                folder = None
        
        if not folder:
            # Ensure default folder exists
            default_name = '기본'
            folder = Folder.query.filter_by(note_id=note_id, name=default_name, deleted_at=None).first()
            if not folder:
                folder = Folder(note_id=note_id, name=default_name)
                db.session.add(folder)
                db.session.commit()
            folder_id = folder.id
        
        # Get files from request
        files = request.files.getlist('files[]')
        if not files or all(f.filename == '' for f in files):
            flash('파일을 선택해주세요.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Get form data
        created_date = request.form.get('created_date')
        tags = request.form.get('tags', '')
        short_desc = request.form.get('short_desc', '')
        
        # Check settings
        allowed_exts = SystemSettings.get('allowed_extensions', '.pdf,.jpg,.png,.jpeg,.csv,.xlsx,.zip').split(',')
        max_size = int(SystemSettings.get('max_file_size_mb', '500')) * 1024 * 1024
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        
        uploaded_count = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            # Check extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_exts:
                flash(f'허용되지 않는 파일 형식입니다: {ext}', 'error')
                continue
            
            # Check file size
            file.seek(0, os.SEEK_END)
            size_tmp = file.tell()
            file.seek(0)
            if size_tmp > max_size:
                flash(f'파일 크기가 제한({max_size//1024//1024}MB)를 초과했습니다.', 'error')
                continue
            
            # Save file
            stored_filename = f"{uuid.uuid4()}{ext}"
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            files_dir = os.path.join(upload_folder, 'files')
            os.makedirs(files_dir, exist_ok=True)
            filepath = os.path.join(files_dir, stored_filename)
            file.save(filepath)
            
            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            file_hash = sha256_hash.hexdigest()
            
            # Get file size
            size = os.path.getsize(filepath)
            
            # Set timestamp_certified_at
            sealed_at = datetime.utcnow()
            
            # Parse created_date
            if created_date:
                try:
                    written_date = datetime.strptime(created_date, '%Y-%m-%d').date()
                except ValueError:
                    written_date = datetime.utcnow().date()
            else:
                written_date = datetime.utcnow().date()
            
            # Validate date
            if written_date > sealed_at.date():
                flash('작성일자는 시점인증일보다 미래일 수 없습니다.', 'error')
                os.remove(filepath)
                continue
            
            # Create file record
            file_record = File(
                note_id=note_id,
                folder_id=folder_id,
                uploader_user_id=current_user.id,
                original_filename=file.filename,
                display_name=file.filename,
                stored_filename=stored_filename,
                mime_type=file.content_type,
                size_bytes=size,
                created_date=written_date,
                uploaded_at=datetime.utcnow(),
                timestamp_certified_at=sealed_at,
                version_number=1,
                short_desc=short_desc,
                file_hash=file_hash
            )
            db.session.add(file_record)
            db.session.flush()
            
            # Add tags
            for t in tag_list:
                file_tag = FileTag(file_id=file_record.id, tag=t)
                db.session.add(file_tag)
            
            # Audit log
            log_audit(current_user.id, 'FILE_UPLOAD', note_id=note_id, file_id=file_record.id,
                      meta_json={'created_date': str(written_date), 'short_desc': short_desc, 'file_hash': file_hash})
            
            uploaded_count += 1
        
        db.session.commit()
        
        if uploaded_count > 0:
            flash(f'{uploaded_count}개 파일이 성공적으로 업로드되었습니다.', 'success')
        else:
            flash('업로드된 파일이 없습니다.', 'warning')
        
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f"Error in quick_upload: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash(f'파일 업로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/files-status')
@login_required
def files_status():
    """연구파일 현황 페이지"""
    from app.models.research_note import ResearchNoteMember as RNMember
    
    # Get user's notes
    notes = db.session.query(ResearchNote).join(
        RNMember,
        (ResearchNote.id == RNMember.note_id) &
        (RNMember.user_id == current_user.id)
    ).filter(ResearchNote.deleted_at.is_(None)).all()
    
    # Get all files from user's notes
    note_ids = [note.id for note in notes] if notes else []
    all_files = []
    if note_ids:
        all_files = File.query.filter(
            File.note_id.in_(note_ids),
            File.is_deleted == False
        ).order_by(File.uploaded_at.desc()).all()
    
    # Group by note
    files_by_note = {}
    for file in all_files:
        if file.note_id not in files_by_note:
            files_by_note[file.note_id] = []
        files_by_note[file.note_id].append(file)
    
    return render_template('dashboard/files_status.html',
                         notes=notes,
                         files_by_note=files_by_note,
                         all_files=all_files,
                         datetime=datetime)

@dashboard_bp.route('/notes-status')
@login_required
def notes_status():
    """연구노트 현황 페이지"""
    from app.models.research_note import ResearchNoteMember as RNMember
    from app.models.folder import Folder
    
    # Get user's notes
    notes = db.session.query(ResearchNote).join(
        RNMember,
        (ResearchNote.id == RNMember.note_id) &
        (RNMember.user_id == current_user.id)
    ).filter(ResearchNote.deleted_at.is_(None)).all()
    
    # Get statistics for each note
    notes_stats = []
    for note in notes:
        files_count = File.query.filter_by(note_id=note.id, is_deleted=False).count()
        folders_count = Folder.query.filter_by(note_id=note.id, deleted_at=None).count()
        members_count = ResearchNoteMember.query.filter_by(note_id=note.id).count()
        
        # Get latest file upload date
        latest_file = File.query.filter_by(note_id=note.id, is_deleted=False).order_by(File.uploaded_at.desc()).first()
        latest_upload = latest_file.uploaded_at if latest_file else None
        
        notes_stats.append({
            'note': note,
            'files_count': files_count,
            'folders_count': folders_count,
            'members_count': members_count,
            'latest_upload': latest_upload
        })
    
    return render_template('dashboard/notes_status.html',
                         notes_stats=notes_stats,
                         datetime=datetime)

