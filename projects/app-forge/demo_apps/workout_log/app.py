from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from db import db, init_db
from models import User
from werkzeug.security import check_password_hash
from functools import wraps
from models import Workout, Habit
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
    return jsonify({"status": "ok", "app": "Workout Log"})


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


# ==== Workout CRUD ====
@app.route('/api/workouts')
@login_required
def list_workouts():
    query = Workout.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Workout.name.ilike(f'%{q}%') | Workout.exercise_type.ilike(f'%{q}%') | Workout.notes.ilike(f'%{q}%'))
    items = query.order_by(Workout.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/workouts', methods=['POST'])
@login_required
def create_workout():
    data = request.get_json()
    item = Workout()
    item.name = data.get('name', '')
    item.exercise_type = data.get('exercise_type', '')
    item.sets = data.get('sets')
    item.reps = data.get('reps')
    item.weight = data.get('weight')
    item.duration_minutes = data.get('duration_minutes')
    item.notes = data.get('notes', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/workouts/<int:id>', methods=['PUT'])
@login_required
def update_workout(id):
    item = Workout.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data: item.name = data['name']
    if 'exercise_type' in data: item.exercise_type = data['exercise_type']
    if 'sets' in data: item.sets = data['sets']
    if 'reps' in data: item.reps = data['reps']
    if 'weight' in data: item.weight = data['weight']
    if 'duration_minutes' in data: item.duration_minutes = data['duration_minutes']
    if 'notes' in data: item.notes = data['notes']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/workouts/<int:id>', methods=['DELETE'])
@login_required
def delete_workout(id):
    item = Workout.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/workouts/export')
@login_required
def export_workouts():
    items = Workout.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['name', 'exercise_type', 'sets', 'reps', 'weight', 'duration_minutes', 'notes'])
    for i in items:
        writer.writerow([i.name, i.exercise_type, i.sets, i.reps, i.weight, i.duration_minutes, i.notes])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=workouts.csv'})


# ==== Habit CRUD ====
@app.route('/api/habits')
@login_required
def list_habits():
    query = Habit.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Habit.name.ilike(f'%{q}%') | Habit.description.ilike(f'%{q}%'))
    items = query.order_by(Habit.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/habits', methods=['POST'])
@login_required
def create_habit():
    data = request.get_json()
    item = Habit()
    item.name = data.get('name', '')
    item.description = data.get('description', '')
    item.target_per_day = data.get('target_per_day')
    item.completed_today = data.get('completed_today', False)
    item.streak = data.get('streak')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/habits/<int:id>', methods=['PUT'])
@login_required
def update_habit(id):
    item = Habit.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data: item.name = data['name']
    if 'description' in data: item.description = data['description']
    if 'target_per_day' in data: item.target_per_day = data['target_per_day']
    if 'completed_today' in data: item.completed_today = data['completed_today']
    if 'streak' in data: item.streak = data['streak']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/habits/<int:id>', methods=['DELETE'])
@login_required
def delete_habit(id):
    item = Habit.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/habits/export')
@login_required
def export_habits():
    items = Habit.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['name', 'description', 'target_per_day', 'completed_today', 'streak'])
    for i in items:
        writer.writerow([i.name, i.description, i.target_per_day, i.completed_today, i.streak])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=habits.csv'})


if __name__ == '__main__':
    app.run(debug=True)