"""
Semantic Cluster Engine

A fast, accurate semantic perception engine using:
1. Pre-defined semantic clusters (thesaurus-style)
2. Fuzzy word matching (stems, prefixes)
3. Simple confidence scoring

This is more reliable than embeddings for a constrained domain
because we control exactly what words map to what concepts.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

# ============================================================================
# SEMANTIC CLUSTERS
# Each cluster represents a concept and the words that express it
# ============================================================================

SEMANTIC_CLUSTERS = {
    'recipe': {
        'words': {'recipe', 'recipes', 'ingredient', 'ingredients', 'meal', 'meals',
                  'dish', 'dishes', 'food', 'foods', 'cook', 'cooking', 'kitchen',
                  'cuisine', 'cuisines', 'pasta', 'sauce', 'spice', 'spices',
                  'breakfast', 'lunch', 'dinner', 'snack', 'bake', 'baking',
                  'fry', 'grill', 'nutrition', 'calorie', 'calories', 'serving',
                  'menu', 'menus', 'dietary', 'vegetarian', 'vegan', 'pantry',
                  'grocery', 'groceries', 'grandma', 'grandmother', 'traditional',
                  'italian', 'mexican', 'asian', 'chinese', 'homemade', 'secret',
                  'family', 'heritage', 'cookbook', 'culinary'},
        'stems': {'recip', 'ingred', 'meal', 'dish', 'cook', 'cuisin', 'past', 
                  'grocer', 'nutri', 'calor'},
        'features': {'database', 'crud', 'search', 'categories'},
    },
    
    'todo': {
        'words': {'todo', 'todos', 'task', 'tasks', 'item', 'items', 'checklist',
                  'checklists', 'reminder', 'reminders', 'deadline', 'deadlines',
                  'due', 'priority', 'priorities', 'project', 'projects', 'goal',
                  'goals', 'milestone', 'milestones', 'progress', 'complete',
                  'completed', 'pending', 'done', 'undone', 'checkbox', 'list',
                  'lists', 'planner', 'action', 'actions'},
        'stems': {'todo', 'task', 'check', 'remind', 'deadlin', 'priorit', 
                  'project', 'goal', 'mileston'},
        'features': {'database', 'crud', 'checkbox', 'categories'},
    },
    
    'expense': {
        'words': {'expense', 'expenses', 'budget', 'budgets', 'money', 'cost',
                  'costs', 'payment', 'payments', 'income', 'salary', 'salaries',
                  'transaction', 'transactions', 'account', 'accounts', 'bank',
                  'banking', 'saving', 'savings', 'spending', 'financial',
                  'finance', 'finances', 'bill', 'bills', 'receipt', 'receipts',
                  'category', 'categories', 'monthly', 'yearly', 'weekly',
                  'debt', 'debts', 'loan', 'loans', 'investment', 'investments',
                  'tax', 'taxes', 'currency'},
        'stems': {'expens', 'budget', 'money', 'cost', 'payment', 'incom', 
                  'salar', 'transact', 'account', 'bank', 'sav', 'spend', 
                  'financ', 'bill', 'receipt'},
        'features': {'database', 'crud', 'charts', 'categories'},
    },
    
    'workout': {
        'words': {'workout', 'workouts', 'exercise', 'exercises', 'gym', 'fitness',
                  'training', 'rep', 'reps', 'set', 'sets', 'weight', 'weights',
                  'cardio', 'muscle', 'muscles', 'routine', 'routines', 'health',
                  'healthy', 'body', 'strength', 'running', 'walking', 'cycling',
                  'swimming', 'yoga', 'stretch', 'stretching', 'warmup', 'cooldown',
                  'athletic', 'athlete', 'sport', 'sports'},
        'stems': {'workout', 'exerc', 'gym', 'fitnes', 'train', 'weight', 
                  'cardio', 'muscl', 'routin', 'health', 'strength'},
        'features': {'database', 'crud', 'history', 'charts'},
    },
    
    'event': {
        'words': {'event', 'events', 'calendar', 'calendars', 'schedule', 'schedules',
                  'appointment', 'appointments', 'date', 'dates', 'time', 'times',
                  'daily', 'weekly', 'monthly', 'yearly', 'recurring', 'meeting',
                  'meetings', 'agenda', 'agendas', 'booking', 'bookings', 'slot',
                  'slots', 'availability', 'available', 'busy', 'free'},
        'stems': {'event', 'calendar', 'schedul', 'appoint', 'meet', 'agenda', 
                  'book'},
        'features': {'database', 'crud', 'calendar'},
    },
    
    'note': {
        'words': {'note', 'notes', 'memo', 'memos', 'journal', 'journals', 'diary',
                  'diaries', 'entry', 'entries', 'write', 'writing', 'text', 'texts',
                  'document', 'documents', 'markdown', 'editor', 'editors',
                  'notebook', 'notebooks', 'draft', 'drafts', 'blog', 'blogs',
                  'post', 'posts', 'article', 'articles', 'thought', 'thoughts'},
        'stems': {'note', 'memo', 'journal', 'diary', 'entry', 'entr', 'write',
                  'writ', 'document', 'doc', 'notebook', 'draft', 'blog', 'articl'},
        'features': {'database', 'crud', 'editor', 'search'},
    },
    
    'bookmark': {
        'words': {'bookmark', 'bookmarks', 'link', 'links', 'url', 'urls', 'website',
                  'websites', 'favorite', 'favorites', 'favourite', 'favourites',
                  'web', 'page', 'pages', 'site', 'sites', 'browser', 'reading',
                  'read', 'later', 'save', 'saved'},
        'stems': {'bookmark', 'link', 'url', 'websit', 'favorit', 'favourit', 
                  'site'},
        'features': {'database', 'crud', 'search', 'categories'},
    },
    
    'contact': {
        'words': {'contact', 'contacts', 'person', 'people', 'persons', 'friend',
                  'friends', 'user', 'users', 'profile', 'profiles', 'address',
                  'addresses', 'phone', 'phones', 'email', 'emails', 'directory',
                  'member', 'members', 'colleague', 'colleagues', 'customer',
                  'customers', 'client', 'clients'},
        'stems': {'contact', 'person', 'peopl', 'friend', 'user', 'profil', 
                  'address', 'phone', 'email', 'member', 'client', 'custom'},
        'features': {'database', 'crud', 'search'},
    },
    
    'photo': {
        'words': {'photo', 'photos', 'photograph', 'photographs', 'image', 'images',
                  'picture', 'pictures', 'pic', 'pics', 'gallery', 'galleries',
                  'album', 'albums', 'camera', 'cameras', 'upload', 'uploads',
                  'snapshot', 'snapshots', 'selfie', 'selfies'},
        'stems': {'photo', 'photograph', 'imag', 'pictur', 'pic', 'galler', 
                  'album', 'camera', 'upload'},
        'features': {'upload', 'gallery', 'storage'},
    },
    
    'movie': {
        'words': {'movie', 'movies', 'film', 'films', 'video', 'videos', 'watch',
                  'watched', 'watching', 'show', 'shows', 'series', 'streaming',
                  'stream', 'netflix', 'cinema', 'theater', 'theatre', 'dvd',
                  'bluray', 'actor', 'actress', 'director', 'imdb', 'rating',
                  'ratings', 'review', 'reviews', 'watchlist'},
        'stems': {'movie', 'film', 'video', 'watch', 'show', 'stream', 'cinem',
                  'theater', 'theatr', 'rating', 'review'},
        'features': {'database', 'crud', 'ratings', 'search'},
    },
    
    'music': {
        'words': {'music', 'song', 'songs', 'playlist', 'playlists', 'audio',
                  'album', 'albums', 'artist', 'artists', 'band', 'bands',
                  'listen', 'listening', 'track', 'tracks', 'spotify', 'mp3',
                  'genre', 'genres', 'concert', 'concerts'},
        'stems': {'music', 'song', 'playlist', 'audio', 'album', 'artist', 
                  'band', 'listen', 'track', 'concert'},
        'features': {'database', 'crud', 'player'},
    },
    
    'flashcard': {
        'words': {'flashcard', 'flashcards', 'card', 'cards', 'study', 'studying',
                  'learn', 'learning', 'quiz', 'quizzes', 'test', 'tests',
                  'practice', 'practicing', 'memorize', 'memorizing', 'memory',
                  'review', 'reviewing', 'education', 'course', 'courses',
                  'lesson', 'lessons', 'exam', 'exams', 'vocabulary', 'vocab',
                  'language', 'languages', 'spaced', 'repetition', 'anki'},
        'stems': {'flashcard', 'card', 'study', 'learn', 'quiz', 'test', 
                  'practic', 'memor', 'review', 'educat', 'course', 'lesson', 
                  'exam', 'vocab', 'languag'},
        'features': {'database', 'crud', 'quiz', 'spaced_repetition'},
    },
    
    'game': {
        'words': {'game', 'games', 'gaming', 'play', 'playing', 'player', 'players',
                  'score', 'scores', 'scoring', 'level', 'levels', 'win', 'winning',
                  'winner', 'lose', 'losing', 'loser', 'turn', 'turns', 'move',
                  'moves', 'round', 'rounds', 'match', 'matches', 'compete',
                  'competition', 'challenge', 'challenges', 'puzzle', 'puzzles',
                  'board', 'dice', 'wordle', 'trivia', 'hangman', 'snake',
                  'tetris', 'tic', 'tac', 'toe', 'chess', 'checkers'},
        'stems': {'game', 'gam', 'play', 'player', 'scor', 'level', 'win', 
                  'match', 'compet', 'challeng', 'puzzl'},
        'features': {'state', 'interactive', 'score'},
    },
    
    'inventory': {
        'words': {'inventory', 'inventories', 'stock', 'stocks', 'warehouse',
                  'supply', 'supplies', 'quantity', 'quantities', 'sku',
                  'barcode', 'barcodes', 'product', 'products', 'asset', 'assets'},
        'stems': {'inventor', 'stock', 'warehous', 'suppl', 'quantit', 
                  'product', 'asset'},
        'features': {'database', 'crud', 'tracking'},
    },
    
    'habit': {
        'words': {'habit', 'habits', 'streak', 'streaks', 'daily', 'routine',
                  'routines', 'tracker', 'tracking', 'track', 'consistency',
                  'consistent', 'goal', 'goals', 'progress', 'chain', 'chains'},
        'stems': {'habit', 'streak', 'routin', 'track', 'consist', 'goal', 
                  'progress'},
        'features': {'database', 'crud', 'charts', 'streak'},
    },
    
    # ========== NEW CLUSTERS FOR NOVEL DOMAINS ==========
    
    'investment': {
        'words': {'investment', 'investments', 'investing', 'investor', 'investors',
                  'portfolio', 'portfolios', 'stock', 'stocks', 'share', 'shares',
                  'crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'token', 'tokens',
                  'trading', 'trade', 'trades', 'trader', 'market', 'markets',
                  'equity', 'equities', 'bond', 'bonds', 'dividend', 'dividends',
                  'roi', 'return', 'returns', 'asset', 'assets', 'wealth', 'fund',
                  'funds', 'etf', 'etfs', 'forex', 'nft', 'nfts', 'defi', 'yield',
                  'wallet', 'wallets', 'blockchain', 'exchange', 'exchanges',
                  'hodl', 'bull', 'bear', 'profit', 'profits', 'loss', 'losses'},
        'stems': {'invest', 'portfolio', 'stock', 'crypto', 'trad', 'market',
                  'equit', 'bond', 'divid', 'asset', 'wealth', 'fund', 'wallet',
                  'blockchain', 'exchange', 'profit'},
        'features': {'database', 'crud', 'charts', 'realtime', 'tracking'},
    },
    
    'science': {
        'words': {'science', 'scientific', 'research', 'researcher', 'experiment',
                  'experiments', 'simulation', 'simulations', 'simulate', 'model',
                  'models', 'modeling', 'analysis', 'analyze', 'data', 'dataset',
                  'datasets', 'hypothesis', 'theory', 'theories', 'physics',
                  'chemistry', 'biology', 'math', 'mathematics', 'quantum',
                  'particle', 'particles', 'molecule', 'molecules', 'atom', 'atoms',
                  'equation', 'equations', 'formula', 'formulas', 'calculation',
                  'calculations', 'calculate', 'lab', 'laboratory', 'visualization',
                  'graph', 'graphs', 'plot', 'plots', 'statistic', 'statistics',
                  'neural', 'network', 'algorithm', 'algorithms', 'ai', 'ml',
                  'machine', 'learning', 'deep', 'tensor'},
        'stems': {'scienc', 'research', 'experiment', 'simulat', 'model', 
                  'analys', 'analyz', 'dataset', 'hypothes', 'theor', 'physic',
                  'chemist', 'biolog', 'quantum', 'molecul', 'atom', 'equat',
                  'formula', 'calcul', 'laborator', 'visual', 'graph', 'plot',
                  'statist', 'algorithm', 'neural'},
        'features': {'canvas', 'charts', 'forms', 'export'},
    },
    
    'medical': {
        'words': {'medical', 'medicine', 'health', 'healthcare', 'patient', 'patients',
                  'doctor', 'doctors', 'nurse', 'nurses', 'hospital', 'clinic',
                  'clinics', 'symptom', 'symptoms', 'diagnosis', 'diagnose',
                  'treatment', 'treatments', 'medication', 'medications', 'drug',
                  'drugs', 'prescription', 'prescriptions', 'appointment', 'checkup',
                  'dna', 'gene', 'genes', 'genetic', 'genetics', 'genome', 'sequence',
                  'sequences', 'sequencing', 'protein', 'proteins', 'cell', 'cells',
                  'blood', 'pressure', 'heart', 'pulse', 'vital', 'vitals',
                  'allergy', 'allergies', 'condition', 'conditions', 'chronic',
                  'therapy', 'therapies', 'vaccine', 'vaccines', 'immunity'},
        'stems': {'medic', 'health', 'patient', 'doctor', 'nurs', 'hospit',
                  'clinic', 'symptom', 'diagnos', 'treatment', 'medicat', 'drug',
                  'prescript', 'dna', 'gene', 'genet', 'genom', 'sequenc', 
                  'protein', 'cell', 'blood', 'vital', 'allerg', 'therap', 'vaccin'},
        'features': {'database', 'crud', 'charts', 'history', 'tracking'},
    },
    
    'developer': {
        'words': {'code', 'codes', 'coding', 'coder', 'coders', 'programming',
                  'program', 'programs', 'programmer', 'developer', 'developers',
                  'development', 'software', 'app', 'apps', 'application',
                  'api', 'apis', 'function', 'functions', 'class', 'classes',
                  'variable', 'variables', 'debug', 'debugging', 'bug', 'bugs',
                  'git', 'github', 'repository', 'repo', 'repos', 'commit',
                  'commits', 'branch', 'branches', 'merge', 'pull', 'push',
                  'snippet', 'snippets', 'regex', 'json', 'yaml', 'sql', 'html',
                  'css', 'javascript', 'python', 'java', 'typescript', 'rust',
                  'ide', 'editor', 'terminal', 'console', 'command', 'script',
                  'scripts', 'deploy', 'deployment', 'server', 'database', 'schema'},
        'stems': {'code', 'cod', 'program', 'develop', 'softwar', 'applicat',
                  'function', 'class', 'variabl', 'debug', 'bug', 'repositor',
                  'repo', 'commit', 'branch', 'merg', 'snippet', 'script',
                  'deploy', 'server', 'databas', 'schem'},
        'features': {'editor', 'crud', 'search', 'export'},
    },
    
    'analytics': {
        'words': {'analytics', 'analytic', 'metric', 'metrics', 'dashboard',
                  'dashboards', 'report', 'reports', 'reporting', 'kpi', 'kpis',
                  'insight', 'insights', 'trend', 'trends', 'chart', 'charts',
                  'graph', 'graphs', 'visualization', 'visualizations', 'data',
                  'dataset', 'datasets', 'aggregate', 'aggregation', 'sum',
                  'average', 'mean', 'median', 'count', 'percentage', 'ratio',
                  'comparison', 'compare', 'benchmark', 'benchmarks', 'performance',
                  'growth', 'decline', 'forecast', 'forecasting', 'prediction',
                  'predictions', 'predict', 'monitor', 'monitoring', 'tracker'},
        'stems': {'analytic', 'metric', 'dashboard', 'report', 'kpi', 'insight',
                  'trend', 'chart', 'graph', 'visual', 'dataset', 'aggregat',
                  'benchmark', 'perform', 'growth', 'forecast', 'predict', 'monitor'},
        'features': {'charts', 'database', 'export', 'realtime'},
    },
    
    'social': {
        'words': {'social', 'community', 'communities', 'user', 'users', 'profile',
                  'profiles', 'follow', 'following', 'follower', 'followers',
                  'friend', 'friends', 'connection', 'connections', 'network',
                  'networking', 'post', 'posts', 'feed', 'feeds', 'comment',
                  'comments', 'like', 'likes', 'share', 'shares', 'message',
                  'messages', 'messaging', 'chat', 'chats', 'chatting', 'group',
                  'groups', 'forum', 'forums', 'discussion', 'discussions',
                  'thread', 'threads', 'mention', 'mentions', 'notification',
                  'notifications', 'timeline', 'wall'},
        'stems': {'social', 'communit', 'user', 'profil', 'follow', 'friend',
                  'connect', 'network', 'post', 'feed', 'comment', 'like',
                  'share', 'messag', 'chat', 'group', 'forum', 'discuss',
                  'thread', 'mention', 'notific', 'timelin'},
        'features': {'auth', 'database', 'crud', 'realtime', 'notifications'},
    },
    
    'ecommerce': {
        'words': {'ecommerce', 'commerce', 'shop', 'shopping', 'store', 'stores',
                  'product', 'products', 'cart', 'carts', 'checkout', 'order',
                  'orders', 'ordering', 'purchase', 'purchases', 'buy', 'buying',
                  'sell', 'selling', 'seller', 'sellers', 'buyer', 'buyers',
                  'price', 'prices', 'pricing', 'discount', 'discounts', 'coupon',
                  'coupons', 'shipping', 'delivery', 'payment', 'payments',
                  'invoice', 'invoices', 'catalog', 'catalogs', 'inventory',
                  'sku', 'variant', 'variants', 'customer', 'customers'},
        'stems': {'ecommerc', 'commerc', 'shop', 'store', 'product', 'cart',
                  'checkout', 'order', 'purchas', 'buy', 'sell', 'price',
                  'discount', 'coupon', 'ship', 'deliver', 'payment', 'invoic',
                  'catalog', 'inventor', 'custom'},
        'features': {'database', 'crud', 'cart', 'checkout', 'payment'},
    },
    
    'travel': {
        'words': {'travel', 'traveling', 'travelling', 'trip', 'trips', 'journey',
                  'journeys', 'vacation', 'vacations', 'holiday', 'holidays',
                  'destination', 'destinations', 'flight', 'flights', 'hotel',
                  'hotels', 'booking', 'bookings', 'reservation', 'reservations',
                  'itinerary', 'itineraries', 'passport', 'visa', 'airport',
                  'airline', 'airlines', 'luggage', 'baggage', 'tour', 'tours',
                  'guide', 'guides', 'attraction', 'attractions', 'sightseeing',
                  'backpack', 'backpacking', 'explore', 'exploring', 'adventure'},
        'stems': {'travel', 'trip', 'journey', 'vacat', 'holiday', 'destin',
                  'flight', 'hotel', 'book', 'reserv', 'itiner', 'passport',
                  'airport', 'airlin', 'tour', 'guid', 'attract', 'explor',
                  'adventur'},
        'features': {'database', 'crud', 'calendar', 'maps', 'search'},
    },
}

# Build reverse index: word -> clusters
WORD_TO_CLUSTERS: Dict[str, Set[str]] = defaultdict(set)
STEM_TO_CLUSTERS: Dict[str, Set[str]] = defaultdict(set)

for cluster_name, info in SEMANTIC_CLUSTERS.items():
    for word in info['words']:
        WORD_TO_CLUSTERS[word].add(cluster_name)
    for stem in info.get('stems', set()):
        STEM_TO_CLUSTERS[stem].add(cluster_name)


# ============================================================================
# SEMANTIC CLUSTER ENGINE
# ============================================================================

@dataclass
class ClusterPercept:
    """Result of cluster-based perception."""
    raw_input: str
    tokens: List[str]
    entities: Dict[str, float]  # cluster -> confidence
    intent: str
    features: Set[str]
    matched_words: Dict[str, List[str]]  # cluster -> matching input words


class SemanticClusterEngine:
    """
    Semantic perception using cluster lookup.
    
    Much simpler and more reliable than embedding math for constrained domains.
    """
    
    INTENT_PATTERNS = {
        'query': ['search', 'find', 'look', 'query', 'get', 'filter', 'where'],
        'create': ['create', 'new', 'build', 'make', 'start', 'app'],
        'delete': ['delete', 'remove', 'clear', 'erase'],
        'update': ['update', 'edit', 'change', 'modify'],
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize input."""
        text = re.sub(r"[^\w\s']", ' ', text.lower())
        text = re.sub(r"'s\b", '', text)
        tokens = text.split()
        stopwords = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'and', 'or', 'but', 'if', 'i', 'me', 'my',
                     'we', 'our', 'you', 'your', 'he', 'she', 'it', 'its',
                     'they', 'them', 'their', 'this', 'that', 'these', 'those',
                     'want', 'need', 'something', 'way', 'help', 'can'}
        return [t for t in tokens if len(t) > 1 and t not in stopwords]
    
    def perceive(self, text: str) -> ClusterPercept:
        """Detect clusters present in the input."""
        tokens = self.tokenize(text)
        
        if not tokens:
            return ClusterPercept(
                raw_input=text, tokens=[], entities={}, intent='unknown',
                features=set(), matched_words={}
            )
        
        # Track matches per cluster
        cluster_matches: Dict[str, List[str]] = defaultdict(list)
        
        for token in tokens:
            # Direct word match
            if token in WORD_TO_CLUSTERS:
                for cluster in WORD_TO_CLUSTERS[token]:
                    cluster_matches[cluster].append(token)
            else:
                # Stem match
                for stem, clusters in STEM_TO_CLUSTERS.items():
                    if token.startswith(stem) or stem.startswith(token[:4] if len(token) >= 4 else token):
                        for cluster in clusters:
                            cluster_matches[cluster].append(token)
        
        # Compute confidence based on number and uniqueness of matches
        entities = {}
        for cluster, matched in cluster_matches.items():
            # Unique matches count more
            unique_matches = len(set(matched))
            total_matches = len(matched)
            
            # Confidence: more unique matches = higher confidence
            # 1 match = 0.6, 2 matches = 0.8, 3+ = 0.95
            if unique_matches >= 3:
                confidence = 0.95
            elif unique_matches == 2:
                confidence = 0.80
            elif unique_matches == 1:
                confidence = 0.60
            else:
                confidence = 0.0
            
            if confidence > 0:
                entities[cluster] = confidence
        
        # Only keep top clusters (if many matched, keep those with most matches)
        if len(entities) > 3:
            sorted_entities = sorted(entities.items(), key=lambda x: -x[1])
            entities = dict(sorted_entities[:3])
        
        # Detect intent
        intent = self._detect_intent(tokens, entities)
        
        # Collect features
        features = set()
        for cluster in entities:
            if cluster in SEMANTIC_CLUSTERS:
                features.update(SEMANTIC_CLUSTERS[cluster]['features'])
        
        return ClusterPercept(
            raw_input=text,
            tokens=tokens,
            entities=entities,
            intent=intent,
            features=features,
            matched_words=dict(cluster_matches)
        )
    
    def _detect_intent(self, tokens: List[str], entities: Dict[str, float]) -> str:
        """Detect intent."""
        for intent, keywords in self.INTENT_PATTERNS.items():
            for token in tokens:
                if token in keywords:
                    return intent
        
        if entities:
            return 'create_app'
        return 'unknown'


