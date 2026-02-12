"""Category Registry - App Type Definitions.

Each category defines:
- What frameworks can be used
- What questions to ask
- What base components are always included
- How to detect if a description belongs to this category

Categories are higher-level than templates - they represent
fundamental types of software rather than specific implementations.
"""

from universal_builder import (
    AppCategory, CategoryConfig, Question, 
    universal_builder
)


# =====================================================================
# Question Banks per Category
# =====================================================================

DATA_APP_QUESTIONS = [
    Question(
        id="has_data",
        text="Does this app need to store data?",
        options=["Yes", "No"],
        default="Yes",
    ),
    Question(
        id="needs_auth",
        text="Do users need to log in?",
        options=["Yes, require login", "Optional accounts", "No, single user"],
        default="No, single user",
    ),
    Question(
        id="multi_user",
        text="Is this for multiple users or just you?",
        options=["Multiple users", "Just me"],
        default="Just me",
        depends_on="needs_auth",
    ),
    Question(
        id="search",
        text="Include search functionality?",
        options=["Yes", "No"],
        default="Yes",
        depends_on="has_data",
    ),
    Question(
        id="export",
        text="Allow exporting data (CSV, JSON)?",
        options=["Yes", "No"],
        default="No",
        depends_on="has_data",
    ),
    Question(
        id="responsive",
        text="Optimize for mobile devices?",
        options=["Yes", "Desktop only"],
        default="Yes",
    ),
]

GAME_QUESTIONS = [
    Question(
        id="game_type",
        text="What type of game?",
        options=["Puzzle", "Action", "Turn-based", "Quiz/Trivia", "Card game", "Other"],
    ),
    Question(
        id="multiplayer",
        text="Multiplayer support?",
        options=["Single player", "Local multiplayer", "Online multiplayer"],
        default="Single player",
    ),
    Question(
        id="leaderboard",
        text="Include high score leaderboard?",
        options=["Yes", "No"],
        default="No",
    ),
    Question(
        id="timer",
        text="Time-based gameplay?",
        options=["Yes, timed", "No time limit"],
        default="No time limit",
    ),
    Question(
        id="difficulty",
        text="Multiple difficulty levels?",
        options=["Yes", "No"],
        default="No",
    ),
]

API_SERVICE_QUESTIONS = [
    Question(
        id="api_style",
        text="API style?",
        options=["REST", "GraphQL", "gRPC"],
        default="REST",
    ),
    Question(
        id="auth_type",
        text="Authentication method?",
        options=["API Key", "JWT Tokens", "OAuth2", "None"],
        default="JWT Tokens",
    ),
    Question(
        id="database",
        text="Database type?",
        options=["SQLite (local)", "PostgreSQL", "MongoDB", "None"],
        default="SQLite (local)",
    ),
    Question(
        id="rate_limiting",
        text="Include rate limiting?",
        options=["Yes", "No"],
        default="No",
    ),
    Question(
        id="caching",
        text="Include caching layer?",
        options=["Yes", "No"],
        default="No",
    ),
    Question(
        id="docs",
        text="Auto-generate API docs?",
        options=["Yes (Swagger/OpenAPI)", "No"],
        default="Yes (Swagger/OpenAPI)",
    ),
]

ML_PIPELINE_QUESTIONS = [
    Question(
        id="ml_task",
        text="What type of ML task?",
        options=["Classification", "Regression", "Clustering", "NLP", "Computer Vision", "Other"],
    ),
    Question(
        id="ml_framework",
        text="ML framework preference?",
        options=["Scikit-learn", "PyTorch", "TensorFlow", "Auto-select"],
        default="Auto-select",
    ),
    Question(
        id="data_source",
        text="Data source?",
        options=["CSV files", "Database", "API", "User upload"],
        default="CSV files",
    ),
    Question(
        id="serve_model",
        text="Serve model as API?",
        options=["Yes", "No, just training"],
        default="Yes",
    ),
    Question(
        id="experiment_tracking",
        text="Track experiments?",
        options=["Yes (MLflow)", "No"],
        default="No",
    ),
]

