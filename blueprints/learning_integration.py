"""
Learning Integration - Bridges ML-ToolBox with Blueprints System

Integrates:
1. Enhanced Code Generator - Working code patterns (tic-tac-toe, todo, etc.)
2. AI Learning Companion - Adaptive progression tracking
3. Level-gated blocks - Unlock advanced features as user grows

Target: Beginners who grow with the system
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json

# Try to import from ML-ToolBox
ML_TOOLBOX_PATH = Path(r"C:\Users\DJMcC\OneDrive\Desktop\toolbox\ML-ToolBox")
if ML_TOOLBOX_PATH.exists():
    sys.path.insert(0, str(ML_TOOLBOX_PATH))
    HAS_ML_TOOLBOX = True
else:
    HAS_ML_TOOLBOX = False


class SkillLevel(Enum):
    """User skill levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class LearningProfile:
    """Tracks user's learning progress"""
    level: SkillLevel = SkillLevel.BEGINNER
    projects_completed: int = 0
    blocks_used: Set[str] = field(default_factory=set)
    concepts_learned: Set[str] = field(default_factory=set)
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    xp: int = 0  # Experience points
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level.value,
            'projects_completed': self.projects_completed,
            'blocks_used': list(self.blocks_used),
            'concepts_learned': list(self.concepts_learned),
            'weak_areas': self.weak_areas,
            'strong_areas': self.strong_areas,
            'xp': self.xp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "LearningProfile":
        profile = cls()
        profile.level = SkillLevel(data.get('level', 'beginner'))
        profile.projects_completed = data.get('projects_completed', 0)
        profile.blocks_used = set(data.get('blocks_used', []))
        profile.concepts_learned = set(data.get('concepts_learned', []))
        profile.weak_areas = data.get('weak_areas', [])
        profile.strong_areas = data.get('strong_areas', [])
        profile.xp = data.get('xp', 0)
        return profile


# ============================================================================
# LEVEL-GATED BLOCKS
# ============================================================================

# Blocks available at each level
LEVEL_BLOCKS = {
    SkillLevel.BEGINNER: {
        'storage_json': {
            'name': 'JSON Storage',
            'description': 'Simple file-based storage. Perfect for learning!',
            'teaches': ['data persistence', 'JSON format', 'file I/O'],
            'xp_reward': 10,
        },
        'crud_basic': {
            'name': 'Basic CRUD',
            'description': 'Create, Read, Update, Delete operations',
            'teaches': ['CRUD pattern', 'HTTP methods', 'REST basics'],
            'xp_reward': 15,
        },
        'console_ui': {
            'name': 'Console UI',
            'description': 'Text-based user interface',
            'teaches': ['user input', 'output formatting', 'menus'],
            'xp_reward': 10,
        },
    },
    SkillLevel.INTERMEDIATE: {
        'storage_sqlite': {
            'name': 'SQLite Storage',
            'description': 'Relational database. Unlocked after JSON mastery!',
            'teaches': ['SQL', 'relational data', 'queries', 'joins'],
            'requires_concepts': ['data persistence'],
            'xp_reward': 25,
        },
        'auth_basic': {
            'name': 'Basic Auth',
            'description': 'User authentication with sessions',
            'teaches': ['authentication', 'sessions', 'security basics'],
            'requires_concepts': ['CRUD pattern'],
            'xp_reward': 30,
        },
        'flask_routes': {
            'name': 'Flask Routes',
            'description': 'Web routes with Flask',
            'teaches': ['web routing', 'HTTP', 'request/response'],
            'requires_concepts': ['REST basics'],
            'xp_reward': 25,
        },
        'html_ui': {
            'name': 'HTML UI',
            'description': 'Web-based user interface',
            'teaches': ['HTML', 'CSS basics', 'forms'],
            'requires_concepts': ['user input'],
            'xp_reward': 20,
        },
    },
    SkillLevel.ADVANCED: {
        'storage_postgres': {
            'name': 'PostgreSQL',
            'description': 'Production database. For serious apps!',
            'teaches': ['production DB', 'migrations', 'connection pooling'],
            'requires_concepts': ['SQL', 'relational data'],
            'xp_reward': 40,
        },
        'auth_oauth': {
            'name': 'OAuth',
            'description': 'Third-party authentication (Google, GitHub)',
            'teaches': ['OAuth flow', 'tokens', 'identity providers'],
            'requires_concepts': ['authentication', 'sessions'],
            'xp_reward': 45,
        },
        'crdt_sync': {
            'name': 'CRDT Sync',
            'description': 'Conflict-free sync for offline + multi-user',
            'teaches': ['CRDTs', 'distributed systems', 'conflict resolution'],
            'requires_concepts': ['data persistence', 'REST basics'],
            'xp_reward': 50,
        },
        'websocket': {
            'name': 'WebSocket',
            'description': 'Real-time bidirectional communication',
            'teaches': ['WebSocket', 'real-time', 'push notifications'],
            'requires_concepts': ['HTTP', 'web routing'],
            'xp_reward': 40,
        },
    },
    SkillLevel.EXPERT: {
        'kubernetes': {
            'name': 'Kubernetes Deploy',
            'description': 'Container orchestration',
            'teaches': ['containers', 'orchestration', 'scaling'],
            'requires_concepts': ['production DB', 'migrations'],
            'xp_reward': 60,
        },
        'graphql': {
            'name': 'GraphQL API',
            'description': 'Flexible query language for APIs',
            'teaches': ['GraphQL', 'schemas', 'resolvers'],
            'requires_concepts': ['REST basics', 'SQL'],
            'xp_reward': 55,
        },
    },
}


# ============================================================================
# WORKING CODE PATTERNS (from ML-ToolBox enhanced_code_generator.py)
# ============================================================================

