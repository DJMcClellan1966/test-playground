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

Advanced Analysis:
    python prompt_twin.py confidence              # Show inferences with confidence scores
    python prompt_twin.py privacy [path]          # Scan for secrets/sensitive data
    python prompt_twin.py temporal                # Analyze patterns with time decay
    python prompt_twin.py negative                # Show abandoned/error-prone patterns
    python prompt_twin.py clusters                # Group similar projects
    python prompt_twin.py explain                 # Explain preferences with evidence
    python prompt_twin.py contradictions          # Detect conflicting patterns
    python prompt_twin.py progression             # Show skill learning timeline
    python prompt_twin.py docs                    # Documentation quality metrics
    python prompt_twin.py agents                  # List multi-agent context views
    python prompt_twin.py agent-context <type>    # Get context for specific agent

Agent Types: code_review, scaffolding, debugging, documentation, default

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
    
    # ========== CONFIDENCE SCORES ==========
    
    def calculate_confidence(self, category, value, count, total_samples):
        """Calculate confidence score for an inference
        
        Returns:
            float: Confidence 0.0-1.0 based on sample size and consistency
        """
        if total_samples == 0:
            return 0.0
        
        # Base confidence from sample ratio
        ratio = count / total_samples
        
        # Adjust for sample size (more samples = more confident)
        sample_factor = min(1.0, total_samples / 10)  # Caps at 10 samples
        
        # Combine ratio and sample size
        confidence = ratio * (0.5 + 0.5 * sample_factor)
        
        return round(confidence, 2)
    
    def get_inferences_with_confidence(self):
        """Get all inferences with confidence scores and evidence"""
        inferences = []
        
        # Technology inferences
        techs = self.profile.get('technologies', {})
        total_projects = len(self.profile.get('projects', {}))
        
        for tech, count in sorted(techs.items(), key=lambda x: -x[1])[:15]:
            conf = self.calculate_confidence('technology', tech, count, total_projects)
            inferences.append({
                'category': 'technology',
                'value': tech,
                'confidence': conf,
                'evidence': f"{count}/{total_projects} projects",
                'sample_size': count,
            })
        
        # Language inferences
        langs = self.profile.get('languages', {})
        total_files = sum(langs.values())
        
        for lang, count in sorted(langs.items(), key=lambda x: -x[1])[:5]:
            conf = self.calculate_confidence('language', lang, count, total_files)
            inferences.append({
                'category': 'language',
                'value': lang,
                'confidence': conf,
                'evidence': f"{count}/{total_files} files",
                'sample_size': count,
            })
        
        # Git pattern inferences
        git_intents = self.profile.get('git_intents', {})
        total_commits = sum(git_intents.values())
        
        for intent, count in sorted(git_intents.items(), key=lambda x: -x[1])[:5]:
            conf = self.calculate_confidence('git_intent', intent, count, total_commits)
            inferences.append({
                'category': 'commit_style',
                'value': intent,
                'confidence': conf,
                'evidence': f"{count}/{total_commits} commits",
                'sample_size': count,
            })
        
        # Preference inferences (from feedback)
        feedback = self.get_feedback(100)
        corrections = [f for f in feedback if f.get('type') == 'correction']
        
        # Infer preferences from correction patterns
        if corrections:
            inferences.append({
                'category': 'feedback',
                'value': 'Corrections logged',
                'confidence': min(1.0, len(corrections) / 10),
                'evidence': f"{len(corrections)} corrections",
                'sample_size': len(corrections),
            })
        
        return sorted(inferences, key=lambda x: -x['confidence'])
    
    def show_confidence_report(self):
        """Display inferences with confidence scores"""
        inferences = self.get_inferences_with_confidence()
        
        print("\n📊 Inference Confidence Report\n")
        print("   Conf  | Category      | Value                 | Evidence")
        print("   " + "-" * 70)
        
        for inf in inferences[:20]:
            conf_bar = "█" * int(inf['confidence'] * 5) + "░" * (5 - int(inf['confidence'] * 5))
            print(f"   {conf_bar} {inf['confidence']:.0%} | {inf['category']:<12} | {inf['value']:<20} | {inf['evidence']}")
        
        print()
        
        # High confidence summary
        high_conf = [i for i in inferences if i['confidence'] >= 0.7]
        print(f"   ✅ High confidence (≥70%): {len(high_conf)} inferences")
        
        # Low confidence warnings
        low_conf = [i for i in inferences if i['confidence'] < 0.3]
        if low_conf:
            print(f"   ⚠️  Low confidence (<30%): {len(low_conf)} inferences - need more data")
        
        print()
        return inferences
    
    # ========== PRIVACY FILTERS ==========
    
    PRIVACY_PATTERNS = [
        (r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]'),
        (r'(?:api[_-]?key|apikey|secret|password|token|auth)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{8,}', '[REDACTED_SECRET]'),
        (r'sk-[a-zA-Z0-9]{32,}', '[OPENAI_KEY]'),
        (r'ghp_[a-zA-Z0-9]{36}', '[GITHUB_TOKEN]'),
        (r'(?:mongodb|postgres|mysql):\/\/[^\s"\']+', '[DATABASE_URL]'),
        (r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----', '[PRIVATE_KEY]'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        (r'(?:private|internal|confidential)[_\s]?(?:repo|project|code)', '[PRIVATE_PROJECT]'),
    ]
    
    def redact_sensitive(self, text):
        """Redact sensitive information from text"""
        if not text:
            return text
        
        redacted = text
        for pattern, replacement in self.PRIVACY_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        
        return redacted
    
    def get_redacted_profile(self):
        """Get profile with sensitive data redacted"""
        profile = self.get_structured_profile()
        
        # Redact project names that might be sensitive
        if 'project_contexts' in profile:
            redacted_contexts = {}
            for name, ctx in profile['project_contexts'].items():
                safe_name = self.redact_sensitive(name)
                redacted_contexts[safe_name] = ctx
            profile['project_contexts'] = redacted_contexts
        
        # Redact feedback
        if 'feedback_summary' in profile:
            fb = profile['feedback_summary']
            if 'recent_outcomes' in fb:
                fb['recent_outcomes'] = [
                    self.redact_sensitive(str(o)) for o in fb.get('recent_outcomes', [])
                ]
        
        return profile
    
    def scan_for_secrets(self, path=None):
        """Scan codebase for potential secrets that should be added to .gitignore"""
        path = Path(path) if path else DESKTOP
        
        print(f"\n🔐 Scanning for secrets in {path}\n")
        
        findings = []
        
        for ext in CODE_EXTENSIONS:
            for f in path.rglob(f'*{ext}'):
                if '.git' in str(f) or 'node_modules' in str(f):
                    continue
                try:
                    content = f.read_text(errors='ignore')[:50000]
                    for pattern, label in self.PRIVACY_PATTERNS:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            findings.append({
                                'file': str(f.relative_to(path)),
                                'type': label,
                                'count': len(matches),
                            })
                except Exception:
                    pass
        
        if findings:
            print(f"   ⚠️  Found {len(findings)} files with potential secrets:\n")
            for f in findings[:10]:
                print(f"   {f['type']}: {f['file']} ({f['count']} matches)")
            print("\n   💡 Consider adding these to .gitignore or using environment variables")
        else:
            print("   ✅ No obvious secrets detected")
        
        print()
        return findings
    
    # ========== TEMPORAL DECAY ==========
    
    def apply_temporal_decay(self, items, date_field='timestamp', half_life_days=90):
        """Apply temporal decay to weight recent items more heavily
        
        Args:
            items: List of dicts with timestamps
            date_field: Field containing ISO timestamp
            half_life_days: Days after which weight is halved
        """
        import math
        
        now = datetime.now()
        weighted = []
        
        for item in items:
            try:
                ts = item.get(date_field, '')
                if isinstance(ts, str) and ts:
                    item_date = datetime.fromisoformat(ts.replace('Z', '+00:00').split('+')[0])
                    days_old = (now - item_date).days
                    
                    # Exponential decay
                    weight = math.exp(-0.693 * days_old / half_life_days)
                else:
                    weight = 0.5  # Unknown date gets half weight
                
                weighted.append({**item, '_weight': round(weight, 3), '_days_old': days_old if 'days_old' in dir() else None})
            except Exception:
                weighted.append({**item, '_weight': 0.5})
        
        return sorted(weighted, key=lambda x: -x.get('_weight', 0))
    
    def get_temporal_analysis(self):
        """Analyze patterns with temporal weighting"""
        # Apply decay to commits
        commits = self.profile.get('git_commits', [])
        weighted_commits = self.apply_temporal_decay(commits, 'date')
        
        # Identify stale patterns
        stale = []
        techs = self.profile.get('technologies', {})
        
        # Check each technology's recency
        for tech, count in techs.items():
            # Look for recent commits mentioning this tech
            recent_mentions = sum(1 for c in weighted_commits[:20] 
                                if tech.lower() in c.get('message', '').lower())
            if count > 3 and recent_mentions == 0:
                stale.append(tech)
        
        return {
            'total_commits': len(commits),
            'recent_commits': len([c for c in weighted_commits if c.get('_weight', 0) > 0.5]),
            'stale_technologies': stale,
            'active_technologies': [t for t in list(techs.keys())[:10] if t not in stale],
        }
    
    def show_temporal_report(self):
        """Show temporal analysis of patterns"""
        analysis = self.get_temporal_analysis()
        
        print("\n⏱️  Temporal Pattern Analysis\n")
        print(f"   Total commits: {analysis['total_commits']}")
        print(f"   Recent (high weight): {analysis['recent_commits']}")
        
        if analysis['stale_technologies']:
            print(f"\n   ⚠️  Stale technologies (no recent activity):")
            for tech in analysis['stale_technologies'][:5]:
                print(f"      - {tech}")
        
        print(f"\n   ✅ Active technologies:")
        for tech in analysis['active_technologies'][:5]:
            print(f"      - {tech}")
        
        print()
        return analysis
    
    # ========== NEGATIVE PATTERNS ==========
    
    def track_negative_patterns(self):
        """Track abandoned technologies and error-prone approaches"""
        negative = {
            'abandoned': [],
            'error_prone': [],
            'refactored_away': [],
        }
        
        # Find abandoned technologies (in old commits, not in recent)
        commits = self.profile.get('git_commits', [])
        old_commits = commits[20:] if len(commits) > 20 else []
        recent_commits = commits[:20]
        
        # Technologies mentioned in old but not recent
        old_techs = set()
        recent_techs = set()
        
        for c in old_commits:
            msg = c.get('message', '').lower()
            for tech in self.profile.get('technologies', {}):
                if tech.lower() in msg:
                    old_techs.add(tech)
        
        for c in recent_commits:
            msg = c.get('message', '').lower()
            for tech in self.profile.get('technologies', {}):
                if tech.lower() in msg:
                    recent_techs.add(tech)
        
        negative['abandoned'] = list(old_techs - recent_techs)
        
        # Error-prone: technologies with high error rates
        feedback = self.get_feedback(200)
        error_counts = Counter()
        
        for entry in feedback:
            if entry.get('type') == 'error':
                error_type = entry.get('error_type', '')
                if error_type:
                    error_counts[error_type] += 1
        
        negative['error_prone'] = [
            {'type': t, 'count': c} 
            for t, c in error_counts.most_common(5)
            if c > 2
        ]
        
        # Refactored away: look for "remove", "delete", "migrate from" in commits
        refactor_keywords = ['remove', 'delete', 'migrate from', 'replace', 'drop', 'deprecate']
        for c in commits[:50]:
            msg = c.get('message', '').lower()
            if any(kw in msg for kw in refactor_keywords):
                negative['refactored_away'].append({
                    'message': c.get('message', '')[:80],
                    'date': c.get('date', '')[:10],
                })
        
        negative['refactored_away'] = negative['refactored_away'][:5]
        
        return negative
    
    def show_negative_patterns(self):
        """Display negative patterns to help AI avoid mistakes"""
        patterns = self.track_negative_patterns()
        
        print("\n🚫 Negative Patterns (Things to Avoid)\n")
        
        if patterns['abandoned']:
            print("   📦 Abandoned Technologies:")
            for tech in patterns['abandoned'][:5]:
                print(f"      - {tech}")
        
        if patterns['error_prone']:
            print("\n   ⚠️  Error-Prone Patterns:")
            for p in patterns['error_prone']:
                print(f"      - {p['type']}: {p['count']} errors")
        
        if patterns['refactored_away']:
            print("\n   🔄 Recently Refactored Away:")
            for r in patterns['refactored_away']:
                print(f"      - {r['message']} ({r['date']})")
        
        if not any(patterns.values()):
            print("   No negative patterns detected yet")
        
        print()
        return patterns
    
    # ========== SEMANTIC CLUSTERING ==========
    
    def cluster_projects(self):
        """Group similar projects to identify true patterns vs one-offs"""
        projects = self.profile.get('projects', {})
        
        clusters = defaultdict(list)
        
        for name, proj in projects.items():
            # Create a fingerprint based on technologies
            techs = tuple(sorted(proj.get('technologies', [])))
            types = tuple(sorted(proj.get('types', [])))
            
            # Cluster by primary type + tech combo
            key = f"{types[0] if types else 'unknown'}_{techs[0] if techs else 'unknown'}"
            clusters[key].append({
                'name': name,
                'technologies': proj.get('technologies', []),
                'types': proj.get('types', []),
            })
        
        # Analyze clusters
        analysis = {
            'clusters': {},
            'one_offs': [],
            'true_patterns': [],
        }
        
        for key, items in clusters.items():
            if len(items) == 1:
                analysis['one_offs'].append(items[0]['name'])
            else:
                analysis['clusters'][key] = {
                    'count': len(items),
                    'projects': [i['name'] for i in items],
                }
                analysis['true_patterns'].append(key)
        
        return analysis
    
    def show_cluster_analysis(self):
        """Show project clustering analysis"""
        analysis = self.cluster_projects()
        
        print("\n🎯 Pattern Clustering Analysis\n")
        
        print(f"   True Patterns (repeated across projects):")
        for pattern in analysis['true_patterns'][:5]:
            cluster = analysis['clusters'][pattern]
            print(f"      - {pattern}: {cluster['count']} projects")
        
        if analysis['one_offs']:
            print(f"\n   ⚡ One-off Experiments ({len(analysis['one_offs'])}):")
            for name in analysis['one_offs'][:3]:
                print(f"      - {name}")
        
        print()
        return analysis
    
    # ========== PREFERENCE EXPLANATIONS ==========
    
    def explain_preferences(self):
        """Link each preference to supporting evidence"""
        explanations = []
        
        techs = self.profile.get('technologies', {})
        total = sum(techs.values())
        
        # Local-first preference
        local_techs = ['SQLite', 'Ollama', 'Local']
        local_count = sum(techs.get(t, 0) for t in local_techs)
        if local_count > 0:
            pct = (local_count / total * 100) if total > 0 else 0
            explanations.append({
                'preference': 'Local-first development',
                'confidence': min(1.0, pct / 50),
                'evidence': f"{pct:.0f}% of projects use local tech (SQLite, Ollama)",
                'supporting_projects': local_count,
            })
        
        # Single-file preference
        if techs.get('Flask', 0) > techs.get('Django', 0):
            explanations.append({
                'preference': 'Lightweight frameworks',
                'confidence': 0.8 if techs.get('Flask', 0) > 3 else 0.5,
                'evidence': f"Flask ({techs.get('Flask', 0)}) preferred over Django ({techs.get('Django', 0)})",
                'supporting_projects': techs.get('Flask', 0),
            })
        
        # Python preference
        langs = self.profile.get('languages', {})
        py_files = langs.get('.py', 0)
        total_files = sum(langs.values())
        if py_files > total_files * 0.5:
            explanations.append({
                'preference': 'Python-first development',
                'confidence': min(1.0, py_files / total_files),
                'evidence': f"{py_files}/{total_files} files ({py_files/total_files*100:.0f}%) are Python",
                'supporting_projects': py_files,
            })
        
        # ML/AI focus
        ml_techs = ['Machine Learning', 'OpenAI', 'LangChain', 'Ollama']
        ml_count = sum(techs.get(t, 0) for t in ml_techs)
        if ml_count > 0:
            explanations.append({
                'preference': 'AI/ML integration focus',
                'confidence': min(1.0, ml_count / 5),
                'evidence': f"{ml_count} projects use ML/AI technologies",
                'supporting_projects': ml_count,
            })
        
        return explanations
    
    def show_preference_explanations(self):
        """Display preferences with their evidence"""
        explanations = self.explain_preferences()
        
        print("\n📋 Preference Explanations\n")
        
        for exp in sorted(explanations, key=lambda x: -x['confidence']):
            conf_pct = exp['confidence'] * 100
            bar = "█" * int(exp['confidence'] * 5) + "░" * (5 - int(exp['confidence'] * 5))
            print(f"   {bar} {conf_pct:.0f}% {exp['preference']}")
            print(f"         └─ {exp['evidence']}")
            print()
        
        return explanations
    
    # ========== CONTRADICTION DETECTION ==========
    
    def detect_contradictions(self):
        """Flag when current work conflicts with historical patterns"""
        contradictions = []
        
        techs = self.profile.get('technologies', {})
        
        # Check for contradicting technology choices
        contradicting_pairs = [
            ('Flask', 'Django'),
            ('SQLite', 'PostgreSQL'),
            ('REST', 'GraphQL'),
            ('Ollama', 'OpenAI'),
        ]
        
        for tech_a, tech_b in contradicting_pairs:
            count_a = techs.get(tech_a, 0)
            count_b = techs.get(tech_b, 0)
            
            if count_a > 0 and count_b > 0:
                # Both are used - potential contradiction
                if count_a > count_b * 2:
                    contradictions.append({
                        'type': 'technology_mix',
                        'primary': tech_a,
                        'secondary': tech_b,
                        'message': f"Primary pattern is {tech_a} ({count_a}) but also using {tech_b} ({count_b})",
                        'severity': 'low' if count_b < 2 else 'medium',
                    })
        
        # Check feedback contradictions
        feedback = self.get_feedback(100)
        corrections = [f for f in feedback if f.get('type') == 'correction']
        
        # Look for repeated corrections of the same thing
        correction_counts = Counter()
        for c in corrections:
            pattern = c.get('ai_suggested', '')[:30]
            correction_counts[pattern] += 1
        
        for pattern, count in correction_counts.most_common(3):
            if count > 2:
                contradictions.append({
                    'type': 'repeated_correction',
                    'pattern': pattern,
                    'count': count,
                    'message': f"Repeatedly correcting: '{pattern}' ({count} times)",
                    'severity': 'high',
                })
        
        return contradictions
    
    def show_contradictions(self):
        """Display detected contradictions"""
        contradictions = self.detect_contradictions()
        
        print("\n⚡ Contradiction Detection\n")
        
        if not contradictions:
            print("   ✅ No significant contradictions detected")
        else:
            for c in contradictions:
                icon = "🔴" if c['severity'] == 'high' else "🟡" if c['severity'] == 'medium' else "🟢"
                print(f"   {icon} {c['message']}")
        
        print()
        return contradictions
    
    # ========== SKILL PROGRESSION ==========
    
    def track_skill_progression(self):
        """Show technology adoption timeline and learning curves"""
        commits = self.profile.get('git_commits', [])
        
        # Group commits by month
        monthly = defaultdict(lambda: {'technologies': Counter(), 'count': 0})
        
        for c in commits:
            date = c.get('date', '')[:7]  # YYYY-MM
            if date:
                monthly[date]['count'] += 1
                msg = c.get('message', '').lower()
                
                # Detect technologies in commit messages
                for tech in ['flask', 'sqlite', 'ollama', 'openai', 'machine learning', 'auth']:
                    if tech in msg:
                        monthly[date]['technologies'][tech.title()] += 1
        
        # Build timeline
        timeline = []
        sorted_months = sorted(monthly.keys())
        
        for month in sorted_months[-12:]:  # Last 12 months
            data = monthly[month]
            timeline.append({
                'month': month,
                'commits': data['count'],
                'new_technologies': list(data['technologies'].keys()),
            })
        
        # Identify learning trajectory
        all_techs_by_month = {}
        seen_techs = set()
        
        for month in sorted_months:
            new_this_month = set(monthly[month]['technologies'].keys()) - seen_techs
            if new_this_month:
                all_techs_by_month[month] = list(new_this_month)
            seen_techs.update(monthly[month]['technologies'].keys())
        
        return {
            'timeline': timeline,
            'tech_adoption': all_techs_by_month,
            'total_technologies_learned': len(seen_techs),
        }
    
    def show_skill_progression(self):
        """Display skill progression timeline"""
        progression = self.track_skill_progression()
        
        print("\n📈 Skill Progression Timeline\n")
        
        if progression['tech_adoption']:
            print("   Technology Adoption:")
            for month, techs in list(progression['tech_adoption'].items())[-6:]:
                print(f"      {month}: + {', '.join(techs)}")
        
        print(f"\n   Total technologies tracked: {progression['total_technologies_learned']}")
        
        if progression['timeline']:
            print("\n   Recent Activity:")
            for entry in progression['timeline'][-3:]:
                print(f"      {entry['month']}: {entry['commits']} commits")
        
        print()
        return progression
    
    # ========== DOCUMENTATION QUALITY ==========
    
    def analyze_documentation_quality(self):
        """Analyze documentation quality metrics"""
        projects = self.profile.get('projects', {})
        
        metrics = {
            'projects_with_readme': 0,
            'total_projects': len(projects),
            'comment_density': 'unknown',
            'doc_files': 0,
        }
        
        # Check for READMEs and docs
        for name, proj in projects.items():
            files = proj.get('files', [])
            if isinstance(files, list):
                if any('readme' in str(f).lower() for f in files):
                    metrics['projects_with_readme'] += 1
                metrics['doc_files'] += sum(1 for f in files if str(f).endswith(('.md', '.rst', '.txt')))
        
        # Calculate ratio
        if metrics['total_projects'] > 0:
            metrics['readme_ratio'] = metrics['projects_with_readme'] / metrics['total_projects']
        else:
            metrics['readme_ratio'] = 0
        
        # Quality score
        metrics['quality_score'] = min(1.0, (
            metrics['readme_ratio'] * 0.5 +
            min(1.0, metrics['doc_files'] / 20) * 0.5
        ))
        
        return metrics
    
    def show_doc_quality(self):
        """Display documentation quality report"""
        metrics = self.analyze_documentation_quality()
        
        print("\n📚 Documentation Quality\n")
        print(f"   Projects with README: {metrics['projects_with_readme']}/{metrics['total_projects']}")
        print(f"   Documentation files: {metrics['doc_files']}")
        print(f"   Quality score: {metrics['quality_score']*100:.0f}%")
        
        if metrics['quality_score'] < 0.5:
            print("\n   💡 Tip: Add READMEs to your projects")
        
        print()
        return metrics
    
    # ========== MULTI-AGENT CONTEXT ==========
    
    def get_context_for_agent(self, agent_type='default'):
        """Get context optimized for specific AI agent types
        
        Args:
            agent_type: 'code_review', 'scaffolding', 'debugging', 'documentation', 'default'
        """
        base_profile = self._get_profile_summary()
        
        views = {
            'code_review': {
                'focus': 'quality_and_patterns',
                'include': ['coding_style', 'error_patterns', 'corrections', 'contradictions'],
                'style_notes': self.analyze_coding_style(),
                'common_errors': self._analyze_common_errors(),
                'negative_patterns': self.track_negative_patterns(),
            },
            'scaffolding': {
                'focus': 'architecture_and_stack',
                'include': ['technologies', 'project_types', 'templates'],
                'tech_stack': dict(base_profile.get('top_technologies', [])[:10]),
                'project_types': dict(self.profile.get('project_types', {}).most_common(5) if hasattr(self.profile.get('project_types', {}), 'most_common') else list(self.profile.get('project_types', {}).items())[:5]),
            },
            'debugging': {
                'focus': 'errors_and_fixes',
                'include': ['common_errors', 'corrections', 'error_patterns'],
                'errors': self._analyze_common_errors(),
                'feedback': self.get_feedback_summary(),
                'negative_patterns': self.track_negative_patterns().get('error_prone', []),
            },
            'documentation': {
                'focus': 'clarity_and_style',
                'include': ['doc_quality', 'project_structure', 'naming'],
                'doc_metrics': self.analyze_documentation_quality(),
                'style': self.analyze_coding_style(),
            },
            'default': {
                'focus': 'general',
                'include': ['all'],
                'full_profile': base_profile,
            },
        }
        
        return views.get(agent_type, views['default'])
    
    def show_agent_contexts(self):
        """Show available agent context types"""
        agent_types = ['code_review', 'scaffolding', 'debugging', 'documentation', 'default']
        
        print("\n🤖 Multi-Agent Context Views\n")
        
        for agent in agent_types:
            ctx = self.get_context_for_agent(agent)
            print(f"   {agent}:")
            print(f"      Focus: {ctx['focus']}")
            print(f"      Includes: {', '.join(ctx['include'])}")
            print()
        
        print("   Usage: GET /mcp/context?agent_type=code_review")


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
    
    # ========== ADVANCED ANALYSIS COMMANDS ==========
    
    elif cmd == 'confidence':
        twin.show_confidence_report()
    
    elif cmd == 'privacy' or cmd == 'secrets':
        path = sys.argv[2] if len(sys.argv) > 2 else None
        twin.scan_for_secrets(path)
    
    elif cmd == 'temporal':
        twin.show_temporal_report()
    
    elif cmd == 'negative':
        twin.show_negative_patterns()
    
    elif cmd == 'clusters':
        twin.show_cluster_analysis()
    
    elif cmd == 'explain':
        twin.show_preference_explanations()
    
    elif cmd == 'contradictions':
        twin.show_contradictions()
    
    elif cmd == 'progression':
        twin.show_skill_progression()
    
    elif cmd == 'docs':
        twin.show_doc_quality()
    
    elif cmd == 'agents':
        twin.show_agent_contexts()
    
    elif cmd == 'agent-context':
        agent_type = sys.argv[2] if len(sys.argv) > 2 else 'default'
        context = twin.get_context_for_agent(agent_type)
        print(json.dumps(context, indent=2, default=str))
        
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == '__main__':
    main()
