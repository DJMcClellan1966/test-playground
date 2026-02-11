"""Code generator - Builds working Flask apps from requirements.

Features:
 - Description-aware domain models (via domain_parser)
 - Working auth (register, login, logout, session gate)
 - Search / CSV export endpoints
 - Standalone HTML for non-data apps (games, calculators, tools)
 - Improved CRUD UI (labelled forms, clear-on-submit, toast, empty state)
"""

import re
from typing import Dict, List
from domain_parser import DomainModel, parse_description
from template_registry import match_template, extract_features
from component_assembler import can_assemble, assemble_html


def detect_app_type(description: str) -> str:
    """Use scored template registry instead of flat regex."""
    best_id, features, scores = match_template(description)
    # If 'data_app' feature found and no game features dominate → CRUD
    if "data_app" in features and scores[0][1] < 5:
        return "generic"  # Will trigger CRUD path in generate_index_html
    return best_id


class CodeGenerator:
    """Generates Flask app boilerplate from requirements + description."""

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
    # index.html  — routes to standalone or CRUD
    # ==================================================================
    def generate_index_html(self, app_name: str, answers: Dict[str, bool],
                            description: str = "") -> str:
        title = app_name.replace("-", " ").title()
        needs_db = answers.get("has_data", False)

        if not needs_db:
            app_type = detect_app_type(description)
            return self._standalone_html(title, app_type, description)

        return self._crud_html(title, answers, description)

    # ==================================================================
    # Backend helper methods (unchanged)
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

    def _base_page(self, title, body_html, css="", js=""):
        return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f5f5;color:#333}}
