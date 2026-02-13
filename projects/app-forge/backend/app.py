# Connection Monitor integration
try:
    from connection_monitor import ConnectionMonitor
    CONNECTION_MONITOR_ENABLED = True
    connection_monitor = ConnectionMonitor()
except ImportError:
    CONNECTION_MONITOR_ENABLED = False
    connection_monitor = None
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

# Dynamic corpus/model modules
try:
    from corpus_search import CorpusSearch
    from template_filler import TemplateFiller
    from dynamic_model import DynamicModelBuilder
    CORPUS_MODULES_ENABLED = True
except ImportError:
    CORPUS_MODULES_ENABLED = False
    CorpusSearch = None
    TemplateFiller = None
    DynamicModelBuilder = None

# Try to use neural-enhanced matching (hybrid router)
try:
    from template_registry import match_template_neural
    # Use neural matcher as default if available
    smart_match_template = match_template_neural
    NEURAL_MATCHING = True
except ImportError:
    # Fall back to traditional matching
    smart_match_template = match_template
    NEURAL_MATCHING = False
from component_assembler import can_assemble, detect_components
from build_memory import memory, BuildRecord
from modular_kernel import builder
from regex_generator import RegexPatternGenerator

# User preference learning (AI-free)
try:
    from user_prefs import record_build as record_user_pref, get_prefs
    USER_PREFS_ENABLED = True
except ImportError:
    USER_PREFS_ENABLED = False
    def record_user_pref(*args, **kwargs): pass
    def get_prefs(): return None

# Universal Kernel memory integration
try:
    from kernel_memory import (
        app_memory, remember_build, suggest_from_memory, learn,
        get_memory_stats
    )
    KERNEL_MEMORY_ENABLED = True
except ImportError:
    KERNEL_MEMORY_ENABLED = False
    app_memory = None
    def remember_build(*args, **kwargs): pass
    def suggest_from_memory(desc): return None
    def learn(*args, **kwargs): pass
    def get_memory_stats(): return {}

# Imagination system - creative template exploration
try:
    from imagination import creative_system
    IMAGINATION_ENABLED = True
except ImportError:
    IMAGINATION_ENABLED = False
    creative_system = None

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

# Initialize pattern generator for learning loop
pattern_generator = RegexPatternGenerator()

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

