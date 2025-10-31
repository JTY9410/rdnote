from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.research_note import ResearchNote, ResearchNoteMember
from app.models.folder import Folder
from app.models.file import File
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.audit_log import AuditLog
from app.utils.auth import log_audit
from app.utils.permissions import can_manage_note, can_access_note
from datetime import datetime, date
import os

notes_bp = Blueprint('notes', __name__)

@notes_bp.post('/<int:note_id>/favorite')
@login_required
def favorite(note_id):
    from app.models.favorite import Favorite
    # 8개 제한
    fav_count = Favorite.query.filter_by(user_id=current_user.id).count()
    if fav_count >= 8 and not Favorite.query.filter_by(user_id=current_user.id, note_id=note_id).first():
        return {'error': '즐겨찾기는 최대 8개까지 가능합니다.'}, 400
    if not Favorite.query.filter_by(user_id=current_user.id, note_id=note_id).first():
        db.session.add(Favorite(user_id=current_user.id, note_id=note_id))
        db.session.commit()
    return {'ok': True}

@notes_bp.delete('/<int:note_id>/favorite')
@login_required
def unfavorite(note_id):
    from app.models.favorite import Favorite
    fav = Favorite.query.filter_by(user_id=current_user.id, note_id=note_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return {'ok': True}

@notes_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        workspace_id = request.form.get('workspace_id')
        title = request.form.get('title')
        project_code = request.form.get('project_code')
        manager_name = request.form.get('manager_name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        allow_writer_delete = request.form.get('allow_writer_delete') == 'on'
        allow_member_download = request.form.get('allow_member_download') == 'on'
        
        # Get members from workspace
        from app.models.workspace import WorkspaceMember as WSMember
        workspace_members = WSMember.query.filter_by(workspace_id=int(workspace_id)).all()
        members_data = []
        roles_data = []
        
        # Validate workspace access
        from app.utils.permissions import get_workspace_role
        if get_workspace_role(current_user.id, int(workspace_id)) is None:
            flash('Access denied to workspace.', 'error')
            return redirect(url_for('dashboard.index'))
        
        # Create note
        note = ResearchNote(
            workspace_id=int(workspace_id),
            owner_user_id=current_user.id,
            title=title,
            project_code=project_code,
            manager_name=manager_name,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            allow_writer_delete=allow_writer_delete,
            allow_member_download=allow_member_download
        )
        db.session.add(note)
        db.session.flush()
        
        # Add current user as owner
        owner_member = ResearchNoteMember(
            note_id=note.id,
            user_id=current_user.id,
            role='OWNER'
        )
        db.session.add(owner_member)
        
        db.session.commit()
        
        log_audit(current_user.id, 'NOTE_CREATE', note_id=note.id)
        flash('Research note created successfully.', 'success')
        return redirect(url_for('notes.detail', note_id=note.id))
    
    # GET request
    workspaces = db.session.query(Workspace).join(
        WorkspaceMember,
        (Workspace.id == WorkspaceMember.workspace_id) &
        (WorkspaceMember.user_id == current_user.id)
    ).all()
    
    return render_template('notes/new.html', workspaces=workspaces)

@notes_bp.route('/<int:note_id>')
@login_required
def detail(note_id):
    note = ResearchNote.query.get_or_404(note_id)
    
    # Check access
    if not can_access_note(current_user.id, note_id):
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get folders
    folders = Folder.query.filter_by(note_id=note_id, deleted_at=None).order_by(Folder.order_index).all()
    
    # Get files
    files = File.query.filter_by(note_id=note_id, is_deleted=False).all()
    
    # Get members
    members = ResearchNoteMember.query.filter_by(note_id=note_id).all()
    
    # Get audit logs
    from app.models.audit_log import AuditLog
    audit_logs = AuditLog.query.filter_by(note_id=note_id).order_by(AuditLog.created_at.desc()).limit(20).all()
    
    # Get download history
    from app.models.download_history import DownloadHistory
    download_history = DownloadHistory.query.filter_by(note_id=note_id).order_by(DownloadHistory.created_at.desc()).limit(10).all()
    
    return render_template('notes/detail.html',
                         note=note,
                         folders=folders,
                         files=files,
                         members=members,
                         audit_logs=audit_logs,
                         download_history=download_history)

@notes_bp.route('/<int:note_id>/settings', methods=['POST'])
@login_required
def settings(note_id):
    note = ResearchNote.query.get_or_404(note_id)
    
    if not can_manage_note(current_user.id, note_id):
        flash('Only note owner can change settings.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    note.allow_writer_delete = request.form.get('allow_writer_delete') == 'on'
    note.allow_member_download = request.form.get('allow_member_download') == 'on'
    note.updated_at = datetime.utcnow()
    db.session.commit()
    
    log_audit(current_user.id, 'NOTE_SETTINGS_UPDATE', note_id=note_id,
              meta_json={'allow_writer_delete': note.allow_writer_delete,
                        'allow_member_download': note.allow_member_download})
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('notes.detail', note_id=note_id))

@notes_bp.route('/<int:note_id>/members', methods=['POST'])
@login_required
def members(note_id):
    note = ResearchNote.query.get_or_404(note_id)
    
    if not can_manage_note(current_user.id, note_id):
        flash('Only note owner can manage members.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    # Get form data
    members_data = request.form.getlist('members')
    roles_data = request.form.getlist('roles')
    action = request.form.get('action')
    
    if action == 'add':
        for i, member_id in enumerate(members_data):
            if member_id and roles_data[i]:
                existing = ResearchNoteMember.query.filter_by(
                    note_id=note_id,
                    user_id=int(member_id)
                ).first()
                
                if not existing:
                    member = ResearchNoteMember(
                        note_id=note_id,
                        user_id=int(member_id),
                        role=roles_data[i]
                    )
                    db.session.add(member)
    elif action == 'update':
        member_id = request.form.get('member_id')
        new_role = request.form.get('role')
        member = ResearchNoteMember.query.get_or_404(member_id)
        member.role = new_role
    
    db.session.commit()
    log_audit(current_user.id, 'NOTE_MEMBER_UPDATE', note_id=note_id,
              meta_json={'action': action})
    flash('Members updated successfully.', 'success')
    return redirect(url_for('notes.detail', note_id=note_id))

@notes_bp.route('/<int:note_id>/approve', methods=['POST'])
@login_required
def approve(note_id):
    note = ResearchNote.query.get_or_404(note_id)
    
    # Check if user is OWNER or REVIEWER
    member = ResearchNoteMember.query.filter_by(note_id=note_id, user_id=current_user.id).first()
    if not member or member.role not in ['OWNER', 'REVIEWER']:
        flash('Only owner or reviewer can approve.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    # Update approval stage based on role
    signed_at = datetime.utcnow()
    stage_before = note.approval_stage
    
    if member.role == 'REVIEWER':
        # REVIEWER approves → stage becomes REVIEWED (minimum)
        note.approval_stage = 'REVIEWED'
        stage_after = 'REVIEWED'
    elif member.role == 'OWNER':
        # OWNER approves → stage becomes APPROVED
        note.approval_stage = 'APPROVED'
        stage_after = 'APPROVED'
    
    db.session.commit()
    
    log_audit(current_user.id, 'REVIEWER_APPROVE', note_id=note_id,
              meta_json={
                  'approver_role': member.role,
                  'signed_at': signed_at.isoformat(),
                  'stage_before': stage_before,
                  'stage_after': stage_after
              })
    
    flash(f'Approval recorded. Stage: {stage_before} → {stage_after}', 'success')
    return redirect(url_for('notes.detail', note_id=note_id))

@notes_bp.route('/<int:note_id>/request-review', methods=['POST'])
@login_required
def request_review(note_id):
    """Owner requests review; moves stage to REVIEWED baseline and logs event."""
    note = ResearchNote.query.get_or_404(note_id)
    # Only owner can request review and reviewer must be assigned
    if note.owner_user_id != current_user.id or not getattr(note, 'reviewer_user_id', None):
        flash('검토 요청은 책임자만 가능하며, 검토자가 지정되어야 합니다.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    prev = note.approval_stage
    note.approval_stage = 'REVIEWED'
    db.session.commit()
    log_audit(current_user.id, 'REVIEW_REQUEST', note_id=note_id,
              meta_json={'stage_before': prev, 'stage_after': 'REVIEWED'})
    flash('검토 요청이 등록되었습니다.', 'success')
    return redirect(url_for('notes.detail', note_id=note_id))

@notes_bp.route('/<int:note_id>/transfer-ownership', methods=['POST'])
@login_required
def transfer_ownership(note_id):
    """Transfer ownership of research note"""
    note = ResearchNote.query.get_or_404(note_id)
    
    if not can_manage_note(current_user.id, note_id):
        flash('Only current owner can transfer ownership.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    new_owner_id = request.form.get('new_owner_id')
    
    if not new_owner_id:
        flash('New owner ID is required.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    old_owner_id = note.owner_user_id
    old_owner = User.query.get(old_owner_id)
    new_owner = User.query.get(int(new_owner_id))
    
    # Update owner
    note.owner_user_id = int(new_owner_id)
    
    # Update member role
    old_owner_member = ResearchNoteMember.query.filter_by(note_id=note_id, user_id=old_owner_id).first()
    new_owner_member = ResearchNoteMember.query.filter_by(note_id=note_id, user_id=int(new_owner_id)).first()
    
    if old_owner_member:
        old_owner_member.role = 'READER'  # Downgrade old owner
    
    if new_owner_member:
        new_owner_member.role = 'OWNER'  # Upgrade new owner
    else:
        # Add as owner if not already a member
        new_owner_member = ResearchNoteMember(
            note_id=note_id,
            user_id=int(new_owner_id),
            role='OWNER'
        )
        db.session.add(new_owner_member)
    
    db.session.commit()
    
    log_audit(current_user.id, 'NOTE_TRANSFER_OWNER', note_id=note_id,
              meta_json={'old_owner': old_owner.email if old_owner else 'N/A', 
                        'new_owner': new_owner.email if new_owner else 'N/A'})
    flash('Ownership transferred successfully.', 'success')
    return redirect(url_for('notes.detail', note_id=note_id))

@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@login_required
def delete(note_id):
    note = ResearchNote.query.get_or_404(note_id)
    
    if not can_manage_note(current_user.id, note_id):
        flash('Only note owner can delete.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    reason = request.form.get('reason')
    
    if not reason:
        flash('삭제 사유는 필수입니다. 연구개발일지는 수년~수십 년 단위로 유지해야 하는 법적 의무가 있습니다.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    note.deleted_at = datetime.utcnow()
    
    # Delete all related files
    from app.models.file import File
    files = File.query.filter_by(note_id=note_id, is_deleted=False).all()
    for file in files:
        file.is_deleted = True
        filepath = os.path.join('uploads/files', file.stored_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.commit()
    
    log_audit(current_user.id, 'NOTE_DELETE', note_id=note_id,
              meta_json={'reason': reason, 'note_title': note.title, 'warning': '장기 보존 의무'})
    flash('Note deleted successfully. 관련 파일도 모두 삭제되었습니다.', 'success')
    return redirect(url_for('dashboard.index'))

@notes_bp.route('/<int:note_id>/audit', methods=['GET'])
@login_required
def audit_json(note_id):
    """Get audit logs for note as JSON"""
    # Check access permission
    if not can_access_note(current_user.id, note_id):
        return jsonify({'error': 'Access denied'}), 403
    
    audit_logs = AuditLog.query.filter_by(note_id=note_id).order_by(AuditLog.created_at.desc()).limit(100).all()
    
    logs = []
    for log in audit_logs:
        logs.append({
            'id': log.id,
            'user': {
                'id': log.user.id if log.user else None,
                'name': log.user.name if log.user else None,
                'email': log.user.email if log.user else None
            },
            'action_type': log.action_type,
            'meta_json': log.meta_json,
            'created_at': log.created_at.isoformat()
        })
    
    return jsonify({'logs': logs})

@notes_bp.route('/<int:note_id>/downloads', methods=['GET'])
@login_required
def downloads_json(note_id):
    """Get download history for note as JSON"""
    # Check access permission
    if not can_access_note(current_user.id, note_id):
        return jsonify({'error': 'Access denied'}), 403
    
    downloads = DownloadHistory.query.filter_by(note_id=note_id).order_by(DownloadHistory.created_at.desc()).limit(50).all()
    
    history = []
    for download in downloads:
        history.append({
            'id': download.id,
            'user': {
                'id': download.user.id if download.user else None,
                'name': download.user.name if download.user else None,
                'email': download.user.email if download.user else None
            },
            'file': {
                'id': download.file.id if download.file else None,
                'name': download.file.display_name if download.file else None
            },
            'download_type': download.download_type,
            'created_at': download.created_at.isoformat()
        })
    
    return jsonify({'downloads': history})

