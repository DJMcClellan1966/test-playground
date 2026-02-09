"""
Learning Integration - Bridges ML-ToolBox with Blueprints System

Integrates:
1. Enhanced Code Generator - Working code patterns (tic-tac-toe, todo, etc.)
2. AI Learning Companion - Adaptive progression tracking
3. Level-gated blocks - Unlock advanced features as user grows

Target: Beginners who grow with the system
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class SkillLevel(Enum):
    """User skill levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class LearningProfile:
    """Tracks user's learning progress"""
    level: SkillLevel = SkillLevel.BEGINNER
    projects_completed: int = 0
    blocks_used: Set[str] = field(default_factory=set)
    concepts_learned: Set[str] = field(default_factory=set)
    weak_areas: List[str] = field(default_factory=list)
    strong_areas: List[str] = field(default_factory=list)
    xp: int = 0  # Experience points
    achievements: Set[str] = field(default_factory=set)  # Earned achievements
    streak_days: int = 0  # Learning streak
    last_activity_date: str = ""  # ISO date string
    
    def to_dict(self) -> Dict:
        return {
            'level': self.level.value,
            'projects_completed': self.projects_completed,
            'blocks_used': list(self.blocks_used),
            'concepts_learned': list(self.concepts_learned),
            'weak_areas': self.weak_areas,
            'strong_areas': self.strong_areas,
            'xp': self.xp,
            'achievements': list(self.achievements),
            'streak_days': self.streak_days,
            'last_activity_date': self.last_activity_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "LearningProfile":
        profile = cls()
        profile.level = SkillLevel(data.get('level', 'beginner'))
        profile.projects_completed = data.get('projects_completed', 0)
        profile.blocks_used = set(data.get('blocks_used', []))
        profile.concepts_learned = set(data.get('concepts_learned', []))
        profile.weak_areas = data.get('weak_areas', [])
        profile.strong_areas = data.get('strong_areas', [])
        profile.xp = data.get('xp', 0)
        profile.achievements = set(data.get('achievements', []))
        profile.streak_days = data.get('streak_days', 0)
        profile.last_activity_date = data.get('last_activity_date', '')
        return profile


# ============================================================================
# ACHIEVEMENTS SYSTEM
# ============================================================================

ACHIEVEMENTS = {
    # Progression achievements
    'first_steps': {
        'name': '🐣 First Steps',
        'description': 'Complete your first project',
        'condition': lambda p: p.projects_completed >= 1,
        'xp_bonus': 10
    },
    'getting_started': {
        'name': '🚀 Getting Started',
        'description': 'Reach 100 XP',
        'condition': lambda p: p.xp >= 100,
        'xp_bonus': 25
    },
    'level_up': {
        'name': '⬆️ Level Up!',
        'description': 'Reach Intermediate level',
        'condition': lambda p: p.level != SkillLevel.BEGINNER,
        'xp_bonus': 50
    },
    'advanced_learner': {
        'name': '🎓 Advanced Learner',
        'description': 'Reach Advanced level',
        'condition': lambda p: p.level in [SkillLevel.ADVANCED, SkillLevel.EXPERT],
        'xp_bonus': 100
    },
    'expert_coder': {
        'name': '👑 Expert Coder',
        'description': 'Reach Expert level',
        'condition': lambda p: p.level == SkillLevel.EXPERT,
        'xp_bonus': 200
    },
    
    # Project achievements  
    'project_trio': {
        'name': '🎯 Project Trio',
        'description': 'Complete 3 projects',
        'condition': lambda p: p.projects_completed >= 3,
        'xp_bonus': 30
    },
    'project_master': {
        'name': '📚 Project Master',
        'description': 'Complete 10 projects',
        'condition': lambda p: p.projects_completed >= 10,
        'xp_bonus': 100
    },
    'completionist': {
        'name': '🏆 Completionist',
        'description': 'Complete 20 projects',
        'condition': lambda p: p.projects_completed >= 20,
        'xp_bonus': 250
    },
    
    # Concept achievements
    'curious_mind': {
        'name': '🧠 Curious Mind',
        'description': 'Learn 5 different concepts',
        'condition': lambda p: len(p.concepts_learned) >= 5,
        'xp_bonus': 25
    },
    'knowledge_seeker': {
        'name': '📖 Knowledge Seeker',
        'description': 'Learn 15 different concepts',
        'condition': lambda p: len(p.concepts_learned) >= 15,
        'xp_bonus': 75
    },
    'polymath': {
        'name': '🌟 Polymath',
        'description': 'Learn 30 different concepts',
        'condition': lambda p: len(p.concepts_learned) >= 30,
        'xp_bonus': 150
    },
    
    # Block usage achievements
    'block_explorer': {
        'name': '🧱 Block Explorer',
        'description': 'Use 5 different blocks',
        'condition': lambda p: len(p.blocks_used) >= 5,
        'xp_bonus': 20
    },
    'block_master': {
        'name': '🏗️ Block Master',
        'description': 'Use 15 different blocks',
        'condition': lambda p: len(p.blocks_used) >= 15,
        'xp_bonus': 60
    },
    
    # Streak achievements
    'on_fire': {
        'name': '🔥 On Fire!',
        'description': 'Maintain a 3-day learning streak',
        'condition': lambda p: p.streak_days >= 3,
        'xp_bonus': 30
    },
    'dedicated': {
        'name': '💪 Dedicated',
        'description': 'Maintain a 7-day learning streak',
        'condition': lambda p: p.streak_days >= 7,
        'xp_bonus': 75
    },
    'unstoppable': {
        'name': '⚡ Unstoppable',
        'description': 'Maintain a 30-day learning streak',
        'condition': lambda p: p.streak_days >= 30,
        'xp_bonus': 300
    },
    
    # Special achievements  
    'algorithm_enthusiast': {
        'name': '🔢 Algorithm Enthusiast',
        'description': 'Learn 3 algorithm concepts',
        'condition': lambda p: len([c for c in p.concepts_learned if c in ['algorithms', 'sorting', 'searching', 'dynamic_programming', 'backtracking', 'greedy', 'divide_and_conquer']]) >= 3,
        'xp_bonus': 50
    },
    'data_wizard': {
        'name': '🗄️ Data Wizard',
        'description': 'Learn database concepts',
        'condition': lambda p: 'sql' in p.concepts_learned or 'databases' in p.concepts_learned,
        'xp_bonus': 40
    },
    'ml_explorer': {
        'name': '🤖 ML Explorer',
        'description': 'Learn 2 ML concepts',
        'condition': lambda p: len([c for c in p.concepts_learned if c in ['ml_fundamentals', 'model_selection', 'model_evaluation', 'entropy', 'information_theory']]) >= 2,
        'xp_bonus': 60
    },
}


# ============================================================================
# LEVEL-GATED BLOCKS
# ============================================================================

# Blocks available at each level
LEVEL_BLOCKS = {
    SkillLevel.BEGINNER: {
        'storage_json': {
            'name': 'JSON Storage',
            'description': 'Simple file-based storage. Perfect for learning!',
            'teaches': ['data persistence', 'JSON format', 'file I/O'],
            'xp_reward': 10,
        },
        'crud_basic': {
            'name': 'Basic CRUD',
            'description': 'Create, Read, Update, Delete operations',
            'teaches': ['CRUD pattern', 'HTTP methods', 'REST basics'],
            'xp_reward': 15,
        },
        'console_ui': {
            'name': 'Console UI',
            'description': 'Text-based user interface',
            'teaches': ['user input', 'output formatting', 'menus'],
            'xp_reward': 10,
        },
    },
    SkillLevel.INTERMEDIATE: {
        'storage_sqlite': {
            'name': 'SQLite Storage',
            'description': 'Relational database. Unlocked after JSON mastery!',
            'teaches': ['SQL', 'relational data', 'queries', 'joins'],
            'requires_concepts': ['data persistence'],
            'xp_reward': 25,
        },
        'auth_basic': {
            'name': 'Basic Auth',
            'description': 'User authentication with sessions',
            'teaches': ['authentication', 'sessions', 'security basics'],
            'requires_concepts': ['CRUD pattern'],
            'xp_reward': 30,
        },
        'flask_routes': {
            'name': 'Flask Routes',
            'description': 'Web routes with Flask',
            'teaches': ['web routing', 'HTTP', 'request/response'],
            'requires_concepts': ['REST basics'],
            'xp_reward': 25,
        },
        'html_ui': {
            'name': 'HTML UI',
            'description': 'Web-based user interface',
            'teaches': ['HTML', 'CSS basics', 'forms'],
            'requires_concepts': ['user input'],
            'xp_reward': 20,
        },
    },
    SkillLevel.ADVANCED: {
        'storage_postgres': {
            'name': 'PostgreSQL',
            'description': 'Production database. For serious apps!',
            'teaches': ['production DB', 'migrations', 'connection pooling'],
            'requires_concepts': ['SQL', 'relational data'],
            'xp_reward': 40,
        },
        'auth_oauth': {
            'name': 'OAuth',
            'description': 'Third-party authentication (Google, GitHub)',
            'teaches': ['OAuth flow', 'tokens', 'identity providers'],
            'requires_concepts': ['authentication', 'sessions'],
            'xp_reward': 45,
        },
        'crdt_sync': {
            'name': 'CRDT Sync',
            'description': 'Conflict-free sync for offline + multi-user',
            'teaches': ['CRDTs', 'distributed systems', 'conflict resolution'],
            'requires_concepts': ['data persistence', 'REST basics'],
            'xp_reward': 50,
        },
        'websocket': {
            'name': 'WebSocket',
            'description': 'Real-time bidirectional communication',
            'teaches': ['WebSocket', 'real-time', 'push notifications'],
            'requires_concepts': ['HTTP', 'web routing'],
            'xp_reward': 40,
        },
    },
    SkillLevel.EXPERT: {
        'kubernetes': {
            'name': 'Kubernetes Deploy',
            'description': 'Container orchestration',
            'teaches': ['containers', 'orchestration', 'scaling'],
            'requires_concepts': ['production DB', 'migrations'],
            'xp_reward': 60,
        },
        'graphql': {
            'name': 'GraphQL API',
            'description': 'Flexible query language for APIs',
            'teaches': ['GraphQL', 'schemas', 'resolvers'],
            'requires_concepts': ['REST basics', 'SQL'],
            'xp_reward': 55,
        },
    },
}


# ============================================================================
# WORKING CODE PATTERNS - Loaded from patterns/ directory
# ============================================================================

def _load_patterns() -> Dict[str, Any]:
    """Load code patterns from external files for cleaner code organization."""
    import json
    patterns_dir = Path(__file__).parent / "patterns"
    metadata_path = patterns_dir / "metadata.json"
    
    if not metadata_path.exists():
        return {}  # Fall back to empty if not extracted yet
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    patterns = {}
    for pattern_id, meta in metadata.items():
        code_path = patterns_dir / f"{pattern_id}.py"
        code = ""
        if code_path.exists():
            with open(code_path, 'r', encoding='utf-8') as f:
                code = f.read()
        
        # Convert level string back to enum
        level_str = meta['level']
        level = SkillLevel.BEGINNER
        for sl in SkillLevel:
            if sl.value == level_str:
                level = sl
                break
        
        patterns[pattern_id] = {
            'level': level,
            'name': meta['name'],
            'description': meta['description'],
            'teaches': meta['teaches'],
            'xp_reward': meta['xp_reward'],
            'code': code,
        }
    
    return patterns


# Load patterns at module import time
CODE_PATTERNS = _load_patterns()


# ============================================================================
# ORACLE RULES (from algorithm-oracle)
# ============================================================================

ORACLE_RULES = {
    'text_safety': {
        'profile': ['text', 'safety_critical'],
        'pattern': 'Rule-Based + Ensemble',
        'suggestion': 'Start with rule-based filters, add ML ensemble with human review',
        'why': 'Text safety requires interpretability and explicit rules for compliance'
    },
    'high_dim_few_samples': {
        'profile': ['high_dimensional', 'few_samples'],
        'pattern': 'Regularized Linear + Feature Selection',
        'suggestion': 'Use L1/L2 regularization, PCA, or tree-based feature importance',
        'why': 'High dimensions with few samples causes overfitting; reduce effective dimensionality'
    },
    'unsupervised_clustering': {
        'profile': ['unsupervised', 'clustering'],
        'pattern': 'K-Means → DBSCAN → Hierarchical',
        'suggestion': 'Start with K-Means for speed, try DBSCAN for arbitrary shapes',
        'why': 'K-Means is fast baseline; DBSCAN handles noise; hierarchical shows structure'
    },
    'need_interpretability': {
        'profile': ['need_interpretability'],
        'pattern': 'Decision Tree → Rules → SHAP',
        'suggestion': 'Use decision trees or extract rules; add SHAP for complex models',
        'why': 'Trees are inherently interpretable; SHAP explains black-box models'
    },
    'imbalanced_classes': {
        'profile': ['imbalanced'],
        'pattern': 'SMOTE + Class Weights + Threshold Tuning',
        'suggestion': 'Oversample minority, adjust class weights, tune decision threshold',
        'why': 'Standard metrics mislead on imbalanced data; balance or re-weight'
    },
    'streaming_data': {
        'profile': ['streaming', 'online_learning'],
        'pattern': 'Online Learning + Sliding Window',
        'suggestion': 'Use online algorithms (SGD), sliding windows for drift detection',
        'why': 'Batch models fail on streaming; need incremental updates'
    },
    'nonlinear_patterns': {
        'profile': ['nonlinear', 'complex_interactions'],
        'pattern': 'Gradient Boosting → Neural Network',
        'suggestion': 'XGBoost/LightGBM for tabular; neural nets for unstructured',
        'why': 'Linear models miss interactions; boosting captures nonlinearity efficiently'
    },
    'binary_classification': {
        'profile': ['binary_classification', 'tabular'],
        'pattern': 'Logistic → Random Forest → XGBoost',
        'suggestion': 'Start with logistic regression baseline, then ensemble methods',
        'why': 'Logistic is interpretable baseline; ensembles usually improve accuracy'
    },
    'regression': {
        'profile': ['regression', 'continuous_target'],
        'pattern': 'Linear → Ridge → Gradient Boosting',
        'suggestion': 'Linear regression first, add regularization, then try boosting',
        'why': 'Linear is interpretable; regularization prevents overfitting; boosting for nonlinear'
    },
    'multi_class': {
        'profile': ['multi_class', 'many_categories'],
        'pattern': 'Softmax → One-vs-Rest → Hierarchical',
        'suggestion': 'Softmax for few classes, OvR for many, hierarchical for structure',
        'why': 'Softmax is natural multi-class; OvR scales better; hierarchical uses domain'
    },
}


def query_oracle(profile_tags: List[str]) -> List[dict]:
    """
    Query the oracle for pattern suggestions based on problem profile.
    
    Args:
        profile_tags: List of problem characteristics like 
                      ['text', 'safety_critical'] or ['imbalanced', 'binary_classification']
    
    Returns:
        List of matching rules with pattern suggestions
    """
    matches = []
    for rule_id, rule in ORACLE_RULES.items():
        score = sum(1 for tag in rule['profile'] if tag in profile_tags)
        if score > 0:
            matches.append({
                'rule_id': rule_id,
                'score': score,
                'pattern': rule['pattern'],
                'suggestion': rule['suggestion'],
                'why': rule['why']
            })
    
    return sorted(matches, key=lambda x: x['score'], reverse=True)


# ============================================================================
# LEARNING SYSTEM
# ============================================================================

class LearningSystem:
    """
    Manages user progression through skill levels
    """
    
    # XP thresholds for each level
    LEVEL_THRESHOLDS = {
        SkillLevel.BEGINNER: 0,
        SkillLevel.INTERMEDIATE: 100,
        SkillLevel.ADVANCED: 300,
        SkillLevel.EXPERT: 600,
    }
    
    def __init__(self, profile_path: str = "learning_profile.json"):
        self.profile_path = Path(profile_path)
        self.profile = self._load_profile()
    
    def _load_profile(self) -> LearningProfile:
        """Load user profile from file"""
        if self.profile_path.exists():
            with open(self.profile_path, 'r') as f:
                return LearningProfile.from_dict(json.load(f))
        return LearningProfile()
    
    def save_profile(self):
        """Save user profile to file"""
        with open(self.profile_path, 'w') as f:
            json.dump(self.profile.to_dict(), f, indent=2)
    
    def add_xp(self, amount: int, reason: str = "") -> Dict[str, Any]:
        """Add XP and check for level up"""
        old_level = self.profile.level
        self.profile.xp += amount
        
        # Update daily streak
        self.update_streak()
        
        # Check for level up
        new_level = self._calculate_level()
        leveled_up = new_level != old_level
        
        if leveled_up:
            self.profile.level = new_level
        
        self.save_profile()
        
        # Check for achievements (after save to ensure level is updated)
        new_achievements = self.check_achievements()
        
        return {
            'xp_gained': amount,
            'total_xp': self.profile.xp,
            'level': self.profile.level.value,
            'leveled_up': leveled_up,
            'reason': reason,
            'next_level_at': self._next_level_xp(),
            'new_achievements': new_achievements
        }
    
    def _calculate_level(self) -> SkillLevel:
        """Calculate level based on XP"""
        for level in reversed(list(SkillLevel)):
            if self.profile.xp >= self.LEVEL_THRESHOLDS[level]:
                return level
        return SkillLevel.BEGINNER
    
    def _next_level_xp(self) -> Optional[int]:
        """XP needed for next level"""
        levels = list(SkillLevel)
        current_index = levels.index(self.profile.level)
        if current_index < len(levels) - 1:
            return self.LEVEL_THRESHOLDS[levels[current_index + 1]]
        return None
    
    def learn_concept(self, concept: str) -> Dict[str, Any]:
        """Mark a concept as learned"""
        was_new = concept not in self.profile.concepts_learned
        self.profile.concepts_learned.add(concept)
        self.save_profile()
        return {'concept': concept, 'was_new': was_new}
    
    def use_block(self, block_name: str) -> Dict[str, Any]:
        """Record block usage"""
        was_new = block_name not in self.profile.blocks_used
        self.profile.blocks_used.add(block_name)
        self.save_profile()
        return {'block': block_name, 'was_new': was_new}
    
    def complete_project(self) -> Dict[str, Any]:
        """Record project completion"""
        self.profile.projects_completed += 1
        result = self.add_xp(50, "Project completed!")
        return result
    
    def get_available_blocks(self) -> Dict[str, Any]:
        """Get blocks available at current level"""
        available = {}
        locked = {}
        
        current_level_index = list(SkillLevel).index(self.profile.level)
        
        for level in SkillLevel:
            level_index = list(SkillLevel).index(level)
            blocks = LEVEL_BLOCKS.get(level, {})
            
            for block_id, block_info in blocks.items():
                # Check if level is unlocked
                if level_index <= current_level_index:
                    # Check if required concepts are learned
                    required = block_info.get('requires_concepts', [])
                    has_prereqs = all(c in self.profile.concepts_learned for c in required)
                    
                    if has_prereqs:
                        available[block_id] = {
                            **block_info,
                            'level': level.value,
                            'unlocked': True
                        }
                    else:
                        locked[block_id] = {
                            **block_info,
                            'level': level.value,
                            'unlocked': False,
                            'missing_concepts': [c for c in required if c not in self.profile.concepts_learned]
                        }
                else:
                    locked[block_id] = {
                        **block_info,
                        'level': level.value,
                        'unlocked': False,
                        'requires_level': level.value
                    }
        
        return {
            'available': available,
            'locked': locked,
            'current_level': self.profile.level.value,
            'xp': self.profile.xp,
            'next_level_at': self._next_level_xp()
        }
    
    def get_available_projects(self) -> Dict[str, Any]:
        """Get code projects available at current level"""
        available = {}
        locked = {}
        
        current_level_index = list(SkillLevel).index(self.profile.level)
        
        for project_id, project_info in CODE_PATTERNS.items():
            project_level = project_info['level']
            level_index = list(SkillLevel).index(project_level)
            
            if level_index <= current_level_index:
                available[project_id] = {
                    'name': project_info['name'],
                    'description': project_info['description'],
                    'teaches': project_info['teaches'],
                    'xp_reward': project_info['xp_reward'],
                    'level': project_level.value
                }
            else:
                locked[project_id] = {
                    'name': project_info['name'],
                    'description': project_info['description'],
                    'requires_level': project_level.value
                }
        
        return {
            'available': available,
            'locked': locked
        }
    
    def get_project_code(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get code for a project if available"""
        if project_id not in CODE_PATTERNS:
            return None
        
        project = CODE_PATTERNS[project_id]
        current_level_index = list(SkillLevel).index(self.profile.level)
        project_level_index = list(SkillLevel).index(project['level'])
        
        if project_level_index > current_level_index:
            return {
                'available': False,
                'requires_level': project['level'].value
            }
        
        # Mark concepts as learned and add XP
        for concept in project['teaches']:
            self.learn_concept(concept)
        
        xp_result = self.add_xp(project['xp_reward'], f"Completed {project['name']}")
        
        return {
            'available': True,
            'name': project['name'],
            'code': project['code'],
            'teaches': project['teaches'],
            **xp_result
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        return {
            'level': self.profile.level.value,
            'xp': self.profile.xp,
            'next_level_at': self._next_level_xp(),
            'projects_completed': self.profile.projects_completed,
            'blocks_used': list(self.profile.blocks_used),
            'concepts_learned': list(self.profile.concepts_learned),
            'progress_percent': self._calculate_progress_percent()
        }
    
    def _calculate_progress_percent(self) -> int:
        """Calculate progress to next level as percentage"""
        current = self.LEVEL_THRESHOLDS[self.profile.level]
        next_lvl = self._next_level_xp()
        
        if next_lvl is None:
            return 100
        
        progress = self.profile.xp - current
        needed = next_lvl - current
        
        return min(100, int((progress / needed) * 100))
    
    def update_streak(self):
        """Update daily streak tracking"""
        from datetime import datetime, timedelta
        
        today = datetime.now().strftime('%Y-%m-%d')
        last = self.profile.last_activity_date
        
        if last == today:
            # Already active today
            return
        
        if last:
            last_date = datetime.strptime(last, '%Y-%m-%d')
            today_date = datetime.strptime(today, '%Y-%m-%d')
            diff = (today_date - last_date).days
            
            if diff == 1:
                # Consecutive day!
                self.profile.streak_days += 1
            elif diff > 1:
                # Streak broken
                self.profile.streak_days = 1
        else:
            # First activity ever
            self.profile.streak_days = 1
        
        self.profile.last_activity_date = today
        self.save_profile()
    
    def check_achievements(self) -> List[Dict[str, Any]]:
        """Check for newly earned achievements and award XP"""
        newly_earned = []
        
        for ach_id, ach_info in ACHIEVEMENTS.items():
            # Skip if already earned
            if ach_id in self.profile.achievements:
                continue
            
            # Check condition
            try:
                if ach_info['condition'](self.profile):
                    self.profile.achievements.add(ach_id)
                    newly_earned.append({
                        'id': ach_id,
                        'name': ach_info['name'],
                        'description': ach_info['description'],
                        'xp_bonus': ach_info['xp_bonus']
                    })
            except Exception:
                pass  # Skip failed conditions
        
        # Award XP for new achievements (without recursion)
        for ach in newly_earned:
            self.profile.xp += ach['xp_bonus']
        
        if newly_earned:
            self.save_profile()
        
        return newly_earned
    
    def get_achievements(self) -> Dict[str, Any]:
        """Get all achievements with earned status"""
        earned = []
        available = []
        
        for ach_id, ach_info in ACHIEVEMENTS.items():
            ach_data = {
                'id': ach_id,
                'name': ach_info['name'],
                'description': ach_info['description'],
                'xp_bonus': ach_info['xp_bonus']
            }
            
            if ach_id in self.profile.achievements:
                earned.append(ach_data)
            else:
                available.append(ach_data)
        
        return {
            'earned': earned,
            'available': available,
            'total_earned': len(earned),
            'total_available': len(ACHIEVEMENTS),
            'streak_days': self.profile.streak_days
        }


# ============================================================================
# API FUNCTIONS (for builder_server.py integration)
# ============================================================================

_learning_system: Optional[LearningSystem] = None

def get_learning_system() -> LearningSystem:
    """Get or create the learning system singleton"""
    global _learning_system
    if _learning_system is None:
        profile_path = Path(__file__).parent / "workspace" / "learning_profile.json"
        profile_path.parent.mkdir(exist_ok=True)
        _learning_system = LearningSystem(str(profile_path))
    return _learning_system


def get_learning_status() -> Dict[str, Any]:
    """API: Get learning status"""
    return get_learning_system().get_status()


def get_available_blocks() -> Dict[str, Any]:
    """API: Get blocks available at current level"""
    return get_learning_system().get_available_blocks()


def get_available_projects() -> Dict[str, Any]:
    """API: Get projects available at current level"""
    return get_learning_system().get_available_projects()


def get_project_code(project_id: str) -> Optional[Dict[str, Any]]:
    """API: Get code for a project"""
    return get_learning_system().get_project_code(project_id)


def record_block_use(block_name: str) -> Dict[str, Any]:
    """API: Record that a block was used"""
    ls = get_learning_system()
    result = ls.use_block(block_name)
    
    # Check if block grants XP for concepts
    for level_blocks in LEVEL_BLOCKS.values():
        if block_name in level_blocks:
            block_info = level_blocks[block_name]
            for concept in block_info.get('teaches', []):
                ls.learn_concept(concept)
            xp = block_info.get('xp_reward', 10)
            xp_result = ls.add_xp(xp, f"Used {block_name}")
            return {**result, **xp_result}
    
    return result


def complete_project() -> Dict[str, Any]:
    """API: Mark project as complete"""
    return get_learning_system().complete_project()


def get_achievements() -> Dict[str, Any]:
    """API: Get all achievements with status"""
    return get_learning_system().get_achievements()


def get_oracle_advice(profile_tags: List[str]) -> Dict[str, Any]:
    """API: Get pattern advice from the oracle based on problem profile"""
    matches = query_oracle(profile_tags)
    return {
        'query': profile_tags,
        'matches': matches,
        'top_recommendation': matches[0] if matches else None
    }


def get_all_oracle_rules() -> Dict[str, Any]:
    """API: Get all available oracle rules"""
    return {
        'rules': ORACLE_RULES,
        'available_tags': sorted(set(
            tag for rule in ORACLE_RULES.values() for tag in rule['profile']
        ))
    }


# ============================================================================
# CLI DEMO
# ============================================================================

def demo():
    """Demonstrate the learning system"""
    print("=" * 60)
    print("LEARNING INTEGRATION DEMO")
    print("=" * 60)
    
    ls = LearningSystem("demo_profile.json")
    
    # Show initial status
    print("\n📊 Initial Status:")
    status = ls.get_status()
    print(f"  Level: {status['level']}")
    print(f"  XP: {status['xp']} / {status['next_level_at']}")
    
    # Show available blocks
    print("\n🧱 Available Blocks:")
    blocks = ls.get_available_blocks()
    for block_id, info in blocks['available'].items():
        print(f"  ✅ {info['name']} - {info['description']}")
    
    print("\n🔒 Locked Blocks:")
    for block_id, info in list(blocks['locked'].items())[:3]:
        reason = info.get('requires_level', info.get('missing_concepts', 'Unknown'))
        print(f"  🔒 {info['name']} - Requires: {reason}")
    
    # Show available projects
    print("\n📚 Available Projects:")
    projects = ls.get_available_projects()
    for proj_id, info in projects['available'].items():
        print(f"  📖 {info['name']} - {info['xp_reward']} XP")
    
    # Simulate learning
    print("\n🎮 Simulating learning...")
    
    # Get a project
    code_result = ls.get_project_code('guess_number')
    if code_result and code_result['available']:
        print(f"  Got code for: {code_result['name']}")
        print(f"  XP gained: {code_result['xp_gained']}")
        print(f"  Concepts learned: {code_result['teaches']}")
    
    # Use some blocks
    ls.use_block('storage_json')
    ls.use_block('crud_basic')
    
    # Complete a project
    result = ls.complete_project()
    print(f"  Project completed! XP: {result['total_xp']}")
    if result['leveled_up']:
        print(f"  🎉 LEVEL UP! Now: {result['level']}")
    
    # Show final status
    print("\n📊 Final Status:")
    status = ls.get_status()
    print(f"  Level: {status['level']}")
    print(f"  XP: {status['xp']} / {status['next_level_at']}")
    print(f"  Concepts: {status['concepts_learned']}")
    print(f"  Progress: {status['progress_percent']}%")
    
    # Cleanup demo file
    Path("demo_profile.json").unlink(missing_ok=True)
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
