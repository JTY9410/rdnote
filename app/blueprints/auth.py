from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.utils.auth import hash_password, check_password, log_audit
from app.models.system_settings import SystemSettings
from datetime import datetime
import os
import base64
import time

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('auth/login.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Throttle on repeated failures
        fail_count = session.get('login_failures', 0)
        need_captcha = session.get('need_captcha', False)
        if fail_count >= 5:
            need_captcha = True
            session['need_captcha'] = True
            # simple placeholder captcha: expect field 'captcha' == 'ok'
            captcha = request.form.get('captcha')
            if captcha != 'ok':
                flash('Captcha required. 입력란에 ok 를 입력하세요.', 'error')
                # Small delay to slow brute-force
                time.sleep(min(2 + fail_count, 8))
                return render_template('auth/login.html', need_captcha=True)
        
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password(user.password_hash, password):
            if user.status == 'active':
                user.last_login_at = datetime.utcnow()
                db.session.commit()
                
                login_user(user)
                log_audit(user.id, 'USER_LOGIN', meta_json={'email': email})
                session.pop('login_failures', None)
                session.pop('need_captcha', None)
                return redirect(url_for('dashboard.index'))
            else:
                log_audit(user.id, 'USER_LOGIN_DENIED', meta_json={'reason': f'status={user.status}'})
                flash('Your account is not active. Please contact administrator.', 'error')
        else:
            # failure path
            session['login_failures'] = fail_count + 1
            # incremental delay
            time.sleep(min(2 + fail_count, 8))
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        org_name = request.form.get('org_name')
        department = request.form.get('department')
        researcher_code = request.form.get('researcher_code')
        workspace_name = request.form.get('workspace_name')
        create_workspace = request.form.get('create_workspace') == 'on'
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')
        
        # Check password match
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        # Save signature
        signature_data = request.form.get('signature_data')
        signature_path = None
        
        if signature_data:
            # Decode base64 signature
            try:
                signature_bytes = base64.b64decode(signature_data.split(',')[1])
                filename = f"{email}_{datetime.utcnow().timestamp()}.png"
                os.makedirs('uploads/signatures', exist_ok=True)
                signature_path = f"uploads/signatures/{filename}"
                
                with open(signature_path, 'wb') as f:
                    f.write(signature_bytes)
            except Exception as e:
                print(f"Error saving signature: {e}")
        
        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            org_name=org_name,
            department=department,
            researcher_code=researcher_code,
            signature_path=signature_path,
            status='pending'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create workspace if requested
        if create_workspace and workspace_name:
            workspace = Workspace(name=workspace_name, owner_user_id=user.id)
            db.session.add(workspace)
            db.session.flush()
            
            # Add user as workspace owner
            member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user.id,
                role='OWNER'
            )
            db.session.add(member)
            db.session.commit()
            
            log_audit(user.id, 'WORKSPACE_CREATE', workspace_id=workspace.id)
        
        log_audit(user.id, 'USER_REGISTER', meta_json={'email': email, 'org_name': org_name})
        
        flash('Registration successful. Please wait for administrator approval.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

