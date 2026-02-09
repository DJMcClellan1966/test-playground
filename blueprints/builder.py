"""
Blueprint Builder - Create Custom Blueprints Without LLM

Interactive, menu-driven blueprint creation using predefined components.
No AI required - uses structured templates and user selections.

Usage:
    python builder.py                  # Interactive mode
    python builder.py --output my-app  # Save to my-app.md
"""

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Output directory
BLUEPRINTS_DIR = Path(__file__).parent


# ============================================================================
# COMPONENT LIBRARIES
# ============================================================================

# Feature categories with pre-built feature sets
FEATURE_LIBRARY = {
    "user_management": {
        "name": "User Management",
        "features": [
            "User registration with email verification",
            "Login/logout with session management",
            "Password reset via email",
            "User profile with avatar and bio",
            "Account settings and preferences",
            "Role-based access control (admin, user, guest)",
        ]
    },
    "content_creation": {
        "name": "Content Creation",
        "features": [
            "Create/edit/delete content items",
            "Rich text editor with formatting",
            "Image and file attachments",
            "Markdown support",
            "Auto-save drafts",
            "Version history",
        ]
    },
    "organization": {
        "name": "Organization & Structure",
        "features": [
            "Folders/categories for grouping",
            "Tags and labels",
            "Search with filters",
            "Sort by date, name, or custom order",
            "Nested hierarchies",
            "Favorites/bookmarks",
        ]
    },
    "collaboration": {
        "name": "Collaboration",
        "features": [
            "Share items with other users",
            "Public/private visibility",
            "Comments and discussions",
            "Real-time collaboration",
            "Activity feed",
            "Notifications",
        ]
    },
    "data_tracking": {
        "name": "Data & Tracking",
        "features": [
            "Progress tracking and completion status",
            "Due dates and reminders",
            "Dashboard with statistics",
            "Charts and visualizations",
            "Export to CSV/PDF",
            "Activity history",
        ]
    },
    "mobile_offline": {
        "name": "Mobile & Offline",
        "features": [
            "Responsive design for mobile",
            "Offline mode with sync",
            "Push notifications",
            "Quick capture/add",
            "Widget support",
            "Dark mode",
        ]
    },
    "integrations": {
        "name": "Integrations",
        "features": [
            "API for third-party access",
            "Webhook notifications",
            "Import from other services",
            "Calendar integration",
            "Email integration",
            "Browser extension",
        ]
    }
}

# Data model templates
MODEL_LIBRARY = {
    "user": {
        "name": "User",
        "fields": [
            ("id", "string (UUID)"),
            ("email", "string (unique)"),
            ("username", "string"),
            ("password_hash", "string"),
            ("created_at", "datetime"),
            ("last_login", "datetime"),
            ("is_active", "boolean"),
            ("role", "string (admin/user/guest)"),
        ]
    },
    "content": {
        "name": "Content",
        "fields": [
            ("id", "string (UUID)"),
            ("title", "string"),
            ("body", "text"),
            ("author_id", "reference (User)"),
            ("created_at", "datetime"),
            ("updated_at", "datetime"),
            ("status", "string (draft/published)"),
        ]
    },
    "category": {
        "name": "Category",
        "fields": [
            ("id", "string (UUID)"),
            ("name", "string"),
            ("description", "text (optional)"),
            ("parent_id", "reference (Category, optional)"),
            ("order", "integer"),
        ]
    },
    "tag": {
        "name": "Tag",
        "fields": [
            ("id", "string (UUID)"),
            ("name", "string (unique)"),
            ("color", "string (hex color)"),
        ]
    },
    "comment": {
        "name": "Comment",
        "fields": [
            ("id", "string (UUID)"),
            ("content_id", "reference (Content)"),
            ("author_id", "reference (User)"),
            ("text", "text"),
            ("created_at", "datetime"),
            ("parent_id", "reference (Comment, optional)"),
        ]
    },
    "file": {
        "name": "File",
        "fields": [
            ("id", "string (UUID)"),
            ("filename", "string"),
            ("content_type", "string"),
            ("size", "integer"),
            ("url", "string"),
            ("uploaded_by", "reference (User)"),
            ("uploaded_at", "datetime"),
        ]
    },
    "notification": {
        "name": "Notification",
        "fields": [
            ("id", "string (UUID)"),
            ("user_id", "reference (User)"),
            ("type", "string"),
            ("title", "string"),
            ("message", "text"),
            ("read", "boolean"),
            ("created_at", "datetime"),
        ]
    },
    "activity": {
        "name": "Activity",
        "fields": [
            ("id", "string (UUID)"),
            ("user_id", "reference (User)"),
            ("action", "string"),
            ("target_type", "string"),
            ("target_id", "string"),
            ("metadata", "json (optional)"),
            ("created_at", "datetime"),
        ]
    }
}

