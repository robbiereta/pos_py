import os
import sys

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

def lambda_handler(event, context):
    return app(event, context)
