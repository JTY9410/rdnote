from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
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
    # Check if user is already authenticated
    try:
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
    except Exception as e:
        current_app.logger.error(f"Error checking authentication status: {e}")
        # Continue with login flow
    
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
        
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('이메일과 비밀번호를 입력해주세요.', 'error')
            return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))
        
        try:
            # Query user with detailed logging
            current_app.logger.info(f"Attempting login for email: {email}")
            user = User.query.filter_by(email=email).first()
            
            if user:
                current_app.logger.info(f"User found: {email}, status: {user.status}, has_hash: {bool(user.password_hash)}")
                
                # Check password
                try:
                    if not user.password_hash:
                        current_app.logger.warning(f"User {email} has no password hash")
                        flash('Invalid email or password.', 'error')
                        session['login_failures'] = fail_count + 1
                        return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))
                    
                    password_valid = check_password(user.password_hash, password)
                    current_app.logger.info(f"Password check for {email}: {password_valid}")
                except Exception as e:
                    current_app.logger.error(f"Error checking password for {email}: {e}")
                    import traceback
                    current_app.logger.error(traceback.format_exc())
                    flash('로그인 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
                    return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))
                
                if password_valid:
                    if user.status == 'active':
                        try:
                            # Update last login time
                            try:
                                user.last_login_at = datetime.utcnow()
                                db.session.commit()
                            except Exception as e:
                                current_app.logger.warning(f"Failed to update last_login_at for {email}: {e}")
                                db.session.rollback()
                                # Continue with login even if this fails
                            
                            # Perform login
                            try:
                                login_user(user, remember=False)
                                current_app.logger.info(f"User {email} logged in successfully")
                            except Exception as e:
                                current_app.logger.error(f"Failed to login user {email}: {e}")
                                import traceback
                                current_app.logger.error(traceback.format_exc())
                                flash('로그인 세션 생성에 실패했습니다. 다시 시도해주세요.', 'error')
                                return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))
                            
                            # Log audit (non-blocking)
                            try:
                                log_audit(user.id, 'USER_LOGIN', meta_json={'email': email})
                            except Exception as e:
                                current_app.logger.warning(f"Failed to log audit for login: {e}")
                                # Don't fail login if audit logging fails
                            
                            # Clear failure counters
                            session.pop('login_failures', None)
                            session.pop('need_captcha', None)
                            
                            # Redirect to dashboard
                            try:
                                # Verify user is logged in before redirect
                                if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
                                    current_app.logger.error(f"User {email} not properly authenticated after login_user()")
                                    raise Exception("Authentication state inconsistent")
                                
                                current_app.logger.info(f"Redirecting {email} to dashboard")
                                flash('로그인되었습니다.', 'success')
                                dashboard_url = url_for('dashboard.index')
                                current_app.logger.info(f"Dashboard URL: {dashboard_url}")
                                return redirect(dashboard_url)
                            except Exception as e:
                                current_app.logger.error(f"Failed to redirect after login for {email}: {e}")
                                import traceback
                                current_app.logger.error(traceback.format_exc())
                                # If redirect fails, show dashboard directly
                                try:
                                    from flask import redirect
                                    return redirect('/dashboard')
                                except Exception as redirect_error:
                                    current_app.logger.error(f"Even simple redirect failed: {redirect_error}")
                                    flash('로그인되었지만 페이지 이동에 실패했습니다. /dashboard로 직접 이동해주세요.', 'warning')
                                    return render_template('auth/login.html', need_captcha=False)
                        except Exception as e:
                            current_app.logger.error(f"Unexpected error during login: {e}")
                            import traceback
                            current_app.logger.error(traceback.format_exc())
                            try:
                                db.session.rollback()
                            except Exception:
                                pass
                            flash('로그인 처리 중 예상치 못한 오류가 발생했습니다. 관리자에게 문의하세요.', 'error')
                    else:
                        try:
                            log_audit(user.id, 'USER_LOGIN_DENIED', meta_json={'reason': f'status={user.status}'})
                        except Exception:
                            pass
                        status_message = {
                            'pending': '계정이 아직 승인되지 않았습니다. 관리자의 승인을 기다려주세요.',
                            'suspended': '계정이 정지되었습니다. 관리자에게 문의하세요.'
                        }.get(user.status, '계정 상태가 비활성화되었습니다. 관리자에게 문의하세요.')
                        flash(status_message, 'error')
                else:
                    # Invalid password
                    session['login_failures'] = fail_count + 1
                    # incremental delay
                    time.sleep(min(2 + fail_count, 8))
                    flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')
            else:
                # User not found
                session['login_failures'] = fail_count + 1
                # incremental delay
                time.sleep(min(2 + fail_count, 8))
                flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')
        except Exception as e:
            current_app.logger.error(f"Database error during login for {email}: {e}")
            import traceback
            error_trace = traceback.format_exc()
            current_app.logger.error(f"Full traceback:\n{error_trace}")
            try:
                db.session.rollback()
                current_app.logger.info("Database session rolled back successfully")
            except Exception as rollback_error:
                current_app.logger.error(f"Error during rollback: {rollback_error}")
            flash('로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error')
    
    return render_template('auth/login.html', need_captcha=session.get('need_captcha', False))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
    except AttributeError:
        # current_user not properly initialized, continue with registration
        pass
    except Exception as e:
        current_app.logger.error(f"Error checking authentication status: {e}")
        # Continue with registration flow
    
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
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                signatures_dir = os.path.join(upload_folder, 'signatures')
                os.makedirs(signatures_dir, exist_ok=True)
                signature_path = os.path.join(signatures_dir, filename)
                
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