# Screen templates
SCREEN_LIBRARY = {
    "auth_screens": {
        "name": "Authentication Screens",
        "screens": [
            ("Login", "Email/password form with 'forgot password' and 'register' links"),
            ("Register", "Registration form with email, username, password fields"),
            ("Forgot Password", "Email input to receive reset link"),
            ("Reset Password", "New password form with confirmation"),
        ]
    },
    "dashboard_screens": {
        "name": "Dashboard & Overview",
        "screens": [
            ("Dashboard", "Overview with key metrics, recent activity, quick actions"),
            ("Statistics", "Charts and graphs showing usage data and trends"),
            ("Activity Feed", "Chronological list of recent activities"),
        ]
    },
    "content_screens": {
        "name": "Content Management",
        "screens": [
            ("List View", "Paginated list with search, filters, and sort options"),
            ("Grid View", "Card-based grid layout for visual browsing"),
            ("Detail View", "Full item display with metadata and actions"),
            ("Edit Form", "Create/edit form with validation and preview"),
        ]
    },
    "organization_screens": {
        "name": "Organization Screens",
        "screens": [
            ("Categories", "Tree view of categories with drag-and-drop reordering"),
            ("Tags Manager", "Tag list with color picker and usage counts"),
            ("Search Results", "Search results with filters and faceted navigation"),
        ]
    },
    "settings_screens": {
        "name": "Settings & Profile",
        "screens": [
            ("Profile", "User profile view and edit"),
            ("Account Settings", "Email, password, notification preferences"),
            ("App Settings", "Theme, language, display preferences"),
        ]
    }
}

# User flow templates
FLOW_LIBRARY = {
    "onboarding": {
        "name": "User Onboarding",
        "steps": [
            "User arrives at landing page",
            "Clicks 'Get Started' or 'Sign Up'",
            "Fills registration form",
            "Receives verification email",
            "Clicks verification link",
            "Sees welcome screen with quick tutorial",
            "Creates first item (guided)",
        ]
    },
    "create_item": {
        "name": "Create New Item",
        "steps": [
            "User clicks 'New' or '+' button",
            "Form opens (modal or full page)",
            "User fills in required fields",
            "Optionally adds tags/category",
            "Clicks 'Save' or 'Create'",
            "Sees success message",
            "Redirected to item view or list",
        ]
    },
    "search_find": {
        "name": "Search & Find",
        "steps": [
            "User clicks search icon or presses /",
            "Search bar expands with filters",
            "User types query",
            "Results appear instantly (debounced)",
            "User clicks filters to narrow down",
            "Clicks result to open item",
        ]
    },
    "organize": {
        "name": "Organize Content",
        "steps": [
            "User views item list",
            "Selects multiple items (checkboxes)",
            "Opens bulk actions menu",
            "Chooses 'Move to folder' or 'Add tags'",
            "Selects destination/tags",
            "Confirms action",
            "Items updated with feedback",
        ]
    },
    "share": {
        "name": "Share Content",
        "steps": [
            "User opens item they want to share",
            "Clicks 'Share' button",
            "Modal shows sharing options",
            "Chooses visibility (public/private/specific people)",
            "Optionally sets expiration",
            "Copies share link or sends invite",
        ]
    }
}


# ============================================================================
# BLUEPRINT GENERATION
# ============================================================================

