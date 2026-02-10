"""
Prompt Twin - Build a local context profile from your coding patterns
======================================================================

This tool:
1. Scans your projects to understand what you build and how
2. Maintains a prompt log you can add to over time
3. Provides context that AI agents can query for better understanding
4. Fetches GitHub profile data (repos, commits, READMEs)
5. Injects context into AI tools (Cursor, VS Code, Ollama)
6. Watches for changes and auto-updates profile
7. Tests completions with Ollama to measure context impact
8. Exposes MCP server for AI agent queries

Usage:
    python prompt_twin.py scan                    # Scan desktop for patterns
    python prompt_twin.py log "your prompt here"  # Add a prompt to history
    python prompt_twin.py context "question"      # Get relevant context
    python prompt_twin.py profile                 # Show your profile
    python prompt_twin.py export                  # Export profile to markdown
    python prompt_twin.py github <username>       # Fetch GitHub data
    python prompt_twin.py inject                  # Inject context into AI tools

Watch Mode & Automation:
    python prompt_twin.py watch [path] [interval] # Watch for changes (30s default)
    python prompt_twin.py hook [repo]             # Install git post-commit hook

Structured Profile:
    python prompt_twin.py structured              # Export structured JSON/YAML profile

Ollama Integration:
    python prompt_twin.py ollama "prompt" [model] # Test completion with context
    python prompt_twin.py analyze                 # LLM analysis of your patterns

MCP Server (for AI agents):
    python prompt_twin.py mcp [port]              # Start MCP server (default: 8765)

Configuration:
    python prompt_twin.py config                  # Show current config
    python prompt_twin.py config set KEY VALUE    # Set config value
    python prompt_twin.py health                  # Check all integrations

Profile Tracking:
    python prompt_twin.py snapshot [name]         # Save profile snapshot
    python prompt_twin.py snapshots               # List snapshots
    python prompt_twin.py diff [snapshot]         # Compare with snapshot
    python prompt_twin.py suggest [description]   # Get template suggestions

Feedback Loop (reality grounding):
    python prompt_twin.py feedback                # Show feedback summary
    python prompt_twin.py outcome "action" "success|failure" [error]
    python prompt_twin.py error "ErrorType" "message" [file]
    python prompt_twin.py correction "ai said" "user wanted"
    python prompt_twin.py nuanced <category> "description"
    python prompt_twin.py nuanced-summary

Nuanced Feedback Categories:
    naming         - AI misunderstood naming conventions
    deprecated     - Suggested deprecated pattern
    style          - Didn't match coding style
    complexity     - Over/under-engineered
    missing_context - Missed project-specific context
    wrong_tech     - Suggested wrong technology
    good           - AI got it right (positive feedback)
"""

import os
import sys
import json
import re
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import hashlib

# Configuration
DESKTOP = Path(os.environ.get('USERPROFILE', os.path.expanduser('~'))) / 'OneDrive/Desktop'
DATA_DIR = Path(__file__).parent / '.prompt_twin'
PROFILE_FILE = DATA_DIR / 'profile.json'
PROMPTS_FILE = DATA_DIR / 'prompts.jsonl'
FEEDBACK_FILE = DATA_DIR / 'feedback.jsonl'  # Reality feedback loop
EXPORT_FILE = DATA_DIR / 'context_for_ai.md'

