"""Component Library - Reusable App Building Blocks.

Components are framework-agnostic specifications of functionality.
Each component:
- Declares what it provides (capabilities)
- Declares what it requires (dependencies)
- Has optional questions for configuration
- Can be implemented differently per framework

The Component Library + Framework Generators = Generated Code
"""

from universal_builder import (
    Component, Question, universal_builder
)


# =====================================================================
# Core Components
# =====================================================================

COMPONENTS = [
    # ---------------------
    # Data / Storage
    # ---------------------
    Component(
        id="database",
        name="Database",
        description="Persistent data storage with SQLAlchemy",
        requires=[],
        provides=["data_storage", "persistence"],
        questions=[
            Question(
                id="db_type",
                text="Database type?",
                options=["SQLite (local)", "PostgreSQL", "MySQL"],
                default="SQLite (local)",
            ),
        ],
    ),
    
    Component(
        id="crud",
        name="CRUD Operations",
        description="Create, Read, Update, Delete endpoints",
        requires=["database"],
        provides=["crud", "data_management"],
        questions=[],
    ),
    
    Component(
        id="search",
        name="Search",
        description="Full-text search across records",
        requires=["database"],
        provides=["search", "filtering"],
        questions=[
            Question(
                id="search_type",
                text="Search type?",
                options=["Basic text match", "Full-text search", "Fuzzy search"],
                default="Basic text match",
            ),
        ],
    ),
    
    Component(
        id="export",
        name="Data Export",
        description="Export data to CSV, JSON, Excel",
        requires=["database"],
        provides=["export"],
        questions=[
            Question(
                id="export_formats",
                text="Export formats?",
                options=["CSV only", "CSV + JSON", "CSV + JSON + Excel"],
                default="CSV + JSON",
            ),
        ],
    ),
    
    Component(
        id="import_data",
        name="Data Import",
        description="Import data from files",
        requires=["database"],
        provides=["import"],
        questions=[
            Question(
                id="import_formats",
                text="Import formats?",
                options=["CSV only", "CSV + JSON", "CSV + JSON + Excel"],
                default="CSV only",
            ),
        ],
    ),
    
    # ---------------------
    # Authentication
    # ---------------------
    Component(
        id="auth",
        name="Authentication",
        description="User login, registration, sessions",
        requires=["database"],
        provides=["auth", "user_session", "user_identity"],
        questions=[
            Question(
                id="auth_method",
                text="Authentication method?",
                options=["Session (cookies)", "JWT Tokens", "API Keys"],
                default="Session (cookies)",
            ),
            Question(
                id="password_hashing",
                text="Password hashing?",
                options=["bcrypt", "argon2", "pbkdf2"],
                default="bcrypt",
            ),
        ],
    ),
    
    Component(
        id="oauth",
        name="OAuth / Social Login",
        description="Login with Google, GitHub, etc.",
        requires=["auth"],
        provides=["oauth", "social_login"],
        questions=[
            Question(
                id="oauth_providers",
                text="OAuth providers?",
                options=["Google", "GitHub", "Google + GitHub", "All major"],
                default="Google + GitHub",
            ),
        ],
    ),
    
    Component(
        id="roles",
        name="Role-Based Access",
        description="User roles and permissions",
        requires=["auth"],
        provides=["roles", "permissions", "access_control"],
        questions=[
            Question(
                id="role_type",
                text="Role system?",
                options=["Simple (admin/user)", "Multiple roles", "Fine-grained permissions"],
                default="Simple (admin/user)",
            ),
        ],
    ),
    
    # ---------------------
    # Realtime
    # ---------------------
    Component(
        id="websocket",
        name="WebSocket",
        description="Real-time bidirectional communication",
        requires=[],
        provides=["realtime", "push_updates"],
        questions=[],
        supported_frameworks=["flask_socketio", "fastapi", "express"],
    ),
    
    Component(
        id="sse",
        name="Server-Sent Events",
        description="Server-to-client push (one-way)",
        requires=[],
        provides=["push_updates"],
        questions=[],
    ),
    
    # ---------------------
    # File Handling
    # ---------------------
    Component(
        id="file_upload",
        name="File Upload",
        description="Upload and store files",
        requires=[],
        provides=["file_upload", "file_storage"],
        questions=[
            Question(
                id="storage_type",
                text="File storage?",
                options=["Local filesystem", "S3 / Cloud", "Database (blob)"],
                default="Local filesystem",
            ),
            Question(
                id="max_file_size",
                text="Max file size?",
                options=["5 MB", "50 MB", "500 MB", "No limit"],
                default="50 MB",
            ),
        ],
    ),
    
    Component(
        id="image_processing",
        name="Image Processing",
        description="Resize, crop, thumbnail generation",
        requires=["file_upload"],
        provides=["image_processing", "thumbnails"],
        questions=[],
    ),
    
    # ---------------------
    # Communication
    # ---------------------
    Component(
        id="email",
        name="Email",
        description="Send emails (SMTP, SendGrid, etc.)",
        requires=[],
        provides=["email"],
        questions=[
            Question(
                id="email_provider",
                text="Email provider?",
                options=["SMTP (any)", "SendGrid", "Mailgun", "SES"],
                default="SMTP (any)",
            ),
        ],
    ),
    
    Component(
        id="notifications",
        name="Notifications",
        description="Push notifications, alerts",
        requires=[],
        provides=["notifications", "alerts"],
        questions=[
            Question(
                id="notification_channels",
                text="Notification channels?",
                options=["In-app only", "In-app + Email", "In-app + Push", "All"],
                default="In-app only",
            ),
        ],
    ),
    
    # ---------------------
    # UI / Frontend
    # ---------------------
    Component(
        id="charts",
        name="Charts & Graphs",
        description="Data visualization (Chart.js, D3)",
        requires=[],
        provides=["charts", "visualization"],
        questions=[
            Question(
                id="chart_library",
                text="Chart library?",
                options=["Chart.js", "D3.js", "Plotly", "Auto-select"],
                default="Chart.js",
            ),
        ],
    ),
    
    Component(
        id="dark_mode",
        name="Dark Mode",
        description="Theme switching (light/dark)",
        requires=[],
        provides=["dark_mode", "theming"],
        questions=[],
    ),
    
    Component(
        id="responsive",
        name="Responsive Design",
        description="Mobile-friendly layouts",
        requires=[],
        provides=["responsive", "mobile_friendly"],
        questions=[],
    ),
    
    # ---------------------
    # API Features
    # ---------------------
    Component(
        id="endpoints",
        name="API Endpoints",
        description="REST/GraphQL endpoint structure",
        requires=[],
        provides=["api", "endpoints"],
        questions=[],
    ),
    
    Component(
        id="validation",
        name="Input Validation",
        description="Request data validation (Pydantic, marshmallow)",
        requires=[],
        provides=["validation"],
        questions=[],
    ),
    
    Component(
        id="rate_limiting",
        name="Rate Limiting",
        description="Request rate limiting per user/IP",
        requires=[],
        provides=["rate_limiting", "abuse_prevention"],
        questions=[
            Question(
                id="rate_limit",
                text="Rate limit?",
                options=["100/minute", "1000/minute", "Custom"],
                default="100/minute",
            ),
        ],
    ),
    
    Component(
        id="caching",
        name="Caching",
        description="Response caching (Redis, in-memory)",
        requires=[],
        provides=["caching", "performance"],
        questions=[
            Question(
                id="cache_backend",
                text="Cache backend?",
                options=["In-memory", "Redis", "Memcached"],
                default="In-memory",
            ),
        ],
    ),
    
    Component(
        id="api_docs",
        name="API Documentation",
        description="Auto-generated docs (Swagger/OpenAPI)",
        requires=["endpoints"],
        provides=["documentation", "openapi"],
        questions=[],
    ),
    
    # ---------------------
    # Game Components
    # ---------------------
    Component(
        id="game_loop",
        name="Game Loop",
        description="Main update/render loop",
        requires=[],
        provides=["game_loop", "frame_updates"],
        questions=[
            Question(
                id="loop_type",
                text="Game loop type?",
                options=["RequestAnimationFrame", "setInterval", "Event-driven"],
                default="RequestAnimationFrame",
            ),
        ],
    ),
    
    Component(
        id="input_handler",
        name="Input Handler",
        description="Keyboard, mouse, touch input",
        requires=[],
        provides=["input", "controls"],
        questions=[
            Question(
                id="input_types",
                text="Input types?",
                options=["Keyboard", "Mouse/Touch", "Both"],
                default="Both",
            ),
        ],
    ),
    
    Component(
        id="renderer",
        name="Renderer",
        description="Canvas, DOM, or WebGL rendering",
        requires=[],
        provides=["rendering", "graphics"],
        questions=[
            Question(
                id="render_type",
                text="Render type?",
                options=["Canvas 2D", "DOM elements", "WebGL", "Auto-select"],
                default="Canvas 2D",
            ),
        ],
    ),
    
    Component(
        id="physics",
        name="Physics Engine",
        description="Collision detection, gravity, etc.",
        requires=["game_loop"],
        provides=["physics", "collisions"],
        questions=[
            Question(
                id="physics_type",
                text="Physics complexity?",
                options=["Basic (AABB collisions)", "Advanced (Matter.js)", "None"],
                default="Basic (AABB collisions)",
            ),
        ],
    ),
    
    Component(
        id="scoring",
        name="Scoring System",
        description="Points, lives, game over logic",
        requires=["game_loop"],
        provides=["scoring", "game_state"],
        questions=[],
    ),
    
    Component(
        id="leaderboard",
        name="Leaderboard",
        description="High score storage and display",
        requires=["scoring"],
        provides=["leaderboard", "persistent_scores"],
        questions=[
            Question(
                id="leaderboard_storage",
                text="Leaderboard storage?",
                options=["Local only", "Server-side", "Both"],
                default="Local only",
            ),
        ],
    ),
    
    # ---------------------
    # ML Components
    # ---------------------
    Component(
        id="data_loader",
        name="Data Loader",
        description="Load and preprocess datasets",
        requires=[],
        provides=["data_loading", "preprocessing"],
        questions=[
            Question(
                id="data_format",
                text="Data format?",
                options=["CSV", "JSON", "Parquet", "Multiple"],
                default="CSV",
            ),
        ],
    ),
    
    Component(
        id="model",
        name="ML Model",
        description="Model definition and training",
        requires=["data_loader"],
        provides=["model", "training"],
        questions=[],
    ),
    
    Component(
        id="evaluator",
        name="Model Evaluator",
        description="Metrics, validation, testing",
        requires=["model"],
        provides=["evaluation", "metrics"],
        questions=[],
    ),
    
    Component(
        id="model_serving",
        name="Model Serving",
        description="Deploy model as API endpoint",
        requires=["model"],
        provides=["model_api", "inference"],
        questions=[],
    ),
    
    # ---------------------
    # CLI Components
    # ---------------------
    Component(
        id="commands",
        name="Commands",
        description="CLI command structure",
        requires=[],
        provides=["commands", "cli"],
        questions=[],
    ),
    
    Component(
        id="argument_parser",
        name="Argument Parser",
        description="Parse command-line arguments",
        requires=[],
        provides=["argument_parsing"],
        questions=[],
    ),
    
    Component(
        id="progress_bar",
        name="Progress Bar",
        description="Visual progress for long operations",
        requires=[],
        provides=["progress_display"],
        questions=[],
    ),
    
    Component(
        id="rich_output",
        name="Rich Output",
        description="Colored, formatted terminal output",
        requires=[],
        provides=["rich_output", "formatting"],
        questions=[],
    ),
    
    # ---------------------
    # Automation Components
    # ---------------------
    Component(
        id="scheduler",
        name="Task Scheduler",
        description="Schedule tasks (cron, intervals)",
        requires=[],
        provides=["scheduling", "cron"],
        questions=[
            Question(
                id="scheduler_type",
                text="Scheduler type?",
                options=["APScheduler (Python)", "Celery", "OS cron"],
                default="APScheduler (Python)",
            ),
        ],
    ),
    
    Component(
        id="task_runner",
        name="Task Runner",
        description="Execute and monitor tasks",
        requires=[],
        provides=["task_execution", "job_management"],
        questions=[],
    ),
    
    Component(
        id="web_scraper",
        name="Web Scraper",
        description="Scrape web pages (requests, BeautifulSoup)",
        requires=[],
        provides=["web_scraping", "html_parsing"],
        questions=[
            Question(
                id="scraper_type",
                text="Scraper type?",
                options=["requests + BeautifulSoup", "Selenium", "Playwright"],
                default="requests + BeautifulSoup",
            ),
        ],
    ),
    
    Component(
        id="retry_logic",
        name="Retry Logic",
        description="Retry failed operations with backoff",
        requires=[],
        provides=["retry", "fault_tolerance"],
        questions=[],
    ),
]


