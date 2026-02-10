"""
Prompt Twin - Build a local context profile from your coding patterns
======================================================================

This tool:
1. Scans your projects to understand what you build and how
2. Maintains a prompt log you can add to over time
3. Provides context that AI agents can query for better understanding
4. Fetches GitHub profile data (repos, commits, READMEs)
5. Injects context into AI tools (Cursor, VS Code, Ollama)

Usage:
    python prompt_twin.py scan                    # Scan desktop for patterns
    python prompt_twin.py log "your prompt here"  # Add a prompt to history
    python prompt_twin.py context "question"      # Get relevant context
    python prompt_twin.py profile                 # Show your profile
    python prompt_twin.py export                  # Export profile to markdown
    python prompt_twin.py github <username>       # Fetch GitHub data
    python prompt_twin.py inject                  # Inject context into AI tools
    
Feedback Loop (reality grounding):
    python prompt_twin.py feedback                # Show feedback summary
    python prompt_twin.py outcome "action" "success|failure" [error]
    python prompt_twin.py error "ErrorType" "message" [file]
    python prompt_twin.py correction "ai said" "user wanted"
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
    
    def set_preference(self, key, value):
        """Set a user preference"""
        if 'preferences' not in self.profile:
            self.profile['preferences'] = {}
        self.profile['preferences'][key] = value
        self._save_profile()
        print(f"Set preference: {key} = {value}")


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
        
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == '__main__':
    main()
