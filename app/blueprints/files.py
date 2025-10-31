from flask import Blueprint, request, jsonify, send_file, flash, url_for
from flask_login import login_required, current_user
from app import db
from app.models.file import File, FileTag
from app.models.research_note import ResearchNote
from app.models.folder import Folder
from app.models.download_history import DownloadHistory
from app.models.system_settings import SystemSettings
from app.utils.auth import log_audit
from app.utils.permissions import can_write_note, can_delete_file, can_download, can_access_note
from datetime import datetime
import os
import uuid
import hashlib
from werkzeug.utils import secure_filename

files_bp = Blueprint('files', __name__)
@files_bp.route('/notes/<int:note_id>/files', methods=['POST'])
@login_required
def upload_to_note(note_id):
    """Upload files to a note by selecting the note only. Creates/uses a default folder."""
    note = ResearchNote.query.get_or_404(note_id)
    # Permission: writer/owner
    if not can_write_note(current_user.id, note_id):
        return jsonify({'error': 'Permission denied'}), 403

    # Ensure default folder exists
    default_name = '기본'
    folder = Folder.query.filter_by(note_id=note_id, name=default_name).first()
    if not folder:
        folder = Folder(note_id=note_id, name=default_name)
        db.session.add(folder)
        db.session.commit()

    # Reuse existing upload logic by setting folder_id
    # Attach folder_id to endpoint
    return upload(folder.id)


