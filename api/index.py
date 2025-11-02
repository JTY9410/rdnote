from app import create_app
import os

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

app = create_app()

# Export for Vercel serverless
if __name__ == '__main__':
    app.run()