CODE_PATTERNS = {
    # Beginner projects
    'guess_number': {
        'level': SkillLevel.BEGINNER,
        'name': 'Guess the Number',
        'description': 'Classic number guessing game',
        'teaches': ['loops', 'conditionals', 'random numbers', 'user input'],
        'xp_reward': 20,
        'code': '''"""
Guess the Number Game
A beginner-friendly project to learn loops and conditionals
"""
import random

def play_game():
    """Main game loop"""
    number = random.randint(1, 100)
    attempts = 0
    
    print("🎮 Guess the Number!")
    print("I'm thinking of a number between 1 and 100.")
    
    while True:
        try:
            guess = int(input("\\nEnter your guess: "))
            attempts += 1
            
            if guess < number:
                print("📉 Too low! Try higher.")
            elif guess > number:
                print("📈 Too high! Try lower.")
            else:
                print(f"\\n🎉 Congratulations! You guessed it in {attempts} attempts!")
                break
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\\nThanks for playing!")
            break

if __name__ == "__main__":
    play_game()
''',
    },
    
    'calculator': {
        'level': SkillLevel.BEGINNER,
        'name': 'Calculator',
        'description': 'Simple arithmetic calculator',
        'teaches': ['functions', 'operators', 'error handling'],
        'xp_reward': 15,
        'code': '''"""
Simple Calculator
Learn functions and error handling
"""

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Division by zero!"
    return a / b

def calculator():
    """Interactive calculator"""
    operations = {
        '+': add,
        '-': subtract,
        '*': multiply,
        '/': divide
    }
    
    print("🧮 Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            expr = input("\\nEnter expression (e.g., 5 + 3): ").strip()
            if expr.lower() == 'quit':
                break
            
            # Parse expression
            parts = expr.split()
            if len(parts) != 3:
                print("Format: number operator number")
                continue
            
            a, op, b = float(parts[0]), parts[1], float(parts[2])
            
            if op in operations:
                result = operations[op](a, b)
                print(f"Result: {result}")
            else:
                print(f"Unknown operator: {op}")
                
        except ValueError:
            print("Invalid numbers!")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    calculator()
''',
    },
    
    'todo_list': {
        'level': SkillLevel.BEGINNER,
        'name': 'Todo List',
        'description': 'Task management with persistence',
        'teaches': ['classes', 'lists', 'file I/O', 'JSON'],
        'xp_reward': 30,
        'code': '''"""
Todo List Application
Learn classes, lists, and file persistence
"""
import json
from pathlib import Path

class TodoList:
    """Simple todo list with persistence"""
    
    def __init__(self, filename="todos.json"):
        self.filename = filename
        self.todos = self._load()
    
    def _load(self):
        """Load todos from file"""
        if Path(self.filename).exists():
            with open(self.filename, 'r') as f:
                return json.load(f)
        return []
    
    def _save(self):
        """Save todos to file"""
        with open(self.filename, 'w') as f:
            json.dump(self.todos, f, indent=2)
    
    def add(self, task):
        """Add a new task"""
        self.todos.append({'task': task, 'done': False})
        self._save()
        print(f"✅ Added: {task}")
    
    def list(self):
        """List all tasks"""
        if not self.todos:
            print("📭 No tasks yet!")
            return
        
        print("\\n📋 Your Tasks:")
        for i, todo in enumerate(self.todos, 1):
            status = "✓" if todo['done'] else " "
            print(f"  {i}. [{status}] {todo['task']}")
    
    def complete(self, index):
        """Mark task as complete"""
        if 1 <= index <= len(self.todos):
            self.todos[index - 1]['done'] = True
            self._save()
            print(f"🎉 Completed: {self.todos[index - 1]['task']}")
        else:
            print("❌ Invalid task number!")
    
    def remove(self, index):
        """Remove a task"""
        if 1 <= index <= len(self.todos):
            task = self.todos.pop(index - 1)['task']
            self._save()
            print(f"🗑️ Removed: {task}")
        else:
            print("❌ Invalid task number!")

def main():
    todo = TodoList()
    
    print("📝 Todo List App")
    print("Commands: add, list, done, remove, quit")
    
    while True:
        cmd = input("\\n> ").strip().lower()
        
        if cmd == 'quit':
            break
        elif cmd == 'list':
            todo.list()
        elif cmd.startswith('add '):
            todo.add(cmd[4:])
        elif cmd.startswith('done '):
            try:
                todo.complete(int(cmd[5:]))
            except ValueError:
                print("Usage: done <number>")
        elif cmd.startswith('remove '):
            try:
                todo.remove(int(cmd[7:]))
            except ValueError:
                print("Usage: remove <number>")
        else:
            print("Commands: add <task>, list, done <n>, remove <n>, quit")

if __name__ == "__main__":
    main()
''',
    },
    
    'tic_tac_toe': {
        'level': SkillLevel.BEGINNER,
        'name': 'Tic-Tac-Toe',
        'description': 'Classic two-player game',
        'teaches': ['2D arrays', 'game logic', 'win detection'],
        'xp_reward': 35,
        'code': '''"""
Tic-Tac-Toe Game
Learn 2D arrays and game logic
"""

def print_board(board):
    """Display the game board"""
    print()
    for i, row in enumerate(board):
        print(f"  {row[0]} | {row[1]} | {row[2]}")
        if i < 2:
            print(" ---|---|---")
    print()

def check_winner(board):
    """Check if there's a winner"""
    # Rows
    for row in board:
        if row[0] == row[1] == row[2] != ' ':
            return row[0]
    
    # Columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != ' ':
            return board[0][col]
    
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]
    
    return None

def is_full(board):
    """Check if board is full"""
    return all(cell != ' ' for row in board for cell in row)

def play_game():
    """Main game loop"""
    board = [[' ' for _ in range(3)] for _ in range(3)]
    current = 'X'
    
    print("🎮 Tic-Tac-Toe")
    print("Enter position as row,col (0-2)")
    print("Example: 1,1 for center")
    
    while True:
        print_board(board)
        print(f"Player {current}'s turn")
        
        try:
            move = input("Enter row,col: ")
            row, col = map(int, move.split(','))
            
            if not (0 <= row <= 2 and 0 <= col <= 2):
                print("Position must be 0-2!")
                continue
            
            if board[row][col] != ' ':
                print("Cell already taken!")
                continue
            
            board[row][col] = current
            
            winner = check_winner(board)
            if winner:
                print_board(board)
                print(f"🎉 Player {winner} wins!")
                break
            
            if is_full(board):
                print_board(board)
                print("🤝 It's a tie!")
                break
            
            current = 'O' if current == 'X' else 'X'
            
        except (ValueError, IndexError):
            print("Invalid input! Use format: row,col")
        except KeyboardInterrupt:
            print("\\nGame ended.")
            break

if __name__ == "__main__":
    play_game()
''',
    },
    
    # Intermediate projects
    'flask_todo': {
        'level': SkillLevel.INTERMEDIATE,
        'name': 'Flask Todo API',
        'description': 'RESTful API with Flask',
        'teaches': ['REST API', 'Flask', 'HTTP methods', 'JSON API'],
        'xp_reward': 50,
        'code': '''"""
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
''',
    },
    
    'sqlite_crud': {
        'level': SkillLevel.INTERMEDIATE,
        'name': 'SQLite CRUD',
        'description': 'Database operations with SQLite',
        'teaches': ['SQL', 'SQLite', 'database design', 'CRUD'],
        'xp_reward': 45,
        'code': '''"""
SQLite CRUD Operations
Learn database operations with SQLite
"""
import sqlite3
from contextlib import contextmanager

DB_FILE = "app.db"

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Initialize database schema"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    print("📦 Database initialized!")

def create_task(title, description=""):
    """Create a new task"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)",
            (title, description)
        )
        print(f"✅ Created task #{cursor.lastrowid}: {title}")
        return cursor.lastrowid

def get_all_tasks():
    """Get all tasks"""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

def get_task(task_id):
    """Get a specific task"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

def update_task(task_id, **kwargs):
    """Update a task"""
    valid_fields = {'title', 'description', 'done'}
    updates = {k: v for k, v in kwargs.items() if k in valid_fields}
    
    if not updates:
        return False
    
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]
    
    with get_db() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    print(f"📝 Updated task #{task_id}")
    return True

def delete_task(task_id):
    """Delete a task"""
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    print(f"🗑️ Deleted task #{task_id}")

def main():
    """Demo CRUD operations"""
    init_db()
    
    # Create
    id1 = create_task("Learn SQL", "Study SELECT, INSERT, UPDATE, DELETE")
    id2 = create_task("Build API", "Create REST endpoints")
    
    # Read
    print("\\n📋 All tasks:")
    for task in get_all_tasks():
        status = "✓" if task['done'] else " "
        print(f"  [{status}] #{task['id']}: {task['title']}")
    
    # Update
    update_task(id1, done=True)
    
    # Read one
    task = get_task(id1)
    print(f"\\n📌 Task #{id1}: {task}")
    
    # Delete
    delete_task(id2)

if __name__ == "__main__":
    main()
''',
    },
    
    # ========================================================================
    # ML_COMPASS CURRICULUM - Algorithm Fundamentals (Knuth)
    # ========================================================================
    
    'knuth_lcg': {
        'name': 'Linear Congruential Generator',
        'description': 'Implement the classic LCG pseudo-random number generator from TAOCP',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['algorithms', 'number_theory', 'modular_arithmetic'],
        'xp_reward': 40,
        'source': 'Knuth - The Art of Computer Programming',
        'code': '''"""
Linear Congruential Generator (LCG)
From: Knuth's "The Art of Computer Programming"

The LCG generates pseudo-random numbers using:
    X(n+1) = (a * X(n) + c) mod m

Key insight: The choice of a, c, m determines the period and quality.
"""

class LCG:
    """Linear Congruential Generator - classic PRNG algorithm"""
    
    def __init__(self, seed: int = 42, 
                 a: int = 1103515245,  # multiplier
                 c: int = 12345,       # increment
                 m: int = 2**31):      # modulus
        self.state = seed
        self.a = a
        self.c = c
        self.m = m
    
    def next(self) -> int:
        """Generate next pseudo-random number"""
        self.state = (self.a * self.state + self.c) % self.m
        return self.state
    
    def random(self) -> float:
        """Generate float in [0, 1)"""
        return self.next() / self.m
    
    def randint(self, low: int, high: int) -> int:
        """Generate integer in [low, high]"""
        return low + (self.next() % (high - low + 1))


def demo():
    rng = LCG(seed=12345)
    
    print("First 10 random numbers:")
    for i in range(10):
        print(f"  {i+1}: {rng.random():.6f}")
    
    print("\\n10 dice rolls:")
    rng2 = LCG(seed=42)
    rolls = [rng2.randint(1, 6) for _ in range(10)]
    print(f"  {rolls}")


if __name__ == "__main__":
    demo()
''',
    },
    
    'knuth_fisher_yates': {
        'name': 'Fisher-Yates Shuffle',
        'description': 'The optimal O(n) algorithm for shuffling arrays in-place',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['algorithms', 'randomization', 'in_place_algorithms'],
        'xp_reward': 35,
        'source': 'Knuth - The Art of Computer Programming',
        'code': '''"""
Fisher-Yates Shuffle Algorithm
From: Knuth's "The Art of Computer Programming"

The only correct way to shuffle an array uniformly at random.
Each permutation has exactly 1/n! probability.
"""
import random


def fisher_yates_shuffle(arr: list) -> list:
    """
    Shuffle array in-place using Fisher-Yates algorithm.
    
    Algorithm:
    1. Start from the last element
    2. Swap it with a random element from [0, i]
    3. Move to i-1 and repeat
    
    Why it works: Each position has equal probability of any element.
    """
    arr = arr.copy()  # Don't modify original
    n = len(arr)
    
    for i in range(n - 1, 0, -1):
        # Pick random index from 0 to i (inclusive)
        j = random.randint(0, i)
        # Swap
        arr[i], arr[j] = arr[j], arr[i]
    
    return arr


def biased_shuffle_wrong(arr: list) -> list:
    """
    WRONG way to shuffle - creates biased distribution!
    Don't do this - shown for educational purposes.
    """
    arr = arr.copy()
    n = len(arr)
    for i in range(n):
        j = random.randint(0, n - 1)  # Bug: should be randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def demo():
    cards = ["A♠", "K♠", "Q♠", "J♠", "10♠"]
    
    print("Original deck:", cards)
    print("\\nShuffled (Fisher-Yates):")
    for i in range(3):
        print(f"  {i+1}: {fisher_yates_shuffle(cards)}")
    
    # Test uniformity
    print("\\nTesting uniformity (first position distribution for [0,1,2]):")
    counts = {0: 0, 1: 0, 2: 0}
    for _ in range(30000):
        shuffled = fisher_yates_shuffle([0, 1, 2])
        counts[shuffled[0]] += 1
    
    for val, count in counts.items():
        print(f"  {val} appeared first: {count/300:.1f}% (expected: 33.3%)")


if __name__ == "__main__":
    demo()
''',
    },
    
    'knuth_binary_search': {
        'name': 'Binary Search Variations',
        'description': 'Master binary search with lower/upper bound variants',
        'level': SkillLevel.BEGINNER,
        'teaches': ['algorithms', 'searching', 'divide_and_conquer'],
        'xp_reward': 30,
        'source': 'Knuth - The Art of Computer Programming',
        'code': '''"""
Binary Search and Its Variations
From: Knuth's "The Art of Computer Programming"

The most important search algorithm - O(log n) complexity.
"""
from typing import List, Optional


def binary_search(arr: List[int], target: int) -> Optional[int]:
    """Find exact match, return index or None"""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2  # Prevent overflow
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return None


def lower_bound(arr: List[int], target: int) -> int:
    """
    Find first position where target could be inserted.
    Returns index of first element >= target.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left


def upper_bound(arr: List[int], target: int) -> int:
    """
    Find last position where target could be inserted.
    Returns index of first element > target.
    """
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    
    return left


def count_occurrences(arr: List[int], target: int) -> int:
    """Count how many times target appears using bounds"""
    return upper_bound(arr, target) - lower_bound(arr, target)


def demo():
    arr = [1, 2, 2, 2, 3, 4, 4, 5, 6]
    print(f"Array: {arr}")
    
    # Basic search
    print(f"\\nSearch for 4: index {binary_search(arr, 4)}")
    print(f"Search for 7: {binary_search(arr, 7)}")
    
    # Bounds
    print(f"\\nLower bound of 2: {lower_bound(arr, 2)} (first 2)")
    print(f"Upper bound of 2: {upper_bound(arr, 2)} (after last 2)")
    print(f"Count of 2s: {count_occurrences(arr, 2)}")
    
    # Practical: find insertion point
    print(f"\\nInsert 3.5 at position: {upper_bound(arr, 3)}")


if __name__ == "__main__":
    demo()
''',
    },
    
    'knuth_heapsort': {
        'name': 'Heapsort Algorithm',
        'description': 'In-place O(n log n) sorting using the heap data structure',
        'level': SkillLevel.ADVANCED,
        'teaches': ['algorithms', 'sorting', 'heap', 'data_structures'],
        'xp_reward': 50,
        'source': 'Knuth - The Art of Computer Programming',
        'code': '''"""
Heapsort Algorithm
From: Knuth's "The Art of Computer Programming"

Guarantees O(n log n) in ALL cases (unlike quicksort).
In-place, but not stable.
"""
from typing import List


def heapify(arr: List[int], n: int, i: int):
    """
    Maintain max-heap property for subtree rooted at index i.
    
    A max-heap has: parent >= both children
    For node at i:
        - Left child: 2*i + 1
        - Right child: 2*i + 2
        - Parent: (i-1) // 2
    """
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    # Check if left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left
    
    # Check if right child exists and is greater than current largest
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    # If largest is not root, swap and continue heapifying
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def heapsort(arr: List[int]) -> List[int]:
    """
    Sort array using heapsort algorithm.
    
    Steps:
    1. Build max-heap from array
    2. Extract max (move to end), reduce heap size
    3. Repeat until sorted
    """
    arr = arr.copy()
    n = len(arr)
    
    # Build max-heap (start from last non-leaf node)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements one by one
    for i in range(n - 1, 0, -1):
        # Move current root (max) to end
        arr[0], arr[i] = arr[i], arr[0]
        # Heapify reduced heap
        heapify(arr, i, 0)
    
    return arr


def demo():
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original: {arr}")
    print(f"Sorted:   {heapsort(arr)}")
    
    # Show heap building process
    print("\\nHeap building visualization:")
    test = [4, 10, 3, 5, 1]
    print(f"  Input: {test}")
    
    # Build heap step by step
    for i in range((len(test) // 2) - 1, -1, -1):
        heapify(test, len(test), i)
        print(f"  After heapify({i}): {test}")


if __name__ == "__main__":
    demo()
''',
    },
    
    # ========================================================================
    # ALGORITHM PATTERNS (Skiena / Bentley)
    # ========================================================================
    
    'kadane_algorithm': {
        'name': "Kadane's Algorithm - Maximum Subarray",
        'description': 'The elegant O(n) solution to maximum subarray problem',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['algorithms', 'dynamic_programming', 'optimization'],
        'xp_reward': 40,
        'source': 'Bentley - Programming Pearls',
        'code': '''"""
Kadane\'s Algorithm - Maximum Subarray Sum
From: Bentley's "Programming Pearls"

Find the contiguous subarray with the largest sum.
This is the OPTIMAL solution: O(n) time, O(1) space.
"""
from typing import List, Tuple


def kadane(arr: List[int]) -> int:
    """
    Find maximum subarray sum.
    
    Key insight: At each position, either:
    1. Extend the previous subarray, OR
    2. Start a new subarray here
    
    max_ending_here = max(arr[i], max_ending_here + arr[i])
    """
    if not arr:
        return 0
    
    max_so_far = arr[0]
    max_ending_here = arr[0]
    
    for i in range(1, len(arr)):
        # Either extend or start fresh
        max_ending_here = max(arr[i], max_ending_here + arr[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far


def kadane_with_indices(arr: List[int]) -> Tuple[int, int, int]:
    """Find maximum subarray sum AND the indices"""
    if not arr:
        return 0, 0, 0
    
    max_so_far = arr[0]
    max_ending_here = arr[0]
    
    start = end = 0
    temp_start = 0
    
    for i in range(1, len(arr)):
        if arr[i] > max_ending_here + arr[i]:
            max_ending_here = arr[i]
            temp_start = i
        else:
            max_ending_here = max_ending_here + arr[i]
        
        if max_ending_here > max_so_far:
            max_so_far = max_ending_here
            start = temp_start
            end = i
    
    return max_so_far, start, end


def demo():
    arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(f"Array: {arr}")
    
    max_sum = kadane(arr)
    print(f"\\nMaximum subarray sum: {max_sum}")
    
    total, start, end = kadane_with_indices(arr)
    subarray = arr[start:end + 1]
    print(f"Subarray: {subarray} (indices {start} to {end})")
    
    # Edge cases
    print("\\nEdge cases:")
    print(f"  All negative [-3, -1, -2]: {kadane([-3, -1, -2])}")
    print(f"  Single element [5]: {kadane([5])}")
    print(f"  All positive [1, 2, 3]: {kadane([1, 2, 3])}")


if __name__ == "__main__":
    demo()
''',
    },
    
    'backtracking_template': {
        'name': 'Backtracking Template',
        'description': 'The universal template for constraint satisfaction problems',
        'level': SkillLevel.ADVANCED,
        'teaches': ['algorithms', 'backtracking', 'recursion', 'constraint_satisfaction'],
        'xp_reward': 55,
        'source': 'Skiena - Algorithm Design Manual',
        'code': '''"""
Backtracking Template
From: Skiena's "Algorithm Design Manual"

A universal pattern for exploring solution spaces.
Use when: combinations, permutations, constraint satisfaction.
"""
from typing import List, Any


def backtrack_template(
    state: Any,
    choices: List[Any],
    results: List[Any],
    is_solution: callable,
    is_valid: callable
):
    """
    Universal backtracking template.
    
    Parameters:
    - state: Current partial solution
    - choices: Available choices at this step
    - results: Accumulator for all solutions
    - is_solution: Check if state is complete solution
    - is_valid: Check if choice is valid given current state
    """
    if is_solution(state):
        results.append(state.copy())
        return
    
    for choice in choices:
        if is_valid(state, choice):
            # Make choice
            state.append(choice)
            
            # Recurse
            backtrack_template(state, choices, results, is_solution, is_valid)
            
            # Undo choice (backtrack)
            state.pop()


# ============================================================================
# EXAMPLE 1: Generate all subsets
# ============================================================================

def subsets(nums: List[int]) -> List[List[int]]:
    """Generate all subsets (power set)"""
    results = []
    
    def backtrack(start: int, current: List[int]):
        results.append(current.copy())
        
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()
    
    backtrack(0, [])
    return results


# ============================================================================
# EXAMPLE 2: N-Queens Problem
# ============================================================================

def n_queens(n: int) -> List[List[str]]:
    """Solve N-Queens: place N queens on NxN board with no attacks"""
    results = []
    
    def is_safe(queens: List[int], row: int, col: int) -> bool:
        for r, c in enumerate(queens):
            if c == col:  # Same column
                return False
            if abs(r - row) == abs(c - col):  # Same diagonal
                return False
        return True
    
    def backtrack(queens: List[int]):
        row = len(queens)
        if row == n:
            # Convert to board representation
            board = []
            for c in queens:
                board.append("." * c + "Q" + "." * (n - c - 1))
            results.append(board)
            return
        
        for col in range(n):
            if is_safe(queens, row, col):
                queens.append(col)
                backtrack(queens)
                queens.pop()
    
    backtrack([])
    return results


def demo():
    print("=== Subsets ===")
    nums = [1, 2, 3]
    print(f"Subsets of {nums}:")
    for subset in subsets(nums):
        print(f"  {subset}")
    
    print("\\n=== N-Queens (4x4) ===")
    solutions = n_queens(4)
    print(f"Found {len(solutions)} solutions")
    for i, board in enumerate(solutions[:2]):  # Show first 2
        print(f"\\nSolution {i + 1}:")
        for row in board:
            print(f"  {row}")


if __name__ == "__main__":
    demo()
''',
    },
    
    'dp_template': {
        'name': 'Dynamic Programming Templates',
        'description': 'Common DP patterns: memoization, tabulation, and state design',
        'level': SkillLevel.ADVANCED,
        'teaches': ['algorithms', 'dynamic_programming', 'optimization', 'memoization'],
        'xp_reward': 60,
        'source': 'Algorithm Design Manual + CLRS',
        'code': '''"""
Dynamic Programming Templates
Essential patterns for optimization problems.

When to use DP:
1. Optimal substructure (optimal solution uses optimal sub-solutions)
2. Overlapping subproblems (same computation repeated)
"""
from functools import lru_cache
from typing import List


# ============================================================================
# PATTERN 1: Top-Down (Memoization)
# ============================================================================

@lru_cache(maxsize=None)
def fibonacci_memo(n: int) -> int:
    """Classic example - O(n) with memoization vs O(2^n) naive"""
    if n <= 1:
        return n
    return fibonacci_memo(n - 1) + fibonacci_memo(n - 2)


# ============================================================================
# PATTERN 2: Bottom-Up (Tabulation)
# ============================================================================

def fibonacci_tab(n: int) -> int:
    """Bottom-up - explicit table, often faster"""
    if n <= 1:
        return n
    
    dp = [0] * (n + 1)
    dp[1] = 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    
    return dp[n]


# ============================================================================
# PATTERN 3: Space Optimized
# ============================================================================

def fibonacci_opt(n: int) -> int:
    """O(1) space - when only previous states matter"""
    if n <= 1:
        return n
    
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    
    return curr


# ============================================================================
# CLASSIC: Longest Common Subsequence (LCS)
# ============================================================================

def lcs(s1: str, s2: str) -> str:
    """Find longest common subsequence"""
    m, n = len(s1), len(s2)
    
    # Build DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # Reconstruct solution
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            result.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    
    return "".join(reversed(result))


# ============================================================================
# CLASSIC: 0/1 Knapsack
# ============================================================================

def knapsack(weights: List[int], values: List[int], capacity: int) -> int:
    """Classic 0/1 knapsack - O(n * capacity)"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(capacity + 1):
            # Don\'t take item i
            dp[i][w] = dp[i - 1][w]
            
            # Take item i (if it fits)
            if weights[i - 1] <= w:
                dp[i][w] = max(
                    dp[i][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
    
    return dp[n][capacity]


def demo():
    print("=== Fibonacci (3 approaches, same result) ===")
    n = 20
    print(f"fib({n}) = {fibonacci_memo(n)} = {fibonacci_tab(n)} = {fibonacci_opt(n)}")
    
    print("\\n=== Longest Common Subsequence ===")
    s1, s2 = "ABCDGH", "AEDFHR"
    print(f"LCS('{s1}', '{s2}') = '{lcs(s1, s2)}'")
    
    print("\\n=== 0/1 Knapsack ===")
    weights = [1, 3, 4, 5]
    values = [1, 4, 5, 7]
    capacity = 7
    print(f"Weights: {weights}, Values: {values}, Capacity: {capacity}")
    print(f"Max value: {knapsack(weights, values, capacity)}")


if __name__ == "__main__":
    demo()
''',
    },
    
    # ========================================================================
    # INFORMATION THEORY FUNDAMENTALS
    # ========================================================================
    
    'info_entropy': {
        'name': 'Information Entropy',
        'description': 'Shannon entropy and information content measurement',
        'level': SkillLevel.ADVANCED,
        'teaches': ['information_theory', 'entropy', 'probability', 'ml_fundamentals'],
        'xp_reward': 45,
        'source': 'Shannon - A Mathematical Theory of Communication',
        'code': '''"""
Information Entropy
From: Shannon's "A Mathematical Theory of Communication"

Entropy measures the average "surprise" or information content.
Fundamental to: compression, ML (cross-entropy loss), decision trees.
"""
import math
from typing import List, Dict
from collections import Counter


def entropy(probabilities: List[float]) -> float:
    """
    Calculate Shannon entropy: H = -Σ p(x) * log2(p(x))
    
    Entropy is maximized when all outcomes are equally likely.
    Entropy is 0 when outcome is certain.
    """
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def entropy_from_data(data: List) -> float:
    """Calculate entropy from a list of observations"""
    n = len(data)
    if n == 0:
        return 0.0
    
    counts = Counter(data)
    probabilities = [count / n for count in counts.values()]
    return entropy(probabilities)


def information_content(probability: float) -> float:
    """
    Information content (self-information) of single event.
    I(x) = -log2(p(x))
    
    Lower probability = higher information when it occurs.
    """
    if probability <= 0:
        return float('inf')
    return -math.log2(probability)


def cross_entropy(true_probs: List[float], pred_probs: List[float]) -> float:
    """
    Cross-entropy: H(p, q) = -Σ p(x) * log2(q(x))
    
    Used in ML as loss function - measures how well q predicts p.
    """
    return -sum(p * math.log2(q) for p, q in zip(true_probs, pred_probs) if p > 0 and q > 0)


def kl_divergence(p: List[float], q: List[float]) -> float:
    """
    Kullback-Leibler divergence: D_KL(P || Q)
    
    Measures how different Q is from P.
    Not symmetric: D_KL(P||Q) ≠ D_KL(Q||P)
    """
    return sum(pi * math.log2(pi / qi) for pi, qi in zip(p, q) if pi > 0 and qi > 0)


def demo():
    print("=== Information Content ===")
    print(f"Fair coin flip: {information_content(0.5):.2f} bits")
    print(f"Rolling a 6: {information_content(1/6):.2f} bits")
    print(f"Rare event (1%): {information_content(0.01):.2f} bits")
    
    print("\\n=== Entropy ===")
    fair_coin = [0.5, 0.5]
    biased_coin = [0.9, 0.1]
    fair_die = [1/6] * 6
    
    print(f"Fair coin: {entropy(fair_coin):.3f} bits")
    print(f"Biased coin (90/10): {entropy(biased_coin):.3f} bits")
    print(f"Fair 6-sided die: {entropy(fair_die):.3f} bits")
    
    print("\\n=== Entropy from Data ===")
    text = "AAABBC"
    print(f"String '{text}': {entropy_from_data(text):.3f} bits")
    
    print("\\n=== Cross-Entropy (ML Loss) ===")
    true = [1.0, 0.0, 0.0]  # One-hot: class 0
    good_pred = [0.9, 0.05, 0.05]
    bad_pred = [0.1, 0.8, 0.1]
    print(f"Good prediction: {cross_entropy(true, good_pred):.3f}")
    print(f"Bad prediction: {cross_entropy(true, bad_pred):.3f}")


if __name__ == "__main__":
    demo()
''',
    },
    
    # ========================================================================
    # ML FUNDAMENTALS
    # ========================================================================
    
    'bias_variance': {
        'name': 'Bias-Variance Tradeoff',
        'description': 'Understanding the fundamental ML tradeoff',
        'level': SkillLevel.ADVANCED,
        'teaches': ['ml_fundamentals', 'model_selection', 'overfitting', 'regularization'],
        'xp_reward': 50,
        'source': 'Bishop - Pattern Recognition and Machine Learning',
        'code': '''"""
Bias-Variance Tradeoff
From: Bishop's "Pattern Recognition and Machine Learning"

Error = Bias² + Variance + Irreducible Noise

- High Bias: Model too simple, underfits (misses patterns)
- High Variance: Model too complex, overfits (memorizes noise)
"""
import random
from typing import List, Tuple


def generate_data(n: int = 50, noise: float = 0.3) -> Tuple[List[float], List[float]]:
    """Generate noisy data from y = sin(x)"""
    x = [random.uniform(0, 2 * 3.14159) for _ in range(n)]
    y = [math.sin(xi) + random.gauss(0, noise) for xi in x]
    return x, y


import math


def polynomial_fit(x: List[float], y: List[float], degree: int) -> List[float]:
    """
    Fit polynomial of given degree using least squares.
    Returns coefficients [a0, a1, a2, ...] for a0 + a1*x + a2*x² + ...
    
    Note: Simplified implementation - use numpy.polyfit in production.
    """
    n = len(x)
    
    # Build Vandermonde matrix
    X = [[xi ** d for d in range(degree + 1)] for xi in x]
    
    # Solve X.T @ X @ coeffs = X.T @ y (normal equations)
    # Simplified: just use polynomial approximation for demo
    
    # For demo, return rough fits
    if degree == 1:
        # Linear fit
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        numer = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denom = sum((xi - x_mean) ** 2 for xi in x)
        slope = numer / denom if denom != 0 else 0
        intercept = y_mean - slope * x_mean
        return [intercept, slope]
    else:
        # For higher degrees, approximate
        return [0] * (degree + 1)  # Placeholder


def predict(x: float, coeffs: List[float]) -> float:
    """Evaluate polynomial at x"""
    return sum(c * (x ** i) for i, c in enumerate(coeffs))


def mse(y_true: List[float], y_pred: List[float]) -> float:
    """Mean squared error"""
    return sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)


def demo():
    print("=== Bias-Variance Tradeoff Demo ===")
    print()
    
    # The theory
    print("KEY INSIGHT:")
    print("  Error = Bias² + Variance + Irreducible Noise")
    print()
    print("  Bias: Error from wrong assumptions")
    print("    → High when model is too simple")
    print("    → Leads to UNDERFITTING")
    print()
    print("  Variance: Error from sensitivity to training data")
    print("    → High when model is too complex")
    print("    → Leads to OVERFITTING")
    print()
    
    print("EXAMPLES:")
    print("-" * 50)
    
    models = [
        ("Linear (degree 1)", "High bias, Low variance", "Underfits"),
        ("Polynomial (degree 3)", "Balanced", "Often optimal"),
        ("Polynomial (degree 15)", "Low bias, High variance", "Overfits"),
    ]
    
    for name, bv, behavior in models:
        print(f"  {name}:")
        print(f"    {bv}")
        print(f"    → {behavior}")
        print()
    
    print("HOW TO DIAGNOSE:")
    print("-" * 50)
    print("  Underfitting (High Bias):")
    print("    - Training error is high")
    print("    - Training ≈ Validation error")
    print("    - Fix: More complex model, more features")
    print()
    print("  Overfitting (High Variance):")
    print("    - Training error is low")
    print("    - Validation error >> Training error")
    print("    - Fix: Regularization, more data, simpler model")
    print()
    
    print("REGULARIZATION TECHNIQUES:")
    print("  - L1 (Lasso): Promotes sparsity")
    print("  - L2 (Ridge): Shrinks all coefficients")
    print("  - Dropout: Random neuron deactivation")
    print("  - Early stopping: Stop before overfitting")


if __name__ == "__main__":
    demo()
''',
    },
    
    'cross_validation': {
        'name': 'Cross-Validation',
        'description': 'Robust model evaluation with k-fold cross-validation',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['ml_fundamentals', 'model_evaluation', 'validation'],
        'xp_reward': 40,
        'source': 'Practical Machine Learning',
        'code': '''"""
Cross-Validation
Essential technique for robust model evaluation.

Why: Single train/test split can be misleading.
How: Multiple splits, average the results.
"""
import random
from typing import List, Tuple, Callable, Any


def k_fold_split(data: List[Any], k: int = 5) -> List[Tuple[List[Any], List[Any]]]:
    """
    Split data into k folds for cross-validation.
    
    Returns list of (train, test) tuples.
    Each data point appears in exactly one test fold.
    """
    # Shuffle data
    data = data.copy()
    random.shuffle(data)
    
    # Calculate fold sizes
    n = len(data)
    fold_size = n // k
    
    folds = []
    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        
        test = data[start:end]
        train = data[:start] + data[end:]
        folds.append((train, test))
    
    return folds


def cross_validate(
    data: List[Any],
    train_model: Callable,
    evaluate: Callable,
    k: int = 5
) -> dict:
    """
    Perform k-fold cross-validation.
    
    Parameters:
    - data: Full dataset
    - train_model: Function(train_data) -> model
    - evaluate: Function(model, test_data) -> score
    - k: Number of folds
    
    Returns dict with scores and statistics.
    """
    folds = k_fold_split(data, k)
    scores = []
    
    for i, (train, test) in enumerate(folds):
        model = train_model(train)
        score = evaluate(model, test)
        scores.append(score)
        print(f"  Fold {i + 1}: {score:.4f}")
    
    return {
        'scores': scores,
        'mean': sum(scores) / len(scores),
        'std': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5,
        'min': min(scores),
        'max': max(scores)
    }


def leave_one_out(data: List[Any]) -> List[Tuple[List[Any], List[Any]]]:
    """
    Leave-One-Out Cross-Validation (LOOCV).
    
    Each sample is used once as test set.
    Most thorough but computationally expensive.
    """
    return [(data[:i] + data[i+1:], [data[i]]) for i in range(len(data))]


def stratified_k_fold(data: List[Tuple[Any, Any]], k: int = 5) -> List[Tuple[List, List]]:
    """
    Stratified K-Fold: Preserves class distribution in each fold.
    
    Important for imbalanced datasets!
    data: List of (features, label) tuples
    """
    # Group by label
    by_label = {}
    for item in data:
        label = item[1]
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(item)
    
    # Shuffle each group
    for label in by_label:
        random.shuffle(by_label[label])
    
    # Distribute to folds
    folds = [[] for _ in range(k)]
    for label, items in by_label.items():
        for i, item in enumerate(items):
            folds[i % k].append(item)
    
    # Create train/test splits
    result = []
    for i in range(k):
        test = folds[i]
        train = [item for j, fold in enumerate(folds) if j != i for item in fold]
        result.append((train, test))
    
    return result


def demo():
    print("=== Cross-Validation Demo ===\\n")
    
    # Simulate a dataset
    random.seed(42)
    data = [(random.random(), random.randint(0, 1)) for _ in range(100)]
    
    # Dummy model and evaluator for demo
    def dummy_train(train_data):
        # Returns "model" (just the training data mean)
        return sum(x[0] for x in train_data) / len(train_data)
    
    def dummy_evaluate(model, test_data):
        # Returns accuracy (random for demo)
        return 0.7 + random.random() * 0.2
    
    print("5-Fold Cross-Validation:")
    results = cross_validate(data, dummy_train, dummy_evaluate, k=5)
    print(f"\\nResults:")
    print(f"  Mean: {results['mean']:.4f} ± {results['std']:.4f}")
    print(f"  Range: [{results['min']:.4f}, {results['max']:.4f}]")
    
    print("\\n" + "=" * 50)
    print("\\nWHEN TO USE WHAT:")
    print("-" * 50)
    print("  5 or 10-Fold: Default choice, good balance")
    print("  Leave-One-Out: Small datasets, expensive")
    print("  Stratified: Imbalanced classes (ALWAYS use!)")
    print("  Repeated: More stable estimates")


if __name__ == "__main__":
    demo()
''',
    },
    
    # ========================================================================
    # PUZZLE GAME PROJECT
    # ========================================================================
    
    'sliding_puzzle': {
        'name': 'Sliding Puzzle Game',
        'description': 'Build a classic 15-puzzle game with HTML/CSS/JavaScript',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['html', 'css', 'javascript', 'game_logic', 'arrays', 'event_handling'],
        'xp_reward': 65,
        'source': 'Desktop/puzzle project',
        'code': '''"""
Sliding Puzzle Game
A complete web-based puzzle game teaching:
- HTML structure
- CSS Grid layout  
- JavaScript arrays and DOM manipulation
- Game state management
- Event handling

Save this as puzzle.html and open in a browser!
"""

HTML_CODE = \'\'\'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sliding Puzzle</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .game-container {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            text-align: center;
        }
        
        h1 {
            color: #333;
            margin-bottom: 16px;
        }
        
        .stats {
            display: flex;
            gap: 24px;
            justify-content: center;
            margin-bottom: 16px;
            color: #666;
        }
        
        .puzzle-grid {
            display: grid;
            grid-template-columns: repeat(4, 80px);
            grid-template-rows: repeat(4, 80px);
            gap: 4px;
            margin: 20px auto;
            background: #ddd;
            padding: 4px;
            border-radius: 8px;
        }
        
        .tile {
            background: #4a90d9;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.15s, background 0.15s;
        }
        
        .tile:hover:not(.empty) {
            background: #357abd;
            transform: scale(0.95);
        }
        
        .tile.empty {
            background: transparent;
            cursor: default;
        }
        
        .controls {
            margin-top: 16px;
        }
        
        button.shuffle {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 32px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        button.shuffle:hover {
            background: #5a6fd6;
        }
        
        .win-message {
            color: #27ae60;
            font-size: 24px;
            font-weight: bold;
            margin-top: 16px;
            display: none;
        }
        
        .win-message.show {
            display: block;
            animation: bounce 0.5s ease;
        }
        
        @keyframes bounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🧩 Sliding Puzzle</h1>
        
        <div class="stats">
            <span>Moves: <strong id="moves">0</strong></span>
            <span>Time: <strong id="time">0:00</strong></span>
        </div>
        
        <div class="puzzle-grid" id="grid"></div>
        
        <div class="controls">
            <button class="shuffle" onclick="shuffle()">Shuffle</button>
        </div>
        
        <div class="win-message" id="win">🎉 You Win!</div>
    </div>

    <script>
        // Game State
        let tiles = [];
        let moves = 0;
        let timer = null;
        let seconds = 0;
        
        // Initialize solved state: [1,2,3,...,15,0]
        function initTiles() {
            tiles = [...Array(15).keys()].map(i => i + 1);
            tiles.push(0); // 0 = empty
        }
        
        // Find empty tile index
        function findEmpty() {
            return tiles.indexOf(0);
        }
        
        // Get valid moves (adjacent to empty)
        function getValidMoves() {
            const empty = findEmpty();
            const row = Math.floor(empty / 4);
            const col = empty % 4;
            const moves = [];
            
            if (row > 0) moves.push(empty - 4); // Up
            if (row < 3) moves.push(empty + 4); // Down
            if (col > 0) moves.push(empty - 1); // Left
            if (col < 3) moves.push(empty + 1); // Right
            
            return moves;
        }
        
        // Move tile at index if valid
        function moveTile(index) {
            const empty = findEmpty();
            const valid = getValidMoves();
            
            if (valid.includes(index)) {
                // Swap
                tiles[empty] = tiles[index];
                tiles[index] = 0;
                
                moves++;
                document.getElementById("moves").textContent = moves;
                
                render();
                checkWin();
                return true;
            }
            return false;
        }
        
        // Shuffle (make 100 random valid moves)
        function shuffle() {
            initTiles();
            for (let i = 0; i < 100; i++) {
                const valid = getValidMoves();
                const randomMove = valid[Math.floor(Math.random() * valid.length)];
                const empty = findEmpty();
                tiles[empty] = tiles[randomMove];
                tiles[randomMove] = 0;
            }
            
            moves = 0;
            seconds = 0;
            document.getElementById("moves").textContent = "0";
            document.getElementById("time").textContent = "0:00";
            document.getElementById("win").classList.remove("show");
            
            // Start timer
            if (timer) clearInterval(timer);
            timer = setInterval(() => {
                seconds++;
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                document.getElementById("time").textContent = 
                    mins + ":" + secs.toString().padStart(2, "0");
            }, 1000);
            
            render();
        }
        
        // Check for win
        function checkWin() {
            for (let i = 0; i < 15; i++) {
                if (tiles[i] !== i + 1) return false;
            }
            if (tiles[15] !== 0) return false;
            
            // Win!
            clearInterval(timer);
            document.getElementById("win").classList.add("show");
            return true;
        }
        
        // Render the grid
        function render() {
            const grid = document.getElementById("grid");
            grid.innerHTML = "";
            
            tiles.forEach((tile, index) => {
                const btn = document.createElement("button");
                btn.className = "tile" + (tile === 0 ? " empty" : "");
                btn.textContent = tile || "";
                btn.onclick = () => moveTile(index);
                grid.appendChild(btn);
            });
        }
        
        // Initialize
        initTiles();
        render();
    </script>
</body>
</html>
\'\'\'

def save_puzzle():
    """Save the puzzle game to an HTML file"""
    with open("puzzle.html", "w") as f:
        f.write(HTML_CODE)
    print("Saved puzzle.html - open in browser to play!")
    print("\\nGame teaches:")
    print("  - HTML structure & semantic elements")
    print("  - CSS Grid for 2D layouts")
    print("  - JavaScript arrays & state management")
    print("  - DOM manipulation & event handling")
    print("  - Game logic & win detection")

if __name__ == "__main__":
    save_puzzle()
''',
    },
    
    'greedy_algorithm': {
        'name': 'Greedy Algorithm Pattern',
        'description': 'When and how to apply greedy strategies',
        'level': SkillLevel.INTERMEDIATE,
        'teaches': ['algorithms', 'greedy', 'optimization'],
        'xp_reward': 35,
        'source': 'Algorithm Design',
        'code': '''"""
Greedy Algorithms
Make locally optimal choices hoping for global optimum.

Works when problem has:
1. Greedy choice property (local optimal → global optimal)
2. Optimal substructure
"""
from typing import List, Tuple


# ============================================================================
# CLASSIC: Activity Selection
# ============================================================================

def activity_selection(activities: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Select maximum non-overlapping activities.
    
    activities: List of (start, end) tuples
    
    Greedy strategy: Always pick the activity that finishes earliest.
    Why it works: Leaves maximum room for future activities.
    """
    # Sort by end time
    sorted_acts = sorted(activities, key=lambda x: x[1])
    
    result = [sorted_acts[0]]
    last_end = sorted_acts[0][1]
    
    for start, end in sorted_acts[1:]:
        if start >= last_end:  # No overlap
            result.append((start, end))
            last_end = end
    
    return result


# ============================================================================
# CLASSIC: Coin Change (Greedy when denominations allow)
# ============================================================================

def coin_change_greedy(amount: int, coins: List[int] = [25, 10, 5, 1]) -> List[int]:
    """
    Make change using minimum coins (greedy).
    
    WARNING: Only works for certain coin systems!
    US coins [25,10,5,1] work, but [1,3,4] for amount 6 would fail.
    (Greedy gives 4+1+1=3 coins, optimal is 3+3=2 coins)
    """
    result = []
    coins = sorted(coins, reverse=True)  # Largest first
    
    for coin in coins:
        while amount >= coin:
            result.append(coin)
            amount -= coin
    
    return result


# ============================================================================
# CLASSIC: Fractional Knapsack
# ============================================================================

def fractional_knapsack(
    weights: List[float], 
    values: List[float], 
    capacity: float
) -> Tuple[float, List[Tuple[int, float]]]:
    """
    Fractional knapsack - can take fractions of items.
    
    Greedy strategy: Take items with highest value/weight ratio first.
    
    Unlike 0/1 knapsack, greedy IS optimal here!
    """
    n = len(weights)
    # (index, value_per_weight)
    ratios = [(i, values[i] / weights[i]) for i in range(n)]
    ratios.sort(key=lambda x: x[1], reverse=True)
    
    total_value = 0
    taken = []  # (item_index, fraction_taken)
    
    for idx, ratio in ratios:
        if capacity <= 0:
            break
        
        if weights[idx] <= capacity:
            # Take whole item
            taken.append((idx, 1.0))
            total_value += values[idx]
            capacity -= weights[idx]
        else:
            # Take fraction
            fraction = capacity / weights[idx]
            taken.append((idx, fraction))
            total_value += values[idx] * fraction
            capacity = 0
    
    return total_value, taken


# ============================================================================
# CLASSIC: Huffman Coding (build optimal prefix code)
# ============================================================================

def huffman_codes(freq: dict) -> dict:
    """
    Build Huffman codes for characters based on frequency.
    
    Greedy: Always merge two lowest-frequency nodes.
    Result: Optimal prefix-free code for compression.
    """
    import heapq
    
    # Create heap of (frequency, id, node)
    heap = [(f, i, (char, None, None)) for i, (char, f) in enumerate(freq.items())]
    heapq.heapify(heap)
    counter = len(heap)
    
    while len(heap) > 1:
        f1, _, left = heapq.heappop(heap)
        f2, _, right = heapq.heappop(heap)
        
        # Merge nodes
        merged = (None, left, right)
        heapq.heappush(heap, (f1 + f2, counter, merged))
        counter += 1
    
    # Build codes by traversing tree
    codes = {}
    
    def traverse(node, code=""):
        char, left, right = node
        if char is not None:
            codes[char] = code or "0"
        else:
            if left:
                traverse(left, code + "0")
            if right:
                traverse(right, code + "1")
    
    if heap:
        traverse(heap[0][2])
    
    return codes


def demo():
    print("=== Activity Selection ===")
    activities = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10), (8, 11)]
    selected = activity_selection(activities)
    print(f"Activities: {activities}")
    print(f"Selected {len(selected)}: {selected}")
    
    print("\\n=== Coin Change ===")
    amount = 67
    coins = coin_change_greedy(amount)
    print(f"Change for {amount}¢: {coins}")
    print(f"Total coins: {len(coins)}")
    
    print("\\n=== Fractional Knapsack ===")
    weights = [10, 20, 30]
    values = [60, 100, 120]
    capacity = 50
    value, taken = fractional_knapsack(weights, values, capacity)
    print(f"Weights: {weights}, Values: {values}, Capacity: {capacity}")
    print(f"Max value: {value}")
    print(f"Items taken: {taken}")
    
    print("\\n=== Huffman Coding ===")
    freq = {'a': 45, 'b': 13, 'c': 12, 'd': 16, 'e': 9, 'f': 5}
    codes = huffman_codes(freq)
    print(f"Frequencies: {freq}")
    print("Huffman codes:")
    for char, code in sorted(codes.items()):
        print(f"  '{char}': {code}")


if __name__ == "__main__":
    demo()
''',
    },
}