# =====================================================================
# Component Registry Functions
# =====================================================================

def register_all_components():
    """Register all components with the universal builder."""
    for component in COMPONENTS:
        universal_builder.register_component(component)


def get_component(component_id: str) -> Component:
    """Get a component by ID."""
    return universal_builder.component_library.get(component_id)


def get_components_by_capability(capability: str) -> list[Component]:
    """Get all components that provide a capability."""
    return [
        c for c in COMPONENTS 
        if capability in c.provides
    ]


def get_component_dependencies(component_id: str) -> list[str]:
    """Get all dependencies (transitive) for a component."""
    component = get_component(component_id)
    if not component:
        return []
    
    deps = set()
    to_process = list(component.requires)
    
    while to_process:
        dep_id = to_process.pop()
        if dep_id not in deps:
            deps.add(dep_id)
            dep = get_component(dep_id)
            if dep:
                to_process.extend(dep.requires)
    
    return list(deps)


# Auto-register on import
register_all_components()


# =====================================================================
# Testing
# =====================================================================

if __name__ == "__main__":
    print("Component Library")
    print("=" * 60)
    
    print(f"\nTotal components: {len(COMPONENTS)}")
    
    # Group by category
    categories = {}
    for comp in COMPONENTS:
        # Infer category from first capability
        cat = comp.provides[0] if comp.provides else "other"
        categories.setdefault(cat, []).append(comp.id)
    
    print("\nComponents by capability:")
    for cat, comps in sorted(categories.items()):
        print(f"  {cat}: {', '.join(comps)}")
    
    print("\nDependency test (auth):")
    deps = get_component_dependencies("auth")
    print(f"  auth requires: {deps}")
    
    print("\nDependency test (leaderboard):")
    deps = get_component_dependencies("leaderboard")
    print(f"  leaderboard requires: {deps}")
