from app import create_app
import os

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Create Flask app instance
app = create_app()

# Vercel automatically detects WSGI apps exported as 'app'