# File patterns to scan
CODE_EXTENSIONS = {'.py', '.js', '.ts', '.cs', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', '.swift', '.kt'}
DOC_EXTENSIONS = {'.md', '.txt', '.rst'}
CONFIG_EXTENSIONS = {'.json', '.yaml', '.yml', '.toml', '.xml', '.ini'}

# Technology detection patterns
TECH_PATTERNS = {
    'Flask': [r'from flask import', r'Flask\(', r'@app\.route'],
    'FastAPI': [r'from fastapi import', r'FastAPI\(', r'@app\.(get|post|put|delete)'],
    'Django': [r'from django', r'INSTALLED_APPS', r'urlpatterns'],
    'React': [r'import React', r'from [\'"]react[\'"]', r'useState', r'useEffect'],
    'Vue': [r'from [\'"]vue[\'"]', r'createApp', r'<template>'],
    'MAUI': [r'Microsoft\.Maui', r'MauiProgram', r'\.xaml'],
    'Blazor': [r'@page', r'<Blazor', r'RenderFragment'],
    'SQLite': [r'sqlite3', r'\.db', r'SQLite'],
    'PostgreSQL': [r'psycopg2', r'postgres', r'PostgreSQL'],
    'MongoDB': [r'pymongo', r'mongoose', r'mongodb'],
    'Ollama': [r'ollama', r'localhost:11434'],
    'OpenAI': [r'openai', r'gpt-4', r'gpt-3'],
    'LangChain': [r'langchain', r'LLMChain'],
    'Semantic Kernel': [r'semantic_kernel', r'Microsoft\.SemanticKernel'],
    'Machine Learning': [r'sklearn', r'tensorflow', r'pytorch', r'torch', r'keras'],
    'RAG': [r'retrieval', r'embeddings', r'vector.*store', r'chromadb', r'qdrant'],
    'WebSocket': [r'websocket', r'socket\.io', r'SignalR'],
    'Auth': [r'jwt', r'oauth', r'authentication', r'bcrypt', r'password.*hash'],
}

# Project type patterns
PROJECT_TYPES = {
    'Web App': ['flask', 'fastapi', 'django', 'express', 'node'],
    'Mobile App': ['maui', 'xamarin', 'flutter', 'react-native', 'expo'],
    'Desktop App': ['electron', 'tauri', 'wpf', 'winforms'],
    'CLI Tool': ['argparse', 'click', 'typer', 'sys.argv'],
    'API Service': ['@app.route', '@app.get', 'endpoint', 'rest'],
    'ML/AI Project': ['model', 'train', 'predict', 'neural', 'llm'],
    'Data Pipeline': ['etl', 'pipeline', 'transform', 'ingest'],
    'Game': ['pygame', 'unity', 'godot', 'game'],
}

# Intent keywords from commits
INTENT_PATTERNS = {
    'feature': [r'^add\b', r'^implement', r'^create', r'^new\b', r'feature'],
    'fix': [r'^fix', r'^bug', r'^resolve', r'^patch'],
    'refactor': [r'^refactor', r'^clean', r'^improve', r'^optimize'],
    'docs': [r'^doc', r'^readme', r'^update.*readme'],
    'setup': [r'^init', r'^setup', r'^config', r'^first commit'],
    'wip': [r'^wip', r'work in progress', r'checkpoint'],
}


class PromptTwin:
    """Your local prompt/context twin"""
    
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.profile = self._load_profile()
        
    def _load_profile(self):
        """Load existing profile or create new"""
        if PROFILE_FILE.exists():
            return json.loads(PROFILE_FILE.read_text(encoding='utf-8'))
        return {
            'created': datetime.now().isoformat(),
            'last_scan': None,
            'projects': {},
            'technologies': Counter(),
            'project_types': Counter(),
            'topics': Counter(),
            'languages': Counter(),
            'preferences': {},
            'patterns': [],
            'git_commits': [],       # Commit messages = intent
            'git_intents': Counter(), # Categorized intents
            'md_content': [],        # Extracted markdown text
        }
    
    def _save_profile(self):
        """Save profile to disk"""
        # Convert Counters to dicts for JSON
        save_data = self.profile.copy()
        for key in ['technologies', 'project_types', 'topics', 'languages', 'git_intents']:
            if isinstance(save_data.get(key), Counter):
                save_data[key] = dict(save_data[key])
        PROFILE_FILE.write_text(json.dumps(save_data, indent=2), encoding='utf-8')
    
    def _extract_git_history(self, project_path, max_commits=50):
        """Extract git commit messages from a project"""
        git_dir = Path(project_path) / '.git'
        if not git_dir.exists():
            return [], {}
        
        commits = []
        intents = Counter()
        
        try:
            # Get commit messages
            result = subprocess.run(
                ['git', '-C', str(project_path), 'log', f'-{max_commits}', 
                 '--format=%s|||%ai', '--date=short'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return [], {}
            
            for line in result.stdout.strip().split('\n'):
                if '|||' not in line:
                    continue
                msg, date = line.rsplit('|||', 1)
                msg = msg.strip()
                if not msg:
                    continue
                    
                commits.append({
                    'message': msg,
                    'date': date.strip().split()[0],
                    'project': Path(project_path).name
                })
                
                # Classify intent
                msg_lower = msg.lower()
                for intent, patterns in INTENT_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, msg_lower):
                            intents[intent] += 1
                            break
                            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            pass
            
        return commits, intents
    
    def _extract_markdown_content(self, project_path, max_files=10):
        """Extract content from markdown files for context"""
        md_content = []
        project_name = Path(project_path).name
        
        try:
            md_files = list(Path(project_path).rglob('*.md'))[:max_files]
            
            for md_file in md_files:
                # Skip node_modules etc
                if any(skip in str(md_file) for skip in ['node_modules', '.git', 'venv', '__pycache__']):
                    continue
                    
                try:
                    content = md_file.read_text(encoding='utf-8', errors='ignore')[:5000]
                    
                    # Extract useful parts
                    extracted = {
                        'file': md_file.name,
                        'project': project_name,
                        'headers': [],
                        'descriptions': [],
                        'todos': [],
                    }
                    
                    # Headers = intent/topic
                    headers = re.findall(r'^#+\s*(.+)$', content, re.MULTILINE)
                    extracted['headers'] = [h.strip() for h in headers[:10]]
                    
                    # First paragraph = description
                    paragraphs = re.split(r'\n\n+', content)
                    for p in paragraphs[:3]:
                        p = p.strip()
                        if p and not p.startswith('#') and len(p) > 50:
                            # Remove markdown syntax
                            clean = re.sub(r'[*_`\[\]\(\)]', '', p)[:300]
                            extracted['descriptions'].append(clean)
                    
                    # TODOs and FIXMEs = intent
                    todos = re.findall(r'(?:TODO|FIXME|XXX)[:\s]*(.+)', content, re.IGNORECASE)
                    extracted['todos'] = [t.strip() for t in todos[:5]]
                    
                    if extracted['headers'] or extracted['descriptions']:
                        md_content.append(extracted)
                        
                except Exception:
                    pass
                    
        except Exception:
            pass
            
        return md_content
    
    def _github_api(self, endpoint, timeout=10):
        """Make a GitHub API request"""
        url = f"https://api.github.com{endpoint}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PromptTwin/1.0'
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"    Rate limited or forbidden: {endpoint}")
            return None
        except Exception as e:
            print(f"    Error fetching {endpoint}: {e}")
            return None
    
    def fetch_github_profile(self, username):
        """Fetch GitHub profile data (public repos, commits, READMEs)"""
        print(f"\nFetching GitHub data for: {username}")
        print("  (Using public API - no auth needed)")
        
        github_data = {
            'username': username,
            'fetched': datetime.now().isoformat(),
            'repos': [],
            'commits': [],
            'languages': Counter(),
            'topics': [],
            'readme_content': [],
        }
        
        # 1. Get public repos
        print(f"\n  Fetching repos...")
        repos = self._github_api(f"/users/{username}/repos?per_page=100&sort=updated")
        if not repos:
            print("    No repos found or API error")
            return github_data
        
        print(f"    Found {len(repos)} repos")
        
        for repo in repos:
            if repo.get('fork'):
                continue  # Skip forks
                
            repo_info = {
                'name': repo['name'],
                'description': repo.get('description', ''),
                'language': repo.get('language', ''),
                'topics': repo.get('topics', []),
                'stars': repo.get('stargazers_count', 0),
                'updated': repo.get('updated_at', ''),
            }
            github_data['repos'].append(repo_info)
            
            # Track languages
            if repo.get('language'):
                github_data['languages'][repo['language']] += 1
            
            # Collect topics
            github_data['topics'].extend(repo.get('topics', []))
        
        print(f"    Non-fork repos: {len(github_data['repos'])}")
        
        # 2. Get recent commits from top repos (by update time)
        print(f"\n  Fetching commits from recent repos...")
        for repo in github_data['repos'][:10]:  # Top 10 most recently updated
            repo_name = repo['name']
            commits = self._github_api(f"/repos/{username}/{repo_name}/commits?per_page=30")
            if commits:
                for commit in commits:
                    msg = commit.get('commit', {}).get('message', '')
                    if msg:
                        # Take first line only
                        first_line = msg.split('\n')[0].strip()
                        if first_line and len(first_line) > 3:
                            github_data['commits'].append({
                                'repo': repo_name,
                                'message': first_line[:200],
                                'date': commit.get('commit', {}).get('author', {}).get('date', '')[:10]
                            })
                print(f"    {repo_name}: {len(commits)} commits")
        
        # 3. Get READMEs from top repos
        print(f"\n  Fetching READMEs...")
        for repo in github_data['repos'][:15]:
            repo_name = repo['name']
            readme = self._github_api(f"/repos/{username}/{repo_name}/readme")
            if readme and readme.get('content'):
                try:
                    import base64
                    content = base64.b64decode(readme['content']).decode('utf-8', errors='ignore')
                    
                    # Extract headers and first paragraph
                    headers = re.findall(r'^#+\s*(.+)$', content, re.MULTILINE)[:5]
                    
                    paragraphs = []
                    for p in re.split(r'\n\n+', content)[:3]:
                        p = p.strip()
                        if p and not p.startswith('#') and len(p) > 30:
                            clean = re.sub(r'[*_`\[\]\(\)]', '', p)[:300]
                            paragraphs.append(clean)
                    
                    if headers or paragraphs:
                        github_data['readme_content'].append({
                            'repo': repo_name,
                            'headers': headers,
                            'descriptions': paragraphs[:2]
                        })
                        print(f"    {repo_name}: README extracted")
                except Exception:
                    pass
        
        # Dedupe topics
        github_data['topics'] = list(set(github_data['topics']))
        github_data['languages'] = dict(github_data['languages'])
        
        # Save to profile
        self.profile['github'] = github_data
        self._save_profile()
        
        # Print summary
        print(f"\n  === GitHub Summary ===")
        print(f"  Repos: {len(github_data['repos'])}")
        print(f"  Commits: {len(github_data['commits'])}")
        print(f"  Languages: {github_data['languages']}")
        print(f"  Topics: {github_data['topics'][:10]}")
        print(f"  READMEs: {len(github_data['readme_content'])}")
        
        return github_data
    
    def scan_projects(self, root_dir=None):
        """Scan directories for project patterns"""
        root = Path(root_dir) if root_dir else DESKTOP
        print(f"Scanning {root}...")
        
        projects_found = {}
        all_techs = Counter()
        all_types = Counter()
        all_langs = Counter()
        all_topics = Counter()
        
        # Find project directories (those with code files)
        for item in root.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith('.'):
                continue
            if item.name in {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'bin', 'obj'}:
                continue
                
            # Check if this is a project directory
            try:
                code_files = []
                for f in item.rglob('*'):
                    code_files.append(f)
                    if len(code_files) >= 1000:  # Limit for performance
                        break
            except (OSError, PermissionError) as e:
                print(f"    Skipping {item.name}: {e}")
                continue
            
            # Count by extension
            ext_counts = Counter(f.suffix.lower() for f in code_files if f.is_file())
            
            # Only process if has code files
            code_count = sum(ext_counts.get(ext, 0) for ext in CODE_EXTENSIONS)
            if code_count < 2:
                continue
                
            print(f"  Analyzing: {item.name}")
            
            project_info = {
                'path': str(item),
                'name': item.name,
                'files': len([f for f in code_files if f.is_file()]),
                'technologies': [],
                'types': [],
                'languages': [],
            }
            
            # Sample code files for content analysis
            sample_content = ""
            readme_content = ""
            
            for f in code_files:
                if f.is_file():
                    # Track languages
                    if f.suffix.lower() in CODE_EXTENSIONS:
                        all_langs[f.suffix.lower()] += 1
                        project_info['languages'].append(f.suffix.lower())
                    
                    # Read README for topics
                    if f.name.lower() in ['readme.md', 'readme.txt', 'readme']:
                        try:
                            readme_content += f.read_text(encoding='utf-8', errors='ignore')[:5000]
                        except:
                            pass
                    
                    # Sample code files  
                    if f.suffix.lower() in CODE_EXTENSIONS and len(sample_content) < 50000:
                        try:
                            sample_content += f.read_text(encoding='utf-8', errors='ignore')[:2000]
                        except:
                            pass
            
            # Detect technologies
            for tech, patterns in TECH_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, sample_content, re.IGNORECASE):
                        all_techs[tech] += 1
                        if tech not in project_info['technologies']:
                            project_info['technologies'].append(tech)
                        break
            
            # Detect project types
            for ptype, keywords in PROJECT_TYPES.items():
                for keyword in keywords:
                    if keyword.lower() in sample_content.lower() or keyword.lower() in readme_content.lower():
                        all_types[ptype] += 1
                        if ptype not in project_info['types']:
                            project_info['types'].append(ptype)
                        break
            
            # Extract topics from README
            if readme_content:
                # Simple topic extraction - look for headers and key phrases
                headers = re.findall(r'^#+\s*(.+)$', readme_content, re.MULTILINE)
                for header in headers[:10]:
                    topic = header.strip().lower()
                    if len(topic) > 3 and len(topic) < 50:
                        all_topics[topic] += 1
            
            project_info['languages'] = list(set(project_info['languages']))[:5]
            projects_found[item.name] = project_info
        
        # Extract git history and markdown from all projects
        print("\n  Extracting git history and markdown...")
        all_commits = []
        all_intents = Counter()
        all_md_content = []
        
        for name, proj in projects_found.items():
            proj_path = proj['path']
            
            # Git commits
            commits, intents = self._extract_git_history(proj_path)
            if commits:
                print(f"    {name}: {len(commits)} commits")
                all_commits.extend(commits)
                all_intents.update(intents)
            
            # Markdown content
            md_content = self._extract_markdown_content(proj_path)
            if md_content:
                all_md_content.extend(md_content)
        
        # Update profile
        self.profile['projects'] = projects_found
        self.profile['technologies'] = all_techs
        self.profile['project_types'] = all_types
        self.profile['languages'] = all_langs
        self.profile['topics'] = all_topics
        self.profile['git_commits'] = all_commits[-200:]  # Keep recent 200
        self.profile['git_intents'] = all_intents
        self.profile['md_content'] = all_md_content
        self.profile['last_scan'] = datetime.now().isoformat()
        
        self._save_profile()
        
        print(f"\nFound {len(projects_found)} projects")
        print(f"Technologies: {dict(all_techs.most_common(10))}")
        print(f"Project types: {dict(all_types.most_common(5))}")
        print(f"Languages: {dict(all_langs.most_common(5))}")
        print(f"Git commits: {len(all_commits)}")
        print(f"Git intents: {dict(all_intents.most_common(5))}")
        print(f"MD files: {len(all_md_content)}")
        
        return projects_found
    
    def log_prompt(self, prompt, tags=None):
        """Log a prompt to history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'tags': tags or [],
            'hash': hashlib.md5(prompt.encode()).hexdigest()[:8]
        }
        
        with open(PROMPTS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        print(f"Logged prompt: {prompt[:50]}...")
        return entry
    
    def get_prompts(self, limit=100):
        """Get logged prompts"""
        if not PROMPTS_FILE.exists():
            return []
        
        prompts = []
        for line in PROMPTS_FILE.read_text(encoding='utf-8').strip().split('\n'):
            if line:
                prompts.append(json.loads(line))
        
        return prompts[-limit:]
    
    # ========== FEEDBACK LOOP WITH REALITY ==========
    
    def log_outcome(self, action, result, exit_code=None, error=None, context=None):
        """Log the outcome of an action (did it work?)
        
        Args:
            action: What was attempted (e.g., "run app.py", "run tests", "applied AI suggestion")
            result: 'success', 'failure', 'partial'
            exit_code: Optional exit code from command
            error: Optional error message
            context: Optional additional context (file, prompt_hash, etc.)
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'outcome',
            'action': action,
            'result': result,
            'exit_code': exit_code,
            'error': error[:500] if error else None,
            'context': context or {},
        }
        
        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        icon = '✓' if result == 'success' else '✗' if result == 'failure' else '◐'
        print(f"{icon} Logged outcome: {action} -> {result}")
        return entry
    
    def log_error(self, error_type, error_message, file_path=None, line=None, suggestion=None):
        """Log an error that occurred (for pattern learning)
        
        Args:
            error_type: Category (e.g., "ImportError", "SyntaxError", "RuntimeError")
            error_message: The actual error
            file_path: Which file
            line: Which line
            suggestion: What fix was applied (if any)
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'error_type': error_type,
            'error_message': error_message[:500],
            'file': str(file_path) if file_path else None,
            'line': line,
            'suggestion': suggestion,
        }
        
        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        print(f"✗ Logged error: {error_type} in {file_path or 'unknown'}")
        return entry
    
    def log_correction(self, ai_suggested, user_wrote, reason=None):
        """Log when user corrects AI suggestion (learn from mistakes)
        
        Args:
            ai_suggested: What the AI suggested
            user_wrote: What the user actually wrote/wanted
            reason: Why (optional)
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'correction',
            'ai_suggested': ai_suggested[:1000],
            'user_wrote': user_wrote[:1000],
            'reason': reason,
        }
        
        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        print(f"📝 Logged correction: AI suggested X, user preferred Y")
        return entry
    
    def log_test_result(self, test_name, passed, duration=None, error=None):
        """Log test results for reality grounding"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'test',
            'test_name': test_name,
            'passed': passed,
            'duration': duration,
            'error': error[:500] if error else None,
        }
        
        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        icon = '✓' if passed else '✗'
        print(f"{icon} Test: {test_name}")
        return entry
    
    def capture_terminal_feedback(self, command, exit_code, output=None):
        """Capture feedback from terminal command execution
        
        This can be called after running commands to log what actually happened.
        """
        result = 'success' if exit_code == 0 else 'failure'
        
        # Try to extract error type from output
        error_type = None
        if output and exit_code != 0:
            if 'ImportError' in output or 'ModuleNotFoundError' in output:
                error_type = 'ImportError'
            elif 'SyntaxError' in output:
                error_type = 'SyntaxError'
            elif 'TypeError' in output:
                error_type = 'TypeError'
            elif 'FileNotFoundError' in output:
                error_type = 'FileNotFoundError'
            elif 'ConnectionError' in output or 'Connection refused' in output:
                error_type = 'ConnectionError'
        
        return self.log_outcome(
            action=f"run: {command[:100]}",
            result=result,
            exit_code=exit_code,
            error=output[:500] if output and exit_code != 0 else None,
            context={'error_type': error_type} if error_type else {}
        )
    
    def get_feedback(self, limit=100, feedback_type=None):
        """Get logged feedback entries"""
        if not FEEDBACK_FILE.exists():
            return []
        
        entries = []
        for line in FEEDBACK_FILE.read_text(encoding='utf-8').strip().split('\n'):
            if line:
                entry = json.loads(line)
                if feedback_type is None or entry.get('type') == feedback_type:
                    entries.append(entry)
        
        return entries[-limit:]
    
    def get_feedback_summary(self):
        """Get a summary of feedback for AI context"""
        feedback = self.get_feedback(500)
        
        summary = {
            'total_entries': len(feedback),
            'outcomes': {'success': 0, 'failure': 0, 'partial': 0},
            'common_errors': Counter(),
            'corrections_count': 0,
            'tests': {'passed': 0, 'failed': 0},
            'recent_failures': [],
        }
        
        for entry in feedback:
            if entry.get('type') == 'outcome':
                result = entry.get('result', 'unknown')
                if result in summary['outcomes']:
                    summary['outcomes'][result] += 1
                if result == 'failure':
                    summary['recent_failures'].append({
                        'action': entry.get('action', ''),
                        'error': entry.get('error', '')[:100],
                        'timestamp': entry.get('timestamp', '')
                    })
            elif entry.get('type') == 'error':
                error_type = entry.get('error_type', 'Unknown')
                summary['common_errors'][error_type] += 1
            elif entry.get('type') == 'correction':
                summary['corrections_count'] += 1
            elif entry.get('type') == 'test':
                if entry.get('passed'):
                    summary['tests']['passed'] += 1
                else:
                    summary['tests']['failed'] += 1
        
        # Keep only recent failures
        summary['recent_failures'] = summary['recent_failures'][-5:]
        summary['common_errors'] = dict(summary['common_errors'].most_common(10))
        
        return summary
    
    def show_feedback(self):
        """Display feedback summary"""
        summary = self.get_feedback_summary()
        
        print("\n" + "="*60)
        print("                    REALITY FEEDBACK")
        print("="*60)
        
        print(f"\n📊 Total Feedback Entries: {summary['total_entries']}")
        
        outcomes = summary['outcomes']
        total_outcomes = sum(outcomes.values())
        if total_outcomes > 0:
            success_rate = (outcomes['success'] / total_outcomes) * 100
            print(f"\n✓ Outcomes:")
            print(f"   Success: {outcomes['success']} ({success_rate:.0f}%)")
            print(f"   Failure: {outcomes['failure']}")
            print(f"   Partial: {outcomes['partial']}")
        
        if summary['common_errors']:
            print(f"\n❌ Common Errors:")
            for error_type, count in list(summary['common_errors'].items())[:5]:
                print(f"   • {error_type}: {count}")
        
        tests = summary['tests']
        if tests['passed'] + tests['failed'] > 0:
            print(f"\n🧪 Tests:")
            print(f"   Passed: {tests['passed']}")
            print(f"   Failed: {tests['failed']}")
        
        if summary['corrections_count'] > 0:
            print(f"\n📝 Corrections: {summary['corrections_count']}")
        
        if summary['recent_failures']:
            print(f"\n⚠️ Recent Failures:")
            for f in summary['recent_failures'][-3:]:
                print(f"   [{f['timestamp'][:10]}] {f['action'][:40]}")
                if f['error']:
                    print(f"      Error: {f['error'][:60]}...")
        
        print("\n" + "="*60)
        return summary
    
    def get_context(self, query, max_items=10):
        """Get relevant context for a query"""
        context = {
            'profile_summary': self._get_profile_summary(),
            'relevant_projects': [],
            'relevant_prompts': [],
            'technologies': [],
            'preferences': self.profile.get('preferences', {}),
        }
        
        query_lower = query.lower()
        
        # Find relevant projects
        for name, project in self.profile.get('projects', {}).items():
            score = 0
            if query_lower in name.lower():
                score += 5
            for tech in project.get('technologies', []):
                if tech.lower() in query_lower or query_lower in tech.lower():
                    score += 3
            for ptype in project.get('types', []):
                if ptype.lower() in query_lower:
                    score += 2
            
            if score > 0:
                context['relevant_projects'].append({
                    'name': name,
                    'score': score,
                    'technologies': project.get('technologies', []),
                    'types': project.get('types', []),
                })
        
        context['relevant_projects'].sort(key=lambda x: x['score'], reverse=True)
        context['relevant_projects'] = context['relevant_projects'][:max_items]
        
        # Find relevant prompts
        prompts = self.get_prompts()
        for prompt in prompts:
            if query_lower in prompt['prompt'].lower():
                context['relevant_prompts'].append(prompt)
        context['relevant_prompts'] = context['relevant_prompts'][:max_items]
        
        # List relevant technologies
        for tech, count in self.profile.get('technologies', {}).items():
            if tech.lower() in query_lower or query_lower in tech.lower():
                context['technologies'].append({'tech': tech, 'usage_count': count})
        
        # Include feedback summary for reality grounding
        context['feedback'] = self.get_feedback_summary()
        
        return context
    
    def _get_profile_summary(self):
        """Get a summary of the profile"""
        techs = self.profile.get('technologies', {})
        types = self.profile.get('project_types', {})
        langs = self.profile.get('languages', {})
        
        if isinstance(techs, Counter):
            techs = dict(techs)
        if isinstance(types, Counter):
            types = dict(types)
        if isinstance(langs, Counter):
            langs = dict(langs)
        
        intents = self.profile.get('git_intents', {})
        if isinstance(intents, Counter):
            intents = dict(intents)
        
        return {
            'total_projects': len(self.profile.get('projects', {})),
            'top_technologies': sorted(techs.items(), key=lambda x: -x[1])[:5],
            'top_project_types': sorted(types.items(), key=lambda x: -x[1])[:3],
            'primary_languages': sorted(langs.items(), key=lambda x: -x[1])[:3],
            'last_scan': self.profile.get('last_scan'),
            'total_commits': len(self.profile.get('git_commits', [])),
            'git_intents': sorted(intents.items(), key=lambda x: -x[1])[:5],
            'md_files': len(self.profile.get('md_content', [])),
            'github': self.profile.get('github', {}),
        }
    
    def show_profile(self):
        """Display profile summary"""
        summary = self._get_profile_summary()
        prompts = self.get_prompts()
        commits = self.profile.get('git_commits', [])
        
        print("\n" + "="*60)
        print("                    YOUR PROMPT TWIN PROFILE")
        print("="*60)
        
        print(f"\n📁 Projects: {summary['total_projects']}")
        print(f"📝 Logged Prompts: {len(prompts)}")
        print(f"🔄 Last Scan: {summary['last_scan'] or 'Never'}")
        
        print("\n🔧 Top Technologies:")
        for tech, count in summary['top_technologies']:
            print(f"   • {tech}: {count} projects")
        
        print("\n📦 Project Types:")
        for ptype, count in summary['top_project_types']:
            print(f"   • {ptype}: {count} projects")
        
        print("\n💻 Primary Languages:")
        for lang, count in summary['primary_languages']:
            print(f"   • {lang}: {count} files")
        
        # Git intents
        if summary['git_intents']:
            print(f"\n📊 Git Activity ({summary['total_commits']} commits):")
            for intent, count in summary['git_intents']:
                print(f"   • {intent}: {count}")
        
        # Recent commits
        if commits:
            print("\n📜 Recent Commits:")
            for c in commits[-5:]:
                print(f"   [{c['project']}] {c['message'][:50]}...")
        
        # GitHub data
        github = summary.get('github', {})
        if github:
            print(f"\n🐙 GitHub ({github.get('username', 'unknown')}):")
            print(f"   Repos: {len(github.get('repos', []))}")
            print(f"   Commits: {len(github.get('commits', []))}")
            gh_langs = github.get('languages', {})
            if gh_langs:
                top_gh = sorted(gh_langs.items(), key=lambda x: -x[1])[:3]
                print(f"   Top Languages: {', '.join(f'{l}({c})' for l,c in top_gh)}")
            gh_topics = github.get('topics', [])[:5]
            if gh_topics:
                print(f"   Topics: {', '.join(gh_topics)}")
        
        if prompts:
            print("\n💬 Recent Prompts:")
            for p in prompts[-5:]:
                print(f"   [{p['timestamp'][:10]}] {p['prompt'][:60]}...")
        
        print("\n" + "="*60)
        return summary
    
    def export_for_ai(self):
        """Export profile as markdown for AI context"""
        summary = self._get_profile_summary()
        prompts = self.get_prompts(50)
        
        content = f"""# User Profile Context for AI Agents

