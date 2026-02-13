from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from db import db, init_db
from models import User
from werkzeug.security import check_password_hash
from functools import wraps
from models import Recipe, Product
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
    return jsonify({"status": "ok", "app": "Meal Planner"})


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


# ==== Recipe CRUD ====
@app.route('/api/recipes')
@login_required
def list_recipes():
    query = Recipe.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Recipe.title.ilike(f'%{q}%') | Recipe.description.ilike(f'%{q}%') | Recipe.ingredients.ilike(f'%{q}%') | Recipe.instructions.ilike(f'%{q}%') | Recipe.category.ilike(f'%{q}%'))
    items = query.order_by(Recipe.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/recipes', methods=['POST'])
@login_required
def create_recipe():
    data = request.get_json()
    item = Recipe()
    item.title = data.get('title', '')
    item.description = data.get('description', '')
    item.ingredients = data.get('ingredients', '')
    item.instructions = data.get('instructions', '')
    item.cook_time_minutes = data.get('cook_time_minutes')
    item.servings = data.get('servings')
    item.rating = data.get('rating')
    item.category = data.get('category', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/recipes/<int:id>', methods=['PUT'])
@login_required
def update_recipe(id):
    item = Recipe.query.get_or_404(id)
    data = request.get_json()
    if 'title' in data: item.title = data['title']
    if 'description' in data: item.description = data['description']
    if 'ingredients' in data: item.ingredients = data['ingredients']
    if 'instructions' in data: item.instructions = data['instructions']
    if 'cook_time_minutes' in data: item.cook_time_minutes = data['cook_time_minutes']
    if 'servings' in data: item.servings = data['servings']
    if 'rating' in data: item.rating = data['rating']
    if 'category' in data: item.category = data['category']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/recipes/<int:id>', methods=['DELETE'])
@login_required
def delete_recipe(id):
    item = Recipe.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/recipes/export')
@login_required
def export_recipes():
    items = Recipe.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['title', 'description', 'ingredients', 'instructions', 'cook_time_minutes', 'servings', 'rating', 'category'])
    for i in items:
        writer.writerow([i.title, i.description, i.ingredients, i.instructions, i.cook_time_minutes, i.servings, i.rating, i.category])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=recipes.csv'})


# ==== Product CRUD ====
@app.route('/api/products')
@login_required
def list_products():
    query = Product.query.filter_by(user_id=session.get('user_id'))
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%') | Product.sku.ilike(f'%{q}%') | Product.category.ilike(f'%{q}%') | Product.description.ilike(f'%{q}%'))
    items = query.order_by(Product.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])

@app.route('/api/products', methods=['POST'])
@login_required
def create_product():
    data = request.get_json()
    item = Product()
    item.name = data.get('name', '')
    item.sku = data.get('sku', '')
    item.quantity = data.get('quantity')
    item.price = data.get('price')
    item.category = data.get('category', '')
    item.description = data.get('description', '')

    item.user_id = session.get('user_id')
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    item = Product.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data: item.name = data['name']
    if 'sku' in data: item.sku = data['sku']
    if 'quantity' in data: item.quantity = data['quantity']
    if 'price' in data: item.price = data['price']
    if 'category' in data: item.category = data['category']
    if 'description' in data: item.description = data['description']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    item = Product.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/products/export')
@login_required
def export_products():
    items = Product.query.filter_by(user_id=session.get('user_id')).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['name', 'sku', 'quantity', 'price', 'category', 'description'])
    for i in items:
        writer.writerow([i.name, i.sku, i.quantity, i.price, i.category, i.description])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=products.csv'})


if __name__ == '__main__':
    app.run(debug=True)