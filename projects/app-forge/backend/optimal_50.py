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
]


# =============================================================================
# ACCESS FUNCTIONS
# =============================================================================

def get_all_examples() -> List[TrainingExample]:
    """Get all 50 optimal training examples."""
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
        desc_is_app = any(w in desc_lower for w in ['app', 'system', 'platform', 'manager', 'tracker', 'collection'])
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
