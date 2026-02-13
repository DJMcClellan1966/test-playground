"""
Build 10 demo apps from basic to complex using App Forge.
Demonstrates the range of apps that can be built without AI.
"""
import urllib.request
import http.cookiejar
import json
import os
import sys

BASE_URL = "http://127.0.0.1:5000/api"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "demo_apps")

# Session management
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# 10 apps from basic to complex
APPS = [
    # Basic (1-3)
    {"name": "coin_flip", "desc": "a coin flip app", "complexity": "basic"},
    {"name": "todo_list", "desc": "a simple todo list to track tasks", "complexity": "basic"},
    {"name": "password_gen", "desc": "a secure password generator", "complexity": "basic"},
    
    # Medium (4-6)
    {"name": "recipe_book", "desc": "a recipe collection app with ingredients and cooking time", "complexity": "medium"},
    {"name": "expense_tracker", "desc": "an expense tracker with categories and monthly totals", "complexity": "medium"},
    {"name": "quiz_app", "desc": "a quiz app with multiple choice questions and scoring", "complexity": "medium"},
    
    # Complex (7-10)
    {"name": "workout_log", "desc": "a workout log with exercise tracking, sets, reps, weight, and progress charts", "complexity": "complex"},
    {"name": "movie_collection", "desc": "a movie collection with ratings, genres, watch status, and search", "complexity": "complex"},
    {"name": "meal_planner", "desc": "a weekly meal planner with recipes, shopping list generation, and nutritional info", "complexity": "complex"},
    {"name": "bookmark_manager", "desc": "a bookmark manager with folders, tags, search, and import/export", "complexity": "complex"},
]


def api_call(endpoint, data, reset_session=False):
    """Make API call to App Forge with session cookies."""
    global cookie_jar, opener
    if reset_session:
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    url = f"{BASE_URL}/{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with opener.open(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Error: {e}")
        return None


def build_app(app_info):
    """Build a single app through the conversation flow."""
    name = app_info["name"]
    desc = app_info["desc"]
    complexity = app_info["complexity"]
    
    print(f"\n{'='*60}")
    print(f"Building: {name} ({complexity})")
    print(f"Description: {desc}")
    print(f"{'='*60}")
    
    # Step 1: Start conversation (reset session for each app)
    start = api_call("start", {"description": desc}, reset_session=True)
    if not start:
        return False
    
    inferred = start.get("inferred", {})
    template = start.get("detected", {}).get("template", "unknown")
    questions_remaining = start.get("total_questions", 0)
    
    print(f"  Template: {template}")
    print(f"  Inferred: {list(inferred.keys())}")
    print(f"  Questions remaining: {questions_remaining}")
    
    # Step 2: Answer remaining questions (use defaults)
    next_q = start.get("next_question")
    while next_q:
        q_id = next_q.get("id")
        # Default to True for feature questions (more capable app)
        answer_resp = api_call("answer", {"question_id": q_id, "answer": True})
        if not answer_resp:
            return False
        if answer_resp.get("complete"):
            break
        next_q = answer_resp.get("next_question")
    
    # Step 3: Generate the app
    gen = api_call("generate", {"app_name": name.replace("_", " ").title()})
    if not gen or "error" in gen:
        print(f"  Generation error: {gen}")
        return False
    
    app_name = gen.get("app_name", name)
    files = gen.get("files", {})
    features = gen.get("features", [])
    
    print(f"  Generated: {app_name}")
    print(f"  Files: {list(files.keys())}")
    print(f"  Features: {features[:5]}{'...' if len(features) > 5 else ''}")
    
    # Step 4: Save files
    app_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(app_dir, exist_ok=True)
    
    for filename, content in files.items():
        filepath = os.path.join(app_dir, filename)
        # Create subdirectories if needed (e.g., templates/)
        file_dir = os.path.dirname(filepath)
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    # Save app info
    info = {
        "name": app_name,
        "description": desc,
        "complexity": complexity,
        "template": template,
        "features": features,
        "inferred": inferred,
        "files": list(files.keys())
    }
    with open(os.path.join(app_dir, "app_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    
    # Count lines of code
    total_lines = sum(len(content.split('\n')) for content in files.values())
    print(f"  Total lines: {total_lines}")
    print(f"  Saved to: {app_dir}")
    
    return True


def main():
    """Build all 10 demo apps."""
    print("="*60)
    print("APP FORGE - Building 10 Demo Apps (Basic to Complex)")
    print("="*60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = {"success": [], "failed": []}
    
    for app in APPS:
        try:
            if build_app(app):
                results["success"].append(app["name"])
            else:
                results["failed"].append(app["name"])
        except Exception as e:
            print(f"  Exception: {e}")
            results["failed"].append(app["name"])
    
    # Summary
    print("\n" + "="*60)
    print("BUILD SUMMARY")
    print("="*60)
    print(f"Success: {len(results['success'])}/10")
    print(f"  - " + "\n  - ".join(results["success"]) if results["success"] else "  None")
    
    if results["failed"]:
        print(f"\nFailed: {len(results['failed'])}/10")
        print(f"  - " + "\n  - ".join(results["failed"]))
    
    # List all generated apps
    print("\n" + "="*60)
    print("GENERATED APPS")
    print("="*60)
    for name in results["success"]:
        app_dir = os.path.join(OUTPUT_DIR, name)
        files = [f for f in os.listdir(app_dir) if f.endswith(('.py', '.html'))]
        print(f"\n{name}/")
        for f in files:
            filepath = os.path.join(app_dir, f)
            lines = len(open(filepath, encoding='utf-8').readlines())
            print(f"  {f} ({lines} lines)")
    
    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