CLI_TOOL_QUESTIONS = [
    Question(
        id="cli_framework",
        text="CLI framework?",
        options=["Click", "Typer", "Argparse (built-in)"],
        default="Click",
    ),
    Question(
        id="subcommands",
        text="Multiple subcommands?",
        options=["Yes", "Single command"],
        default="Single command",
    ),
    Question(
        id="config_file",
        text="Support config file?",
        options=["Yes (YAML)", "Yes (JSON)", "No"],
        default="No",
    ),
    Question(
        id="progress_bar",
        text="Show progress for long operations?",
        options=["Yes", "No"],
        default="No",
    ),
    Question(
        id="output_format",
        text="Output format?",
        options=["Plain text", "JSON", "Table", "Multiple formats"],
        default="Plain text",
    ),
]

AUTOMATION_QUESTIONS = [
    Question(
        id="trigger",
        text="How should it run?",
        options=["On schedule (cron)", "On event", "On demand", "Continuously"],
        default="On demand",
    ),
    Question(
        id="automation_type",
        text="What type of automation?",
        options=["Web scraping", "File processing", "API integration", "Data sync", "Other"],
    ),
    Question(
        id="notifications",
        text="Send notifications?",
        options=["Email", "Slack", "Discord", "No"],
        default="No",
    ),
    Question(
        id="logging",
        text="Detailed logging?",
        options=["Yes", "Minimal"],
        default="Minimal",
    ),
    Question(
        id="retry",
        text="Retry on failure?",
        options=["Yes, with backoff", "No"],
        default="No",
    ),
]


# =====================================================================
# Category Configurations
# =====================================================================

CATEGORY_CONFIGS = [
    CategoryConfig(
        category=AppCategory.DATA_APP,
        name="Data Collection App",
        description="Apps for storing, managing, and browsing collections of data",
        default_framework="flask",
        supported_frameworks=["flask", "fastapi", "django", "express"],
        questions=DATA_APP_QUESTIONS,
        base_components=["crud", "database"],
    ),
    
    CategoryConfig(
        category=AppCategory.GAME,
        name="Game / Interactive",
        description="Browser games, interactive experiences, visualizations",
        default_framework="html_canvas",
        supported_frameworks=["html_canvas", "pygame", "phaser"],
        questions=GAME_QUESTIONS,
        base_components=["game_loop", "input_handler", "renderer"],
    ),
    
    CategoryConfig(
        category=AppCategory.API_SERVICE,
        name="API Service",
        description="REST APIs, GraphQL services, backend services",
        default_framework="fastapi",
        supported_frameworks=["fastapi", "flask", "express", "dotnet"],
        questions=API_SERVICE_QUESTIONS,
        base_components=["endpoints", "validation", "error_handling"],
    ),
    
    CategoryConfig(
        category=AppCategory.ML_PIPELINE,
        name="ML Pipeline",
        description="Machine learning models, data science workflows",
        default_framework="sklearn_pipeline",
        supported_frameworks=["sklearn_pipeline", "pytorch", "tensorflow"],
        questions=ML_PIPELINE_QUESTIONS,
        base_components=["data_loader", "model", "evaluator"],
    ),
    
    CategoryConfig(
        category=AppCategory.CLI_TOOL,
        name="Command-Line Tool",
        description="Terminal utilities, scripts with arguments",
        default_framework="click",
        supported_frameworks=["click", "typer", "argparse"],
        questions=CLI_TOOL_QUESTIONS,
        base_components=["commands", "argument_parser"],
    ),
    
    CategoryConfig(
        category=AppCategory.AUTOMATION,
        name="Automation / Bot",
        description="Scheduled tasks, web scrapers, workflow automation",
        default_framework="python_script",
        supported_frameworks=["python_script", "celery", "airflow"],
        questions=AUTOMATION_QUESTIONS,
        base_components=["scheduler", "task_runner"],
    ),
]


# =====================================================================
# Detection Patterns per Category
# =====================================================================