@files_bp.route('/folders/<int:folder_id>/files', methods=['POST'])
@login_required
def upload(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    note_id = folder.note_id
    
    # Check permission
    if not can_write_note(current_user.id, note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    files = request.files.getlist('files[]') or request.files.getlist('file')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    created_date = request.form.get('created_date') or request.form.get('createdDate')
    tags = request.form.get('tags', '')
    short_desc = request.form.get('short_desc') or request.form.get('shortDesc', '')
    
    # Check settings
    allowed_exts = SystemSettings.get('allowed_extensions', '.pdf,.jpg,.png,.jpeg,.csv,.xlsx,.zip').split(',')
    max_size = int(SystemSettings.get('max_file_size_mb', '500')) * 1024 * 1024
    
    uploaded_files = []

    # Parse and validate tags once
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if len(tag_list) > 30:
            return jsonify({'error': '태그는 파일당 최대 30개까지 가능합니다.'}), 400
        for t in tag_list:
            if len(t) > 20:
                return jsonify({'error': f'태그 "{t}" 길이가 20자를 초과했습니다.'}), 400
    
    for file in files:
        if file.filename == '':
            continue
        
        # Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_exts:
            return jsonify({'error': f'Extension {ext} not allowed'}), 400
        
        # Save file (size limit check first)
        file.seek(0, os.SEEK_END)
        size_tmp = file.tell()
        file.seek(0)
        if size_tmp > max_size:
            return jsonify({'error': f'파일 크기가 제한({max_size//1024//1024}MB)를 초과했습니다.'}), 400

        # Save file
        stored_filename = f"{uuid.uuid4()}{ext}"
        os.makedirs('uploads/files', exist_ok=True)
        filepath = os.path.join('uploads/files', stored_filename)
        file.save(filepath)
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()
        
        # Get file size
        size = os.path.getsize(filepath)
        
        # Set timestamp_certified_at (시점인증) - 서버 시각, 불변
        sealed_at = datetime.utcnow()
        
        # Parse created_date (written_at)
        if created_date:
            try:
                written_date = datetime.strptime(created_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '작성일자 형식이 올바르지 않습니다 (YYYY-MM-DD)'}), 400
        else:
            written_date = datetime.utcnow().date()
        
        # Validate: written_at (created_date) must be <= sealed_at (요구사항 39, 154)
        if written_date > sealed_at.date():
            return jsonify({'error': '작성일자는 시점인증일보다 미래일 수 없습니다.'}), 422
        
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
        
        uploaded_files.append(file_record)
    
    db.session.commit()
    
    # Audit log per file
    for f in uploaded_files:
        log_audit(current_user.id, 'FILE_UPLOAD', note_id=note_id, file_id=f.id,
                  meta_json={'created_date': created_date, 'short_desc': short_desc, 'file_hash': f.file_hash})
    
    return jsonify({'success': True, 'files': [{'id': f.id, 'name': f.display_name} for f in uploaded_files]}), 201

@files_bp.post('/files/drive')
@login_required
def drive_import():
    """Drive import request: enforce 10MB conversion cap and accept allowed entries.
    Payload: { note_id, folder_id?, entries:[{external_id, size}] }
    Response: {accepted:[...], blocked:[{external_id, blocked_reason:"GT_10MB"}]}"""
    d = request.json or {}
    note_id = d.get('note_id')
    folder_id = d.get('folder_id')
    entries = d.get('entries', [])
    if not note_id:
        return {'error': 'note_id is required'}, 400
    if not can_write_note(current_user.id, note_id):
        return {'error': 'Permission denied'}, 403
    accepted, blocked = [], []
    cap = 10 * 1024 * 1024
    for e in entries:
        size = int(e.get('size', 0) or 0)
        ext_id = e.get('external_id')
        if size > cap:
            blocked.append({'external_id': ext_id, 'blocked_reason': 'GT_10MB'})
        else:
            accepted.append({'external_id': ext_id})
    # In a real worker flow, enqueue conversion jobs here.
    log_audit(current_user.id, 'DRIVE_IMPORT_REQUEST', note_id=note_id,
              meta_json={'accepted': len(accepted), 'blocked': len(blocked)})
    return {'accepted': accepted, 'blocked': blocked}, 200

@files_bp.route('/files/<int:file_id>/new-version', methods=['POST'])
@login_required
def new_version(file_id):
    file_record = File.query.get_or_404(file_id)
    data = request.json or request.form
    change_reason = data.get('change_reason', '')
    
    # Check permission
    if not can_write_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    old_version = file_record.version_number
    
    # Save new version
    ext = os.path.splitext(file.filename)[1].lower()
    stored_filename = f"{uuid.uuid4()}{ext}"
    os.makedirs('uploads/files', exist_ok=True)
    filepath = os.path.join('uploads/files', stored_filename)
    file.save(filepath)
    
    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    file_hash = sha256_hash.hexdigest()
    
    # Set timestamp_certified_at (시점인증) - 서버 시각, 불변
    sealed_at = datetime.utcnow()
    
    # Use existing created_date, but validate it's not after sealed_at
    # (This should already be valid from original file, but double-check)
    if file_record.created_date > sealed_at.date():
        # This shouldn't happen, but ensure consistency
        created_date_to_use = sealed_at.date()
    else:
        created_date_to_use = file_record.created_date
    
    # Create new version record
    new_file = File(
        note_id=file_record.note_id,
        folder_id=file_record.folder_id,
        uploader_user_id=current_user.id,
        original_filename=file.filename,
        display_name=file_record.display_name,
        stored_filename=stored_filename,
        mime_type=file.content_type,
        size_bytes=os.path.getsize(filepath),
        created_date=created_date_to_use,
        uploaded_at=datetime.utcnow(),
        timestamp_certified_at=sealed_at,
        version_number=old_version + 1,
        short_desc=file_record.short_desc,
        file_hash=file_hash
    )
    db.session.add(new_file)
    db.session.flush()
    
    # Copy tags
    for tag in file_record.tags:
        new_tag = FileTag(file_id=new_file.id, tag=tag.tag)
        db.session.add(new_tag)
    
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_VERSION_UP', note_id=file_record.note_id, file_id=file_record.id,
              meta_json={'old_version': old_version, 'new_version': old_version + 1, 'reason': change_reason, 'file_hash': file_hash})
    
    return jsonify({'success': True, 'new_file_id': new_file.id}), 201

@files_bp.route('/files/<int:file_id>/rename', methods=['POST'])
@login_required
def rename(file_id):
    file_record = File.query.get_or_404(file_id)
    data = request.json or request.form
    new_name = data.get('display_name')
    
    # Check permission
    if not can_write_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    old_name = file_record.display_name
    file_record.display_name = new_name
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_RENAME', note_id=file_record.note_id, file_id=file_id,
              meta_json={'old_name': old_name, 'new_name': new_name})
    
    return jsonify({'success': True}), 200