.navbar{{background:#ff7a59;color:#fff;padding:16px 20px;text-align:center}}
.navbar h1{{font-size:22px;font-weight:700}}
.container{{max-width:640px;margin:30px auto;padding:0 16px}}
.card{{background:#fff;border-radius:12px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);margin-bottom:16px;text-align:center}}
button{{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:15px;font-weight:600;transition:all .2s}}
.btn-primary{{background:#ff7a59;color:#fff}}.btn-primary:hover{{background:#ff6b3f;transform:translateY(-1px)}}
.btn-secondary{{background:#6c757d;color:#fff}}.btn-secondary:hover{{background:#5a6268}}
input,select{{padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:15px;width:100%;margin-bottom:10px}}
input:focus{{outline:none;border-color:#ff7a59;box-shadow:0 0 0 3px rgba(255,122,89,.15)}}
{css}
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
        # Templates that matched via required features — always trustworthy
        REQUIRED_FEATURE_TEMPLATES = {
            "tictactoe", "hangman", "wordle", "calculator", "converter", "timer",
            "reaction_game", "simon_game", "reflex_game", "minesweeper"
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
            "sliding_puzzle": self._sliding_puzzle_html,
            "hangman": self._hangman_html,
            "wordle": self._wordle_html,
            "reaction_game": self._simon_grid_html,
            "simon_game": self._simon_grid_html,
            "reflex_game": self._simon_grid_html,
            "minesweeper": self._minesweeper_html,
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
.progress-bar{height:100%;background:#ff7a59;border-radius:3px;transition:width .3s}
.options{display:flex;flex-direction:column;gap:10px;margin:20px 0;text-align:left}
.option{padding:14px 18px;background:#f8f8f8;border:2px solid #e0e0e0;border-radius:8px;cursor:pointer;font-size:15px;transition:all .2s}
.option:hover{border-color:#ff7a59;background:#fff5f2}
.option.correct{border-color:#2ecc71;background:#d4edda}
.option.wrong{border-color:#e74c3c;background:#ffeaea}
.score-big{font-size:56px;font-weight:700;color:#ff7a59;margin:16px 0}"""
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
        css = """.board{display:grid;grid-template-columns:repeat(3,100px);gap:4px;margin:16px auto;width:fit-content}
.cell{width:100px;height:100px;background:#fff;border:2px solid #ddd;border-radius:8px;font-size:36px;font-weight:700;cursor:pointer;transition:all .15s}
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
        css = """.board{display:grid;grid-template-columns:repeat(4,80px);gap:8px;margin:16px auto;width:fit-content}
.mem{width:80px;height:80px;border-radius:8px;font-size:32px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s;border:2px solid #ddd}
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

    # --- Sliding Tile Puzzle ---
    def _sliding_puzzle_html(self, title, desc):
        # Extract grid size from features
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

        cell_px = max(60, 280 // size)
        board_px = cell_px * size + (size - 1) * 4

        css = f""".board{{display:grid;grid-template-columns:repeat({size},{cell_px}px);gap:4px;margin:16px auto;width:{board_px}px}}
.tile{{width:{cell_px}px;height:{cell_px}px;display:flex;align-items:center;justify-content:center;font-size:{max(16, 36 - size * 4)}px;font-weight:700;border-radius:8px;cursor:pointer;transition:all .15s;user-select:none}}
.tile.num{{background:#ff7a59;color:#fff;border:2px solid #e8694a}}.tile.num:hover{{background:#ff6b3f;transform:scale(1.03)}}
.tile.empty{{background:transparent;cursor:default}}
.moves{{font-size:15px;color:#888;margin:10px 0}}
.win{{animation:celebrate .6s ease-in-out}}
@keyframes celebrate{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.05)}}}}"""

        body = f"""<div class="card">
    <h2>Sliding Puzzle ({size}×{size})</h2>
    <p class="moves">Moves: <strong id="moves">0</strong></p>
    <div class="board" id="board"></div>
    <button class="btn-primary" onclick="newGame()" style="margin-top:12px">Shuffle</button>
</div>"""

        js = f"""var SIZE={size},board,moves,won;
function newGame(){{
  board=[];for(var i=1;i<SIZE*SIZE;i++)board.push(i);board.push(0);
  // Fisher-Yates shuffle that produces solvable state
  do{{for(var i=board.length-1;i>0;i--){{var j=Math.floor(Math.random()*(i+1));var t=board[i];board[i]=board[j];board[j]=t;}}}}while(!isSolvable());
  moves=0;won=false;document.getElementById('moves').textContent='0';render();
}}
function isSolvable(){{
  var inv=0;var flat=board.filter(function(x){{return x!==0;}});
  for(var i=0;i<flat.length;i++)for(var j=i+1;j<flat.length;j++)if(flat[i]>flat[j])inv++;
  if(SIZE%2===1)return inv%2===0;
  var emptyRow=Math.floor(board.indexOf(0)/SIZE);
  return(inv+emptyRow)%2===1;
}}
function render(){{
  var b=document.getElementById('board');b.innerHTML='';
  board.forEach(function(v,i){{
    var d=document.createElement('div');
    if(v===0){{d.className='tile empty';}}
    else{{d.className='tile num';d.textContent=v;d.onclick=function(){{clickTile(i);}};}}
    b.appendChild(d);
  }});
  if(won)b.classList.add('win');else b.classList.remove('win');
}}
function clickTile(i){{
  if(won)return;var ei=board.indexOf(0);
  var row=Math.floor(i/SIZE),col=i%SIZE,er=Math.floor(ei/SIZE),ec=ei%SIZE;
  if((Math.abs(row-er)+Math.abs(col-ec))!==1)return;
  board[ei]=board[i];board[i]=0;moves++;document.getElementById('moves').textContent=moves;
  if(checkWin()){{won=true;}}render();
  if(won)setTimeout(function(){{alert('Solved in '+moves+' moves!');}},300);
}}
function checkWin(){{
  for(var i=0;i<SIZE*SIZE-1;i++)if(board[i]!==i+1)return false;return true;
}}
newGame();"""
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
        css = """.grid{display:grid;grid-template-columns:repeat(5,56px);gap:6px;margin:16px auto;width:fit-content}
.cell{width:56px;height:56px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:700;
border:2px solid #ddd;border-radius:6px;text-transform:uppercase;transition:all .3s}
.cell.correct{background:#2ecc71;color:#fff;border-color:#2ecc71}
.cell.present{background:#f1c40f;color:#fff;border-color:#f1c40f}
.cell.absent{background:#888;color:#fff;border-color:#888}
.cell.filled{border-color:#999}
.kb{display:flex;flex-wrap:wrap;justify-content:center;gap:4px;max-width:480px;margin:12px auto}
.kb button{min-width:32px;height:42px;border-radius:6px;font-size:13px;font-weight:700;background:#ddd;border:none;cursor:pointer}
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

    # --- Generic Game (reaction time) ---
    def _generic_game_html(self, title, desc):
        css = """.game-area{width:280px;height:280px;border-radius:16px;margin:20px auto;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:18px;font-weight:600;color:#fff;transition:background .3s;user-select:none}
.wait{background:#e74c3c}.go{background:#2ecc71}
.result{font-size:28px;font-weight:700;margin:10px 0;color:#ff7a59}"""
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
        """Simon-style grid reaction game with score tracking"""
        css = """.game-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.score-box{background:#f0f0f0;padding:8px 16px;border-radius:8px;font-weight:600}
.score-box span{color:#ff7a59;font-size:20px}
.grid{display:grid;grid-template-columns:repeat(9,1fr);gap:4px;max-width:360px;margin:0 auto 20px}
.cell{aspect-ratio:1;background:#3498db;border-radius:6px;cursor:pointer;transition:all .15s;border:none}
.cell:hover{transform:scale(1.05);opacity:0.9}
.cell.target{background:#2ecc71!important;box-shadow:0 0 12px #2ecc71}
.cell.distractor{box-shadow:0 0 8px rgba(0,0,0,0.3)}
.cell.wrong{background:#e74c3c!important;animation:shake .3s}
.cell.correct{background:#27ae60!important;animation:pulse .2s}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
@keyframes pulse{50%{transform:scale(1.15)}}
.stats{display:flex;gap:20px;justify-content:center;margin:15px 0;font-size:14px;color:#666}
.game-btn{background:#ff7a59;color:#fff;border:none;padding:12px 28px;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;transition:background .2s}
.game-btn:hover{background:#e5684a}
.game-btn:disabled{background:#ccc;cursor:not-allowed}
.level-indicator{text-align:center;font-size:14px;color:#888;margin-bottom:10px}
.game-over{text-align:center;padding:20px}
.game-over h3{color:#e74c3c;margin-bottom:10px}
.high-score{color:#27ae60;font-weight:600}"""
        body = """<div class="card">
    <div class="game-header">
        <h2>""" + title + """</h2>
        <div class="score-box">Score: <span id="score">0</span></div>
    </div>
    <div class="level-indicator">Level <span id="level">1</span> - Speed: <span id="speed">Normal</span></div>
    <div id="gameArea">
        <div class="grid" id="grid"></div>
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
    <div style="text-align:center;margin-top:15px">
        <button class="game-btn" id="startBtn" onclick="startGame()">Start Game</button>
    </div>
</div>"""
        js = """var grid,score=0,hits=0,misses=0,level=1,best=parseInt(localStorage.getItem('simonBest')||'0'),
playing=false,targetCell=null,distractors=[],gameLoop=null,showTime=1500,maxMisses=3;
var distractorColors=['#e74c3c','#f39c12','#9b59b6','#e91e63','#ff5722'];

function init(){grid=document.getElementById('grid');grid.innerHTML='';
for(var i=0;i<81;i++){var c=document.createElement('button');c.className='cell';c.dataset.idx=i;
c.onclick=function(){cellClick(this)};grid.appendChild(c);}
document.getElementById('best').textContent=best;}

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
        css = """.game-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;padding:0 10px}
.info-box{background:#f0f0f0;padding:8px 16px;border-radius:8px;font-weight:600;font-size:18px}
.info-box.mines{color:#e74c3c}.info-box.timer{color:#3498db}
.grid{display:grid;grid-template-columns:repeat(9,1fr);gap:2px;max-width:324px;margin:0 auto 20px;background:#888;padding:3px;border-radius:6px}
.cell{width:34px;height:34px;background:#bbb;border:none;font-size:16px;font-weight:700;cursor:pointer;border-radius:3px;transition:all .1s}
.cell:hover:not(.revealed){background:#ccc}
.cell.revealed{background:#ddd;cursor:default}
.cell.mine{background:#e74c3c!important}
.cell.flag{background:#f1c40f}.cell.flag::after{content:'\1F6A9'}
.cell.n1{color:#0000ff}.cell.n2{color:#008000}.cell.n3{color:#ff0000}.cell.n4{color:#000080}
.cell.n5{color:#800000}.cell.n6{color:#008080}.cell.n7{color:#000}.cell.n8{color:#808080}
.game-over{text-align:center;padding:20px;display:none}
.game-over h3{margin-bottom:10px}.game-over.win h3{color:#27ae60}.game-over.lose h3{color:#e74c3c}
.game-btn{background:#ff7a59;color:#fff;border:none;padding:12px 28px;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer}
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
        .card {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
        input, textarea, select {{ padding: 9px 11px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; width: 100%; font-family: inherit; }}
        input:focus, textarea:focus {{ outline: none; border-color: #ff7a59; box-shadow: 0 0 0 3px rgba(255,122,89,.12); }}
        button {{ padding: 9px 18px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; transition: all .2s; }}
        .btn-primary {{ background: #ff7a59; color: white; }}
        .btn-primary:hover {{ background: #ff6b3f; transform: translateY(-1px); }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .btn-danger {{ background: transparent; color: #dc3545; font-size: 18px; padding: 4px 10px; border-radius: 4px; }}
        .btn-danger:hover {{ background: #ffeaea; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #fafafa; font-weight: 600; font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: .5px; }}
        tr:hover td {{ background: #fafafa; }}
        .hidden {{ display: none; }}
        .section {{ display: none; }}
        .section.active {{ display: block; }}
        .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .form-field {{ display: flex; flex-direction: column; }}
        .form-field.full-width {{ grid-column: 1 / -1; }}
        .form-field label {{ font-size: 13px; font-weight: 600; color: #555; margin-bottom: 4px; }}
        .form-field label input[type="checkbox"] {{ width: auto; margin-right: 6px; }}
        .empty-state {{ text-align: center; padding: 40px 20px; color: #bbb; font-size: 15px; }}
        .toast {{ position: fixed; bottom: 24px; right: 24px; background: #2ecc71; color: white; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px; transform: translateY(80px); opacity: 0; transition: all .3s; z-index: 999; pointer-events: none; }}
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