# ============================================================================
# APP FORGE BRIDGE
# ============================================================================

def perceive_for_app_forge(description: str) -> Dict[str, Any]:
    """Bridge function for App Forge integration."""
    engine = SemanticClusterEngine()
    percept = engine.perceive(description)
    
    return {
        'entities': percept.entities,
        'features': list(percept.features),
        'intent': percept.intent,
        'confidence': max(percept.entities.values()) if percept.entities else 0.0,
        'tokens': percept.tokens,
        'matched_words': percept.matched_words
    }


# ============================================================================
# TESTING
# ============================================================================

def benchmark():
    """Run benchmark."""
    engine = SemanticClusterEngine()
    
    test_cases = [
        ("recipe app with ingredients", {'recipe'}, "Standard recipe"),
        ("todo list with categories", {'todo'}, "Standard todo"),
        ("expense tracker with budget", {'expense'}, "Standard expense"),
        ("grandma's secret pasta dishes", {'recipe'}, "Novel: grandma's recipes"),
        ("organize workout routines", {'workout'}, "Novel: workout"),
        ("remember movies watched", {'movie'}, "Novel: movies"),
        ("study with flashcards", {'flashcard'}, "Novel: flashcards"),
        ("meal planning budget", {'recipe', 'expense'}, "Mixed: meal + budget"),
        ("fitness journal photos", {'workout', 'photo'}, "Mixed: fitness + photo"),
        ("track daily habits", {'habit'}, "Habit tracking"),
        ("something to catalog grandmother's traditional Italian cuisine", {'recipe'}, "Complex novel"),
    ]
    
    print("="*60)
    print("SEMANTIC CLUSTER ENGINE BENCHMARK")
    print("="*60)
    
    passed = 0
    for text, expected, desc in test_cases:
        result = engine.perceive(text)
        detected = set(result.entities.keys())
        
        hit = bool(expected & detected)
        passed += hit
        
        status = "✓" if hit else "✗"
        print(f"\n[{status}] {desc}")
        print(f"    Input: {text}")
        print(f"    Expected: {expected}")
        print(f"    Detected: {detected}")
        if result.matched_words:
            print(f"    Matches: {dict(result.matched_words)}")
    
    accuracy = passed / len(test_cases) * 100
    print(f"\n{'='*60}")
    print(f"Accuracy: {passed}/{len(test_cases)} ({accuracy:.0f}%)")
    return accuracy


if __name__ == "__main__":
    benchmark()