@files_bp.route('/files/<int:file_id>/update-date', methods=['PUT', 'POST'])
@login_required
def update_created_date(file_id):
    """Update file created_date (written_at) - 요구사항 4.6, 4.11: 작성일자 인라인 변경"""
    file_record = File.query.get_or_404(file_id)
    data = request.json or request.form
    new_date_str = data.get('created_date') or data.get('written_at')
    
    # Check permission
    if not can_write_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    if not new_date_str:
        return jsonify({'error': '작성일자는 필수입니다.'}), 400
    
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '작성일자 형식이 올바르지 않습니다 (YYYY-MM-DD)'}), 400
    
    # Validate: written_at (created_date) must be <= sealed_at (요구사항 39, 154)
    sealed_at_date = file_record.timestamp_certified_at.date() if file_record.timestamp_certified_at else datetime.utcnow().date()
    if new_date > sealed_at_date:
        return jsonify({'error': '작성일자는 시점인증일보다 미래일 수 없습니다.'}), 422
    
    old_date = file_record.created_date
    file_record.created_date = new_date
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_UPDATE_DATE', note_id=file_record.note_id, file_id=file_id,
              meta_json={'old_date': old_date.isoformat() if old_date else None, 
                        'new_date': new_date.isoformat()})
    
    return jsonify({'success': True, 'created_date': new_date.isoformat()}), 200

@files_bp.route('/files/<int:file_id>/meta', methods=['GET'])
@login_required
def file_meta(file_id):
    f = File.query.get_or_404(file_id)
    if not can_access_note(current_user.id, f.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    data = {
        'id': f.id,
        'name': f.display_name,
        'original': f.original_filename,
        'size_bytes': f.size_bytes,
        'created_date': f.created_date.isoformat() if f.created_date else None,
        'uploaded_at': f.uploaded_at.isoformat() if f.uploaded_at else None,
        'uploader': f.uploader_user.name if f.uploader_user else None,
        'version': f.version_number,
        'hash': f.file_hash,
        'note_id': f.note_id,
        'folder_id': f.folder_id
    }
    return jsonify({'file': data})

@files_bp.route('/files/<int:file_id>/tags', methods=['POST'])
@login_required
def update_tags(file_id):
    file_record = File.query.get_or_404(file_id)
    data = request.json or request.form
    raw = data.get('tags', '')
    
    # Check permission
    if not can_write_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Validate
    tag_list = [t.strip() for t in raw.split(',') if t.strip()]
    if len(tag_list) > 30:
        return jsonify({'error': '태그는 파일당 최대 30개까지 가능합니다.'}), 400
    for t in tag_list:
        if len(t) > 20:
            return jsonify({'error': f'태그 "{t}" 길이가 20자를 초과했습니다.'}), 400

    # Delete old tags
    FileTag.query.filter_by(file_id=file_id).delete()
    
    # Add new tags
    for t in tag_list:
        file_tag = FileTag(file_id=file_id, tag=t)
        db.session.add(file_tag)
    
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_TAG_UPDATE', note_id=file_record.note_id, file_id=file_id,
              meta_json={'tags': ','.join(tag_list)})

    return jsonify({'success': True}), 200

@files_bp.get('/files/search')
@login_required
def search_files():
    from sqlalchemy import or_
    from app.models.user import User

    q = (request.args.get('q') or '').strip()
    author = request.args.get('author')
    mime = request.args.get('type')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    tag = request.args.get('tag')

    query = File.query.filter_by(is_deleted=False)

    if q:
        like = f'%{q}%'
        query = query.filter(or_(File.display_name.ilike(like), File.original_filename.ilike(like)))

    if author:
        query = query.join(File.uploader_user).filter(User.name.ilike(f'%{author}%'))

    if mime:
        query = query.filter(File.mime_type.ilike(f'%{mime}%'))

    if date_from:
        query = query.filter(File.created_date >= date_from)
    if date_to:
        query = query.filter(File.created_date <= date_to)

    if tag:
        query = query.join(FileTag, FileTag.file_id == File.id).filter(FileTag.tag.ilike(f'%{tag}%'))

    items = query.order_by(File.uploaded_at.desc()).limit(100).all()
    return {'items': [
        {
            'id': f.id,
            'name': f.display_name,
            'ext': (f.original_filename.rsplit('.',1)[1].lower() if '.' in f.original_filename else ''),
            'created_date': f.created_date.isoformat() if f.created_date else None
        } for f in items
    ]}
    
    return jsonify({'success': True}), 200

