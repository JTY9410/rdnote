from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.utils.auth import hash_password, check_password, log_audit
from datetime import datetime
import os
import base64

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    return render_template('profile/index.html')

@profile_bp.route('/update', methods=['POST'])
@login_required
def update():
    current_user.org_name = request.form.get('org_name')
    current_user.department = request.form.get('department')
    current_user.researcher_code = request.form.get('researcher_code')
    current_user.updated_at = datetime.utcnow()
    
    db.session.commit()
    log_audit(current_user.id, 'PROFILE_UPDATE')
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('profile.index'))

@profile_bp.route('/password', methods=['POST'])
@login_required
def password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not check_password(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile.index'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile.index'))
    
    current_user.password_hash = hash_password(new_password)
    db.session.commit()
    log_audit(current_user.id, 'PASSWORD_CHANGE')
    flash('Password changed successfully.', 'success')
    return redirect(url_for('profile.index'))

@profile_bp.route('/signature', methods=['POST'])
@login_required
def signature():
    signature_data = request.form.get('signature_data')
    
    if signature_data:
        try:
            signature_bytes = base64.b64decode(signature_data.split(',')[1])
            filename = f"{current_user.email}_{datetime.utcnow().timestamp()}.png"
            os.makedirs('uploads/signatures', exist_ok=True)
            signature_path = f"uploads/signatures/{filename}"
            
            # Delete old signature if exists
            if current_user.signature_path and os.path.exists(current_user.signature_path):
                os.remove(current_user.signature_path)
            
            with open(signature_path, 'wb') as f:
                f.write(signature_bytes)
            
            current_user.signature_path = signature_path
            db.session.commit()
            log_audit(current_user.id, 'SIGNATURE_UPDATE')
            flash('Signature updated successfully.', 'success')
        except Exception as e:
            flash(f'Error saving signature: {e}', 'error')
    else:
        flash('No signature data provided.', 'error')
    
    return redirect(url_for('profile.index'))

