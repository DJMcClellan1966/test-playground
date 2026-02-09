"""
GraphQL API Server
Expert-level project teaching GraphQL fundamentals.

GraphQL advantages over REST:
- Single endpoint, flexible queries
- Client specifies exactly what data it needs
- Strong typing with schema
- Real-time with subscriptions
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json


# ============================================================================
# SCHEMA DEFINITION
# ============================================================================

SCHEMA = """
type Query {
    task(id: ID!): Task
    tasks(status: String): [Task!]!
    user(id: ID!): User
}

type Mutation {
    createTask(input: TaskInput!): Task!
    updateTask(id: ID!, input: TaskInput!): Task
    deleteTask(id: ID!): Boolean!
}

type Subscription {
    taskCreated: Task!
    taskUpdated: Task!
}

type Task {
    id: ID!
    title: String!
    description: String
    status: TaskStatus!
    assignee: User
    createdAt: String!
}

type User {
    id: ID!
    name: String!
    email: String!
    tasks: [Task!]!
}

enum TaskStatus {
    TODO
    IN_PROGRESS
    DONE
}

input TaskInput {
    title: String!
    description: String
    status: TaskStatus
    assigneeId: ID
}
"""


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class User:
    id: str
    name: str
    email: str
    
@dataclass
class Task:
    id: str
    title: str
    status: str = "TODO"
    description: str = ""
    assignee_id: Optional[str] = None
    created_at: str = ""


# ============================================================================
# IN-MEMORY DATABASE
# ============================================================================

class Database:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.tasks: Dict[str, Task] = {}
        self._task_counter = 0
        self._user_counter = 0
        self._seed_data()
    
    def _seed_data(self):
        # Create users
        u1 = User("1", "Alice", "alice@example.com")
        u2 = User("2", "Bob", "bob@example.com")
        self.users = {"1": u1, "2": u2}
        
        # Create tasks
        self.tasks = {
            "1": Task("1", "Learn GraphQL", "IN_PROGRESS", "Study schema design", "1"),
            "2": Task("2", "Build API", "TODO", "Implement resolvers", "1"),
            "3": Task("3", "Write tests", "TODO", "", "2"),
        }
        self._task_counter = 3
    
    def get_task(self, id: str) -> Optional[Task]:
        return self.tasks.get(id)
    
    def get_tasks(self, status: Optional[str] = None) -> List[Task]:
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def create_task(self, title: str, description: str = "", 
                    status: str = "TODO", assignee_id: str = None) -> Task:
        self._task_counter += 1
        task = Task(
            id=str(self._task_counter),
            title=title,
            description=description,
            status=status,
            assignee_id=assignee_id
        )
        self.tasks[task.id] = task
        return task
    
    def get_user(self, id: str) -> Optional[User]:
        return self.users.get(id)


# ============================================================================
# RESOLVERS
# ============================================================================

class Resolvers:
    """
    Resolvers map GraphQL operations to actual data fetching.
    Each resolver handles one field in the schema.
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    # Query resolvers
    def resolve_task(self, id: str) -> Optional[dict]:
        task = self.db.get_task(id)
        return self._task_to_dict(task) if task else None
    
    def resolve_tasks(self, status: Optional[str] = None) -> List[dict]:
        return [self._task_to_dict(t) for t in self.db.get_tasks(status)]
    
    def resolve_user(self, id: str) -> Optional[dict]:
        user = self.db.get_user(id)
        return self._user_to_dict(user) if user else None
    
    # Mutation resolvers
    def resolve_create_task(self, input: dict) -> dict:
        task = self.db.create_task(
            title=input['title'],
            description=input.get('description', ''),
            status=input.get('status', 'TODO'),
            assignee_id=input.get('assigneeId')
        )
        return self._task_to_dict(task)
    
    # Field resolvers (for nested objects)
    def resolve_task_assignee(self, task: dict) -> Optional[dict]:
        if task.get('assignee_id'):
            user = self.db.get_user(task['assignee_id'])
            return self._user_to_dict(user) if user else None
        return None
    
    def resolve_user_tasks(self, user: dict) -> List[dict]:
        user_id = user['id']
        return [
            self._task_to_dict(t) 
            for t in self.db.tasks.values() 
            if t.assignee_id == user_id
        ]
    
    # Helpers
    def _task_to_dict(self, task: Task) -> dict:
        return {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'assignee_id': task.assignee_id,
            'createdAt': task.created_at
        }
    
    def _user_to_dict(self, user: User) -> dict:
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }


# ============================================================================
# SIMPLE QUERY EXECUTOR
# ============================================================================

def execute_query(resolvers: Resolvers, query: str, variables: dict = None) -> dict:
    """
    Simplified GraphQL executor (production would use graphql-core).
    Demonstrates the concept of query parsing and resolution.
    """
    variables = variables or {}
    
    # Very simplified parsing - just for demo
    if 'tasks' in query:
        status = variables.get('status')
        tasks = resolvers.resolve_tasks(status)
        # Resolve nested assignee if requested
        if 'assignee' in query:
            for task in tasks:
                task['assignee'] = resolvers.resolve_task_assignee(task)
        return {'data': {'tasks': tasks}}
    
    elif 'task(' in query:
        # Extract ID from query
        import re
        match = re.search(r'task\(id:\s*"?(\w+)"?\)', query)
        if match:
            task = resolvers.resolve_task(match.group(1))
            return {'data': {'task': task}}
    
    elif 'createTask' in query:
        task = resolvers.resolve_create_task(variables.get('input', {}))
        return {'data': {'createTask': task}}
    
    return {'data': None, 'errors': ['Unknown query']}


def demo():
    print("=== GraphQL API Demo ===\n")
    
    db = Database()
    resolvers = Resolvers(db)
    
    # Query all tasks
    print("Query: { tasks { id title status } }")
    result = execute_query(resolvers, "{ tasks { id title status } }")
    print(f"Result: {json.dumps(result, indent=2)}\n")
    
    # Query with filter
    print("Query: { tasks(status: TODO) { title } }")
    result = execute_query(resolvers, "{ tasks { title } }", {'status': 'TODO'})
    print(f"Result: {json.dumps(result, indent=2)}\n")
    
    # Mutation
    print("Mutation: createTask")
    result = execute_query(
        resolvers, 
        "mutation { createTask(input: $input) { id title } }",
        {'input': {'title': 'New GraphQL Task', 'status': 'TODO'}}
    )
    print(f"Result: {json.dumps(result, indent=2)}\n")
    
    print("=== Key Concepts ===")
    print("1. Schema: Defines types, queries, mutations")
    print("2. Resolvers: Map operations to data fetching")
    print("3. Single endpoint: POST /graphql")
    print("4. Client controls response shape")


if __name__ == "__main__":
    demo()