CATEGORY_PATTERNS = {
    AppCategory.DATA_APP: {
        "keywords": [
            "collection", "tracker", "log", "list", "inventory", "catalog",
            "recipe", "todo", "task", "note", "habit", "budget", "expense",
            "journal", "diary", "bookmark", "library", "portfolio", "contact",
            "event", "calendar", "movie", "book", "workout", "grocery",
        ],
        "patterns": [
            r"\b(save|store|track|collect|manage)\b.*\b(data|items?|entries?)\b",
            r"\b(crud|database|storage)\b",
        ],
        "anti_patterns": [
            r"\bgame\b", r"\bplay\b", r"\bscore\b",
        ],
    },
    
    AppCategory.GAME: {
        "keywords": [
            "game", "play", "puzzle", "quiz", "trivia", "score", "level",
            "snake", "pong", "tetris", "memory", "card", "dice", "guess",
            "wordle", "hangman", "minesweeper", "sudoku", "chess", "tic tac toe",
        ],
        "patterns": [
            r"\b(play|gaming|interactive)\b",
            r"\b(win|lose|high\s*score|leaderboard)\b",
        ],
        "anti_patterns": [],
    },
    
    AppCategory.API_SERVICE: {
        "keywords": [
            "api", "rest", "graphql", "endpoint", "service", "backend",
            "microservice", "webhook", "integration",
        ],
        "patterns": [
            r"\brest\s*api\b",
            r"\b(get|post|put|delete)\s+(endpoint|route)\b",
            r"\bjson\s*(api|service)\b",
        ],
        "anti_patterns": [],
    },
    
    AppCategory.ML_PIPELINE: {
        "keywords": [
            "ml", "machine learning", "model", "predict", "train", "dataset",
            "classification", "regression", "clustering", "neural", "ai",
            "tensorflow", "pytorch", "sklearn", "deep learning",
        ],
        "patterns": [
            r"\b(train|fit)\s+(a\s+)?model\b",
            r"\bpredict\b.*\b(price|value|class|label)\b",
            r"\b(neural|deep)\s*(network|learning)\b",
        ],
        "anti_patterns": [],
    },
    
    AppCategory.CLI_TOOL: {
        "keywords": [
            "cli", "command", "terminal", "script", "utility", "tool",
            "argument", "flag", "option",
        ],
        "patterns": [
            r"\bcommand[\s-]*line\b",
            r"\bterminal\s+(app|tool|utility)\b",
            r"\b(run|execute)\s+from\s+(terminal|shell)\b",
        ],
        "anti_patterns": [],
    },
    
    AppCategory.AUTOMATION: {
        "keywords": [
            "automate", "automation", "bot", "scrape", "schedule", "cron", "workflow",
            "backup", "monitoring", "monitor", "sync", "pipeline", "etl",
        ],
        "patterns": [
            r"\b(scrape|crawl)\s+(web|site|page)\b",
            r"\b(automate|schedule)\s+(task|job|process)\b",
            r"\bbot\b.*\b(slack|discord|telegram)\b",
            r"\b(backup|monitoring)\s+(script|automation)\b",
            r"\b(file|price|data)\s+(backup|monitoring|monitor)\b",
        ],
        "anti_patterns": [],
    },
}


# =====================================================================
# Registration Function
# =====================================================================

def register_all_categories():
    """Register all category configurations with the universal builder."""
    for config in CATEGORY_CONFIGS:
        universal_builder.register_category(config)


# Auto-register on import
register_all_categories()


# =====================================================================
# Category Detection
# =====================================================================

import re

def detect_category(description: str) -> tuple[AppCategory, float]:
    """Detect the most likely category and confidence score.
    
    Returns (category, confidence) where confidence is 0-1.
    """
    desc_lower = description.lower()
    scores = {}
    
    for category, patterns in CATEGORY_PATTERNS.items():
        score = 0.0
        
        # Keyword matches
        for keyword in patterns["keywords"]:
            if keyword in desc_lower:
                # Longer keywords are more specific
                score += 0.1 * (len(keyword) / 5)
        
        # Pattern matches (higher value)
        for pattern in patterns.get("patterns", []):
            if re.search(pattern, desc_lower):
                score += 0.3
        
        # Anti-patterns reduce score
        for pattern in patterns.get("anti_patterns", []):
            if re.search(pattern, desc_lower):
                score -= 0.5
        
        scores[category] = max(0, score)
    
    # Find best match
    if not scores or max(scores.values()) == 0:
        return AppCategory.DATA_APP, 0.3  # Default with low confidence
    
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    
    # Normalize confidence (cap at 1.0)
    confidence = min(1.0, best_score / 2.0)
    
    return best_category, confidence


# =====================================================================
# Testing
# =====================================================================

if __name__ == "__main__":
    test_cases = [
        "a recipe collection app with ingredients",
        "a snake game",
        "a REST API for managing users",
        "a machine learning model to predict house prices",
        "a CLI tool for converting images",
        "a bot that scrapes news headlines daily",
        "a todo list app",
        "a multiplayer quiz game",
        "a GraphQL API with authentication",
    ]
    
    print("Category Detection Tests")
    print("=" * 60)
    
    for desc in test_cases:
        category, confidence = detect_category(desc)
        conf_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        print(f"[{conf_bar}] {category.value:15} ← {desc}")
