"""Code generator - Builds working Flask apps from requirements.

Features:
 - Description-aware domain models (via domain_parser)
 - Working auth (register, login, logout, session gate)
 - Search / CSV export endpoints
 - Standalone HTML for non-data apps (games, calculators, tools)
 - Improved CRUD UI (labelled forms, clear-on-submit, toast, empty state)
"""

import re
from typing import Dict, List, Set, Tuple
from domain_parser import DomainModel, parse_description
from template_registry import match_template, extract_features
from component_assembler import can_assemble, assemble_html
from template_algebra import algebra, MICRO_TEMPLATES, MicroTemplate
from template_synthesis import SmartSynthesizer

# Error validation and auto-fixing
try:
    from error_fixer import validate_and_fix_files, validate_generated_code
    HAS_ERROR_FIXER = True
except ImportError:
    HAS_ERROR_FIXER = False

# Design system for category-aware theming
try:
    from design_system import get_category_css, detect_category, AppCategory
    HAS_DESIGN_SYSTEM = True
except ImportError:
    HAS_DESIGN_SYSTEM = False

# Compliance module for privacy/GDPR/cookies
try:
    from compliance import (
        detect_data_collection, generate_compliance_features,
        generate_cookie_consent_html, generate_privacy_policy_html,
        generate_gdpr_routes, Jurisdiction
    )
    HAS_COMPLIANCE = True
except ImportError:
    HAS_COMPLIANCE = False

# Enterprise features module (tests, API docs, security, devops, etc.)
try:
    from enterprise_features import generate_enterprise_features, detect_features
    HAS_ENTERPRISE = True
except ImportError:
    HAS_ENTERPRISE = False


def detect_app_type(description: str) -> str:
    """Use scored template registry instead of flat regex."""
    best_id, features, scores = match_template(description)
    # If 'data_app' feature found and no game features dominate → CRUD
    if "data_app" in features and scores[0][1] < 5:
        return "generic"  # Will trigger CRUD path in generate_index_html
    return best_id


class CodeGenerator:
    """Generates Flask app boilerplate from requirements + description."""
    
    def __init__(self):
        self.synthesizer = SmartSynthesizer()
        self._current_description = ""  # Used for category-aware theming

    # ==================================================================
    # Micro-Template Integration (Enterprise Features + Synthesis)
    # ==================================================================
    
    def _detect_micro_templates(self, description: str) -> List[str]:
        """Detect which micro-templates apply + synthesize new ones if needed."""
        # Use SmartSynthesizer which both detects AND synthesizes
        result = self.synthesizer.analyze_and_synthesize(description)
        
        # Return all template IDs (existing + newly synthesized)
        template_ids = result.get('existing_templates', [])
        synthesized = result.get('synthesized_templates', [])
        
        # Add synthesized template IDs
        for synth in synthesized:
            if hasattr(synth, 'id'):
                template_ids.append(synth.id)
        
        return template_ids
    
    def _get_synthesis_report(self, description: str) -> Dict:
        """Get full synthesis report for debugging/display."""
        return self.synthesizer.analyze_and_synthesize(description)
    
    def _get_enterprise_fields(self, template_ids: List[str]) -> List[Tuple[str, str, bool]]:
        """Get extra fields from detected micro-templates (including synthesized).
        Returns list of (field_name, sql_type, nullable) tuples."""
        fields = []
        seen = set()
        
        type_map = {
            'string': 'db.String(255)',
            'str': 'db.String(255)',
            'text': 'db.Text',
            'integer': 'db.Integer',
            'int': 'db.Integer',
            'float': 'db.Float',
            'boolean': 'db.Boolean',
            'bool': 'db.Boolean',
            'datetime': 'db.DateTime',
            'json': 'db.JSON',
            'list': 'db.JSON',
            'enum': 'db.String(50)',
            'decimal': 'db.Float',
            'reference': 'db.Integer',
            'self_reference': 'db.Integer',
        }
        
        for tid in template_ids:
            if tid not in MICRO_TEMPLATES:
                continue
            template = MICRO_TEMPLATES[tid]
            for field in template.fields:
                # Handle both dict format (MicroTemplate) and string format (synthesized)
                if isinstance(field, dict):
                    fname = field.get('name', '')
                    ftype_key = field.get('type', 'string')
                    nullable = field.get('nullable', True)
                else:
                    # Synthesized templates use string field names
                    fname = str(field)
                    ftype_key = 'string'  # Default to string for synthesized
                    nullable = True
                
                if not fname or fname in seen:
                    continue
                seen.add(fname)
                
                ftype = type_map.get(ftype_key, 'db.String(255)')
                fields.append((fname, ftype, nullable))
        
        return fields
    
    def _get_enterprise_operations(self, template_ids: List[str]) -> List[str]:
        """Get operations enabled by detected micro-templates."""
        ops = []
        for tid in template_ids:
            if tid in MICRO_TEMPLATES:
                ops.extend(MICRO_TEMPLATES[tid].operations)
        return list(set(ops))
    
    def _generate_enterprise_routes(self, model_name: str, operations: List[str], 
                                     has_auth: bool) -> str:
        """Generate Flask routes for enterprise operations."""
        lower = model_name.lower()
        cls = model_name
        auth_dec = "\n@login_required" if has_auth else ""
        lines = []
        
        # File upload routes
        if 'upload_file' in operations:
            lines.append(f"""
# ==== File Upload for {cls} ====
import os
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/{lower}s/<int:id>/upload', methods=['POST']){auth_dec}
def upload_{lower}_file(id):
    item = {cls}.query.get_or_404(id)
    if 'file' not in request.files:
        return jsonify({{"error": "No file provided"}}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({{"error": "No file selected"}}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{{id}}_{{filename}}")
    file.save(filepath)
    item.file_path = filepath
    item.file_name = filename
    item.file_size = os.path.getsize(filepath)
    item.file_type = file.content_type
    db.session.commit()
    return jsonify(item.to_dict())
""")
        
        # Role management routes
        if 'assign_role' in operations:
            lines.append(f"""
# ==== RBAC Routes for {cls} ====
@app.route('/api/{lower}s/<int:id>/role', methods=['PUT']){auth_dec}
def assign_{lower}_role(id):
    item = {cls}.query.get_or_404(id)
    data = request.get_json()
    role = data.get('role', 'viewer')
    if role not in ['admin', 'editor', 'viewer', 'guest']:
        return jsonify({{"error": "Invalid role"}}), 400
    item.role = role
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/{lower}s/by-role/<role>'){auth_dec}
def list_{lower}s_by_role(role):
    items = {cls}.query.filter_by(role=role).all()
    return jsonify([item.to_dict() for item in items])
""")
        
        # Soft delete routes
        if 'soft_delete' in operations:
            lines.append(f"""
# ==== Soft Delete Routes for {cls} ====
@app.route('/api/{lower}s/<int:id>/delete', methods=['POST']){auth_dec}
def soft_delete_{lower}(id):
    item = {cls}.query.get_or_404(id)
    item.is_deleted = True
    item.deleted_at = datetime.utcnow()
    item.deleted_by = session.get('user_id')
    db.session.commit()
    return jsonify({{"ok": True, "message": "Item moved to trash"}})

@app.route('/api/{lower}s/<int:id>/restore', methods=['POST']){auth_dec}
def restore_{lower}(id):
    item = {cls}.query.get_or_404(id)
    item.is_deleted = False
    item.deleted_at = None
    item.deleted_by = None
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/{lower}s/trash'){auth_dec}
def list_{lower}s_trash():
    items = {cls}.query.filter_by(is_deleted=True).all()
    return jsonify([item.to_dict() for item in items])
""")
        
        # Audit log routes  
        if 'log_change' in operations:
            lines.append(f"""
# ==== Audit Log Routes for {cls} ====
@app.route('/api/{lower}s/<int:id>/audit'){auth_dec}
def get_{lower}_audit(id):
    item = {cls}.query.get_or_404(id)
    return jsonify({{"audit_log": item.audit_log or []}})

def _log_{lower}_change(item, action, changes):
    import json
    log = json.loads(item.audit_log) if item.audit_log else []
    log.append({{
        "action": action,
        "changes": changes,
        "user_id": session.get('user_id'),
        "timestamp": datetime.utcnow().isoformat()
    }})
    item.audit_log = json.dumps(log)
    item.last_modified_by = session.get('user_id')
""")
        
        # Background job routes
        if 'queue_job' in operations:
            lines.append(f"""
# ==== Background Job Routes for {cls} ====
import uuid

@app.route('/api/{lower}s/<int:id>/job', methods=['POST']){auth_dec}
def queue_{lower}_job(id):
    item = {cls}.query.get_or_404(id)
    data = request.get_json()
    job_type = data.get('type', 'process')
    item.job_id = str(uuid.uuid4())
    item.job_status = 'queued'
    db.session.commit()
    # In production, this would queue to Celery/RQ
    return jsonify({{"job_id": item.job_id, "status": "queued"}})

@app.route('/api/{lower}s/<int:id>/job/status'){auth_dec}
def get_{lower}_job_status(id):
    item = {cls}.query.get_or_404(id)
    return jsonify({{"job_id": item.job_id, "status": item.job_status, "result": item.job_result}})
""")
        
        # API key routes
        if 'generate_api_key' in operations:
            lines.append(f"""
# ==== API Key Routes for {cls} ====
import secrets

@app.route('/api/{lower}s/<int:id>/api-key', methods=['POST']){auth_dec}
def generate_{lower}_api_key(id):
    item = {cls}.query.get_or_404(id)
    item.api_key = secrets.token_urlsafe(32)
    item.api_key_created = datetime.utcnow()
    db.session.commit()
    return jsonify({{"api_key": item.api_key}})

@app.route('/api/{lower}s/<int:id>/api-key', methods=['DELETE']){auth_dec}
def revoke_{lower}_api_key(id):
    item = {cls}.query.get_or_404(id)
    item.api_key = None
    item.api_key_created = None
    db.session.commit()
    return jsonify({{"ok": True}})
""")
        
        return '\n'.join(lines)

    # ==================================================================
    # app.py  (backend generation — unchanged)
    # ==================================================================
    def generate_app_py(self, app_name: str, answers: Dict[str, bool],
                        description: str = "") -> str:
        needs_db = answers.get("has_data", False)
        needs_auth = answers.get("needs_auth", False)
        needs_realtime = answers.get("realtime", False)
        needs_search = answers.get("search", False)
        needs_export = answers.get("export", False)

        models = parse_description(description) if (needs_db and description) else []

        parts: List[str] = []
        parts.append(self._imports(needs_db, needs_auth, needs_realtime,
                                   needs_search, needs_export))
        parts.append(self._app_init(app_name, needs_db, needs_realtime))
        if needs_auth and needs_db:
            parts.append(self._user_model())
        if needs_db:
            for m in models:
                parts.append(self._domain_model(m, needs_auth))
        parts.append(self._base_routes(app_name))
        if needs_auth and needs_db:
            parts.append(self._auth_routes())
        if needs_db:
            for m in models:
                parts.append(self._crud_routes(m, needs_auth, needs_search,
                                               needs_export))
        parts.append(self._main_block(needs_db, needs_realtime))
        return "\n".join(parts)

    # ==================================================================
    # requirements.txt
    # ==================================================================
    def generate_requirements_txt(self, answers: Dict[str, bool]) -> str:
        reqs = ["flask==3.0.2", "flask-cors==4.0.0"]
        if answers.get("has_data"):
            reqs.append("flask-sqlalchemy==3.1.1")
        if answers.get("realtime"):
            reqs.append("flask-socketio==5.3.6")
        return "\n".join(reqs) + "\n"

    # ==================================================================
    # Multi-file generation for data apps
    # ==================================================================
    
    def generate_models_py(self, answers: Dict[str, bool], description: str = "") -> str:
        """Generate models.py with SQLAlchemy models + enterprise fields."""
        needs_auth = answers.get("needs_auth", False)
        models = parse_description(description) if description else []
        
        # Detect micro-templates for enterprise features
        detected_templates = self._detect_micro_templates(description) if description else []
        enterprise_fields = self._get_enterprise_fields(detected_templates)
        
        parts = [
            "from db import db",
            "from datetime import datetime",
            ""
        ]
        
        if needs_auth:
            parts.append(self._user_model())
        
        for m in models:
            # Enhance model with enterprise fields
            enhanced_model = self._enhance_model_with_enterprise(m, enterprise_fields)
            parts.append(self._domain_model(enhanced_model, needs_auth))
        
        return "\n".join(parts)
    
    def _enhance_model_with_enterprise(self, model: DomainModel, enterprise_fields: List[Tuple[str, str, bool]]) -> DomainModel:
        """Add enterprise fields to a domain model."""
        existing_names = {f[0] for f in model.fields}
        new_fields = list(model.fields)
        
        for fname, ftype, nullable in enterprise_fields:
            if fname not in existing_names:
                new_fields.append((fname, ftype, nullable))
        
        return DomainModel(
            name=model.name,
            table_name=model.table_name,
            fields=new_fields,
            has_relationship=model.has_relationship
        )
    
    def generate_db_py(self) -> str:
        """Generate db.py for database initialization."""
        return """from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
"""
    
    def generate_index_html(self, app_name: str, answers: Dict[str, bool], description: str = "") -> str:
        """
        Generate index.html for the app.
        Routes to either CRUD HTML or standalone HTML based on app type.
        """
        # Store description for category-aware theming
        self._current_description = description
        
        needs_db = answers.get("has_data", False)
        app_type = detect_app_type(description) if description else "generic"
        
        # Data apps (CRUD) use the database-backed HTML
        if needs_db:
            return self._crud_html(app_name, answers, description)
        
        # Standalone apps (games, tools, calculators) use component-based HTML
        return self._standalone_html(app_name, app_type, description)
    
    def generate_data_app_files(self, app_name: str, answers: Dict[str, bool], description: str = "",
                                  auto_fix: bool = True) -> Dict[str, str]:
        """Generate all files for a multi-file data app with SQLite.
        
        Args:
            app_name: Name of the app
            answers: Feature flags (has_data, needs_auth, etc.)
            description: Natural language description
            auto_fix: If True, automatically validate and fix syntax errors
            
        Returns:
            Dict of filename -> content (with fixes applied if auto_fix=True)
        """
        needs_db = answers.get("has_data", False)
        
        if not needs_db:
            # Single file app
            files = {
                "app.py": self.generate_app_py(app_name, answers, description),
                "requirements.txt": self.generate_requirements_txt(answers),
                "templates/index.html": self.generate_index_html(app_name, answers, description)
            }
        else:
            # Multi-file data app
            files = {
                "app.py": self._generate_data_app_py(app_name, answers, description),
                "models.py": self.generate_models_py(answers, description),
                "db.py": self.generate_db_py(),
                "requirements.txt": self.generate_requirements_txt(answers),
                "templates/index.html": self.generate_index_html(app_name, answers, description),
                "README.md": self._generate_readme(app_name, description)
            }
        
        # Add compliance features (cookie consent, privacy policy, GDPR routes)
        if HAS_COMPLIANCE:
            files = self._add_compliance_features(files, app_name, description, answers)
        
        # Add enterprise features (tests, API docs, security, devops)
        if HAS_ENTERPRISE:
            files = self._add_enterprise_features(files, app_name, description, answers)
        
        # Auto-validate and fix Python syntax errors
        if auto_fix and HAS_ERROR_FIXER:
            fixed_files, fix_log = validate_and_fix_files(files)
            # Store fix log for debugging (accessible via generator.last_fix_log)
            self.last_fix_log = fix_log
            return fixed_files
        
        return files
    
    def _add_compliance_features(self, files: Dict[str, str], app_name: str, 
                                   description: str, answers: Dict[str, bool]) -> Dict[str, str]:
        """Add compliance features based on detected requirements."""
        # Get compliance features
        compliance_files = generate_compliance_features(
            app_name=app_name,
            description=description,
            answers=answers,
            model_fields=[]  # Could extract from models.py if needed
        )
        
        # Add privacy policy page if generated
        if 'templates/privacy.html' in compliance_files:
            files['templates/privacy.html'] = compliance_files['templates/privacy.html']
        
        # Inject cookie consent into index.html
        if 'cookie_consent_html' in compliance_files:
            if 'templates/index.html' in files:
                # Insert cookie banner before closing </body>
                consent_html = compliance_files['cookie_consent_html']
                files['templates/index.html'] = files['templates/index.html'].replace(
                    '</body>',
                    f'\n{consent_html}\n</body>'
                )
        
        # Inject GDPR routes into app.py
        if 'gdpr_routes' in compliance_files:
            if 'app.py' in files:
                gdpr_routes = compliance_files['gdpr_routes']
                # Insert before if __name__ == '__main__':
                files['app.py'] = files['app.py'].replace(
                    "if __name__ == '__main__':",
                    f"{gdpr_routes}\n\nif __name__ == '__main__':"
                )
                # Add privacy policy route
                files['app.py'] = files['app.py'].replace(
                    "if __name__ == '__main__':",
                    '''@app.route('/privacy')
def privacy():
    return send_file('templates/privacy.html')


if __name__ == '__main__':'''
                )
        
        # Inject CCPA footer if needed
        if 'ccpa_footer_html' in compliance_files:
            if 'templates/index.html' in files:
                # Insert footer before closing </body>
                footer_html = compliance_files['ccpa_footer_html']
                files['templates/index.html'] = files['templates/index.html'].replace(
                    '</body>',
                    f'\n{footer_html}\n</body>'
                )
        
        return files
    
    def _add_enterprise_features(self, files: Dict[str, str], app_name: str,
                                   description: str, answers: Dict[str, bool]) -> Dict[str, str]:
        """Add enterprise features (tests, API docs, security, devops, etc.)."""
        # Get model names from description
        models = parse_description(description) if description else []
        model_names = [m.name for m in models] if models else ['Item']
        
        # Generate enterprise features
        enterprise_files = generate_enterprise_features(
            app_name=app_name,
            description=description,
            answers=answers,
            models=model_names
        )
        
        # Add generated files (except those that need injection)
        for filename, content in enterprise_files.items():
            if filename not in files:  # Don't overwrite existing files
                files[filename] = content
        
        # Inject health check routes into app.py
        if answers.get('has_data') and 'app.py' in files:
            health_routes = '''
# =============================================================================
# Health Checks
# =============================================================================
import time
_start_time = time.time()

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

@app.route('/health/ready')
def readiness():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready', 'uptime': int(time.time() - _start_time)})
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

'''
            files['app.py'] = files['app.py'].replace(
                "if __name__ == '__main__':",
                f"{health_routes}\nif __name__ == '__main__':"
            )
        
        # Inject API docs routes if OpenAPI spec was generated
        if 'openapi.json' in files and 'app.py' in files:
            docs_routes = '''
# =============================================================================
# API Documentation
# =============================================================================

@app.route('/api/openapi.json')
def openapi_spec():
    return send_file('openapi.json', mimetype='application/json')

@app.route('/docs')
def swagger_ui():
    return send_file('templates/swagger.html')

'''
            files['app.py'] = files['app.py'].replace(
                "if __name__ == '__main__':",
                f"{docs_routes}\nif __name__ == '__main__':"
            )
        
        # Add accessibility CSS/JS links to index.html
        if 'templates/index.html' in files:
            accessibility_links = '''<link rel="stylesheet" href="/static/accessibility.css">'''
            accessibility_script = '''<script src="/static/accessibility.js"></script>'''
            
            # Add CSS link in head
            if '<head>' in files['templates/index.html']:
                files['templates/index.html'] = files['templates/index.html'].replace(
                    '</head>',
                    f'{accessibility_links}\n</head>'
                )
            
            # Add JS script before body close
            if '</body>' in files['templates/index.html']:
                files['templates/index.html'] = files['templates/index.html'].replace(
                    '</body>',
                    f'{accessibility_script}\n</body>'
                )
            
            # Add skip link after body open
            skip_link = '<a href="#main" class="skip-link">Skip to main content</a>'
            files['templates/index.html'] = files['templates/index.html'].replace(
                '<body>',
                f'<body>\n{skip_link}'
            )
        
        return files
    
    def _generate_data_app_py(self, app_name: str, answers: Dict[str, bool], description: str = "") -> str:
        """Generate app.py that imports from models and db modules + enterprise routes."""
        needs_auth = answers.get("needs_auth", False)
        needs_search = answers.get("search", False)
        needs_export = answers.get("export", False)
        models = parse_description(description) if description else []
        
        # Detect micro-templates for enterprise features
        detected_templates = self._detect_micro_templates(description) if description else []
        enterprise_ops = self._get_enterprise_operations(detected_templates)
        
        imports = [
            "from flask import Flask, render_template, request, jsonify, session, redirect, url_for",
            "from flask_cors import CORS",
            "from datetime import datetime",
            "from db import db, init_db"
        ]
        
        if needs_auth:
            imports.append("from models import User")
            imports.append("from werkzeug.security import check_password_hash")
            imports.append("from functools import wraps")
        
        # Import all models
        model_imports = [m.name for m in models]
        if model_imports:
            imports.append(f"from models import {', '.join(model_imports)}")
        
        if needs_export:
            imports.append("import csv")
            imports.append("import io")
        
        parts = ["\n".join(imports)]
        parts.append(self._app_init(app_name, True, False))
        parts.append("\n# Initialize database")
        parts.append("init_db(app)")
        parts.append(self._base_routes(app_name))
        
        if needs_auth:
            parts.append(self._auth_routes())
        
        for m in models:
            parts.append(self._crud_routes(m, needs_auth, needs_search, needs_export))
            # Add enterprise routes for this model
            if enterprise_ops:
                parts.append(self._generate_enterprise_routes(m.name, enterprise_ops, needs_auth))
        
        parts.append("\nif __name__ == '__main__':")
        parts.append("    app.run(debug=True)")
        
        return "\n".join(parts)
    
    def _generate_readme(self, app_name: str, description: str) -> str:
        """Generate README.md for the project."""
        title = app_name.replace("-", " ").title()
        return f"""# {title}

{description}

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

3. Open your browser to `http://127.0.0.1:5000`

## Features

- SQLite database for data persistence
- RESTful API endpoints
- Responsive web interface
- CRUD operations

## Generated by App Forge
"""
    
    # ==================================================================
    # Docker & Deployment Configuration
    # ==================================================================
    
    def generate_dockerfile(self, app_name: str) -> str:
        """Generate Dockerfile for the project."""
        return """FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
"""
    
    def generate_docker_compose(self, app_name: str) -> str:
        """Generate docker-compose.yml for the project."""
        service_name = app_name.replace(" ", "-").lower()
        return f"""version: '3.8'

services:
  {service_name}:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    restart: unless-stopped
"""
    
    def generate_vercel_config(self) -> str:
        """Generate vercel.json for Vercel deployment."""
        return """{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
"""
    
    def generate_railway_config(self) -> str:
        """Generate railway.json for Railway deployment."""
        return """{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
"""
    
    def generate_render_config(self, app_name: str) -> str:
        """Generate render.yaml for Render deployment."""
        service_name = app_name.replace(" ", "-").lower()
        return f"""services:
  - type: web
    name: {service_name}
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: FLASK_ENV
        value: production
"""
    
    def generate_deployment_files(self, app_name: str) -> Dict[str, str]:
        """Generate all deployment configuration files."""
        return {
            "Dockerfile": self.generate_dockerfile(app_name),
            "docker-compose.yml": self.generate_docker_compose(app_name),
            ".dockerignore": """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.db
*.sqlite
*.sqlite3
.env
.git
.gitignore
""",
            "vercel.json": self.generate_vercel_config(),
            "railway.json": self.generate_railway_config(),
            "render.yaml": self.generate_render_config(app_name),
        }

    def _imports(self, db: bool, auth: bool, rt: bool, search: bool, export: bool) -> str:
        """Generate import statements for single-file app.py."""
        lines = [
            "from flask import Flask, render_template, request, jsonify, session, redirect, url_for",
            "from flask_cors import CORS",
            "from datetime import datetime",
        ]
        if db:
            lines.append("from flask_sqlalchemy import SQLAlchemy")
        if auth:
            lines.append("from werkzeug.security import generate_password_hash, check_password_hash")
            lines.append("from functools import wraps")
        if rt:
            lines.append("from flask_socketio import SocketIO, emit")
        if export:
            lines.append("import csv, io")
        return "\n".join(lines) + "\n"

    def _app_init(self, name, db, rt):
        s = f"\napp = Flask(__name__)\napp.config['SECRET_KEY'] = 'dev-secret-key'\nCORS(app)\n"
        if db:
            s += "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'\n"
            s += "app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False\n"
            s += "db = SQLAlchemy(app)\n"
        if rt:
            s += "socketio = SocketIO(app, cors_allowed_origins='*')\n"
        return s

    def _user_model(self):
        return """
# ==== User Model ====
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated
"""

    def _domain_model(self, m: DomainModel, has_auth: bool):
        lines = [f"\n# ==== {m.name} Model ===="]
        lines.append(f"class {m.name}(db.Model):")
        lines.append(f"    id = db.Column(db.Integer, primary_key=True)")
        for fname, ftype, nullable in m.fields:
            null_str = "" if not nullable else ", nullable=True"
            default_str = ""
            if ftype == "db.Boolean":
                default_str = ", default=False"
            lines.append(f"    {fname} = db.Column({ftype}{null_str}{default_str})")
        lines.append(f"    created_at = db.Column(db.DateTime, default=datetime.utcnow)")
        if has_auth:
            lines.append(f"    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)")
        lines.append(f"")
        lines.append(f"    def to_dict(self):")
        lines.append(f"        return {{")
        lines.append(f'            "id": self.id,')
        for fname, ftype, _ in m.fields:
            if "DateTime" in ftype:
                lines.append(f'            "{fname}": self.{fname}.isoformat() if self.{fname} else None,')
            else:
                lines.append(f'            "{fname}": self.{fname},')
        lines.append(f'            "created_at": self.created_at.isoformat() if self.created_at else None,')
        lines.append(f"        }}")
        return "\n".join(lines) + "\n"

    def _base_routes(self, name):
        return f"""
# ==== Routes ====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({{"status": "ok", "app": "{name}"}})
"""

    def _auth_routes(self):
        return """
# ==== Auth Routes ====
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not username or not email or len(password) < 4:
        return jsonify({"error": "Username, email, and password (4+ chars) required"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already taken"}), 409
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({"id": user.id, "username": user.username}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    session['user_id'] = user.id
    return jsonify({"id": user.id, "username": user.username})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route('/api/me')
def current_user():
    uid = session.get('user_id')
    if not uid:
        return jsonify({"user": None})
    user = User.query.get(uid)
    return jsonify({"user": {"id": user.id, "username": user.username, "email": user.email} if user else None})
"""

    def _crud_routes(self, m: DomainModel, has_auth, has_search, has_export):
        lower = m.table_name
        cls = m.name
        auth_dec = "\n@login_required" if has_auth else ""
        user_filter = f".filter_by(user_id=session.get('user_id'))" if has_auth else ""
        user_assign = f"\n    item.user_id = session.get('user_id')" if has_auth else ""

        text_fields = [f for f, t, _ in m.fields if "String" in t or "Text" in t]

        lines = [f"\n# ==== {cls} CRUD ===="]
        lines.append(f"@app.route('/api/{lower}s'){auth_dec}")
        lines.append(f"def list_{lower}s():")
        lines.append(f"    query = {cls}.query{user_filter}")
        if has_search and text_fields:
            lines.append(f"    q = request.args.get('q', '').strip()")
            lines.append(f"    if q:")
            or_clauses = " | ".join(f"{cls}.{f}.ilike(f'%{{q}}%')" for f in text_fields)
            lines.append(f"        query = query.filter({or_clauses})")
        lines.append(f"    items = query.order_by({cls}.created_at.desc()).all()")
        lines.append(f"    return jsonify([i.to_dict() for i in items])")

        lines.append(f"\n@app.route('/api/{lower}s', methods=['POST']){auth_dec}")
        lines.append(f"def create_{lower}():")
        lines.append(f"    data = request.get_json()")
        lines.append(f"    item = {cls}()")
        for fname, ftype, _ in m.fields:
            if "Boolean" in ftype:
                lines.append(f"    item.{fname} = data.get('{fname}', False)")
            elif "Integer" in ftype or "Float" in ftype:
                lines.append(f"    item.{fname} = data.get('{fname}')")
            else:
                lines.append(f"    item.{fname} = data.get('{fname}', '')")
        lines.append(user_assign)
        lines.append(f"    db.session.add(item)")
        lines.append(f"    db.session.commit()")
        lines.append(f"    return jsonify(item.to_dict()), 201")

        lines.append(f"\n@app.route('/api/{lower}s/<int:id>', methods=['PUT']){auth_dec}")
        lines.append(f"def update_{lower}(id):")
        lines.append(f"    item = {cls}.query.get_or_404(id)")
        lines.append(f"    data = request.get_json()")
        for fname, ftype, _ in m.fields:
            lines.append(f"    if '{fname}' in data: item.{fname} = data['{fname}']")
        lines.append(f"    db.session.commit()")
        lines.append(f"    return jsonify(item.to_dict())")

        lines.append(f"\n@app.route('/api/{lower}s/<int:id>', methods=['DELETE']){auth_dec}")
        lines.append(f"def delete_{lower}(id):")
        lines.append(f"    item = {cls}.query.get_or_404(id)")
        lines.append(f"    db.session.delete(item)")
        lines.append(f"    db.session.commit()")
        lines.append(f"    return jsonify({{'ok': True}})")

        if has_export:
            lines.append(f"\n@app.route('/api/{lower}s/export'){auth_dec}")
            lines.append(f"def export_{lower}s():")
            lines.append(f"    items = {cls}.query{user_filter}.all()")
            lines.append(f"    si = io.StringIO()")
            lines.append(f"    writer = csv.writer(si)")
            header_fields = [f"'{f}'" for f, _, _ in m.fields]
            lines.append(f"    writer.writerow([{', '.join(header_fields)}])")
            lines.append(f"    for i in items:")
            row_fields = [f"i.{f}" for f, _, _ in m.fields]
            lines.append(f"        writer.writerow([{', '.join(row_fields)}])")
            lines.append(f"    from flask import Response")
            lines.append(f"    return Response(si.getvalue(), mimetype='text/csv',")
            lines.append(f"                    headers={{'Content-Disposition': 'attachment; filename={lower}s.csv'}})")

        return "\n".join(lines) + "\n"

    def _main_block(self, db, rt):
        s = "\nif __name__ == '__main__':\n"
        if db:
            s += "    with app.app_context():\n        db.create_all()\n"
        if rt:
            s += "    socketio.run(app, debug=True, port=5000)\n"
        else:
            s += "    app.run(debug=True, port=5000)\n"
        return s

    # ==================================================================
    # STANDALONE HTML  (non-data apps — games, tools, etc.)
    # ==================================================================

    def _base_page(self, title, body_html, css="", js="", description=""):
        """Generate base HTML page with category-aware theming."""
        # Use passed description or fall back to instance variable
        desc = description or self._current_description
        
        # Use design system if available, otherwise fallback to default
        if HAS_DESIGN_SYSTEM and desc:
            base_css = get_category_css(desc)
        else:
            # Fallback to original styling
            base_css = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;color:#333}