# ============================================================================
# ORACLE RULES (from algorithm-oracle)
# ============================================================================

ORACLE_RULES = {
    'text_safety': {
        'profile': ['text', 'safety_critical'],
        'pattern': 'Rule-Based + Ensemble',
        'suggestion': 'Start with rule-based filters, add ML ensemble with human review',
        'why': 'Text safety requires interpretability and explicit rules for compliance'
    },
    'high_dim_few_samples': {
        'profile': ['high_dimensional', 'few_samples'],
        'pattern': 'Regularized Linear + Feature Selection',
        'suggestion': 'Use L1/L2 regularization, PCA, or tree-based feature importance',
        'why': 'High dimensions with few samples causes overfitting; reduce effective dimensionality'
    },
    'unsupervised_clustering': {
        'profile': ['unsupervised', 'clustering'],
        'pattern': 'K-Means → DBSCAN → Hierarchical',
        'suggestion': 'Start with K-Means for speed, try DBSCAN for arbitrary shapes',
        'why': 'K-Means is fast baseline; DBSCAN handles noise; hierarchical shows structure'
    },
    'need_interpretability': {
        'profile': ['need_interpretability'],
        'pattern': 'Decision Tree → Rules → SHAP',
        'suggestion': 'Use decision trees or extract rules; add SHAP for complex models',
        'why': 'Trees are inherently interpretable; SHAP explains black-box models'
    },
    'imbalanced_classes': {
        'profile': ['imbalanced'],
        'pattern': 'SMOTE + Class Weights + Threshold Tuning',
        'suggestion': 'Oversample minority, adjust class weights, tune decision threshold',
        'why': 'Standard metrics mislead on imbalanced data; balance or re-weight'
    },
    'streaming_data': {
        'profile': ['streaming', 'online_learning'],
        'pattern': 'Online Learning + Sliding Window',
        'suggestion': 'Use online algorithms (SGD), sliding windows for drift detection',
        'why': 'Batch models fail on streaming; need incremental updates'
    },
    'nonlinear_patterns': {
        'profile': ['nonlinear', 'complex_interactions'],
        'pattern': 'Gradient Boosting → Neural Network',
        'suggestion': 'XGBoost/LightGBM for tabular; neural nets for unstructured',
        'why': 'Linear models miss interactions; boosting captures nonlinearity efficiently'
    },
    'binary_classification': {
        'profile': ['binary_classification', 'tabular'],
        'pattern': 'Logistic → Random Forest → XGBoost',
        'suggestion': 'Start with logistic regression baseline, then ensemble methods',
        'why': 'Logistic is interpretable baseline; ensembles usually improve accuracy'
    },
    'regression': {
        'profile': ['regression', 'continuous_target'],
        'pattern': 'Linear → Ridge → Gradient Boosting',
        'suggestion': 'Linear regression first, add regularization, then try boosting',
        'why': 'Linear is interpretable; regularization prevents overfitting; boosting for nonlinear'
    },
    'multi_class': {
        'profile': ['multi_class', 'many_categories'],
        'pattern': 'Softmax → One-vs-Rest → Hierarchical',
        'suggestion': 'Softmax for few classes, OvR for many, hierarchical for structure',
        'why': 'Softmax is natural multi-class; OvR scales better; hierarchical uses domain'
    },
}


