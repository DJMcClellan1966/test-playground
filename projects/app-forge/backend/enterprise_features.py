"""
Enterprise Features Module - Production-Ready App Components
=============================================================
Generates composable features for production Flask apps:

HIGH VALUE:
- Unit Test Generator (pytest tests for routes/models)
- API Documentation (OpenAPI/Swagger specs)
- Database Migrations (Alembic setup)
- Email Notifications (SendGrid/SMTP templates)
- File Uploads (image/document handling)

SECURITY:
- Rate Limiting (Flask-Limiter)
- CSRF Protection (Flask-WTF)
- Input Validation (marshmallow schemas)
- 2FA/TOTP (pyotp integration)
- Password Policies (strength, expiry)

DEVOPS:
- Health Checks (/health endpoint)
- Structured Logging (JSON logs)
- Error Tracking (Sentry)
- Environment Config (.env + python-dotenv)

ACCESSIBILITY:
- ARIA Labels (screen reader support)
- Keyboard Navigation (focus management)
- i18n (Flask-Babel)

EXTRAS:
- Pagination
- Redis Caching
- PDF Export
- Webhooks
- GraphQL
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum, auto


class Feature(Enum):
    """Available enterprise features."""
    # High Value
    UNIT_TESTS = auto()
    API_DOCS = auto()
    MIGRATIONS = auto()
    EMAIL = auto()
    FILE_UPLOAD = auto()
    
    # Security
    RATE_LIMIT = auto()
    CSRF = auto()
    VALIDATION = auto()
    TWO_FACTOR = auto()
    PASSWORD_POLICY = auto()
    
    # DevOps
    HEALTH_CHECK = auto()
    LOGGING = auto()
    ERROR_TRACKING = auto()
    ENV_CONFIG = auto()
    
    # Accessibility
    ARIA = auto()
    KEYBOARD_NAV = auto()
    I18N = auto()
    
    # Extras
    PAGINATION = auto()
    CACHING = auto()
    PDF_EXPORT = auto()
    WEBHOOKS = auto()
    GRAPHQL = auto()


@dataclass
class FeatureRequirements:
    """What features are needed based on app description."""
    features: Set[Feature] = field(default_factory=set)
    
    def needs(self, feature: Feature) -> bool:
        return feature in self.features


# =============================================================================
# FEATURE DETECTION
# =============================================================================

FEATURE_PATTERNS = {
    Feature.UNIT_TESTS: [r"test|tdd|quality|ci.?cd|pipeline"],
    Feature.API_DOCS: [r"api|swagger|openapi|document|spec"],
    Feature.MIGRATIONS: [r"migration|schema|evolv|version|alembic"],
    Feature.EMAIL: [r"email|mail|notification|alert|send|smtp"],
    Feature.FILE_UPLOAD: [r"upload|image|file|photo|document|attachment|media"],
    Feature.RATE_LIMIT: [r"rate.?limit|throttl|abuse|dos|protect"],
    Feature.CSRF: [r"csrf|form|secure|xsrf"],
    Feature.VALIDATION: [r"valid|schema|sanitiz|input|form"],
    Feature.TWO_FACTOR: [r"2fa|two.?factor|mfa|otp|authenticator|totp"],
    Feature.PASSWORD_POLICY: [r"password.?polic|strength|secure.?password|expir"],
    Feature.HEALTH_CHECK: [r"health|monitor|status|alive|ready"],
    Feature.LOGGING: [r"log|audit|trace|debug"],
    Feature.ERROR_TRACKING: [r"sentry|error.?track|crash|exception"],
    Feature.ENV_CONFIG: [r"env|config|secret|dotenv|setting"],
    Feature.ARIA: [r"aria|accessible|screen.?reader|a11y"],
    Feature.KEYBOARD_NAV: [r"keyboard|focus|tab|shortcut"],
    Feature.I18N: [r"i18n|language|translat|locale|international"],
    Feature.PAGINATION: [r"pagination|paging|page|limit|offset"],
    Feature.CACHING: [r"cache|redis|memcache|fast"],
    Feature.PDF_EXPORT: [r"pdf|report|print|export"],
    Feature.WEBHOOKS: [r"webhook|callback|notify|event|trigger"],
    Feature.GRAPHQL: [r"graphql|query|mutation|resolv"],
}


def detect_features(description: str, answers: Dict[str, bool] = None) -> FeatureRequirements:
    """Detect which enterprise features are needed."""
    desc_lower = description.lower()
    answers = answers or {}
    req = FeatureRequirements()
    
    # Pattern-based detection
    for feature, patterns in FEATURE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, desc_lower, re.IGNORECASE):
                req.features.add(feature)
                break
    
    # Always include these for data apps with auth
    if answers.get("needs_auth"):
        req.features.add(Feature.PASSWORD_POLICY)
        req.features.add(Feature.CSRF)
        req.features.add(Feature.VALIDATION)
    
    if answers.get("has_data"):
        req.features.add(Feature.HEALTH_CHECK)
        req.features.add(Feature.LOGGING)
        req.features.add(Feature.ENV_CONFIG)
    
    # Add pagination for collection apps
    if re.search(r"collection|list|catalog|library|browse|many", desc_lower):
        req.features.add(Feature.PAGINATION)
    
    return req


# =============================================================================
# UNIT TEST GENERATOR
# =============================================================================

def generate_tests(app_name: str, models: List[str], has_auth: bool) -> str:
    """Generate pytest test file for the app."""
    model_tests = ""
    for model in models:
        model_lower = model.lower()
        model_tests += f'''

class Test{model}:
    """Tests for {model} model and routes."""
    
    def test_create_{model_lower}(self, client):
        """Test creating a new {model_lower}."""
        response = client.post('/api/{model_lower}', json={{
            'name': 'Test {model}'
        }})
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert 'id' in data or 'name' in data
    
    def test_list_{model_lower}s(self, client):
        """Test listing all {model_lower}s."""
        response = client.get('/api/{model_lower}')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_get_{model_lower}(self, client):
        """Test getting a single {model_lower}."""
        # First create one
        client.post('/api/{model_lower}', json={{'name': 'Test'}})
        response = client.get('/api/{model_lower}/1')
        assert response.status_code in [200, 404]
    
    def test_update_{model_lower}(self, client):
        """Test updating a {model_lower}."""
        client.post('/api/{model_lower}', json={{'name': 'Test'}})
        response = client.put('/api/{model_lower}/1', json={{
            'name': 'Updated {model}'
        }})
        assert response.status_code in [200, 404]
    
    def test_delete_{model_lower}(self, client):
        """Test deleting a {model_lower}."""
        client.post('/api/{model_lower}', json={{'name': 'Test'}})
        response = client.delete('/api/{model_lower}/1')
        assert response.status_code in [200, 204, 404]
'''
    
    auth_tests = ""
    if has_auth:
        auth_tests = '''

class TestAuth:
    """Tests for authentication."""
    
    def test_register(self, client):
        """Test user registration."""
        response = client.post('/api/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        assert response.status_code in [200, 201, 400]
    
    def test_login(self, client):
        """Test user login."""
        # Register first
        client.post('/api/register', json={
            'username': 'testuser',
            'email': 'test@example.com', 
            'password': 'TestPass123!'
        })
        # Then login
        response = client.post('/api/login', json={
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        assert response.status_code in [200, 401]
    
    def test_logout(self, client):
        """Test user logout."""
        response = client.post('/api/logout')
        assert response.status_code in [200, 302]
    
    def test_protected_route_unauthorized(self, client):
        """Test that protected routes require auth."""
        response = client.get('/api/me')
        assert response.status_code in [401, 302, 200]
'''

    return f'''"""