*Generated: {datetime.now().isoformat()}*
*This file provides context about the user's coding patterns and preferences.*

## Developer Profile

- **Total Projects**: {summary['total_projects']}
- **Logged Prompts**: {len(prompts)}
- **Last Scan**: {summary['last_scan'] or 'Never'}

## Technologies Used

The user frequently works with:

| Technology | Usage Count |
|------------|-------------|
"""
        for tech, count in summary['top_technologies']:
            content += f"| {tech} | {count} |\n"
        
        content += f"""
## Project Types

| Type | Count |
|------|-------|
"""
        for ptype, count in summary['top_project_types']:
            content += f"| {ptype} | {count} |\n"
        
        content += f"""
## Primary Languages

| Language | File Count |
|----------|------------|
"""
        for lang, count in summary['primary_languages']:
            content += f"| {lang} | {count} |\n"
        
        content += f"""
## Projects

"""
        for name, proj in list(self.profile.get('projects', {}).items())[:20]:
            techs = ', '.join(proj.get('technologies', [])[:5])
            content += f"- **{name}**: {techs or 'No detected tech'}\n"
        
        # Git activity
        commits = self.profile.get('git_commits', [])
        if commits:
            content += f"""
## Git Activity ({len(commits)} commits analyzed)

### Commit Intent Patterns

