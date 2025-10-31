from flask import Blueprint, request, jsonify
import hmac
import hashlib
import os

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.post('/webhooks/github')
def github_webhook():
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
    signature = request.headers.get('X-Hub-Signature-256', '')
    body = request.get_data() or b''
    calc = 'sha256=' + hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, signature or ''):
        return jsonify({'error': 'Bad signature'}), 401
    # Optionally record event
    return jsonify({'accepted': True}), 202