@files_bp.route('/files/<int:file_id>/download', methods=['GET'])
@login_required
def download(file_id):
    from flask import redirect
    from app.models.audit_log import AuditLog
    
    file_record = File.query.filter_by(id=file_id, is_deleted=False).first_or_404()
    note = ResearchNote.query.get_or_404(file_record.note_id)
    
    # Check download permission
    if not can_download(current_user.id, file_record.note_id, note):
        log_audit(current_user.id, 'FILE_DOWNLOAD_DENIED', file_id=file_id,
                  meta_json={'reason': 'permission denied'})
        flash('Download denied.', 'error')
        return redirect(url_for('notes.detail', note_id=note.id))
    
    # Check daily limit
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_downloads = DownloadHistory.query.filter(
        DownloadHistory.user_id == current_user.id,
        DownloadHistory.created_at >= today_start
    ).count()
    
    daily_limit = int(SystemSettings.get('daily_download_limit', '100'))
    
    if today_downloads >= daily_limit:
        log_audit(current_user.id, 'FILE_DOWNLOAD_LIMIT_BLOCKED', file_id=file_id,
                  meta_json={'limit': daily_limit, 'today_count': today_downloads})
        flash('Daily download limit reached.', 'error')
        return redirect(url_for('notes.detail', note_id=note.id))
    
    # Record download
    download_history = DownloadHistory(
        note_id=file_record.note_id,
        file_id=file_id,
        user_id=current_user.id,
        download_type='RAW_FILE'
    )
    db.session.add(download_history)
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_DOWNLOAD', note_id=file_record.note_id, file_id=file_id)
    
    # Send file
    filepath = os.path.join('uploads/files', file_record.stored_filename)
    if not os.path.exists(filepath):
        flash('File not found.', 'error')
        return redirect(url_for('notes.detail', note_id=note.id))
    
    return send_file(filepath, as_attachment=True, download_name=file_record.display_name)

@files_bp.route('/files/<int:file_id>/move', methods=['POST'])
@login_required
def move(file_id):
    """Move file to different folder"""
    file_record = File.query.get_or_404(file_id)
    data = request.json or request.form
    new_folder_id = data.get('folder_id')
    
    # Check permission
    if not can_write_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    old_folder_id = file_record.folder_id
    file_record.folder_id = new_folder_id
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_MOVE', note_id=file_record.note_id, file_id=file_id,
              meta_json={'old_folder_id': old_folder_id, 'new_folder_id': new_folder_id})
    
    return jsonify({'success': True}), 200

@files_bp.route('/files/<int:file_id>/versions', methods=['GET'])
@login_required
def get_versions(file_id):
    """Get all versions of a file"""
    file_record = File.query.get_or_404(file_id)
    
    # Check permission
    if not can_access_note(current_user.id, file_record.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get all versions of this file (same display_name)
    all_versions = File.query.filter_by(
        note_id=file_record.note_id,
        display_name=file_record.display_name,
        is_deleted=False
    ).order_by(File.version_number.desc()).all()
    
    versions = []
    for version in all_versions:
        versions.append({
            'id': version.id,
            'version_number': version.version_number,
            'uploaded_at': version.uploaded_at.isoformat(),
            'uploader': version.uploader_user.name if version.uploader_user else '-',
            'size': version.size_bytes,
            'timestamp_certified_at': version.timestamp_certified_at.isoformat() if version.timestamp_certified_at else None
        })
    
    return jsonify({'versions': versions}), 200

@files_bp.route('/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete(file_id):
    file_record = File.query.get_or_404(file_id)
    note = ResearchNote.query.get(file_record.note_id)
    data = request.json or {}
    reason = data.get('reason', '')
    
    # Check permission
    if not can_delete_file(current_user.id, file_record.note_id, note):
        return jsonify({'error': 'Permission denied'}), 403
    
    # 장기 보존 의무 경고가 프론트엔드에 추가되어야 함
    # 여기서는 reason이 필수인지 확인
    if not reason:
        return jsonify({'error': '삭제 사유는 필수입니다. 연구개발일지는 수년~수십 년 단위로 유지해야 하는 법적 의무가 있습니다.'}), 400
    
    # Delete file from disk
    filepath = os.path.join('uploads/files', file_record.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    file_record.is_deleted = True
    db.session.commit()
    
    log_audit(current_user.id, 'FILE_DELETE', note_id=file_record.note_id, file_id=file_id,
              meta_json={'reason': reason, 'file_name': file_record.display_name, 'warning': '장기 보존 의무'})
    
    return jsonify({'success': True}), 200

