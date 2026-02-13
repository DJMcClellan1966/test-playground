from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from db import db, init_db
from models import User
from werkzeug.security import check_password_hash
from functools import wraps
from models import Movie
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
    return jsonify({"status": "ok", "app": "Movie Collection"})


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


# ==== Movie CRUD ====
@app.route('/api/movies')
@login_required
def list_movies():
    query = Movie.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Movie.title.ilike(f'%{q}%') | Movie.genre.ilike(f'%{q}%') | Movie.notes.ilike(f'%{q}%'))
    items = query.order_by(Movie.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/movies', methods=['POST'])
@login_required
def create_movie():
    data = request.get_json()
    item = Movie()
    item.title = data.get('title', '')
    item.year = data.get('year')
    item.genre = data.get('genre', '')
    item.rating = data.get('rating')
    item.watched = data.get('watched', False)
    item.notes = data.get('notes', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/movies/<int:id>', methods=['PUT'])
@login_required
def update_movie(id):
    item = Movie.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data: item.title = data['title']
    if 'year' in data: item.year = data['year']
    if 'genre' in data: item.genre = data['genre']
    if 'rating' in data: item.rating = data['rating']
    if 'watched' in data: item.watched = data['watched']
    if 'notes' in data: item.notes = data['notes']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/movies/<int:id>', methods=['DELETE'])
@login_required
def delete_movie(id):
    item = Movie.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/movies/export')
@login_required
def export_movies():
    items = Movie.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['title', 'year', 'genre', 'rating', 'watched', 'notes'])
    for i in items:
        writer.writerow([i.title, i.year, i.genre, i.rating, i.watched, i.notes])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=movies.csv'})


if __name__ == '__main__':
    app.run(debug=True)