"""App Forge - Natural language app builder."""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os

from smartq import *
from smartq import total_relevant_count, infer_from_description
from solver import solver
from codegen import generator, detect_app_type
from project_manager import manager
from preview_server import preview
from template_registry import match_template, extract_features, explain_match

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='')
CORS(app)
app.config['SECRET_KEY'] = 'dev-secret'

# =============================================================================
# Session Management  
# =============================================================================

@app.before_request
def init_session():
    """Initialize session for wizard."""
    if 'profile' not in session:
        session['profile'] = None
    if 'answered' not in session:
        session['answered'] = {}


# =============================================================================
# API Endpoints
# =============================================================================

@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_wizard():
    """User submits app description."""
    data = request.get_json()
    description = data.get('description', '').strip()
    
    if not description or len(description) < 10:
        return jsonify({"error": "Please describe your app (at least 10 characters)"}), 400
    
    # Auto-infer answers from description
    inferred = infer_from_description(description)
    
    # Detect what template will be used (for frontend display)
    best_template, features, scores = match_template(description)
    feature_summary = {k: f.value for k, f in features.items()}
    
    # Create profile
    profile = Profile(description)
    session['profile'] = profile.to_dict()
    session['answered'] = inferred.copy()
    session['inferred_count'] = len(inferred)
    session.modified = True
    
    # Get remaining questions after inference
    remaining = get_relevant_questions(inferred)
    next_q = remaining[0] if remaining else None
    
    return jsonify({
        "profile": session['profile'],
        "inferred": inferred,
        "total_questions": len(remaining),
        "next_question": {
            "id": next_q.id,
            "text": next_q.text,
        } if next_q else None,
        "detected": {
            "template": best_template,
            "features": feature_summary,
        },
    })


@app.route('/api/answer', methods=['POST'])
def answer_question():
    """User answers a question."""
    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')  # true/false
    
    answered = session.get('answered', {})
    answered[question_id] = answer
    session['answered'] = answered
    session.modified = True
    
    # Check if done
    if is_complete(answered):
        return jsonify({
            "complete": True,
            "answered": answered,
            "total_questions": 0,
        })
    
    # Get next question
    next_q = get_next_question(answered)
    remaining = get_relevant_questions(answered)
    inferred_count = session.get('inferred_count', 0)
    user_answered = len(answered) - inferred_count
    
    return jsonify({
        "complete": False,
        "answered": answered,
        "total_questions": user_answered + len(remaining),
        "next_question": {
            "id": next_q.id,
            "text": next_q.text,
        } if next_q else None,
    })


@app.route('/api/generate', methods=['POST'])
def generate_project():
    """Generate the app from answers and start live preview."""
    profile_data = session.get('profile')
    answered = session.get('answered', {})
    
    if not profile_data or not answered:
        return jsonify({"error": "No profile or answers"}), 400
    
    profile = Profile.from_dict(profile_data)
    
    # Solve for tech stack
    tech_stack = solver.solve(answered, profile.description)
    
    # Generate code — pass description for domain-aware models
    app_name = request.get_json().get('app_name', 'My App')
    app_py = generator.generate_app_py(app_name, answered, profile.description)
    requirements_txt = generator.generate_requirements_txt(answered)
    index_html = generator.generate_index_html(app_name, answered, profile.description)
    
    # Auto-start live preview server
    result = preview.start(app_py, requirements_txt, index_html)
    preview_url = result.get('preview_url', '') if result.get('success') else ''
    preview_error = result.get('error', '') if not result.get('success') else ''
    
    return jsonify({
        "tech_stack": tech_stack.to_dict(),
        "app_name": app_name,
        "files": {
            "app.py": app_py,
            "requirements.txt": requirements_txt,
            "templates/index.html": index_html,
        },
        "preview_url": preview_url,
        "preview_error": preview_error,
    })


@app.route('/api/regenerate', methods=['POST'])
def regenerate():
    """Iterate mode: re-enter questions step keeping existing answers. #6"""
    answered = session.get('answered', {})
    profile_data = session.get('profile')
    if not profile_data:
        return jsonify({"error": "No profile"}), 400

    # Client sends which answer to change (optional)
    data = request.get_json() or {}
    reset_from = data.get('reset_from')  # question id to clear + later ones
    if reset_from:
        # Remove this answer and any that depended on it
        to_remove = []
        found = False
        for q in QUESTIONS:
            if q.id == reset_from:
                found = True
            if found:
                to_remove.append(q.id)
        for qid in to_remove:
            answered.pop(qid, None)
        session['answered'] = answered
        session.modified = True

    next_q = get_next_question(answered)
    return jsonify({
        "answered": answered,
        "total_questions": total_relevant_count(answered),
        "next_question": {
            "id": next_q.id,
            "text": next_q.text
        } if next_q else None,
        "complete": next_q is None,
    })


@app.route('/api/save-and-preview', methods=['POST'])
def save_and_preview():
    """Save project to disk."""
    data = request.get_json()
    app_name = data.get('app_name', 'My App')
    description = data.get('description', '')
    answered = data.get('answered', {})
    files = data.get('files', {})
    
    if not files:
        return jsonify({"error": "No generated files to save"}), 400
    
    try:
        project_path = manager.create_project(
            app_name=app_name,
            description=description,
            answers=answered,
            app_py=files.get('app.py', ''),
            requirements_txt=files.get('requirements.txt', ''),
            index_html=files.get('templates/index.html', ''),
        )
        
        return jsonify({
            "success": True,
            "project_path": str(project_path),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/export-github', methods=['POST'])
def export_github():
    """Export to GitHub."""
    data = request.get_json()
    project_path = data.get('project_path')
    github_url = data.get('github_url')  # https://github.com/user/repo.git
    
    try:
        manager.init_git(project_path, github_url)
        return jsonify({"success": True, "message": "Pushed to GitHub!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/preview/stop', methods=['POST'])
def stop_preview():
    """Stop the live preview server."""
    preview.stop()
    return jsonify({"success": True})


@app.route('/api/projects')
def list_projects():
    """Get all saved projects."""
    projects = manager.get_projects()
    return jsonify(projects)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/api/explain', methods=['POST'])
def explain_template():
    """Show what features were extracted and which template was chosen."""
    data = request.get_json()
    description = data.get('description', '').strip()
    if not description:
        return jsonify({"error": "No description"}), 400

    best_id, features, scores = match_template(description)
    return jsonify({
        "template": best_id,
        "features": {k: {"value": f.value, "confidence": f.confidence}
                     for k, f in features.items()},
        "scores": [{"id": tid, "score": s} for tid, s in scores[:5]],
        "explanation": explain_match(description),
    })


if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        # Clean up preview server on exit
        preview.stop()