def query_oracle(profile_tags: List[str]) -> List[dict]:
    """
    Query the oracle for pattern suggestions based on problem profile.
    
    Args:
        profile_tags: List of problem characteristics like 
                      ['text', 'safety_critical'] or ['imbalanced', 'binary_classification']
    
    Returns:
        List of matching rules with pattern suggestions
    """
    matches = []
    for rule_id, rule in ORACLE_RULES.items():
        score = sum(1 for tag in rule['profile'] if tag in profile_tags)
        if score > 0:
            matches.append({
                'rule_id': rule_id,
                'score': score,
                'pattern': rule['pattern'],
                'suggestion': rule['suggestion'],
                'why': rule['why']
            })
    
    return sorted(matches, key=lambda x: x['score'], reverse=True)


# ============================================================================
# LEARNING SYSTEM
# ============================================================================

class LearningSystem:
    """
    Manages user progression through skill levels
    """
    
    # XP thresholds for each level
    LEVEL_THRESHOLDS = {
        SkillLevel.BEGINNER: 0,
        SkillLevel.INTERMEDIATE: 100,
        SkillLevel.ADVANCED: 300,
        SkillLevel.EXPERT: 600,
    }
    
    def __init__(self, profile_path: str = "learning_profile.json"):
        self.profile_path = Path(profile_path)
        self.profile = self._load_profile()
    
    def _load_profile(self) -> LearningProfile:
        """Load user profile from file"""
        if self.profile_path.exists():
            with open(self.profile_path, 'r') as f:
                return LearningProfile.from_dict(json.load(f))
        return LearningProfile()
    
    def save_profile(self):
        """Save user profile to file"""
        with open(self.profile_path, 'w') as f:
            json.dump(self.profile.to_dict(), f, indent=2)
    
    def add_xp(self, amount: int, reason: str = "") -> Dict[str, Any]:
        """Add XP and check for level up"""
        old_level = self.profile.level
        self.profile.xp += amount
        
        # Check for level up
        new_level = self._calculate_level()
        leveled_up = new_level != old_level
        
        if leveled_up:
            self.profile.level = new_level
        
        self.save_profile()
        
        return {
            'xp_gained': amount,
            'total_xp': self.profile.xp,
            'level': self.profile.level.value,
            'leveled_up': leveled_up,
            'reason': reason,
            'next_level_at': self._next_level_xp()
        }
    
    def _calculate_level(self) -> SkillLevel:
        """Calculate level based on XP"""
        for level in reversed(list(SkillLevel)):
            if self.profile.xp >= self.LEVEL_THRESHOLDS[level]:
                return level
        return SkillLevel.BEGINNER
    
    def _next_level_xp(self) -> Optional[int]:
        """XP needed for next level"""
        levels = list(SkillLevel)
        current_index = levels.index(self.profile.level)
        if current_index < len(levels) - 1:
            return self.LEVEL_THRESHOLDS[levels[current_index + 1]]
        return None
    
    def learn_concept(self, concept: str) -> Dict[str, Any]:
        """Mark a concept as learned"""
        was_new = concept not in self.profile.concepts_learned
        self.profile.concepts_learned.add(concept)
        self.save_profile()
        return {'concept': concept, 'was_new': was_new}
    
    def use_block(self, block_name: str) -> Dict[str, Any]:
        """Record block usage"""
        was_new = block_name not in self.profile.blocks_used
        self.profile.blocks_used.add(block_name)
        self.save_profile()
        return {'block': block_name, 'was_new': was_new}
    
    def complete_project(self) -> Dict[str, Any]:
        """Record project completion"""
        self.profile.projects_completed += 1
        result = self.add_xp(50, "Project completed!")
        return result
    
    def get_available_blocks(self) -> Dict[str, Any]:
        """Get blocks available at current level"""
        available = {}
        locked = {}
        
        current_level_index = list(SkillLevel).index(self.profile.level)
        
        for level in SkillLevel:
            level_index = list(SkillLevel).index(level)
            blocks = LEVEL_BLOCKS.get(level, {})
            
            for block_id, block_info in blocks.items():
                # Check if level is unlocked
                if level_index <= current_level_index:
                    # Check if required concepts are learned
                    required = block_info.get('requires_concepts', [])
                    has_prereqs = all(c in self.profile.concepts_learned for c in required)
                    
                    if has_prereqs:
                        available[block_id] = {
                            **block_info,
                            'level': level.value,
                            'unlocked': True
                        }
                    else:
                        locked[block_id] = {
                            **block_info,
                            'level': level.value,
                            'unlocked': False,
                            'missing_concepts': [c for c in required if c not in self.profile.concepts_learned]
                        }
                else:
                    locked[block_id] = {
                        **block_info,
                        'level': level.value,
                        'unlocked': False,
                        'requires_level': level.value
                    }
        
        return {
            'available': available,
            'locked': locked,
            'current_level': self.profile.level.value,
            'xp': self.profile.xp,
            'next_level_at': self._next_level_xp()
        }
    
    def get_available_projects(self) -> Dict[str, Any]:
        """Get code projects available at current level"""
        available = {}
        locked = {}
        
        current_level_index = list(SkillLevel).index(self.profile.level)
        
        for project_id, project_info in CODE_PATTERNS.items():
            project_level = project_info['level']
            level_index = list(SkillLevel).index(project_level)
            
            if level_index <= current_level_index:
                available[project_id] = {
                    'name': project_info['name'],
                    'description': project_info['description'],
                    'teaches': project_info['teaches'],
                    'xp_reward': project_info['xp_reward'],
                    'level': project_level.value
                }
            else:
                locked[project_id] = {
                    'name': project_info['name'],
                    'description': project_info['description'],
                    'requires_level': project_level.value
                }
        
        return {
            'available': available,
            'locked': locked
        }
    
    def get_project_code(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get code for a project if available"""
        if project_id not in CODE_PATTERNS:
            return None
        
        project = CODE_PATTERNS[project_id]
        current_level_index = list(SkillLevel).index(self.profile.level)
        project_level_index = list(SkillLevel).index(project['level'])
        
        if project_level_index > current_level_index:
            return {
                'available': False,
                'requires_level': project['level'].value
            }
        
        # Mark concepts as learned and add XP
        for concept in project['teaches']:
            self.learn_concept(concept)
        
        xp_result = self.add_xp(project['xp_reward'], f"Completed {project['name']}")
        
        return {
            'available': True,
            'name': project['name'],
            'code': project['code'],
            'teaches': project['teaches'],
            **xp_result
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        return {
            'level': self.profile.level.value,
            'xp': self.profile.xp,
            'next_level_at': self._next_level_xp(),
            'projects_completed': self.profile.projects_completed,
            'blocks_used': list(self.profile.blocks_used),
            'concepts_learned': list(self.profile.concepts_learned),
            'progress_percent': self._calculate_progress_percent()
        }
    
    def _calculate_progress_percent(self) -> int:
        """Calculate progress to next level as percentage"""
        current = self.LEVEL_THRESHOLDS[self.profile.level]
        next_lvl = self._next_level_xp()
        
        if next_lvl is None:
            return 100
        
        progress = self.profile.xp - current
        needed = next_lvl - current
        
        return min(100, int((progress / needed) * 100))


# ============================================================================
# API FUNCTIONS (for builder_server.py integration)
# ============================================================================

_learning_system: Optional[LearningSystem] = None

def get_learning_system() -> LearningSystem:
    """Get or create the learning system singleton"""
    global _learning_system
    if _learning_system is None:
        profile_path = Path(__file__).parent / "workspace" / "learning_profile.json"
        profile_path.parent.mkdir(exist_ok=True)
        _learning_system = LearningSystem(str(profile_path))
    return _learning_system


def get_learning_status() -> Dict[str, Any]:
    """API: Get learning status"""
    return get_learning_system().get_status()


def get_available_blocks() -> Dict[str, Any]:
    """API: Get blocks available at current level"""
    return get_learning_system().get_available_blocks()


def get_available_projects() -> Dict[str, Any]:
    """API: Get projects available at current level"""
    return get_learning_system().get_available_projects()


def get_project_code(project_id: str) -> Optional[Dict[str, Any]]:
    """API: Get code for a project"""
    return get_learning_system().get_project_code(project_id)


def record_block_use(block_name: str) -> Dict[str, Any]:
    """API: Record that a block was used"""
    ls = get_learning_system()
    result = ls.use_block(block_name)
    
    # Check if block grants XP for concepts
    for level_blocks in LEVEL_BLOCKS.values():
        if block_name in level_blocks:
            block_info = level_blocks[block_name]
            for concept in block_info.get('teaches', []):
                ls.learn_concept(concept)
            xp = block_info.get('xp_reward', 10)
            xp_result = ls.add_xp(xp, f"Used {block_name}")
            return {**result, **xp_result}
    
    return result


def complete_project() -> Dict[str, Any]:
    """API: Mark project as complete"""
    return get_learning_system().complete_project()


def get_oracle_advice(profile_tags: List[str]) -> Dict[str, Any]:
    """API: Get pattern advice from the oracle based on problem profile"""
    matches = query_oracle(profile_tags)
    return {
        'query': profile_tags,
        'matches': matches,
        'top_recommendation': matches[0] if matches else None
    }


def get_all_oracle_rules() -> Dict[str, Any]:
    """API: Get all available oracle rules"""
    return {
        'rules': ORACLE_RULES,
        'available_tags': sorted(set(
            tag for rule in ORACLE_RULES.values() for tag in rule['profile']
        ))
    }


# ============================================================================
# CLI DEMO
# ============================================================================

def demo():
    """Demonstrate the learning system"""
    print("=" * 60)
    print("LEARNING INTEGRATION DEMO")
    print("=" * 60)
    
    ls = LearningSystem("demo_profile.json")
    
    # Show initial status
    print("\n📊 Initial Status:")
    status = ls.get_status()
    print(f"  Level: {status['level']}")
    print(f"  XP: {status['xp']} / {status['next_level_at']}")
    
    # Show available blocks
    print("\n🧱 Available Blocks:")
    blocks = ls.get_available_blocks()
    for block_id, info in blocks['available'].items():
        print(f"  ✅ {info['name']} - {info['description']}")
    
    print("\n🔒 Locked Blocks:")
    for block_id, info in list(blocks['locked'].items())[:3]:
        reason = info.get('requires_level', info.get('missing_concepts', 'Unknown'))
        print(f"  🔒 {info['name']} - Requires: {reason}")
    
    # Show available projects
    print("\n📚 Available Projects:")
    projects = ls.get_available_projects()
    for proj_id, info in projects['available'].items():
        print(f"  📖 {info['name']} - {info['xp_reward']} XP")
    
    # Simulate learning
    print("\n🎮 Simulating learning...")
    
    # Get a project
    code_result = ls.get_project_code('guess_number')
    if code_result and code_result['available']:
        print(f"  Got code for: {code_result['name']}")
        print(f"  XP gained: {code_result['xp_gained']}")
        print(f"  Concepts learned: {code_result['teaches']}")
    
    # Use some blocks
    ls.use_block('storage_json')
    ls.use_block('crud_basic')
    
    # Complete a project
    result = ls.complete_project()
    print(f"  Project completed! XP: {result['total_xp']}")
    if result['leveled_up']:
        print(f"  🎉 LEVEL UP! Now: {result['level']}")
    
    # Show final status
    print("\n📊 Final Status:")
    status = ls.get_status()
    print(f"  Level: {status['level']}")
    print(f"  XP: {status['xp']} / {status['next_level_at']}")
    print(f"  Concepts: {status['concepts_learned']}")
    print(f"  Progress: {status['progress_percent']}%")
    
    # Cleanup demo file
    Path("demo_profile.json").unlink(missing_ok=True)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