def generate_blueprint(config: Dict) -> str:
    """
    Generate a blueprint markdown file from configuration.
    
    Args:
        config: Dict with title, purpose, features, models, screens, flows
        
    Returns:
        Complete blueprint as markdown string
    """
    lines = []
    
    # Title
    lines.append(f"# {config.get('title', 'Custom App')} Blueprint")
    lines.append("")
    lines.append(f"_Generated by Blueprint Builder on {datetime.now().strftime('%Y-%m-%d')}_")
    lines.append("")
    
    # Core Purpose
    lines.append("## Core Purpose")
    lines.append("")
    purpose = config.get('purpose', 'A custom application.')
    lines.append(purpose)
    lines.append("")
    
    # User Types
    lines.append("## User Types")
    lines.append("")
    user_types = config.get('user_types', ['Regular users who want to accomplish their goals'])
    for ut in user_types:
        lines.append(f"- **{ut}**")
    lines.append("")
    
    # Feature Categories
    lines.append("## Feature Categories")
    lines.append("")
    features = config.get('features', {})
    for category_id, feature_list in features.items():
        category_name = FEATURE_LIBRARY.get(category_id, {}).get('name', category_id)
        lines.append(f"### {category_name}")
        lines.append("")
        for feat in feature_list:
            lines.append(f"- {feat}")
        lines.append("")
    
    # User Flows
    if config.get('flows'):
        lines.append("## User Flows")
        lines.append("")
        for flow_id in config['flows']:
            flow = FLOW_LIBRARY.get(flow_id, {})
            lines.append(f"### {flow.get('name', flow_id)}")
            lines.append("")
            steps = flow.get('steps', [])
            for i, step in enumerate(steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
    
    # Screens
    if config.get('screens'):
        lines.append("## Screens")
        lines.append("")
        for screen_group_id in config['screens']:
            group = SCREEN_LIBRARY.get(screen_group_id, {})
            lines.append(f"### {group.get('name', screen_group_id)}")
            lines.append("")
            for screen_name, screen_desc in group.get('screens', []):
                lines.append(f"**{screen_name}**")
                lines.append(f"- {screen_desc}")
                lines.append("")
    
    # Data Model
    if config.get('models'):
        lines.append("## Data Model")
        lines.append("")
        for model_id in config['models']:
            model = MODEL_LIBRARY.get(model_id, {})
            lines.append(f"### {model.get('name', model_id)}")
            lines.append("")
            lines.append("```")
            for field_name, field_type in model.get('fields', []):
                lines.append(f"{field_name}: {field_type}")
            lines.append("```")
            lines.append("")
    
    # File Structure
    lines.append("## File Structure")
    lines.append("")
    lines.append("```")
    project_name = config.get('title', 'app').lower().replace(' ', '-')
    lines.append(f"{project_name}/")
    
    # Generate appropriate structure based on stack preference
    stack = config.get('stack', 'flask')
    if stack in ('flask', 'fastapi'):
        lines.append("├── src/")
        lines.append("│   ├── app.py")
        lines.append("│   ├── models/")
        lines.append("│   ├── routes/")
        lines.append("│   └── utils/")
        lines.append("├── tests/")
        lines.append("├── requirements.txt")
        lines.append("└── README.md")
    elif stack in ('react', 'express'):
        lines.append("├── src/")
        lines.append("│   ├── components/")
        lines.append("│   ├── pages/")
        lines.append("│   ├── services/")
        lines.append("│   └── utils/")
        lines.append("├── public/")
        lines.append("├── package.json")
        lines.append("└── README.md")
    
    lines.append("```")
    lines.append("")
    
    # Common Pitfalls
    lines.append("## Common Pitfalls")
    lines.append("")
    lines.append("- Don't skip user authentication security best practices")
    lines.append("- Avoid premature optimization - get it working first")
    lines.append("- Remember to handle error states in the UI")
    lines.append("- Plan for data migration before changing models")
    lines.append("- Test on mobile devices early")
    lines.append("")
    
    # Implementation Order
    lines.append("## Implementation Order")
    lines.append("")
    lines.append("1. Set up project structure and dependencies")
    lines.append("2. Implement core data models")
    lines.append("3. Build authentication (if needed)")
    lines.append("4. Create main CRUD functionality")
    lines.append("5. Add organization features (search, filter, sort)")
    lines.append("6. Implement secondary features")
    lines.append("7. Polish UI and add error handling")
    lines.append("8. Test and deploy")
    lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def prompt_multi_select(options: List[Tuple[str, str]], prompt: str) -> List[str]:
    """Prompt user to select multiple options."""
    print(f"\n{prompt}")
    print("Enter numbers separated by commas (e.g., 1,3,5) or 'all':\n")
    
    for i, (key, label) in enumerate(options, 1):
        print(f"  {i}. {label}")
    
    response = input("\n> ").strip()
    
    if response.lower() == 'all':
        return [key for key, label in options]
    
    selected = []
    try:
        indices = [int(x.strip()) for x in response.split(",")]
        for idx in indices:
            if 1 <= idx <= len(options):
                selected.append(options[idx - 1][0])
    except ValueError:
        pass
    
    return selected


def run_interactive() -> Optional[str]:
    """Run interactive blueprint builder."""
    print("\n" + "=" * 60)
    print("🔨 Blueprint Builder - Create Your Custom Blueprint")
    print("=" * 60)
    print("\nAnswer questions to build your blueprint.\n")
    
    config = {
        "features": {},
        "models": [],
        "screens": [],
        "flows": [],
    }
    
    # 1. Basic Info
    print("📝 Basic Information")
    print("-" * 40)
    
    config["title"] = input("App name: ").strip() or "My App"
    config["purpose"] = input("One-sentence purpose: ").strip() or "A productivity application"
    
    # 2. User Types
    print("\n👤 Who will use this app?")
    user_types = input("User types (comma-separated, e.g., 'Admin, Regular User'): ").strip()
    config["user_types"] = [ut.strip() for ut in user_types.split(",")] if user_types else ["User"]
    
    # 3. Stack
    print("\n🛠️ Tech Stack")
    print("  1. Flask (Python backend)")
    print("  2. FastAPI (Python async)")
    print("  3. Express (Node.js)")
    print("  4. React (Frontend)")
    stack_choice = input("> ").strip()
    stack_map = {"1": "flask", "2": "fastapi", "3": "express", "4": "react"}
    config["stack"] = stack_map.get(stack_choice, "flask")
    
    # 4. Features
    print("\n✨ Feature Categories")
    print("-" * 40)
    
    feature_options = [(k, v["name"]) for k, v in FEATURE_LIBRARY.items()]
    selected_categories = prompt_multi_select(feature_options, "Which feature categories do you need?")
    
    for cat_id in selected_categories:
        cat = FEATURE_LIBRARY.get(cat_id, {})
        features = cat.get("features", [])
        
        print(f"\n{cat['name']} features:")
        feature_opts = [(str(i), f) for i, f in enumerate(features, 1)]
        selected = prompt_multi_select(feature_opts, f"Select features for {cat['name']}:")
        
        if selected:
            config["features"][cat_id] = [features[int(x) - 1] for x in selected]
    
    # 5. Data Models
    print("\n📊 Data Models")
    print("-" * 40)
    
    model_options = [(k, v["name"]) for k, v in MODEL_LIBRARY.items()]
    config["models"] = prompt_multi_select(model_options, "Which data models do you need?")
    
    # 6. Screens
    print("\n📱 Screens")
    print("-" * 40)
    
    screen_options = [(k, v["name"]) for k, v in SCREEN_LIBRARY.items()]
    config["screens"] = prompt_multi_select(screen_options, "Which screen groups do you need?")
    
    # 7. User Flows
    print("\n🔄 User Flows")
    print("-" * 40)
    
    flow_options = [(k, v["name"]) for k, v in FLOW_LIBRARY.items()]
    config["flows"] = prompt_multi_select(flow_options, "Which user flows to include?")
    
    # Generate
    print("\n" + "=" * 60)
    print("📄 Generating Blueprint...")
    print("=" * 60)
    
    blueprint = generate_blueprint(config)
    
    # Preview
    print("\n--- PREVIEW (first 30 lines) ---\n")
    for line in blueprint.split("\n")[:30]:
        print(line)
    print("\n...(truncated)...\n")
    
    # Save
    save = input("Save blueprint? (y/n): ").strip().lower()
    if save == 'y':
        filename = config["title"].lower().replace(" ", "-") + ".md"
        filepath = BLUEPRINTS_DIR / filename
        
        filepath.write_text(blueprint, encoding="utf-8")
        print(f"\n✅ Saved to: {filepath}")
        print(f"\n💡 Generate project with:")
        print(f"   python scaffold.py {filename[:-3]} --name {config['title'].replace(' ', '')} --generate")
        
        return str(filepath)
    
    return None


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Create custom blueprints without AI"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output filename (without .md extension)"
    )
    
    parser.add_argument(
        "--list-components",
        action="store_true",
        help="List all available components"
    )
    
    args = parser.parse_args()
    
    if args.list_components:
        print("\n📚 Available Components\n")
        
        print("FEATURE CATEGORIES:")
        for key, val in FEATURE_LIBRARY.items():
            print(f"  {key}: {val['name']} ({len(val['features'])} features)")
        
        print("\nDATA MODELS:")
        for key, val in MODEL_LIBRARY.items():
            print(f"  {key}: {val['name']} ({len(val['fields'])} fields)")
        
        print("\nSCREEN GROUPS:")
        for key, val in SCREEN_LIBRARY.items():
            print(f"  {key}: {val['name']} ({len(val['screens'])} screens)")
        
        print("\nUSER FLOWS:")
        for key, val in FLOW_LIBRARY.items():
            print(f"  {key}: {val['name']} ({len(val['steps'])} steps)")
        
        print()
        return
    
    # Interactive mode
    run_interactive()


if __name__ == "__main__":
    main()
