from flask import Blueprint, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models.folder import Folder
from app.models.research_note import ResearchNote
from app.models.file import File
from app.utils.auth import log_audit
from app.utils.permissions import can_write_note, can_manage_note
from datetime import datetime

folders_bp = Blueprint('folders', __name__)

@folders_bp.route('/notes/<int:note_id>/folders', methods=['POST'])
@login_required
def create(note_id):
    name = request.form.get('name')
    
    # Check permission
    if not can_write_note(current_user.id, note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Validate folder name length (≤50자)
    if not name or len(name.strip()) == 0:
        return jsonify({'error': '폴더 이름은 필수입니다.'}), 400
    if len(name) > 50:
        return jsonify({'error': '폴더 이름은 최대 50자까지 가능합니다.'}), 400
    
    # Check folder count limit (≤30개 per note)
    folder_count = Folder.query.filter_by(note_id=note_id, deleted_at=None).count()
    if folder_count >= 30:
        return jsonify({'error': '노트당 폴더는 최대 30개까지 가능합니다.'}), 422
    
    # Get max order_index
    max_order = db.session.query(db.func.max(Folder.order_index)).filter_by(note_id=note_id).scalar() or 0
    
    folder = Folder(
        note_id=note_id,
        name=name,
        order_index=max_order + 1
    )
    db.session.add(folder)
    db.session.commit()
    
    log_audit(current_user.id, 'FOLDER_CREATE', note_id=note_id, meta_json={'folder_name': name})
    return jsonify({'id': folder.id, 'name': folder.name}), 201

@folders_bp.route('/folders/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    new_name = request.form.get('name')
    
    # Check permission
    if not can_write_note(current_user.id, folder.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Validate folder name length (≤50자)
    if not new_name or len(new_name.strip()) == 0:
        return jsonify({'error': '폴더 이름은 필수입니다.'}), 400
    if len(new_name) > 50:
        return jsonify({'error': '폴더 이름은 최대 50자까지 가능합니다.'}), 400
    
    old_name = folder.name
    folder.name = new_name
    folder.updated_at = datetime.utcnow()
    db.session.commit()
    
    log_audit(current_user.id, 'FOLDER_RENAME', note_id=folder.note_id,
              meta_json={'old_name': old_name, 'new_name': new_name})
    return jsonify({'success': True}), 200

@folders_bp.route('/folders/reorder', methods=['POST'])
@login_required
def reorder():
    data = request.json
    folders = data.get('folders', [])
    
    updated = []
    for item in folders:
        folder = Folder.query.get(item['folder_id'])
        if folder:
            # Check permission
            if can_write_note(current_user.id, folder.note_id):
                folder.order_index = item['order_index']
                updated.append(folder.id)
    
    if updated:
        db.session.commit()
        log_audit(current_user.id, 'FOLDER_REORDER', meta_json={'updated': updated})
    
    return jsonify({'success': True, 'updated': updated}), 200

@folders_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    reason = request.form.get('reason')
    
    # Check permission (only owner)
    if not can_manage_note(current_user.id, folder.note_id):
        return jsonify({'error': 'Permission denied'}), 403
    
    # Delete all files in folder
    files = File.query.filter_by(folder_id=folder_id, is_deleted=False).all()
    for file in files:
        file.is_deleted = True
        log_audit(current_user.id, 'FILE_DELETE', file_id=file.id,
                  meta_json={'reason': f'Deleted with folder: {reason}'})
    
    folder.deleted_at = datetime.utcnow()
    db.session.commit()
    
    log_audit(current_user.id, 'FOLDER_DELETE', note_id=folder.note_id,
              meta_json={'folder_name': folder.name, 'reason': reason, 'file_count': len(files)})
    
    return jsonify({'success': True}), 200

