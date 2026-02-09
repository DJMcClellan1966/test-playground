"""
Flask Todo API
Learn REST API development with Flask
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage (use SQLite for persistence)
todos = []
next_id = 1

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all todos"""
    return jsonify({'todos': todos})

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Get a specific todo"""
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if todo:
        return jsonify(todo)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    global next_id
    data = request.get_json()
    
    if not data or 'task' not in data:
        return jsonify({'error': 'Task required'}), 400
    
    todo = {
        'id': next_id,
        'task': data['task'],
        'done': False
    }
    todos.append(todo)
    next_id += 1
    
    return jsonify(todo), 201

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo"""
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if not todo:
        return jsonify({'error': 'Not found'}), 404
    
    data = request.get_json()
    if 'task' in data:
        todo['task'] = data['task']
    if 'done' in data:
        todo['done'] = data['done']
    
    return jsonify(todo)

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo"""
    global todos
    todos = [t for t in todos if t['id'] != todo_id]
    return '', 204

if __name__ == '__main__':
    print("🚀 Flask Todo API")
    print("Endpoints:")
    print("  GET    /api/todos       - List all")
    print("  POST   /api/todos       - Create new")
    print("  GET    /api/todos/<id>  - Get one")
    print("  PUT    /api/todos/<id>  - Update")
    print("  DELETE /api/todos/<id>  - Delete")
    app.run(debug=True, port=5000)
