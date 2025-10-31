from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.workspace import Workspace, WorkspaceMember
from app.models.research_note import ResearchNote
from app.utils.auth import log_audit
from app.utils.permissions import get_workspace_role
from datetime import datetime

workspaces_bp = Blueprint('workspaces', __name__)

@workspaces_bp.route('/')
@login_required
def index():
    workspaces = db.session.query(Workspace).join(
        WorkspaceMember,
        (Workspace.id == WorkspaceMember.workspace_id) &
        (WorkspaceMember.user_id == current_user.id)
    ).all()
    return render_template('workspaces/index.html', workspaces=workspaces)

@workspaces_bp.route('/<int:workspace_id>')
@login_required
def detail(workspace_id):
    workspace = Workspace.query.get_or_404(workspace_id)
    
    # Check access
    if get_workspace_role(current_user.id, workspace_id) is None:
        flash('Access denied.', 'error')
        return redirect(url_for('workspaces.index'))
    
    # Get members
    members = WorkspaceMember.query.filter_by(workspace_id=workspace_id).all()
    
    # Get notes
    notes = ResearchNote.query.filter_by(workspace_id=workspace_id).filter(ResearchNote.deleted_at.is_(None)).all()
    
    return render_template('workspaces/detail.html', 
                         workspace=workspace, 
                         members=members,
                         notes=notes)

@workspaces_bp.route('/', methods=['POST'])
@login_required
def create():
    name = request.form.get('name')
    
    if not name:
        flash('Workspace name is required.', 'error')
        return redirect(url_for('workspaces.index'))
    
    workspace = Workspace(name=name, owner_user_id=current_user.id)
    db.session.add(workspace)
    db.session.flush()
    
    # Add creator as owner
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role='OWNER'
    )
    db.session.add(member)
    db.session.commit()
    
    log_audit(current_user.id, 'WORKSPACE_CREATE', workspace_id=workspace.id)
    flash('Workspace created successfully.', 'success')
    return redirect(url_for('workspaces.index'))

@workspaces_bp.route('/<int:workspace_id>/invite', methods=['POST'])
@login_required
def invite(workspace_id):
    email = request.form.get('email')
    
    # Check permission
    role = get_workspace_role(current_user.id, workspace_id)
    if role != 'OWNER':
        flash('Only workspace owner can invite members.', 'error')
        return redirect(url_for('workspaces.detail', workspace_id=workspace_id))
    
    # Find user
    from app.models.user import User
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('workspaces.detail', workspace_id=workspace_id))
    
    # Check if already member
    if WorkspaceMember.query.filter_by(workspace_id=workspace_id, user_id=user.id).first():
        flash('User is already a member.', 'error')
        return redirect(url_for('workspaces.detail', workspace_id=workspace_id))
    
    # Add member
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role='MEMBER'
    )
    db.session.add(member)
    db.session.commit()
    
    log_audit(current_user.id, 'WORKSPACE_INVITE', workspace_id=workspace_id, 
              meta_json={'invited_user': email})
    flash('Member added successfully.', 'success')
    return redirect(url_for('workspaces.detail', workspace_id=workspace_id))

@workspaces_bp.route('/<int:workspace_id>/member-role', methods=['POST'])
@login_required
def update_member_role(workspace_id):
    member_id = request.form.get('member_id')
    new_role = request.form.get('role')
    action = request.form.get('action')
    
    # Check permission
    role = get_workspace_role(current_user.id, workspace_id)
    if role != 'OWNER':
        flash('Only workspace owner can manage members.', 'error')
        return redirect(url_for('workspaces.detail', workspace_id=workspace_id))
    
    if action == 'remove':
        member = WorkspaceMember.query.get_or_404(member_id)
        db.session.delete(member)
        db.session.commit()
        log_audit(current_user.id, 'WORKSPACE_MEMBER_REMOVE', workspace_id=workspace_id,
                  meta_json={'removed_user_id': member.user_id})
        flash('Member removed successfully.', 'success')
    else:
        member = WorkspaceMember.query.get_or_404(member_id)
        member.role = new_role
        db.session.commit()
        log_audit(current_user.id, 'WORKSPACE_MEMBER_CHANGE', workspace_id=workspace_id,
                  meta_json={'member_id': member_id, 'new_role': new_role})
        flash('Member role updated successfully.', 'success')
    
    return redirect(url_for('workspaces.detail', workspace_id=workspace_id))

