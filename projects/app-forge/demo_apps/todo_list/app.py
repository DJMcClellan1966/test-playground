from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from db import db, init_db
from models import User
from werkzeug.security import check_password_hash
from functools import wraps
from models import Todo, Task
import csv
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize database
init_db(app)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated


# ==== Routes ====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "app": "Todo List"})


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


# ==== Todo CRUD ====
@app.route('/api/todos')
@login_required
def list_todos():
    query = Todo.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Todo.title.ilike(f'%{q}%') | Todo.description.ilike(f'%{q}%') | Todo.priority.ilike(f'%{q}%'))
    items = query.order_by(Todo.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/todos', methods=['POST'])
@login_required
def create_todo():
    data = request.get_json()
    item = Todo()
    item.title = data.get('title', '')
    item.description = data.get('description', '')
    item.done = data.get('done', False)
    item.priority = data.get('priority', '')
    item.due_date = data.get('due_date', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/todos/<int:id>', methods=['PUT'])
@login_required
def update_todo(id):
    item = Todo.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data: item.title = data['title']
    if 'description' in data: item.description = data['description']
    if 'done' in data: item.done = data['done']
    if 'priority' in data: item.priority = data['priority']
    if 'due_date' in data: item.due_date = data['due_date']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/todos/<int:id>', methods=['DELETE'])
@login_required
def delete_todo(id):
    item = Todo.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/todos/export')
@login_required
def export_todos():
    items = Todo.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['title', 'description', 'done', 'priority', 'due_date'])
    for i in items:
        writer.writerow([i.title, i.description, i.done, i.priority, i.due_date])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=todos.csv'})


# ==== Task CRUD ====
@app.route('/api/tasks')
@login_required
def list_tasks():
    query = Task.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Task.title.ilike(f'%{q}%') | Task.description.ilike(f'%{q}%') | Task.priority.ilike(f'%{q}%'))
    items = query.order_by(Task.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    item = Task()
    item.title = data.get('title', '')
    item.description = data.get('description', '')
    item.done = data.get('done', False)
    item.priority = data.get('priority', '')
    item.due_date = data.get('due_date', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/tasks/<int:id>', methods=['PUT'])
@login_required
def update_task(id):
    item = Task.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data: item.title = data['title']
    if 'description' in data: item.description = data['description']
    if 'done' in data: item.done = data['done']
    if 'priority' in data: item.priority = data['priority']
    if 'due_date' in data: item.due_date = data['due_date']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/tasks/<int:id>', methods=['DELETE'])
@login_required
def delete_task(id):
    item = Task.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/tasks/export')
@login_required
def export_tasks():
    items = Task.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['title', 'description', 'done', 'priority', 'due_date'])
    for i in items:
        writer.writerow([i.title, i.description, i.done, i.priority, i.due_date])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=tasks.csv'})


if __name__ == '__main__':
    app.run(debug=True)