"""
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
    print("\n📋 All tasks:")
    for task in get_all_tasks():
        status = "✓" if task['done'] else " "
        print(f"  [{status}] #{task['id']}: {task['title']}")
    
    # Update
    update_task(id1, done=True)
    
    # Read one
    task = get_task(id1)
    print(f"\n📌 Task #{id1}: {task}")
    
    # Delete
    delete_task(id2)

if __name__ == "__main__":
    main()
