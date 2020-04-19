#Separate module to run Flask application with Gunicorn
from api import create_app
API_app = create_app()