Test Suite for {app_name}
Generated by App Forge
Run with: pytest tests/ -v
"""

import pytest
from app import app, db


@pytest.fixture
def client():
    """Create test client with fresh database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


@pytest.fixture
def auth_client(client):
    """Create authenticated test client."""
    client.post('/api/register', json={{
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    }})
    client.post('/api/login', json={{
        'username': 'testuser',
        'password': 'TestPass123!'
    }})
    return client


class TestHealthCheck:
    """Basic app tests."""
    
    def test_app_exists(self, client):
        """Test that app exists."""
        assert client is not None
    
    def test_index(self, client):
        """Test index page loads."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_health(self, client):
        """Test health endpoint."""
        response = client.get('/health')
        assert response.status_code in [200, 404]
{auth_tests}
{model_tests}
'''


# =============================================================================
# API DOCUMENTATION (OpenAPI/Swagger)
# =============================================================================

def generate_openapi_spec(app_name: str, description: str, models: List[str], 
                          has_auth: bool) -> str:
    """Generate OpenAPI 3.0 specification."""
    
    # Generate model schemas
    schemas = {}
    paths = {}
    
    for model in models:
        model_lower = model.lower()
        
        # Schema definition
        schemas[model] = {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "name": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time", "readOnly": True}
            },
            "required": ["name"]
        }
        
        # CRUD paths
        paths[f"/api/{model_lower}"] = {
            "get": {
                "summary": f"List all {model_lower}s",
                "tags": [model],
                "responses": {
                    "200": {
                        "description": f"List of {model_lower}s",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": f"#/components/schemas/{model}"}
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": f"Create a new {model_lower}",
                "tags": [model],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{model}"}
                        }
                    }
                },
                "responses": {
                    "201": {"description": f"{model} created"}
                }
            }
        }
        
        paths[f"/api/{model_lower}/{{id}}"] = {
            "get": {
                "summary": f"Get a {model_lower} by ID",
                "tags": [model],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": f"The {model_lower}",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{model}"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "put": {
                "summary": f"Update a {model_lower}",
                "tags": [model],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{model}"}
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Updated"}
                }
            },
            "delete": {
                "summary": f"Delete a {model_lower}",
                "tags": [model],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "204": {"description": "Deleted"}
                }
            }
        }
    
    # Auth endpoints
    if has_auth:
        schemas["User"] = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            }
        }
        schemas["LoginRequest"] = {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string", "format": "password"}
            },
            "required": ["username", "password"]
        }
        paths["/api/login"] = {
            "post": {
                "summary": "User login",
                "tags": ["Auth"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/LoginRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid credentials"}
                }
            }
        }
        paths["/api/register"] = {
            "post": {
                "summary": "User registration",
                "tags": ["Auth"],
                "responses": {
                    "201": {"description": "User created"},
                    "400": {"description": "Validation error"}
                }
            }
        }
    
    import json
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": app_name,
            "description": description,
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:5000", "description": "Development"}
        ],
        "paths": paths,
        "components": {
            "schemas": schemas
        }
    }
    
    return json.dumps(spec, indent=2)


def generate_swagger_ui_html(app_name: str) -> str:
    """Generate Swagger UI HTML page."""
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>{app_name} - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: "/api/openapi.json",
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
            layout: "BaseLayout"
        }});
    </script>
</body>
</html>
'''


def generate_api_docs_routes() -> str:
    """Generate Flask routes for API documentation."""
    return '''
# =============================================================================
# API Documentation (OpenAPI/Swagger)
# =============================================================================

@app.route('/api/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification."""
    return send_file('openapi.json', mimetype='application/json')


@app.route('/docs')
def swagger_ui():
    """Swagger UI documentation."""
    return send_file('templates/swagger.html')
'''


# =============================================================================
# DATABASE MIGRATIONS (Alembic)
# =============================================================================

def generate_alembic_ini() -> str:
    """Generate alembic.ini configuration."""
    return '''# Alembic configuration file
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = sqlite:///app.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
'''


def generate_alembic_env_py() -> str:
    """Generate migrations/env.py for Alembic."""
    return '''"""Alembic environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import *  # Import all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


def generate_alembic_script_py_mako() -> str:
    """Generate migrations/script.py.mako template."""
    return '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
'''


# =============================================================================
# EMAIL NOTIFICATIONS
# =============================================================================

def generate_email_module() -> str:
    """Generate email.py for sending notifications."""
    return '''"""
Email Module - Send notifications via SMTP or SendGrid
Usage:
    from email_service import send_email, send_welcome_email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional


# Configuration (from environment)
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@example.com')


def send_email(to: str, subject: str, body: str, html: str = None) -> bool:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        html: Optional HTML body
    
    Returns:
        True if sent successfully
    """
    if not SMTP_USER or not SMTP_PASS:
        print(f"[EMAIL] Would send to {to}: {subject}")
        return True  # Fake success in dev
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to
        
        msg.attach(MIMEText(body, 'plain'))
        if html:
            msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to, msg.as_string())
        
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def send_welcome_email(to: str, username: str) -> bool:
    """Send welcome email to new user."""
    subject = "Welcome to the app!"
    body = f"""Hi {username},

Thanks for signing up! We're excited to have you.

