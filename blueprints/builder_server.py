"""
Builder Dev Server - Makes the Visual Editor Actually Work

This server provides:
1. API endpoints for the visual editor to write files
2. File watching with auto-regeneration
3. Live preview of generated projects
4. Hot reload on changes

Run with: python builder_server.py
Then open: http://localhost:5000
"""

import os
import sys
import json
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import socketserver

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_scaffold import IntelligentScaffolder
from contracts import Contract, Field, ContractRegistry
from blocks import BLOCKS, BlockAssembler
from beyond_belief import CrossLanguageSynthesizer, LANGUAGE_TARGETS
from advisor_ai import get_advice, quick_ask, check_ollama
from logic_advisor import analyze_state, ask_question
from csp_constraint_solver import (
    ArchitectureCSP, validate_block_configuration, 
    suggest_blocks_for_requirements, BLOCK_SPECS
)

# Configuration
PORT = 8088
PROJECT_DIR = Path(__file__).parent / "workspace"
STATIC_DIR = Path(__file__).parent


class BuilderAPIHandler(SimpleHTTPRequestHandler):
    """HTTP handler with API endpoints for the builder."""
    
    def __init__(self, *args, **kwargs):
        self.project_dir = PROJECT_DIR
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        
        if parsed.path == '/':
            # Serve the visual editor
            self.path = '/builder.html'
            return super().do_GET()
        
        elif parsed.path == '/api/blocks':
            self.send_json(self.get_blocks())
        
        elif parsed.path == '/api/project':
            self.send_json(self.get_project_structure())
        
        elif parsed.path == '/api/templates':
            self.send_json(self.get_templates())
        
        elif parsed.path.startswith('/api/file'):
            params = parse_qs(parsed.query)
            filepath = params.get('path', [''])[0]
            self.send_json(self.read_file(filepath))
        
        elif parsed.path == '/api/browse':
            params = parse_qs(parsed.query)
            dir_path = params.get('path', [''])[0]
            self.send_json(self.browse_directory(dir_path))
        
        elif parsed.path == '/api/drives':
            self.send_json(self.get_drives())
        
        elif parsed.path == '/api/output-path':
            self.send_json({'path': str(self.project_dir)})
        
        elif parsed.path.startswith('/preview/'):
            # Serve files from the generated project
            file_path = parsed.path.replace('/preview/', '')
            self.serve_preview_file(file_path)
        
        else:
            return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}
        
        if parsed.path == '/api/generate':
            result = self.generate_project(data)
            self.send_json(result)
        
        elif parsed.path == '/api/save':
            result = self.save_file(data)
            self.send_json(result)
        
        elif parsed.path == '/api/create-contract':
            result = self.create_contract(data)
            self.send_json(result)
        
        elif parsed.path == '/api/scaffold':
            result = self.scaffold_from_blocks(data)
            self.send_json(result)
        
        elif parsed.path == '/api/ask':
            result = self.ask_ai(data)
            self.send_json(result)
        
        elif parsed.path == '/api/logic/analyze':
            result = self.logic_analyze(data)
            self.send_json(result)
        
        elif parsed.path == '/api/logic/ask':
            result = self.logic_ask(data)
            self.send_json(result)
        
        elif parsed.path == '/api/csp/validate':
            result = self.csp_validate(data)
            self.send_json(result)
        
        elif parsed.path == '/api/csp/solve':
            result = self.csp_solve(data)
            self.send_json(result)
        
        elif parsed.path == '/api/set-output':
            result = self.set_output_path(data)
            self.send_json(result)
        
        else:
            self.send_error(404, "API endpoint not found")
    
    def send_cors_headers(self):
        """Add CORS headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def send_json(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def browse_directory(self, path_str):
        """Browse a directory and return its contents."""
        import string
        
        # Default to desktop if no path given
        if not path_str:
            path_str = os.path.expanduser("~/Desktop")
        
        path = Path(path_str)
        
        if not path.exists():
            return {'error': f'Path does not exist: {path_str}'}
        
        if not path.is_dir():
            return {'error': f'Not a directory: {path_str}'}
        
        items = []
        try:
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    items.append({
                        'name': item.name,
                        'path': str(item),
                        'is_dir': item.is_dir(),
                        'size': item.stat().st_size if item.is_file() else None,
                    })
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            return {'error': f'Permission denied: {path_str}'}
        
        # Get parent path
        parent = str(path.parent) if path.parent != path else None
        
        return {
            'path': str(path),
            'parent': parent,
            'items': items,
        }
    
    def get_drives(self):
        """Get available drives (Windows) or root directories."""
        import platform
        
        if platform.system() == 'Windows':
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append({
                        'name': f"{letter}:",
                        'path': drive,
                        'is_dir': True
                    })
            return {'drives': drives}
        else:
            # Unix - return common locations
            locations = [
                {'name': 'Home', 'path': os.path.expanduser('~'), 'is_dir': True},
                {'name': 'Root', 'path': '/', 'is_dir': True},
            ]
            return {'drives': locations}
    
    def set_output_path(self, data):
        """Set the output directory for generated projects."""
        new_path = data.get('path', '')
        
        if not new_path:
            return {'error': 'No path provided'}
        
        path = Path(new_path)
        
        # Create if doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.project_dir = path
            # Update global PROJECT_DIR
            global PROJECT_DIR
            PROJECT_DIR = path
            return {
                'success': True,
                'path': str(path),
                'message': f'Output path set to: {path}'
            }
        except Exception as e:
            return {'error': f'Could not set path: {e}'}
    
    def get_blocks(self):
        """Get all available blocks."""
        blocks = []
        for name, block in BLOCKS.items():
            # Infer category from block id prefix
            if name.startswith('auth'):
                category = 'auth'
            elif name.startswith('storage'):
                category = 'storage'
            elif name.startswith('sync'):
                category = 'sync'
            elif name.startswith('crud') or name.startswith('graphql'):
                category = 'api'
            else:
                category = 'feature'
            
            blocks.append({
                'id': name,
                'name': block.name,
                'category': category,
                'requires': [{'name': p.name, 'type': p.type} for p in block.requires],
                'provides': [{'name': p.name, 'type': p.type} for p in block.provides],
                'description': block.description,
            })
        return {'blocks': blocks}
    
    def get_project_structure(self):
        """Get current project file structure."""
        if not self.project_dir.exists():
            return {'files': [], 'exists': False}
        
        files = []
        for path in self.project_dir.rglob('*'):
            if path.is_file():
                rel_path = path.relative_to(self.project_dir)
                files.append({
                    'path': str(rel_path).replace('\\', '/'),
                    'size': path.stat().st_size,
                    'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                })
        
        return {'files': files, 'exists': True, 'root': str(self.project_dir)}
    
    def get_templates(self):
        """Get available project templates."""
        return {
            'templates': [
                {'id': 'api', 'name': 'REST API', 'description': 'Flask REST API with CRUD'},
                {'id': 'web', 'name': 'Web App', 'description': 'Full-stack web application'},
                {'id': 'cli', 'name': 'CLI Tool', 'description': 'Command-line application'},
            ]
        }
    
    def read_file(self, filepath):
        """Read a file from the project."""
        full_path = self.project_dir / filepath
        if not full_path.exists():
            return {'error': 'File not found', 'path': filepath}
        
        try:
            content = full_path.read_text(encoding='utf-8')
            return {'path': filepath, 'content': content}
        except Exception as e:
            return {'error': str(e), 'path': filepath}
    
    def save_file(self, data):
        """Save a file to the project."""
        filepath = data.get('path', '')
        content = data.get('content', '')
        
        if not filepath:
            return {'error': 'No path specified'}
        
        full_path = self.project_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            full_path.write_text(content, encoding='utf-8')
            return {'success': True, 'path': filepath}
        except Exception as e:
            return {'error': str(e)}
    
    def create_contract(self, data):
        """Create a contract and generate code."""
        name = data.get('name', 'Item')
        fields = data.get('fields', [])
        invariants = data.get('invariants', [])
        languages = data.get('languages', ['python', 'typescript'])
        
        # Create contract
        contract_fields = [
            Field(
                name=f['name'],
                type=f.get('type', 'string'),
                required=f.get('required', True),
                default=f.get('default'),
            )
            for f in fields
        ]
        
        contract = Contract(
            name=name,
            description=data.get('description', ''),
            fields=contract_fields,
            invariants=invariants,
        )
        
        # Generate code for each language
        synth = CrossLanguageSynthesizer(contract)
        generated = {}
        
        for lang in languages:
            if lang in LANGUAGE_TARGETS:
                code = synth.generate(lang)
                ext = LANGUAGE_TARGETS[lang].extension
                filename = f"{name.lower()}{ext}"
                
                # Save to project
                filepath = self.project_dir / "models" / lang / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(code, encoding='utf-8')
                
                generated[lang] = {
                    'path': f"models/{lang}/{filename}",
                    'code': code,
                }
        
        return {
            'success': True,
            'contract': name,
            'generated': generated,
        }
    
    def ask_ai(self, data):
        """Ask the local AI advisor a question."""
        question = data.get('question', '')
        context = data.get('context', '')
        
        if not question:
            return {'error': 'No question provided'}
        
        # Check if Ollama is running
        if not check_ollama():
            return {
                'success': False,
                'error': 'Local AI not available',
                'message': 'Start Ollama with: ollama serve',
                'fallback': self._get_fallback_advice(question)
            }
        
        # If asking about a project, use get_advice
        if any(word in question.lower() for word in ['build', 'create', 'make', 'need', 'blocks', 'project']):
            result = get_advice(question)
            return result
        else:
            # General question
            response = quick_ask(question)
            return {
                'success': True,
                'response': response
            }
    
    def _get_fallback_advice(self, question):
        """Provide basic advice without AI."""
        q = question.lower()
        
        if 'blog' in q or 'website' in q:
            return "For a blog/website, use: storage_json + crud_routes. Start with personal-website blueprint."
        elif 'todo' in q or 'task' in q:
            return "For todos/tasks, use: storage_sqlite + crud_routes + auth_basic. Start with task-manager blueprint."
        elif 'offline' in q:
            return "For offline support, add sync_crdt block. Requires storage_sqlite."
        elif 'auth' in q or 'login' in q:
            return "Add auth_basic block for login. Provides session management."
        else:
            return "Start with storage_sqlite + crud_routes for most apps. Run: python advisor_ai.py for interactive help."
    
    def logic_analyze(self, data):
        """Analyze state using deterministic logic advisor."""
        blocks = data.get('blocks', [])
        entities = data.get('entities', [])
        
        # Extract block types
        block_types = [b.get('type', b) if isinstance(b, dict) else b for b in blocks]
        
        # Run analysis
        result = analyze_state(block_types, entities)
        result['success'] = True
        return result
    
    def logic_ask(self, data):
        """Answer question using deterministic logic."""
        question = data.get('question', '')
        context = data.get('context', {})
        
        if not question:
            return {'success': False, 'error': 'No question provided'}
        
        # Get answer from logic advisor
        answer = ask_question(question, context)
        
        return {
            'success': True,
            'response': answer,
            'source': 'logic'  # Indicates this is rule-based, not AI
        }
    
    def csp_validate(self, data):
        """
        Validate block configuration using CSP constraint solver.
        
        Returns validation result with conflicts/suggestions if invalid.
        """
        blocks = data.get('blocks', [])
        requirements = data.get('requirements', {})
        
        # Extract block types
        block_types = [b.get('type', b) if isinstance(b, dict) else b for b in blocks]
        
        # Create CSP solver and add blocks
        solver = ArchitectureCSP()
        
        # Add requirements
        for k, v in requirements.items():
            solver.set_requirement(k, v)
        
        # Add blocks
        for block in block_types:
            # Map canonical block names to CSP block specs
            csp_block = self._map_to_csp_block(block)
            if csp_block:
                try:
                    solver.add_block(csp_block)
                except ValueError:
                    pass  # Unknown block, skip
        
        # Validate
        result = solver.validate()
        
        if result.valid:
            return {
                'success': True,
                'valid': True,
                'blocks': list(solver.selected_blocks),
                'capabilities': {k: v for k, v in result.solution.items() 
                               if k.startswith('cap_') and v},
                'derivation': solver.explain()
            }
        else:
            return {
                'success': True,
                'valid': False,
                'conflicts': result.conflict.explanation if result.conflict else 'Unknown conflict',
                'suggestions': result.conflict.suggestions if result.conflict else [],
                'derivation': solver.explain()
            }
    
    def csp_solve(self, data):
        """
        Solve for a valid configuration using CSP constraint propagation.
        
        Automatically adds required blocks to satisfy constraints.
        """
        blocks = data.get('blocks', [])
        requirements = data.get('requirements', {})
        
        # Extract block types
        block_types = [b.get('type', b) if isinstance(b, dict) else b for b in blocks]
        
        # Create CSP solver
        solver = ArchitectureCSP()
        
        # Add requirements
        for k, v in requirements.items():
            solver.set_requirement(k, v)
        
        # Add user-selected blocks
        for block in block_types:
            csp_block = self._map_to_csp_block(block)
            if csp_block:
                try:
                    solver.add_block(csp_block)
                except ValueError:
                    pass
        
        # Solve (auto-adds required blocks)
        result = solver.solve()
        
        if result.valid:
            # Compute what was auto-added
            original_blocks = set(self._map_to_csp_block(b) for b in block_types if self._map_to_csp_block(b))
            auto_added = solver.selected_blocks - original_blocks
            
            return {
                'success': True,
                'valid': True,
                'blocks': list(solver.selected_blocks),
                'autoAdded': list(auto_added),
                'capabilities': {k.replace('cap_', ''): v for k, v in result.solution.items() 
                               if k.startswith('cap_') and v},
                'derivation': solver.explain(),
                'requiredBlocks': list(solver.get_required_blocks())
            }
        else:
            return {
                'success': True,
                'valid': False,
                'conflicts': result.conflict.explanation if result.conflict else 'Unknown conflict',
                'suggestions': result.conflict.suggestions if result.conflict else [],
                'derivation': solver.explain()
            }
    
    def _map_to_csp_block(self, block_type):
        """Map visual editor block names to CSP block spec names."""
        # Direct matches
        if block_type in BLOCK_SPECS:
            return block_type
        
        # Common mappings
        mappings = {
            'json_storage': 'storage_json',
            'sqlite_storage': 'storage_sqlite',
            'sqlite': 'storage_sqlite',
            'json': 'storage_json',
            'auth': 'auth_basic',
            'basic_auth': 'auth_basic',
            'oauth': 'auth_oauth',
            'crdt': 'crdt_sync',
            'sync': 'crdt_sync',
            'crud': 'crud_routes',
            'routes': 'crud_routes',
            'flask': 'backend_flask',
            'fastapi': 'backend_fastapi',
            'ws': 'websocket',
        }
        
        return mappings.get(block_type)
    
    def scaffold_from_blocks(self, data):
        """Generate a full project from block configuration."""
        blocks = data.get('blocks', [])
        project_name = data.get('name', 'my_project')
        entities = data.get('entities', [])
        
        # Map block types to constraints
        constraints = set()
        for block in blocks:
            block_type = block.get('type', '')
            if 'auth' in block_type:
                constraints.add('needs_auth')
            if 'sqlite' in block_type or 'postgres' in block_type:
                constraints.add('needs_database')
            if 'crdt' in block_type:
                constraints.add('offline')
                constraints.add('sync')
            if 'websocket' in block_type:
                constraints.add('realtime')
            if 'crud' in block_type or 'graphql' in block_type:
                constraints.add('needs_api')
        
        # Generate project directory
        self.project_dir = Path(STATIC_DIR) / "workspace" / project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Use intelligent scaffolder with output directory
        scaffolder = IntelligentScaffolder(output_dir=str(self.project_dir))
        
        # Add constraints as requirements (e.g., "needs_auth" -> "authentication")
        requirement_list = list(constraints) if constraints else []
        if requirement_list:
            scaffolder.understand_requirements(requirement_list)
        
        # Select components based on constraints
        scaffolder.select_components()
        
        # Add entities using define_entities API
        if entities:
            entity_defs = []
            for entity in entities:
                entity_defs.append({
                    'name': entity.get('name', 'Item'),
                    'fields': entity.get('fields', []),
                })
            scaffolder.define_entities(entity_defs)
        
        try:
            files = scaffolder.generate_project()
            scaffolder.write_files(files)
            
            # Also generate block-specific code
            block_code = self._generate_block_code(blocks)
            
            # Save block code
            blocks_file = self.project_dir / "generated_blocks.py"
            blocks_file.write_text(block_code, encoding='utf-8')
            
            return {
                'success': True,
                'project': project_name,
                'path': str(self.project_dir),
                'files': list(files.keys()),
                'message': f"Project generated at {self.project_dir}",
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_block_code(self, blocks):
        """Generate combined code from selected blocks."""
        lines = [
            '"""',
            'Generated Code from Visual Block Editor',
            f'Generated at: {datetime.now().isoformat()}',
            '"""',
            '',
        ]
        
        for block in blocks:
            block_type = block.get('type', '')
            if block_type in BLOCKS:
                block_def = BLOCKS[block_type]
                lines.append(f'\n# ---- {block_def.name} ----')
                # code is a dict like {"flask": "..."}, get flask version
                if isinstance(block_def.code, dict):
                    code = block_def.code.get('flask', block_def.code.get(list(block_def.code.keys())[0] if block_def.code else '', ''))
                else:
                    code = block_def.code or ''
                lines.append(code)
        
        return '\n'.join(lines)
    
    def generate_project(self, data):
        """Generate a complete project from requirements."""
        requirements = data.get('requirements', [])
        entities = data.get('entities', [])
        name = data.get('name', 'generated_project')
        
        scaffolder = IntelligentScaffolder()
        
        for req in requirements:
            scaffolder.add_requirement(req)
        
        for entity in entities:
            scaffolder.define_entity(entity['name'], entity.get('fields', []))
        
        output_dir = self.project_dir / name
        result = scaffolder.generate_project(str(output_dir))
        
        return {
            'success': True,
            'path': str(output_dir),
            'files': result.get('files', []),
        }
    
    def serve_preview_file(self, file_path):
        """Serve a file from the generated project for preview."""
        full_path = self.project_dir / file_path
        
        if not full_path.exists():
            self.send_error(404, "File not found")
            return
        
        # Determine content type
        ext = full_path.suffix.lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.py': 'text/plain',
            '.ts': 'text/plain',
        }
        content_type = content_types.get(ext, 'text/plain')
        
        try:
            content = full_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads."""
    allow_reuse_address = True


def run_server(port=PORT, open_browser_flag=True):
    """Start the development server."""
    # Ensure workspace exists
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"""
================================================================
         Blueprint Builder Dev Server
================================================================

   Visual Editor:  http://localhost:{port}
   API Docs:       http://localhost:{port}/api
   Workspace:      {str(PROJECT_DIR)}

   Press Ctrl+C to stop

================================================================
""")
    
    server = ThreadedHTTPServer(('', port), BuilderAPIHandler)
    
    # Open browser (unless disabled)
    if open_browser_flag:
        def open_browser():
            time.sleep(0.5)
            webbrowser.open(f'http://localhost:{port}')
        
        threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Blueprint Builder Dev Server')
    parser.add_argument('--port', '-p', type=int, default=PORT, help='Port to run on')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    
    args = parser.parse_args()
    
    run_server(args.port, open_browser_flag=not args.no_browser)
