def get_note_role(user_id, note_id):
    """Get user's role in a note"""
    from app.models.research_note import ResearchNoteMember
    
    membership = ResearchNoteMember.query.filter_by(
        note_id=note_id,
        user_id=user_id
    ).first()
    
    return membership.role if membership else None

def can_access_note(user_id, note_id):
    """Check if user can access a note"""
    role = get_note_role(user_id, note_id)
    return role is not None

def can_write_note(user_id, note_id):
    """Check if user can write to a note"""
    role = get_note_role(user_id, note_id)
    return role in ['OWNER', 'WRITER']

def can_delete_file(user_id, note_id, note):
    """Check if user can delete files"""
    from app.models.research_note import ResearchNoteMember
    
    role = get_note_role(user_id, note_id)
    
    if role == 'OWNER':
        return True
    
    if role == 'WRITER' and note and note.allow_writer_delete:
        return True
    
    return False

def can_download(user_id, note_id, note):
    """Check if user can download files"""
    from app.models.research_note import ResearchNoteMember
    
    role = get_note_role(user_id, note_id)
    
    if role == 'OWNER':
        return True
    
    if role in ['WRITER', 'READER', 'REVIEWER'] and note and note.allow_member_download:
        return True
    
    return False

def can_manage_note(user_id, note_id):
    """Check if user is owner of a note"""
    role = get_note_role(user_id, note_id)
    return role == 'OWNER'

def is_admin(user):
    """Check if user is admin"""
    return user and user.is_admin

def get_workspace_role(user_id, workspace_id):
    """Get user's role in a workspace"""
    from app.models.workspace import WorkspaceMember
    
    membership = WorkspaceMember.query.filter_by(
        workspace_id=workspace_id,
        user_id=user_id
    ).first()
    
    return membership.role if membership else None