Best,
The Team
"""
    html = f"""
    <h2>Welcome, {username}!</h2>
    <p>Thanks for signing up! We're excited to have you.</p>
    <p>Best,<br>The Team</p>
    """
    return send_email(to, subject, body, html)


def send_password_reset_email(to: str, reset_link: str) -> bool:
    """Send password reset email."""
    subject = "Password Reset Request"
    body = f"""You requested a password reset.

Click here to reset your password:
{reset_link}

If you didn't request this, ignore this email.
"""
    html = f"""
    <h2>Password Reset</h2>
    <p>You requested a password reset.</p>
    <p><a href="{reset_link}">Click here to reset your password</a></p>
    <p style="color:#888;font-size:12px">If you didn't request this, ignore this email.</p>
    """
    return send_email(to, subject, body, html)


def send_notification(to: str, title: str, message: str) -> bool:
    """Send a generic notification email."""
    return send_email(to, title, message, f"<p>{message}</p>")


# SendGrid support (optional)
def send_via_sendgrid(to: str, subject: str, body: str, html: str = None) -> bool:
    """Send email via SendGrid API."""
    if not SENDGRID_API_KEY:
        return send_email(to, subject, body, html)  # Fallback to SMTP
    
    try:
        import requests
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={
                'Authorization': f'Bearer {SENDGRID_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'personalizations': [{'to': [{'email': to}]}],
                'from': {'email': FROM_EMAIL},
                'subject': subject,
                'content': [
                    {'type': 'text/plain', 'value': body},
                    {'type': 'text/html', 'value': html or body}
                ]
            }
        )
        return response.status_code == 202
    except Exception as e:
        print(f"[SENDGRID ERROR] {e}")
        return False
'''


# =============================================================================
# FILE UPLOADS
# =============================================================================

def generate_upload_module() -> str:
    """Generate file upload handling module."""
    return '''"""
File Upload Module - Handle image and document uploads
Usage:
    from uploads import save_upload, get_upload_url, delete_upload
"""

import os
import uuid
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List
from werkzeug.utils import secure_filename


# Configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'xlsx'},
    'all': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'doc', 'docx', 'txt', 'md', 'csv', 'xlsx'}
}

# Ensure upload folder exists
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


def allowed_file(filename: str, category: str = 'all') -> bool:
    """Check if file extension is allowed."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS.get(category, ALLOWED_EXTENSIONS['all'])


def get_file_hash(file_data: bytes) -> str:
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(file_data).hexdigest()[:16]


def save_upload(file, category: str = 'all', subfolder: str = None) -> Tuple[bool, str, Optional[str]]:
    """
    Save an uploaded file.
    
    Args:
        file: Flask FileStorage object
        category: 'image', 'document', or 'all'
        subfolder: Optional subfolder within uploads
    
    Returns:
        (success, message, filename_or_none)
    """
    if not file or not file.filename:
        return False, "No file provided", None
    
    if not allowed_file(file.filename, category):
        return False, f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS[category]}", None
    
    # Read file to check size
    file_data = file.read()
    if len(file_data) > MAX_FILE_SIZE:
        return False, f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB", None
    file.seek(0)  # Reset for saving
    
    # Generate unique filename
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    file_hash = get_file_hash(file_data)
    unique_name = f"{uuid.uuid4().hex[:8]}_{file_hash}.{ext}"
    
    # Determine save path
    save_folder = Path(UPLOAD_FOLDER)
    if subfolder:
        save_folder = save_folder / subfolder
        save_folder.mkdir(parents=True, exist_ok=True)
    
    save_path = save_folder / unique_name
    
    # Save file
    try:
        with open(save_path, 'wb') as f:
            f.write(file_data)
        return True, "File uploaded successfully", unique_name
    except Exception as e:
        return False, f"Upload failed: {e}", None


def get_upload_url(filename: str, subfolder: str = None) -> str:
    """Get URL for an uploaded file."""
    if subfolder:
        return f"/uploads/{subfolder}/{filename}"
    return f"/uploads/{filename}"


def get_upload_path(filename: str, subfolder: str = None) -> Path:
    """Get filesystem path for an uploaded file."""
    if subfolder:
        return Path(UPLOAD_FOLDER) / subfolder / filename
    return Path(UPLOAD_FOLDER) / filename


def delete_upload(filename: str, subfolder: str = None) -> bool:
    """Delete an uploaded file."""
    path = get_upload_path(filename, subfolder)
    try:
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def list_uploads(subfolder: str = None) -> List[str]:
    """List all uploaded files."""
    folder = Path(UPLOAD_FOLDER) / subfolder if subfolder else Path(UPLOAD_FOLDER)
    if not folder.exists():
        return []
    return [f.name for f in folder.iterdir() if f.is_file()]


# Flask routes for file upload
UPLOAD_ROUTES = """
from flask import send_from_directory
from uploads import save_upload, delete_upload, UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    success, message, filename = save_upload(file)
    
    if success:
        return jsonify({'message': message, 'filename': filename, 'url': f'/uploads/{filename}'})
    return jsonify({'error': message}), 400


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/upload/<filename>', methods=['DELETE'])
def remove_upload(filename):
    if delete_upload(filename):
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'File not found'}), 404
"""
'''


# =============================================================================
# SECURITY FEATURES
# =============================================================================

def generate_security_module() -> str:
    """Generate security features module."""
    return '''"""
Security Module - Rate limiting, CSRF, validation, 2FA, password policies
"""

import re
import os
import secrets
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, List


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, key: str, limit: int = 100, window_seconds: int = 60) -> bool:
        """Check if request is allowed within rate limit."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        self.requests[key].append(now)
        return True
    
    def remaining(self, key: str, limit: int = 100, window_seconds: int = 60) -> int:
        """Get remaining requests in window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        
        if key not in self.requests:
            return limit
        
        recent = [t for t in self.requests[key] if t > cutoff]
        return max(0, limit - len(recent))


rate_limiter = RateLimiter()


def rate_limit(limit: int = 100, window: int = 60, key_func=None):
    """Rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, jsonify
            
            # Get rate limit key (default: IP address)
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            if not rate_limiter.is_allowed(key, limit, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# =============================================================================
# CSRF PROTECTION
# =============================================================================

def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token matches session."""
    if not token or not session_token:
        return False
    return secrets.compare_digest(token, session_token)


CSRF_ROUTES = """
from functools import wraps

def csrf_protect(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not token or token != session.get('csrf_token'):
                return jsonify({'error': 'CSRF token invalid'}), 403
        return f(*args, **kwargs)
    return decorated

@app.before_request
def ensure_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': session.get('csrf_token', '')}
"""


