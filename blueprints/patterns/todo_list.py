"""
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
        
        print("\n📋 Your Tasks:")
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
        cmd = input("\n> ").strip().lower()
        
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