| Intent | Count |
|--------|-------|
"""
            for intent, count in summary.get('git_intents', []):
                content += f"| {intent} | {count} |\n"
            
            content += f"""
### Recent Commit Messages (Sample)

These show how the user describes their work:

"""
            for c in commits[-30:]:
                content += f"- [{c['project']}] {c['message'][:100]}\n"
        
        # Markdown content
        md_content = self.profile.get('md_content', [])
        if md_content:
            content += f"""
## Documentation Patterns ({len(md_content)} MD files)

### Common Topics/Headers

"""
            # Collect all headers
            all_headers = []
            for md in md_content[:20]:
                all_headers.extend(md.get('headers', [])[:3])
            for h in all_headers[:25]:
                content += f"- {h}\n"
            
            content += f"""
### Project Descriptions (from READMEs)

"""
            for md in md_content[:10]:
                for desc in md.get('descriptions', [])[:1]:
                    content += f"- **{md['project']}**: {desc[:200]}...\n"
        
        # GitHub data
        github = self.profile.get('github', {})
        if github and github.get('repos'):
            content += f"""
## GitHub Profile (@{github.get('username', 'unknown')})

### Repositories ({len(github.get('repos', []))} total)

| Repo | Description | Language |
|------|-------------|----------|
"""
            for repo in github.get('repos', [])[:15]:
                desc = (repo.get('description') or 'No description')[:50]
                lang = repo.get('language') or '-'
                content += f"| {repo['name']} | {desc} | {lang} |\n"
            
            gh_langs = github.get('languages', {})
            if gh_langs:
                content += f"""
### GitHub Languages

| Language | Repos |
|----------|-------|
"""
                for lang, count in sorted(gh_langs.items(), key=lambda x: -x[1])[:8]:
                    content += f"| {lang} | {count} |\n"
            
            gh_topics = github.get('topics', [])
            if gh_topics:
                content += f"""
### GitHub Topics/Tags

{', '.join(gh_topics[:20])}
"""
            
            gh_commits = github.get('commits', [])
            if gh_commits:
                content += f"""
### GitHub Commit Messages (Sample)

These show work across all repos:

"""
                for c in gh_commits[-25:]:
                    content += f"- [{c['repo']}] {c['message'][:100]}\n"
        
        if prompts:
            content += f"""
## Recent Prompts (Sample)

These are examples of how the user typically phrases requests:

"""
            for p in prompts[-20:]:
                content += f"- {p['prompt'][:200]}\n"
        
        # Feedback / Reality Grounding
        feedback_summary = self.get_feedback_summary()
        if feedback_summary['total_entries'] > 0:
            content += f"""
## Reality Feedback (What Actually Works)

**Tracked Outcomes**: {feedback_summary['total_entries']} entries
"""
            outcomes = feedback_summary['outcomes']
            total = sum(outcomes.values())
            if total > 0:
                success_rate = (outcomes['success'] / total) * 100
                content += f"""
### Success Rate: {success_rate:.0f}%

| Result | Count |
|--------|-------|
| Success | {outcomes['success']} |
| Failure | {outcomes['failure']} |
| Partial | {outcomes['partial']} |
"""
            
            if feedback_summary['common_errors']:
                content += """
### Common Errors (watch out for these)

| Error Type | Occurrences |
|------------|-------------|
"""
                for err_type, count in feedback_summary['common_errors'].items():
                    content += f"| {err_type} | {count} |\n"
            
            if feedback_summary['corrections_count'] > 0:
                content += f"""
### Corrections Logged: {feedback_summary['corrections_count']}

*The user has corrected AI suggestions {feedback_summary['corrections_count']} times.*
*Consider patterns in what the user prefers over AI suggestions.*
"""
            
            if feedback_summary['recent_failures']:
                content += """
### Recent Failures (avoid these patterns)

"""
                for f in feedback_summary['recent_failures']:
                    content += f"- {f['action']}: {f['error'][:80]}...\n"
        
        content += f"""
## Inferred Preferences

Based on patterns:
- Prefers **local-first** approaches (Ollama, SQLite usage)
- Builds **full-stack** applications
- Values **working code over sophisticated architecture**
- Uses **Python** and **.NET** ecosystems
- Interested in **AI/ML integration**

## How to Use This Context

When the user asks for help:
1. Prefer their familiar technologies when suggesting solutions
2. Match their coding style (practical over theoretical)
3. Reference their existing projects when relevant
4. Keep solutions simple and runnable
5. Note their commit style - they tend to {self._infer_commit_style()}

---
*This context is automatically generated by prompt_twin.py*
"""
        
        EXPORT_FILE.write_text(content, encoding='utf-8')
        print(f"Exported to: {EXPORT_FILE}")
        return EXPORT_FILE
    
    def _infer_commit_style(self):
        """Infer commit style from patterns"""
        intents = self.profile.get('git_intents', {})
        if isinstance(intents, Counter):
            intents = dict(intents)
        
        if not intents:
            return "write brief descriptive messages"
        
        top = max(intents.items(), key=lambda x: x[1])[0] if intents else 'feature'
        styles = {
            'feature': 'add new features incrementally',
            'fix': 'fix issues as they arise',
            'refactor': 'refactor and clean up code regularly',
            'wip': 'commit work-in-progress frequently',
            'docs': 'maintain good documentation',
        }
        return styles.get(top, 'write brief descriptive messages')
    
    def inject_context(self, target_dir=None):
        """Inject context into AI tools (Cursor, VS Code, Ollama)"""
        target = Path(target_dir) if target_dir else DESKTOP
        summary = self._get_profile_summary()
        
        # Generate compact context for injection
        context = self._generate_compact_context()
        
        results = []
        
        # 1. Create .cursorrules file (Cursor reads this automatically)
        cursorrules_path = target / '.cursorrules'
        cursorrules_content = f"""# User Context (Auto-generated by prompt_twin.py)
# This file is read by Cursor to understand user preferences

{context}

# Instructions for Cursor
When helping this user:
- Prefer their familiar technologies (Flask, SQLite, Ollama, Python)
- Match their coding style (practical over theoretical)
- Keep solutions simple and runnable
- Suggest local-first approaches when appropriate
"""
        try:
            cursorrules_path.write_text(cursorrules_content, encoding='utf-8')
            results.append(f"✓ Created {cursorrules_path}")
        except Exception as e:
            results.append(f"✗ Failed to create .cursorrules: {e}")
        
        # 2. Create .github/copilot-instructions.md (VS Code Copilot reads this)
        github_dir = target / '.github'
        github_dir.mkdir(exist_ok=True)
        copilot_path = github_dir / 'copilot-instructions.md'
        copilot_content = f"""# Copilot Instructions

{context}