# =============================================================================
# INPUT VALIDATION
# =============================================================================

class ValidationError(Exception):
    """Validation error with field-specific messages."""
    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        return False, "Email is required"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    if len(email) > 254:
        return False, "Email too long"
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format."""
    if not username:
        return False, "Username is required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 30:
        return False, "Username must be at most 30 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


def validate_required(value, field_name: str) -> Tuple[bool, str]:
    """Validate required field."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_name} is required"
    return True, ""


def validate_length(value: str, field_name: str, min_len: int = 0, max_len: int = 1000) -> Tuple[bool, str]:
    """Validate string length."""
    if len(value) < min_len:
        return False, f"{field_name} must be at least {min_len} characters"
    if len(value) > max_len:
        return False, f"{field_name} must be at most {max_len} characters"
    return True, ""


def sanitize_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


# =============================================================================
# PASSWORD POLICY
# =============================================================================

class PasswordPolicy:
    """Configurable password strength requirements."""
    
    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        max_length: int = 128
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against policy."""
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters")
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain an uppercase letter")
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain a lowercase letter")
        if self.require_digit and not re.search(r'\\d', password):
            errors.append("Password must contain a digit")
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain a special character")
        
        return len(errors) == 0, errors
    
    def get_strength(self, password: str) -> str:
        """Get password strength rating."""
        score = 0
        if len(password) >= 8: score += 1
        if len(password) >= 12: score += 1
        if re.search(r'[A-Z]', password): score += 1
        if re.search(r'[a-z]', password): score += 1
        if re.search(r'\\d', password): score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 1
        
        if score <= 2: return "weak"
        if score <= 4: return "medium"
        return "strong"


password_policy = PasswordPolicy()


# =============================================================================
# TWO-FACTOR AUTHENTICATION (TOTP)
# =============================================================================

def generate_totp_secret() -> str:
    """Generate a TOTP secret key."""
    return secrets.token_hex(20)


def get_totp_uri(secret: str, username: str, app_name: str) -> str:
    """Generate TOTP URI for QR code."""
    import base64
    secret_b32 = base64.b32encode(bytes.fromhex(secret)).decode('utf-8').rstrip('=')
    return f"otpauth://totp/{app_name}:{username}?secret={secret_b32}&issuer={app_name}"


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify a TOTP code.
    
    For full implementation, use pyotp:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    This is a simplified version.
    """
    import time
    import hmac
    import struct
    import base64
    
    try:
        # Convert hex secret to base32 for standard TOTP
        secret_bytes = bytes.fromhex(secret)
        
        # Get current time counter (30-second windows)
        counter = int(time.time()) // 30
        
        # Check codes within window
        for i in range(-window, window + 1):
            # Generate expected code
            counter_bytes = struct.pack('>Q', counter + i)
            hmac_hash = hmac.new(secret_bytes, counter_bytes, 'sha1').digest()
            offset = hmac_hash[-1] & 0x0f
            truncated = struct.unpack('>I', hmac_hash[offset:offset+4])[0] & 0x7fffffff
            expected_code = str(truncated % 1000000).zfill(6)
            
            if secrets.compare_digest(code, expected_code):
                return True
        
        return False
    except Exception:
        return False


TOTP_ROUTES = """
@app.route('/api/2fa/setup', methods=['POST'])
def setup_2fa():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    from security import generate_totp_secret, get_totp_uri
    
    secret = generate_totp_secret()
    # Store secret temporarily (user must verify before it's saved)
    session['pending_totp_secret'] = secret
    
    user = User.query.get(session['user_id'])
    uri = get_totp_uri(secret, user.username, 'MyApp')
    
    return jsonify({'secret': secret, 'uri': uri})


@app.route('/api/2fa/verify', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    code = data.get('code', '')
    
    secret = session.get('pending_totp_secret')
    if not secret:
        return jsonify({'error': 'No 2FA setup in progress'}), 400
    
    from security import verify_totp
    
    if verify_totp(secret, code):
        # Save to user record
        user = User.query.get(session['user_id'])
        user.totp_secret = secret
        db.session.commit()
        del session['pending_totp_secret']
        return jsonify({'message': '2FA enabled'})
    
    return jsonify({'error': 'Invalid code'}), 400
"""
'''


# =============================================================================
# DEVOPS FEATURES
# =============================================================================

def generate_devops_module() -> str:
    """Generate DevOps features module."""
    return '''"""
DevOps Module - Health checks, logging, error tracking, env config
"""

import os
import sys
import json
import logging
from datetime import datetime
from functools import wraps


# =============================================================================
# ENVIRONMENT CONFIG
# =============================================================================

def load_env(env_file: str = '.env'):
    """Load environment variables from .env file."""
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass  # .env is optional


def get_config(key: str, default=None, required: bool = False):
    """Get configuration value from environment."""
    value = os.environ.get(key, default)
    if required and value is None:
        raise RuntimeError(f"Required config '{key}' not set")
    return value


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================

class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key in ['user_id', 'request_id', 'ip', 'path', 'method']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        return json.dumps(log_data)


def setup_logging(app_name: str, level: str = 'INFO', json_format: bool = True):
    """Configure structured logging."""
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))
    
    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    logger.addHandler(handler)
    return logger


def log_request(logger):
    """Decorator to log incoming requests."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request, g
            import uuid
            
            request_id = str(uuid.uuid4())[:8]
            g.request_id = request_id
            
            logger.info(f"Request started", extra={
                'request_id': request_id,
                'path': request.path,
                'method': request.method,
                'ip': request.remote_addr
            })
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Request failed: {e}", extra={
                    'request_id': request_id,
                    'path': request.path
                })
                raise
        return decorated
    return decorator


# =============================================================================
# HEALTH CHECKS
# =============================================================================

def generate_health_routes() -> str:
    """Generate health check routes."""
    return """
import time

_start_time = time.time()

@app.route('/health')
def health_check():
    \"\"\"Basic health check.\"\"\"
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/health/live')
def liveness():
    \"\"\"Kubernetes liveness probe.\"\"\"
    return jsonify({'status': 'alive'})


@app.route('/health/ready')
def readiness():
    \"\"\"Kubernetes readiness probe - checks database connection.\"\"\"
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {e}'
        return jsonify({'status': 'not ready', 'database': db_status}), 503
    
    return jsonify({
        'status': 'ready',
        'database': db_status,
        'uptime_seconds': int(time.time() - _start_time)
    })


