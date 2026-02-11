"""App Forge - Natural language app builder."""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os

from smartq import *
from solver import solver
from codegen import generator
from project_manager import manager

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
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
    
    # Create profile
    profile = Profile(description)
    session['profile'] = profile.to_dict()
    session['answered'] = {}
    session.modified = True
    
    # Get first question
    next_q = get_next_question({})
    
    return jsonify({
        "profile": session['profile'],
        "next_question": {
            "id": next_q.id,
            "text": next_q.text,
        } if next_q else None,
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
        })
    
    # Get next question
    next_q = get_next_question(answered)
    
    return jsonify({
        "complete": False,
        "answered": answered,
        "next_question": {
            "id": next_q.id,
            "text": next_q.text,
        } if next_q else None,
    })


@app.route('/api/generate', methods=['POST'])
def generate_project():
    """Generate the app from answers."""
    profile_data = session.get('profile')
    answered = session.get('answered', {})
    
    if not profile_data or not answered:
        return jsonify({"error": "No profile or answers"}), 400
    
    profile = Profile.from_dict(profile_data)
    
    # Solve for tech stack
    tech_stack = solver.solve(answered, profile.description)
    
    # Generate code
    app_name = request.get_json().get('app_name', 'My App')
    app_py = generator.generate_app_py(app_name, answered)
    requirements_txt = generator.generate_requirements_txt(answered)
    index_html = generator.generate_index_html(app_name, answered)
    
    return jsonify({
        "tech_stack": tech_stack.to_dict(),
        "app_name": app_name,
        "files": {
            "app.py": app_py,
            "requirements.txt": requirements_txt,
            "templates/index.html": index_html,
        },
    })


@app.route('/api/save-and-preview', methods=['POST'])
def save_and_preview():
    """Save project to disk and start preview server."""
    data = request.get_json()
    app_name = data.get('app_name', 'My App')
    profile_data = session.get('profile')
    answered = session.get('answered', {})
    
    if not profile_data:
        return jsonify({"error": "No profile"}), 400
    
    profile = Profile.from_dict(profile_data)
    
    # Generate code
    app_py = generator.generate_app_py(app_name, answered)
    requirements_txt = generator.generate_requirements_txt(answered)
    index_html = generator.generate_index_html(app_name, answered)
    
    # Save to filesystem
    project_path = manager.create_project(
        app_name=app_name,
        description=profile.description,
        answers=answered,
        app_py=app_py,
        requirements_txt=requirements_txt,
        index_html=index_html,
    )
    
    # TODO: Start preview server in subprocess
    
    return jsonify({
        "success": True,
        "project_path": str(project_path),
        "preview_url": f"file:///{project_path}",
    })


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


@app.route('/api/projects')
def list_projects():
    """Get all saved projects."""
    projects = manager.get_projects()
    return jsonify(projects)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