# Example endpoint: Dynamic template filling and model building
@app.route('/api/dynamic_fill', methods=['POST'])
def dynamic_fill():
    """Fill a template using corpus search and build a model dynamically."""
    if not CORPUS_MODULES_ENABLED:
        return jsonify({"error": "Corpus/template/model modules not available"}), 500
    data = request.get_json() or {}
    template = data.get('template', {})
    user_input = data.get('user_input', '')
    corpus_dirs = data.get('corpus_dirs', ["../patterns", "../docs"])
    # Fill template
    tf = TemplateFiller(corpus_dirs)
    filled = tf.fill_template(template, user_input)
    # Build model
    dmb = DynamicModelBuilder()
    model = dmb.build_model(filled)
    return jsonify({
        "filled_template": filled,
        "model": model
    })

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
    
    # NEW: Check kernel memory for similar past builds
    memory_suggestion = None
    if KERNEL_MEMORY_ENABLED:
        try:
            result = suggest_from_memory(description)
            if result:
                memory_suggestion = {
                    'template_id': result[0],
                    'confidence': result[1],
                    'source': 'memory'
                }
        except Exception as e:
            print(f"Warning: Memory lookup failed: {e}")
    
    # Detect what template will be used (neural-enhanced matching)
    best_template, features, scores = smart_match_template(description)
    feature_summary = {k: f.value for k, f in features.items()}

    # If memory has high confidence, use that instead
    if memory_suggestion and memory_suggestion['confidence'] >= 0.8:
        best_template = memory_suggestion['template_id']

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
    session['template_id'] = assembled_component if assembled else best_template
    session.modified = True
    
    # Get remaining questions after inference (including contextual)
    try:
        from smartq import get_all_questions_with_context
        remaining = get_all_questions_with_context(description, session['template_id'], inferred)
    except ImportError:
        # Fallback to base questions
        remaining = get_relevant_questions(inferred)
    
    next_q = remaining[0] if remaining else None
    
    # NEW: Creative exploration via imagination system
    creative_insights = None
    if IMAGINATION_ENABLED and creative_system:
        try:
            exploration = creative_system.explore_idea(description)
            exp = exploration.get('exploration', {})
            if exp.get('tensions_found', 0) > 0 or exp.get('bridges_found', 0) > 5:
                creative_insights = {
                    'tensions': exp.get('tensions_found', 0),
                    'bridges': exp.get('bridges_found', 0),
                    'resonances': exp.get('templates_resonated', 0),
                    'hybrid_proposal': exploration.get('hybrid_proposal'),
                    'questions': exploration.get('questions', [])[:2],
                    'suggestions': exploration.get('suggestions', [])[:2],
                }
        except Exception as e:
            print(f"Warning: Imagination exploration failed: {e}")

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
        # NEW: Include memory-based suggestion if available
        "memory_suggestion": memory_suggestion,
        "kernel_memory_enabled": KERNEL_MEMORY_ENABLED,
        # NEW: Creative exploration insights
        "creative_insights": creative_insights,
        "imagination_enabled": IMAGINATION_ENABLED,
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
    
    # Check if done (using contextual questions if available)
    profile = session.get('profile', {})
    description = profile.get('description', '')
    template_id = session.get('template_id', 'generic')
    
    try:
        from smartq import get_all_questions_with_context
        remaining = get_all_questions_with_context(description, template_id, answered)
    except ImportError:
        remaining = get_relevant_questions(answered)
    
    if len(remaining) == 0:
        return jsonify({
            "complete": True,
            "answered": answered,
            "total_questions": 0,
        })
    
    # Get next question
    next_q = remaining[0] if remaining else None
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
    
    # Detect template for history (neural-enhanced)
    best_template, features, scores = smart_match_template(profile.description)
    if CONNECTION_MONITOR_ENABLED:
        connection_monitor.log_template_match(best_template, {k: f.value for k, f in features.items()}, scores[0][1])
        # Feedback loop: analyze after match
        analysis = connection_monitor.analyze()
        unused_features = analysis.get("unused_features", [])
        hybrid_suggestions = analysis.get("hybrid_suggestions", [])
        # If unused features exist, surface them in response
        if unused_features:
            print(f"Unused features detected: {unused_features}")
        # If hybrid suggestions exist, adapt template selection
        if hybrid_suggestions:
            print(f"Hybrid template suggestions: {hybrid_suggestions}")
            # Optionally, select a hybrid template if confidence is high
            # (Placeholder logic)
            best_template = hybrid_suggestions[0] if hybrid_suggestions else best_template
    
    # Generate code — pass description for domain-aware models
    app_name = request.get_json().get('app_name', 'My App')
    if CONNECTION_MONITOR_ENABLED:
        connection_monitor.log_interaction("generator", "generate_app_py", {"app_name": app_name, "answers": answered})
    # Endpoint: Retrieve connection monitor analysis
    @app.route('/api/connection_analysis', methods=['GET'])
    def connection_analysis():
        if not CONNECTION_MONITOR_ENABLED:
            return jsonify({"error": "Connection monitor not available"}), 500
        summary = connection_monitor.analyze()
        return jsonify(summary)
    
    # Check if this is a data app requiring multi-file generation
    needs_db = answered.get('has_data', False)
    if needs_db:
        files = generator.generate_data_app_files(app_name, answered, profile.description)
        app_py = files.get('app.py', '')
        requirements_txt = files.get('requirements.txt', '')
        index_html = files.get('templates/index.html', '')
    else:
        app_py = generator.generate_app_py(app_name, answered, profile.description)
        requirements_txt = generator.generate_requirements_txt(answered)
        index_html = generator.generate_index_html(app_name, answered, profile.description)
        files = {
            "app.py": app_py,
            "requirements.txt": requirements_txt,
            "templates/index.html": index_html,
        }
    
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
    
    # Record user preference (AI-free learning)
    if USER_PREFS_ENABLED:
        record_user_pref(best_template, features, profile.description)
    
    # Auto-start live preview server (pass all files for multi-file apps)
    result = preview.start(files)
    preview_url = result.get('preview_url', '') if result.get('success') else ''
    preview_error = result.get('error', '') if not result.get('success') else ''
    
    return jsonify({
        "tech_stack": {
            **tech_stack.to_dict(), 
            "template": best_template,
            "build_id": session.get('current_build_id')
        },
        "app_name": app_name,
        "files": files,
        "preview_url": preview_url,
        "preview_error": preview_error,
        "connection_monitor": {
            "unused_features": unused_features if CONNECTION_MONITOR_ENABLED else [],
            "hybrid_suggestions": hybrid_suggestions if CONNECTION_MONITOR_ENABLED else []
        }
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


@app.route('/api/download/<build_id>', methods=['GET'])
def download_build(build_id):
    """Download a build as a zip file."""
    import zipfile
    import io
    from flask import send_file
    
    include_deployment = request.args.get('deployment', 'false').lower() == 'true'
    
    try:
        # Get build from memory
        build = memory.get_build(build_id)
        if not build:
            return jsonify({"error": "Build not found"}), 404
        
        # Regenerate files from build
        profile_data = session.get('profile')
        answered = session.get('answered', {})
        
        if profile_data and answered:
            profile = Profile.from_dict(profile_data)
            app_name = build.title or 'My App'
            needs_db = answered.get('has_data', False)
            
            if needs_db:
                files = generator.generate_data_app_files(app_name, answered, profile.description)
            else:
                files = {
                    "app.py": generator.generate_app_py(app_name, answered, profile.description),
                    "requirements.txt": generator.generate_requirements_txt(answered),
                    "templates/index.html": generator.generate_index_html(app_name, answered, profile.description)
                }
            
            # Add deployment files if requested
            if include_deployment:
                deployment_files = generator.generate_deployment_files(app_name)
                files.update(deployment_files)
        else:
            # Fallback: just HTML file from build
            files = {"index.html": build.code}
        
        # Create zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all generated files
            for filepath, content in files.items():
                zip_file.writestr(filepath, content)
            
            # Add README if not already present
            if 'README.md' not in files:
                readme = f"""# {build.title}

{build.description}

## Generated by App Forge
Template: {build.template}
Created: {build.timestamp}

## How to Use
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python app.py`
3. Open your browser to http://127.0.0.1:5000

## Deployment
This package includes deployment configurations for:
- Docker (Dockerfile, docker-compose.yml)
- Vercel (vercel.json)
- Railway (railway.json)
- Render (render.yaml)
"""
                zip_file.writestr('README.md', readme)
        
        # Prepare download
        zip_buffer.seek(0)
        filename = f"{build.title.replace(' ', '-').lower()}.zip"
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
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

    best_id, features, scores = smart_match_template(description)
    return jsonify({
        "template": best_id,
        "features": {k: {"value": f.value, "confidence": f.confidence}
                     for k, f in features.items()},
        "scores": [{"id": tid, "score": s} for tid, s in scores[:5]],
        "explanation": explain_match(description),
        "neural_matching": NEURAL_MATCHING,
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
    
    # Learning loop: teach the pattern generator about this successful build
    try:
        pattern_generator.learn_from_prompt(build.description, build.template_used)
    except Exception as e:
        print(f"Warning: Failed to learn from build {build_id}: {e}")
    
    # NEW: Remember in Universal Kernel memory for better future decisions
    if KERNEL_MEMORY_ENABLED:
        try:
            # Extract features from answers
            features = []
            if build.answers:
                if build.answers.get('has_data'):
                    features.append('database')
                if build.answers.get('needs_auth'):
                    features.append('auth')
                if build.answers.get('search'):
                    features.append('search')
                if build.answers.get('export'):
                    features.append('export')
                if build.answers.get('realtime'):
                    features.append('realtime')
            
            # Remember this successful build
            remember_build(
                description=build.description,
                template_id=build.template_used,
                features=features,
                success=True
            )
            
            # Learn user preferences
            if build.tech_stack:
                for tech in build.tech_stack:
                    learn('framework', tech)
        except Exception as e:
            print(f"Warning: Kernel memory error: {e}")
    
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
# Kernel Memory API (Universal Kernel Integration)
# =============================================================================

@app.route('/api/memory/status')
def memory_status():
    """Get kernel memory statistics."""
    if not KERNEL_MEMORY_ENABLED:
        return jsonify({
            "kernel_memory_available": False,
            "error": "Universal Kernel not integrated",
        })
    
    stats = get_memory_stats()
    return jsonify({
        "kernel_memory_available": True,
        **stats
    })


@app.route('/api/memory/suggest', methods=['POST'])
def memory_suggest():
    """Get template suggestion from memory."""
    if not KERNEL_MEMORY_ENABLED:
        return jsonify({
            "suggestion": None,
            "error": "Kernel memory not available",
        })
    
    data = request.get_json()
    description = data.get('description', '').strip()
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    result = suggest_from_memory(description)
    if result:
        return jsonify({
            "suggestion": {
                "template_id": result[0],
                "confidence": result[1],
            }
        })
    return jsonify({"suggestion": None})


@app.route('/api/memory/similar', methods=['POST'])
def memory_similar():
    """Find similar past builds."""
    if not KERNEL_MEMORY_ENABLED or not app_memory:
        return jsonify({
            "similar_builds": [],
            "error": "Kernel memory not available",
        })
    
    data = request.get_json()
    description = data.get('description', '').strip()
    n = data.get('limit', 5)
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    similar = app_memory.recall_similar_builds(description, n=n)
    return jsonify({
        "similar_builds": [
            {
                "description": b.description,
                "template_id": b.template_id,
                "features": b.features,
                "success": b.success,
            }
            for b in similar
        ]
    })


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


@app.route('/api/user-stats', methods=['GET'])
def get_user_stats():
    """Get user preference learning statistics."""
    if not USER_PREFS_ENABLED:
        return jsonify({"enabled": False, "message": "User preference learning not available"})
    
    prefs = get_prefs()
    stats = prefs.get_stats()
    
    return jsonify({
        "enabled": True,
        "total_builds": stats.get('total_builds', 0),
        "template_counts": stats.get('template_counts', {}),
        "most_used_template": stats.get('most_used'),
        "feature_preferences": stats.get('feature_prefs', {}),
    })


@app.route('/api/user-stats/clear', methods=['POST'])
def clear_user_stats():
    """Clear user preference learning history."""
    if not USER_PREFS_ENABLED:
        return jsonify({"success": False, "error": "User preference learning not available"})
    
    prefs = get_prefs()
    prefs.clear()
    return jsonify({"success": True, "message": "User preferences cleared"})


# =============================================================================
# AI-Assist API (NRI - Numerical Resonance Intelligence)
# =============================================================================

@app.route('/api/ai-assist/status')
def ai_assist_status():
    """Check if AI-assist (NRI) is available."""
    try:
        from ai_assist import describe_capabilities
        return jsonify(describe_capabilities())
    except ImportError:
        return jsonify({
            "enabled": False,
            "error": "AI-assist module not available"
        })


@app.route('/api/ai-assist/suggest', methods=['POST'])
def ai_assist_suggest():
    """Get AI-assisted template suggestions using NRI."""
    try:
        from ai_assist import ai_assist_suggestions
    except ImportError:
        return jsonify({
            "suggestions": [],
            "error": "AI-assist module not available"
        })
    
    data = request.get_json()
    description = data.get('description', '').strip()
    top_k = data.get('top_k', 3)
    
    if not description:
        return jsonify({"error": "No description provided"}), 400
    
    suggestions = ai_assist_suggestions(description, top_k=top_k)
    return jsonify({
        "description": description,
        "suggestions": suggestions,
        "method": "NRI (Numerical Resonance Intelligence)"
    })


@app.route('/api/ai-assist/similarity', methods=['POST'])
def ai_assist_similarity():
    """Compute NRI similarity between two texts."""
    try:
        from ai_assist import get_nri
        nri = get_nri()
    except ImportError:
        return jsonify({
            "error": "AI-assist module not available"
        }), 400
    
    data = request.get_json()
    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    
    if not text1 or not text2:
        return jsonify({"error": "Both text1 and text2 are required"}), 400
    
    primes1 = nri.encode_to_primes(text1.lower())
    primes2 = nri.encode_to_primes(text2.lower())
    resonance = nri.compute_resonance(primes1, primes2)
    
    return jsonify({
        "text1": text1,
        "text2": text2,
        "similarity": round(resonance, 4),
        "similarity_percent": f"{resonance:.1%}",
        "method": "NRI harmonic resonance"
    })


# =============================================================================
# Pattern Generator API
# =============================================================================

@app.route('/api/patterns/status')
def patterns_status():
    """Get pattern generator status."""
    try:
        from regex_generator import RegexPatternGenerator
        generator = RegexPatternGenerator()
        all_patterns = generator.generate_all_patterns()
        return jsonify({
            "enabled": True,
            "templates_analyzed": len(all_patterns),
            "total_patterns": sum(len(p) for p in all_patterns.values()),
            "learned_templates": len(generator.learned_patterns),
            "synonyms_available": True
        })
    except ImportError:
        return jsonify({"enabled": False, "error": "Pattern generator not available"})


@app.route('/api/patterns/for-template/<template_id>')
def patterns_for_template(template_id):
    """Get generated patterns for a specific template."""
    try:
        from regex_generator import RegexPatternGenerator
        from template_registry import TEMPLATE_REGISTRY
        
        generator = RegexPatternGenerator()
        
        # Find template
        template = None
        for t in TEMPLATE_REGISTRY:
            if t.id == template_id:
                template = t
                break
        
        if not template:
            return jsonify({"error": f"Template '{template_id}' not found"}), 404
        
        patterns = generator.generate_patterns_from_template(
            template.id, template.name, template.tags
        )
        
        return jsonify({
            "template_id": template_id,
            "template_name": template.name,
            "patterns": [
                {"pattern": p.pattern, "source": p.source, "confidence": p.confidence}
                for p in sorted(patterns, key=lambda x: -x.confidence)
            ]
        })
    except ImportError as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patterns/suggest', methods=['POST'])
def patterns_suggest():
    """Suggest patterns to match a prompt to a template."""
    try:
        from regex_generator import RegexPatternGenerator
    except ImportError:
        return jsonify({"error": "Pattern generator not available"}), 500
    
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    template_id = data.get('template_id', '')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    generator = RegexPatternGenerator()
    suggestions = generator.suggest_patterns_for_prompt(prompt, template_id)
    
    return jsonify({
        "prompt": prompt,
        "target_template": template_id or "(any)",
        "suggested_patterns": suggestions
    })


@app.route('/api/patterns/detect-gaps', methods=['POST'])
def patterns_detect_gaps():
    """Detect routing gaps for a list of test prompts."""
    try:
        from regex_generator import RegexPatternGenerator
    except ImportError:
        return jsonify({"error": "Pattern generator not available"}), 500
    
    data = request.get_json()
    prompts = data.get('prompts', [])
    
    if not prompts:
        return jsonify({"error": "Provide a list of prompts to test"}), 400
    
    generator = RegexPatternGenerator()
    gaps = generator.detect_gaps(prompts)
    
    return jsonify({
        "tested": len(prompts),
        "gaps_found": len(gaps),
        "gaps": [
            {
                "prompt": g.prompt,
                "fell_to": g.fell_to,
                "matched_template": g.matched_template,
                "suggested_patterns": g.suggested_patterns
            }
            for g in gaps
        ]
    })


@app.route('/api/patterns/learn', methods=['POST'])
def patterns_learn():
    """Learn a successful prompt → template mapping."""
    try:
        from regex_generator import RegexPatternGenerator
    except ImportError:
        return jsonify({"error": "Pattern generator not available"}), 500
    
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    template_id = data.get('template_id', '').strip()
    
    if not prompt or not template_id:
        return jsonify({"error": "Both prompt and template_id are required"}), 400
    
    generator = RegexPatternGenerator()
    generator.learn_from_prompt(prompt, template_id)
    
    return jsonify({
        "success": True,
        "learned": {"prompt": prompt, "template_id": template_id}
    })


@app.route('/api/patterns/export')
def patterns_export():
    """Export auto-generated SEMANTIC_ROUTES code."""
    try:
        from regex_generator import RegexPatternGenerator
    except ImportError:
        return jsonify({"error": "Pattern generator not available"}), 500
    
    generator = RegexPatternGenerator()
    code = generator.to_semantic_routes_format()
    
    return jsonify({
        "format": "python",
        "code": code
    })


if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000)
    finally:
        # Clean up preview server on exit
        preview.stop()