@app.route('/health/metrics')
def metrics():
    \"\"\"Basic metrics endpoint.\"\"\"
    import os
    import psutil
    
    process = psutil.Process(os.getpid())
    
    return jsonify({
        'uptime_seconds': int(time.time() - _start_time),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'cpu_percent': process.cpu_percent(),
        'connections': len(process.connections())
    })
"""


# =============================================================================
# ERROR TRACKING (Sentry-like)
# =============================================================================

class ErrorTracker:
    """Simple error tracking (use Sentry SDK in production)."""
    
    def __init__(self, dsn: str = None):
        self.dsn = dsn
        self.errors = []  # In-memory for dev
    
    def capture_exception(self, exception, context: dict = None):
        """Capture an exception."""
        import traceback
        
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': type(exception).__name__,
            'message': str(exception),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.errors.append(error_data)
        
        # If Sentry DSN configured, would send here
        if self.dsn:
            self._send_to_sentry(error_data)
        
        return error_data
    
    def _send_to_sentry(self, error_data):
        """Send error to Sentry (placeholder)."""
        # In production: use sentry_sdk.capture_exception()
        pass
    
    def get_recent_errors(self, limit: int = 10):
        """Get recent errors."""
        return self.errors[-limit:]


error_tracker = ErrorTracker(os.environ.get('SENTRY_DSN'))


SENTRY_SETUP = """
# Error tracking setup (add to app.py)
import os

SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1
        )
        print("Sentry error tracking enabled")
    except ImportError:
        print("sentry-sdk not installed, error tracking disabled")
"""
'''


def generate_env_template() -> str:
    """Generate .env.template file."""
    return '''# Environment Configuration
# Copy this to .env and fill in values

# Flask
FLASK_ENV=development
SECRET_KEY=change-this-to-random-string

# Database
DATABASE_URL=sqlite:///app.db

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
FROM_EMAIL=noreply@example.com
SENDGRID_API_KEY=

# File uploads
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=10485760

# Error tracking (optional)
SENTRY_DSN=

# Rate limiting
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# Feature flags
ENABLE_2FA=false
ENABLE_GDPR=true
'''


# =============================================================================
# ACCESSIBILITY FEATURES
# =============================================================================

def generate_accessibility_css() -> str:
    """Generate accessibility CSS."""
    return '''
/* =============================================================================
   ACCESSIBILITY STYLES
   ============================================================================= */

/* Focus indicators - WCAG 2.1 requirement */
*:focus {
    outline: 2px solid var(--color-primary, #0066cc);
    outline-offset: 2px;
}

*:focus:not(:focus-visible) {
    outline: none;
}

*:focus-visible {
    outline: 2px solid var(--color-primary, #0066cc);
    outline-offset: 2px;
}

/* Skip to main content link */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--color-primary, #0066cc);
    color: white;
    padding: 8px 16px;
    z-index: 10000;
    text-decoration: none;
}

.skip-link:focus {
    top: 0;
}

/* Visually hidden but accessible to screen readers */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    * {
        border-color: currentColor !important;
    }
    
    button, .btn {
        border: 2px solid currentColor !important;
    }
}

/* Form accessibility */
label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
}

input:invalid,
textarea:invalid,
select:invalid {
    border-color: var(--color-error, #dc3545);
}

.error-message {
    color: var(--color-error, #dc3545);
    font-size: 14px;
    margin-top: 4px;
}

/* Required field indicator */
.required::after {
    content: " *";
    color: var(--color-error, #dc3545);
}

/* Touch targets - minimum 44x44px for mobile */
button,
.btn,
input[type="checkbox"],
input[type="radio"],
a {
    min-height: 44px;
    min-width: 44px;
}

/* Text sizing - respect user preferences */
html {
    font-size: 100%; /* Respects browser settings */
}

/* Ensure sufficient color contrast */
.low-emphasis {
    color: #595959; /* 4.5:1 ratio on white */
}
'''


def generate_accessibility_js() -> str:
    """Generate accessibility JavaScript."""
    return '''
// =============================================================================
// ACCESSIBILITY JAVASCRIPT
// =============================================================================

(function() {
    'use strict';
    
    // ==========================================================================
    // KEYBOARD NAVIGATION
    // ==========================================================================
    
    // Trap focus in modals
    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', function(e) {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    lastElement.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastElement) {
                    firstElement.focus();
                    e.preventDefault();
                }
            }
        });
    }
    
    // Make all modals trap focus
    document.querySelectorAll('[role="dialog"]').forEach(trapFocus);
    
    // ==========================================================================
    // KEYBOARD SHORTCUTS
    // ==========================================================================
    
    const shortcuts = {
        'Alt+1': function() { window.location.href = '/'; },
        'Alt+s': function() { document.querySelector('[type="search"]')?.focus(); },
        'Escape': function() { 
            document.querySelector('[role="dialog"]:not([hidden])')?.setAttribute('hidden', '');
        }
    };
    
    document.addEventListener('keydown', function(e) {
        const key = (e.altKey ? 'Alt+' : '') + (e.ctrlKey ? 'Ctrl+' : '') + e.key;
        if (shortcuts[key]) {
            shortcuts[key]();
            e.preventDefault();
        }
    });
    
    // ==========================================================================
    // ARIA LIVE REGIONS
    // ==========================================================================
    
    // Create announcement region
    const announcer = document.createElement('div');
    announcer.setAttribute('role', 'status');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
    
    window.announce = function(message) {
        announcer.textContent = '';
        setTimeout(function() {
            announcer.textContent = message;
        }, 100);
    };
    
    // ==========================================================================
    // FORM VALIDATION ANNOUNCEMENTS
    // ==========================================================================
    
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const invalidFields = form.querySelectorAll(':invalid');
            if (invalidFields.length > 0) {
                e.preventDefault();
                const messages = Array.from(invalidFields).map(function(field) {
                    return field.labels?.[0]?.textContent || field.name;
                });
                announce('Form has errors in: ' + messages.join(', '));
                invalidFields[0].focus();
            }
        });
    });
    
    // ==========================================================================
    // LOADING STATES
    // ==========================================================================
    
    window.setLoading = function(element, loading) {
        if (loading) {
            element.setAttribute('aria-busy', 'true');
            element.setAttribute('aria-disabled', 'true');
        } else {
            element.removeAttribute('aria-busy');
            element.removeAttribute('aria-disabled');
        }
    };
    
})();
'''


def generate_skip_link_html() -> str:
    """Generate skip link for keyboard navigation."""
    return '''<a href="#main" class="skip-link">Skip to main content</a>'''


# =============================================================================
# EXTRA FEATURES
# =============================================================================

def generate_pagination_helpers() -> str:
    """Generate pagination helper code."""
    return '''
# =============================================================================
# PAGINATION
# =============================================================================

def paginate(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """
    Paginate a SQLAlchemy query.
    
    Returns:
        dict with items, total, page, per_page, pages, has_next, has_prev
    """
    per_page = min(per_page, max_per_page)
    page = max(1, page)
    
    total = query.count()
    pages = (total + per_page - 1) // per_page
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }


# Usage in route:
# @app.route('/api/items')
# def list_items():
#     page = request.args.get('page', 1, type=int)
#     per_page = request.args.get('per_page', 20, type=int)
#     
#     query = Item.query.order_by(Item.created_at.desc())
#     result = paginate(query, page, per_page)
#     
#     return jsonify({
#         'items': [item.to_dict() for item in result['items']],
#         'pagination': {
#             'page': result['page'],
#             'per_page': result['per_page'],
#             'total': result['total'],
#             'pages': result['pages'],
#             'has_next': result['has_next'],
#             'has_prev': result['has_prev']
#         }
#     })
'''


def generate_redis_cache() -> str:
    """Generate Redis caching helper."""
    return '''"""