## Preferences
- Use Python for scripts, Flask/FastAPI for APIs
- Prefer SQLite for local storage
- Keep code practical and runnable
- Local-first when possible (Ollama over cloud APIs)
"""
        try:
            copilot_path.write_text(copilot_content, encoding='utf-8')
            results.append(f"✓ Created {copilot_path}")
        except Exception as e:
            results.append(f"✗ Failed to create copilot-instructions.md: {e}")
        
        # 3. Create Ollama system prompt wrapper
        ollama_wrapper_path = DATA_DIR / 'ollama_with_context.py'
        ollama_wrapper = f'''#!/usr/bin/env python3
"""
Ollama wrapper that auto-injects your prompt twin context.
Usage: python ollama_with_context.py "your prompt here"
"""
import sys
import json
import urllib.request

CONTEXT = """
{context.replace(chr(10), chr(10))}
"""

def query_ollama(prompt, model="qwen2.5:7b"):
    """Query Ollama with auto-injected context"""
    full_prompt = f"{{CONTEXT}}\\n\\nUser request: {{prompt}}"
    
    data = json.dumps({{
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }}).encode()
    
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={{"Content-Type": "application/json"}}
    )
    
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    return result.get("response", "")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ollama_with_context.py \\"your prompt\\"")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    print(query_ollama(prompt))
'''
        try:
            ollama_wrapper_path.write_text(ollama_wrapper, encoding='utf-8')
            results.append(f"✓ Created {ollama_wrapper_path}")
        except Exception as e:
            results.append(f"✗ Failed to create Ollama wrapper: {e}")
        
        # 4. Copy to clipboard (if pyperclip available)
        try:
            import pyperclip
            pyperclip.copy(context)
            results.append("✓ Context copied to clipboard")
        except ImportError:
            # Fallback: use PowerShell clip
            try:
                proc = subprocess.run(
                    ['powershell', '-c', f'Set-Clipboard -Value "{context[:8000]}"'],
                    capture_output=True, timeout=5
                )
                if proc.returncode == 0:
                    results.append("✓ Context copied to clipboard (via PowerShell)")
            except Exception:
                results.append("○ Clipboard: Install pyperclip for auto-copy")
        
        print("\n=== Context Injection Complete ===\n")
        for r in results:
            print(f"  {r}")
        
        print(f"\n  Files created in: {target}")
        print(f"\n  Usage:")
        print(f"    • Cursor: Open folder, context auto-loads from .cursorrules")
        print(f"    • VS Code Copilot: Context loads from .github/copilot-instructions.md")
        print(f"    • Ollama: python {ollama_wrapper_path} \"your prompt\"")
        print()
        
        return results
    
    def _generate_compact_context(self):
        """Generate a compact context string for injection"""
        summary = self._get_profile_summary()
        
        lines = ["## Developer Profile"]
        
        # Tech stack
        if summary['top_technologies']:
            techs = ', '.join(t[0] for t in summary['top_technologies'][:5])
            lines.append(f"Technologies: {techs}")
        
        # Languages
        if summary['primary_languages']:
            langs = ', '.join(f"{l[0]}({l[1]})" for l in summary['primary_languages'][:3])
            lines.append(f"Languages: {langs}")
        
        # Project types
        if summary['top_project_types']:
            types = ', '.join(t[0] for t in summary['top_project_types'][:3])
            lines.append(f"Project Types: {types}")
        
        # GitHub
        github = summary.get('github', {})
        if github:
            lines.append(f"GitHub: @{github.get('username', 'unknown')} ({len(github.get('repos', []))} repos)")
            gh_langs = github.get('languages', {})
            if gh_langs:
                top_gh = sorted(gh_langs.items(), key=lambda x: -x[1])[:3]
                lines.append(f"GitHub Languages: {', '.join(f'{l}({c})' for l,c in top_gh)}")
        
        # Commit style
        if summary.get('git_intents'):
            top_intent = summary['git_intents'][0][0] if summary['git_intents'] else 'feature'
            lines.append(f"Commit Style: {self._infer_commit_style()}")
        
        # Preferences
        lines.append("")
        lines.append("## Preferences")
        lines.append("- Local-first (Ollama, SQLite)")
        lines.append("- Practical working code over theory")
        lines.append("- Full-stack Python + .NET")
        lines.append("- Interested in ML/AI, information theory")
        
        return '\n'.join(lines)
    
    # ========== WATCH MODE ==========
    
    def watch(self, paths=None, interval=30):
        """Watch for file changes and auto-update profile
        
        Args:
            paths: List of paths to watch (default: Desktop)
            interval: Seconds between checks (default: 30)
        """
        import time
        
        watch_paths = paths or [DESKTOP]
        print(f"👁️  Watch mode started (checking every {interval}s)")
        print(f"   Watching: {', '.join(str(p) for p in watch_paths)}")
        print("   Press Ctrl+C to stop\n")
        
        # Track file modification times
        last_scan = {}
        
        def get_file_mtimes(root):
            """Get modification times for relevant files"""
            mtimes = {}
            root = Path(root)
            if not root.exists():
                return mtimes
            for ext in CODE_EXTENSIONS | DOC_EXTENSIONS:
                for f in root.rglob(f'*{ext}'):
                    if '.git' not in str(f) and 'node_modules' not in str(f):
                        try:
                            mtimes[str(f)] = f.stat().st_mtime
                        except (PermissionError, OSError):
                            pass
            return mtimes
        
        # Initial scan
        for p in watch_paths:
            last_scan.update(get_file_mtimes(p))
        print(f"   Tracking {len(last_scan)} files")
        
        try:
            while True:
                time.sleep(interval)
                
                # Check for changes
                changed = False
                for p in watch_paths:
                    current = get_file_mtimes(p)
                    for f, mtime in current.items():
                        if f not in last_scan or last_scan[f] != mtime:
                            changed = True
                            print(f"   📝 Changed: {Path(f).name}")
                    last_scan.update(current)
                
                if changed:
                    print(f"\n   🔄 Re-scanning at {datetime.now().strftime('%H:%M:%S')}...")
                    self.scan_projects()
                    self.inject_context()
                    print("   ✓ Profile updated and injected\n")
                    
        except KeyboardInterrupt:
            print("\n   ⏹️  Watch mode stopped")
    
    def setup_git_hook(self, repo_path=None):
        """Install a git post-commit hook for auto-scanning
        
        Args:
            repo_path: Repository to add hook to (default: current directory)
        """
        repo = Path(repo_path) if repo_path else Path.cwd()
        git_dir = repo / '.git'
        
        if not git_dir.exists():
            print(f"❌ Not a git repository: {repo}")
            return False
        
        hooks_dir = git_dir / 'hooks'
        hooks_dir.mkdir(exist_ok=True)
        
        hook_file = hooks_dir / 'post-commit'
        
        # Create hook script
        script_path = Path(__file__).absolute()
        hook_content = f'''#!/bin/sh
# Auto-update prompt twin after commits
python "{script_path}" scan
python "{script_path}" inject
echo "✓ Prompt twin updated"
'''
        
        hook_file.write_text(hook_content)
        
        # Make executable (Windows doesn't really need this, but good practice)
        try:
            import stat
            hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        except Exception:
            pass
        
        print(f"✓ Git hook installed: {hook_file}")
        print("  Profile will auto-update after each commit")
        return True
    
    # ========== STRUCTURED PROFILE ==========
    
    def analyze_coding_style(self):
        """Analyze coding patterns and style preferences"""
        style = {
            'naming_conventions': {},
            'file_organization': {},
            'common_patterns': [],
            'framework_preferences': [],
            'database_preferences': [],
        }
        
        # Analyze from scanned projects
        techs = self.profile.get('technologies', {})
        
        # Framework preferences
        web_frameworks = ['Flask', 'FastAPI', 'Django', 'Express']
        for fw in web_frameworks:
            if techs.get(fw, 0) > 0:
                style['framework_preferences'].append(fw)
        
        # Database preferences
        dbs = ['SQLite', 'PostgreSQL', 'MongoDB', 'Redis']
        for db in dbs:
            if techs.get(db, 0) > 0:
                style['database_preferences'].append(db)
        
        # Infer naming from commit messages
        commits = self.profile.get('git_commits', [])
        if commits:
            # Check if commits use lowercase, present tense, etc.
            lowercase_starts = sum(1 for c in commits if c.get('message', '').split()[0].islower())
            style['naming_conventions']['commit_style'] = 'lowercase_present' if lowercase_starts > len(commits) / 2 else 'capitalized'
        
        # Common patterns from code
        patterns = []
        if techs.get('Flask', 0) > 0 and techs.get('SQLite', 0) > 0:
            patterns.append('Flask + SQLite for local apps')
        if techs.get('Ollama', 0) > 0:
            patterns.append('Local LLM via Ollama')
        if any(techs.get(t, 0) > 0 for t in ['Machine Learning', 'OpenAI', 'LangChain']):
            patterns.append('AI/ML integration')
        
        style['common_patterns'] = patterns
        
        return style
    
    def get_structured_profile(self):
        """Get a fully structured profile with all sections"""
        return {
            'meta': {
                'version': '2.0',
                'created': self.profile.get('created'),
                'last_scan': self.profile.get('last_scan'),
                'last_updated': datetime.now().isoformat(),
            },
            'coding_style': self.analyze_coding_style(),
            'common_errors': self._analyze_common_errors(),
            'preferred_patterns': self._get_preferred_patterns(),
            'project_contexts': self._get_project_contexts(),
            'technologies': dict(self.profile.get('technologies', {})),
            'feedback_summary': self.get_feedback_summary(),
        }
    
    def _analyze_common_errors(self):
        """Analyze common errors from feedback"""
        feedback = self.get_feedback(500)
        errors = {}
        
        for entry in feedback:
            if entry.get('type') == 'error':
                err_type = entry.get('error_type', 'Unknown')
                if err_type not in errors:
                    errors[err_type] = {'count': 0, 'examples': []}
                errors[err_type]['count'] += 1
                if len(errors[err_type]['examples']) < 3:
                    errors[err_type]['examples'].append(entry.get('error_message', '')[:100])
        
        return errors
    
    def _get_preferred_patterns(self):
        """Extract preferred patterns from feedback and code"""
        patterns = {
            'preferred': [],
            'avoided': [],
        }
        
        feedback = self.get_feedback(500)
        for entry in feedback:
            if entry.get('type') == 'correction':
                # User corrected AI = pattern to avoid
                patterns['avoided'].append({
                    'ai_suggested': entry.get('ai_suggested', '')[:100],
                    'user_preferred': entry.get('user_wrote', '')[:100],
                    'reason': entry.get('reason'),
                })
        
        # Preferred patterns from code analysis
        style = self.analyze_coding_style()
        patterns['preferred'] = style.get('common_patterns', [])
        
        return patterns
    
    def _get_project_contexts(self):
        """Get context for each project"""
        contexts = {}
        for name, project in list(self.profile.get('projects', {}).items())[:20]:
            files = project.get('files', 0)
            # Handle both int count and list
            file_count = files if isinstance(files, int) else len(files) if isinstance(files, list) else 0
            contexts[name] = {
                'technologies': project.get('technologies', []),
                'types': project.get('types', []),
                'file_count': file_count,
            }
        return contexts
    
    def export_structured(self):
        """Export structured profile as YAML-like format"""
        profile = self.get_structured_profile()
        
        structured_file = DATA_DIR / 'profile_structured.json'
        structured_file.write_text(json.dumps(profile, indent=2), encoding='utf-8')
        print(f"✓ Exported structured profile: {structured_file}")
        
        # Also create a YAML-like readable version
        yaml_file = DATA_DIR / 'profile.yaml'
        yaml_content = self._to_yaml_like(profile)
        yaml_file.write_text(yaml_content, encoding='utf-8')
        print(f"✓ Exported readable profile: {yaml_file}")
        
        return profile
    
    def _to_yaml_like(self, data, indent=0):
        """Convert dict to readable YAML-like format (no PyYAML dependency)"""
        lines = []
        prefix = '  ' * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)) and value:
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._to_yaml_like(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    lines.append(f"{prefix}-")
                    lines.append(self._to_yaml_like(item, indent + 1))
                else:
                    lines.append(f"{prefix}- {item}")
        
        return '\n'.join(lines)
    
    # ========== OLLAMA INTEGRATION ==========
    
    def test_with_ollama(self, prompt, model='qwen2.5:7b'):
        """Test prompt completion with context injected into Ollama
        
        Args:
            prompt: The user prompt to test
            model: Ollama model to use
        """
        import time
        
        # Generate system prompt from profile
        system_prompt = self._generate_ollama_system_prompt()
        
        print(f"🧪 Testing with Ollama ({model})")
        print(f"   System prompt: {len(system_prompt)} chars")
        print(f"   User prompt: {prompt[:50]}...")
        print()
        
        # Test WITHOUT context
        print("⏳ Testing without context...")
        start = time.time()
        result_no_ctx = self._query_ollama(prompt, model=model)
        time_no_ctx = time.time() - start
        
        # Test WITH context
        print("⏳ Testing with context...")
        start = time.time()
        result_with_ctx = self._query_ollama(prompt, system_prompt=system_prompt, model=model)
        time_with_ctx = time.time() - start
        
        print("\n" + "="*60)
        print("WITHOUT CONTEXT:")
        print("-"*60)
        print(result_no_ctx[:500])
        print(f"\n[{time_no_ctx:.1f}s]")
        
        print("\n" + "="*60)
        print("WITH YOUR PROFILE CONTEXT:")
        print("-"*60)
        print(result_with_ctx[:500])
        print(f"\n[{time_with_ctx:.1f}s]")
        print("="*60)
        
        return result_no_ctx, result_with_ctx
    
    def _generate_ollama_system_prompt(self):
        """Generate a system prompt for Ollama based on profile"""
        summary = self._get_profile_summary()
        feedback = self.get_feedback_summary()
        
        lines = [
            "You are a coding assistant for a developer with these preferences:",
            "",
            "## Tech Stack",
        ]
        
        if summary['top_technologies']:
            techs = ', '.join(t[0] for t in summary['top_technologies'][:8])
            lines.append(f"Primary: {techs}")
        
        if summary['primary_languages']:
            langs = ', '.join(l[0] for l in summary['primary_languages'][:5])
            lines.append(f"Languages: {langs}")
        
        lines.extend([
            "",
            "## Style Preferences",
            "- Prefer local-first solutions (Ollama over cloud APIs, SQLite over hosted DBs)",
            "- Keep code practical and runnable",
            "- Single-file apps when possible",
            "- Standard library over heavy dependencies",
        ])
        
        # Add error patterns to avoid
        if feedback.get('common_errors'):
            lines.extend(["", "## Common Errors (avoid these)"])
            for err_type, count in list(feedback['common_errors'].items())[:5]:
                lines.append(f"- {err_type}: {count} occurrences")
        
        # Add correction patterns
        corrections = self._get_preferred_patterns().get('avoided', [])
        if corrections:
            lines.extend(["", "## User Corrections (learn from these)"])
            for c in corrections[:3]:
                lines.append(f"- Changed: {c.get('ai_suggested', '?')[:50]}")
                lines.append(f"  To: {c.get('user_preferred', '?')[:50]}")
        
        lines.extend([
            "",
            "Be concise. Provide working code. Match the developer's style.",
        ])
        
        return '\n'.join(lines)
    
    def _query_ollama(self, prompt, system_prompt=None, model='qwen2.5:7b'):
        """Query Ollama API"""
        try:
            data = {
                'model': model,
                'prompt': prompt,
                'stream': False,
            }
            if system_prompt:
                data['system'] = system_prompt
            
            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                json.dumps(data).encode(),
                {'Content-Type': 'application/json'}
            )
            r = urllib.request.urlopen(req, timeout=60)
            result = json.loads(r.read())
            return result.get('response', '')
        except Exception as e:
            return f"[Ollama error: {e}]"
    
    # ========== NUANCED FEEDBACK ==========
    
    def log_nuanced_feedback(self, category, description, context=None):
        """Log nuanced feedback about AI interactions
        
        Categories:
        - naming: AI misunderstood naming conventions
        - deprecated: Suggested deprecated pattern
        - style: Didn't match coding style
        - complexity: Over/under-engineered
        - missing_context: Missed project-specific context
        - wrong_tech: Suggested wrong technology
        - good: AI got it right (positive feedback)
        """
        valid_categories = [
            'naming', 'deprecated', 'style', 'complexity',
            'missing_context', 'wrong_tech', 'good', 'other'
        ]
        
        if category not in valid_categories:
            print(f"⚠️  Unknown category. Valid: {', '.join(valid_categories)}")
            category = 'other'
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'nuanced_feedback',
            'category': category,
            'description': description[:500],
            'context': context or {},
        }
        
        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        icons = {
            'naming': '📛', 'deprecated': '⚠️', 'style': '🎨',
            'complexity': '📐', 'missing_context': '❓',
            'wrong_tech': '🔧', 'good': '✅', 'other': '📝'
        }
        print(f"{icons.get(category, '📝')} Logged {category}: {description[:50]}...")
        return entry
    
    def get_nuanced_feedback_summary(self):
        """Get summary of nuanced feedback categories"""
        feedback = self.get_feedback(500)
        
        categories = Counter()
        examples = defaultdict(list)
        
        for entry in feedback:
            if entry.get('type') == 'nuanced_feedback':
                cat = entry.get('category', 'other')
                categories[cat] += 1
                if len(examples[cat]) < 3:
                    examples[cat].append(entry.get('description', '')[:80])
        
        return {
            'counts': dict(categories),
            'examples': dict(examples),
            'total': sum(categories.values()),
        }
    
    def set_preference(self, key, value):
        """Set a user preference"""
        if 'preferences' not in self.profile:
            self.profile['preferences'] = {}
        self.profile['preferences'][key] = value
        self._save_profile()
        print(f"Set preference: {key} = {value}")
    
    # ========== MCP SERVER MODE ==========
    
    def start_mcp_server(self, port=8765):
        """Start an MCP-compatible tool server
        
        Exposes prompt twin as tools that AI agents can query:
        - get_context: Get context for a query
        - get_profile: Get developer profile summary
        - log_feedback: Log outcome/error/correction
        - get_technologies: Get tech stack
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        twin = self
        
        class MCPHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress logging
            
            def _send_json(self, data, status=200):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def do_GET(self):
                if self.path == '/mcp/tools':
                    # Return available tools (MCP discovery)
                    tools = {
                        'tools': [
                            {
                                'name': 'prompt_twin_context',
                                'description': 'Get developer context for a query',
                                'parameters': {'query': 'string'}
                            },
                            {
                                'name': 'prompt_twin_profile',
                                'description': 'Get developer profile summary',
                                'parameters': {}
                            },
                            {
                                'name': 'prompt_twin_technologies',
                                'description': 'Get developer tech stack',
                                'parameters': {}
                            },
                            {
                                'name': 'prompt_twin_feedback',
                                'description': 'Log feedback about AI interaction',
                                'parameters': {'type': 'string', 'message': 'string'}
                            }
                        ]
                    }
                    self._send_json(tools)
                    
                elif self.path == '/mcp/profile':
                    summary = twin._get_profile_summary()
                    self._send_json(summary)
                    
                elif self.path == '/mcp/technologies':
                    techs = dict(twin.profile.get('technologies', {}))
                    self._send_json({'technologies': techs})
                    
                elif self.path == '/health':
                    self._send_json({'status': 'ok', 'version': '2.0'})
                    
                else:
                    self._send_json({'error': 'Unknown endpoint'}, 404)
            
            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length)) if length else {}
                
                if self.path == '/mcp/context':
                    query = body.get('query', '')
                    context = twin.get_context(query)
                    self._send_json(context)
                    
                elif self.path == '/mcp/feedback':
                    fb_type = body.get('type', 'outcome')
                    if fb_type == 'error':
                        twin.log_error(
                            body.get('error_type', 'Unknown'),
                            body.get('message', ''),
                            body.get('file')
                        )
                    elif fb_type == 'correction':
                        twin.log_correction(
                            body.get('ai_suggested', ''),
                            body.get('user_wrote', ''),
                            body.get('reason')
                        )
                    else:
                        twin.log_outcome(
                            body.get('action', ''),
                            body.get('result', 'success'),
                            body.get('error')
                        )
                    self._send_json({'status': 'logged'})
                    
                elif self.path == '/mcp/invoke':
                    # MCP tool invocation
                    tool = body.get('tool', '')
                    params = body.get('parameters', {})
                    
                    if tool == 'prompt_twin_context':
                        result = twin.get_context(params.get('query', ''))
                    elif tool == 'prompt_twin_profile':
                        result = twin._get_profile_summary()
                    elif tool == 'prompt_twin_technologies':
                        result = {'technologies': dict(twin.profile.get('technologies', {}))}
                    else:
                        result = {'error': f'Unknown tool: {tool}'}
                    
                    self._send_json(result)
                    
                else:
                    self._send_json({'error': 'Unknown endpoint'}, 404)
        
        print(f"🔌 MCP Server starting on http://localhost:{port}")
        print(f"   Tools: /mcp/tools")
        print(f"   Profile: /mcp/profile")
        print(f"   Context: POST /mcp/context")
        print(f"   Invoke: POST /mcp/invoke")
        print(f"   Press Ctrl+C to stop\n")
        
        server = HTTPServer(('127.0.0.1', port), MCPHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n   ⏹️  MCP Server stopped")
    
    # ========== CONFIG FILE SUPPORT ==========
    
    def load_config(self):
        """Load configuration from .prompt_twin/config.json"""
        config_file = DATA_DIR / 'config.json'
        
        default_config = {
            'scan_paths': [str(DESKTOP)],
            'watch_interval': 30,
            'ollama_model': 'qwen2.5:7b',
            'ollama_url': 'http://localhost:11434',
            'mcp_port': 8765,
            'auto_inject': True,
            'inject_targets': ['cursor', 'copilot', 'ollama'],
            'exclude_patterns': ['.git', 'node_modules', '__pycache__', '.venv'],
            'max_file_size_kb': 500,
        }
        
        if config_file.exists():
            try:
                user_config = json.loads(config_file.read_text(encoding='utf-8'))
                default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Config error: {e}")
        
        return default_config
    
    def save_config(self, config):
        """Save configuration to .prompt_twin/config.json"""
        config_file = DATA_DIR / 'config.json'
        config_file.write_text(json.dumps(config, indent=2), encoding='utf-8')
        print(f"✓ Config saved: {config_file}")
    
    def show_config(self):
        """Show current configuration"""
        config = self.load_config()
        print("\n⚙️  Configuration (.prompt_twin/config.json)\n")
        for key, value in config.items():
            print(f"   {key}: {value}")
        print()
    
    def set_config(self, key, value):
        """Set a configuration value"""
        config = self.load_config()
        
        # Type conversion
        if key in ('watch_interval', 'mcp_port', 'max_file_size_kb'):
            value = int(value)
        elif key in ('auto_inject',):
            value = value.lower() in ('true', '1', 'yes')
        elif key in ('scan_paths', 'inject_targets', 'exclude_patterns'):
            value = [v.strip() for v in value.split(',')]
        
        config[key] = value
        self.save_config(config)
        print(f"Set {key} = {value}")
    
    # ========== LLM AUTO-ANALYSIS ==========
    
    def analyze_with_llm(self, aspect='all'):
        """Use LLM to analyze your coding patterns and suggest improvements
        
        Args:
            aspect: 'all', 'patterns', 'errors', 'style', 'suggestions'
        """
        config = self.load_config()
        model = config.get('ollama_model', 'qwen2.5:7b')
        
        # Build analysis prompt
        summary = self._get_profile_summary()
        feedback = self.get_feedback_summary()
        structured = self.get_structured_profile()
        
        analysis_prompt = f"""Analyze this developer's coding profile and provide insights:

## Technologies
{json.dumps(dict(list(summary.get('top_technologies', [])[:10])), indent=2)}

## Languages  
{json.dumps(dict(list(summary.get('primary_languages', [])[:5])), indent=2)}

## Common Errors
{json.dumps(feedback.get('common_errors', {}), indent=2)}

## Corrections Made
{json.dumps(structured.get('preferred_patterns', {}).get('avoided', [])[:5], indent=2)}

## Recent Git Activity
{json.dumps(dict(list(summary.get('git_intent_summary', {}).items())[:5]), indent=2)}

Based on this profile, provide:
1. THREE patterns you notice in their work
2. TWO potential blind spots or errors to watch for
3. TWO suggestions to improve their workflow
4. ONE technology they might benefit from learning

Be concise and specific. No generic advice."""

        print(f"🔍 Analyzing profile with {model}...")
        print()
        
        result = self._query_ollama(analysis_prompt, model=model)
        
        print("="*60)
        print("📊 LLM ANALYSIS OF YOUR CODING PROFILE")
        print("="*60)
        print(result)
        print("="*60)
        
        # Save analysis
        analysis_file = DATA_DIR / 'analysis.md'
        analysis_file.write_text(f"# Profile Analysis\n\nGenerated: {datetime.now().isoformat()}\n\n{result}", encoding='utf-8')
        print(f"\n✓ Saved to {analysis_file}")
        
        return result
    
    # ========== TEMPLATE SUGGESTIONS ==========
    
    def suggest_templates(self, description=None):
        """Suggest project templates based on your profile and description
        
        Args:
            description: Optional project description
        """
        summary = self._get_profile_summary()
        techs = dict(summary.get('top_technologies', [])[:10])
        
        # Define templates based on common stacks
        templates = {
            'flask_sqlite': {
                'name': 'Flask + SQLite App',
                'stack': ['Flask', 'SQLite'],
                'files': ['app.py', 'database.py', 'templates/'],
                'description': 'Simple Flask app with SQLite storage'
            },
            'flask_auth': {
                'name': 'Flask with Auth',
                'stack': ['Flask', 'Auth', 'SQLite'],
                'files': ['app.py', 'auth.py', 'models.py'],
                'description': 'Flask app with user authentication'
            },
            'ml_pipeline': {
                'name': 'ML Pipeline',
                'stack': ['Machine Learning', 'pandas'],
                'files': ['train.py', 'predict.py', 'data/'],
                'description': 'Machine learning training pipeline'
            },
            'api_service': {
                'name': 'REST API Service',
                'stack': ['Flask', 'FastAPI'],
                'files': ['main.py', 'routes.py', 'models.py'],
                'description': 'RESTful API service'
            },
            'ollama_tool': {
                'name': 'Ollama Integration',
                'stack': ['Ollama', 'Machine Learning'],
                'files': ['chat.py', 'embeddings.py'],
                'description': 'Local LLM tool with Ollama'
            },
            'cli_tool': {
                'name': 'CLI Tool',
                'stack': [],
                'files': ['main.py', 'commands.py'],
                'description': 'Command-line tool (stdlib only)'
            }
        }
        
        # Score templates based on profile match
        scored = []
        for tid, template in templates.items():
            score = 0
            for tech in template['stack']:
                if techs.get(tech, 0) > 0:
                    score += techs[tech]
            
            # Boost if description matches
            if description:
                desc_lower = description.lower()
                if any(word in desc_lower for word in ['auth', 'login', 'user']):
                    if 'Auth' in template['stack']:
                        score += 10
                if any(word in desc_lower for word in ['ml', 'train', 'model', 'predict']):
                    if 'Machine Learning' in template['stack']:
                        score += 10
                if any(word in desc_lower for word in ['api', 'rest', 'endpoint']):
                    if 'Flask' in template['stack'] or 'FastAPI' in template['stack']:
                        score += 5
                if any(word in desc_lower for word in ['ollama', 'llm', 'chat', 'ai']):
                    if 'Ollama' in template['stack']:
                        score += 10
            
            scored.append((score, tid, template))
        
        # Sort by score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        print("\n🎯 Template Suggestions Based on Your Profile\n")
        if description:
            print(f"   Query: \"{description}\"\n")
        
        for i, (score, tid, template) in enumerate(scored[:4], 1):
            match = "⭐⭐⭐" if score > 10 else "⭐⭐" if score > 5 else "⭐" if score > 0 else ""
            print(f"{i}. {template['name']} {match}")
            print(f"   {template['description']}")
            print(f"   Stack: {', '.join(template['stack']) or 'stdlib'}")
            print(f"   Files: {', '.join(template['files'])}")
            print()
        
        return scored[:4]
    
    # ========== PROFILE DIFF TRACKING ==========
    
    def save_snapshot(self, name=None):
        """Save a snapshot of current profile for tracking changes"""
        snapshots_dir = DATA_DIR / 'snapshots'
        snapshots_dir.mkdir(exist_ok=True)
        
        name = name or datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_file = snapshots_dir / f'{name}.json'
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'name': name,
            'profile': self.get_structured_profile(),
        }
        
        snapshot_file.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
        print(f"✓ Snapshot saved: {snapshot_file.name}")
        return snapshot_file
    
    def list_snapshots(self):
        """List available profile snapshots"""
        snapshots_dir = DATA_DIR / 'snapshots'
        if not snapshots_dir.exists():
            print("No snapshots yet. Use 'python prompt_twin.py snapshot' to create one.")
            return []
        
        snapshots = sorted(snapshots_dir.glob('*.json'), reverse=True)
        
        print(f"\n📸 Profile Snapshots ({len(snapshots)} total)\n")
        for s in snapshots[:10]:
            try:
                data = json.loads(s.read_text(encoding='utf-8'))
                ts = data.get('timestamp', 'Unknown')[:10]
                techs = len(data.get('profile', {}).get('technologies', {}))
                print(f"   {s.stem} ({ts}) - {techs} technologies")
            except:
                print(f"   {s.stem}")
        
        return [s.stem for s in snapshots]
    
    def diff_profile(self, snapshot_name=None):
        """Compare current profile with a previous snapshot"""
        snapshots_dir = DATA_DIR / 'snapshots'
        
        if not snapshot_name:
            # Find most recent snapshot
            snapshots = sorted(snapshots_dir.glob('*.json'), reverse=True)
            if not snapshots:
                print("No snapshots to compare. Create one first with 'snapshot'")
                return
            snapshot_name = snapshots[0].stem
        
        snapshot_file = snapshots_dir / f'{snapshot_name}.json'
        if not snapshot_file.exists():
            print(f"Snapshot not found: {snapshot_name}")
            return
        
        old_data = json.loads(snapshot_file.read_text(encoding='utf-8'))
        old_profile = old_data.get('profile', {})
        
        current = self.get_structured_profile()
        
        print(f"\n📊 Profile Diff: {snapshot_name} → Now\n")
        print(f"   Snapshot: {old_data.get('timestamp', 'Unknown')[:10]}")
        print(f"   Current:  {datetime.now().strftime('%Y-%m-%d')}\n")
        
        # Compare technologies
        old_techs = set(old_profile.get('technologies', {}).keys())
        new_techs = set(current.get('technologies', {}).keys())
        
        added = new_techs - old_techs
        removed = old_techs - new_techs
        
        if added:
            print(f"   ➕ New technologies: {', '.join(added)}")
        if removed:
            print(f"   ➖ Removed: {', '.join(removed)}")
        
        # Compare project count
        old_ctx = old_profile.get('project_contexts', {})
        new_ctx = current.get('project_contexts', {})
        
        new_projects = set(new_ctx.keys()) - set(old_ctx.keys())
        if new_projects:
            print(f"   📁 New projects: {', '.join(list(new_projects)[:5])}")
        
        # Compare feedback
        old_fb = old_profile.get('feedback_summary', {})
        new_fb = current.get('feedback_summary', {})
        
        old_total = old_fb.get('total_outcomes', 0)
        new_total = new_fb.get('total_outcomes', 0)
        if new_total > old_total:
            print(f"   📝 New feedback entries: {new_total - old_total}")
        
        print()
        return {'added': list(added), 'removed': list(removed), 'new_projects': list(new_projects)}
    
    # ========== HEALTH CHECK ==========
    
    def health_check(self):
        """Verify all AI tool integrations are working"""
        print("\n🏥 Prompt Twin Health Check\n")
        
        checks = []
        
        # 1. Profile exists and has data
        has_profile = bool(self.profile.get('technologies'))
        print(f"   {'✅' if has_profile else '❌'} Profile: {'Has data' if has_profile else 'Empty - run scan'}")
        checks.append(('profile', has_profile))
        
        # 2. .cursorrules exists
        cursor_file = Path('.cursorrules')
        has_cursor = cursor_file.exists()
        print(f"   {'✅' if has_cursor else '⚠️'} Cursor: {'.cursorrules exists' if has_cursor else 'Not found - run inject'}")
        checks.append(('cursor', has_cursor))
        
        # 3. copilot-instructions.md exists
        copilot_file = Path('.github/copilot-instructions.md')
        has_copilot = copilot_file.exists()
        print(f"   {'✅' if has_copilot else '⚠️'} Copilot: {'copilot-instructions.md exists' if has_copilot else 'Not found - run inject'}")
        checks.append(('copilot', has_copilot))
        
        # 4. Ollama reachable
        try:
            r = urllib.request.urlopen('http://localhost:11434/api/version', timeout=3)
            version = json.loads(r.read()).get('version', 'unknown')
            has_ollama = True
            print(f"   ✅ Ollama: Running (v{version})")
        except:
            has_ollama = False
            print(f"   ⚠️  Ollama: Not reachable at localhost:11434")
        checks.append(('ollama', has_ollama))
        
        # 5. Git hook installed
        hook_file = Path('.git/hooks/post-commit')
        has_hook = hook_file.exists() and 'prompt_twin' in hook_file.read_text(errors='ignore')
        print(f"   {'✅' if has_hook else '⚠️'} Git Hook: {'Installed' if has_hook else 'Not installed - run hook'}")
        checks.append(('git_hook', has_hook))
        
        # 6. Config file
        config_file = DATA_DIR / 'config.json'
        has_config = config_file.exists()
        print(f"   {'✅' if has_config else 'ℹ️'} Config: {'Custom config' if has_config else 'Using defaults'}")
        checks.append(('config', True))  # Not a failure
        
        # 7. Feedback data
        has_feedback = FEEDBACK_FILE.exists() and FEEDBACK_FILE.stat().st_size > 0
        print(f"   {'✅' if has_feedback else 'ℹ️'} Feedback: {'Has entries' if has_feedback else 'No feedback yet'}")
        checks.append(('feedback', True))  # Not a failure
        
        # Summary
        passed = sum(1 for _, ok in checks if ok)
        total = len(checks)
        
        print(f"\n   Status: {passed}/{total} checks passed")
        
        if not has_profile:
            print("\n   💡 Run: python prompt_twin.py scan")
        if not has_cursor or not has_copilot:
            print("   💡 Run: python prompt_twin.py inject")
        if not has_ollama:
            print("   💡 Start Ollama: ollama serve")
        
        print()
        return all(ok for _, ok in checks[:4])  # First 4 are critical