.navbar{background:#ff7a59;color:#fff;padding:16px 20px;text-align:center}
.navbar h1{font-size:22px;font-weight:700}
.container{max-width:640px;margin:30px auto;padding:0 16px}
.card{background:#fff;border-radius:12px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:16px;text-align:center}
button{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:600;transition:all .2s}
.btn-primary{background:#ff7a59;color:#fff}.btn-primary:hover{background:#ff6b3f;transform:translateY(-1px)}
.btn-secondary{background:#6c757d;color:#fff}.btn-secondary:hover{background:#5a6268}
input,select{padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;width:100%;margin-bottom:10px}
input:focus{outline:none;border-color:#ff7a59;box-shadow:0 0 0 3px rgba(255,122,89,.15)}
"""
        
        # Combine base CSS with any additional custom CSS
        full_css = base_css + "\n" + css if css else base_css
        
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{full_css}
</style>
</head>
<body>
<nav class="navbar"><h1>{title}</h1></nav>
<div class="container">
{body_html}
</div>
<script>
{js}
</script>
</body>
</html>"""

    def _standalone_html(self, title, app_type, description):
        # Store description for category-aware theming in _base_page
        self._current_description = description
        
        # Templates that matched via required features — always trustworthy
        REQUIRED_FEATURE_TEMPLATES = {
            "tictactoe", "hangman", "wordle", "calculator", "converter", "timer",
            "reaction_game", "simon_game", "reflex_game", "minesweeper",
            "snake", "tetris", "game_2048",
            "platformer", "shooter", "breakout",
            "pong", "cookie_clicker", "sudoku", "connect_four", "blackjack", "flappy",
            # Games that were missing - would break if routed through component assembler
            "memory_game", "sliding_puzzle", "quiz", "guess_game", "jigsaw"
        }

        # Check the component assembler FIRST for novel apps
        # Only override speculative template matches (not required-feature ones)
        # min_priority=80 avoids weak generic-generator false positives
        if app_type not in REQUIRED_FEATURE_TEMPLATES:
            if can_assemble(description, min_priority=80):
                return assemble_html(title, description)

        generators = {
            "guess_game": self._guess_game_html,
            "quiz": self._quiz_html,
            "tictactoe": self._tictactoe_html,
            "memory_game": self._memory_game_html,
            "calculator": self._calculator_html,
            "converter": self._converter_html,
            "timer": self._timer_html,
            "jigsaw": self._jigsaw_html,
            "sliding_puzzle": self._sliding_puzzle_html,
            "hangman": self._hangman_html,
            "wordle": self._wordle_html,
            "reaction_game": self._simon_grid_html,
            "simon_game": self._simon_grid_html,
            "reflex_game": self._simon_grid_html,
            "minesweeper": self._minesweeper_html,
            "snake": self._snake_html,
            "tetris": self._tetris_html,
            "game_2048": self._2048_html,
            "platformer": self._phaser_platformer_html,
            "shooter": self._phaser_shooter_html,
            "breakout": self._phaser_breakout_html,
            "pong": self._pong_html,
            "cookie_clicker": self._cookie_clicker_html,
            "sudoku": self._sudoku_html,
            "connect_four": self._connect_four_html,
            "blackjack": self._blackjack_html,
            "flappy": self._flappy_html,
            "algorithm_visualizer": self._algorithm_visualizer_html,
            "generic_game": self._generic_game_html,
        }
        gen = generators.get(app_type)
        if gen:
            return gen(title, description)

        # Last resort: check assembler with any priority
        if can_assemble(description):
            return assemble_html(title, description)

        # Absolute fallback
        return self._generic_app_html(title, description)

    # --- Guess the Number ---
    def _guess_game_html(self, title, desc):
        body = """<div class="card">
    <h2 id="message">I'm thinking of a number between 1 and 100</h2>
    <p id="hint" style="color:#888;margin:12px 0;font-size:18px">Take a guess!</p>
    <div style="max-width:260px;margin:0 auto">
        <input type="number" id="guess" min="1" max="100" placeholder="Enter 1-100..." autofocus>
        <button class="btn-primary" onclick="makeGuess()" style="width:100%">Guess</button>
    </div>
    <p id="attempts" style="margin-top:12px;font-size:14px;color:#888"></p>
    <button class="btn-secondary" onclick="newGame()" style="margin-top:8px;display:none" id="btn-new">Play Again</button>
</div>"""
        js = """var target,attempts,gameOver;
function newGame(){target=Math.floor(Math.random()*100)+1;attempts=0;gameOver=false;
document.getElementById('message').textContent="I'm thinking of a number between 1 and 100";
document.getElementById('hint').textContent='Take a guess!';document.getElementById('hint').style.color='#888';
document.getElementById('attempts').textContent='';document.getElementById('guess').value='';
document.getElementById('guess').disabled=false;document.getElementById('btn-new').style.display='none';}
function makeGuess(){if(gameOver)return;var g=parseInt(document.getElementById('guess').value);
if(isNaN(g)||g<1||g>100){document.getElementById('hint').textContent='Please enter a number 1-100!';return;}
attempts++;if(g===target){document.getElementById('message').textContent='You got it!';
document.getElementById('hint').textContent=target+' in '+attempts+' attempt'+(attempts>1?'s':'')+'!';
document.getElementById('hint').style.color='#2ecc71';document.getElementById('guess').disabled=true;
document.getElementById('btn-new').style.display='inline-block';gameOver=true;
}else{document.getElementById('hint').textContent=g<target?'Higher!':'Lower!';
document.getElementById('hint').style.color=g<target?'#1c7ed6':'#e74c3c';}
document.getElementById('attempts').textContent='Attempts: '+attempts;
document.getElementById('guess').value='';document.getElementById('guess').focus();}
document.getElementById('guess').addEventListener('keydown',function(e){if(e.key==='Enter')makeGuess();});
newGame();"""
        return self._base_page(title, body, "", js)

    # --- Quiz ---
    def _quiz_html(self, title, desc):
        css = """.progress{width:100%;height:6px;background:#eee;border-radius:3px;margin-bottom:16px}
.progress-bar{height:100%;background:var(--color-primary);border-radius:3px;transition:width .3s}
.options{display:flex;flex-direction:column;gap:10px;margin:20px 0;text-align:left}
.option{padding:14px 18px;background:#f8f8f8;border:2px solid #e0e0e0;border-radius:8px;cursor:pointer;font-size:15px;transition:all .2s}
.option:hover{border-color:var(--color-primary);background:rgba(var(--color-primary-rgb,255,122,89),.05)}
.option.correct{border-color:#2ecc71;background:#d4edda}
.option.wrong{border-color:#e74c3c;background:#ffeaea}
.score-big{font-size:56px;font-weight:700;color:var(--color-primary);margin:16px 0}"""
        body = """<div class="card" id="quiz-card">
    <div class="progress"><div class="progress-bar" id="progress" style="width:0%"></div></div>
    <p id="q-count" style="font-size:13px;color:#888;margin-bottom:10px"></p>
    <h2 id="question" style="font-size:20px"></h2>
    <div class="options" id="options"></div>
</div>
<div class="card" id="results" style="display:none">
    <h2>Quiz Complete!</h2>
    <div class="score-big" id="final-score"></div>
    <p id="score-msg" style="font-size:16px;color:#666"></p>
    <button class="btn-primary" onclick="startQuiz()" style="margin-top:16px">Play Again</button>
</div>"""
        js = """var questions=[
{q:"What is the capital of France?",o:["Berlin","Madrid","Paris","Rome"],a:2},
{q:"Which planet is closest to the sun?",o:["Venus","Mercury","Earth","Mars"],a:1},
{q:"What is 12 x 12?",o:["124","144","132","156"],a:1},
{q:"Who painted the Mona Lisa?",o:["Picasso","Van Gogh","Da Vinci","Rembrandt"],a:2},
{q:"What is the largest ocean?",o:["Atlantic","Indian","Arctic","Pacific"],a:3},
{q:"In what year did the Titanic sink?",o:["1905","1912","1918","1923"],a:1},
{q:"What gas do plants absorb?",o:["Oxygen","Nitrogen","CO2","Hydrogen"],a:2},
{q:"How many continents are there?",o:["5","6","7","8"],a:2},
{q:"What is the speed of light (approx km/s)?",o:["150,000","300,000","450,000","600,000"],a:1},
{q:"Which element has the symbol 'O'?",o:["Gold","Osmium","Oxygen","Oganesson"],a:2}];
var cur=0,score=0,answered=false;
function startQuiz(){cur=0;score=0;questions.sort(function(){return Math.random()-.5;});
document.getElementById('quiz-card').style.display='block';
document.getElementById('results').style.display='none';showQ();}
function showQ(){answered=false;var q=questions[cur];
document.getElementById('progress').style.width=((cur/questions.length)*100)+'%';
document.getElementById('q-count').textContent='Question '+(cur+1)+' of '+questions.length;
document.getElementById('question').textContent=q.q;
var opts=document.getElementById('options');opts.innerHTML='';
q.o.forEach(function(o,i){var b=document.createElement('button');b.className='option';
b.textContent=o;b.onclick=function(){pick(i);};opts.appendChild(b);});}
function pick(i){if(answered)return;answered=true;var q=questions[cur];
var btns=document.getElementById('options').children;btns[q.a].classList.add('correct');
if(i===q.a){score++;}else{btns[i].classList.add('wrong');}
setTimeout(function(){cur++;if(cur<questions.length)showQ();else{
document.getElementById('quiz-card').style.display='none';
document.getElementById('results').style.display='block';
document.getElementById('progress').style.width='100%';
var pct=Math.round((score/questions.length)*100);
document.getElementById('final-score').textContent=score+'/'+questions.length;
var msg=pct>=80?'Excellent!':pct>=60?'Good job!':pct>=40?'Not bad!':'Keep practicing!';
document.getElementById('score-msg').textContent=pct+'% — '+msg;}},800);}
startQuiz();"""
        return self._base_page(title, body, css, js)

    # --- Tic Tac Toe ---
    def _tictactoe_html(self, title, desc):
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center}
.board{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;width:min(90vw,90vh,400px);height:min(90vw,90vh,400px);margin:16px auto}
.cell{width:100%;aspect-ratio:1;background:#fff;border:2px solid #ddd;border-radius:8px;font-size:min(10vw,48px);font-weight:700;cursor:pointer;transition:all .15s;display:flex;align-items:center;justify-content:center}
.cell:hover{background:#fff5f2;border-color:#ff7a59}.cell.x{color:#ff7a59}.cell.o{color:#1c7ed6}
.cell.win{background:#d4edda;border-color:#2ecc71}
.score{display:flex;justify-content:center;gap:30px;margin:10px 0;font-size:15px}"""
        body = """<div class="card">
    <h2 id="status">X's turn</h2>
    <div class="score"><span>X: <strong id="sx">0</strong></span><span>O: <strong id="so">0</strong></span><span>Draws: <strong id="sd">0</strong></span></div>
    <div class="board" id="board"></div>
    <button class="btn-primary" onclick="newGame()">New Game</button>
</div>"""
        js = """var board,turn,over,scores={x:0,o:0,d:0};
function newGame(){board=Array(9).fill('');turn='X';over=false;document.getElementById('status').textContent="X's turn";render();}
function render(){var b=document.getElementById('board');b.innerHTML='';
board.forEach(function(v,i){var c=document.createElement('button');c.className='cell'+(v?' '+v.toLowerCase():'');c.textContent=v;c.onclick=function(){move(i);};b.appendChild(c);});}
function move(i){if(over||board[i])return;board[i]=turn;
var w=checkWin();if(w){over=true;highlight(w);scores[turn.toLowerCase()]++;
document.getElementById('s'+turn.toLowerCase()).textContent=scores[turn.toLowerCase()];
document.getElementById('status').textContent=turn+' wins!';}
else if(board.every(function(c){return c;})){over=true;scores.d++;
document.getElementById('sd').textContent=scores.d;document.getElementById('status').textContent="It's a draw!";}
else{turn=turn==='X'?'O':'X';document.getElementById('status').textContent=turn+"'s turn";}render();}
function checkWin(){var lines=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
for(var i=0;i<lines.length;i++){var l=lines[i];if(board[l[0]]&&board[l[0]]===board[l[1]]&&board[l[1]]===board[l[2]])return l;}return null;}
function highlight(cells){var btns=document.getElementById('board').children;cells.forEach(function(i){btns[i].classList.add('win');});}
newGame();"""
        return self._base_page(title, body, css, js)

    # --- Memory Match ---
    def _memory_game_html(self, title, desc):
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:min(2vw,8px);width:min(90vw,90vh,400px);margin:16px auto}
.mem{width:100%;aspect-ratio:1;border-radius:8px;font-size:min(8vw,32px);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s;border:2px solid #ddd}
.mem.hidden{background:#ff7a59;color:transparent}.mem.hidden:hover{background:#ff6b3f}
.mem.revealed{background:#fff;border-color:#1c7ed6}.mem.matched{background:#d4edda;border-color:#2ecc71;cursor:default}
.stats{display:flex;gap:24px;justify-content:center;margin:10px 0;font-size:15px;color:#555}"""
        body = """<div class="card">
    <h2>Memory Match</h2>
    <div class="stats"><span>Moves: <strong id="moves">0</strong></span><span>Pairs: <strong id="pairs">0</strong>/8</span></div>
    <div class="board" id="board"></div>
    <button class="btn-primary" onclick="startGame()" style="margin-top:12px">New Game</button>
</div>"""
        js = """var emojis=['&#x1F34E;','&#x1F355;','&#x1F3AE;','&#x1F3B8;','&#x2B50;','&#x1F3AF;','&#x1F431;','&#x1F308;'];
var cards,flipped,matched,moves,lock;
function startGame(){var pairs=emojis.concat(emojis);pairs.sort(function(){return Math.random()-.5;});
cards=pairs;flipped=[];matched=new Set();moves=0;lock=false;
document.getElementById('moves').textContent='0';document.getElementById('pairs').textContent='0';
var b=document.getElementById('board');b.innerHTML='';
cards.forEach(function(e,i){var c=document.createElement('div');c.className='mem hidden';c.innerHTML=e;c.dataset.i=i;c.onclick=function(){flip(i);};b.appendChild(c);});}
function flip(i){if(lock||flipped.includes(i)||matched.has(i))return;
var els=document.getElementById('board').children;els[i].className='mem revealed';flipped.push(i);
if(flipped.length===2){moves++;document.getElementById('moves').textContent=moves;lock=true;
var a=flipped[0],b=flipped[1];
if(cards[a]===cards[b]){matched.add(a);matched.add(b);els[a].className='mem matched';els[b].className='mem matched';
document.getElementById('pairs').textContent=(matched.size/2);flipped=[];lock=false;
if(matched.size===cards.length)setTimeout(function(){alert('You won in '+moves+' moves!');},400);}
else{setTimeout(function(){els[a].className='mem hidden';els[b].className='mem hidden';flipped=[];lock=false;},700);}}}
startGame();"""
        return self._base_page(title, body, css, js)

    # --- Calculator ---
    def _calculator_html(self, title, desc):
        css = """.display{background:#1a1b1e;color:#fff;padding:20px;font-size:32px;text-align:right;border-radius:8px;margin-bottom:10px;min-height:60px;word-break:break-all;font-family:'Courier New',monospace}
.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.key{padding:18px;font-size:20px;border-radius:8px;background:#f0f0f0;border:none;cursor:pointer;font-weight:600;transition:all .1s}
.key:hover{background:#e0e0e0}.key:active{transform:scale(.95)}
.key.op{background:#ff7a59;color:#fff}.key.op:hover{background:#ff6b3f}
.key.eq{background:#2ecc71;color:#fff;grid-column:span 2}.key.eq:hover{background:#27ae60}
.key.wide{grid-column:span 2}"""
        body = """<div class="card" style="max-width:340px;margin:0 auto">
    <div class="display" id="display">0</div>
    <div class="keys">
        <button class="key" onclick="press('7')">7</button><button class="key" onclick="press('8')">8</button>
        <button class="key" onclick="press('9')">9</button><button class="key op" onclick="pressOp('/')">&#247;</button>
        <button class="key" onclick="press('4')">4</button><button class="key" onclick="press('5')">5</button>
        <button class="key" onclick="press('6')">6</button><button class="key op" onclick="pressOp('*')">&#215;</button>
        <button class="key" onclick="press('1')">1</button><button class="key" onclick="press('2')">2</button>
        <button class="key" onclick="press('3')">3</button><button class="key op" onclick="pressOp('-')">&#8722;</button>
        <button class="key wide" onclick="press('0')">0</button><button class="key" onclick="press('.')">.</button>
        <button class="key op" onclick="pressOp('+')">+</button>
        <button class="key" onclick="clearAll()">C</button><button class="key" onclick="backspace()">&#9003;</button>
        <button class="key eq" onclick="compute()">=</button>
    </div>
</div>"""
        js = """var current='0',operator='',previous='',fresh=true;
function show(){document.getElementById('display').textContent=current;}
function press(d){if(fresh){current=d==='.'?'0.':d;fresh=false;}else{if(d==='.'&&current.includes('.'))return;current+=d;}show();}
function pressOp(op){if(operator&&!fresh)compute();previous=current;operator=op;fresh=true;}
function compute(){if(!operator||fresh)return;var a=parseFloat(previous),b=parseFloat(current),r=0;
if(operator==='+')r=a+b;else if(operator==='-')r=a-b;else if(operator==='*')r=a*b;
else if(operator==='/'){if(b===0){current='Error';operator='';fresh=true;show();return;}r=a/b;}
current=parseFloat(r.toFixed(10)).toString();operator='';fresh=true;show();}
function clearAll(){current='0';operator='';previous='';fresh=true;show();}
function backspace(){if(fresh)return;current=current.slice(0,-1)||'0';show();}
document.addEventListener('keydown',function(e){if(e.key>='0'&&e.key<='9'||e.key==='.')press(e.key);
else if('+-*/'.includes(e.key))pressOp(e.key);else if(e.key==='Enter'||e.key==='=')compute();
else if(e.key==='Backspace')backspace();else if(e.key==='Escape')clearAll();});"""
        return self._base_page(title, body, css, js)

    # --- Unit Converter ---
    def _converter_html(self, title, desc):
        css = """.group{margin:14px 0;padding:16px;background:#f8f8f8;border-radius:8px;text-align:left}
.group h3{font-size:14px;color:#888;margin-bottom:8px}
.row{display:flex;gap:8px;align-items:center}
.row input,.row select{flex:1;margin-bottom:0}
.row span{font-weight:600;color:#888;flex-shrink:0}"""
        body = """<div class="card" style="max-width:500px;margin:0 auto;text-align:left">
    <h2 style="text-align:center">Unit Converter</h2>
    <div class="group"><h3>Temperature</h3>
        <div class="row"><input type="number" id="tv" value="100" oninput="ct()">
        <select id="tf" onchange="ct()"><option value="c">C</option><option value="f">F</option><option value="k">K</option></select>
        <span>&rarr;</span><input id="tr" readonly style="background:#eee">
        <select id="tt" onchange="ct()"><option value="f">F</option><option value="c">C</option><option value="k">K</option></select></div></div>
    <div class="group"><h3>Length</h3>
        <div class="row"><input type="number" id="lv" value="1" oninput="cl()">
        <select id="lf" onchange="cl()"><option value="m">m</option><option value="ft">ft</option><option value="km">km</option><option value="mi">mi</option><option value="cm">cm</option></select>
        <span>&rarr;</span><input id="lr" readonly style="background:#eee">
        <select id="lt" onchange="cl()"><option value="ft">ft</option><option value="m">m</option><option value="km">km</option><option value="mi">mi</option><option value="cm">cm</option></select></div></div>
    <div class="group"><h3>Weight</h3>
        <div class="row"><input type="number" id="wv" value="1" oninput="cw()">
        <select id="wf" onchange="cw()"><option value="kg">kg</option><option value="lb">lb</option><option value="oz">oz</option><option value="g">g</option></select>
        <span>&rarr;</span><input id="wr" readonly style="background:#eee">
        <select id="wt" onchange="cw()"><option value="lb">lb</option><option value="kg">kg</option><option value="oz">oz</option><option value="g">g</option></select></div></div>
</div>"""
        js = """function ct(){var v=parseFloat(document.getElementById('tv').value),f=document.getElementById('tf').value,t=document.getElementById('tt').value;
var c=f==='c'?v:f==='f'?(v-32)*5/9:v-273.15;var r=t==='c'?c:t==='f'?c*9/5+32:c+273.15;
document.getElementById('tr').value=isNaN(r)?'':r.toFixed(2);}
var lf={m:1,ft:0.3048,km:1000,mi:1609.344,cm:0.01};
function cl(){var v=parseFloat(document.getElementById('lv').value),f=document.getElementById('lf').value,t=document.getElementById('lt').value;
document.getElementById('lr').value=isNaN(v)?'':(v*lf[f]/lf[t]).toFixed(4);}
var wf={kg:1,lb:0.453592,oz:0.0283495,g:0.001};
function cw(){var v=parseFloat(document.getElementById('wv').value),f=document.getElementById('wf').value,t=document.getElementById('wt').value;
document.getElementById('wr').value=isNaN(v)?'':(v*wf[f]/wf[t]).toFixed(4);}
ct();cl();cw();"""
        return self._base_page(title, body, css, js)

    # --- Timer / Pomodoro ---
    def _timer_html(self, title, desc):
        css = """.time{font-size:72px;font-weight:700;font-family:'Courier New',monospace;margin:20px 0;color:#1a1b1e}
.presets{display:flex;gap:8px;justify-content:center;margin-bottom:16px;flex-wrap:wrap}
.presets button{font-size:13px;padding:8px 14px}
.controls{display:flex;gap:10px;justify-content:center}"""
        body = """<div class="card">
    <h2>Timer</h2>
    <div class="presets">
        <button class="btn-secondary" onclick="set(1)">1 min</button>
        <button class="btn-secondary" onclick="set(5)">5 min</button>
        <button class="btn-secondary" onclick="set(15)">15 min</button>
        <button class="btn-secondary" onclick="set(25)">25 min</button>
        <button class="btn-secondary" onclick="set(60)">60 min</button>
    </div>
    <div class="time" id="display">25:00</div>
    <div class="controls">
        <button class="btn-primary" id="btn-go" onclick="toggle()">Start</button>
        <button class="btn-secondary" onclick="reset()">Reset</button>
    </div>
</div>"""
        js = """var total=25*60,remain=25*60,iv=null,on=false;
function fmt(s){var m=Math.floor(s/60),sec=s%60;return String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');}
function show(){document.getElementById('display').textContent=fmt(remain);document.getElementById('display').style.color=remain<=10&&remain>0?'#e74c3c':'#1a1b1e';}
function set(min){stop();total=min*60;remain=total;show();}
function toggle(){on?stop():start();}
function start(){if(remain<=0)return;on=true;document.getElementById('btn-go').textContent='Pause';
iv=setInterval(function(){remain--;show();if(remain<=0){stop();document.getElementById('display').style.color='#2ecc71';alert('Time is up!');}},1000);}
function stop(){on=false;clearInterval(iv);iv=null;document.getElementById('btn-go').textContent='Start';}
function reset(){stop();remain=total;show();}
show();"""
        return self._base_page(title, body, css, js)

    # --- Jigsaw / Image Puzzle ---
    def _jigsaw_html(self, title, desc):
        """Image puzzle: upload an image, split into pieces, drag to reassemble."""
        features = extract_features(desc)
        # Default 3x3, can be 2-6
        size = 3
        if "grid_size" in features:
            try:
                size = int(features["grid_size"].value)
                size = max(2, min(6, size))
            except ValueError:
                size = 3

        css = """*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%;font-family:system-ui,sans-serif;background:#1a1a2e}
.container{min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px;color:#fff}
h2{margin-bottom:10px}
.upload-area{width:min(90vw,400px);padding:30px;border:3px dashed #4a4a6a;border-radius:12px;text-align:center;margin:20px 0;cursor:pointer;transition:all .2s}
.upload-area:hover{border-color:#ff7a59;background:#2a2a4a}
.upload-area.hidden{display:none}
#file-input{display:none}
.game-area{display:none;flex-direction:column;align-items:center;width:100%}
.game-area.active{display:flex}
.boards{display:flex;gap:20px;flex-wrap:wrap;justify-content:center;margin:20px 0}
.board-container{display:flex;flex-direction:column;align-items:center}
.board-label{font-size:14px;color:#888;margin-bottom:8px}
.board{display:grid;gap:2px;background:#333;padding:2px;border-radius:8px}
.piece{background-size:cover;background-position:center;border-radius:4px;cursor:grab;transition:transform .15s,box-shadow .15s}
.piece:hover{transform:scale(1.05);box-shadow:0 4px 12px rgba(255,122,89,.5)}
.piece.dragging{opacity:.6;cursor:grabbing}
.slot{background:#2a2a4a;border:2px dashed #4a4a6a;border-radius:4px}
.slot.correct{border-color:#2ecc71;background:#1a3a2a}
.slot.highlight{border-color:#ff7a59;background:#3a2a3a}
.info{font-size:14px;color:#aaa;margin:10px 0}
.btn{padding:10px 24px;font-size:16px;border:none;border-radius:8px;cursor:pointer;margin:5px}
.btn-primary{background:#ff7a59;color:#fff}.btn-primary:hover{background:#ff6b3f}
.btn-secondary{background:#4a4a6a;color:#fff}.btn-secondary:hover{background:#5a5a7a}
.win-msg{font-size:24px;color:#2ecc71;margin:15px 0;animation:pulse 1s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}"""

        body = f"""<div class="container">
<h2>Image Puzzle</h2>
<p style="color:#888;margin-bottom:15px">Upload an image to turn it into a {size}x{size} puzzle</p>

<div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
    <p style="font-size:18px;margin-bottom:10px">Click to upload an image</p>
    <p style="color:#888">or drag and drop</p>
    <input type="file" id="file-input" accept="image/*">
</div>

<div class="game-area" id="game-area">
    <div class="boards">
        <div class="board-container">
            <div class="board-label">Scrambled Pieces</div>
            <div class="board" id="pieces-board"></div>
        </div>
        <div class="board-container">
            <div class="board-label">Your Puzzle</div>
            <div class="board" id="puzzle-board"></div>
        </div>
    </div>
    <p class="info">Pieces placed: <strong id="placed">0</strong> / <strong id="total">{size*size}</strong></p>
    <p class="win-msg" id="win-msg" style="display:none">Puzzle Complete!</p>
    <div>
        <button class="btn btn-secondary" onclick="resetPuzzle()">Reset</button>
        <button class="btn btn-primary" onclick="newImage()">New Image</button>
    </div>
</div>
</div>"""

        js = f"""var SIZE={size};
var pieces=[],slots=[],imgUrl='',draggedPiece=null,draggedIdx=-1;

document.getElementById('file-input').addEventListener('change',function(e){{
    if(e.target.files&&e.target.files[0])loadImage(e.target.files[0]);
}});

var uploadArea=document.getElementById('upload-area');
uploadArea.addEventListener('dragover',function(e){{e.preventDefault();e.stopPropagation();this.style.borderColor='#ff7a59';}});
uploadArea.addEventListener('dragleave',function(e){{e.preventDefault();e.stopPropagation();this.style.borderColor='#4a4a6a';}});
uploadArea.addEventListener('drop',function(e){{
    e.preventDefault();e.stopPropagation();this.style.borderColor='#4a4a6a';
    if(e.dataTransfer.files&&e.dataTransfer.files[0])loadImage(e.dataTransfer.files[0]);
}});

function loadImage(file){{
    var reader=new FileReader();
    reader.onload=function(e){{imgUrl=e.target.result;startGame();}};
    reader.readAsDataURL(file);
}}

function startGame(){{
    document.getElementById('upload-area').classList.add('hidden');
    document.getElementById('game-area').classList.add('active');
    document.getElementById('win-msg').style.display='none';
    
    // Create pieces array with correct positions
    pieces=[];for(var i=0;i<SIZE*SIZE;i++)pieces.push(i);
    
    // Shuffle pieces
    for(var i=pieces.length-1;i>0;i--){{
        var j=Math.floor(Math.random()*(i+1));
        var t=pieces[i];pieces[i]=pieces[j];pieces[j]=t;
    }}
    
    // Reset slots
    slots=[];for(var i=0;i<SIZE*SIZE;i++)slots.push(-1);
    
    render();
}}

function render(){{
    var cellSize=Math.min(80,Math.floor((window.innerWidth-100)/SIZE/2.5));
    var boardSize=cellSize*SIZE+(SIZE-1)*2+4;
    
    var piecesBoard=document.getElementById('pieces-board');
    var puzzleBoard=document.getElementById('puzzle-board');
    
    piecesBoard.style.gridTemplateColumns='repeat('+SIZE+','+cellSize+'px)';
    puzzleBoard.style.gridTemplateColumns='repeat('+SIZE+','+cellSize+'px)';
    
    // Render pieces board (scrambled pieces not yet placed)
    piecesBoard.innerHTML='';
    pieces.forEach(function(p,i){{
        var div=document.createElement('div');
        div.style.width=cellSize+'px';
        div.style.height=cellSize+'px';
        if(p===-1){{
            div.className='slot';
        }}else{{
            div.className='piece';
            var row=Math.floor(p/SIZE),col=p%SIZE;
            div.style.backgroundImage='url('+imgUrl+')';
            div.style.backgroundSize=(SIZE*100)+'% '+(SIZE*100)+'%';
            div.style.backgroundPosition=(col*100/(SIZE-1))+'% '+(row*100/(SIZE-1))+'%';
            div.draggable=true;
            div.dataset.idx=i;
            div.dataset.piece=p;
            div.ondragstart=function(e){{dragStart(e,i,'pieces');}};
            div.ondragend=dragEnd;
        }}
        piecesBoard.appendChild(div);
    }});
    
    // Render puzzle board (target slots)
    puzzleBoard.innerHTML='';
    slots.forEach(function(s,i){{
        var div=document.createElement('div');
        div.style.width=cellSize+'px';
        div.style.height=cellSize+'px';
        div.dataset.slot=i;
        if(s===-1){{
            div.className='slot';
            div.ondragover=function(e){{e.preventDefault();this.classList.add('highlight');}};
            div.ondragleave=function(){{this.classList.remove('highlight');}};
            div.ondrop=function(e){{dropOnSlot(e,i);}};
        }}else{{
            div.className='piece';
            if(s===i)div.classList.add('correct');
            var row=Math.floor(s/SIZE),col=s%SIZE;
            div.style.backgroundImage='url('+imgUrl+')';
            div.style.backgroundSize=(SIZE*100)+'% '+(SIZE*100)+'%';
            div.style.backgroundPosition=(col*100/(SIZE-1))+'% '+(row*100/(SIZE-1))+'%';
            div.draggable=true;
            div.ondragstart=function(e){{dragStart(e,i,'puzzle');}};
            div.ondragend=dragEnd;
        }}
        puzzleBoard.appendChild(div);
    }});
    
    // Update count
    var placed=slots.filter(function(s){{return s!==-1;}}).length;
    document.getElementById('placed').textContent=placed;
    
    // Check win
    if(placed===SIZE*SIZE){{
        var won=true;
        for(var i=0;i<SIZE*SIZE;i++)if(slots[i]!==i){{won=false;break;}}
        if(won)document.getElementById('win-msg').style.display='block';
    }}
}}

var dragSource='';
function dragStart(e,idx,source){{
    draggedIdx=idx;dragSource=source;
    e.target.classList.add('dragging');
}}
function dragEnd(e){{e.target.classList.remove('dragging');draggedIdx=-1;}}

function dropOnSlot(e,slotIdx){{
    e.preventDefault();
    e.target.classList.remove('highlight');
    if(draggedIdx===-1)return;
    
    var piece;
    if(dragSource==='pieces'){{
        piece=pieces[draggedIdx];
        pieces[draggedIdx]=-1;
    }}else{{
        piece=slots[draggedIdx];
        slots[draggedIdx]=-1;
    }}
    
    // If slot has a piece, move it back to pieces
    if(slots[slotIdx]!==-1){{
        var oldPiece=slots[slotIdx];
        // Find empty spot in pieces
        for(var i=0;i<pieces.length;i++){{
            if(pieces[i]===-1){{pieces[i]=oldPiece;break;}}
        }}
    }}
    
    slots[slotIdx]=piece;
    render();
}}

function resetPuzzle(){{
    // Move all pieces back
    pieces=[];for(var i=0;i<SIZE*SIZE;i++)pieces.push(-1);
    var idx=0;
    for(var i=0;i<SIZE*SIZE;i++){{
        if(slots[i]!==-1){{pieces[idx++]=slots[i];}}
    }}
    // Re-shuffle
    for(var i=idx-1;i>0;i--){{
        var j=Math.floor(Math.random()*(i+1));
        var t=pieces[i];pieces[i]=pieces[j];pieces[j]=t;
    }}
    slots=[];for(var i=0;i<SIZE*SIZE;i++)slots.push(-1);
    document.getElementById('win-msg').style.display='none';
    render();
}}

function newImage(){{
    document.getElementById('upload-area').classList.remove('hidden');
    document.getElementById('game-area').classList.remove('active');
    document.getElementById('file-input').value='';
}}
"""
        return self._base_page(title, body, css, js)

    # --- Sliding Tile Puzzle ---
    def _sliding_puzzle_html(self, title, desc):
        # Extract grid size and layout features (inspired by PrettyFoto Puzzles)
        features = extract_features(desc)
        size = 3
        if "grid_size" in features:
            try:
                size = int(features["grid_size"].value)
                if size < 2:
                    size = 3
                if size > 6:
                    size = 6
            except ValueError:
                size = 3

        # Check for explicit fixed-size request
        use_fixed = "fixed_size" in features

        if use_fixed:
            cell_px = max(60, 280 // size)
            board_px = cell_px * size + (size - 1) * 4
            css = f"""*{{box-sizing:border-box}}
.card{{padding:20px;text-align:center}}
.board{{display:grid;grid-template-columns:repeat({size},{cell_px}px);gap:4px;width:{board_px}px;margin:16px auto}}
.tile{{width:{cell_px}px;height:{cell_px}px;display:flex;align-items:center;justify-content:center;font-size:{max(16, 36 - size * 4)}px;font-weight:700;border-radius:8px;cursor:pointer;transition:all .15s;user-select:none}}
.tile.num{{background:#ff7a59;color:#fff;border:2px solid #e8694a}}.tile.num:hover{{background:#ff6b3f;transform:scale(1.03)}}
.tile.empty{{background:#f0f0f0;border:2px dashed #ccc;cursor:default}}
.stats{{font-size:13px;color:#666;margin:8px 0}}.stats span{{margin:0 8px}}
.difficulty{{font-size:12px;color:#888;margin:4px 0}}
.moves{{font-size:15px;color:#888;margin:10px 0}}
.win{{animation:celebrate .6s ease-in-out}}
@keyframes celebrate{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}"""
        else:
            # Responsive (default)
            css = f"""*{{box-sizing:border-box}}html,body{{margin:0;min-height:100%;overflow:auto}}
.card{{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}}
.board{{display:grid;grid-template-columns:repeat({size},1fr);gap:4px;width:min(90vw,90vh,400px);margin:16px auto}}
.tile{{aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:clamp(14px,calc(80vw/{size}/2),{max(20, 40 - size * 4)}px);font-weight:700;border-radius:8px;cursor:pointer;transition:all .15s;user-select:none}}
.tile.num{{background:#ff7a59;color:#fff;border:2px solid #e8694a}}.tile.num:hover{{background:#ff6b3f;transform:scale(1.03)}}
.tile.empty{{background:#f0f0f0;border:2px dashed #ccc;cursor:default}}
.stats{{font-size:13px;color:#666;margin:8px 0}}.stats span{{margin:0 8px}}
.difficulty{{font-size:12px;color:#888;margin:4px 0}}
.moves{{font-size:15px;color:#888;margin:10px 0}}
.win{{animation:celebrate .6s ease-in-out}}
@keyframes celebrate{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}"""

        body = f"""<div class="card">
    <h2>Sliding Puzzle ({size}×{size})</h2>
    <p class="stats"><span>Wins: <strong id="wins">0</strong></span><span>Streak: <strong id="streak">0</strong></span></p>
    <p class="difficulty" id="diffLabel">Difficulty: Easy</p>
    <p class="moves">Moves: <strong id="moves">0</strong></p>
    <div class="board" id="board"></div>
    <button class="btn-primary" onclick="newGame()" style="margin-top:12px">Shuffle</button>
</div>"""

        # Enhanced JS with progressive difficulty from PrettyFoto
        js = f"""var SIZE={size},board,emptyIdx,moves,won,shuffleSeed=Date.now();
var stats={{won:0,streak:0,bestStreak:0}};
try{{var s=localStorage.getItem('slidingPuzzleStats');if(s)stats=JSON.parse(s);}}catch(e){{}}
function saveStats(){{try{{localStorage.setItem('slidingPuzzleStats',JSON.stringify(stats));}}catch(e){{}}}}
function updateStatsUI(){{document.getElementById('wins').textContent=stats.won;document.getElementById('streak').textContent=stats.streak;
  var pct=Math.min(stats.won,10)/10;var labels=['Easy','Medium','Challenging','Hard','Expert'];
  document.getElementById('diffLabel').textContent='Difficulty: '+labels[Math.min(Math.floor(pct*5),4)];}}
function seededRandom(s){{s=Math.sin(s)*10000;return s-Math.floor(s);}}
function getNeighbors(idx){{var n=[],row=Math.floor(idx/SIZE),col=idx%SIZE;
  if(row>0)n.push(idx-SIZE);if(row<SIZE-1)n.push(idx+SIZE);
  if(col>0)n.push(idx-1);if(col<SIZE-1)n.push(idx+1);return n;}}
function countInversions(){{var arr=[],blank=SIZE*SIZE-1;
  for(var i=0;i<SIZE*SIZE;i++)if(board[i]!==blank)arr.push(board[i]);
  var inv=0;for(var i=0;i<arr.length;i++)for(var j=i+1;j<arr.length;j++)if(arr[i]>arr[j])inv++;return inv;}}
function isSolvable(){{var inv=countInversions(),emptyRow=Math.floor(emptyIdx/SIZE),fromBottom=SIZE-1-emptyRow;
  return(inv+fromBottom)%2===0;}}
function ensureSolvable(){{if(isSolvable())return;var blank=SIZE*SIZE-1,a=-1,b=-1;
  for(var i=0;i<SIZE*SIZE&&b===-1;i++){{if(board[i]===blank)continue;if(a===-1){{a=i;continue;}}b=i;}}
  if(a!==-1&&b!==-1){{var t=board[a];board[a]=board[b];board[b]=t;}}}}
function shuffleTiles(){{var total=SIZE*SIZE;board=[];for(var i=0;i<total;i++)board.push(i);emptyIdx=total-1;
  var baseMoves=SIZE*SIZE*20,minMoves=5,winsForFull=10;
  var progress=Math.min(stats.won,winsForFull)/winsForFull;
  var shuffleMoves=Math.round(minMoves+(baseMoves-minMoves)*progress);
  for(var i=0;i<shuffleMoves;i++){{var neighbors=getNeighbors(emptyIdx);
    var ri=Math.floor(seededRandom(shuffleSeed+i)*neighbors.length);var ni=neighbors[ri];
    board[emptyIdx]=board[ni];board[ni]=total-1;emptyIdx=ni;}}
  ensureSolvable();}}
function newGame(){{shuffleSeed=Date.now();shuffleTiles();moves=0;won=false;
  document.getElementById('moves').textContent='0';render();updateStatsUI();}}
function render(){{var b=document.getElementById('board');b.innerHTML='';
  board.forEach(function(v,i){{var d=document.createElement('div');
    if(v===SIZE*SIZE-1){{d.className='tile empty';}}
    else{{d.className='tile num';d.textContent=v+1;d.onclick=function(){{clickTile(i);}};}}
    b.appendChild(d);}});
  if(won)b.classList.add('win');else b.classList.remove('win');}}
function clickTile(i){{if(won)return;var row=Math.floor(i/SIZE),col=i%SIZE,er=Math.floor(emptyIdx/SIZE),ec=emptyIdx%SIZE;
  if((Math.abs(row-er)+Math.abs(col-ec))!==1)return;
  board[emptyIdx]=board[i];board[i]=SIZE*SIZE-1;emptyIdx=i;
  moves++;document.getElementById('moves').textContent=moves;
  if(checkWin()){{won=true;stats.won++;stats.streak++;if(stats.streak>stats.bestStreak)stats.bestStreak=stats.streak;saveStats();}}
  render();if(won){{updateStatsUI();setTimeout(function(){{alert('Solved in '+moves+' moves!');}},300);}}}}
function checkWin(){{for(var i=0;i<SIZE*SIZE-1;i++)if(board[i]!==i)return false;return true;}}
updateStatsUI();newGame();"""
        return self._base_page(title, body, css, js)

    # --- Hangman ---
    def _hangman_html(self, title, desc):
        css = """.word{font-size:36px;letter-spacing:12px;font-weight:700;margin:20px 0;font-family:'Courier New',monospace}
.keyboard{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;max-width:420px;margin:16px auto}
.key{width:38px;height:42px;border-radius:6px;font-size:16px;font-weight:700;background:#f0f0f0;border:none;cursor:pointer}
.key:hover{background:#ff7a59;color:#fff}.key.used{opacity:.3;cursor:default}.key.hit{background:#2ecc71;color:#fff}
.key.miss{background:#e74c3c;color:#fff;opacity:.5}
.hangman-drawing{font-size:14px;font-family:'Courier New',monospace;white-space:pre;line-height:1.3;margin:10px 0;color:#e74c3c}
.status{font-size:18px;font-weight:600;margin:10px 0}"""
        body = """<div class="card">
    <h2>Hangman</h2>
    <div class="hangman-drawing" id="drawing"></div>
    <div class="word" id="word"></div>
    <div class="status" id="status"></div>
    <div class="keyboard" id="keyboard"></div>
    <button class="btn-primary" onclick="newGame()" id="btn-new" style="margin-top:12px;display:none">New Word</button>
</div>"""
        js = r"""var WORDS=["PYTHON","JAVASCRIPT","ALGORITHM","FUNCTION","VARIABLE","BROWSER","KEYBOARD","PROGRAM","DATABASE","NETWORK",
"ABSTRACT","COMPILER","LIBRARY","CONSOLE","INTEGER","BOOLEAN","ELEMENT","FRAMEWORK","SYNTAX","MODULE"];
var word,guessed,wrong,maxWrong=6,over;
var STAGES=["","  O","  O\n  |","  O\n /|","  O\n /|\\","  O\n /|\\\n /","  O\n /|\\\n / \\"];
function newGame(){word=WORDS[Math.floor(Math.random()*WORDS.length)];guessed=new Set();wrong=0;over=false;
document.getElementById('btn-new').style.display='none';document.getElementById('status').textContent='';
buildKeyboard();render();}
function buildKeyboard(){var kb=document.getElementById('keyboard');kb.innerHTML='';
'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach(function(ch){
var b=document.createElement('button');b.className='key';b.textContent=ch;
b.onclick=function(){guess(ch,b);};kb.appendChild(b);});}
function guess(ch,btn){if(over||guessed.has(ch))return;guessed.add(ch);
if(word.includes(ch)){btn.classList.add('used','hit');}
else{wrong++;btn.classList.add('used','miss');}
render();checkEnd();}
function render(){
document.getElementById('word').textContent=word.split('').map(function(c){return guessed.has(c)?c:'_';}).join('');
document.getElementById('drawing').textContent="  -----\n  |   |\n"+(STAGES[wrong]||"")+"\n  |\n=====";
}
function checkEnd(){var won=word.split('').every(function(c){return guessed.has(c);});
if(won){over=true;document.getElementById('status').innerHTML='You won! &#127881;';document.getElementById('status').style.color='#2ecc71';document.getElementById('btn-new').style.display='inline-block';}
else if(wrong>=maxWrong){over=true;document.getElementById('word').textContent=word;document.getElementById('status').textContent='Game over! The word was '+word;document.getElementById('status').style.color='#e74c3c';document.getElementById('btn-new').style.display='inline-block';}}
document.addEventListener('keydown',function(e){var ch=e.key.toUpperCase();if(ch.length===1&&ch>='A'&&ch<='Z'){
var btn=document.querySelector('.key:not(.used)');
var btns=document.getElementById('keyboard').children;
for(var i=0;i<btns.length;i++){if(btns[i].textContent===ch&&!btns[i].classList.contains('used')){guess(ch,btns[i]);break;}}}});
newGame();"""
        return self._base_page(title, body, css, js)

    # --- Wordle-style ---
    def _wordle_html(self, title, desc):
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:min(1.5vw,6px);width:min(90vw,45vh,350px);margin:16px auto}
.cell{width:100%;aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:min(6vw,24px);font-weight:700;
border:2px solid #ddd;border-radius:6px;text-transform:uppercase;transition:all .3s}
.cell.correct{background:#2ecc71;color:#fff;border-color:#2ecc71}
.cell.present{background:#f1c40f;color:#fff;border-color:#f1c40f}
.cell.absent{background:#888;color:#fff;border-color:#888}
.cell.filled{border-color:#999}
.kb{display:flex;flex-wrap:wrap;justify-content:center;gap:min(1vw,4px);max-width:min(95vw,480px);margin:12px auto}
.kb button{min-width:min(8vw,32px);height:min(10vw,42px);border-radius:6px;font-size:min(3.5vw,13px);font-weight:700;background:#ddd;border:none;cursor:pointer}
.kb button:hover{background:#ccc}
.kb button.correct{background:#2ecc71;color:#fff}.kb button.present{background:#f1c40f;color:#fff}
.kb button.absent{background:#888;color:#fff}
.msg{font-size:18px;font-weight:600;margin:8px 0;min-height:28px}"""
        body = """<div class="card">
    <h2>Wordle</h2>
    <p class="msg" id="msg"></p>
    <div class="grid" id="grid"></div>
    <div class="kb" id="kb"></div>
    <button class="btn-primary" onclick="newGame()" id="btn-new" style="margin-top:12px;display:none">New Game</button>
</div>"""
        js = r"""var WORDS=["CRANE","SLATE","TRACE","AUDIO","RAISE","STARE","ARISE","TEARS","LEARN","CROWN",
"FLAME","GHOST","BRAVE","DROWN","FUNGI","JUICE","KNELT","PLUMB","QUERY","SWIRL",
"FLASK","PIXEL","GRAPH","STORM","WITCH","BLAZE","CHUNK","DRIFT","FROST","GRIND"];
var VALID=new Set(WORDS);
var word,guesses,current,over,maxGuesses=6;
function newGame(){word=WORDS[Math.floor(Math.random()*WORDS.length)];guesses=[];current='';over=false;
document.getElementById('msg').textContent='';document.getElementById('btn-new').style.display='none';
buildGrid();buildKB();}
function buildGrid(){var g=document.getElementById('grid');g.innerHTML='';
for(var r=0;r<maxGuesses;r++)for(var c=0;c<5;c++){var d=document.createElement('div');d.className='cell';d.id='c'+r+'_'+c;g.appendChild(d);}}
function buildKB(){var kb=document.getElementById('kb');kb.innerHTML='';
'QWERTYUIOP ASDFGHJKL ZXCVBNM'.split(' ').forEach(function(row){
row.split('').forEach(function(ch){var b=document.createElement('button');b.textContent=ch;b.id='kb_'+ch;
b.onclick=function(){typeLetter(ch);};kb.appendChild(b);});
if(row==='ASDFGHJKL'){var bk=document.createElement('button');bk.textContent='⌫';bk.style.minWidth='48px';bk.onclick=backspace;kb.appendChild(bk);}
if(row==='ZXCVBNM'){var en=document.createElement('button');en.textContent='ENTER';en.style.minWidth='56px';en.onclick=submitGuess;kb.appendChild(en);}});}
function typeLetter(ch){if(over||current.length>=5)return;current+=ch;updateRow();}
function backspace(){if(over||current.length===0)return;current=current.slice(0,-1);updateRow();}
function updateRow(){var r=guesses.length;for(var c=0;c<5;c++){var cell=document.getElementById('c'+r+'_'+c);
cell.textContent=current[c]||'';cell.className='cell'+(current[c]?' filled':'');}}
function submitGuess(){if(over||current.length!==5)return;
var row=guesses.length;var result=checkWord(current);
for(var c=0;c<5;c++){var cell=document.getElementById('c'+row+'_'+c);cell.className='cell '+result[c];
var kb=document.getElementById('kb_'+current[c]);if(kb){
if(result[c]==='correct')kb.className='correct';
else if(result[c]==='present'&&kb.className!=='correct')kb.className='present';
else if(result[c]==='absent'&&kb.className==='')kb.className='absent';}}
guesses.push(current);
if(current===word){over=true;document.getElementById('msg').innerHTML='You got it in '+(guesses.length)+' tries! &#127881;';
document.getElementById('msg').style.color='#2ecc71';document.getElementById('btn-new').style.display='inline-block';}
else if(guesses.length>=maxGuesses){over=true;document.getElementById('msg').textContent='The word was '+word;
document.getElementById('msg').style.color='#e74c3c';document.getElementById('btn-new').style.display='inline-block';}
current='';}
function checkWord(g){var result=Array(5).fill('absent');var wArr=word.split('');var gArr=g.split('');
// First pass: exact matches
for(var i=0;i<5;i++){if(gArr[i]===wArr[i]){result[i]='correct';wArr[i]=null;gArr[i]=null;}}
// Second pass: present but wrong position
for(var i=0;i<5;i++){if(gArr[i]){var idx=wArr.indexOf(gArr[i]);if(idx!==-1){result[i]='present';wArr[idx]=null;}}}
return result;}
document.addEventListener('keydown',function(e){if(e.key==='Enter')submitGuess();
else if(e.key==='Backspace')backspace();
else{var ch=e.key.toUpperCase();if(ch.length===1&&ch>='A'&&ch<='Z')typeLetter(ch);}});
newGame();"""
        return self._base_page(title, body, css, js)

    # --- Algorithm Visualizer (from ML-ToolBox patterns) ---
    def _algorithm_visualizer_html(self, title, desc):
        css = """*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:auto}
.card{min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}
.controls{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin:16px 0}
.controls select,.controls button{padding:8px 16px;border-radius:6px;font-size:14px;border:1px solid #ddd}
.controls button{background:#ff7a59;color:#fff;border:none;cursor:pointer;font-weight:600}
.controls button:hover{background:#e8694a}
.controls button:disabled{background:#ccc;cursor:not-allowed}
.viz-area{display:flex;align-items:flex-end;justify-content:center;gap:2px;height:300px;padding:20px;background:#f9f9f9;border-radius:12px;margin:16px 0;width:min(90vw,600px)}
.bar{background:#ff7a59;border-radius:4px 4px 0 0;transition:height .15s,background .15s;min-width:8px;flex:1;max-width:30px}
.bar.comparing{background:#3498db}
.bar.swapping{background:#e74c3c}
.bar.sorted{background:#2ecc71}
.bar.pivot{background:#9b59b6}
.info{font-size:14px;color:#666;margin:8px 0}
.info span{margin:0 12px}
.legend{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-top:12px}
.legend-item{display:flex;align-items:center;gap:6px;font-size:12px}
.legend-color{width:16px;height:16px;border-radius:3px}"""
        body = """<div class="card">
    <h2>Algorithm Visualizer</h2>
    <p style="color:#888;margin:4px 0">Watch sorting algorithms in action!</p>
    <div class="controls">
        <select id="algo">
            <option value="bubble">Bubble Sort</option>
            <option value="selection">Selection Sort</option>
            <option value="insertion">Insertion Sort</option>
            <option value="quick">Quick Sort</option>
            <option value="merge">Merge Sort</option>
        </select>
        <select id="size">
            <option value="10">10 bars</option>
            <option value="20" selected>20 bars</option>
            <option value="30">30 bars</option>
            <option value="50">50 bars</option>
        </select>
        <select id="speed">
            <option value="500">Slow</option>
            <option value="150" selected>Medium</option>
            <option value="30">Fast</option>
        </select>
        <button id="startBtn" onclick="startSort()">Start</button>
        <button onclick="reset()">Reset</button>
    </div>
    <div class="info">
        <span>Comparisons: <strong id="comps">0</strong></span>
        <span>Swaps: <strong id="swaps">0</strong></span>
    </div>
    <div class="viz-area" id="viz"></div>
    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background:#ff7a59"></div>Unsorted</div>
        <div class="legend-item"><div class="legend-color" style="background:#3498db"></div>Comparing</div>
        <div class="legend-item"><div class="legend-color" style="background:#e74c3c"></div>Swapping</div>
        <div class="legend-item"><div class="legend-color" style="background:#9b59b6"></div>Pivot</div>
        <div class="legend-item"><div class="legend-color" style="background:#2ecc71"></div>Sorted</div>
    </div>
</div>"""
        js = r"""var arr=[],running=false,delay=150,comps=0,swaps=0;
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function reset(){running=false;comps=0;swaps=0;document.getElementById('comps').textContent='0';
  document.getElementById('swaps').textContent='0';document.getElementById('startBtn').disabled=false;
  var n=parseInt(document.getElementById('size').value);arr=[];
  for(var i=0;i<n;i++)arr.push(Math.floor(Math.random()*250)+10);render();}
function render(hi1,hi2,pivotIdx,sorted){var v=document.getElementById('viz');v.innerHTML='';
  arr.forEach(function(h,i){var b=document.createElement('div');b.className='bar';
    if(sorted&&sorted.includes(i))b.classList.add('sorted');
    else if(i===pivotIdx)b.classList.add('pivot');
    else if(i===hi1||i===hi2)b.classList.add(hi1!==undefined&&hi2!==undefined?'swapping':'comparing');
    b.style.height=h+'px';v.appendChild(b);});}
async function bubbleSort(){var n=arr.length;
  for(var i=0;i<n-1&&running;i++){for(var j=0;j<n-i-1&&running;j++){
    comps++;document.getElementById('comps').textContent=comps;render(j,j+1);await sleep(delay);
    if(arr[j]>arr[j+1]){var t=arr[j];arr[j]=arr[j+1];arr[j+1]=t;swaps++;
      document.getElementById('swaps').textContent=swaps;render(j,j+1);await sleep(delay);}}}}
async function selectionSort(){var n=arr.length;
  for(var i=0;i<n-1&&running;i++){var minIdx=i;
    for(var j=i+1;j<n&&running;j++){comps++;document.getElementById('comps').textContent=comps;
      render(minIdx,j);await sleep(delay);if(arr[j]<arr[minIdx])minIdx=j;}
    if(minIdx!==i){var t=arr[i];arr[i]=arr[minIdx];arr[minIdx]=t;swaps++;
      document.getElementById('swaps').textContent=swaps;render(i,minIdx);await sleep(delay);}}}
async function insertionSort(){var n=arr.length;
  for(var i=1;i<n&&running;i++){var key=arr[i],j=i-1;
    while(j>=0&&arr[j]>key&&running){comps++;document.getElementById('comps').textContent=comps;
      render(j,j+1);await sleep(delay);arr[j+1]=arr[j];swaps++;
      document.getElementById('swaps').textContent=swaps;j--;}
    arr[j+1]=key;render();await sleep(delay);}}
async function quickSort(lo,hi){if(lo>=hi||!running)return;
  var pivot=arr[hi],i=lo-1;
  for(var j=lo;j<hi&&running;j++){comps++;document.getElementById('comps').textContent=comps;
    render(j,hi,hi);await sleep(delay);
    if(arr[j]<pivot){i++;var t=arr[i];arr[i]=arr[j];arr[j]=t;swaps++;
      document.getElementById('swaps').textContent=swaps;render(i,j,hi);await sleep(delay);}}
  var t=arr[i+1];arr[i+1]=arr[hi];arr[hi]=t;swaps++;
  document.getElementById('swaps').textContent=swaps;render(i+1,hi);await sleep(delay);
  await quickSort(lo,i);await quickSort(i+2,hi);}
async function mergeSort(l,r){if(l>=r||!running)return;var m=Math.floor((l+r)/2);
  await mergeSort(l,m);await mergeSort(m+1,r);
  var left=arr.slice(l,m+1),right=arr.slice(m+1,r+1),i=0,j=0,k=l;
  while(i<left.length&&j<right.length&&running){comps++;
    document.getElementById('comps').textContent=comps;render(k);await sleep(delay);
    if(left[i]<=right[j])arr[k++]=left[i++];else arr[k++]=right[j++];
    swaps++;document.getElementById('swaps').textContent=swaps;}
  while(i<left.length&&running){arr[k++]=left[i++];render(k);await sleep(delay);}
  while(j<right.length&&running){arr[k++]=right[j++];render(k);await sleep(delay);}}
async function startSort(){if(running)return;running=true;comps=0;swaps=0;
  document.getElementById('comps').textContent='0';document.getElementById('swaps').textContent='0';
  document.getElementById('startBtn').disabled=true;delay=parseInt(document.getElementById('speed').value);
  var algo=document.getElementById('algo').value;
  if(algo==='bubble')await bubbleSort();
  else if(algo==='selection')await selectionSort();
  else if(algo==='insertion')await insertionSort();
  else if(algo==='quick')await quickSort(0,arr.length-1);
  else if(algo==='merge')await mergeSort(0,arr.length-1);
  if(running){var sorted=arr.map(function(_,i){return i;});render(null,null,null,sorted);}
  running=false;document.getElementById('startBtn').disabled=false;}
reset();"""
        return self._base_page(title, body, css, js)

    # --- Generic Game (reaction time) ---
    def _generic_game_html(self, title, desc):
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px}
.game-area{width:min(80vw,80vh,400px);height:min(80vw,80vh,400px);border-radius:16px;margin:20px auto;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:min(5vw,18px);font-weight:600;color:#fff;transition:background .3s;user-select:none}
.wait{background:#e74c3c}.go{background:#2ecc71}
.result{font-size:min(8vw,28px);font-weight:700;margin:10px 0;color:#ff7a59}"""
        body = """<div class="card">
    <h2>Reaction Time</h2>
    <p style="color:#888;margin:6px 0">Click the box when it turns green!</p>
    <div class="game-area wait" id="game" onclick="click2()">Click to start</div>
    <div class="result" id="result"></div>
    <p id="best" style="font-size:14px;color:#888"></p>
</div>"""
        js = """var state='idle',to=null,t0=0,best=Infinity;
function startRound(){state='waiting';var g=document.getElementById('game');g.className='game-area wait';g.textContent='Wait...';document.getElementById('result').textContent='';
to=setTimeout(function(){state='ready';g.className='game-area go';g.textContent='CLICK NOW!';t0=Date.now();},1000+Math.random()*3000);}
function click2(){var g=document.getElementById('game');
if(state==='idle'){startRound();}
else if(state==='waiting'){clearTimeout(to);g.className='game-area wait';g.textContent='Too early! Click to retry';document.getElementById('result').textContent='';state='idle';}
else if(state==='ready'){var ms=Date.now()-t0;if(ms<best)best=ms;
document.getElementById('result').textContent=ms+'ms';document.getElementById('best').textContent='Best: '+best+'ms';
g.className='game-area wait';g.textContent='Click to play again';state='idle';}}"""
        return self._base_page(title, body, css, js)

    def _simon_grid_html(self, title, desc):
        """Simon-style grid reaction game with score tracking - RESPONSIVE"""
        css = """*{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%;overflow:auto}
body{display:flex;flex-direction:column}
.card{flex:1;display:flex;flex-direction:column;padding:10px;max-height:100vh}
.game-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-shrink:0}
.score-box{background:#f0f0f0;padding:8px 16px;border-radius:8px;font-weight:600}
.score-box span{color:#ff7a59;font-size:20px}
.grid-container{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
.grid{display:grid;grid-template-columns:repeat(9,1fr);gap:clamp(2px,0.5vmin,6px);
width:min(90vw,90vh,600px);height:min(90vw,90vh,600px);aspect-ratio:1}
.cell{background:#3498db;border-radius:clamp(4px,1vmin,8px);cursor:pointer;transition:all .15s;border:none;width:100%;height:100%}
.cell:hover{transform:scale(1.05);opacity:0.9}
.cell.target{background:#2ecc71!important;box-shadow:0 0 12px #2ecc71}
.cell.distractor{box-shadow:0 0 8px rgba(0,0,0,0.3)}
.cell.wrong{background:#e74c3c!important;animation:shake .3s}
.cell.correct{background:#27ae60!important;animation:pulse .2s}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
@keyframes pulse{50%{transform:scale(1.15)}}
.stats{display:flex;gap:15px;justify-content:center;padding:8px 0;font-size:14px;color:#666;flex-shrink:0}
.game-btn{background:#ff7a59;color:#fff;border:none;padding:12px 28px;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:background .2s}
.game-btn:hover{background:#e5684a}
.game-btn:disabled{background:#ccc;cursor:not-allowed}
.level-indicator{text-align:center;font-size:14px;color:#888;margin-bottom:5px;flex-shrink:0}
.game-over{text-align:center;padding:20px}
.game-over h3{color:#e74c3c;margin-bottom:10px}
.high-score{color:#27ae60;font-weight:600}
.controls{text-align:center;padding:10px 0;flex-shrink:0}"""
        body = """<div class="card">
    <div class="game-header">
        <h2 style="margin:0;font-size:clamp(16px,4vw,24px)">""" + title + """</h2>
        <div class="score-box">Score: <span id="score">0</span></div>
    </div>
    <div class="level-indicator">Level <span id="level">1</span> - Speed: <span id="speed">Normal</span></div>
    <div id="gameArea">
        <div class="grid-container">
            <div class="grid" id="grid"></div>
        </div>
        <div class="stats">
            <span>Hits: <strong id="hits">0</strong></span>
            <span>Misses: <strong id="misses">0</strong></span>
            <span>Best: <strong id="best">0</strong></span>
        </div>
    </div>
    <div id="gameOver" class="game-over" style="display:none">
        <h3>Game Over!</h3>
        <p>Final Score: <span id="finalScore">0</span></p>
        <p id="newRecord" class="high-score" style="display:none">🎉 New High Score!</p>
    </div>
    <div class="controls">
        <button class="game-btn" id="startBtn" onclick="startGame()">Start Game</button>
    </div>
</div>"""
        js = """var grid,score=0,hits=0,misses=0,level=1,best=parseInt(localStorage.getItem('simonBest')||'0'),
playing=false,targetCell=null,distractors=[],gameLoop=null,showTime=1500,maxMisses=3;
var distractorColors=['#e74c3c','#f39c12','#9b59b6','#e91e63','#ff5722'];

function init(){grid=document.getElementById('grid');grid.innerHTML='';
for(var i=0;i<81;i++){var c=document.createElement('button');c.className='cell';c.dataset.idx=i;
c.onclick=function(){cellClick(this)};grid.appendChild(c);}
document.getElementById('best').textContent=best;
window.addEventListener('resize',adjustGrid);adjustGrid();}

function adjustGrid(){var container=document.querySelector('.grid-container');
var size=Math.min(container.clientWidth,container.clientHeight,window.innerWidth*0.95,window.innerHeight*0.6);
grid.style.width=size+'px';grid.style.height=size+'px';}

function startGame(){if(playing)return;
playing=true;score=0;hits=0;misses=0;level=1;showTime=1500;
document.getElementById('startBtn').textContent='Playing...';
document.getElementById('startBtn').disabled=true;
document.getElementById('gameOver').style.display='none';
document.getElementById('gameArea').style.display='block';
updateDisplay();nextTarget();}

function clearTiles(){if(targetCell){targetCell.classList.remove('target');targetCell.style.background='';targetCell=null;}
distractors.forEach(function(d){d.classList.remove('distractor');d.style.background='';});distractors=[];}

function getRandomCells(count,exclude){var cells=grid.querySelectorAll('.cell');var available=[];
for(var i=0;i<cells.length;i++){if(cells[i]!==exclude)available.push(cells[i]);}
var result=[];for(var i=0;i<count&&available.length>0;i++){
var idx=Math.floor(Math.random()*available.length);result.push(available.splice(idx,1)[0]);}
return result;}

function nextTarget(){if(!playing)return;clearTiles();
var cells=grid.querySelectorAll('.cell');
var idx=Math.floor(Math.random()*81);
targetCell=cells[idx];targetCell.classList.add('target');
var numDistractors=Math.min(level-1,5);
if(numDistractors>0){distractors=getRandomCells(numDistractors,targetCell);
distractors.forEach(function(d,i){d.classList.add('distractor');
d.style.background=distractorColors[i%distractorColors.length];});}
gameLoop=setTimeout(function(){if(playing&&targetCell){clearTiles();
var cells=grid.querySelectorAll('.cell');cells[idx].classList.add('wrong');
setTimeout(function(){cells[idx].classList.remove('wrong')},200);
misses++;updateDisplay();if(misses>=maxMisses){endGame();}else{nextTarget();}}},showTime);}

function cellClick(cell){if(!playing)return;
if(cell===targetCell){clearTimeout(gameLoop);clearTiles();
cell.classList.add('correct');setTimeout(function(){cell.classList.remove('correct')},150);
hits++;score+=10*level;
if(hits%5===0){level++;showTime=Math.max(300,showTime-100);
document.getElementById('speed').textContent=['Normal','Fast','Faster','Extreme','Insane','ULTRA'][Math.min(level-1,5)];}
updateDisplay();setTimeout(nextTarget,200);}
else if(distractors.indexOf(cell)>=0||cell.classList.contains('distractor')){
cell.classList.add('wrong');setTimeout(function(){cell.classList.remove('wrong')},200);
misses++;score=Math.max(0,score-10);updateDisplay();if(misses>=maxMisses)endGame();}
else{cell.classList.add('wrong');setTimeout(function(){cell.classList.remove('wrong')},200);
misses++;score=Math.max(0,score-5);updateDisplay();if(misses>=maxMisses)endGame();}}

function updateDisplay(){document.getElementById('score').textContent=score;
document.getElementById('hits').textContent=hits;
document.getElementById('misses').textContent=misses+'/'+maxMisses;
document.getElementById('level').textContent=level;}

function endGame(){playing=false;clearTimeout(gameLoop);clearTiles();
document.getElementById('finalScore').textContent=score;
if(score>best){best=score;localStorage.setItem('simonBest',best);
document.getElementById('best').textContent=best;
document.getElementById('newRecord').style.display='block';}
else{document.getElementById('newRecord').style.display='none';}
document.getElementById('gameOver').style.display='block';
document.getElementById('startBtn').textContent='Play Again';
document.getElementById('startBtn').disabled=false;}

init();"""
        return self._base_page(title, body, css, js)

    def _minesweeper_html(self, title, desc):
        """Classic Minesweeper game with 9x9 grid and 10 mines"""
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:10px}
.game-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding:0 10px;width:100%;max-width:min(90vw,400px)}
.info-box{background:#f0f0f0;padding:8px 16px;border-radius:8px;font-weight:600;font-size:min(4.5vw,18px)}
.info-box.mines{color:#e74c3c}.info-box.timer{color:#3498db}
.grid{display:grid;grid-template-columns:repeat(9,1fr);gap:2px;width:min(90vw,90vh,400px);margin:0 auto 20px;background:#888;padding:3px;border-radius:6px}
.cell{width:100%;aspect-ratio:1;background:#bbb;border:none;font-size:min(4vw,16px);font-weight:700;cursor:pointer;border-radius:3px;transition:all .1s;display:flex;align-items:center;justify-content:center}
.cell:hover:not(.revealed){background:#ccc}
.cell.revealed{background:#ddd;cursor:default}
.cell.mine{background:#e74c3c!important}
.cell.flag{background:#f1c40f}.cell.flag::after{content:'\1F6A9'}
.cell.n1{color:#0000ff}.cell.n2{color:#008000}.cell.n3{color:#ff0000}.cell.n4{color:#000080}
.cell.n5{color:#800000}.cell.n6{color:#008080}.cell.n7{color:#000}.cell.n8{color:#808080}
.game-over{text-align:center;padding:20px;display:none}
.game-over h3{margin-bottom:10px}.game-over.win h3{color:#27ae60}.game-over.lose h3{color:#e74c3c}
.game-btn{background:#ff7a59;color:#fff;border:none;padding:min(3vw,12px) min(7vw,28px);border-radius:8px;font-size:min(4vw,16px);font-weight:600;cursor:pointer}
.game-btn:hover{background:#e5684a}"""
        body = """<div class="card">
    <h2>""" + title + """</h2>
    <div class="game-header">
        <div class="info-box mines"><span id="mineCount">10</span></div>
        <button class="game-btn" onclick="newGame()">New Game</button>
        <div class="info-box timer"><span id="timer">0</span></div>
    </div>
    <div class="grid" id="grid"></div>
    <div class="game-over" id="gameOver">
        <h3 id="endMessage">Game Over</h3>
        <p>Time: <span id="finalTime">0</span>s</p>
    </div>
</div>"""
        js = """var ROWS=9,COLS=9,MINES=10,grid,revealed,flagged,mines,gameOver,firstClick,timerInterval,seconds;
function newGame(){grid=document.getElementById('grid');grid.innerHTML='';
revealed=Array(ROWS).fill().map(()=>Array(COLS).fill(false));
flagged=Array(ROWS).fill().map(()=>Array(COLS).fill(false));
mines=[];gameOver=false;firstClick=true;seconds=0;
clearInterval(timerInterval);document.getElementById('timer').textContent='0';
document.getElementById('mineCount').textContent=MINES;
document.getElementById('gameOver').style.display='none';
document.getElementById('gameOver').className='game-over';
for(var r=0;r<ROWS;r++)for(var c=0;c<COLS;c++){var cell=document.createElement('button');
cell.className='cell';cell.dataset.r=r;cell.dataset.c=c;
cell.onclick=function(){reveal(+this.dataset.r,+this.dataset.c)};
cell.oncontextmenu=function(e){e.preventDefault();toggleFlag(+this.dataset.r,+this.dataset.c);return false};
grid.appendChild(cell);}}
function placeMines(fr,fc){mines=[];while(mines.length<MINES){var r=Math.floor(Math.random()*ROWS),c=Math.floor(Math.random()*COLS);
if((r===fr&&c===fc)||mines.some(m=>m[0]===r&&m[1]===c))continue;mines.push([r,c]);}}
function isMine(r,c){return mines.some(m=>m[0]===r&&m[1]===c);}
function countAdj(r,c){var cnt=0;for(var dr=-1;dr<=1;dr++)for(var dc=-1;dc<=1;dc++){
var nr=r+dr,nc=c+dc;if(nr>=0&&nr<ROWS&&nc>=0&&nc<COLS&&isMine(nr,nc))cnt++;}return cnt;}
function getCell(r,c){return grid.children[r*COLS+c];}
function reveal(r,c){if(gameOver||flagged[r][c]||revealed[r][c])return;
if(firstClick){firstClick=false;placeMines(r,c);timerInterval=setInterval(function(){seconds++;document.getElementById('timer').textContent=seconds;},1000);}
revealed[r][c]=true;var cell=getCell(r,c);cell.classList.add('revealed');
if(isMine(r,c)){cell.classList.add('mine');cell.innerHTML='&#128163;';endGame(false);return;}
var adj=countAdj(r,c);if(adj>0){cell.textContent=adj;cell.classList.add('n'+adj);}
else{for(var dr=-1;dr<=1;dr++)for(var dc=-1;dc<=1;dc++){var nr=r+dr,nc=c+dc;
if(nr>=0&&nr<ROWS&&nc>=0&&nc<COLS&&!revealed[nr][nc])reveal(nr,nc);}}
checkWin();}
function toggleFlag(r,c){if(gameOver||revealed[r][c])return;
flagged[r][c]=!flagged[r][c];var cell=getCell(r,c);
cell.classList.toggle('flag');var cnt=flagged.flat().filter(Boolean).length;
document.getElementById('mineCount').textContent=MINES-cnt;}
function checkWin(){var cnt=0;for(var r=0;r<ROWS;r++)for(var c=0;c<COLS;c++)if(revealed[r][c])cnt++;
if(cnt===ROWS*COLS-MINES)endGame(true);}
function endGame(won){gameOver=true;clearInterval(timerInterval);
document.getElementById('finalTime').textContent=seconds;
document.getElementById('endMessage').textContent=won?'You Win!':'Game Over';
document.getElementById('gameOver').className='game-over '+(won?'win':'lose');
document.getElementById('gameOver').style.display='block';
if(!won)mines.forEach(function(m){var cell=getCell(m[0],m[1]);cell.classList.add('mine');cell.innerHTML='&#128163;';});}
newGame();"""
        return self._base_page(title, body, css, js)

    # --- Snake Game ---
    def _snake_html(self, title, desc):
        """Classic Snake game with arrow key controls"""
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.game-header{display:flex;gap:20px;align-items:center;margin-bottom:15px}
.info-box{background:#f0f0f0;padding:8px 16px;border-radius:8px;font-weight:600;font-size:16px}
.info-box.score{color:#27ae60}.info-box.high{color:#9b59b6}
canvas{border:2px solid #333;border-radius:8px;background:#1a1a2e;touch-action:none}
.controls{display:flex;gap:10px;margin-top:15px;flex-wrap:wrap;justify-content:center}
.game-btn{background:var(--color-primary);color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer}
.game-btn:hover{filter:brightness(0.9)}
.mobile-controls{display:none;margin-top:15px}
.d-pad{display:grid;grid-template-columns:repeat(3,50px);grid-template-rows:repeat(3,50px);gap:4px}
.d-btn{background:#444;color:#fff;border:none;border-radius:8px;font-size:20px;cursor:pointer}
.d-btn:active{background:var(--color-primary)}
@media(max-width:600px){.mobile-controls{display:block}canvas{width:min(90vw,320px);height:min(90vw,320px)}}"""
        body = """<div class="card">
    <h2>""" + title + """</h2>
    <div class="game-header">
        <div class="info-box score">Score: <span id="score">0</span></div>
        <div class="info-box high">Best: <span id="high">0</span></div>
    </div>
    <canvas id="canvas" width="400" height="400"></canvas>
    <div class="controls">
        <button class="game-btn" onclick="startGame()">New Game</button>
        <button class="game-btn" onclick="togglePause()">Pause</button>
    </div>
    <div class="mobile-controls">
        <div class="d-pad">
            <div></div><button class="d-btn" onclick="setDir(0,-1)">&#9650;</button><div></div>
            <button class="d-btn" onclick="setDir(-1,0)">&#9664;</button>
            <div></div>
            <button class="d-btn" onclick="setDir(1,0)">&#9654;</button>
            <div></div><button class="d-btn" onclick="setDir(0,1)">&#9660;</button><div></div>
        </div>
    </div>
    <p style="color:#888;font-size:13px;margin-top:10px">Use arrow keys or WASD to move</p>
</div>"""
        js = """var canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
var GRID=20,SIZE=canvas.width/GRID;
var snake,dir,food,score,highScore,gameLoop,paused,gameOver;
try{highScore=parseInt(localStorage.getItem('snake_high'))||0;}catch(e){highScore=0;}
document.getElementById('high').textContent=highScore;
function startGame(){snake=[{x:10,y:10}];dir={x:1,y:0};score=0;paused=false;gameOver=false;
document.getElementById('score').textContent=0;placeFood();
if(gameLoop)clearInterval(gameLoop);gameLoop=setInterval(update,120);}
function placeFood(){do{food={x:Math.floor(Math.random()*GRID),y:Math.floor(Math.random()*GRID)};}
while(snake.some(s=>s.x===food.x&&s.y===food.y));}
function setDir(dx,dy){if((dx!==0&&dir.x===0)||(dy!==0&&dir.y===0)){dir={x:dx,y:dy};}}
function togglePause(){if(gameOver)return;paused=!paused;}
function update(){if(paused||gameOver)return;
var head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
if(head.x<0||head.x>=GRID||head.y<0||head.y>=GRID||snake.some(s=>s.x===head.x&&s.y===head.y)){
gameOver=true;clearInterval(gameLoop);if(score>highScore){highScore=score;localStorage.setItem('snake_high',highScore);
document.getElementById('high').textContent=highScore;}return;}
snake.unshift(head);
if(head.x===food.x&&head.y===food.y){score++;document.getElementById('score').textContent=score;placeFood();}
else{snake.pop();}draw();}
function draw(){ctx.fillStyle='#1a1a2e';ctx.fillRect(0,0,canvas.width,canvas.height);
ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.arc((food.x+0.5)*SIZE,(food.y+0.5)*SIZE,SIZE/2-2,0,Math.PI*2);ctx.fill();
snake.forEach((s,i)=>{ctx.fillStyle=i===0?'#2ecc71':'#27ae60';
ctx.fillRect(s.x*SIZE+1,s.y*SIZE+1,SIZE-2,SIZE-2);});}
document.addEventListener('keydown',function(e){
if(e.key==='ArrowUp'||e.key==='w')setDir(0,-1);
else if(e.key==='ArrowDown'||e.key==='s')setDir(0,1);
else if(e.key==='ArrowLeft'||e.key==='a')setDir(-1,0);
else if(e.key==='ArrowRight'||e.key==='d')setDir(1,0);
else if(e.key===' ')togglePause();});
startGame();"""
        return self._base_page(title, body, css, js)

    # --- 2048 Game ---
    def _2048_html(self, title, desc):
        """Classic 2048 tile merging game"""
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.game-header{display:flex;gap:20px;align-items:center;margin-bottom:15px}
.info-box{background:#bbada0;color:#fff;padding:8px 16px;border-radius:8px;font-weight:600;font-size:16px;text-align:center}
.info-box span{display:block;font-size:22px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;background:#bbada0;padding:10px;border-radius:8px;width:min(90vw,340px)}
.cell{aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:clamp(16px,6vw,32px);font-weight:700;border-radius:6px;background:#cdc1b4;color:#776e65;transition:all .1s}
.cell[data-val="2"]{background:#eee4da}.cell[data-val="4"]{background:#ede0c8}
.cell[data-val="8"]{background:#f2b179;color:#f9f6f2}.cell[data-val="16"]{background:#f59563;color:#f9f6f2}
.cell[data-val="32"]{background:#f67c5f;color:#f9f6f2}.cell[data-val="64"]{background:#f65e3b;color:#f9f6f2}
.cell[data-val="128"]{background:#edcf72;color:#f9f6f2;font-size:clamp(14px,5vw,28px)}
.cell[data-val="256"]{background:#edcc61;color:#f9f6f2;font-size:clamp(14px,5vw,28px)}
.cell[data-val="512"]{background:#edc850;color:#f9f6f2;font-size:clamp(14px,5vw,28px)}
.cell[data-val="1024"]{background:#edc53f;color:#f9f6f2;font-size:clamp(12px,4vw,24px)}
.cell[data-val="2048"]{background:#edc22e;color:#f9f6f2;font-size:clamp(12px,4vw,24px)}
.controls{display:flex;gap:10px;margin-top:15px}
.game-btn{background:#8f7a66;color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer}
.game-btn:hover{background:#9f8b77}
.mobile-controls{display:none;margin-top:15px}
.d-pad{display:grid;grid-template-columns:repeat(3,50px);grid-template-rows:repeat(3,50px);gap:4px}
.d-btn{background:#8f7a66;color:#fff;border:none;border-radius:8px;font-size:20px;cursor:pointer}
.d-btn:active{background:var(--color-primary)}
@media(max-width:500px){.mobile-controls{display:block}}"""
        body = """<div class="card">
    <h2>""" + title + """</h2>
    <div class="game-header">
        <div class="info-box">SCORE<span id="score">0</span></div>
        <div class="info-box">BEST<span id="best">0</span></div>
    </div>
    <div class="grid" id="grid"></div>
    <div class="controls">
        <button class="game-btn" onclick="newGame()">New Game</button>
    </div>
    <div class="mobile-controls">
        <div class="d-pad">
            <div></div><button class="d-btn" onclick="move('up')">&#9650;</button><div></div>
            <button class="d-btn" onclick="move('left')">&#9664;</button><div></div>
            <button class="d-btn" onclick="move('right')">&#9654;</button>
            <div></div><button class="d-btn" onclick="move('down')">&#9660;</button><div></div>
        </div>
    </div>
    <p style="color:#888;font-size:13px;margin-top:10px">Use arrow keys to slide tiles</p>
</div>"""
        js = """var grid,score,best=0;
try{best=parseInt(localStorage.getItem('2048_best'))||0;}catch(e){}
document.getElementById('best').textContent=best;
function newGame(){grid=[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];score=0;
document.getElementById('score').textContent=0;addTile();addTile();render();}
function addTile(){var empty=[];for(var r=0;r<4;r++)for(var c=0;c<4;c++)if(grid[r][c]===0)empty.push([r,c]);
if(empty.length===0)return;var[r,c]=empty[Math.floor(Math.random()*empty.length)];
grid[r][c]=Math.random()<0.9?2:4;}
function render(){var el=document.getElementById('grid');el.innerHTML='';
for(var r=0;r<4;r++)for(var c=0;c<4;c++){var cell=document.createElement('div');
cell.className='cell';var v=grid[r][c];if(v>0){cell.textContent=v;cell.dataset.val=v;}
el.appendChild(cell);}}
function slide(row){var arr=row.filter(v=>v>0);var merged=[];
for(var i=0;i<arr.length;i++){if(i<arr.length-1&&arr[i]===arr[i+1]){merged.push(arr[i]*2);
score+=arr[i]*2;i++;}else{merged.push(arr[i]);}}
while(merged.length<4)merged.push(0);return merged;}
function move(dir){var moved=false,oldGrid=JSON.stringify(grid);
if(dir==='left'){for(var r=0;r<4;r++)grid[r]=slide(grid[r]);}
else if(dir==='right'){for(var r=0;r<4;r++)grid[r]=slide(grid[r].reverse()).reverse();}
else if(dir==='up'){for(var c=0;c<4;c++){var col=[grid[0][c],grid[1][c],grid[2][c],grid[3][c]];
var s=slide(col);for(var r=0;r<4;r++)grid[r][c]=s[r];}}
else if(dir==='down'){for(var c=0;c<4;c++){var col=[grid[3][c],grid[2][c],grid[1][c],grid[0][c]];
var s=slide(col);grid[3][c]=s[0];grid[2][c]=s[1];grid[1][c]=s[2];grid[0][c]=s[3];}}
if(JSON.stringify(grid)!==oldGrid){addTile();document.getElementById('score').textContent=score;
if(score>best){best=score;localStorage.setItem('2048_best',best);document.getElementById('best').textContent=best;}}
render();checkGameOver();}
function checkGameOver(){for(var r=0;r<4;r++)for(var c=0;c<4;c++){if(grid[r][c]===0)return;
if(c<3&&grid[r][c]===grid[r][c+1])return;if(r<3&&grid[r][c]===grid[r+1][c])return;}
alert('Game Over! Score: '+score);}
document.addEventListener('keydown',function(e){
if(e.key==='ArrowUp'){e.preventDefault();move('up');}
else if(e.key==='ArrowDown'){e.preventDefault();move('down');}
else if(e.key==='ArrowLeft'){e.preventDefault();move('left');}
else if(e.key==='ArrowRight'){e.preventDefault();move('right');}});
var touchStartX,touchStartY;
document.addEventListener('touchstart',function(e){touchStartX=e.touches[0].clientX;touchStartY=e.touches[0].clientY;},{passive:true});
document.addEventListener('touchend',function(e){if(!touchStartX)return;
var dx=e.changedTouches[0].clientX-touchStartX,dy=e.changedTouches[0].clientY-touchStartY;
if(Math.abs(dx)>Math.abs(dy)){if(dx>30)move('right');else if(dx<-30)move('left');}
else{if(dy>30)move('down');else if(dy<-30)move('up');}touchStartX=null;},{passive:true});
newGame();"""
        return self._base_page(title, body, css, js)

    # --- Tetris Game ---
    def _tetris_html(self, title, desc):
        """Classic Tetris with falling blocks"""
        css = """*{box-sizing:border-box}html,body{height:100%;margin:0;overflow:auto}
.card{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px}
.game-wrap{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;justify-content:center}
.game-area{display:flex;flex-direction:column;align-items:center}
canvas{border:2px solid #333;background:#111}
.side-panel{display:flex;flex-direction:column;gap:10px}
.info-box{background:#333;color:#fff;padding:10px 16px;border-radius:8px;text-align:center;min-width:100px}
.info-box .label{font-size:12px;color:#888;text-transform:uppercase}.info-box .val{font-size:20px;font-weight:700}
.next-box{background:#333;padding:10px;border-radius:8px}
.next-box canvas{border:none;background:#222}
.controls{display:flex;gap:8px;margin-top:15px;flex-wrap:wrap;justify-content:center}
.game-btn{background:#ff7a59;color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer}
.game-btn:hover{background:#e5684a}
.mobile-controls{display:none;margin-top:15px}
.m-row{display:flex;gap:8px;justify-content:center;margin:4px 0}
.m-btn{width:50px;height:50px;background:#444;color:#fff;border:none;border-radius:8px;font-size:18px;cursor:pointer}
.m-btn:active{background:#ff7a59}
@media(max-width:500px){.mobile-controls{display:block}.game-wrap{flex-direction:column;align-items:center}}"""
        body = """<div class="card">
    <h2>""" + title + """</h2>
    <div class="game-wrap">
        <div class="game-area"><canvas id="board" width="200" height="400"></canvas></div>
        <div class="side-panel">
            <div class="info-box"><div class="label">Score</div><div class="val" id="score">0</div></div>
            <div class="info-box"><div class="label">Level</div><div class="val" id="level">1</div></div>
            <div class="info-box"><div class="label">Lines</div><div class="val" id="lines">0</div></div>
            <div class="next-box"><div class="label" style="color:#888;font-size:12px;margin-bottom:5px">NEXT</div>
                <canvas id="next" width="80" height="80"></canvas></div>
        </div>
    </div>
    <div class="controls">
        <button class="game-btn" onclick="startGame()">New Game</button>
        <button class="game-btn" onclick="togglePause()">Pause</button>
    </div>
    <div class="mobile-controls">
        <div class="m-row"><button class="m-btn" onclick="rotate()">&#8635;</button></div>
        <div class="m-row">
            <button class="m-btn" onclick="moveP(-1)">&#9664;</button>
            <button class="m-btn" onclick="drop()">&#9660;</button>
            <button class="m-btn" onclick="moveP(1)">&#9654;</button>
        </div>
    </div>
    <p style="color:#888;font-size:12px;margin-top:8px">&#8592;&#8594; Move, &#8593; Rotate, &#8595; Drop, Space Hard Drop</p>
</div>"""
        js = """var canvas=document.getElementById('board'),ctx=canvas.getContext('2d');
var nextCanvas=document.getElementById('next'),nextCtx=nextCanvas.getContext('2d');
var COLS=10,ROWS=20,SZ=20,NEXTSZ=20;
var SHAPES=[[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[1,0,0],[1,1,1]],[[0,0,1],[1,1,1]],[[1,1,0],[0,1,1]],[[0,1,1],[1,1,0]]];
var COLORS=['#00f0f0','#f0f000','#a000f0','#f0a000','#0000f0','#00f000','#f00000'];
var board,piece,nextPiece,px,py,score,level,lines,gameLoop,paused,gameOver;
function newPiece(){var i=Math.floor(Math.random()*SHAPES.length);return{shape:SHAPES[i].map(r=>[...r]),color:COLORS[i]};}
function startGame(){board=Array.from({length:ROWS},()=>Array(COLS).fill(0));
piece=newPiece();nextPiece=newPiece();px=3;py=0;score=0;level=1;lines=0;paused=false;gameOver=false;
updateUI();if(gameLoop)clearInterval(gameLoop);gameLoop=setInterval(tick,1000-level*80);drawNext();}
function updateUI(){document.getElementById('score').textContent=score;
document.getElementById('level').textContent=level;document.getElementById('lines').textContent=lines;}
function drawNext(){nextCtx.fillStyle='#222';nextCtx.fillRect(0,0,80,80);
var s=nextPiece.shape;var ox=(4-s[0].length)*NEXTSZ/2,oy=(4-s.length)*NEXTSZ/2;
nextCtx.fillStyle=nextPiece.color;
for(var r=0;r<s.length;r++)for(var c=0;c<s[0].length;c++)if(s[r][c])nextCtx.fillRect(ox+c*NEXTSZ+1,oy+r*NEXTSZ+1,NEXTSZ-2,NEXTSZ-2);}
function valid(nx,ny,shape){var s=shape||piece.shape;
for(var r=0;r<s.length;r++)for(var c=0;c<s[0].length;c++)
if(s[r][c]){var x=nx+c,y=ny+r;if(x<0||x>=COLS||y>=ROWS)return false;if(y>=0&&board[y][x])return false;}return true;}
function lock(){var s=piece.shape;for(var r=0;r<s.length;r++)for(var c=0;c<s[0].length;c++)
if(s[r][c]){var y=py+r;if(y<0){gameOver=true;clearInterval(gameLoop);alert('Game Over! Score: '+score);return;}
board[y][px+c]=piece.color;}clearLines();piece=nextPiece;nextPiece=newPiece();px=3;py=0;drawNext();}
function clearLines(){var cleared=0;for(var r=ROWS-1;r>=0;r--){if(board[r].every(c=>c)){board.splice(r,1);board.unshift(Array(COLS).fill(0));cleared++;r++;}}
if(cleared){lines+=cleared;score+=cleared*100*level;var newLevel=Math.floor(lines/10)+1;
if(newLevel>level){level=newLevel;clearInterval(gameLoop);gameLoop=setInterval(tick,Math.max(100,1000-level*80));}updateUI();}}
function tick(){if(paused||gameOver)return;if(valid(px,py+1))py++;else lock();draw();}
function moveP(d){if(!paused&&!gameOver&&valid(px+d,py))px+=d;draw();}
function rotate(){if(paused||gameOver)return;var s=piece.shape;var rotated=s[0].map((_,i)=>s.map(r=>r[i]).reverse());
if(valid(px,py,rotated))piece.shape=rotated;draw();}
function drop(){if(paused||gameOver)return;while(valid(px,py+1))py++;lock();draw();}
function togglePause(){if(!gameOver)paused=!paused;}
function draw(){ctx.fillStyle='#111';ctx.fillRect(0,0,canvas.width,canvas.height);
for(var r=0;r<ROWS;r++)for(var c=0;c<COLS;c++)if(board[r][c]){ctx.fillStyle=board[r][c];ctx.fillRect(c*SZ+1,r*SZ+1,SZ-2,SZ-2);}
var s=piece.shape;ctx.fillStyle=piece.color;
for(var r=0;r<s.length;r++)for(var c=0;c<s[0].length;c++)if(s[r][c])ctx.fillRect((px+c)*SZ+1,(py+r)*SZ+1,SZ-2,SZ-2);}
document.addEventListener('keydown',function(e){if(gameOver)return;
if(e.key==='ArrowLeft'){moveP(-1);e.preventDefault();}
else if(e.key==='ArrowRight'){moveP(1);e.preventDefault();}
else if(e.key==='ArrowUp'){rotate();e.preventDefault();}
else if(e.key==='ArrowDown'){if(valid(px,py+1))py++;draw();e.preventDefault();}
else if(e.key===' '){drop();e.preventDefault();}
else if(e.key==='p')togglePause();});
startGame();"""
        return self._base_page(title, body, css, js)

    # ==================================================================
    # Phaser.js Game Templates (advanced 2D game framework)
    # ==================================================================

    def _phaser_platformer_html(self, title, desc):
        """Phaser.js platformer with physics, platforms, and collectibles"""
        return f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif}}
#game-container{{border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.5)}}
.hud{{color:#fff;padding:10px 20px;display:flex;gap:30px;font-size:18px;background:rgba(0,0,0,0.3);border-radius:8px;margin-bottom:10px}}
.hud span{{font-weight:700;color:#ffd700}}
.instructions{{color:#888;font-size:13px;margin-top:10px}}
</style>
</head><body>
<div class="hud">Score: <span id="score">0</span> | Lives: <span id="lives">3</span></div>
<div id="game-container"></div>
<p class="instructions">Arrow keys or WASD to move, Space to jump</p>
<script>
const config={{
    type:Phaser.AUTO,parent:'game-container',width:800,height:500,
    backgroundColor:'#87ceeb',
    physics:{{default:'arcade',arcade:{{gravity:{{y:800}},debug:false}}}},
    scene:{{preload,create,update}}
}};
let player,platforms,coins,enemies,cursors,score=0,lives=3,gameOver=false;
function preload(){{}}
function create(){{
    // Platforms (ground + floating)
    platforms=this.physics.add.staticGroup();
    const ground=this.add.rectangle(400,490,800,20,0x228b22);
    platforms.add(ground);this.physics.add.existing(ground,true);
    [[150,380,200],[400,300,150],[650,400,180],[300,200,120],[550,150,100]].forEach(([x,y,w])=>{{
        const p=this.add.rectangle(x,y,w,20,0x8b4513);platforms.add(p);this.physics.add.existing(p,true);
    }});
    // Player (simple rectangle)
    player=this.add.rectangle(100,400,32,48,0x4169e1);
    this.physics.add.existing(player);player.body.setCollideWorldBounds(true);player.body.setBounce(0.1);
    this.physics.add.collider(player,platforms);
    // Coins
    coins=this.physics.add.group();
    [[200,340],[400,260],[600,360],[350,160],[550,110],[100,340],[700,360]].forEach(([x,y])=>{{
        const c=this.add.circle(x,y,12,0xffd700);coins.add(c);this.physics.add.existing(c,true);
    }});
    this.physics.add.overlap(player,coins,(p,c)=>{{c.destroy();score+=10;document.getElementById('score').textContent=score;}});
    // Enemies (moving hazards)
    enemies=this.physics.add.group();
    [[300,370,100],[500,290,80]].forEach(([x,y,range])=>{{
        const e=this.add.rectangle(x,y,24,24,0xff4444);enemies.add(e);this.physics.add.existing(e);
        e.body.setImmovable(true);e.body.setAllowGravity(false);
        e.startX=x;e.range=range;e.dir=1;
    }});
    this.physics.add.collider(enemies,platforms);
    this.physics.add.overlap(player,enemies,hitEnemy,null,this);
    // Controls
    cursors=this.input.keyboard.createCursorKeys();
    this.input.keyboard.addKeys('W,A,S,D,SPACE');
}}
function hitEnemy(p,e){{
    if(gameOver)return;
    lives--;document.getElementById('lives').textContent=lives;
    if(lives<=0){{gameOver=true;this.physics.pause();this.add.text(400,250,'GAME OVER',{{fontSize:'48px',fill:'#ff0000'}}).setOrigin(0.5);}}
    else{{player.x=100;player.y=400;}}
}}
function update(){{
    if(gameOver)return;
    const keys=this.input.keyboard;
    // Horizontal movement
    if(cursors.left.isDown||keys.checkDown(keys.addKey('A'))){{player.body.setVelocityX(-200);}}
    else if(cursors.right.isDown||keys.checkDown(keys.addKey('D'))){{player.body.setVelocityX(200);}}
    else{{player.body.setVelocityX(0);}}
    // Jump
    if((cursors.up.isDown||cursors.space.isDown||keys.checkDown(keys.addKey('W')))&&player.body.touching.down){{
        player.body.setVelocityY(-450);
    }}
    // Move enemies
    enemies.children.iterate(e=>{{
        if(!e)return;
        e.x+=e.dir*1.5;
        if(e.x>e.startX+e.range||e.x<e.startX-e.range)e.dir*=-1;
    }});
    // Win condition
    if(coins.countActive()===0&&!gameOver){{
        gameOver=true;this.add.text(400,250,'YOU WIN!',{{fontSize:'48px',fill:'#00ff00'}}).setOrigin(0.5);
    }}
}}
new Phaser.Game(config);
</script></body></html>'''

    def _phaser_shooter_html(self, title, desc):
        """Phaser.js space shooter with enemies and bullets"""
        return f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a1a;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif}}
#game-container{{border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(0,100,255,0.3)}}
.hud{{color:#fff;padding:10px 20px;display:flex;gap:30px;font-size:18px;background:rgba(0,50,100,0.5);border-radius:8px;margin-bottom:10px}}
.hud span{{font-weight:700;color:#00ffff}}
.instructions{{color:#666;font-size:13px;margin-top:10px}}
</style>
</head><body>
<div class="hud">Score: <span id="score">0</span> | Wave: <span id="wave">1</span> | Lives: <span id="lives">3</span></div>
<div id="game-container"></div>
<p class="instructions">Arrow keys to move, Space to shoot</p>
<script>
const config={{
    type:Phaser.AUTO,parent:'game-container',width:800,height:600,
    backgroundColor:'#0a0a2e',
    physics:{{default:'arcade',arcade:{{debug:false}}}},
    scene:{{preload,create,update}}
}};
let player,bullets,enemies,cursors,score=0,lives=3,wave=1,lastFire=0,gameOver=false;
function preload(){{}}
function create(){{
    // Stars background
    for(let i=0;i<100;i++){{
        const s=this.add.circle(Phaser.Math.Between(0,800),Phaser.Math.Between(0,600),Phaser.Math.Between(1,2),0xffffff,Phaser.Math.FloatBetween(0.3,1));
        this.tweens.add({{targets:s,alpha:0.2,duration:Phaser.Math.Between(500,2000),yoyo:true,repeat:-1}});
    }}
    // Player ship (triangle)
    player=this.add.polygon(400,550,[0,-20,15,15,-15,15],0x00ff88);
    this.physics.add.existing(player);player.body.setCollideWorldBounds(true);
    // Bullets group
    bullets=this.physics.add.group({{maxSize:50}});
    // Enemies group
    enemies=this.physics.add.group();
    spawnWave.call(this);
    // Collisions
    this.physics.add.overlap(bullets,enemies,(b,e)=>{{
        b.destroy();e.destroy();score+=10;document.getElementById('score').textContent=score;
        if(enemies.countActive()===0){{wave++;document.getElementById('wave').textContent=wave;spawnWave.call(this);}}
    }});
    this.physics.add.overlap(player,enemies,(p,e)=>{{
        e.destroy();lives--;document.getElementById('lives').textContent=lives;
        if(lives<=0){{gameOver=true;this.physics.pause();this.add.text(400,300,'GAME OVER',{{fontSize:'48px',fill:'#ff0000'}}).setOrigin(0.5);}}
    }});
    cursors=this.input.keyboard.createCursorKeys();
    this.input.keyboard.addKey('SPACE');
}}
function spawnWave(){{
    const cols=5+wave,rows=2+Math.floor(wave/2);
    for(let r=0;r<rows;r++){{
        for(let c=0;c<cols;c++){{
            const x=100+c*((600)/(cols-1||1)),y=50+r*40;
            const e=this.add.polygon(x,y,[0,-12,10,10,-10,10],0xff4444);
            enemies.add(e);this.physics.add.existing(e);
            e.body.setVelocity(Phaser.Math.Between(-30,30)*wave,20+wave*5);
            e.body.setBounce(1,0);e.body.setCollideWorldBounds(true);
        }}
    }}
}}
function update(time){{
    if(gameOver)return;
    // Movement
    if(cursors.left.isDown)player.body.setVelocityX(-300);
    else if(cursors.right.isDown)player.body.setVelocityX(300);
    else player.body.setVelocityX(0);
    if(cursors.up.isDown)player.body.setVelocityY(-200);
    else if(cursors.down.isDown)player.body.setVelocityY(200);
    else player.body.setVelocityY(0);
    // Shooting
    if(cursors.space.isDown&&time>lastFire+150){{
        lastFire=time;
        const b=this.add.rectangle(player.x,player.y-25,4,16,0x00ffff);
        bullets.add(b);this.physics.add.existing(b);b.body.setVelocityY(-500);
    }}
    // Cleanup off-screen bullets
    bullets.children.iterate(b=>{{if(b&&b.y<-20)b.destroy();}});
    // Check enemies reaching bottom
    enemies.children.iterate(e=>{{if(e&&e.y>580){{e.destroy();lives--;document.getElementById('lives').textContent=lives;if(lives<=0){{gameOver=true;this.physics.pause();this.add.text(400,300,'GAME OVER',{{fontSize:'48px',fill:'#ff0000'}}).setOrigin(0.5);}}}}}});
}}
new Phaser.Game(config);
</script></body></html>'''

    def _phaser_breakout_html(self, title, desc):
        """Phaser.js breakout / brick breaker game"""
        return f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif}}
#game-container{{border-radius:8px;overflow:hidden;box-shadow:0 4px 20px rgba(255,100,0,0.3)}}
.hud{{color:#fff;padding:10px 20px;display:flex;gap:30px;font-size:18px;background:rgba(100,50,0,0.5);border-radius:8px;margin-bottom:10px}}
.hud span{{font-weight:700;color:#ffa500}}
.instructions{{color:#666;font-size:13px;margin-top:10px}}
</style>
</head><body>
<div class="hud">Score: <span id="score">0</span> | Lives: <span id="lives">3</span></div>
<div id="game-container"></div>
<p class="instructions">Move mouse or use arrow keys to control paddle. Click to launch ball.</p>
<script>
const config={{
    type:Phaser.AUTO,parent:'game-container',width:800,height:600,
    backgroundColor:'#1a1a2e',
    physics:{{default:'arcade',arcade:{{debug:false}}}},
    scene:{{preload,create,update}}
}};
let paddle,ball,bricks,cursors,score=0,lives=3,ballLaunched=false,gameOver=false;
function preload(){{}}
function create(){{
    // Paddle
    paddle=this.add.rectangle(400,560,120,16,0x4488ff);
    this.physics.add.existing(paddle);paddle.body.setImmovable(true);paddle.body.setCollideWorldBounds(true);
    // Ball
    ball=this.add.circle(400,540,10,0xffffff);
    this.physics.add.existing(ball);ball.body.setCollideWorldBounds(true);ball.body.setBounce(1);
    ball.body.setMaxSpeed(600);
    // Bricks
    bricks=this.physics.add.staticGroup();
    const colors=[0xff4444,0xff8844,0xffff44,0x44ff44,0x4444ff,0xff44ff];
    for(let row=0;row<6;row++){{
        for(let col=0;col<10;col++){{
            const x=80+col*65,y=60+row*28;
            const b=this.add.rectangle(x,y,60,22,colors[row]);
            bricks.add(b);this.physics.add.existing(b,true);
        }}
    }}
    // Collisions
    this.physics.add.collider(ball,paddle,(b,p)=>{{
        const diff=b.x-p.x;
        b.body.setVelocityX(diff*5);
    }});
    this.physics.add.collider(ball,bricks,(b,brick)=>{{
        brick.destroy();score+=10;document.getElementById('score').textContent=score;
        if(bricks.countActive()===0){{
            gameOver=true;this.physics.pause();
            this.add.text(400,300,'YOU WIN!',{{fontSize:'48px',fill:'#00ff00'}}).setOrigin(0.5);
        }}
    }});
    // Controls
    cursors=this.input.keyboard.createCursorKeys();
    this.input.on('pointermove',(p)=>{{if(!gameOver)paddle.x=Phaser.Math.Clamp(p.x,60,740);}});
    this.input.on('pointerdown',()=>{{if(!ballLaunched&&!gameOver){{ballLaunched=true;ball.body.setVelocity(Phaser.Math.Between(-200,200),-400);}}}});
}}
function update(){{
    if(gameOver)return;
    // Keyboard paddle control
    if(cursors.left.isDown)paddle.body.setVelocityX(-400);
    else if(cursors.right.isDown)paddle.body.setVelocityX(400);
    else paddle.body.setVelocityX(0);
    // Ball follows paddle before launch
    if(!ballLaunched){{ball.x=paddle.x;ball.y=paddle.y-20;}}
    // Ball fell off bottom
    if(ball.y>590){{
        lives--;document.getElementById('lives').textContent=lives;
        if(lives<=0){{
            gameOver=true;this.physics.pause();
            this.add.text(400,300,'GAME OVER',{{fontSize:'48px',fill:'#ff0000'}}).setOrigin(0.5);
        }}else{{
            ballLaunched=false;ball.body.setVelocity(0,0);ball.x=paddle.x;ball.y=paddle.y-20;
        }}
    }}
}}
new Phaser.Game(config);
</script></body></html>'''

    # --- Pong Game ---
    def _pong_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#111;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif}}
canvas{{border:2px solid #fff}}
.score{{color:#fff;font-size:24px;text-align:center;margin-bottom:10px}}
.controls{{color:#888;font-size:12px;text-align:center;margin-top:10px}}
</style></head><body>
<div>
<div class="score">Player: <span id="p1">0</span> | Computer: <span id="p2">0</span></div>
<canvas id="c" width="600" height="400"></canvas>
<div class="controls">Use W/S or Arrow Keys to move your paddle</div>
</div>
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const W=600,H=400,paddleH=80,paddleW=10,ballSize=10;
let p1Y=H/2-paddleH/2,p2Y=H/2-paddleH/2,ballX=W/2,ballY=H/2,ballVX=4,ballVY=3;
let p1Score=0,p2Score=0,keys={{}};
document.addEventListener('keydown',e=>keys[e.key]=true);
document.addEventListener('keyup',e=>keys[e.key]=false);
function update(){{
    if(keys['w']||keys['W']||keys['ArrowUp'])p1Y=Math.max(0,p1Y-6);
    if(keys['s']||keys['S']||keys['ArrowDown'])p1Y=Math.min(H-paddleH,p1Y+6);
    // Simple AI
    if(p2Y+paddleH/2<ballY)p2Y=Math.min(H-paddleH,p2Y+4);
    if(p2Y+paddleH/2>ballY)p2Y=Math.max(0,p2Y-4);
    ballX+=ballVX;ballY+=ballVY;
    if(ballY<=0||ballY>=H-ballSize)ballVY=-ballVY;
    // Left paddle
    if(ballX<=paddleW+10&&ballY+ballSize>=p1Y&&ballY<=p1Y+paddleH){{ballVX=-ballVX;ballX=paddleW+11;}}
    // Right paddle
    if(ballX>=W-paddleW-10-ballSize&&ballY+ballSize>=p2Y&&ballY<=p2Y+paddleH){{ballVX=-ballVX;ballX=W-paddleW-11-ballSize;}}
    // Scoring
    if(ballX<0){{p2Score++;document.getElementById('p2').textContent=p2Score;reset();}}
    if(ballX>W){{p1Score++;document.getElementById('p1').textContent=p1Score;reset();}}
}}
function reset(){{ballX=W/2;ballY=H/2;ballVX=4*(Math.random()>0.5?1:-1);ballVY=3*(Math.random()>0.5?1:-1);}}
function draw(){{
    ctx.fillStyle='#111';ctx.fillRect(0,0,W,H);
    ctx.setLineDash([5,5]);ctx.strokeStyle='#444';ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle='#fff';
    ctx.fillRect(10,p1Y,paddleW,paddleH);
    ctx.fillRect(W-paddleW-10,p2Y,paddleW,paddleH);
    ctx.fillRect(ballX,ballY,ballSize,ballSize);
}}
function loop(){{update();draw();requestAnimationFrame(loop);}}
loop();
</script></body></html>'''

    # --- Cookie Clicker / Idle Game ---
    def _cookie_clicker_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:linear-gradient(135deg,#1a1a2e,#16213e);min-height:100vh;font-family:'Segoe UI',sans-serif;color:#fff;display:flex;justify-content:center;padding:20px}}
.container{{max-width:800px;width:100%}}
h1{{text-align:center;margin-bottom:20px;font-size:28px}}
.main{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.cookie-area{{text-align:center}}
.cookie{{width:200px;height:200px;border-radius:50%;background:linear-gradient(135deg,#c4a35a,#8b6914);border:none;cursor:pointer;font-size:60px;transition:transform 0.1s;box-shadow:0 10px 30px rgba(0,0,0,0.4)}}
.cookie:hover{{transform:scale(1.05)}}
.cookie:active{{transform:scale(0.95)}}
.count{{font-size:32px;margin:20px 0}}
.per-sec{{color:#888;font-size:14px}}
.shop{{background:rgba(255,255,255,0.1);border-radius:12px;padding:20px}}
.shop h2{{margin-bottom:15px;font-size:18px}}
.upgrade{{background:rgba(255,255,255,0.1);padding:12px;border-radius:8px;margin-bottom:10px;cursor:pointer;transition:background 0.2s}}
.upgrade:hover{{background:rgba(255,255,255,0.2)}}
.upgrade.locked{{opacity:0.5;cursor:not-allowed}}
.upgrade-name{{font-weight:bold}}
.upgrade-info{{font-size:12px;color:#aaa;margin-top:4px}}
</style></head><body>
<div class="container">
<h1>🍪 {title}</h1>
<div class="main">
<div class="cookie-area">
<div class="count"><span id="count">0</span> cookies</div>
<button class="cookie" onclick="click1()">🍪</button>
<div class="per-sec"><span id="cps">0</span> per second</div>
</div>
<div class="shop">
<h2>Upgrades</h2>
<div class="upgrade" onclick="buy(0)"><span class="upgrade-name">Cursor</span> - $<span id="p0">15</span><div class="upgrade-info">+0.1/sec (owned: <span id="o0">0</span>)</div></div>
<div class="upgrade" onclick="buy(1)"><span class="upgrade-name">Grandma</span> - $<span id="p1">100</span><div class="upgrade-info">+1/sec (owned: <span id="o1">0</span>)</div></div>
<div class="upgrade" onclick="buy(2)"><span class="upgrade-name">Farm</span> - $<span id="p2">500</span><div class="upgrade-info">+8/sec (owned: <span id="o2">0</span>)</div></div>
<div class="upgrade" onclick="buy(3)"><span class="upgrade-name">Factory</span> - $<span id="p3">3000</span><div class="upgrade-info">+47/sec (owned: <span id="o3">0</span>)</div></div>
</div>
</div>
</div>
<script>
let cookies=0,cps=0;
const upgrades=[
    {{name:'Cursor',base:15,cps:0.1,owned:0}},
    {{name:'Grandma',base:100,cps:1,owned:0}},
    {{name:'Farm',base:500,cps:8,owned:0}},
    {{name:'Factory',base:3000,cps:47,owned:0}}
];
function getPrice(i){{return Math.floor(upgrades[i].base*Math.pow(1.15,upgrades[i].owned));}}
function click1(){{cookies++;update();}}
function buy(i){{
    const price=getPrice(i);
    if(cookies>=price){{
        cookies-=price;upgrades[i].owned++;
        cps=upgrades.reduce((s,u)=>s+u.cps*u.owned,0);
        update();
    }}
}}
function update(){{
    document.getElementById('count').textContent=Math.floor(cookies);
    document.getElementById('cps').textContent=cps.toFixed(1);
    upgrades.forEach((u,i)=>{{
        document.getElementById('p'+i).textContent=getPrice(i);
        document.getElementById('o'+i).textContent=u.owned;
    }});
}}
setInterval(()=>{{cookies+=cps/10;update();}},100);
update();
</script></body></html>'''

    # --- Sudoku ---
    def _sudoku_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#f0f0f0;min-height:100vh;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;padding:20px}}
.container{{background:#fff;padding:30px;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,0.1)}}
h1{{text-align:center;margin-bottom:20px;color:#333}}
.grid{{display:grid;grid-template-columns:repeat(9,40px);gap:1px;background:#333;padding:2px;border-radius:4px}}
.cell{{width:40px;height:40px;border:none;text-align:center;font-size:18px;font-weight:bold;background:#fff}}
.cell:focus{{background:#e3f2fd;outline:none}}
.cell.fixed{{background:#f5f5f5;color:#333}}
.cell.error{{background:#ffebee;color:#c62828}}
.cell:nth-child(3n){{border-right:2px solid #333}}
.cell:nth-child(n+19):nth-child(-n+27),.cell:nth-child(n+46):nth-child(-n+54){{border-bottom:2px solid #333}}
.row-break{{display:none}}
.btns{{margin-top:20px;text-align:center}}
.btns button{{padding:10px 20px;margin:5px;border:none;border-radius:8px;cursor:pointer;font-size:14px}}
.btns button:first-child{{background:#4caf50;color:#fff}}
.btns button:last-child{{background:#f44336;color:#fff}}
#msg{{text-align:center;margin-top:10px;font-weight:bold}}
</style></head><body>
<div class="container">
<h1>{title}</h1>
<div class="grid" id="grid"></div>
<div class="btns">
<button onclick="check()">Check Solution</button>
<button onclick="newGame()">New Game</button>
</div>
<div id="msg"></div>
</div>
<script>
const puzzles=[
'530070000600195000098000060800060003400803001700020006060000280000419005000080079',
'003020600900305001001806400008102900700000008006708200002609500800203009005010300',
'200080300060070084030500209000105408000000000402706000301007040720040060004010003'
];
let puzzle='',solution='';
function shuffle(a){{for(let i=a.length-1;i>0;i--){{const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}}return a;}}
function newGame(){{
    const idx=Math.floor(Math.random()*puzzles.length);
    puzzle=puzzles[idx];
    const grid=document.getElementById('grid');
    grid.innerHTML='';
    for(let i=0;i<81;i++){{
        const cell=document.createElement('input');
        cell.className='cell'+(puzzle[i]!=='0'?' fixed':'');
        cell.maxLength=1;
        cell.value=puzzle[i]==='0'?'':puzzle[i];
        if(puzzle[i]!=='0')cell.readOnly=true;
        cell.oninput=()=>{{cell.value=cell.value.replace(/[^1-9]/g,'');}};
        grid.appendChild(cell);
    }}
    document.getElementById('msg').textContent='';
}}
function check(){{
    const cells=[...document.querySelectorAll('.cell')];
    let valid=true;
    cells.forEach(c=>c.classList.remove('error'));
    // Check rows
    for(let r=0;r<9;r++){{
        const row=cells.slice(r*9,r*9+9).map(c=>c.value);
        if(new Set(row.filter(v=>v)).size!==row.filter(v=>v).length){{
            cells.slice(r*9,r*9+9).forEach(c=>c.classList.add('error'));valid=false;
        }}
    }}
    // Check columns
    for(let c=0;c<9;c++){{
        const col=[];for(let r=0;r<9;r++)col.push(cells[r*9+c].value);
        if(new Set(col.filter(v=>v)).size!==col.filter(v=>v).length){{
            for(let r=0;r<9;r++)cells[r*9+c].classList.add('error');valid=false;
        }}
    }}
    // Check complete
    const complete=cells.every(c=>c.value);
    document.getElementById('msg').textContent=valid&&complete?'🎉 Solved!':(valid?'Keep going...':'Errors found');
    document.getElementById('msg').style.color=valid&&complete?'#4caf50':(valid?'#ff9800':'#f44336');
}}
newGame();
</script></body></html>'''

    # --- Connect Four ---
    def _connect_four_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:linear-gradient(135deg,#1a237e,#0d47a1);min-height:100vh;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center}}
.container{{text-align:center}}
h1{{color:#fff;margin-bottom:20px}}
.board{{background:#1565c0;padding:10px;border-radius:12px;display:inline-block;box-shadow:0 10px 40px rgba(0,0,0,0.3)}}
.row{{display:flex}}
.cell{{width:50px;height:50px;background:#0d47a1;border-radius:50%;margin:3px;cursor:pointer;transition:all 0.3s}}
.cell:hover{{background:#1976d2}}
.cell.red{{background:#f44336}}
.cell.yellow{{background:#ffeb3b}}
#status{{color:#fff;margin-top:20px;font-size:18px}}
button{{margin-top:15px;padding:10px 30px;border:none;border-radius:8px;background:#fff;color:#1565c0;font-size:16px;cursor:pointer}}
</style></head><body>
<div class="container">
<h1>{title}</h1>
<div class="board" id="board"></div>
<div id="status">🔴 Red's turn</div>
<button onclick="reset()">New Game</button>
</div>
<script>
const ROWS=6,COLS=7;
let board,turn,gameOver;
function init(){{
    board=Array(ROWS).fill(null).map(()=>Array(COLS).fill(0));
    turn=1;gameOver=false;
    render();
    document.getElementById('status').textContent="🔴 Red's turn";
}}
function render(){{
    const el=document.getElementById('board');
    el.innerHTML='';
    for(let r=0;r<ROWS;r++){{
        const row=document.createElement('div');
        row.className='row';
        for(let c=0;c<COLS;c++){{
            const cell=document.createElement('div');
            cell.className='cell'+(board[r][c]===1?' red':'')+(board[r][c]===2?' yellow':'');
            cell.onclick=()=>drop(c);
            row.appendChild(cell);
        }}
        el.appendChild(row);
    }}
}}
function drop(col){{
    if(gameOver)return;
    for(let r=ROWS-1;r>=0;r--){{
        if(board[r][col]===0){{
            board[r][col]=turn;
            if(checkWin(r,col)){{
                gameOver=true;
                document.getElementById('status').textContent=(turn===1?'🔴 Red':'🟡 Yellow')+' wins!';
            }}else{{
                turn=turn===1?2:1;
                document.getElementById('status').textContent=(turn===1?'🔴 Red':'🟡 Yellow')+"'s turn";
            }}
            render();return;
        }}
    }}
}}
function checkWin(r,c){{
    const dirs=[[0,1],[1,0],[1,1],[1,-1]];
    for(let[dr,dc]of dirs){{
        let count=1;
        for(let i=1;i<4;i++)if(board[r+dr*i]?.[c+dc*i]===turn)count++;else break;
        for(let i=1;i<4;i++)if(board[r-dr*i]?.[c-dc*i]===turn)count++;else break;
        if(count>=4)return true;
    }}
    return false;
}}
function reset(){{init();}}
init();
</script></body></html>'''

    # --- Blackjack ---
    def _blackjack_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:linear-gradient(135deg,#1b5e20,#2e7d32);min-height:100vh;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center}}
.table{{background:#2e7d32;padding:40px;border-radius:20px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.4);min-width:400px;border:8px solid #1b5e20}}
h1{{color:#fff;margin-bottom:20px}}
.hand{{display:flex;justify-content:center;gap:10px;min-height:120px;margin:15px 0}}
.card{{width:70px;height:100px;background:#fff;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;box-shadow:0 4px 8px rgba(0,0,0,0.2)}}
.card.red{{color:#c62828}}
.card.hidden{{background:linear-gradient(135deg,#1565c0,#0d47a1);color:transparent}}
.label{{color:#a5d6a7;font-size:14px;margin-bottom:5px}}
.score{{color:#fff;font-size:18px;margin:10px 0}}
.btns{{margin-top:20px}}
.btns button{{padding:12px 24px;margin:5px;border:none;border-radius:8px;font-size:16px;cursor:pointer}}
#hit{{background:#ffeb3b;color:#333}}
#stand{{background:#f44336;color:#fff}}
#deal{{background:#2196f3;color:#fff}}
#msg{{color:#fff;font-size:20px;margin-top:15px;font-weight:bold}}
</style></head><body>
<div class="table">
<h1>{title}</h1>
<div class="label">Dealer</div>
<div class="hand" id="dealer"></div>
<div class="score">Dealer: <span id="ds">0</span></div>
<div class="label">Your Hand</div>
<div class="hand" id="player"></div>
<div class="score">You: <span id="ps">0</span></div>
<div class="btns">
<button id="hit" onclick="hit()">Hit</button>
<button id="stand" onclick="stand()">Stand</button>
<button id="deal" onclick="deal()">Deal</button>
</div>
<div id="msg"></div>
</div>
<script>
const suits=['♠','♥','♦','♣'],ranks=['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
let deck,pHand,dHand,gameOver;
function createDeck(){{deck=[];for(let s of suits)for(let r of ranks)deck.push({{rank:r,suit:s}});shuffle();}}
function shuffle(){{for(let i=deck.length-1;i>0;i--){{const j=Math.floor(Math.random()*(i+1));[deck[i],deck[j]]=[deck[j],deck[i]];}};}}
function cardVal(card){{if(['J','Q','K'].includes(card.rank))return 10;if(card.rank==='A')return 11;return parseInt(card.rank);}}
function handVal(hand){{let v=hand.reduce((s,c)=>s+cardVal(c),0),aces=hand.filter(c=>c.rank==='A').length;while(v>21&&aces>0){{v-=10;aces--;}}return v;}}
function renderCard(c,hidden=false){{
    const isRed=['♥','♦'].includes(c.suit);
    return `<div class="card${{isRed?' red':''}}${{hidden?' hidden':''}}">${{hidden?'':c.rank+c.suit}}</div>`;
}}
function render(showDealer=false){{
    document.getElementById('player').innerHTML=pHand.map(c=>renderCard(c)).join('');
    document.getElementById('dealer').innerHTML=dHand.map((c,i)=>renderCard(c,!showDealer&&i===1)).join('');
    document.getElementById('ps').textContent=handVal(pHand);
    document.getElementById('ds').textContent=showDealer?handVal(dHand):'?';
}}
function deal(){{
    createDeck();pHand=[deck.pop(),deck.pop()];dHand=[deck.pop(),deck.pop()];gameOver=false;
    document.getElementById('msg').textContent='';
    document.getElementById('hit').disabled=false;document.getElementById('stand').disabled=false;
    render();
    if(handVal(pHand)===21)endGame('Blackjack! You win!');
}}
function hit(){{
    if(gameOver)return;
    pHand.push(deck.pop());render();
    if(handVal(pHand)>21)endGame('Bust! Dealer wins.');
}}
function stand(){{
    if(gameOver)return;
    while(handVal(dHand)<17)dHand.push(deck.pop());
    render(true);
    const pv=handVal(pHand),dv=handVal(dHand);
    if(dv>21)endGame('Dealer busts! You win!');
    else if(pv>dv)endGame('You win!');
    else if(dv>pv)endGame('Dealer wins.');
    else endGame('Push - tie game.');
}}
function endGame(msg){{
    gameOver=true;render(true);
    document.getElementById('msg').textContent=msg;
    document.getElementById('hit').disabled=true;document.getElementById('stand').disabled=true;
}}
deal();
</script></body></html>'''

    # --- Flappy Bird ---
    def _flappy_html(self, title, desc):
        return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#70c5ce;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif}}
canvas{{border:2px solid #333}}
#ui{{position:absolute;top:20px;color:#fff;font-size:28px;text-shadow:2px 2px 2px #333}}
</style></head><body>
<div id="ui">Score: <span id="score">0</span></div>
<canvas id="c" width="400" height="600"></canvas>
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const W=400,H=600,GRAVITY=0.5,JUMP=-8,PIPE_WIDTH=60,GAP=150;
let bird={{x:80,y:H/2,vy:0,size:25}},pipes=[],score=0,gameOver=false,started=false;
function addPipe(){{
    const minY=100,maxY=H-GAP-100;
    const gapY=minY+Math.random()*(maxY-minY);
    pipes.push({{x:W,gapY:gapY,passed:false}});
}}
function reset(){{
    bird.y=H/2;bird.vy=0;pipes=[];score=0;gameOver=false;started=false;
    document.getElementById('score').textContent=0;
}}
function jump(){{
    if(gameOver){{reset();return;}}
    if(!started){{started=true;addPipe();}}
    bird.vy=JUMP;
}}
document.addEventListener('keydown',e=>{{if(e.code==='Space')jump();}});
canvas.addEventListener('click',jump);
canvas.addEventListener('touchstart',e=>{{e.preventDefault();jump();}});
function update(){{
    if(!started||gameOver)return;
    bird.vy+=GRAVITY;bird.y+=bird.vy;
    // Pipes
    for(let p of pipes){{
        p.x-=3;
        if(!p.passed&&p.x+PIPE_WIDTH<bird.x){{p.passed=true;score++;document.getElementById('score').textContent=score;}}
    }}
    pipes=pipes.filter(p=>p.x>-PIPE_WIDTH);
    if(pipes.length===0||pipes[pipes.length-1].x<W-200)addPipe();
    // Collision
    if(bird.y<0||bird.y+bird.size>H)gameOver=true;
    for(let p of pipes){{
        if(bird.x+bird.size>p.x&&bird.x<p.x+PIPE_WIDTH){{
            if(bird.y<p.gapY||bird.y+bird.size>p.gapY+GAP)gameOver=true;
        }}
    }}
}}
function draw(){{
    ctx.fillStyle='#70c5ce';ctx.fillRect(0,0,W,H);
    // Ground
    ctx.fillStyle='#ded895';ctx.fillRect(0,H-40,W,40);
    ctx.fillStyle='#7cba5f';ctx.fillRect(0,H-50,W,10);
    // Pipes
    ctx.fillStyle='#73bf2e';
    for(let p of pipes){{
        ctx.fillRect(p.x,0,PIPE_WIDTH,p.gapY);
        ctx.fillRect(p.x,p.gapY+GAP,PIPE_WIDTH,H-p.gapY-GAP);
        ctx.fillStyle='#5a9c24';
        ctx.fillRect(p.x-5,p.gapY-20,PIPE_WIDTH+10,20);
        ctx.fillRect(p.x-5,p.gapY+GAP,PIPE_WIDTH+10,20);
        ctx.fillStyle='#73bf2e';
    }}
    // Bird
    ctx.fillStyle='#f7dc6f';ctx.beginPath();ctx.arc(bird.x+bird.size/2,bird.y+bird.size/2,bird.size/2,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(bird.x+bird.size/2+5,bird.y+bird.size/2-3,6,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#333';ctx.beginPath();ctx.arc(bird.x+bird.size/2+7,bird.y+bird.size/2-3,3,0,Math.PI*2);ctx.fill();
    ctx.fillStyle='#e74c3c';ctx.beginPath();ctx.moveTo(bird.x+bird.size,bird.y+bird.size/2);ctx.lineTo(bird.x+bird.size+10,bird.y+bird.size/2-3);ctx.lineTo(bird.x+bird.size+10,bird.y+bird.size/2+5);ctx.fill();
    // Messages
    if(!started){{ctx.fillStyle='#fff';ctx.font='24px sans-serif';ctx.textAlign='center';ctx.fillText('Tap or Space to Start',W/2,H/2);}}
    if(gameOver){{ctx.fillStyle='rgba(0,0,0,0.5)';ctx.fillRect(0,0,W,H);ctx.fillStyle='#fff';ctx.font='36px sans-serif';ctx.textAlign='center';ctx.fillText('Game Over!',W/2,H/2-20);ctx.font='18px sans-serif';ctx.fillText('Tap to restart',W/2,H/2+20);}}
}}
function loop(){{update();draw();requestAnimationFrame(loop);}}
loop();
</script></body></html>'''

    # --- Generic App (fallback) ---
    def _generic_app_html(self, title, desc):
        body = f"""<div class="card">
    <h2>{title}</h2>
    <p style="color:#666;margin:12px 0;font-size:16px">{desc or 'Your app is ready!'}</p>
    <div style="background:#f8f8f8;border-radius:8px;padding:20px;margin:20px 0;text-align:left">
        <p style="font-size:14px;color:#555;line-height:1.6">This app is set up and running with Flask.
        Edit <code style="background:#eee;padding:2px 6px;border-radius:3px">templates/index.html</code> to build your interface.</p>
    </div>
    <p style="font-size:13px;color:#aaa">Powered by Flask</p>
</div>"""
        return self._base_page(title, body)

    # ==================================================================
    # CRUD HTML  (data apps — improved forms, feedback, empty state)
    # ==================================================================

    def _crud_html(self, title, answers, description):
        needs_auth = answers.get("needs_auth", False)
        needs_search = answers.get("search", False)
        needs_export = answers.get("export", False)
        models = parse_description(description) if description else []

        nav_links = ""
        model_sections = ""
        auth_html = ""

        if needs_auth:
            auth_html = self._html_auth_js()

        for m in models:
            nav_links += f'        <a href="#" onclick="showSection(\'{m.table_name}\')">{m.name}s</a>\n'
            model_sections += self._html_model_section(m, needs_search, needs_export)

        scripts = self._html_scripts(models, needs_auth)

        # Use design system for theming if available
        if HAS_DESIGN_SYSTEM:
            from design_system import get_theme_for_description
            theme = get_theme_for_description(description)
            p = theme.palette
            css_vars = f"""
        :root {{
            --color-primary: {p.primary};
            --color-secondary: {p.secondary};
            --color-bg: {p.background};
            --color-surface: {p.surface};
            --color-text: {p.text};
            --color-text-muted: {p.text_muted};
            --color-border: {p.border};
            --color-success: {p.success};
            --color-warning: {p.warning};
            --color-error: {p.error};
        }}"""
        else:
            css_vars = """
        :root {
            --color-primary: #ff7a59;
            --color-secondary: #ff6b3f;
            --color-bg: #f5f5f5;
            --color-surface: #ffffff;
            --color-text: #333333;
            --color-text-muted: #888888;
            --color-border: #dddddd;
            --color-success: #2ecc71;
            --color-warning: #f39c12;
            --color-error: #dc3545;
        }"""

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        {css_vars}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--color-bg); color: var(--color-text); }}
        .navbar {{ background: var(--color-primary); color: white; padding: 14px 20px; display: flex; align-items: center; gap: 20px; }}
        .navbar h1 {{ font-size: 20px; }}
        .navbar a {{ color: white; text-decoration: none; font-size: 14px; opacity: .85; }}
        .navbar a:hover {{ opacity: 1; }}
        .container {{ max-width: 900px; margin: 24px auto; padding: 0 16px; }}
        .card {{ background: var(--color-surface); border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
        input, textarea, select {{ padding: 9px 11px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 14px; width: 100%; font-family: inherit; }}
        input:focus, textarea:focus {{ outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(0,0,0,.08); }}
        button {{ padding: 9px 18px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all .2s; }}
        .btn-primary {{ background: var(--color-primary); color: white; }}
        .btn-primary:hover {{ filter: brightness(1.1); transform: translateY(-1px); }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .btn-danger {{ background: transparent; color: var(--color-error); font-size: 18px; padding: 4px 10px; border-radius: 4px; }}
        .btn-danger:hover {{ background: #ffeaea; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--color-border); }}
        th {{ background: var(--color-bg); font-weight: 600; font-size: 12px; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: .5px; }}
        tr:hover td {{ background: var(--color-bg); }}
        .hidden {{ display: none; }}
        .section {{ display: none; }}
        .section.active {{ display: block; }}
        .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .form-field {{ display: flex; flex-direction: column; }}
        .form-field.full-width {{ grid-column: 1 / -1; }}
        .form-field label {{ font-size: 13px; font-weight: 600; color: var(--color-text-muted); margin-bottom: 4px; }}
        .form-field label input[type="checkbox"] {{ width: auto; margin-right: 6px; }}
        .empty-state {{ text-align: center; padding: 40px 20px; color: var(--color-text-muted); font-size: 15px; }}
        .toast {{ position: fixed; bottom: 24px; right: 24px; background: var(--color-success); color: white; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px; transform: translateY(80px); opacity: 0; transition: all .3s; z-index: 999; pointer-events: none; }}
        .toast.show {{ transform: translateY(0); opacity: 1; }}
        #auth-section {{ margin-bottom: 16px; }}
        .form-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }}
        .form-row > * {{ flex: 1; min-width: 150px; }}
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>{title}</h1>
{nav_links}
    </nav>
    <div class="container">
{auth_html}
{model_sections}
    </div>
    <div id="toast" class="toast"></div>
{scripts}
</body>
</html>
"""

    def _html_auth_js(self):
        return """
        <div id="auth-section" class="card">
            <div id="auth-forms">
                <h3>Login or Register</h3>
                <div class="form-row">
                    <input id="auth-username" placeholder="Username">
                    <input id="auth-email" placeholder="Email">
                    <input id="auth-password" type="password" placeholder="Password">
                </div>
                <button class="btn-primary" onclick="doRegister()">Register</button>
                <button class="btn-secondary" onclick="doLogin()">Login</button>
            </div>
            <div id="auth-info" class="hidden">
                <p>Logged in as <strong id="auth-name"></strong>
                <button class="btn-secondary" onclick="doLogout()">Logout</button></p>
            </div>
        </div>"""

    def _html_model_section(self, m: DomainModel, has_search, has_export):
        lower = m.table_name
        cls = m.name
        form_fields = []
        for fname, ftype, nullable in m.fields:
            label = fname.replace("_", " ").title()
            req = " required" if not nullable else ""
            star = " *" if not nullable else ""
            if "Text" in ftype:
                form_fields.append(f"""
                    <div class="form-field full-width">
                        <label for="add-{lower}-{fname}">{label}{star}</label>
                        <textarea id="add-{lower}-{fname}" rows="3"{req}></textarea>
                    </div>""")
            elif "Boolean" in ftype:
                form_fields.append(f"""
                    <div class="form-field">
                        <label><input type="checkbox" id="add-{lower}-{fname}"> {label}</label>
                    </div>""")
            elif "Integer" in ftype or "Float" in ftype:
                step = '0.1' if 'Float' in ftype else '1'
                form_fields.append(f"""
                    <div class="form-field">
                        <label for="add-{lower}-{fname}">{label}{star}</label>
                        <input type="number" step="{step}" id="add-{lower}-{fname}"{req}>
                    </div>""")
            elif "DateTime" in ftype:
                form_fields.append(f"""
                    <div class="form-field">
                        <label for="add-{lower}-{fname}">{label}{star}</label>
                        <input type="datetime-local" id="add-{lower}-{fname}"{req}>
                    </div>""")
            else:
                form_fields.append(f"""
                    <div class="form-field">
                        <label for="add-{lower}-{fname}">{label}{star}</label>
                        <input id="add-{lower}-{fname}"{req}>
                    </div>""")

        search_bar = ""
        if has_search:
            search_bar = f'\n            <input id="search-{lower}" placeholder="Search {cls}s..." oninput="load{cls}s()" style="margin-bottom:16px">'

        export_btn = ""
        if has_export:
            export_btn = f' <button type="button" class="btn-secondary" onclick="window.location=\'/api/{lower}s/export\'">Export CSV</button>'

        visible = [(f, f.replace("_", " ").title()) for f, t, _ in m.fields if "Text" not in t][:5]
        th_cells = "".join(f"<th>{lbl}</th>" for _, lbl in visible)

        return f"""
        <div id="section-{lower}" class="section card">
            <h2 style="margin-bottom:16px">{cls}s</h2>{search_bar}
            <form id="form-{lower}" onsubmit="return add{cls}()">
                <div class="form-grid">{"".join(form_fields)}
                </div>
                <div style="margin-top:14px">
                    <button type="submit" class="btn-primary">Add {cls}</button>{export_btn}
                </div>
            </form>
            <div id="empty-{lower}" class="empty-state">No {lower}s yet &mdash; add your first one above!</div>
            <table id="table-wrap-{lower}" style="display:none">
                <thead><tr>{th_cells}<th style="width:50px"></th></tr></thead>
                <tbody id="table-{lower}"></tbody>
            </table>
        </div>"""

    def _html_scripts(self, models: List[DomainModel], has_auth):
        parts = ["<script>"]

        parts.append("""
    function showToast(msg) {
        var t = document.getElementById('toast');
        t.textContent = msg; t.classList.add('show');
        setTimeout(function(){ t.classList.remove('show'); }, 2000);
    }
    function showSection(name) {
        document.querySelectorAll('.section').forEach(function(s){ s.classList.remove('active'); });
        var el = document.getElementById('section-' + name);
        if (el) el.classList.add('active');
    }
""")

        if has_auth:
            parts.append("""
    async function checkAuth() {
        var res = await fetch('/api/me');
        var data = await res.json();
        if (data.user) {
            document.getElementById('auth-forms').classList.add('hidden');
            document.getElementById('auth-info').classList.remove('hidden');
            document.getElementById('auth-name').textContent = data.user.username;
        } else {
            document.getElementById('auth-forms').classList.remove('hidden');
            document.getElementById('auth-info').classList.add('hidden');
        }
    }
    async function doRegister() {
        var res = await fetch('/api/register', { method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                username: document.getElementById('auth-username').value,
                email: document.getElementById('auth-email').value,
                password: document.getElementById('auth-password').value,
            })});
        var data = await res.json();
        if (data.error) { alert(data.error); return; }
        checkAuth();
    }
    async function doLogin() {
        var res = await fetch('/api/login', { method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                email: document.getElementById('auth-email').value,
                password: document.getElementById('auth-password').value,
            })});
        var data = await res.json();
        if (data.error) { alert(data.error); return; }
        checkAuth();
    }
    async function doLogout() {
        await fetch('/api/logout', {method:'POST'});
        checkAuth();
    }
    checkAuth();
""")

        for m in models:
            lower = m.table_name
            cls = m.name
            visible = [(f, t) for f, t, _ in m.fields if "Text" not in t][:5]

            td_cells = ""
            for fname, ftype in visible:
                if "Boolean" in ftype:
                    td_cells += "<td>${item." + fname + " ? '&#10003;' : ''}</td>"
                else:
                    td_cells += "<td>${item." + fname + " || ''}</td>"
            td_cells += "<td><button class='btn-danger' onclick='delete" + cls + "(${item.id})'>&#215;</button></td>"

            field_assigns = []
            for fname, ftype, _ in m.fields:
                el_id = f"add-{lower}-{fname}"
                if "Boolean" in ftype:
                    field_assigns.append(f"{fname}: document.getElementById('{el_id}').checked")
                elif "Integer" in ftype:
                    field_assigns.append(f"{fname}: parseInt(document.getElementById('{el_id}').value) || 0")
                elif "Float" in ftype:
                    field_assigns.append(f"{fname}: parseFloat(document.getElementById('{el_id}').value) || 0")
                else:
                    field_assigns.append(f"{fname}: document.getElementById('{el_id}').value")
            body_str = ", ".join(field_assigns)

            parts.append(f"""
    async function load{cls}s() {{
        var q = document.getElementById('search-{lower}') ? document.getElementById('search-{lower}').value : '';
        var url = '/api/{lower}s' + (q ? '?q=' + encodeURIComponent(q) : '');
        var res = await fetch(url);
        var items = await res.json();
        if (items.length === 0) {{
            document.getElementById('empty-{lower}').style.display = 'block';
            document.getElementById('table-wrap-{lower}').style.display = 'none';
        }} else {{
            document.getElementById('empty-{lower}').style.display = 'none';
            document.getElementById('table-wrap-{lower}').style.display = 'table';
            document.getElementById('table-{lower}').innerHTML = items.map(function(item) {{
                return `<tr>{td_cells}</tr>`;
            }}).join('');
        }}
    }}
    async function add{cls}() {{
        await fetch('/api/{lower}s', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
            body: JSON.stringify({{ {body_str} }}) }});
        document.getElementById('form-{lower}').reset();
        showToast('{cls} added!');
        load{cls}s();
        return false;
    }}
    async function delete{cls}(id) {{
        await fetch('/api/{lower}s/' + id, {{ method:'DELETE' }});
        showToast('{cls} removed');
        load{cls}s();
    }}
    load{cls}s();
""")

        if models:
            parts.append(f"    showSection('{models[0].table_name}');")

        parts.append("</script>")
        return "\n".join(parts)


# Singleton
generator = CodeGenerator()