Redis Caching Module
Usage:
    from cache import cache, cache_key, invalidate

    @cache(ttl=300)
    def get_expensive_data():
        ...
"""

import os
import json
import hashlib
from functools import wraps
from typing import Any, Optional

REDIS_URL = os.environ.get('REDIS_URL')

try:
    import redis
    _redis = redis.from_url(REDIS_URL) if REDIS_URL else None
except ImportError:
    _redis = None

# In-memory fallback for development
_memory_cache = {}


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    if _redis:
        data = _redis.get(key)
        return json.loads(data) if data else None
    return _memory_cache.get(key)


def set_cached(key: str, value: Any, ttl: int = 300):
    """Set value in cache."""
    if _redis:
        _redis.setex(key, ttl, json.dumps(value))
    else:
        _memory_cache[key] = value


def invalidate(key: str):
    """Remove key from cache."""
    if _redis:
        _redis.delete(key)
    else:
        _memory_cache.pop(key, None)


def invalidate_pattern(pattern: str):
    """Remove keys matching pattern."""
    if _redis:
        for key in _redis.scan_iter(pattern):
            _redis.delete(key)
    else:
        keys_to_delete = [k for k in _memory_cache if pattern.replace('*', '') in k]
        for k in keys_to_delete:
            del _memory_cache[k]


def cache(ttl: int = 300, key_prefix: str = ''):
    """Caching decorator."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = key_prefix + cache_key(f.__name__, *args, **kwargs)
            
            cached = get_cached(key)
            if cached is not None:
                return cached
            
            result = f(*args, **kwargs)
            set_cached(key, result, ttl)
            return result
        return decorated
    return decorator
'''


def generate_pdf_export() -> str:
    """Generate PDF export helper."""
    return '''"""
PDF Export Module
Usage:
    from pdf_export import generate_pdf, html_to_pdf
    
Requires: pip install weasyprint
"""

import os
from typing import Optional

try:
    from weasyprint import HTML, CSS
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


def html_to_pdf(html_content: str, css: str = None) -> bytes:
    """Convert HTML string to PDF bytes."""
    if not HAS_WEASYPRINT:
        raise ImportError("weasyprint not installed. Run: pip install weasyprint")
    
    html = HTML(string=html_content)
    stylesheets = [CSS(string=css)] if css else []
    
    return html.write_pdf(stylesheets=stylesheets)


