from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models.research_note import ResearchNote, ResearchNoteMember
from app.models.file import File, FileTag
from app.models.folder import Folder
from app.models.download_history import DownloadHistory
from app.models.system_settings import SystemSettings
from app.utils.auth import log_audit
from datetime import datetime
import os

export_bp = Blueprint('export', __name__)

# Check if WeasyPrint is available
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint not available: {e}")

@export_bp.route('/notes/<int:note_id>/exports', methods=['GET'])
@login_required
def list_exports(note_id):
    """Return recent 20 PDF export records for a note (derived status=done)."""
    note = ResearchNote.query.get_or_404(note_id)
    # permission check (any role that can access note)
    from app.utils.permissions import can_access_note
    if not can_access_note(current_user.id, note_id):
        return {'error': 'Permission denied'}, 403
    items = DownloadHistory.query.filter_by(note_id=note_id, download_type='PDF_EXPORT') \
        .order_by(DownloadHistory.created_at.desc()).limit(20).all()
    return {
        'items': [
            {
                'id': it.id,
                'note_id': it.note_id,
                'status': 'done',  # derived as export is synchronous
                'created_at': it.created_at.isoformat()
            } for it in items
        ]
    }

@export_bp.route('/notes/<int:note_id>/export/pdf', methods=['GET'])
@login_required
def pdf(note_id):
    if not WEASYPRINT_AVAILABLE:
        flash('PDF export is temporarily unavailable. Please contact administrator.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    from app.models.user import User
    from app.models.audit_log import AuditLog
    
    note = ResearchNote.query.get_or_404(note_id)
    
    # Check download permission
    note_role = db.session.query(ResearchNoteMember.role).filter_by(
        note_id=note_id, user_id=current_user.id
    ).scalar()
    
    if note_role != 'OWNER':
        # Check if non-owner can download
        if not note.allow_member_download:
            flash('Download denied.', 'error')
            return redirect(url_for('notes.detail', note_id=note_id))
        
        # Check daily limit
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_downloads = DownloadHistory.query.filter(
            DownloadHistory.user_id == current_user.id,
            DownloadHistory.created_at >= today_start
        ).count()
        
        daily_limit = int(SystemSettings.get('daily_download_limit', '100'))
        
        if today_downloads >= daily_limit:
            flash('Daily download limit reached.', 'error')
            return redirect(url_for('notes.detail', note_id=note_id))
    
    # Get all data for PDF
    folders = Folder.query.filter_by(note_id=note_id, deleted_at=None).order_by(Folder.order_index).all()
    
    # Get files with all versions, order by folder and created_date
    files = File.query.filter_by(note_id=note_id, is_deleted=False).order_by(File.folder_id, File.created_date, File.version_number).all()
    
    # tags_list는 File 모델의 @property로 제공됨
    
    members = ResearchNoteMember.query.filter_by(note_id=note_id).all()
    audit_logs = AuditLog.query.filter_by(note_id=note_id).order_by(AuditLog.created_at.desc()).limit(50).all()
    download_history = DownloadHistory.query.filter_by(note_id=note_id).order_by(DownloadHistory.created_at.desc()).limit(20).all()
    
    # Get owner and reviewer
    owner = User.query.get(note.owner_user_id)
    reviewer = User.query.get(note.reviewer_user_id) if note.reviewer_user_id else None
    
    # Prepare signature image paths for PDF
    owner_signature_url = None
    reviewer_signature_url = None
    
    if owner and owner.signature_path:
        # Convert signature path to absolute file path for WeasyPrint
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.isabs(upload_folder):
            if os.path.exists('/app'):
                upload_folder = os.path.join('/app', upload_folder)
            else:
                upload_folder = os.path.join(current_app.root_path, '..', upload_folder)
                upload_folder = os.path.abspath(upload_folder)
        
        # signature_path might be relative or absolute
        if os.path.isabs(owner.signature_path):
            owner_sig_path = owner.signature_path
        else:
            # Remove 'uploads/' prefix if present
            sig_rel_path = owner.signature_path.replace('uploads/', '').replace('signatures/', '')
            owner_sig_path = os.path.join(upload_folder, 'signatures', sig_rel_path)
        
        if os.path.exists(owner_sig_path):
            owner_signature_url = f"file://{owner_sig_path}"
    
    if reviewer and reviewer.signature_path:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.isabs(upload_folder):
            if os.path.exists('/app'):
                upload_folder = os.path.join('/app', upload_folder)
            else:
                upload_folder = os.path.join(current_app.root_path, '..', upload_folder)
                upload_folder = os.path.abspath(upload_folder)
        
        # signature_path might be relative or absolute
        if os.path.isabs(reviewer.signature_path):
            reviewer_sig_path = reviewer.signature_path
        else:
            # Remove 'uploads/' prefix if present
            sig_rel_path = reviewer.signature_path.replace('uploads/', '').replace('signatures/', '')
            reviewer_sig_path = os.path.join(upload_folder, 'signatures', sig_rel_path)
        
        if os.path.exists(reviewer_sig_path):
            reviewer_signature_url = f"file://{reviewer_sig_path}"
    
    # Render template
    html = render_template('export_pdf.html',
                          note=note,
                          folders=folders,
                          files=files,
                          members=members,
                          audit_logs=audit_logs,
                          download_history=download_history,
                          owner=owner,
                          reviewer=reviewer,
                          current_user=current_user,
                          export_date=datetime.utcnow(),
                          owner_signature_url=owner_signature_url,
                          reviewer_signature_url=reviewer_signature_url)
    
    # Generate PDF
    export_folder = current_app.config.get('EXPORT_FOLDER', 'exports')
    # Ensure absolute path
    if not os.path.isabs(export_folder):
        # In Docker, files are in /app, so resolve relative to /app
        # For local development, use app root
        if os.path.exists('/app'):
            export_folder = os.path.join('/app', export_folder)
        else:
            export_folder = os.path.join(current_app.root_path, '..', export_folder)
            export_folder = os.path.abspath(export_folder)
    os.makedirs(export_folder, exist_ok=True)
    pdf_filename = f"note_{note_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(export_folder, pdf_filename)
    
    try:
        HTML(string=html).write_pdf(pdf_path)
    except Exception as e:
        # Fallback to ReportLab simple PDF if WeasyPrint fails (version mismatch etc.)
        current_app.logger.warning(f"WeasyPrint failed, using ReportLab fallback: {e}")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            c = canvas.Canvas(pdf_path, pagesize=A4)
            W, H = A4
            c.setFont("Helvetica-Bold", 16)
            c.drawString(20*mm, H-20*mm, f"{note.title} (노트 ID: {note.id})")
            c.setFont("Helvetica", 11)
            meta_lines = [
                f"OWNER: {owner.name if owner else '-'}",
                f"REVIEWER: {reviewer.name if reviewer else '-'}",
                f"기간: {(note.start_date.strftime('%Y-%m-%d') if note.start_date else '-')}",
                f" ~ {(note.end_date.strftime('%Y-%m-%d') if note.end_date else '-')}",
                f"파일 수: {len(files)}",
                f"생성: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            ]
            y = H-30*mm
            for line in meta_lines:
                c.drawString(20*mm, y, line)
                y -= 7*mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20*mm, y-5*mm, "파일 목록")
            y -= 15*mm
            c.setFont("Helvetica", 10)
            for f in files:
                row = f"- {f.display_name}  v{f.version_number}  ({(f.created_date.strftime('%Y-%m-%d') if f.created_date else '-')})"
                c.drawString(20*mm, y, row)
                y -= 6*mm
                if y < 20*mm:
                    c.showPage(); y = H-20*mm; c.setFont("Helvetica", 10)
            c.save()
        except Exception as fallback_error:
            current_app.logger.error(f"ReportLab fallback also failed: {fallback_error}")
            raise
    
    # Verify PDF file was created
    if not os.path.exists(pdf_path):
        current_app.logger.error(f"PDF file was not created at {pdf_path}")
        flash('PDF 생성에 실패했습니다.', 'error')
        return redirect(url_for('notes.detail', note_id=note_id))
    
    # Record download
    download_history_record = DownloadHistory(
        note_id=note_id,
        file_id=None,
        user_id=current_user.id,
        download_type='PDF_EXPORT'
    )
    db.session.add(download_history_record)
    db.session.commit()
    
    log_audit(current_user.id, 'NOTE_PDF_EXPORT', note_id=note_id,
              meta_json={'note_id': note_id, 'user_id': current_user.id})
    
    return send_file(pdf_path, as_attachment=True, download_name=f"{note.title}.pdf")
