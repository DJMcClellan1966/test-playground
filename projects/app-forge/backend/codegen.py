"""Code generator - Builds working Flask apps from requirements.

Improvements over v1:
 - #1  Description-aware domain models (via domain_parser)
 - #2  Fully working auth (register, login, logout, session gate)
 - #3  Generates Flask + flask-socketio (matches solver)
 - #5  Search endpoint and CSV export when flags are set
 - #9  requirements.txt lists flask-socketio (not python-socketio)
"""

from typing import Dict, List
from domain_parser import DomainModel, parse_description


class CodeGenerator:
    """Generates Flask app boilerplate from requirements + description."""

    # ------------------------------------------------------------------
    # app.py
    # ------------------------------------------------------------------
    def generate_app_py(self, app_name: str, answers: Dict[str, bool],
                        description: str = "") -> str:
        needs_db = answers.get("has_data", False)
        needs_auth = answers.get("needs_auth", False)
        needs_realtime = answers.get("realtime", False)
        needs_search = answers.get("search", False)
        needs_export = answers.get("export", False)

        # Domain models from description
        models = parse_description(description) if (needs_db and description) else []

        parts: List[str] = []

        # --- imports ---
        parts.append(self._imports(needs_db, needs_auth, needs_realtime,
                                   needs_search, needs_export))
        # --- app init ---
        parts.append(self._app_init(app_name, needs_db, needs_realtime))
        # --- user model (auth) ---
        if needs_auth and needs_db:
            parts.append(self._user_model())
        # --- domain models ---
        if needs_db:
            for m in models:
                parts.append(self._domain_model(m, needs_auth))
        # --- routes ---
        parts.append(self._base_routes(app_name))
        if needs_auth and needs_db:
            parts.append(self._auth_routes())
        if needs_db:
            for m in models:
                parts.append(self._crud_routes(m, needs_auth, needs_search,
                                               needs_export))
        # --- main ---
        parts.append(self._main_block(needs_db, needs_realtime))

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # requirements.txt  (#9 fix: flask-socketio not python-socketio)
    # ------------------------------------------------------------------
    def generate_requirements_txt(self, answers: Dict[str, bool]) -> str:
        reqs = ["flask==3.0.2", "flask-cors==4.0.0"]
        if answers.get("has_data"):
            reqs.append("flask-sqlalchemy==3.1.1")
        if answers.get("realtime"):
            reqs.append("flask-socketio==5.3.6")
        return "\n".join(reqs) + "\n"

    # ------------------------------------------------------------------
    # index.html  (richer generated page)
    # ------------------------------------------------------------------
    def generate_index_html(self, app_name: str, answers: Dict[str, bool],
                            description: str = "") -> str:
        title = app_name.title()
        needs_auth = answers.get("needs_auth", False)
        needs_db = answers.get("has_data", False)
        needs_search = answers.get("search", False)
        needs_export = answers.get("export", False)
        models = parse_description(description) if (needs_db and description) else []

        nav_links = ""
        model_sections = ""
        auth_js = ""
        scripts = ""

        if needs_auth:
            nav_links += self._html_auth_nav()
            auth_js = self._html_auth_js()

        for m in models:
            nav_links += f'        <a href="#" onclick="showSection(\'{m.table_name}\')">{m.name}s</a>\n'
            model_sections += self._html_model_section(m, needs_search, needs_export)

        scripts = self._html_scripts(models, needs_auth)

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .navbar {{ background: #ff7a59; color: white; padding: 14px 20px; display: flex; align-items: center; gap: 20px; }}
        .navbar h1 {{ font-size: 20px; }}
        .navbar a {{ color: white; text-decoration: none; font-size: 14px; opacity: .85; }}
        .navbar a:hover {{ opacity: 1; }}
        .container {{ max-width: 900px; margin: 24px auto; padding: 0 16px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
        .status {{ padding: 10px; background: #d4edda; color: #155724; border-radius: 4px; margin-bottom: 16px; font-size: 14px; }}
        input, textarea, select {{ padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 100%; margin-bottom: 8px; }}
        button {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
        .btn-primary {{ background: #ff7a59; color: white; }}
        .btn-primary:hover {{ background: #ff6b3f; }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
        th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f8f8; font-weight: 600; }}
        .hidden {{ display: none; }}
        .section {{ display: none; }}
        .section.active {{ display: block; }}
        .form-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }}
        .form-row > * {{ flex: 1; min-width: 150px; }}
        #auth-section {{ margin-bottom: 16px; }}
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>{title}</h1>
{nav_links}
        <span style="flex:1"></span>
        <span id="auth-nav"></span>
    </nav>
    <div class="container">
        <div class="status" id="status-bar">&#10003; App is running</div>
{auth_js}
{model_sections}
    </div>
{scripts}
</body>
</html>
"""

    # ==================================================================
    # Private helpers
    # ==================================================================

    def _imports(self, db, auth, rt, search, export):
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
        # LIST + search
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

        # CREATE
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

        # UPDATE
        lines.append(f"\n@app.route('/api/{lower}s/<int:id>', methods=['PUT']){auth_dec}")
        lines.append(f"def update_{lower}(id):")
        lines.append(f"    item = {cls}.query.get_or_404(id)")
        lines.append(f"    data = request.get_json()")
        for fname, ftype, _ in m.fields:
            lines.append(f"    if '{fname}' in data: item.{fname} = data['{fname}']")
        lines.append(f"    db.session.commit()")
        lines.append(f"    return jsonify(item.to_dict())")

        # DELETE
        lines.append(f"\n@app.route('/api/{lower}s/<int:id>', methods=['DELETE']){auth_dec}")
        lines.append(f"def delete_{lower}(id):")
        lines.append(f"    item = {cls}.query.get_or_404(id)")
        lines.append(f"    db.session.delete(item)")
        lines.append(f"    db.session.commit()")
        lines.append(f"    return jsonify({{'ok': True}})")

        # CSV export
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
    # HTML helpers
    # ==================================================================
    def _html_auth_nav(self):
        return ""

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
        form_inputs = []
        for fname, ftype, _ in m.fields:
            label = fname.replace("_", " ").title()
            if "Text" in ftype:
                form_inputs.append(f'<textarea id="add-{lower}-{fname}" placeholder="{label}"></textarea>')
            elif "Boolean" in ftype:
                form_inputs.append(
                    f'<label><input type="checkbox" id="add-{lower}-{fname}"> {label}</label>')
            elif "Integer" in ftype or "Float" in ftype:
                form_inputs.append(
                    f'<input type="number" id="add-{lower}-{fname}" placeholder="{label}">')
            elif "DateTime" in ftype:
                form_inputs.append(
                    f'<input type="datetime-local" id="add-{lower}-{fname}" placeholder="{label}">')
            else:
                form_inputs.append(
                    f'<input id="add-{lower}-{fname}" placeholder="{label}">')

        search_bar = ""
        if has_search:
            search_bar = f'<input id="search-{lower}" placeholder="Search {cls}s..." oninput="load{cls}s()">'

        export_btn = ""
        if has_export:
            export_btn = f'<button class="btn-secondary" onclick="window.location=\'/api/{lower}s/export\'">Export CSV</button>'

        visible_fields = [(f, f.replace("_", " ").title()) for f, t, _ in m.fields if "Text" not in t][:5]
        th_cells = "".join(f"<th>{label}</th>" for _, label in visible_fields)

        return f"""
        <div id="section-{lower}" class="section card">
            <h2>{cls}s</h2>
            {search_bar}
            <div class="form-row">
                {"".join(form_inputs)}
            </div>
            <button class="btn-primary" onclick="add{cls}()">Add {cls}</button>
            {export_btn}
            <table>
                <thead><tr>{th_cells}<th>Actions</th></tr></thead>
                <tbody id="table-{lower}"></tbody>
            </table>
        </div>"""

    def _html_scripts(self, models: List[DomainModel], has_auth):
        parts = ["<script>"]

        parts.append("""
    function showSection(name) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
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
                    td_cells += "${item." + fname + " ? '&#10003;' : ''}"
                    td_cells = td_cells.replace("${", "<td>${")
                    # Simpler approach
            # Rebuild td_cells cleanly
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
        var tbody = document.getElementById('table-{lower}');
        tbody.innerHTML = items.map(function(item) {{ return `<tr>{td_cells}</tr>`; }}).join('');
    }}
    async function add{cls}() {{
        await fetch('/api/{lower}s', {{ method:'POST', headers:{{'Content-Type':'application/json'}},
            body: JSON.stringify({{ {body_str} }}) }});
        load{cls}s();
    }}
    async function delete{cls}(id) {{
        await fetch('/api/{lower}s/' + id, {{ method:'DELETE' }});
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