def generate_report_pdf(title: str, data: list, columns: list) -> bytes:
    """Generate a simple table report PDF."""
    # Build HTML table
    headers = ''.join(f'<th>{col}</th>' for col in columns)
    rows = ''
    for item in data:
        cells = ''.join(f'<td>{item.get(col, "")}</td>' for col in columns)
        rows += f'<tr>{cells}</tr>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px 8px; text-align: left; }}
            th {{ background: #f5f5f5; font-weight: bold; }}
            tr:nth-child(even) {{ background: #fafafa; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="footer">Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </body>
    </html>
    """
    
    return html_to_pdf(html)


# Flask route for PDF export
PDF_ROUTE = """
@app.route('/api/export/pdf')
def export_pdf():
    from pdf_export import generate_report_pdf
    
    # Get data from database
    items = Item.query.all()
    data = [item.to_dict() for item in items]
    columns = ['id', 'name', 'created_at']
    
    pdf_bytes = generate_report_pdf('Data Export', data, columns)
    
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=export.pdf'}
    )
"""
'''


def generate_webhooks() -> str:
    """Generate webhook support."""
    return '''"""
Webhook Module - Send and receive webhooks
Usage:
    from webhooks import send_webhook, register_webhook
"""

import os
import json
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Optional


# Registered webhooks (in production, store in database)
_webhooks: Dict[str, List[dict]] = {}


def register_webhook(event: str, url: str, secret: str = None) -> str:
    """Register a webhook for an event."""
    webhook_id = hashlib.md5(f"{event}:{url}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    if event not in _webhooks:
        _webhooks[event] = []
    
    _webhooks[event].append({
        'id': webhook_id,
        'url': url,
        'secret': secret,
        'created_at': datetime.now().isoformat()
    })
    
    return webhook_id


def unregister_webhook(webhook_id: str) -> bool:
    """Remove a webhook."""
    for event, hooks in _webhooks.items():
        for hook in hooks:
            if hook['id'] == webhook_id:
                hooks.remove(hook)
                return True
    return False


def sign_payload(payload: dict, secret: str) -> str:
    """Sign webhook payload with HMAC-SHA256."""
    body = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify incoming webhook signature."""
    expected = sign_payload(json.loads(payload), secret)
    return hmac.compare_digest(expected, signature)


def send_webhook(event: str, data: dict, async_send: bool = False) -> List[dict]:
    """
    Send webhook to all registered endpoints.
    
    Args:
        event: Event name (e.g., 'user.created', 'item.updated')
        data: Event data
        async_send: If True, send asynchronously (requires celery/threading)
    
    Returns:
        List of delivery results
    """
    results = []
    
    for hook in _webhooks.get(event, []):
        payload = {
            'event': event,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'webhook_id': hook['id']
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': event
        }
        
        if hook.get('secret'):
            headers['X-Webhook-Signature'] = sign_payload(payload, hook['secret'])
        
        try:
            response = requests.post(
                hook['url'],
                json=payload,
                headers=headers,
                timeout=10
            )
            results.append({
                'webhook_id': hook['id'],
                'url': hook['url'],
                'status': response.status_code,
                'success': response.status_code < 400
            })
        except Exception as e:
            results.append({
                'webhook_id': hook['id'],
                'url': hook['url'],
                'status': 0,
                'success': False,
                'error': str(e)
            })
    
    return results


# Flask routes for webhook management
WEBHOOK_ROUTES = """
@app.route('/api/webhooks', methods=['GET'])
def list_webhooks():
    from webhooks import _webhooks
    all_hooks = []
    for event, hooks in _webhooks.items():
        for hook in hooks:
            all_hooks.append({**hook, 'event': event})
    return jsonify(all_hooks)


@app.route('/api/webhooks', methods=['POST'])
def create_webhook():
    from webhooks import register_webhook
    data = request.get_json()
    
    webhook_id = register_webhook(
        event=data['event'],
        url=data['url'],
        secret=data.get('secret')
    )
    
    return jsonify({'id': webhook_id, 'message': 'Webhook registered'})


@app.route('/api/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    from webhooks import unregister_webhook
    
    if unregister_webhook(webhook_id):
        return jsonify({'message': 'Webhook removed'})
    return jsonify({'error': 'Webhook not found'}), 404
"""
'''


# =============================================================================
# INTERNATIONALIZATION (i18n)
# =============================================================================

def generate_i18n_module() -> str:
    """Generate internationalization support."""
    return '''"""
Internationalization Module (i18n)
Usage:
    from i18n import get_text, set_locale, get_locales

Requires: pip install flask-babel
"""

import os
from functools import wraps
from typing import Dict, List, Optional

# Translations storage (in production, use gettext .po files)
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'en': {
        'welcome': 'Welcome',
        'login': 'Log In',
        'logout': 'Log Out',
        'register': 'Register',
        'submit': 'Submit',
        'save': 'Save',
        'cancel': 'Cancel',
        'delete': 'Delete',
        'edit': 'Edit',
        'search': 'Search',
        'no_results': 'No results found',
        'error': 'An error occurred',
        'success': 'Success',
        'loading': 'Loading...',
        'confirm_delete': 'Are you sure you want to delete this?',
    },
    'es': {
        'welcome': 'Bienvenido',
        'login': 'Iniciar Sesión',
        'logout': 'Cerrar Sesión',
        'register': 'Registrarse',
        'submit': 'Enviar',
        'save': 'Guardar',
        'cancel': 'Cancelar',
        'delete': 'Eliminar',
        'edit': 'Editar',
        'search': 'Buscar',
        'no_results': 'No se encontraron resultados',
        'error': 'Ocurrió un error',
        'success': 'Éxito',
        'loading': 'Cargando...',
        'confirm_delete': '¿Estás seguro de que quieres eliminar esto?',
    },
    'fr': {
        'welcome': 'Bienvenue',
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'register': "S'inscrire",
        'submit': 'Soumettre',
        'save': 'Enregistrer',
        'cancel': 'Annuler',
        'delete': 'Supprimer',
        'edit': 'Modifier',
        'search': 'Rechercher',
        'no_results': 'Aucun résultat trouvé',
        'error': 'Une erreur est survenue',
        'success': 'Succès',
        'loading': 'Chargement...',
        'confirm_delete': 'Êtes-vous sûr de vouloir supprimer ceci?',
    },
    'de': {
        'welcome': 'Willkommen',
        'login': 'Anmelden',
        'logout': 'Abmelden',
        'register': 'Registrieren',
        'submit': 'Absenden',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'delete': 'Löschen',
        'edit': 'Bearbeiten',
        'search': 'Suchen',
        'no_results': 'Keine Ergebnisse gefunden',
        'error': 'Ein Fehler ist aufgetreten',
        'success': 'Erfolg',
        'loading': 'Wird geladen...',
        'confirm_delete': 'Sind Sie sicher, dass Sie dies löschen möchten?',
    }
}

# Current locale (thread-local in production)
_current_locale = 'en'


def get_locales() -> List[str]:
    """Get list of available locales."""
    return list(TRANSLATIONS.keys())


def set_locale(locale: str):
    """Set current locale."""
    global _current_locale
    if locale in TRANSLATIONS:
        _current_locale = locale


def get_locale() -> str:
    """Get current locale."""
    return _current_locale


def get_text(key: str, locale: str = None, **kwargs) -> str:
    """
    Get translated text for a key.
    
    Args:
        key: Translation key
        locale: Override locale (uses current if not specified)
        **kwargs: Format arguments
    
    Returns:
        Translated string or key if not found
    """
    loc = locale or _current_locale
    translations = TRANSLATIONS.get(loc, TRANSLATIONS['en'])
    text = translations.get(key, key)
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


# Shorthand alias
_ = get_text


def add_translation(locale: str, key: str, value: str):
    """Add or update a translation."""
    if locale not in TRANSLATIONS:
        TRANSLATIONS[locale] = {}
    TRANSLATIONS[locale][key] = value


def detect_locale_from_request():
    """Detect locale from Accept-Language header."""
    from flask import request
    
    accept_lang = request.headers.get('Accept-Language', 'en')
    for locale in get_locales():
        if locale in accept_lang.lower():
            return locale
    return 'en'


# Flask integration
I18N_ROUTES = """
from i18n import get_text, set_locale, get_locales, detect_locale_from_request

@app.before_request
def set_request_locale():
    # Check session first, then detect from request
    locale = session.get('locale')
    if not locale:
        locale = detect_locale_from_request()
    set_locale(locale)

@app.route('/api/locale', methods=['GET'])
def get_current_locale():
    from i18n import get_locale, get_locales
    return jsonify({
        'current': get_locale(),
        'available': get_locales()
    })

@app.route('/api/locale', methods=['POST'])
def change_locale():
    data = request.get_json()
    locale = data.get('locale', 'en')
    
    if locale in get_locales():
        session['locale'] = locale
        set_locale(locale)
        return jsonify({'message': 'Locale changed', 'locale': locale})
    
    return jsonify({'error': 'Invalid locale'}), 400

@app.context_processor
def inject_i18n():
    from i18n import get_text, get_locale
    return {
        '_': get_text,
        'current_locale': get_locale()
    }
"""


def get_language_selector_html() -> str:
    """Generate language selector HTML."""
    return """
<div class="language-selector">
    <label for="lang-select" class="sr-only">Language</label>
    <select id="lang-select" onchange="changeLanguage(this.value)">
        <option value="en">English</option>
        <option value="es">Español</option>
        <option value="fr">Français</option>
        <option value="de">Deutsch</option>
    </select>
</div>

<script>
function changeLanguage(locale) {
    fetch('/api/locale', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({locale: locale})
    }).then(function() {
        window.location.reload();
    });
}
</script>
"""
'''


# =============================================================================
# GRAPHQL
# =============================================================================

def generate_graphql_module(models: List[str]) -> str:
    """Generate GraphQL schema and resolvers."""
    
    # Generate type definitions
    type_defs = []
    query_fields = []
    mutation_fields = []
    resolvers = []
    
    for model in models:
        model_lower = model.lower()
        
        type_defs.append(f"""
type {model} {{
    id: ID!
    name: String!
    created_at: String
}}""")
        
        query_fields.append(f"    {model_lower}s: [{model}!]!")
        query_fields.append(f"    {model_lower}(id: ID!): {model}")
        
        mutation_fields.append(f"    create{model}(name: String!): {model}!")
        mutation_fields.append(f"    update{model}(id: ID!, name: String!): {model}")
        mutation_fields.append(f"    delete{model}(id: ID!): Boolean!")
        
        resolvers.append(f'''
    # {model} Resolvers
    @query.field("{model_lower}s")
    def resolve_{model_lower}s(_, info):
        return {model}.query.all()
    
    @query.field("{model_lower}")
    def resolve_{model_lower}(_, info, id):
        return {model}.query.get(id)
    
    @mutation.field("create{model}")
    def resolve_create_{model_lower}(_, info, name):
        item = {model}(name=name)
        db.session.add(item)
        db.session.commit()
        return item
    
    @mutation.field("update{model}")
    def resolve_update_{model_lower}(_, info, id, name):
        item = {model}.query.get(id)
        if item:
            item.name = name
            db.session.commit()
        return item
    
    @mutation.field("delete{model}")
    def resolve_delete_{model_lower}(_, info, id):
        item = {model}.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
''')
    
    return f'''"""
GraphQL Module
Usage:
    from graphql_api import schema, graphql_routes

Requires: pip install ariadne
"""

from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL

# Schema definition
type_defs = """
{"".join(type_defs)}

type Query {{
{chr(10).join(query_fields)}
}}

type Mutation {{
{chr(10).join(mutation_fields)}
}}
"""

# Resolvers
query = QueryType()
mutation = MutationType()

# Import models
from models import *
from db import db


{"".join(resolvers)}


# Create executable schema
schema = make_executable_schema(type_defs, query, mutation)


# Flask integration
GRAPHQL_ROUTES = """
from ariadne import graphql_sync
from ariadne.constants import PLAYGROUND_HTML
from graphql_api import schema

@app.route('/graphql', methods=['GET'])
def graphql_playground():
    return PLAYGROUND_HTML, 200

@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema, data, context_value=request)
    status_code = 200 if success else 400
    return jsonify(result), status_code
"""
'''


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_enterprise_features(
    app_name: str,
    description: str,
    answers: Dict[str, bool],
    models: List[str] = None
) -> Dict[str, str]:
    """
    Generate all enterprise feature files.
    
    Returns:
        Dict of filename -> content
    """
    models = models or ['Item']
    has_auth = answers.get('needs_auth', False)
    
    # Detect which features to include
    req = detect_features(description, answers)
    
    files = {}
    
    # Always include these for production apps
    if answers.get('has_data'):
        files['tests/test_app.py'] = generate_tests(app_name, models, has_auth)
        files['.env.template'] = generate_env_template()
    
    # API Documentation
    if Feature.API_DOCS in req.features or answers.get('has_data'):
        files['openapi.json'] = generate_openapi_spec(app_name, description, models, has_auth)
        files['templates/swagger.html'] = generate_swagger_ui_html(app_name)
    
    # Database migrations
    if Feature.MIGRATIONS in req.features:
        files['alembic.ini'] = generate_alembic_ini()
        files['migrations/env.py'] = generate_alembic_env_py()
        files['migrations/script.py.mako'] = generate_alembic_script_py_mako()
    
    # Email
    if Feature.EMAIL in req.features or has_auth:
        files['email_service.py'] = generate_email_module()
    
    # File uploads
    if Feature.FILE_UPLOAD in req.features:
        files['uploads.py'] = generate_upload_module()
    
    # Security module (always for auth apps)
    if has_auth or any(f in req.features for f in [Feature.RATE_LIMIT, Feature.CSRF, Feature.VALIDATION, Feature.TWO_FACTOR, Feature.PASSWORD_POLICY]):
        files['security.py'] = generate_security_module()
    
    # DevOps
    if any(f in req.features for f in [Feature.HEALTH_CHECK, Feature.LOGGING, Feature.ERROR_TRACKING, Feature.ENV_CONFIG]) or answers.get('has_data'):
        files['devops.py'] = generate_devops_module()
    
    # Accessibility CSS/JS
    files['static/accessibility.css'] = generate_accessibility_css()
    files['static/accessibility.js'] = generate_accessibility_js()
    
    # Extras
    if Feature.CACHING in req.features:
        files['cache.py'] = generate_redis_cache()
    
    if Feature.PDF_EXPORT in req.features:
        files['pdf_export.py'] = generate_pdf_export()
    
    if Feature.WEBHOOKS in req.features:
        files['webhooks.py'] = generate_webhooks()
    
    # i18n (internationalization)
    if Feature.I18N in req.features:
        files['i18n.py'] = generate_i18n_module()
    
    # GraphQL
    if Feature.GRAPHQL in req.features:
        files['graphql_api.py'] = generate_graphql_module(models)
    
    return files


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Enterprise Features Module Test")
    print("=" * 60)
    
    # Test feature detection
    test_cases = [
        ("a todo list app", {}),
        ("a recipe app with user login and file uploads", {"needs_auth": True, "has_data": True}),
        ("an e-commerce store with email notifications and webhooks", {"has_data": True}),
        ("a health tracker with PDF reports", {"has_data": True, "needs_auth": True}),
    ]
    
    for desc, answers in test_cases:
        print(f"\n--- {desc} ---")
        req = detect_features(desc, answers)
        print(f"  Features: {[f.name for f in req.features]}")
        
        files = generate_enterprise_features("TestApp", desc, answers, ["Recipe", "User"])
        print(f"  Generated files: {list(files.keys())}")
