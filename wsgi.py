"""
WSGI Entry Point for ORBCOMM Service Tracker
Production server configuration using Gunicorn
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Import the Flask application
from orbcomm_dashboard import app

# Application callable for WSGI server
application = app

if __name__ == "__main__":
    # This block is used for development/debugging only
    # In production, use gunicorn to run this file
    app.run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_ENV") == "development",
    )
