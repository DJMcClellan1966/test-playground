"""
The 50 Optimal Training Examples
================================

Mathematically derived minimal dataset to cover 92% of all app types.
Based on analysis from optimal_data_calculator.py.

This is the "training data" for AI-free template generation.
Each example carries ~5 bits of decision information.
Total: ~241 bits = enough to generate any app.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum


class Category(Enum):
    DATA_APP = 'data_app'
    GAME = 'game'
    API = 'api'
    CLI = 'cli'
    ML = 'ml'
    AUTOMATION = 'automation'


class Complexity(Enum):
    TRIVIAL = 'trivial'      # Single entity, no auth, no relationships
    SIMPLE = 'simple'        # 1-2 entities, basic features
    MODERATE = 'moderate'    # Auth, relationships, 3+ features
    COMPLEX = 'complex'      # Multi-service, advanced patterns


@dataclass
class TrainingExample:
    """A single optimal training example."""
    id: str
    description: str
    category: Category
    complexity: Complexity
    
    # Entity types this example demonstrates
    entities: List[str] = field(default_factory=list)
    
    # Features this example demonstrates
    features: Set[str] = field(default_factory=set)
    
    # Relationships
    relationships: List[str] = field(default_factory=list)
    
    # UI type
    ui_type: str = 'web'
    
    # Domain-specific fields to generate
    domain_fields: Dict[str, str] = field(default_factory=dict)
    
    # Code generation hints
    framework: str = 'flask'
    needs_database: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'category': self.category.value,
            'complexity': self.complexity.value,
            'entities': self.entities,
            'features': list(self.features),
            'relationships': self.relationships,
            'ui_type': self.ui_type,
            'domain_fields': self.domain_fields,
            'framework': self.framework,
            'needs_database': self.needs_database,
        }


# =============================================================================
# THE 50 OPTIMAL TRAINING EXAMPLES
# =============================================================================

OPTIMAL_TRAINING_SET: List[TrainingExample] = [
    
    # =========================================================================
    # SECTION 1: CORE ARCHETYPES (30 examples)
    # =========================================================================
    
    # --- Simple Collection (Trivial Data Apps) ---
    TrainingExample(
        id='simple_todo',
        description='a todo list',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['task'],
        features=set(),
        domain_fields={'title': 'str', 'completed': 'bool'},
        framework='flask',
    ),
    TrainingExample(
        id='simple_bookmark',
        description='a bookmark manager',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['bookmark'],
        features=set(),
        domain_fields={'url': 'str', 'title': 'str'},
        framework='flask',
    ),
    TrainingExample(
        id='simple_notes',
        description='a note taking app',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['note'],
        features=set(),
        domain_fields={'title': 'str', 'content': 'text'},
        framework='flask',
    ),
    TrainingExample(
        id='simple_shopping',
        description='a shopping list',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['item'],
        features=set(),
        domain_fields={'name': 'str', 'quantity': 'int', 'bought': 'bool'},
        framework='flask',
    ),
    
    # --- Collection + Features (Simple Data Apps) ---
    TrainingExample(
        id='recipe_searchable',
        description='a recipe app with search and tags',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['recipe', 'tag'],
        features={'search', 'tags'},
        relationships=['has_many:tags'],
        domain_fields={
            'title': 'str', 'ingredients': 'text', 'instructions': 'text',
            'prep_time': 'int', 'cook_time': 'int', 'servings': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='bookmark_categorized',
        description='a bookmark manager with categories',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['bookmark', 'category'],
        features={'tags'},
        relationships=['belongs_to:category'],
        domain_fields={'url': 'str', 'title': 'str', 'description': 'str'},
        framework='flask',
    ),
    TrainingExample(
        id='movie_collection',
        description='a movie collection with tags and ratings',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['movie', 'tag'],
        features={'tags', 'ratings'},
        relationships=['has_many:tags'],
        domain_fields={
            'title': 'str', 'year': 'int', 'director': 'str',
            'rating': 'float', 'watched': 'bool',
        },
        framework='flask',
    ),
    
    # --- Authenticated Apps (Moderate Data Apps) ---
    TrainingExample(
        id='recipe_auth',
        description='a recipe app with user accounts',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'recipe'],
        features={'auth', 'search'},
        relationships=['belongs_to:user'],
        domain_fields={
            'title': 'str', 'ingredients': 'text', 'instructions': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='task_auth',
        description='a personal task manager with login',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'task'],
        features={'auth'},
        relationships=['belongs_to:user'],
        domain_fields={'title': 'str', 'due_date': 'datetime', 'priority': 'int'},
        framework='flask',
    ),
    TrainingExample(
        id='blog_auth',
        description='a blog platform with authors',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'post'],
        features={'auth', 'search'},
        relationships=['belongs_to:user'],
        domain_fields={'title': 'str', 'body': 'text', 'published_at': 'datetime'},
        framework='flask',
    ),
    
    # --- Social/Community Apps (Complex Data Apps) ---
    TrainingExample(
        id='recipe_social',
        description='a recipe sharing platform with ratings and comments',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['user', 'recipe', 'comment', 'rating'],
        features={'auth', 'ratings', 'comments', 'share'},
        relationships=['belongs_to:user', 'has_many:comments', 'has_many:ratings'],
        domain_fields={
            'title': 'str', 'ingredients': 'text', 'instructions': 'text',
            'avg_rating': 'float', 'share_count': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='community_forum',
        description='a community forum with threads and replies',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['user', 'thread', 'reply'],
        features={'auth', 'comments'},
        relationships=['belongs_to:user', 'has_many:replies'],
        domain_fields={'title': 'str', 'body': 'text', 'pinned': 'bool'},
        framework='flask',
    ),
    TrainingExample(
        id='fitness_social',
        description='a social network for fitness enthusiasts',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['user', 'workout', 'follow', 'comment'],
        features={'auth', 'share', 'comments', 'stats'},
        relationships=['many_to_many:followers', 'has_many:workouts'],
        domain_fields={'bio': 'str', 'workout_count': 'int', 'follower_count': 'int'},
        framework='flask',
    ),
    
    # --- Domain-Specific: Fitness ---
    TrainingExample(
        id='workout_tracker',
        description='a workout tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['workout', 'exercise'],
        features={'history'},
        relationships=['has_many:exercises'],
        domain_fields={
            'exercise_type': 'str', 'sets': 'int', 'reps': 'int',
            'weight': 'float', 'duration': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='exercise_log',
        description='an exercise log with statistics',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['exercise_log'],
        features={'history', 'stats'},
        domain_fields={
            'exercise_name': 'str', 'sets': 'int', 'reps': 'int',
            'weight': 'float', 'date': 'date',
        },
        framework='flask',
    ),
    
    # --- Domain-Specific: Finance ---
    TrainingExample(
        id='budget_tracker',
        description='a budget tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['budget', 'expense'],
        features={'stats'},
        relationships=['has_many:expenses'],
        domain_fields={
            'category': 'str', 'limit': 'float', 'spent': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='expense_manager',
        description='an expense manager with categories',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['expense', 'category'],
        features={'stats', 'export'},
        relationships=['belongs_to:category'],
        domain_fields={
            'amount': 'float', 'description': 'str', 'date': 'date',
            'recurring': 'bool',
        },
        framework='flask',
    ),
    
    # --- Games: Simple ---
    TrainingExample(
        id='snake_game',
        description='a snake game',
        category=Category.GAME,
        complexity=Complexity.TRIVIAL,
        entities=['game_state'],
        features=set(),
        ui_type='canvas',
        domain_fields={'score': 'int', 'high_score': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='pong_game',
        description='a pong game',
        category=Category.GAME,
        complexity=Complexity.TRIVIAL,
        entities=['game_state'],
        features=set(),
        ui_type='canvas',
        domain_fields={'player1_score': 'int', 'player2_score': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='reaction_test',
        description='a reaction time test',
        category=Category.GAME,
        complexity=Complexity.TRIVIAL,
        entities=['score'],
        features={'stats'},
        ui_type='canvas',
        domain_fields={'reaction_time_ms': 'int', 'attempts': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    
    # --- Games: Puzzle ---
    TrainingExample(
        id='wordle_clone',
        description='a wordle clone',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game', 'guess'],
        features={'stats'},
        ui_type='canvas',
        domain_fields={'target_word': 'str', 'guesses': 'list', 'solved': 'bool'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='sudoku_game',
        description='a sudoku puzzle game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['puzzle', 'cell'],
        features={'stats'},
        ui_type='canvas',
        domain_fields={'grid': 'list', 'difficulty': 'str', 'solved': 'bool'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='tictactoe',
        description='a tic tac toe game',
        category=Category.GAME,
        complexity=Complexity.TRIVIAL,
        entities=['game'],
        features=set(),
        ui_type='canvas',
        domain_fields={'board': 'list', 'current_player': 'str', 'winner': 'str'},
        framework='html_canvas',
        needs_database=False,
    ),
    
    # --- Games: With Scores/Leaderboard ---
    TrainingExample(
        id='tetris_scores',
        description='a tetris game with high scores',
        category=Category.GAME,
        complexity=Complexity.MODERATE,
        entities=['game', 'score', 'user'],
        features={'auth', 'stats'},
        ui_type='canvas',
        domain_fields={'score': 'int', 'level': 'int', 'lines_cleared': 'int'},
        framework='flask',
    ),
    TrainingExample(
        id='quiz_multiplayer',
        description='a multiplayer quiz game',
        category=Category.GAME,
        complexity=Complexity.MODERATE,
        entities=['quiz', 'question', 'user', 'score'],
        features={'auth', 'stats'},
        domain_fields={'question_text': 'str', 'options': 'list', 'correct': 'int'},
        framework='flask',
    ),
    
    # --- APIs: Simple ---
    TrainingExample(
        id='users_api',
        description='a REST API for users',
        category=Category.API,
        complexity=Complexity.TRIVIAL,
        entities=['user'],
        features=set(),
        ui_type='api_only',
        domain_fields={'username': 'str', 'email': 'str'},
        framework='fastapi',
    ),
    TrainingExample(
        id='products_api',
        description='an API for products',
        category=Category.API,
        complexity=Complexity.TRIVIAL,
        entities=['product'],
        features=set(),
        ui_type='api_only',
        domain_fields={'name': 'str', 'price': 'float', 'sku': 'str'},
        framework='fastapi',
    ),
    
    # --- APIs: Authenticated ---
    TrainingExample(
        id='jwt_api',
        description='an API with JWT authentication',
        category=Category.API,
        complexity=Complexity.MODERATE,
        entities=['user', 'token'],
        features={'auth'},
        ui_type='api_only',
        domain_fields={'username': 'str', 'email': 'str', 'hashed_password': 'str'},
        framework='fastapi',
    ),
    TrainingExample(
        id='secure_rest',
        description='a secure REST service for user data',
        category=Category.API,
        complexity=Complexity.MODERATE,
        entities=['user', 'session'],
        features={'auth', 'search'},
        ui_type='api_only',
        domain_fields={'username': 'str', 'role': 'str'},
        framework='fastapi',
    ),
    
    # --- CLI Tools ---
    TrainingExample(
        id='file_converter',
        description='a file converter CLI tool',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='password_gen',
        description='a password generator',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='cli_todo',
        description='a CLI task manager',
        category=Category.CLI,
        complexity=Complexity.SIMPLE,
        entities=['task'],
        features={'export'},
        ui_type='cli',
        domain_fields={'title': 'str', 'done': 'bool'},
        framework='click',
    ),
    
    # --- ML Pipelines ---
    TrainingExample(
        id='sentiment_classifier',
        description='a sentiment classifier',
        category=Category.ML,
        complexity=Complexity.SIMPLE,
        entities=['model', 'prediction'],
        features={'stats'},
        ui_type='api_only',
        domain_fields={'text': 'str', 'sentiment': 'str', 'confidence': 'float'},
        framework='fastapi',
    ),
    TrainingExample(
        id='image_classifier',
        description='an image classification model',
        category=Category.ML,
        complexity=Complexity.SIMPLE,
        entities=['model', 'image', 'prediction'],
        features={'stats'},
        ui_type='api_only',
        domain_fields={'image_url': 'str', 'predicted_class': 'str', 'confidence': 'float'},
        framework='fastapi',
    ),
    
    # --- Automation ---
    TrainingExample(
        id='web_scraper',
        description='a web scraper',
        category=Category.AUTOMATION,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features={'notifications'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='file_backup',
        description='a file backup automation script',
        category=Category.AUTOMATION,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features={'notifications'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    
    # =========================================================================
    # SECTION 2: FEATURE COMBINATIONS (7 examples)
    # =========================================================================
    
    TrainingExample(
        id='feature_search_tags',
        description='a recipe app with search and tags',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['recipe', 'tag'],
        features={'search', 'tags'},
        relationships=['has_many:tags'],
        domain_fields={'title': 'str', 'ingredients': 'text'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_auth_export',
        description='a personal finance tracker with export',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'expense'],
        features={'auth', 'export'},
        relationships=['belongs_to:user'],
        domain_fields={'amount': 'float', 'category': 'str'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_ratings_comments',
        description='a product review app',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['product', 'review', 'user'],
        features={'ratings', 'comments'},
        relationships=['has_many:reviews'],
        domain_fields={'product_name': 'str', 'rating': 'int', 'comment': 'text'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_history_stats',
        description='a workout tracker with statistics',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['workout'],
        features={'history', 'stats'},
        domain_fields={'exercise': 'str', 'reps': 'int', 'weight': 'float'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_share_notify',
        description='a social todo list with notifications',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'task'],
        features={'share', 'notifications', 'auth'},
        relationships=['belongs_to:user'],
        domain_fields={'title': 'str', 'shared_with': 'list'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_auth_search_tags',
        description='a bookmarking app with accounts and tags',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['user', 'bookmark', 'tag'],
        features={'auth', 'search', 'tags'},
        relationships=['belongs_to:user', 'has_many:tags'],
        domain_fields={'url': 'str', 'title': 'str'},
        framework='flask',
    ),
    TrainingExample(
        id='feature_full_social',
        description='a community recipe site with all features',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['user', 'recipe', 'comment', 'rating'],
        features={'auth', 'ratings', 'comments', 'share', 'search', 'tags'},
        relationships=['belongs_to:user', 'has_many:comments', 'has_many:tags'],
        domain_fields={'title': 'str', 'ingredients': 'text', 'avg_rating': 'float'},
        framework='flask',
    ),
    
    # =========================================================================
    # SECTION 3: COMPLEXITY EDGES (4 examples)
    # =========================================================================
    
    TrainingExample(
        id='edge_trivial_counter',
        description='a simple counter app',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['counter'],
        features=set(),
        domain_fields={'count': 'int'},
        framework='flask',
    ),
    TrainingExample(
        id='edge_trivial_dice',
        description='a dice roller',
        category=Category.GAME,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='canvas',
        domain_fields={},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='edge_complex_saas',
        description='a multi-tenant SaaS platform',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['tenant', 'user', 'subscription', 'invoice'],
        features={'auth', 'export', 'notifications', 'stats'},
        relationships=['belongs_to:tenant', 'has_many:subscriptions'],
        domain_fields={
            'tenant_name': 'str', 'plan': 'str', 'seats': 'int',
            'billing_email': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='edge_complex_ecommerce',
        description='an e-commerce marketplace',
        category=Category.DATA_APP,
        complexity=Complexity.COMPLEX,
        entities=['user', 'product', 'order', 'cart', 'review', 'seller'],
        features={'auth', 'search', 'ratings', 'export', 'notifications'},
        relationships=['belongs_to:seller', 'has_many:products', 'has_many:orders'],
        domain_fields={
            'product_name': 'str', 'price': 'float', 'inventory': 'int',
            'order_total': 'float', 'order_status': 'str',
        },
        framework='flask',
    ),
    
    # =========================================================================
    # SECTION 4: ENTITY COVERAGE (8 examples)
    # =========================================================================
    
    TrainingExample(
        id='entity_recipe',
        description='a cooking recipe collection',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['recipe'],
        features=set(),
        domain_fields={
            'title': 'str', 'ingredients': 'text', 'instructions': 'text',
            'prep_time': 'int', 'cook_time': 'int', 'servings': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_task',
        description='a task management system',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['task', 'project'],
        features=set(),
        domain_fields={
            'title': 'str', 'description': 'text', 'due_date': 'datetime',
            'priority': 'int', 'status': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_product',
        description='an inventory management app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['product', 'category'],
        features={'search'},
        domain_fields={
            'name': 'str', 'sku': 'str', 'price': 'float',
            'quantity': 'int', 'reorder_level': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_post',
        description='a blog publishing platform',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['post', 'author'],
        features={'search'},
        domain_fields={
            'title': 'str', 'body': 'text', 'slug': 'str',
            'published_at': 'datetime', 'draft': 'bool',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_event',
        description='a calendar scheduling app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['event', 'calendar'],
        features={'notifications'},
        domain_fields={
            'title': 'str', 'start_time': 'datetime', 'end_time': 'datetime',
            'location': 'str', 'recurring': 'bool',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_workout',
        description='a gym workout planner',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['workout', 'exercise'],
        features={'history'},
        domain_fields={
            'exercise_name': 'str', 'sets': 'int', 'reps': 'int',
            'weight': 'float', 'rest_seconds': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_expense',
        description='a personal budget tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['expense', 'budget'],
        features={'stats'},
        domain_fields={
            'amount': 'float', 'category': 'str', 'date': 'date',
            'description': 'str', 'recurring': 'bool',
        },
        framework='flask',
    ),
    TrainingExample(
        id='entity_media',
        description='a photo gallery manager',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['photo', 'album'],
        features={'tags', 'search'},
        domain_fields={
            'filename': 'str', 'url': 'str', 'thumbnail_url': 'str',
            'width': 'int', 'height': 'int', 'taken_at': 'datetime',
        },
        framework='flask',
    ),
    
    # =========================================================================
    # SECTION 5: EXPANDED DOMAIN COVERAGE (100+ new examples)
    # =========================================================================
    
    # --- Healthcare / Medical ---
    TrainingExample(
        id='medical_appointment',
        description='a medical appointment scheduler',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['patient', 'doctor', 'appointment'],
        features={'auth', 'notifications'},
        relationships=['belongs_to:patient', 'belongs_to:doctor'],
        domain_fields={
            'patient_name': 'str', 'doctor_name': 'str', 
            'appointment_time': 'datetime', 'reason': 'text', 'status': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='medication_tracker',
        description='a medication reminder app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['medication', 'dose'],
        features={'notifications'},
        domain_fields={
            'medication_name': 'str', 'dosage': 'str', 
            'frequency': 'str', 'time_to_take': 'time', 'taken': 'bool',
        },
        framework='flask',
    ),
    TrainingExample(
        id='health_vitals',
        description='a health vitals tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['vital_reading'],
        features={'stats', 'history'},
        domain_fields={
            'blood_pressure': 'str', 'heart_rate': 'int', 
            'temperature': 'float', 'weight': 'float', 'recorded_at': 'datetime',
        },
        framework='flask',
    ),
    
    # --- Education / Learning ---
    TrainingExample(
        id='course_catalog',
        description='an online course catalog',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['course', 'instructor', 'enrollment'],
        features={'search', 'auth'},
        domain_fields={
            'course_name': 'str', 'description': 'text', 
            'instructor': 'str', 'price': 'float', 'duration_hours': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='grade_tracker',
        description='a student grade tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['student', 'grade', 'assignment'],
        features={'stats'},
        domain_fields={
            'student_name': 'str', 'assignment_name': 'str', 
            'score': 'float', 'max_score': 'float', 'submitted_at': 'datetime',
        },
        framework='flask',
    ),
    TrainingExample(
        id='vocabulary_builder',
        description='a vocabulary learning app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['word', 'definition'],
        features={'search'},
        domain_fields={
            'word': 'str', 'definition': 'text', 
            'example_sentence': 'text', 'difficulty': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='flashcard_deck',
        description='a flashcard study system',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['deck', 'flashcard'],
        features={'tags'},
        domain_fields={
            'front': 'text', 'back': 'text', 
            'last_reviewed': 'datetime', 'ease_factor': 'float',
        },
        framework='flask',
    ),
    
    # --- Travel / Transportation ---
    TrainingExample(
        id='trip_planner',
        description='a trip planning app',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['trip', 'destination', 'itinerary'],
        features={'search', 'export'},
        domain_fields={
            'destination': 'str', 'start_date': 'date', 'end_date': 'date',
            'budget': 'float', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='packing_list',
        description='a travel packing list',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['item'],
        features=set(),
        domain_fields={
            'item_name': 'str', 'quantity': 'int', 'packed': 'bool', 'category': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='fuel_log',
        description='a car fuel consumption tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['fuel_entry'],
        features={'stats'},
        domain_fields={
            'date': 'date', 'odometer': 'int', 'gallons': 'float',
            'price_per_gallon': 'float', 'total_cost': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='mileage_tracker',
        description='a vehicle mileage log',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['trip_log'],
        features={'export', 'stats'},
        domain_fields={
            'start_odometer': 'int', 'end_odometer': 'int', 
            'purpose': 'str', 'date': 'date', 'reimbursable': 'bool',
        },
        framework='flask',
    ),
    
    # --- Real Estate / Property ---
    TrainingExample(
        id='property_listing',
        description='a real estate listing app',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['property', 'agent'],
        features={'search', 'tags'},
        domain_fields={
            'address': 'str', 'price': 'float', 'bedrooms': 'int',
            'bathrooms': 'float', 'square_feet': 'int', 'listing_type': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='rent_tracker',
        description='a rent payment tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['rent_payment', 'tenant'],
        features={'notifications'},
        domain_fields={
            'tenant_name': 'str', 'amount': 'float', 'due_date': 'date',
            'paid_date': 'date', 'status': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='maintenance_log',
        description='a property maintenance log',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['maintenance_request'],
        features={'history'},
        domain_fields={
            'issue': 'text', 'priority': 'str', 'reported_date': 'date',
            'resolved_date': 'date', 'cost': 'float',
        },
        framework='flask',
    ),
    
    # --- Food & Drink ---
    TrainingExample(
        id='wine_cellar',
        description='a wine collection tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['wine'],
        features={'tags', 'ratings'},
        domain_fields={
            'name': 'str', 'vintage': 'int', 'region': 'str',
            'varietal': 'str', 'rating': 'float', 'quantity': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='coffee_log',
        description='a coffee tasting journal',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['coffee'],
        features={'ratings', 'tags'},
        domain_fields={
            'roaster': 'str', 'origin': 'str', 'roast_level': 'str',
            'tasting_notes': 'text', 'rating': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='restaurant_tracker',
        description='a restaurant visit tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['restaurant', 'visit'],
        features={'ratings', 'tags'},
        domain_fields={
            'name': 'str', 'cuisine': 'str', 'location': 'str',
            'rating': 'float', 'visited_at': 'date',
        },
        framework='flask',
    ),
    TrainingExample(
        id='beer_tracker',
        description='a craft beer collection app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['beer'],
        features={'ratings', 'search'},
        domain_fields={
            'name': 'str', 'brewery': 'str', 'style': 'str',
            'abv': 'float', 'rating': 'float', 'notes': 'text',
        },
        framework='flask',
    ),
    
    # --- Hobbies / Collections ---
    TrainingExample(
        id='book_library',
        description='a personal book library',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['book'],
        features={'tags', 'search'},
        domain_fields={
            'title': 'str', 'author': 'str', 'isbn': 'str',
            'genre': 'str', 'read': 'bool', 'rating': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='vinyl_collection',
        description='a vinyl record collection',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['record'],
        features={'tags', 'search'},
        domain_fields={
            'artist': 'str', 'album': 'str', 'year': 'int',
            'genre': 'str', 'condition': 'str', 'value': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='comic_collection',
        description='a comic book collection manager',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['comic'],
        features={'tags', 'search'},
        domain_fields={
            'title': 'str', 'issue': 'int', 'publisher': 'str',
            'condition': 'str', 'value': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='stamp_collection',
        description='a stamp collection catalog',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['stamp'],
        features={'tags', 'search'},
        domain_fields={
            'country': 'str', 'year': 'int', 'denomination': 'str',
            'condition': 'str', 'value': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='plant_tracker',
        description='a plant care tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['plant', 'care_log'],
        features={'notifications'},
        domain_fields={
            'name': 'str', 'species': 'str', 'location': 'str',
            'last_watered': 'date', 'water_frequency': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='pet_care',
        description='a pet care management app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['pet', 'care_event'],
        features={'notifications', 'history'},
        domain_fields={
            'name': 'str', 'species': 'str', 'breed': 'str',
            'birth_date': 'date', 'weight': 'float',
        },
        framework='flask',
    ),
    
    # --- Sports / Fitness ---
    TrainingExample(
        id='running_log',
        description='a running log',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['run'],
        features={'stats', 'history'},
        domain_fields={
            'distance': 'float', 'duration': 'int', 'pace': 'float',
            'date': 'date', 'route': 'str', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='weight_tracker',
        description='a weight tracking app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['weight_entry'],
        features={'stats', 'history'},
        domain_fields={
            'weight': 'float', 'date': 'date', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='cycling_log',
        description='a cycling activity tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['ride'],
        features={'stats', 'history'},
        domain_fields={
            'distance': 'float', 'duration': 'int', 'elevation': 'int',
            'date': 'date', 'route_name': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='golf_scorecard',
        description='a golf scorecard tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['round', 'hole_score'],
        features={'stats'},
        domain_fields={
            'course_name': 'str', 'date': 'date', 'total_score': 'int',
            'handicap': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='swim_log',
        description='a swimming workout log',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['swim'],
        features={'stats', 'history'},
        domain_fields={
            'distance': 'int', 'laps': 'int', 'duration': 'int',
            'stroke': 'str', 'date': 'date',
        },
        framework='flask',
    ),
    
    # --- Business / Professional ---
    TrainingExample(
        id='client_crm',
        description='a simple CRM for clients',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['client', 'contact', 'note'],
        features={'auth', 'search'},
        domain_fields={
            'company_name': 'str', 'contact_name': 'str', 'email': 'str',
            'phone': 'str', 'status': 'str', 'value': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='invoice_tracker',
        description='an invoice tracking system',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['invoice', 'client', 'line_item'],
        features={'export', 'stats'},
        domain_fields={
            'invoice_number': 'str', 'client_name': 'str', 'amount': 'float',
            'due_date': 'date', 'status': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='timesheet',
        description='a timesheet tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['time_entry', 'project'],
        features={'stats', 'export'},
        domain_fields={
            'project': 'str', 'description': 'text', 'hours': 'float',
            'date': 'date', 'billable': 'bool',
        },
        framework='flask',
    ),
    TrainingExample(
        id='lead_tracker',
        description='a sales lead tracker',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['lead', 'activity'],
        features={'auth', 'stats'},
        domain_fields={
            'name': 'str', 'email': 'str', 'company': 'str',
            'status': 'str', 'value': 'float', 'source': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='meeting_notes',
        description='a meeting notes app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['meeting', 'action_item'],
        features={'search', 'tags'},
        domain_fields={
            'title': 'str', 'date': 'datetime', 'attendees': 'text',
            'notes': 'text', 'action_items': 'text',
        },
        framework='flask',
    ),
    
    # --- Games: Additional ---
    TrainingExample(
        id='chess_game',
        description='a chess game',
        category=Category.GAME,
        complexity=Complexity.MODERATE,
        entities=['game', 'move'],
        features=set(),
        ui_type='canvas',
        domain_fields={'board': 'list', 'current_player': 'str', 'move_history': 'list'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='checkers_game',
        description='a checkers game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game'],
        features=set(),
        ui_type='canvas',
        domain_fields={'board': 'list', 'current_player': 'str'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='card_game',
        description='a card matching game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game', 'card'],
        features=set(),
        ui_type='canvas',
        domain_fields={'cards': 'list', 'flipped': 'list', 'matched': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='maze_game',
        description='a maze puzzle game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['maze', 'player'],
        features=set(),
        ui_type='canvas',
        domain_fields={'maze': 'list', 'player_position': 'list', 'moves': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='crossword',
        description='a crossword puzzle',
        category=Category.GAME,
        complexity=Complexity.MODERATE,
        entities=['puzzle', 'clue'],
        features=set(),
        ui_type='canvas',
        domain_fields={'grid': 'list', 'clues_across': 'list', 'clues_down': 'list'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='word_search',
        description='a word search puzzle',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['puzzle'],
        features=set(),
        ui_type='canvas',
        domain_fields={'grid': 'list', 'words': 'list', 'found': 'list'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='simon_game',
        description='a simon says memory game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game'],
        features=set(),
        ui_type='canvas',
        domain_fields={'sequence': 'list', 'level': 'int', 'score': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='brick_breaker',
        description='a brick breaker game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game'],
        features=set(),
        ui_type='canvas',
        domain_fields={'bricks': 'list', 'score': 'int', 'lives': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='space_invaders',
        description='a space invaders game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game', 'enemy'],
        features=set(),
        ui_type='canvas',
        domain_fields={'enemies': 'list', 'score': 'int', 'level': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    TrainingExample(
        id='asteroids_game',
        description='an asteroids game',
        category=Category.GAME,
        complexity=Complexity.SIMPLE,
        entities=['game'],
        features=set(),
        ui_type='canvas',
        domain_fields={'asteroids': 'list', 'score': 'int', 'lives': 'int'},
        framework='html_canvas',
        needs_database=False,
    ),
    
    # --- Tools / Utilities ---
    TrainingExample(
        id='color_picker',
        description='a color picker tool',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='json_formatter',
        description='a JSON formatter tool',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='base64_encoder',
        description='a base64 encoder decoder',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='hash_generator',
        description='a hash generator tool',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='lorem_ipsum',
        description='a lorem ipsum generator',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='uuid_generator',
        description='a UUID generator',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='regex_tester',
        description='a regex tester tool',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    TrainingExample(
        id='diff_checker',
        description='a text diff checker',
        category=Category.CLI,
        complexity=Complexity.TRIVIAL,
        entities=[],
        features=set(),
        ui_type='web',
        domain_fields={},
        framework='flask',
        needs_database=False,
    ),
    
    # --- Content / Media ---
    TrainingExample(
        id='podcast_tracker',
        description='a podcast episode tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['podcast', 'episode'],
        features={'search'},
        domain_fields={
            'podcast_name': 'str', 'episode_title': 'str', 'duration': 'int',
            'listened': 'bool', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='youtube_watchlist',
        description='a youtube video watchlist',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['video'],
        features={'tags'},
        domain_fields={
            'title': 'str', 'url': 'str', 'channel': 'str',
            'watched': 'bool', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='article_saver',
        description='an article saving app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['article'],
        features={'tags', 'search'},
        domain_fields={
            'title': 'str', 'url': 'str', 'source': 'str',
            'read': 'bool', 'saved_at': 'datetime',
        },
        framework='flask',
    ),
    TrainingExample(
        id='quote_collection',
        description='a quote collection app',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['quote'],
        features={'tags'},
        domain_fields={
            'quote_text': 'text', 'author': 'str', 'source': 'str',
        },
        framework='flask',
    ),
    
    # --- Social / Communication ---
    TrainingExample(
        id='contact_book',
        description='a contact book app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['contact'],
        features={'search'},
        domain_fields={
            'name': 'str', 'email': 'str', 'phone': 'str',
            'company': 'str', 'notes': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='birthday_reminder',
        description='a birthday reminder app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['person'],
        features={'notifications'},
        domain_fields={
            'name': 'str', 'birthday': 'date', 'relationship': 'str',
            'gift_ideas': 'text',
        },
        framework='flask',
    ),
    TrainingExample(
        id='gift_tracker',
        description='a gift tracking app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['gift', 'person'],
        features=set(),
        domain_fields={
            'recipient': 'str', 'gift_idea': 'str', 'occasion': 'str',
            'purchased': 'bool', 'budget': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='wishlist',
        description='a personal wishlist',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['wish'],
        features=set(),
        domain_fields={
            'item_name': 'str', 'price': 'float', 'url': 'str',
            'priority': 'str', 'purchased': 'bool',
        },
        framework='flask',
    ),
    
    # --- Productivity ---
    TrainingExample(
        id='daily_journal',
        description='a daily journal app',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['entry'],
        features={'search'},
        domain_fields={
            'date': 'date', 'content': 'text', 'mood': 'str',
            'tags': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='goal_tracker',
        description='a personal goal tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['goal', 'milestone'],
        features={'stats'},
        domain_fields={
            'goal_title': 'str', 'target_date': 'date', 'progress': 'int',
            'status': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='decision_helper',
        description='a decision making helper',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['decision', 'option'],
        features=set(),
        domain_fields={
            'question': 'str', 'option': 'str', 'pros': 'text',
            'cons': 'text', 'weight': 'int',
        },
        framework='flask',
    ),
    TrainingExample(
        id='morning_routine',
        description='a morning routine checklist',
        category=Category.DATA_APP,
        complexity=Complexity.TRIVIAL,
        entities=['routine_item'],
        features=set(),
        domain_fields={
            'item': 'str', 'order': 'int', 'completed': 'bool',
            'time_estimate': 'int',
        },
        framework='flask',
    ),
    
    # --- Finance ---
    TrainingExample(
        id='subscription_tracker',
        description='a subscription tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['subscription'],
        features={'stats', 'notifications'},
        domain_fields={
            'name': 'str', 'cost': 'float', 'billing_cycle': 'str',
            'next_due': 'date', 'category': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='investment_tracker',
        description='an investment portfolio tracker',
        category=Category.DATA_APP,
        complexity=Complexity.MODERATE,
        entities=['holding', 'transaction'],
        features={'stats', 'history'},
        domain_fields={
            'symbol': 'str', 'shares': 'float', 'buy_price': 'float',
            'current_price': 'float', 'gain_loss': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='debt_tracker',
        description='a debt payoff tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['debt', 'payment'],
        features={'stats'},
        domain_fields={
            'creditor': 'str', 'balance': 'float', 'interest_rate': 'float',
            'minimum_payment': 'float',
        },
        framework='flask',
    ),
    TrainingExample(
        id='savings_goal',
        description='a savings goal tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['goal', 'deposit'],
        features={'stats'},
        domain_fields={
            'goal_name': 'str', 'target_amount': 'float', 'current_amount': 'float',
            'target_date': 'date',
        },
        framework='flask',
    ),
    
    # --- Home / Household ---
    TrainingExample(
        id='chore_chart',
        description='a household chore chart',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['chore'],
        features={'notifications'},
        domain_fields={
            'chore_name': 'str', 'assignee': 'str', 'frequency': 'str',
            'last_done': 'date', 'next_due': 'date',
        },
        framework='flask',
    ),
    TrainingExample(
        id='home_inventory',
        description='a home inventory tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['item'],
        features={'search', 'tags'},
        domain_fields={
            'item_name': 'str', 'location': 'str', 'purchase_date': 'date',
            'value': 'float', 'serial_number': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='warranty_tracker',
        description='a warranty expiration tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['warranty'],
        features={'notifications'},
        domain_fields={
            'product': 'str', 'purchase_date': 'date', 'expiry_date': 'date',
            'vendor': 'str', 'receipt_url': 'str',
        },
        framework='flask',
    ),
    TrainingExample(
        id='pantry_tracker',
        description='a pantry inventory tracker',
        category=Category.DATA_APP,
        complexity=Complexity.SIMPLE,
        entities=['item'],
        features={'notifications'},
        domain_fields={
            'item_name': 'str', 'quantity': 'int', 'expiry_date': 'date',
            'category': 'str',
        },
        framework='flask',
    ),
    
    # --- API Examples ---
    TrainingExample(
        id='weather_api',
        description='a weather data API',
        category=Category.API,
        complexity=Complexity.SIMPLE,
        entities=['weather'],
        features=set(),
        ui_type='api_only',
        domain_fields={'city': 'str', 'temperature': 'float', 'conditions': 'str'},
        framework='fastapi',
    ),
    TrainingExample(
        id='quotes_api',
        description='a random quotes API',
        category=Category.API,
        complexity=Complexity.TRIVIAL,
        entities=['quote'],
        features=set(),
        ui_type='api_only',
        domain_fields={'quote': 'str', 'author': 'str'},
        framework='fastapi',
    ),
    TrainingExample(
        id='todo_api',
        description='a RESTful todo API',
        category=Category.API,
        complexity=Complexity.SIMPLE,
        entities=['todo'],
        features=set(),
        ui_type='api_only',
        domain_fields={'title': 'str', 'completed': 'bool', 'due_date': 'datetime'},
        framework='fastapi',
    ),
    TrainingExample(
        id='blog_api',
        description='a blog posts API',
        category=Category.API,
        complexity=Complexity.SIMPLE,
        entities=['post', 'author'],
        features={'auth'},
        ui_type='api_only',
        domain_fields={'title': 'str', 'content': 'text', 'author_id': 'int'},
        framework='fastapi',
    ),
    TrainingExample(
        id='inventory_api',
        description='an inventory management API',
        category=Category.API,
        complexity=Complexity.MODERATE,
        entities=['product', 'category', 'stock'],
        features={'auth', 'search'},
        ui_type='api_only',
        domain_fields={'name': 'str', 'sku': 'str', 'quantity': 'int', 'price': 'float'},
        framework='fastapi',
    ),
    
    # --- ML Examples ---
    TrainingExample(
        id='spam_classifier',
        description='a spam email classifier',
        category=Category.ML,
        complexity=Complexity.SIMPLE,
        entities=['email', 'prediction'],
        features={'stats'},
        ui_type='api_only',
        domain_fields={'text': 'str', 'is_spam': 'bool', 'confidence': 'float'},
        framework='fastapi',
    ),
    TrainingExample(
        id='text_summarizer',
        description='a text summarization model',
        category=Category.ML,
        complexity=Complexity.MODERATE,
        entities=['document', 'summary'],
        features=set(),
        ui_type='api_only',
        domain_fields={'text': 'text', 'summary': 'text', 'ratio': 'float'},
        framework='fastapi',
    ),
    TrainingExample(
        id='recommendation_engine',
        description='a product recommendation engine',
        category=Category.ML,
        complexity=Complexity.MODERATE,
        entities=['user', 'product', 'recommendation'],
        features={'auth'},
        ui_type='api_only',
        domain_fields={'user_id': 'int', 'product_ids': 'list', 'scores': 'list'},
        framework='fastapi',
    ),
    
    # --- Automation Examples ---
    TrainingExample(
        id='email_sender',
        description='an automated email sender',
        category=Category.AUTOMATION,
        complexity=Complexity.SIMPLE,
        entities=[],
        features={'notifications'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='data_exporter',
        description='a database export automation',
        category=Category.AUTOMATION,
        complexity=Complexity.SIMPLE,
        entities=[],
        features={'export'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='log_analyzer',
        description='a log file analyzer',
        category=Category.AUTOMATION,
        complexity=Complexity.SIMPLE,
        entities=[],
        features={'stats'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
    TrainingExample(
        id='report_generator',
        description='an automated report generator',
        category=Category.AUTOMATION,
        complexity=Complexity.MODERATE,
        entities=['report'],
        features={'export', 'stats'},
        ui_type='cli',
        domain_fields={},
        framework='click',
        needs_database=False,
    ),
]


# =============================================================================
# ACCESS FUNCTIONS
# =============================================================================

def get_all_examples() -> List[TrainingExample]:
    """Get all optimal training examples."""
    return OPTIMAL_TRAINING_SET


def get_by_category(category: Category) -> List[TrainingExample]:
    """Get examples by category."""
    return [ex for ex in OPTIMAL_TRAINING_SET if ex.category == category]


def get_by_complexity(complexity: Complexity) -> List[TrainingExample]:
    """Get examples by complexity."""
    return [ex for ex in OPTIMAL_TRAINING_SET if ex.complexity == complexity]


def get_by_feature(feature: str) -> List[TrainingExample]:
    """Get examples that use a specific feature."""
    return [ex for ex in OPTIMAL_TRAINING_SET if feature in ex.features]


def get_by_entity(entity: str) -> List[TrainingExample]:
    """Get examples that use a specific entity type."""
    return [ex for ex in OPTIMAL_TRAINING_SET if entity in ex.entities]


# Synonym mapping for better matching
SYNONYMS = {
    'collection': ['app', 'manager', 'tracker', 'list'],
    'app': ['application', 'system', 'platform', 'tool'],
    'user': ['account', 'member', 'author', 'profile'],
    'accounts': ['auth', 'login', 'users', 'authors'],
    'tags': ['categories', 'labels', 'groups'],
    'categories': ['tags', 'labels', 'groups'],
    'blog': ['post', 'article', 'journal'],
    'recipe': ['cooking', 'meal', 'dish'],
    'cooking': ['recipe', 'meal', 'dish'],
    'inventory': ['product', 'stock', 'warehouse'],
    'product': ['inventory', 'item', 'stock'],
    'forum': ['thread', 'community', 'discuss'],
    'thread': ['forum', 'discussion', 'topic'],
    'sudoku': ['puzzle', '9x9', 'number grid'],
    'puzzle': ['game', 'brain teaser', 'challenge'],
}

# Direct keyword to example ID mapping - highest priority matches
KEYWORD_TO_EXAMPLE_ID = {
    'sudoku': 'sudoku_game',
    'wordle': 'wordle_clone',
    'tic tac toe': 'tictactoe',
    'tictactoe': 'tictactoe',
    'hangman': 'hangman',
    'snake': 'snake_game',
    'pong': 'pong_game',
    'tetris': 'tetris_scores',
    'minesweeper': 'minesweeper',
    'chess': 'chess_game',
    'checkers': 'checkers_game',
    'blackjack': 'blackjack',
    '2048': 'game_2048',
}

# Entity synonyms - map domain keywords to entity names
ENTITY_SYNONYMS = {
    'blog': ['post', 'article'],
    'post': ['blog', 'article'],
    'inventory': ['product', 'stock'],
    'product': ['inventory', 'item'],
    'forum': ['thread', 'reply'],
    'thread': ['forum', 'topic'],
    'community': ['forum', 'thread'],
}


def expand_synonyms(text: str) -> Set[str]:
    """Expand text with synonyms for better matching."""
    words = set(text.lower().split())
    expanded = set(words)
    for word in words:
        if word in SYNONYMS:
            expanded.update(SYNONYMS[word])
    return expanded


def find_best_match(description: str) -> TrainingExample:
    """Find the best matching training example for a description."""
    desc_lower = description.lower()
    
    # PRIORITY 1: Direct keyword to example ID mapping (exact game/app types)
    for keyword, example_id in KEYWORD_TO_EXAMPLE_ID.items():
        if keyword in desc_lower:
            for ex in OPTIMAL_TRAINING_SET:
                if ex.id == example_id:
                    return ex
    
    desc_expanded = expand_synonyms(desc_lower)
    best_match = None
    best_score = -999
    
    # Detect features mentioned in description
    feature_keywords = {
        'auth': ['login', 'user', 'account', 'auth', 'accounts'],
        'search': ['search', 'find', 'filter', 'searchable'],
        'tags': ['tag', 'category', 'label', 'tags', 'categories'],
        'ratings': ['rate', 'rating', 'star', 'review', 'ratings'],
        'comments': ['comment', 'reply', 'discuss', 'comments', 'forum', 'thread'],
        'export': ['export', 'download'],
        'share': ['share', 'social', 'sharing'],
        'history': ['history', 'track', 'log'],
        'stats': ['stats', 'statistics', 'analytics'],
    }
    
    desc_features = set()
    for feature, keywords in feature_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            desc_features.add(feature)
    
    for ex in OPTIMAL_TRAINING_SET:
        score = 0
        ex_desc_lower = ex.description.lower()
        ex_expanded = expand_synonyms(ex_desc_lower)
        
        # Exact match bonus
        if desc_lower == ex_desc_lower:
            return ex
        
        # Word overlap (with synonym expansion)
        desc_words = set(desc_lower.split())
        ex_words = set(ex_desc_lower.split())
        direct_overlap = len(desc_words & ex_words)
        expanded_overlap = len(desc_expanded & ex_expanded)
        score += direct_overlap * 3  # Boost direct matches
        score += (expanded_overlap - direct_overlap)  # Add synonym bonus
        
        # Entity matching with synonyms
        if ex.entities:
            primary = ex.entities[0]
            entity_matched = False
            
            # Direct match
            if primary in desc_lower:
                score += 10  # Highest weight for primary entity
                entity_matched = True
            # Plural/variations
            elif primary + 's' in desc_lower or (len(primary) > 3 and primary[:-1] in desc_lower):
                score += 7
                entity_matched = True
            # Synonym match
            else:
                synonyms = ENTITY_SYNONYMS.get(primary, [])
                for syn in synonyms:
                    if syn in desc_lower:
                        score += 8  # Synonym match
                        entity_matched = True
                        break
                
                # Also check reverse - does desc word have this entity as synonym?
                for word in desc_words:
                    if primary in ENTITY_SYNONYMS.get(word, []):
                        score += 8
                        entity_matched = True
                        break
            
            if not entity_matched:
                # Penalty if primary entity doesn't match at all
                score -= 5
            
            # Secondary entity matches
            for entity in ex.entities[1:]:
                if entity in desc_lower:
                    score += 3
                # Extra entities not in description is a penalty
                elif entity not in ['user', 'tag', 'category']:  # Common supporting entities
                    score -= 1
        else:
            # Examples with no entities should be penalized if description implies entity
            data_keywords = ['app', 'manager', 'tracker', 'list', 'system', 'platform', 
                            'collection', 'inventory', 'blog', 'forum']
            if any(kw in desc_lower for kw in data_keywords):
                score -= 8  # Strong penalty for CLI tools matching data app descriptions
        
        # Feature matching - both positive and negative signals
        matched_features = desc_features & ex.features
        extra_features = ex.features - desc_features  # Features example has but description doesn't
        missing_features = desc_features - ex.features  # Features description has but example doesn't
        
        score += len(matched_features) * 4  # Reward matching features
        score -= len(extra_features) * 2    # Penalize extra complexity
        score -= len(missing_features) * 3  # Penalize missing features
        
        # Simplicity bonus: if description is simple, prefer simpler examples
        if len(desc_features) == 0 and len(ex.features) == 0:
            score += 5  # Both are simple
        elif len(desc_features) == 0 and len(ex.features) > 0:
            score -= 3  # Example too complex for simple description
        
        # Category matching: prefer DATA_APP examples for app/system descriptions
        # and API examples for api descriptions
        desc_is_api = any(w in desc_lower for w in ['api', 'rest', 'endpoint', 'service', 'backend'])
        desc_is_app = any(w in desc_lower for w in ['app', 'system', 'platform', 'manager', 'tracker', 'collection',
                                                     'blog', 'recipe', 'todo', 'task', 'note', 'bookmark', 'inventory',
                                                     'expense', 'budget', 'journal', 'calendar', 'workout'])
        desc_is_cli = any(w in desc_lower for w in ['cli', 'command line', 'terminal'])
        desc_is_game = any(w in desc_lower for w in ['game', 'play', 'puzzle'])
        
        ex_is_api = ex.category.value == 'api'
        ex_is_cli = ex.category.value == 'cli'
        ex_is_game = ex.category.value == 'game'
        
        # Reward matching categories, penalize mismatches
        if desc_is_api:
            if ex_is_api:
                score += 8  # Strong bonus for API match
            elif ex_is_cli:
                score -= 10  # Strong penalty for CLI when expecting API
            else:
                score -= 3
        elif desc_is_app:
            if ex_is_api:
                score -= 5  # Penalty for API when expecting app
            if ex_is_cli:
                score -= 8  # Strong penalty for CLI when expecting app
        elif desc_is_game:
            if ex_is_game:
                score += 5  # Bonus for game match
            elif not ex_is_game:
                score -= 3
        elif desc_is_cli:
            if ex_is_cli:
                score += 5
            elif ex_is_api:
                score -= 3
        
        # Direct keyword match in description - important words that should strongly influence matching
        # Primary domain keywords (what kind of app is it) - highest priority
        primary_keywords = ['blog', 'recipe', 'forum', 'inventory', 'todo', 'task', 'workout', 
                            'expense', 'calendar', 'contact', 'movie', 'photo', 'quiz']
        for keyword in primary_keywords:
            if keyword in desc_lower:
                # Check if this keyword appears in example description OR entities
                if keyword in ex_desc_lower:
                    score += 12  # Highest priority for primary domain match
                elif keyword in ex.entities:
                    score += 10  # Strong match via entities
                else:
                    # This is the PRIMARY domain but example doesn't match it - big penalty
                    score -= 6
        
        # Secondary keywords (features, characteristics) - lower priority
        secondary_keywords = ['secure', 'jwt', 'graphql', 'multiplayer']
        for keyword in secondary_keywords:
            if keyword in desc_lower:
                if keyword in ex_desc_lower:
                    score += 6  # Good bonus for matching secondary keywords
        
        # Exact phrase matching for common patterns - but not as strong as primary domain
        exact_phrases = ['rest service', 'secure rest']
        for phrase in exact_phrases:
            if phrase in desc_lower:
                if phrase in ex_desc_lower:
                    score += 8  # Good bonus for exact phrase match
        
        if score > best_score:
            best_score = score
            best_match = ex
    
    return best_match or OPTIMAL_TRAINING_SET[0]


def get_domain_fields(entity: str) -> Dict[str, str]:
    """Get domain-specific fields for an entity type."""
    # Find examples with this entity and merge their fields
    fields = {}
    for ex in OPTIMAL_TRAINING_SET:
        if entity in ex.entities:
            fields.update(ex.domain_fields)
    return fields


def get_statistics() -> Dict:
    """Get statistics about the training set."""
    by_category = {}
    by_complexity = {}
    features_count = {}
    entities_count = {}
    
    for ex in OPTIMAL_TRAINING_SET:
        # Category
        cat = ex.category.value
        by_category[cat] = by_category.get(cat, 0) + 1
        
        # Complexity
        comp = ex.complexity.value
        by_complexity[comp] = by_complexity.get(comp, 0) + 1
        
        # Features
        for f in ex.features:
            features_count[f] = features_count.get(f, 0) + 1
        
        # Entities
        for e in ex.entities:
            entities_count[e] = entities_count.get(e, 0) + 1
    
    return {
        'total_examples': len(OPTIMAL_TRAINING_SET),
        'by_category': by_category,
        'by_complexity': by_complexity,
        'features_coverage': features_count,
        'entities_coverage': entities_count,
        'unique_entities': len(entities_count),
        'unique_features': len(features_count),
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("THE 50 OPTIMAL TRAINING EXAMPLES")
    print("=" * 70)
    
    stats = get_statistics()
    print(f"\nTotal examples: {stats['total_examples']}")
    
    print("\nBy Category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat:15} {count:2} examples")
    
    print("\nBy Complexity:")
    for comp, count in sorted(stats['by_complexity'].items()):
        print(f"  {comp:15} {count:2} examples")
    
    print(f"\nUnique entities covered: {stats['unique_entities']}")
    print(f"Unique features covered: {stats['unique_features']}")
    
    print("\n" + "=" * 70)
    print("ENTITY COVERAGE")
    print("=" * 70)
    for entity, count in sorted(stats['entities_coverage'].items(), key=lambda x: -x[1]):
        print(f"  {entity:15} {count:2} examples")
    
    print("\n" + "=" * 70)
    print("FEATURE COVERAGE")
    print("=" * 70)
    for feature, count in sorted(stats['features_coverage'].items(), key=lambda x: -x[1]):
        print(f"  {feature:15} {count:2} examples")
    
    print("\n" + "=" * 70)
    print("SAMPLE: FINDING BEST MATCH")
    print("=" * 70)
    
    test_descriptions = [
        "a recipe app with ratings",
        "a workout tracker",
        "a blog with comments",
        "a multiplayer game with leaderboard",
        "a REST API",
    ]
    
    for desc in test_descriptions:
        match = find_best_match(desc)
        print(f"\n  \"{desc}\"")
        print(f"    → Best match: {match.id}")
        print(f"    → Category: {match.category.value}, Complexity: {match.complexity.value}")
        print(f"    → Features: {match.features or 'none'}")
        print(f"    → Domain fields: {list(match.domain_fields.keys())[:4]}...")
