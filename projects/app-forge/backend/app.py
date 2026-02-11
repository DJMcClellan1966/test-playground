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
from component_assembler import can_assemble, detect_components
from build_memory import memory, BuildRecord
from modular_kernel import builder

# Import classifier (optional ML module)
try:
    from classifier import classifier
    ML_AVAILABLE = True
except ImportError:
    classifier = None
    ML_AVAILABLE = False

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

    # If data_app features dominate, the actual path is CRUD, not a game
    if "data_app" in features and scores[0][1] < 5:
        best_template = "crud"

    # Check if the component assembler can handle this (novel apps)
    assembled = False
    assembled_component = None
    REQUIRED_FEATURE_TEMPLATES = {"tictactoe", "hangman", "wordle", "calculator", "converter", "timer"}
    comps = detect_components(description)
    if comps and comps[0][0] >= 80 and best_template not in REQUIRED_FEATURE_TEMPLATES:
        assembled = True
        assembled_component = comps[0][1]["id"]
    
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
            "template": assembled_component if assembled else best_template,
            "features": feature_summary,
            "assembled": assembled,
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
    
    # Detect template for history
    best_template, features, _ = match_template(profile.description)
    
    # Generate code — pass description for domain-aware models
    app_name = request.get_json().get('app_name', 'My App')
    app_py = generator.generate_app_py(app_name, answered, profile.description)
    requirements_txt = generator.generate_requirements_txt(answered)
    index_html = generator.generate_index_html(app_name, answered, profile.description)
    
    # Auto-save to build history
    try:
        import hashlib
        code_hash = hashlib.md5(app_py.encode()).hexdigest()[:16]
        record = BuildRecord(
            description=profile.description,
            template_used=best_template,
            features={k: f.value for k, f in features.items()},
            answers=answered,
            generated_code_hash=code_hash,
            status='pending',
        )
        session['current_build_id'] = memory.save(record)
        session.modified = True
    except Exception as e:
        print(f"Failed to save build history: {e}")
    
    # Auto-start live preview server
    result = preview.start(app_py, requirements_txt, index_html)
    preview_url = result.get('preview_url', '') if result.get('success') else ''
    preview_error = result.get('error', '') if not result.get('success') else ''
    
    return jsonify({
        "tech_stack": {**tech_stack.to_dict(), "template": best_template},
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
        
        # Mark build as accepted in history
        build_id = session.get('current_build_id')
        if build_id:
            try:
                memory.mark_status(build_id, 'accepted')
            except Exception:
                pass
        
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


# ============ Build Memory API ============

@app.route('/api/builds', methods=['GET'])
def list_builds():
    """Get recent builds with optional status filter."""
    status = request.args.get('status')  # 'good', 'bad', or None for all
    limit = request.args.get('limit', 50, type=int)
    
    if status == 'good':
        builds = memory.get_good_builds(limit)
    elif status == 'bad':
        builds = memory.get_bad_builds(limit)
    else:
        # Get both
        good = memory.get_good_builds(limit // 2)
        bad = memory.get_bad_builds(limit // 2)
        builds = sorted(good + bad, key=lambda b: b.updated_at, reverse=True)[:limit]
    
    return jsonify([{
        "id": b.id,
        "description": b.description,
        "template_used": b.template_used,
        "components": b.components,
        "status": b.status,
        "rejection_reason": b.rejection_reason,
        "revision": b.revision,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
    } for b in builds])


@app.route('/api/builds/<build_id>')
def get_build(build_id):
    """Get a specific build."""
    build = memory.get_build(build_id)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify({
        "id": build.id,
        "description": build.description,
        "template_used": build.template_used,
        "components": build.components,
        "features": build.features,
        "answers": build.answers,
        "status": build.status,
        "rejection_reason": build.rejection_reason,
        "revision": build.revision,
        "parent_id": build.parent_id,
        "user_edits": build.user_edits,
        "created_at": build.created_at,
        "updated_at": build.updated_at,
    })


@app.route('/api/builds/<build_id>/accept', methods=['POST'])
def accept_build(build_id):
    """Mark a build as accepted (move to Good store)."""
    build = memory.accept_build(build_id)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify({
        "success": True,
        "message": "Build accepted and moved to Good store",
        "build_id": build.id,
    })


@app.route('/api/builds/<build_id>/reject', methods=['POST'])
def reject_build(build_id):
    """Mark a build as rejected (move to Bad store with reason)."""
    data = request.get_json() or {}
    reason = data.get('reason', 'Not specified')
    
    build = memory.reject_build(build_id, reason)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify({
        "success": True,
        "message": "Build rejected and moved to Bad store",
        "build_id": build.id,
        "reason": reason,
    })


@app.route('/api/builds/<build_id>/delete', methods=['DELETE'])
def delete_build(build_id):
    """Soft delete a build with reason."""
    data = request.get_json() or {}
    reason = data.get('reason', 'User deleted')
    
    build = memory.delete_build(build_id, reason)
    if not build:
        return jsonify({"error": "Build not found"}), 404
    return jsonify({
        "success": True,
        "message": "Build marked as deleted",
        "build_id": build.id,
        "reason": reason,
    })


@app.route('/api/builds/<build_id>/revise', methods=['POST'])
def revise_build(build_id):
    """Create a new revision of an existing build."""
    data = request.get_json() or {}
    edits = data.get('edits', {})  # Dict of what the user changed
    
    new_build = memory.create_revision(build_id, edits)
    if not new_build:
        return jsonify({"error": "Original build not found"}), 404
    return jsonify({
        "success": True,
        "message": f"Created revision {new_build.revision}",
        "build_id": new_build.id,
        "revision": new_build.revision,
        "parent_id": new_build.parent_id,
    })


@app.route('/api/builds/<build_id>/revisions')
def get_revisions(build_id):
    """Get the full revision chain for a build."""
    chain = memory.get_revision_chain(build_id)
    return jsonify([{
        "id": b.id,
        "revision": b.revision,
        "status": b.status,
        "user_edits": b.user_edits,
        "created_at": b.created_at,
    } for b in chain])


@app.route('/api/builds/stats')
def get_build_stats():
    """Get statistics about builds."""
    return jsonify(memory.get_stats())


# ============ Modular Kernel API ============

@app.route('/api/compose', methods=['POST'])
def compose_modular():
    """Use modular kernel + component architecture to compose an app."""
    data = request.get_json()
    description = data.get('description', '').strip()
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    result = builder.compose(description)
    return jsonify(result.to_dict())


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """Get recommendations based on description and build history."""
    data = request.get_json()
    description = data.get('description', '').strip()
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    recommendations = builder.get_recommendations(description)
    return jsonify(recommendations)


@app.route('/api/kernels')
def list_kernels():
    """List available kernels."""
    from modular_kernel import KERNELS
    return jsonify([{
        "id": k.id,
        "name": k.name,
        "description": k.description,
        "provides": k.provides,
    } for k in KERNELS.values()])


@app.route('/api/components')
def list_components():
    """List available component slots."""
    from modular_kernel import COMPONENT_SLOTS
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "category": c.category,
        "requires": c.requires,
        "provides": c.provides,
    } for c in COMPONENT_SLOTS.values()])


# ============ ML Classifier API ============

@app.route('/api/ml/status')
def ml_status():
    """Get ML classifier training status."""
    if not ML_AVAILABLE or not classifier:
        return jsonify({
            "ml_available": False,
            "error": "scikit-learn not installed or classifier not loaded",
        })
    return jsonify(classifier.status())


@app.route('/api/ml/train', methods=['POST'])
def ml_train():
    """Train all ML classifiers on Good store data."""
    if not ML_AVAILABLE or not classifier:
        return jsonify({
            "success": False,
            "error": "scikit-learn not installed",
        }), 400
    
    data = request.get_json() or {}
    force = data.get('force', False)
    
    results = classifier.train_all(force=force)
    return jsonify(results)


@app.route('/api/ml/predict', methods=['POST'])
def ml_predict():
    """Get ML predictions for a description."""
    if not ML_AVAILABLE or not classifier:
        return jsonify({
            "ml_available": False,
            "error": "ML not available",
        })
    
    data = request.get_json()
    description = data.get('description', '').strip()
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    predictions = classifier.predict(description)
    return jsonify(predictions)


# =============================================================================
# Build History API
# =============================================================================

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get build history."""
    try:
        builds = memory.get_recent(limit=50)
        return jsonify({
            "builds": [
                {
                    "id": b.id,
                    "description": b.description,
                    "template_used": b.template_used,
                    "status": b.status,
                    "created_at": b.created_at,
                    "revision": b.revision,
                }
                for b in builds
            ]
        })
    except Exception as e:
        return jsonify({"builds": [], "error": str(e)})


@app.route('/api/history/save', methods=['POST'])
def save_to_history():
    """Save a build to history."""
    data = request.get_json()
    description = data.get('description', '')
    template = data.get('template', 'unknown')
    status = data.get('status', 'pending')
    reason = data.get('reason', '')
    
    try:
        record = BuildRecord(
            description=description,
            template_used=template,
            status=status,
            rejection_reason=reason,
            answers=session.get('answered', {}),
        )
        build_id = memory.save(record)
        return jsonify({"success": True, "id": build_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/history/<int:build_id>', methods=['DELETE'])
def delete_from_history(build_id):
    """Delete a build from history."""
    try:
        memory.mark_status(build_id, 'deleted', 'User deleted')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        # Clean up preview server on exit
        preview.stop()
