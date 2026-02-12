"""
Kernel Composer - Compositional Algorithm Generator

Composes algorithms from primitives + operations + control patterns.
Enables novel algorithm generation without templates.

Architecture:
  Primitive (Grid2D, Graph, Tree, Stream, Set, Sequence, StateMachine)
  + Operation (map, filter, reduce, neighbors, search, sort)
  + Control (iterate, recurse, backtrack, evolve)
  + Termination (steps, convergence, found, manual)
  = Working Algorithm Code
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum


# =============================================================================
# Computational Primitives
# =============================================================================

class Primitive(Enum):
    GRID2D = "grid2d"           # Cells with neighbors (Game of Life, maze, image)
    GRAPH = "graph"             # Nodes with edges (social network, pathfinding)
    TREE = "tree"               # Hierarchical (file system, decision tree)
    STREAM = "stream"           # Infinite sequence (Fibonacci, data pipeline)
    SET = "set"                 # Unordered collection (deduplication, membership)
    SEQUENCE = "sequence"       # Ordered elements (sorting, searching)
    STATE_MACHINE = "state_machine"  # States + transitions (parsers, game states)
    PARTICLES = "particles"     # Moving entities (physics sim, flocking)


class Operation(Enum):
    MAP = "map"                 # Transform each element
    FILTER = "filter"           # Keep matching elements
    REDUCE = "reduce"           # Accumulate to single value
    NEIGHBORS = "neighbors"     # Get adjacent elements
    SEARCH = "search"           # Find first match
    SORT = "sort"               # Order elements
    COUNT = "count"             # Count matching
    EXPAND = "expand"           # Generate from element
    MERGE = "merge"             # Combine multiple


class Control(Enum):
    ITERATE = "iterate"         # while(cond) { step() }
    RECURSE = "recurse"         # f(x) = base OR f(smaller(x))
    BACKTRACK = "backtrack"     # try { choice } or { undo; next }
    EVOLVE = "evolve"           # mutate → evaluate → select → repeat
    STREAM_PROCESS = "stream"   # continuous input processing


class Termination(Enum):
    STEPS = "steps"             # Fixed number of iterations
    CONVERGENCE = "convergence" # Until state stops changing
    FOUND = "found"             # Until target found
    MANUAL = "manual"           # User controls
    THRESHOLD = "threshold"     # Until value exceeds threshold


# =============================================================================
# Keyword to Primitive Mappings
# =============================================================================

PRIMITIVE_SIGNALS = {
    Primitive.GRID2D: [
        r'\bcell(s|ular)?\b', r'\bgrid\b', r'\blife\b', r'\bconway\b',
        r'\bmaze\b', r'\btile[sd]?\b', r'\bpixel\b', r'\bimage\b',
        r'\bspread\b', r'\binfect\b', r'\bvirus\b', r'\bfire\b',
        r'\bautomata?\b', r'\bneighbor\b', r'\b2d\s*(array|matrix)\b',
    ],
    Primitive.GRAPH: [
        r'\bgraph\s*(visual|algorithm|travers)', r'\bnode\s*(visual|algorithm)',
        r'\bedge\s*(visual|algorithm)', r'\bnetwork\s*(visual|algorithm)',
        r'\bpath\s*find', r'\bshort(est)?\s*path\b', r'\broute\s*(find|visual)',
        r'\bconnect(ed|ion)?\s*(visual|algorithm)', r'\btravers(e|al)\b', 
        r'\bbfs\b', r'\bdfs\b', r'\bdijkstra\b', r'\ba\*\b',
        r'\bgraph\s*theory\b',
    ],
    Primitive.TREE: [
        r'\btree\b', r'\bhierarchi(y|cal)\b', r'\bparent\b', r'\bchild\b',
        r'\bfolder\b', r'\bdirectory\b', r'\borg(anization)?\s*chart\b',
        r'\bdecision\s*tree\b', r'\bbinary\s*tree\b', r'\bast\b',
        r'\brecursive\s*structure\b',
    ],
    Primitive.STREAM: [
        r'\bstream\b', r'\bpipeline\b', r'\bfibonacci\b', r'\bsequence\b',
        r'\binfinite\b', r'\bgenerat(e|or)\b', r'\breal[- ]?time\b',
        r'\bevent[- ]?stream\b', r'\bdata\s*flow\b',
    ],
    Primitive.SET: [
        r'\bset\b', r'\bunique\b', r'\bdedupe\b', r'\bdeduplicat\b',
        r'\bmembership\b', r'\bunion\b', r'\bintersect\b',
    ],
    Primitive.SEQUENCE: [
        r'\bsort(ing|ed)?\s*(algorithm|visual)', r'\bsearch(ing)?\s*(algorithm|visual)', 
        r'\barray\s*(visual|algorithm)', r'\balgorithm\s*(visual|display)',
        r'\border(ed|ing)?\s*(visual|algorithm)', r'\brank(ing|ed)?\s*visual',
        r'\bvisualiz(e|er|ation)\s*(sort|search|algorithm)',
        r'\bquicksort\b', r'\bmergesort\b', r'\bbubblesort\b', r'\bheapsort\b',
        r'\bbinary\s*search\b',
    ],
    Primitive.STATE_MACHINE: [
        r'\bstate\s*machine\b', r'\bfsm\b', r'\bautomaton\b',
        r'\bstate[sd]?\b.*\btransition\b', r'\bpars(e|er|ing)\b',
        r'\bworkflow\b', r'\bstatus\b.*\bchange\b',
    ],
    Primitive.PARTICLES: [
        r'\bparticle[sd]?\b', r'\bphysic[s]?\b', r'\bsimulat(e|ion)\b',
        r'\bflocking\b', r'\bboid[s]?\b', r'\bgravity\b', r'\bcollision\b',
        r'\bmovement\b', r'\bvelocity\b', r'\bswarm\b',
    ],
}

OPERATION_SIGNALS = {
    Operation.NEIGHBORS: [r'\bneighbor\b', r'\badjacent\b', r'\bsurround\b'],
    Operation.COUNT: [r'\bcount\b', r'\bhow\s*many\b', r'\bnumber\s*of\b'],
    Operation.SEARCH: [r'\bfind\b', r'\bsearch\b', r'\blocate\b', r'\bpath\b'],
    Operation.SORT: [r'\bsort\b', r'\border\b', r'\brank\b'],
    Operation.FILTER: [r'\bfilter\b', r'\bkeep\b', r'\bremove\b', r'\bexclude\b'],
    Operation.MAP: [r'\btransform\b', r'\bconvert\b', r'\bapply\b'],
    Operation.REDUCE: [r'\bsum\b', r'\btotal\b', r'\baccumulat\b', r'\baggregate\b'],
}

CONTROL_SIGNALS = {
    Control.ITERATE: [r'\bloop\b', r'\brepeat\b', r'\bgeneration\b', r'\bstep\b', r'\btick\b'],
    Control.RECURSE: [r'\brecurs\b', r'\bdivide\b', r'\bconquer\b'],
    Control.BACKTRACK: [r'\bbacktrack\b', r'\bundo\b', r'\bpuzzle\b', r'\bsolve\b', r'\bsudoku\b'],
    Control.EVOLVE: [r'\bevolve\b', r'\bgenetic\b', r'\bmutate\b', r'\bfitness\b', r'\boptimiz\b'],
}

TERMINATION_SIGNALS = {
    Termination.STEPS: [r'\bstep[sd]?\b', r'\bgeneration\b', r'\btick\b', r'\bframe\b'],
    Termination.CONVERGENCE: [r'\bstable\b', r'\bconverg\b', r'\bequilibrium\b', r'\bsettle\b'],
    Termination.FOUND: [r'\bfind\b', r'\bfound\b', r'\bgoal\b', r'\btarget\b', r'\bdestination\b'],
    Termination.MANUAL: [r'\bclick\b', r'\bbutton\b', r'\buser\b', r'\binteractive\b'],
}


# =============================================================================
# Kernel Specification
# =============================================================================

@dataclass
class KernelSpec:
    """Specification for a composable algorithm kernel."""
    primitive: Primitive
    operations: List[Operation] = field(default_factory=list)
    control: Control = Control.ITERATE
    termination: Termination = Termination.MANUAL
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'primitive': self.primitive.value,
            'operations': [o.value for o in self.operations],
            'control': self.control.value,
            'termination': self.termination.value,
            'params': self.params,
        }


# =============================================================================
# Known Algorithm Patterns
# =============================================================================

ALGORITHM_PATTERNS = {
    # Cellular Automata
    'game_of_life': KernelSpec(
        primitive=Primitive.GRID2D,
        operations=[Operation.NEIGHBORS, Operation.COUNT, Operation.MAP],
        control=Control.ITERATE,
        termination=Termination.MANUAL,
        params={'survive': [2, 3], 'birth': [3], 'wrap': True}
    ),
    'virus_spread': KernelSpec(
        primitive=Primitive.GRID2D,
        operations=[Operation.NEIGHBORS, Operation.FILTER, Operation.MAP],
        control=Control.ITERATE,
        termination=Termination.CONVERGENCE,
        params={'spread_probability': 0.3, 'recovery_time': 10}
    ),
    'forest_fire': KernelSpec(
        primitive=Primitive.GRID2D,
        operations=[Operation.NEIGHBORS, Operation.MAP],
        control=Control.ITERATE,
        termination=Termination.CONVERGENCE,
        params={'ignite_prob': 0.001, 'grow_prob': 0.01}
    ),
    
    # Graph Algorithms
    'pathfinding': KernelSpec(
        primitive=Primitive.GRAPH,
        operations=[Operation.NEIGHBORS, Operation.SEARCH],
        control=Control.ITERATE,
        termination=Termination.FOUND,
        params={'algorithm': 'astar', 'heuristic': 'manhattan'}
    ),
    'maze_solver': KernelSpec(
        primitive=Primitive.GRAPH,
        operations=[Operation.NEIGHBORS, Operation.SEARCH],
        control=Control.BACKTRACK,
        termination=Termination.FOUND,
        params={'algorithm': 'dfs'}
    ),
    
    # Sorting/Searching
    'visualize_sort': KernelSpec(
        primitive=Primitive.SEQUENCE,
        operations=[Operation.SORT],
        control=Control.ITERATE,
        termination=Termination.CONVERGENCE,
        params={'algorithm': 'quicksort', 'visualize': True}
    ),
    
    # Particle Systems
    'particle_sim': KernelSpec(
        primitive=Primitive.PARTICLES,
        operations=[Operation.MAP, Operation.FILTER],
        control=Control.ITERATE,
        termination=Termination.MANUAL,
        params={'forces': ['gravity'], 'bounds': 'bounce'}
    ),
    'flocking': KernelSpec(
        primitive=Primitive.PARTICLES,
        operations=[Operation.NEIGHBORS, Operation.REDUCE, Operation.MAP],
        control=Control.ITERATE,
        termination=Termination.MANUAL,
        params={'separation': 1.5, 'alignment': 1.0, 'cohesion': 1.0}
    ),
    
    # Evolution
    'genetic_algorithm': KernelSpec(
        primitive=Primitive.SEQUENCE,
        operations=[Operation.MAP, Operation.SORT, Operation.FILTER],
        control=Control.EVOLVE,
        termination=Termination.THRESHOLD,
        params={'population': 100, 'mutation_rate': 0.1}
    ),
}


# =============================================================================
# Detection Functions
# =============================================================================

def _detect(text: str, signals: Dict) -> List[Tuple[Any, int]]:
    """Detect patterns and return matches with confidence scores."""
    text = text.lower()
    results = []
    for key, patterns in signals.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text):
                score += 1
        if score > 0:
            results.append((key, score))
    return sorted(results, key=lambda x: -x[1])


def detect_primitive(description: str) -> Optional[Primitive]:
    """Detect the most likely computational primitive."""
    matches = _detect(description, PRIMITIVE_SIGNALS)
    return matches[0][0] if matches else None


def detect_operations(description: str) -> List[Operation]:
    """Detect relevant operations."""
    matches = _detect(description, OPERATION_SIGNALS)
    return [m[0] for m in matches]


def detect_control(description: str) -> Control:
    """Detect control flow pattern."""
    matches = _detect(description, CONTROL_SIGNALS)
    return matches[0][0] if matches else Control.ITERATE


def detect_termination(description: str) -> Termination:
    """Detect termination condition."""
    matches = _detect(description, TERMINATION_SIGNALS)
    return matches[0][0] if matches else Termination.MANUAL


def detect_known_algorithm(description: str) -> Optional[str]:
    """Check if description matches a known algorithm pattern."""
    text = description.lower()
    
    pattern_keywords = {
        'game_of_life': [r'\blife\b', r'\bconway\b', r'\bcellular\s*auto'],
        'virus_spread': [r'\bvirus\b', r'\bspread\b', r'\binfect', r'\bepidemic'],
        'forest_fire': [r'\bforest\s*fire\b', r'\bfire\s*spread'],
        'pathfinding': [r'\bpath\s*find', r'\bshortest\s*path', r'\ba\*\b', r'\bdijkstra'],
        'maze_solver': [r'\bmaze\b.*\bsolv', r'\bsolv.*\bmaze'],
        'visualize_sort': [r'\bsort.*\bvisual', r'\bvisual.*\bsort'],
        'particle_sim': [r'\bparticle\b', r'\bphysics\s*sim'],
        'flocking': [r'\bflock', r'\bboid', r'\bswarm\b'],
        'genetic_algorithm': [r'\bgenetic\b', r'\bevolut', r'\bevol.*\balgorithm'],
    }
    
    for name, keywords in pattern_keywords.items():
        for kw in keywords:
            if re.search(kw, text):
                return name
    return None


# =============================================================================
# Kernel Composer
# =============================================================================

class KernelComposer:
    """
    Composes algorithm kernels from descriptions.
    
    Usage:
        composer = KernelComposer()
        spec = composer.compose("Conway's Game of Life")
        code = composer.generate(spec)
    """
    
    def compose(self, description: str) -> Optional[KernelSpec]:
        """
        Compose a kernel specification from a description.
        Returns None if no suitable primitive detected.
        """
        # Check for known algorithm
        known = detect_known_algorithm(description)
        if known and known in ALGORITHM_PATTERNS:
            return ALGORITHM_PATTERNS[known]
        
        # Detect components
        primitive = detect_primitive(description)
        if not primitive:
            return None
            
        operations = detect_operations(description)
        control = detect_control(description)
        termination = detect_termination(description)
        
        # Apply defaults based on primitive
        if not operations:
            operations = self._default_operations(primitive)
        
        return KernelSpec(
            primitive=primitive,
            operations=operations,
            control=control,
            termination=termination,
            params=self._infer_params(description, primitive)
        )
    
    def _default_operations(self, primitive: Primitive) -> List[Operation]:
        """Get default operations for a primitive."""
        defaults = {
            Primitive.GRID2D: [Operation.NEIGHBORS, Operation.MAP],
            Primitive.GRAPH: [Operation.NEIGHBORS, Operation.SEARCH],
            Primitive.TREE: [Operation.EXPAND],
            Primitive.STREAM: [Operation.MAP, Operation.FILTER],
            Primitive.SET: [Operation.FILTER],
            Primitive.SEQUENCE: [Operation.MAP],
            Primitive.STATE_MACHINE: [Operation.MAP],
            Primitive.PARTICLES: [Operation.MAP],
        }
        return defaults.get(primitive, [Operation.MAP])
    
    def _infer_params(self, description: str, primitive: Primitive) -> Dict:
        """Infer parameters from description."""
        params = {}
        text = description.lower()
        
        # Grid size
        size_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', text)
        if size_match:
            params['width'] = int(size_match.group(1))
            params['height'] = int(size_match.group(2))
        elif primitive == Primitive.GRID2D:
            params['width'] = 50
            params['height'] = 50
        
        # Speed/rate
        if 'fast' in text:
            params['speed'] = 2.0
        elif 'slow' in text:
            params['speed'] = 0.5
        
        return params
    
    def can_compose(self, description: str) -> bool:
        """Check if we can compose a kernel for this description."""
        # First check: must detect a primitive
        if detect_primitive(description) is None:
            return False
        
        # Negative filter: common data/CRUD apps should NOT use kernel composer
        text = description.lower()
        data_app_patterns = [
            r'\btodo\b', r'\btask\b', r'\brecipe\b', r'\bnote\b', r'\bblog\b',
            r'\bcontact\b', r'\buser\b', r'\bcrud\b', r'\bmanager\b', r'\btracker\b',
            r'\binventory\b', r'\bcollection\b', r'\bapp\b(?!.*visual)',
            r'\bapi\b', r'\brest\b', r'\bservice\b', r'\bdashboard\b',
            r'\bform\b', r'\bsurvey\b', r'\bpoll\b', r'\bquiz\s+app\b',
        ]
        for pattern in data_app_patterns:
            if re.search(pattern, text):
                # But allow if it also has strong algorithm signals
                known = detect_known_algorithm(description)
                if not known:
                    return False
        
        return True
    
    def generate(self, spec: KernelSpec) -> str:
        """Generate HTML/JS code for a kernel specification."""
        generators = {
            Primitive.GRID2D: self._generate_grid2d,
            Primitive.GRAPH: self._generate_graph,
            Primitive.PARTICLES: self._generate_particles,
            Primitive.SEQUENCE: self._generate_sequence,
        }
        
        generator = generators.get(spec.primitive)
        if generator:
            return generator(spec)
        
        # Fallback: return a stub
        return self._generate_stub(spec)
    
    def _generate_grid2d(self, spec: KernelSpec) -> str:
        """Generate Grid2D cellular automaton code."""
        width = spec.params.get('width', 50)
        height = spec.params.get('height', 50)
        survive = spec.params.get('survive', [2, 3])
        birth = spec.params.get('birth', [3])
        
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Grid2D Simulation</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            display: flex; flex-direction: column; align-items: center; 
            justify-content: center; min-height: 100vh; 
            background: #1a1a2e; font-family: system-ui; color: white;
        }}
        canvas {{ border: 2px solid #4a4a6a; cursor: crosshair; }}
        .controls {{ margin: 20px; display: flex; gap: 10px; }}
        button {{ 
            padding: 10px 20px; font-size: 16px; cursor: pointer;
            background: #4a4a6a; color: white; border: none; border-radius: 4px;
        }}
        button:hover {{ background: #6a6a8a; }}
        .info {{ color: #888; margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>Grid2D Cellular Automaton</h1>
    <div class="controls">
        <button id="startStop">Start</button>
        <button id="step">Step</button>
        <button id="clear">Clear</button>
        <button id="random">Random</button>
    </div>
    <canvas id="canvas"></canvas>
    <div class="info">Click to toggle cells. Survive: {survive}, Birth: {birth}</div>
    
    <script>
        const WIDTH = {width};
        const HEIGHT = {height};
        const CELL_SIZE = Math.min(12, Math.floor(800 / Math.max(WIDTH, HEIGHT)));
        const SURVIVE = {survive};
        const BIRTH = {birth};
        
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = WIDTH * CELL_SIZE;
        canvas.height = HEIGHT * CELL_SIZE;
        
        let grid = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0));
        let running = false;
        let intervalId = null;
        
        function countNeighbors(x, y) {{
            let count = 0;
            for (let dy = -1; dy <= 1; dy++) {{
                for (let dx = -1; dx <= 1; dx++) {{
                    if (dx === 0 && dy === 0) continue;
                    const nx = (x + dx + WIDTH) % WIDTH;
                    const ny = (y + dy + HEIGHT) % HEIGHT;
                    count += grid[ny][nx];
                }}
            }}
            return count;
        }}
        
        function step() {{
            const newGrid = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0));
            for (let y = 0; y < HEIGHT; y++) {{
                for (let x = 0; x < WIDTH; x++) {{
                    const neighbors = countNeighbors(x, y);
                    if (grid[y][x]) {{
                        newGrid[y][x] = SURVIVE.includes(neighbors) ? 1 : 0;
                    }} else {{
                        newGrid[y][x] = BIRTH.includes(neighbors) ? 1 : 0;
                    }}
                }}
            }}
            grid = newGrid;
            draw();
        }}
        
        function draw() {{
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#4ae';
            for (let y = 0; y < HEIGHT; y++) {{
                for (let x = 0; x < WIDTH; x++) {{
                    if (grid[y][x]) {{
                        ctx.fillRect(x * CELL_SIZE + 1, y * CELL_SIZE + 1, 
                                     CELL_SIZE - 2, CELL_SIZE - 2);
                    }}
                }}
            }}
        }}
        
        canvas.addEventListener('click', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / CELL_SIZE);
            const y = Math.floor((e.clientY - rect.top) / CELL_SIZE);
            if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT) {{
                grid[y][x] = 1 - grid[y][x];
                draw();
            }}
        }});
        
        document.getElementById('startStop').addEventListener('click', () => {{
            running = !running;
            document.getElementById('startStop').textContent = running ? 'Stop' : 'Start';
            if (running) {{
                intervalId = setInterval(step, 100);
            }} else {{
                clearInterval(intervalId);
            }}
        }});
        
        document.getElementById('step').addEventListener('click', step);
        
        document.getElementById('clear').addEventListener('click', () => {{
            grid = Array(HEIGHT).fill(null).map(() => Array(WIDTH).fill(0));
            draw();
        }});
        
        document.getElementById('random').addEventListener('click', () => {{
            grid = Array(HEIGHT).fill(null).map(() => 
                Array(WIDTH).fill(0).map(() => Math.random() < 0.3 ? 1 : 0)
            );
            draw();
        }});
        
        draw();
    </script>
</body>
</html>'''

    def _generate_particles(self, spec: KernelSpec) -> str:
        """Generate particle system code."""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Particle System</title>
    <style>
        * { margin: 0; padding: 0; }
        body { background: #111; overflow: hidden; }
        canvas { display: block; }
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        const particles = [];
        const GRAVITY = 0.1;
        
        class Particle {
            constructor(x, y) {
                this.x = x;
                this.y = y;
                this.vx = (Math.random() - 0.5) * 10;
                this.vy = (Math.random() - 0.5) * 10;
                this.life = 1;
                this.decay = 0.01 + Math.random() * 0.02;
                this.color = `hsl(${Math.random() * 60 + 10}, 100%, 50%)`;
            }
            
            update() {
                this.vy += GRAVITY;
                this.x += this.vx;
                this.y += this.vy;
                this.life -= this.decay;
                
                // Bounce
                if (this.x < 0 || this.x > canvas.width) this.vx *= -0.8;
                if (this.y > canvas.height) { this.y = canvas.height; this.vy *= -0.8; }
            }
            
            draw() {
                ctx.globalAlpha = this.life;
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, 4, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        canvas.addEventListener('click', (e) => {
            for (let i = 0; i < 50; i++) {
                particles.push(new Particle(e.clientX, e.clientY));
            }
        });
        
        function animate() {
            ctx.fillStyle = 'rgba(17, 17, 17, 0.1)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            for (let i = particles.length - 1; i >= 0; i--) {
                particles[i].update();
                particles[i].draw();
                if (particles[i].life <= 0) particles.splice(i, 1);
            }
            
            ctx.globalAlpha = 1;
            ctx.fillStyle = 'white';
            ctx.font = '16px system-ui';
            ctx.fillText('Click anywhere to spawn particles', 20, 30);
            ctx.fillText(`Particles: ${particles.length}`, 20, 50);
            
            requestAnimationFrame(animate);
        }
        
        animate();
    </script>
</body>
</html>'''

    def _generate_graph(self, spec: KernelSpec) -> str:
        """Generate graph visualization/pathfinding code."""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Graph Pathfinding</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; min-height: 100vh;
            background: #1a1a2e; font-family: system-ui; color: white;
        }
        canvas { border: 2px solid #4a4a6a; cursor: crosshair; }
        .controls { margin: 20px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
        button { 
            padding: 10px 20px; font-size: 14px; cursor: pointer;
            background: #4a4a6a; color: white; border: none; border-radius: 4px;
        }
        button:hover { background: #6a6a8a; }
        button.active { background: #4ae; }
        .info { color: #888; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <h1>Graph Pathfinding (A*)</h1>
    <div class="controls">
        <button id="wall" class="active">Draw Walls</button>
        <button id="start">Set Start</button>
        <button id="end">Set End</button>
        <button id="find">Find Path</button>
        <button id="clear">Clear</button>
    </div>
    <canvas id="canvas"></canvas>
    <div class="info">Draw walls, set start/end points, then find path</div>
    
    <script>
        const COLS = 40, ROWS = 30, SIZE = 20;
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = COLS * SIZE;
        canvas.height = ROWS * SIZE;
        
        let grid = Array(ROWS).fill(null).map(() => Array(COLS).fill(0));
        let start = {x: 1, y: 1};
        let end = {x: COLS - 2, y: ROWS - 2};
        let mode = 'wall';
        let path = [];
        
        function draw() {
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Grid
            for (let y = 0; y < ROWS; y++) {
                for (let x = 0; x < COLS; x++) {
                    if (grid[y][x] === 1) {
                        ctx.fillStyle = '#555';
                        ctx.fillRect(x * SIZE + 1, y * SIZE + 1, SIZE - 2, SIZE - 2);
                    }
                }
            }
            
            // Path
            ctx.fillStyle = '#4ae';
            for (const p of path) {
                ctx.fillRect(p.x * SIZE + 4, p.y * SIZE + 4, SIZE - 8, SIZE - 8);
            }
            
            // Start/End
            ctx.fillStyle = '#4a4';
            ctx.fillRect(start.x * SIZE + 2, start.y * SIZE + 2, SIZE - 4, SIZE - 4);
            ctx.fillStyle = '#a44';
            ctx.fillRect(end.x * SIZE + 2, end.y * SIZE + 2, SIZE - 4, SIZE - 4);
        }
        
        function heuristic(a, b) {
            return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
        }
        
        function findPath() {
            const openSet = [start];
            const cameFrom = {};
            const gScore = {};
            const fScore = {};
            const key = (p) => `${p.x},${p.y}`;
            
            gScore[key(start)] = 0;
            fScore[key(start)] = heuristic(start, end);
            
            while (openSet.length > 0) {
                openSet.sort((a, b) => (fScore[key(a)] || Infinity) - (fScore[key(b)] || Infinity));
                const current = openSet.shift();
                
                if (current.x === end.x && current.y === end.y) {
                    path = [];
                    let c = current;
                    while (cameFrom[key(c)]) {
                        path.unshift(c);
                        c = cameFrom[key(c)];
                    }
                    draw();
                    return;
                }
                
                const neighbors = [
                    {x: current.x + 1, y: current.y},
                    {x: current.x - 1, y: current.y},
                    {x: current.x, y: current.y + 1},
                    {x: current.x, y: current.y - 1},
                ];
                
                for (const n of neighbors) {
                    if (n.x < 0 || n.x >= COLS || n.y < 0 || n.y >= ROWS) continue;
                    if (grid[n.y][n.x] === 1) continue;
                    
                    const tentative = (gScore[key(current)] || 0) + 1;
                    if (tentative < (gScore[key(n)] || Infinity)) {
                        cameFrom[key(n)] = current;
                        gScore[key(n)] = tentative;
                        fScore[key(n)] = tentative + heuristic(n, end);
                        if (!openSet.find(o => o.x === n.x && o.y === n.y)) {
                            openSet.push(n);
                        }
                    }
                }
            }
            
            path = [];
            draw();
            alert('No path found!');
        }
        
        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / SIZE);
            const y = Math.floor((e.clientY - rect.top) / SIZE);
            
            if (mode === 'wall') {
                grid[y][x] = 1 - grid[y][x];
            } else if (mode === 'start') {
                start = {x, y};
                grid[y][x] = 0;
            } else if (mode === 'end') {
                end = {x, y};
                grid[y][x] = 0;
            }
            path = [];
            draw();
        });
        
        document.querySelectorAll('.controls button').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.id === 'find') { findPath(); return; }
                if (btn.id === 'clear') { 
                    grid = Array(ROWS).fill(null).map(() => Array(COLS).fill(0));
                    path = [];
                    draw();
                    return;
                }
                document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                mode = btn.id;
            });
        });
        
        draw();
    </script>
</body>
</html>'''

    def _generate_sequence(self, spec: KernelSpec) -> str:
        """Generate sorting visualization code."""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Sorting Visualizer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; min-height: 100vh;
            background: #1a1a2e; font-family: system-ui; color: white;
        }
        canvas { border: 2px solid #4a4a6a; }
        .controls { margin: 20px; display: flex; gap: 10px; }
        button, select { 
            padding: 10px 20px; font-size: 16px; cursor: pointer;
            background: #4a4a6a; color: white; border: none; border-radius: 4px;
        }
        button:hover { background: #6a6a8a; }
        .info { color: #888; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Sorting Visualizer</h1>
    <div class="controls">
        <select id="algorithm">
            <option value="bubble">Bubble Sort</option>
            <option value="quick">Quick Sort</option>
            <option value="merge">Merge Sort</option>
            <option value="insertion">Insertion Sort</option>
        </select>
        <button id="sort">Sort</button>
        <button id="random">Randomize</button>
    </div>
    <canvas id="canvas"></canvas>
    <div class="info">Comparisons: <span id="comps">0</span> | Swaps: <span id="swaps">0</span></div>
    
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const N = 100;
        canvas.width = N * 8;
        canvas.height = 400;
        
        let arr = [];
        let comparisons = 0, swaps = 0;
        let sorting = false;
        
        function randomize() {
            arr = Array.from({length: N}, () => Math.random() * canvas.height * 0.9 + 10);
            comparisons = 0; swaps = 0;
            updateStats();
            draw();
        }
        
        function draw(highlight = []) {
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            for (let i = 0; i < arr.length; i++) {
                ctx.fillStyle = highlight.includes(i) ? '#f44' : '#4ae';
                ctx.fillRect(i * 8, canvas.height - arr[i], 6, arr[i]);
            }
        }
        
        function updateStats() {
            document.getElementById('comps').textContent = comparisons;
            document.getElementById('swaps').textContent = swaps;
        }
        
        async function sleep(ms) {
            return new Promise(r => setTimeout(r, ms));
        }
        
        async function bubbleSort() {
            for (let i = 0; i < arr.length; i++) {
                for (let j = 0; j < arr.length - i - 1; j++) {
                    comparisons++;
                    draw([j, j + 1]);
                    await sleep(5);
                    if (arr[j] > arr[j + 1]) {
                        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
                        swaps++;
                    }
                    updateStats();
                }
            }
        }
        
        async function insertionSort() {
            for (let i = 1; i < arr.length; i++) {
                let key = arr[i];
                let j = i - 1;
                while (j >= 0 && arr[j] > key) {
                    comparisons++;
                    arr[j + 1] = arr[j];
                    swaps++;
                    draw([j, j + 1]);
                    await sleep(5);
                    updateStats();
                    j--;
                }
                arr[j + 1] = key;
            }
        }
        
        async function quickSort(lo = 0, hi = arr.length - 1) {
            if (lo >= hi) return;
            let pivot = arr[hi];
            let i = lo;
            for (let j = lo; j < hi; j++) {
                comparisons++;
                draw([i, j, hi]);
                await sleep(10);
                if (arr[j] < pivot) {
                    [arr[i], arr[j]] = [arr[j], arr[i]];
                    swaps++;
                    i++;
                }
                updateStats();
            }
            [arr[i], arr[hi]] = [arr[hi], arr[i]];
            swaps++;
            await quickSort(lo, i - 1);
            await quickSort(i + 1, hi);
        }
        
        document.getElementById('sort').addEventListener('click', async () => {
            if (sorting) return;
            sorting = true;
            comparisons = 0; swaps = 0;
            const algo = document.getElementById('algorithm').value;
            if (algo === 'bubble') await bubbleSort();
            else if (algo === 'insertion') await insertionSort();
            else if (algo === 'quick') await quickSort();
            draw();
            sorting = false;
        });
        
        document.getElementById('random').addEventListener('click', () => {
            if (!sorting) randomize();
        });
        
        randomize();
    </script>
</body>
</html>'''

    def _generate_stub(self, spec: KernelSpec) -> str:
        """Generate a stub for unsupported primitives."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>{spec.primitive.value.title()} Kernel</title>
    <style>
        body {{ 
            font-family: system-ui; background: #1a1a2e; color: white;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; margin: 0;
        }}
        .info {{ 
            background: #2a2a4e; padding: 40px; border-radius: 8px;
            max-width: 600px;
        }}
        pre {{ background: #1a1a2e; padding: 20px; border-radius: 4px; overflow: auto; }}
    </style>
</head>
<body>
    <div class="info">
        <h1>{spec.primitive.value.title()} Kernel</h1>
        <p>This kernel type is recognized but full code generation is not yet implemented.</p>
        <h3>Detected Specification:</h3>
        <pre>{spec.to_dict()}</pre>
        <p>Components detected:</p>
        <ul>
            <li>Primitive: {spec.primitive.value}</li>
            <li>Operations: {', '.join(o.value for o in spec.operations)}</li>
            <li>Control: {spec.control.value}</li>
            <li>Termination: {spec.termination.value}</li>
        </ul>
    </div>
</body>
</html>'''


# =============================================================================
# Module API
# =============================================================================

composer = KernelComposer()


def can_compose(description: str) -> bool:
    """Check if we can compose a kernel for this description."""
    return composer.can_compose(description)


def compose(description: str) -> Optional[KernelSpec]:
    """Compose a kernel specification from description."""
    return composer.compose(description)


def generate(description: str) -> Optional[str]:
    """Generate code for a description (full pipeline)."""
    spec = composer.compose(description)
    if spec:
        return composer.generate(spec)
    return None


def analyze(description: str) -> Dict:
    """Analyze a description and return detected components."""
    return {
        'primitive': detect_primitive(description),
        'operations': detect_operations(description),
        'control': detect_control(description),
        'termination': detect_termination(description),
        'known_algorithm': detect_known_algorithm(description),
        'can_compose': can_compose(description),
    }


# =============================================================================
# Test
# =============================================================================

if __name__ == '__main__':
    tests = [
        "Conway's Game of Life",
        "a virus spread simulator",
        "pathfinding visualizer",
        "particle physics simulation",
        "sorting algorithm visualizer",
        "a recipe app",  # Should NOT match
        "genetic algorithm optimizer",
        "maze solver",
        "flocking birds simulation",
    ]
    
    print("=" * 60)
    print("KERNEL COMPOSER TEST")
    print("=" * 60)
    
    for desc in tests:
        analysis = analyze(desc)
        spec = compose(desc)
        
        print(f"\n{desc}")
        print(f"  Can compose: {analysis['can_compose']}")
        if analysis['can_compose']:
            print(f"  Primitive: {analysis['primitive'].value if analysis['primitive'] else 'None'}")
            print(f"  Operations: {[o.value for o in analysis['operations']]}")
            print(f"  Control: {analysis['control'].value}")
            print(f"  Known: {analysis['known_algorithm'] or 'novel'}")
        else:
            print(f"  -> Falls back to template system")