def main():
    """CLI entry point"""
    twin = PromptTwin()
    
    if len(sys.argv) < 2:
        print(__doc__)
        twin.show_profile()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'scan':
        path = sys.argv[2] if len(sys.argv) > 2 else None
        twin.scan_projects(path)
        
    elif cmd == 'log':
        if len(sys.argv) < 3:
            print("Usage: python prompt_twin.py log 'your prompt here'")
            return
        prompt = ' '.join(sys.argv[2:])
        twin.log_prompt(prompt)
        
    elif cmd == 'context':
        if len(sys.argv) < 3:
            print("Usage: python prompt_twin.py context 'your query'")
            return
        query = ' '.join(sys.argv[2:])
        context = twin.get_context(query)
        print(json.dumps(context, indent=2))
        
    elif cmd == 'profile':
        twin.show_profile()
        
    elif cmd == 'export':
        twin.export_for_ai()
        
    elif cmd == 'pref':
        if len(sys.argv) < 4:
            print("Usage: python prompt_twin.py pref key value")
            return
        twin.set_preference(sys.argv[2], ' '.join(sys.argv[3:]))
    
    elif cmd == 'github':
        if len(sys.argv) < 3:
            print("Usage: python prompt_twin.py github <username>")
            print("Example: python prompt_twin.py github DJMcClellan1966")
            return
        username = sys.argv[2]
        twin.fetch_github_profile(username)
    
    elif cmd == 'inject':
        target = sys.argv[2] if len(sys.argv) > 2 else None
        twin.inject_context(target)
    
    elif cmd == 'feedback':
        twin.show_feedback()
    
    elif cmd == 'outcome':
        if len(sys.argv) < 4:
            print("Usage: python prompt_twin.py outcome 'action' 'success|failure|partial' [error]")
            return
        action = sys.argv[2]
        result = sys.argv[3]
        error = sys.argv[4] if len(sys.argv) > 4 else None
        twin.log_outcome(action, result, error=error)
    
    elif cmd == 'error':
        if len(sys.argv) < 4:
            print("Usage: python prompt_twin.py error 'ErrorType' 'error message' [file]")
            return
        error_type = sys.argv[2]
        message = sys.argv[3]
        file = sys.argv[4] if len(sys.argv) > 4 else None
        twin.log_error(error_type, message, file)
    
    elif cmd == 'correction':
        if len(sys.argv) < 4:
            print("Usage: python prompt_twin.py correction 'ai suggested' 'user wanted'")
            return
        ai_suggested = sys.argv[2]
        user_wrote = sys.argv[3]
        reason = sys.argv[4] if len(sys.argv) > 4 else None
        twin.log_correction(ai_suggested, user_wrote, reason)
    
    # ========== NEW COMMANDS ==========
    
    elif cmd == 'watch':
        path = sys.argv[2] if len(sys.argv) > 2 else None
        interval = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        twin.watch([path] if path else None, interval)
    
    elif cmd == 'hook':
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        twin.setup_git_hook(repo)
    
    elif cmd == 'structured':
        twin.export_structured()
    
    elif cmd == 'ollama':
        if len(sys.argv) < 3:
            print("Usage: python prompt_twin.py ollama 'your prompt' [model]")
            print("Example: python prompt_twin.py ollama 'write a flask api' qwen2.5:7b")
            return
        prompt = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else 'qwen2.5:7b'
        twin.test_with_ollama(prompt, model)
    
    elif cmd == 'nuanced':
        if len(sys.argv) < 4:
            print("Usage: python prompt_twin.py nuanced <category> 'description'")
            print("Categories: naming, deprecated, style, complexity, missing_context, wrong_tech, good")
            print("Example: python prompt_twin.py nuanced naming 'AI used camelCase instead of snake_case'")
            return
        category = sys.argv[2]
        description = ' '.join(sys.argv[3:])
        twin.log_nuanced_feedback(category, description)
    
    elif cmd == 'nuanced-summary':
        summary = twin.get_nuanced_feedback_summary()
        print(f"\n📊 Nuanced Feedback Summary ({summary['total']} total)\n")
        for cat, count in summary['counts'].items():
            print(f"  {cat}: {count}")
            for ex in summary['examples'].get(cat, []):
                print(f"    - {ex}")
    
    # ========== NEW HIGH-VALUE COMMANDS ==========
    
    elif cmd == 'mcp':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
        twin.start_mcp_server(port)
    
    elif cmd == 'config':
        if len(sys.argv) < 3:
            twin.show_config()
        elif sys.argv[2] == 'set' and len(sys.argv) >= 5:
            twin.set_config(sys.argv[3], ' '.join(sys.argv[4:]))
        else:
            print("Usage:")
            print("  python prompt_twin.py config              # Show config")
            print("  python prompt_twin.py config set KEY VAL  # Set value")
    
    elif cmd == 'analyze':
        twin.analyze_with_llm()
    
    elif cmd == 'suggest':
        desc = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None
        twin.suggest_templates(desc)
    
    elif cmd == 'snapshot':
        name = sys.argv[2] if len(sys.argv) > 2 else None
        twin.save_snapshot(name)
    
    elif cmd == 'snapshots':
        twin.list_snapshots()
    
    elif cmd == 'diff':
        name = sys.argv[2] if len(sys.argv) > 2 else None
        twin.diff_profile(name)
    
    elif cmd == 'health':
        twin.health_check()
        
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == '__main__':
    main()
