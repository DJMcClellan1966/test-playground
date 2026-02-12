"""
Component-Based Game Engine for App Forge

Instead of 30+ separate game templates with duplicated code,
this engine provides a unified structure where games are defined
as configurations that plug into a common shell.

Architecture:
  GameEngine (common shell)
  ├── HTML boilerplate
  ├── CSS (configurable themes)
  ├── Input abstraction (keys/clicks/touch)
  ├── Game loop (init → update → render)
  ├── State management (score, gameOver, etc)
  └── UI overlay (score display, game over screen)
  
  GameConfig (per-game)
  ├── render_type: 'canvas' | 'grid' | 'cards'
  ├── state: initial state variables
  ├── mechanics: JS code for game logic
  ├── renderer: JS code for drawing
  └── input_map: key/click bindings
  
Benefits:
  - ~60% code reduction
  - Adding new games = defining a config dict
  - Consistent styling across all games
  - Easier maintenance
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


@dataclass
class GameConfig:
    """Configuration for a game type."""
    id: str
    name: str
    render_type: str  # 'canvas', 'grid', 'cards', 'custom'
    
    # Canvas games
    canvas_width: int = 400
    canvas_height: int = 400
    cell_size: int = 20
    
    # Grid games  
    grid_rows: int = 3
    grid_cols: int = 3
    
    # Initial state (becomes JS variables)
    state: Dict = field(default_factory=dict)
    
    # JavaScript code snippets
    init_code: str = ""      # Called once at start
    update_code: str = ""    # Called each frame/tick
    render_code: str = ""    # Draw the game
    input_handlers: str = "" # Event handler code
    
    # Additional JS functions
    helpers: str = ""        # Helper functions
    
    # Input configuration
    keys: List[str] = field(default_factory=list)  # Keys to listen for
    click_enabled: bool = True
    
    # Game loop type
    loop_type: str = "raf"  # 'raf' (requestAnimationFrame), 'interval', 'event'
    tick_ms: int = 100      # For interval-based games
    
    # Styling
    primary_color: str = "#4CAF50"
    secondary_color: str = "#2196F3"
    bg_color: str = "#1a1a2e"


class GameEngine:
    """Generates complete game HTML from a GameConfig."""
    
    def __init__(self):
        self.configs: Dict[str, GameConfig] = {}
        self._register_builtin_games()
    
    def register(self, config: GameConfig):
        """Register a game configuration."""
        self.configs[config.id] = config
    
    def generate(self, game_id: str, title: str, desc: str = "") -> str:
        """Generate complete HTML for a game."""
        config = self.configs.get(game_id)
        if not config:
            raise ValueError(f"Unknown game: {game_id}")
        
        return self._build_html(config, title, desc)
    
    def _build_html(self, cfg: GameConfig, title: str, desc: str) -> str:
        """Build the complete HTML for a game."""
        
        # Build the game area based on render type
        if cfg.render_type == "canvas":
            game_area = f'<canvas id="gameCanvas" width="{cfg.canvas_width}" height="{cfg.canvas_height}"></canvas>'
            render_setup = f'''
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const CELL = {cfg.cell_size};
const COLS = Math.floor(canvas.width / CELL);
const ROWS = Math.floor(canvas.height / CELL);'''
        elif cfg.render_type == "grid":
            game_area = '<div id="gameGrid" class="game-grid"></div>'
            render_setup = f'''
const ROWS = {cfg.grid_rows};
const COLS = {cfg.grid_cols};
const grid = document.getElementById('gameGrid');'''
        elif cfg.render_type == "cards":
            game_area = '<div id="cardArea" class="card-area"></div>'
            render_setup = '''const cardArea = document.getElementById('cardArea');'''
        else:
            game_area = '<div id="gameArea" class="game-area"></div>'
            render_setup = '''const gameArea = document.getElementById('gameArea');'''
        
        # Build state initialization
        state_init = "\n".join(f"let {k} = {json.dumps(v)};" for k, v in cfg.state.items())
        
        # Build input handlers
        input_code = self._build_input_handlers(cfg)
        
        # Build game loop
        loop_code = self._build_game_loop(cfg)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: {cfg.bg_color};
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }}
        h1 {{
            margin-bottom: 10px;
            color: {cfg.primary_color};
        }}
        #scoreDisplay {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: {cfg.secondary_color};
        }}
        #gameContainer {{
            position: relative;
            background: #16213e;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        canvas {{
            display: block;
            background: #0f0f23;
            border-radius: 5px;
        }}
        .game-grid {{
            display: grid;
            grid-template-columns: repeat({cfg.grid_cols}, 1fr);
            gap: 5px;
            padding: 10px;
        }}
        .grid-cell {{
            aspect-ratio: 1;
            background: #2d3436;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .grid-cell:hover {{ background: #636e72; }}
        .card-area {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            max-width: 500px;
        }}
        .card {{
            width: 60px;
            height: 90px;
            background: white;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            cursor: pointer;
            color: #333;
        }}
        #gameOver {{
            position: absolute;
            inset: 0;
            background: rgba(0,0,0,0.85);
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }}
        #gameOver h2 {{ color: {cfg.primary_color}; margin-bottom: 10px; }}
        #gameOver p {{ margin-bottom: 20px; }}
        button {{
            background: {cfg.primary_color};
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 1em;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 15px;
        }}
        button:hover {{ filter: brightness(1.1); }}
        .controls {{
            margin-top: 15px;
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div id="scoreDisplay">Score: <span id="score">0</span></div>
    <div id="gameContainer">
        {game_area}
        <div id="gameOver">
            <h2>Game Over!</h2>
            <p>Final Score: <span id="finalScore">0</span></p>
            <button onclick="restart()">Play Again</button>
        </div>
    </div>
    <div class="controls">{self._get_control_hints(cfg)}</div>
    <button onclick="restart()">Restart</button>
    
    <script>
        // ===== ENGINE SETUP =====
        {render_setup}
        
        // ===== GAME STATE =====
        {state_init}
        let score = 0;
        let gameOver = false;
        
        // ===== HELPER FUNCTIONS =====
        {cfg.helpers}
        
        function showGameOver() {{
            gameOver = true;
            document.getElementById('finalScore').textContent = score;
            document.getElementById('gameOver').style.display = 'flex';
        }}
        
        function updateScore(points) {{
            score += points;
            document.getElementById('score').textContent = score;
        }}
        
        function setScore(val) {{
            score = val;
            document.getElementById('score').textContent = score;
        }}
        
        // ===== GAME LOGIC =====
        function init() {{
            score = 0;
            gameOver = false;
            document.getElementById('score').textContent = '0';
            document.getElementById('gameOver').style.display = 'none';
            {cfg.init_code}
        }}
        
        function update() {{
            if (gameOver) return;
            {cfg.update_code}
        }}
        
        function render() {{
            {cfg.render_code}
        }}
        
        function restart() {{
            init();
            render();
        }}
        
        // ===== INPUT HANDLING =====
        {input_code}
        
        // ===== GAME LOOP =====
        {loop_code}
        
        // Start the game
        init();
        render();
    </script>
</body>
</html>'''
    
    def _build_input_handlers(self, cfg: GameConfig) -> str:
        """Generate input event handlers."""
        code = ""
        
        if cfg.keys:
            code += f'''
document.addEventListener('keydown', e => {{
    if (gameOver) return;
    {cfg.input_handlers}
}});'''
        
        if cfg.click_enabled:
            target = "canvas" if cfg.render_type == "canvas" else "document"
            code += f'''
{target if cfg.render_type == "canvas" else "document.getElementById('gameContainer')"}.addEventListener('click', e => {{
    if (gameOver) return;
    {cfg.input_handlers if not cfg.keys else '// Click handling in render/grid setup'}
}});'''
        
        return code
    
    def _build_game_loop(self, cfg: GameConfig) -> str:
        """Generate the game loop."""
        if cfg.loop_type == "raf":
            return '''
let lastTime = 0;
function gameLoop(timestamp) {
    if (timestamp - lastTime > 16) {  // ~60fps
        update();
        render();
        lastTime = timestamp;
    }
    if (!gameOver) requestAnimationFrame(gameLoop);
}
requestAnimationFrame(gameLoop);'''
        
        elif cfg.loop_type == "interval":
            return f'''
setInterval(() => {{
    update();
    render();
}}, {cfg.tick_ms});'''
        
        else:  # event-driven
            return "// Event-driven game - no loop needed"
    
    def _get_control_hints(self, cfg: GameConfig) -> str:
        """Generate control hints based on config."""
        hints = []
        if "Arrow" in str(cfg.keys):
            hints.append("Arrow keys to move")
        if "Space" in str(cfg.keys) or " " in str(cfg.keys):
            hints.append("Space to action")
        if cfg.click_enabled and cfg.render_type in ("grid", "cards"):
            hints.append("Click to play")
        return " | ".join(hints) if hints else "Use arrow keys or click"
    
    def _register_builtin_games(self):
        """Register the built-in game configurations."""
        
        # ===== SNAKE =====
        self.register(GameConfig(
            id="snake",
            name="Snake",
            render_type="canvas",
            canvas_width=400,
            canvas_height=400,
            cell_size=20,
            state={
                "snake": [[5, 5]],
                "food": [10, 10],
                "dx": 1,
                "dy": 0,
                "nextDx": 1,
                "nextDy": 0,
            },
            keys=["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"],
            loop_type="interval",
            tick_ms=120,
            
            init_code='''
snake = [[5, 5], [4, 5], [3, 5]];
food = [Math.floor(Math.random() * COLS), Math.floor(Math.random() * ROWS)];
dx = 1; dy = 0; nextDx = 1; nextDy = 0;
''',
            
            update_code='''
dx = nextDx; dy = nextDy;
const head = [snake[0][0] + dx, snake[0][1] + dy];

// Wall collision
if (head[0] < 0 || head[0] >= COLS || head[1] < 0 || head[1] >= ROWS) {
    showGameOver(); return;
}

// Self collision
if (snake.some(s => s[0] === head[0] && s[1] === head[1])) {
    showGameOver(); return;
}

snake.unshift(head);

// Eat food
if (head[0] === food[0] && head[1] === food[1]) {
    updateScore(10);
    do {
        food = [Math.floor(Math.random() * COLS), Math.floor(Math.random() * ROWS)];
    } while (snake.some(s => s[0] === food[0] && s[1] === food[1]));
} else {
    snake.pop();
}
''',
            
            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Draw snake
ctx.fillStyle = '#4CAF50';
snake.forEach((seg, i) => {
    ctx.fillStyle = i === 0 ? '#66BB6A' : '#4CAF50';
    ctx.fillRect(seg[0] * CELL + 1, seg[1] * CELL + 1, CELL - 2, CELL - 2);
});

// Draw food
ctx.fillStyle = '#f44336';
ctx.beginPath();
ctx.arc(food[0] * CELL + CELL/2, food[1] * CELL + CELL/2, CELL/2 - 2, 0, Math.PI * 2);
ctx.fill();
''',
            
            input_handlers='''
const keyMap = {
    'ArrowUp': [0, -1], 'ArrowDown': [0, 1],
    'ArrowLeft': [-1, 0], 'ArrowRight': [1, 0]
};
if (keyMap[e.key] && !(keyMap[e.key][0] === -dx && keyMap[e.key][1] === -dy)) {
    [nextDx, nextDy] = keyMap[e.key];
    e.preventDefault();
}
''',
            
            click_enabled=False,
        ))
        
        # ===== PONG =====
        self.register(GameConfig(
            id="pong",
            name="Pong",
            render_type="canvas",
            canvas_width=600,
            canvas_height=400,
            state={
                "paddleH": 80,
                "paddleW": 10,
                "ballSize": 10,
                "playerY": 160,
                "aiY": 160,
                "ballX": 300,
                "ballY": 200,
                "ballDx": 4,
                "ballDy": 3,
                "playerScore": 0,
                "aiScore": 0,
            },
            keys=["ArrowUp", "ArrowDown", "w", "s"],
            loop_type="raf",
            
            init_code='''
playerY = canvas.height/2 - paddleH/2;
aiY = canvas.height/2 - paddleH/2;
ballX = canvas.width/2;
ballY = canvas.height/2;
ballDx = (Math.random() > 0.5 ? 1 : -1) * 4;
ballDy = (Math.random() - 0.5) * 6;
playerScore = 0; aiScore = 0;
''',

            update_code='''
// Move ball
ballX += ballDx;
ballY += ballDy;

// Top/bottom bounce
if (ballY <= 0 || ballY >= canvas.height - ballSize) ballDy = -ballDy;

// Paddle collision
if (ballX <= paddleW + 10 && ballY >= playerY && ballY <= playerY + paddleH) {
    ballDx = Math.abs(ballDx) * 1.05;
    ballDy += (ballY - (playerY + paddleH/2)) * 0.1;
}
if (ballX >= canvas.width - paddleW - 10 - ballSize && ballY >= aiY && ballY <= aiY + paddleH) {
    ballDx = -Math.abs(ballDx) * 1.05;
}

// Score
if (ballX < 0) {
    aiScore++;
    ballX = canvas.width/2; ballY = canvas.height/2;
    ballDx = 4; ballDy = (Math.random() - 0.5) * 6;
}
if (ballX > canvas.width) {
    playerScore++;
    updateScore(1);
    ballX = canvas.width/2; ballY = canvas.height/2;
    ballDx = -4; ballDy = (Math.random() - 0.5) * 6;
}

// AI movement
const aiCenter = aiY + paddleH/2;
if (aiCenter < ballY - 20) aiY += 3;
if (aiCenter > ballY + 20) aiY -= 3;
aiY = Math.max(0, Math.min(canvas.height - paddleH, aiY));

if (playerScore >= 5 || aiScore >= 5) showGameOver();
''',

            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Center line
ctx.setLineDash([10, 10]);
ctx.strokeStyle = '#333';
ctx.beginPath();
ctx.moveTo(canvas.width/2, 0);
ctx.lineTo(canvas.width/2, canvas.height);
ctx.stroke();
ctx.setLineDash([]);

// Paddles
ctx.fillStyle = '#4CAF50';
ctx.fillRect(10, playerY, paddleW, paddleH);
ctx.fillStyle = '#f44336';
ctx.fillRect(canvas.width - paddleW - 10, aiY, paddleW, paddleH);

// Ball
ctx.fillStyle = '#fff';
ctx.beginPath();
ctx.arc(ballX, ballY, ballSize/2, 0, Math.PI * 2);
ctx.fill();

// Scores
ctx.font = '30px Arial';
ctx.fillText(playerScore, canvas.width/4, 50);
ctx.fillText(aiScore, 3*canvas.width/4, 50);
''',

            input_handlers='''
if (e.key === 'ArrowUp' || e.key === 'w') { playerY -= 20; e.preventDefault(); }
if (e.key === 'ArrowDown' || e.key === 's') { playerY += 20; e.preventDefault(); }
playerY = Math.max(0, Math.min(canvas.height - paddleH, playerY));
''',
            click_enabled=False,
        ))
        
        # ===== TIC TAC TOE =====
        self.register(GameConfig(
            id="tictactoe",
            name="Tic Tac Toe",
            render_type="grid",
            grid_rows=3,
            grid_cols=3,
            state={
                "board": ["", "", "", "", "", "", "", "", ""],
                "currentPlayer": "X",
                "winner": None,
            },
            loop_type="event",
            click_enabled=True,
            
            init_code='''
board = ["", "", "", "", "", "", "", "", ""];
currentPlayer = "X";
winner = null;
renderGrid();
''',

            helpers='''
function checkWin() {
    const wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
    for (const [a,b,c] of wins) {
        if (board[a] && board[a] === board[b] && board[a] === board[c]) {
            return board[a];
        }
    }
    return board.includes("") ? null : "tie";
}

function cellClick(i) {
    if (board[i] || winner || gameOver) return;
    board[i] = currentPlayer;
    winner = checkWin();
    if (winner) {
        if (winner !== "tie") updateScore(winner === "X" ? 10 : 0);
        setTimeout(showGameOver, 500);
    } else {
        currentPlayer = currentPlayer === "X" ? "O" : "X";
    }
    renderGrid();
}

function renderGrid() {
    grid.innerHTML = "";
    board.forEach((cell, i) => {
        const div = document.createElement("div");
        div.className = "grid-cell";
        div.textContent = cell;
        div.style.color = cell === "X" ? "#4CAF50" : "#f44336";
        div.onclick = () => cellClick(i);
        grid.appendChild(div);
    });
}
''',
            render_code="renderGrid();",
            update_code="",
            input_handlers="",
        ))
        
        # ===== MEMORY GAME =====
        self.register(GameConfig(
            id="memory",
            name="Memory Match",
            render_type="grid",
            grid_rows=4,
            grid_cols=4,
            state={
                "cards": [],
                "flipped": [],
                "matched": [],
                "moves": 0,
            },
            loop_type="event",
            
            init_code='''
const symbols = ["🍎","🍊","🍋","🍇","🍓","🍒","🥝","🍑"];
cards = [...symbols, ...symbols].sort(() => Math.random() - 0.5);
flipped = [];
matched = [];
moves = 0;
renderMemory();
''',

            helpers='''
function flipCard(i) {
    if (flipped.length >= 2 || flipped.includes(i) || matched.includes(i) || gameOver) return;
    flipped.push(i);
    moves++;
    renderMemory();
    
    if (flipped.length === 2) {
        setTimeout(() => {
            if (cards[flipped[0]] === cards[flipped[1]]) {
                matched.push(...flipped);
                updateScore(10);
                if (matched.length === cards.length) {
                    setTimeout(showGameOver, 300);
                }
            }
            flipped = [];
            renderMemory();
        }, 800);
    }
}

function renderMemory() {
    grid.innerHTML = "";
    cards.forEach((card, i) => {
        const div = document.createElement("div");
        div.className = "grid-cell";
        div.style.fontSize = "1.8em";
        const revealed = flipped.includes(i) || matched.includes(i);
        div.textContent = revealed ? card : "?";
        div.style.background = matched.includes(i) ? "#2d5" : (flipped.includes(i) ? "#456" : "#2d3436");
        div.onclick = () => flipCard(i);
        grid.appendChild(div);
    });
    document.getElementById("score").textContent = moves + " moves";
}
''',
            render_code="renderMemory();",
            update_code="",
            input_handlers="",
        ))
        
        # ===== FLAPPY =====
        self.register(GameConfig(
            id="flappy",
            name="Flappy Bird",
            render_type="canvas",
            canvas_width=400,
            canvas_height=600,
            state={
                "birdY": 300,
                "birdVel": 0,
                "pipes": [],
                "frame": 0,
            },
            keys=[" "],
            loop_type="raf",
            
            init_code='''
birdY = canvas.height / 2;
birdVel = 0;
pipes = [];
frame = 0;
''',

            update_code='''
frame++;

// Gravity
birdVel += 0.4;
birdY += birdVel;

// Spawn pipes
if (frame % 100 === 0) {
    const gap = 150;
    const gapY = Math.random() * (canvas.height - gap - 100) + 50;
    pipes.push({ x: canvas.width, gapY, gap, scored: false });
}

// Move pipes
pipes.forEach(p => p.x -= 3);
pipes = pipes.filter(p => p.x > -60);

// Collision
const birdX = 80, birdR = 15;
for (const p of pipes) {
    if (birdX + birdR > p.x && birdX - birdR < p.x + 50) {
        if (birdY - birdR < p.gapY || birdY + birdR > p.gapY + p.gap) {
            showGameOver(); return;
        }
    }
    if (!p.scored && p.x + 50 < birdX) {
        p.scored = true;
        updateScore(1);
    }
}

// Floor/ceiling
if (birdY < 0 || birdY > canvas.height) showGameOver();
''',

            render_code='''
// Sky
ctx.fillStyle = '#70c5ce';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Pipes
ctx.fillStyle = '#73bf2e';
pipes.forEach(p => {
    ctx.fillRect(p.x, 0, 50, p.gapY);
    ctx.fillRect(p.x, p.gapY + p.gap, 50, canvas.height);
});

// Bird
ctx.fillStyle = '#f7dc6f';
ctx.beginPath();
ctx.arc(80, birdY, 15, 0, Math.PI * 2);
ctx.fill();
ctx.fillStyle = '#e74c3c';
ctx.beginPath();
ctx.arc(88, birdY - 3, 4, 0, Math.PI * 2);
ctx.fill();
''',

            input_handlers='''
if (e.key === ' ' || e.code === 'Space') {
    birdVel = -8;
    e.preventDefault();
}
''',
            click_enabled=True,
            helpers='''
document.getElementById('gameContainer').addEventListener('click', () => {
    if (!gameOver) birdVel = -8;
});
'''
        ))

        # ===== TETRIS =====
        self.register(GameConfig(
            id="tetris",
            name="Tetris",
            render_type="canvas",
            canvas_width=300,
            canvas_height=600,
            cell_size=30,
            state={
                "board": [],
                "piece": None,
                "pieceX": 0,
                "pieceY": 0,
                "pieceType": 0,
            },
            keys=["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "],
            loop_type="interval",
            tick_ms=500,
            
            init_code='''
const SHAPES = [
    [[1,1,1,1]], // I
    [[1,1],[1,1]], // O
    [[0,1,0],[1,1,1]], // T
    [[1,0,0],[1,1,1]], // L
    [[0,0,1],[1,1,1]], // J
    [[0,1,1],[1,1,0]], // S
    [[1,1,0],[0,1,1]]  // Z
];
const COLORS = ['#00f0f0','#f0f000','#a000f0','#f0a000','#0000f0','#00f000','#f00000'];
board = Array(20).fill(null).map(() => Array(10).fill(0));
spawnPiece();
''',
            
            helpers='''
function spawnPiece() {
    pieceType = Math.floor(Math.random() * SHAPES.length);
    piece = SHAPES[pieceType].map(r => [...r]);
    pieceX = Math.floor((10 - piece[0].length) / 2);
    pieceY = 0;
    if (collides(pieceX, pieceY, piece)) showGameOver();
}

function collides(px, py, p) {
    for (let y = 0; y < p.length; y++) {
        for (let x = 0; x < p[y].length; x++) {
            if (p[y][x]) {
                const bx = px + x, by = py + y;
                if (bx < 0 || bx >= 10 || by >= 20) return true;
                if (by >= 0 && board[by][bx]) return true;
            }
        }
    }
    return false;
}

function merge() {
    for (let y = 0; y < piece.length; y++) {
        for (let x = 0; x < piece[y].length; x++) {
            if (piece[y][x] && pieceY + y >= 0) {
                board[pieceY + y][pieceX + x] = COLORS[pieceType];
            }
        }
    }
}

function clearLines() {
    let cleared = 0;
    for (let y = 19; y >= 0; y--) {
        if (board[y].every(c => c)) {
            board.splice(y, 1);
            board.unshift(Array(10).fill(0));
            cleared++;
            y++;
        }
    }
    if (cleared) updateScore(cleared * 100);
}

function rotate() {
    const rotated = piece[0].map((_, i) => piece.map(r => r[i]).reverse());
    if (!collides(pieceX, pieceY, rotated)) piece = rotated;
}
''',

            update_code='''
if (!collides(pieceX, pieceY + 1, piece)) {
    pieceY++;
} else {
    merge();
    clearLines();
    spawnPiece();
}
''',

            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Draw board
for (let y = 0; y < 20; y++) {
    for (let x = 0; x < 10; x++) {
        if (board[y][x]) {
            ctx.fillStyle = board[y][x];
            ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
    }
}

// Draw current piece
ctx.fillStyle = COLORS[pieceType];
for (let y = 0; y < piece.length; y++) {
    for (let x = 0; x < piece[y].length; x++) {
        if (piece[y][x]) {
            ctx.fillRect((pieceX + x) * CELL, (pieceY + y) * CELL, CELL - 1, CELL - 1);
        }
    }
}
''',

            input_handlers='''
if (e.key === 'ArrowLeft' && !collides(pieceX - 1, pieceY, piece)) { pieceX--; render(); }
if (e.key === 'ArrowRight' && !collides(pieceX + 1, pieceY, piece)) { pieceX++; render(); }
if (e.key === 'ArrowDown' && !collides(pieceX, pieceY + 1, piece)) { pieceY++; render(); }
if (e.key === 'ArrowUp' || e.key === ' ') { rotate(); render(); }
e.preventDefault();
''',
            click_enabled=False,
        ))

        # ===== GAME 2048 =====
        self.register(GameConfig(
            id="game_2048",
            name="2048",
            render_type="grid",
            grid_rows=4,
            grid_cols=4,
            state={"grid": []},
            keys=["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"],
            loop_type="event",
            
            init_code='''
grid = Array(4).fill(null).map(() => Array(4).fill(0));
addTile(); addTile();
render2048();
''',

            helpers='''
function addTile() {
    const empty = [];
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) if (!grid[r][c]) empty.push([r,c]);
    if (empty.length) {
        const [r,c] = empty[Math.floor(Math.random() * empty.length)];
        grid[r][c] = Math.random() < 0.9 ? 2 : 4;
    }
}

function slide(row) {
    let arr = row.filter(x => x);
    for (let i = 0; i < arr.length - 1; i++) {
        if (arr[i] === arr[i+1]) {
            arr[i] *= 2;
            updateScore(arr[i]);
            arr.splice(i+1, 1);
        }
    }
    while (arr.length < 4) arr.push(0);
    return arr;
}

function move(dir) {
    let moved = false;
    const prev = JSON.stringify(grid);
    if (dir === 'left') {
        grid = grid.map(r => slide(r));
    } else if (dir === 'right') {
        grid = grid.map(r => slide(r.reverse()).reverse());
    } else if (dir === 'up') {
        for (let c = 0; c < 4; c++) {
            let col = [grid[0][c], grid[1][c], grid[2][c], grid[3][c]];
            col = slide(col);
            for (let r = 0; r < 4; r++) grid[r][c] = col[r];
        }
    } else if (dir === 'down') {
        for (let c = 0; c < 4; c++) {
            let col = [grid[3][c], grid[2][c], grid[1][c], grid[0][c]];
            col = slide(col);
            for (let r = 0; r < 4; r++) grid[3-r][c] = col[r];
        }
    }
    if (JSON.stringify(grid) !== prev) {
        addTile();
        if (!canMove()) setTimeout(showGameOver, 300);
    }
    render2048();
}

function canMove() {
    for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
        if (!grid[r][c]) return true;
        if (c < 3 && grid[r][c] === grid[r][c+1]) return true;
        if (r < 3 && grid[r][c] === grid[r+1][c]) return true;
    }
    return false;
}

const TILE_COLORS = {0:'#cdc1b4',2:'#eee4da',4:'#ede0c8',8:'#f2b179',16:'#f59563',32:'#f67c5f',64:'#f65e3b',128:'#edcf72',256:'#edcc61',512:'#edc850',1024:'#edc53f',2048:'#edc22e'};

function render2048() {
    const gridEl = document.getElementById('gameGrid');
    gridEl.innerHTML = '';
    for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 4; c++) {
            const tile = document.createElement('div');
            tile.className = 'grid-cell';
            tile.style.background = TILE_COLORS[grid[r][c]] || '#3c3a32';
            tile.style.color = grid[r][c] > 4 ? '#f9f6f2' : '#776e65';
            tile.style.fontWeight = 'bold';
            tile.textContent = grid[r][c] || '';
            gridEl.appendChild(tile);
        }
    }
}
''',
            render_code="render2048();",
            update_code="",
            input_handlers='''
const dirs = {ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down'};
if (dirs[e.key]) { move(dirs[e.key]); e.preventDefault(); }
''',
        ))

        # ===== BREAKOUT =====
        self.register(GameConfig(
            id="breakout",
            name="Breakout",
            render_type="canvas",
            canvas_width=480,
            canvas_height=400,
            state={
                "paddleX": 200,
                "ballX": 240,
                "ballY": 350,
                "ballDx": 3,
                "ballDy": -3,
                "bricks": [],
            },
            keys=["ArrowLeft", "ArrowRight"],
            loop_type="raf",
            
            init_code='''
paddleX = canvas.width / 2 - 40;
ballX = canvas.width / 2;
ballY = canvas.height - 50;
ballDx = 3 * (Math.random() > 0.5 ? 1 : -1);
ballDy = -3;
bricks = [];
const rows = 5, cols = 8, brickW = 55, brickH = 20;
for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
        bricks.push({x: c * 60 + 5, y: r * 25 + 30, w: brickW, h: brickH, alive: true});
    }
}
''',

            update_code='''
ballX += ballDx;
ballY += ballDy;

// Wall bounce
if (ballX <= 5 || ballX >= canvas.width - 5) ballDx = -ballDx;
if (ballY <= 5) ballDy = -ballDy;

// Paddle bounce
if (ballY >= canvas.height - 30 && ballX >= paddleX && ballX <= paddleX + 80) {
    ballDy = -Math.abs(ballDy);
    ballDx += (ballX - (paddleX + 40)) * 0.1;
}

// Floor = game over
if (ballY > canvas.height) showGameOver();

// Brick collision
bricks.forEach(b => {
    if (b.alive && ballX >= b.x && ballX <= b.x + b.w && ballY >= b.y && ballY <= b.y + b.h) {
        b.alive = false;
        ballDy = -ballDy;
        updateScore(10);
    }
});

// Win check
if (bricks.every(b => !b.alive)) showGameOver();
''',

            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Bricks
const colors = ['#e74c3c','#e67e22','#f1c40f','#2ecc71','#3498db'];
bricks.forEach((b, i) => {
    if (b.alive) {
        ctx.fillStyle = colors[Math.floor(i / 8) % colors.length];
        ctx.fillRect(b.x, b.y, b.w, b.h);
    }
});

// Paddle
ctx.fillStyle = '#ecf0f1';
ctx.fillRect(paddleX, canvas.height - 20, 80, 10);

// Ball
ctx.fillStyle = '#fff';
ctx.beginPath();
ctx.arc(ballX, ballY, 6, 0, Math.PI * 2);
ctx.fill();
''',

            input_handlers='''
if (e.key === 'ArrowLeft') { paddleX = Math.max(0, paddleX - 25); e.preventDefault(); }
if (e.key === 'ArrowRight') { paddleX = Math.min(canvas.width - 80, paddleX + 25); e.preventDefault(); }
''',
            click_enabled=False,
        ))

        # ===== MINESWEEPER =====
        self.register(GameConfig(
            id="minesweeper",
            name="Minesweeper",
            render_type="grid",
            grid_rows=9,
            grid_cols=9,
            state={"board": [], "revealed": [], "flags": [], "mines": 10, "firstClick": True},
            loop_type="event",
            
            init_code='''
const SIZE = 9;
mines = 10;
board = Array(SIZE).fill(null).map(() => Array(SIZE).fill(0));
revealed = Array(SIZE).fill(null).map(() => Array(SIZE).fill(false));
flags = Array(SIZE).fill(null).map(() => Array(SIZE).fill(false));
firstClick = true;
renderMines();
''',

            helpers='''
function placeMines(safeR, safeC) {
    let placed = 0;
    while (placed < mines) {
        const r = Math.floor(Math.random() * 9);
        const c = Math.floor(Math.random() * 9);
        if (board[r][c] !== -1 && (Math.abs(r-safeR) > 1 || Math.abs(c-safeC) > 1)) {
            board[r][c] = -1;
            placed++;
        }
    }
    // Calculate numbers
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            if (board[r][c] === -1) continue;
            let count = 0;
            for (let dr = -1; dr <= 1; dr++) {
                for (let dc = -1; dc <= 1; dc++) {
                    const nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < 9 && nc >= 0 && nc < 9 && board[nr][nc] === -1) count++;
                }
            }
            board[r][c] = count;
        }
    }
}

function reveal(r, c) {
    if (r < 0 || r >= 9 || c < 0 || c >= 9 || revealed[r][c] || flags[r][c]) return;
    revealed[r][c] = true;
    updateScore(1);
    if (board[r][c] === 0) {
        for (let dr = -1; dr <= 1; dr++) {
            for (let dc = -1; dc <= 1; dc++) reveal(r + dr, c + dc);
        }
    }
}

function cellClick(r, c, rightClick) {
    if (gameOver) return;
    if (rightClick) {
        if (!revealed[r][c]) flags[r][c] = !flags[r][c];
        renderMines();
        return;
    }
    if (flags[r][c]) return;
    if (firstClick) {
        placeMines(r, c);
        firstClick = false;
    }
    if (board[r][c] === -1) {
        revealed = revealed.map(row => row.map(() => true));
        renderMines();
        setTimeout(showGameOver, 500);
        return;
    }
    reveal(r, c);
    // Check win
    let unrevealed = 0;
    for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) if (!revealed[r][c]) unrevealed++;
    if (unrevealed === mines) showGameOver();
    renderMines();
}

function renderMines() {
    const g = document.getElementById('gameGrid');
    g.style.gridTemplateColumns = 'repeat(9, 1fr)';
    g.innerHTML = '';
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.fontSize = '1em';
            if (revealed[r][c]) {
                cell.style.background = '#bbb';
                if (board[r][c] === -1) {
                    cell.textContent = '💣';
                    cell.style.background = '#f44';
                } else if (board[r][c] > 0) {
                    cell.textContent = board[r][c];
                    cell.style.color = ['#00f','#080','#f00','#008','#800','#088','#000','#888'][board[r][c]-1];
                }
            } else {
                cell.textContent = flags[r][c] ? '🚩' : '';
            }
            cell.onclick = () => cellClick(r, c, false);
            cell.oncontextmenu = (e) => { e.preventDefault(); cellClick(r, c, true); };
            g.appendChild(cell);
        }
    }
}
''',
            render_code="renderMines();",
            update_code="",
            input_handlers="",
        ))

        # ===== WORDLE =====
        self.register(GameConfig(
            id="wordle",
            name="Wordle",
            render_type="grid",
            grid_rows=6,
            grid_cols=5,
            state={"word": "", "guesses": [], "currentGuess": "", "row": 0},
            keys=["a-z", "Enter", "Backspace"],
            loop_type="event",
            
            init_code='''
const WORDS = ["REACT","HELLO","WORLD","CRANE","SLATE","AUDIO","RAISE","SIREN","STEAM","TRIED"];
word = WORDS[Math.floor(Math.random() * WORDS.length)];
guesses = [];
currentGuess = "";
row = 0;
renderWordle();
''',

            helpers='''
function renderWordle() {
    const g = document.getElementById('gameGrid');
    g.innerHTML = '';
    for (let r = 0; r < 6; r++) {
        for (let c = 0; c < 5; c++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.width = '50px';
            cell.style.height = '50px';
            if (r < guesses.length) {
                const letter = guesses[r][c];
                cell.textContent = letter;
                if (word[c] === letter) {
                    cell.style.background = '#6aaa64';
                } else if (word.includes(letter)) {
                    cell.style.background = '#c9b458';
                } else {
                    cell.style.background = '#787c7e';
                }
                cell.style.color = 'white';
            } else if (r === row) {
                cell.textContent = currentGuess[c] || '';
                cell.style.borderColor = '#565758';
            }
            g.appendChild(cell);
        }
    }
}

function submitGuess() {
    if (currentGuess.length !== 5) return;
    guesses.push(currentGuess);
    if (currentGuess === word) {
        updateScore((6 - row) * 100);
        setTimeout(showGameOver, 500);
    } else if (row >= 5) {
        setTimeout(showGameOver, 500);
    }
    row++;
    currentGuess = "";
    renderWordle();
}
''',
            render_code="renderWordle();",
            update_code="",
            input_handlers='''
if (e.key === 'Enter') { submitGuess(); }
else if (e.key === 'Backspace') { currentGuess = currentGuess.slice(0, -1); renderWordle(); }
else if (e.key.match(/^[a-zA-Z]$/) && currentGuess.length < 5) {
    currentGuess += e.key.toUpperCase();
    renderWordle();
}
''',
        ))

        # ===== HANGMAN =====
        self.register(GameConfig(
            id="hangman",
            name="Hangman",
            render_type="canvas",
            canvas_width=400,
            canvas_height=400,
            state={"word": "", "guessed": [], "wrong": 0},
            keys=["a-z"],
            loop_type="event",
            
            init_code='''
const WORDS = ["PYTHON","JAVASCRIPT","CODING","HANGMAN","PROGRAM","DEVELOPER","FUNCTION","VARIABLE"];
word = WORDS[Math.floor(Math.random() * WORDS.length)];
guessed = [];
wrong = 0;
''',

            helpers='''
function guessLetter(letter) {
    if (guessed.includes(letter) || gameOver) return;
    guessed.push(letter);
    if (!word.includes(letter)) {
        wrong++;
        if (wrong >= 6) setTimeout(showGameOver, 500);
    } else {
        const remaining = word.split('').filter(l => !guessed.includes(l));
        if (remaining.length === 0) {
            updateScore(100 - wrong * 10);
            setTimeout(showGameOver, 500);
        }
    }
    render();
}
''',

            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);

// Draw gallows
ctx.strokeStyle = '#888';
ctx.lineWidth = 3;
ctx.beginPath();
ctx.moveTo(50, 350); ctx.lineTo(150, 350);
ctx.moveTo(100, 350); ctx.lineTo(100, 50);
ctx.moveTo(100, 50); ctx.lineTo(250, 50);
ctx.moveTo(250, 50); ctx.lineTo(250, 80);
ctx.stroke();

// Draw hangman parts based on wrong guesses
ctx.strokeStyle = '#fff';
ctx.fillStyle = '#fff';
if (wrong >= 1) { ctx.beginPath(); ctx.arc(250, 110, 30, 0, Math.PI * 2); ctx.stroke(); } // Head
if (wrong >= 2) { ctx.beginPath(); ctx.moveTo(250, 140); ctx.lineTo(250, 240); ctx.stroke(); } // Body
if (wrong >= 3) { ctx.beginPath(); ctx.moveTo(250, 160); ctx.lineTo(200, 200); ctx.stroke(); } // Left arm
if (wrong >= 4) { ctx.beginPath(); ctx.moveTo(250, 160); ctx.lineTo(300, 200); ctx.stroke(); } // Right arm
if (wrong >= 5) { ctx.beginPath(); ctx.moveTo(250, 240); ctx.lineTo(200, 310); ctx.stroke(); } // Left leg
if (wrong >= 6) { ctx.beginPath(); ctx.moveTo(250, 240); ctx.lineTo(300, 310); ctx.stroke(); } // Right leg

// Draw word
ctx.font = '24px monospace';
ctx.textAlign = 'center';
let display = word.split('').map(l => guessed.includes(l) ? l : '_').join(' ');
ctx.fillText(display, 200, 380);

// Draw guessed letters
ctx.font = '14px sans-serif';
ctx.fillStyle = '#888';
ctx.fillText('Guessed: ' + guessed.join(', '), 200, 30);
''',

            input_handlers='''
const letter = e.key.toUpperCase();
if (letter.match(/^[A-Z]$/)) guessLetter(letter);
''',
            click_enabled=False,
        ))

        # ===== SUDOKU =====
        self.register(GameConfig(
            id="sudoku",
            name="Sudoku",
            render_type="grid",
            grid_rows=9,
            grid_cols=9,
            state={"puzzle": [], "solution": [], "selected": None},
            keys=["1-9"],
            loop_type="event",
            
            init_code='''
// Simple puzzle generator
const base = [[5,3,4,6,7,8,9,1,2],[6,7,2,1,9,5,3,4,8],[1,9,8,3,4,2,5,6,7],
              [8,5,9,7,6,1,4,2,3],[4,2,6,8,5,3,7,9,1],[7,1,3,9,2,4,8,5,6],
              [9,6,1,5,3,7,2,8,4],[2,8,7,4,1,9,6,3,5],[3,4,5,2,8,6,1,7,9]];
solution = base.map(r => [...r]);
puzzle = base.map(r => r.map(c => Math.random() < 0.5 ? c : 0));
selected = null;
renderSudoku();
''',

            helpers='''
function renderSudoku() {
    const g = document.getElementById('gameGrid');
    g.style.gridTemplateColumns = 'repeat(9, 1fr)';
    g.innerHTML = '';
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.fontSize = '1.2em';
            cell.style.borderWidth = '1px';
            if (c % 3 === 0) cell.style.borderLeftWidth = '3px';
            if (r % 3 === 0) cell.style.borderTopWidth = '3px';
            if (c === 8) cell.style.borderRightWidth = '3px';
            if (r === 8) cell.style.borderBottomWidth = '3px';
            const val = puzzle[r][c];
            cell.textContent = val || '';
            if (solution[r][c] === base[r][c] && base[r][c] !== 0 && val !== 0) {
                cell.style.color = '#888';
            }
            if (selected && selected[0] === r && selected[1] === c) {
                cell.style.background = '#4CAF50';
            }
            cell.onclick = () => { selected = [r, c]; renderSudoku(); };
            g.appendChild(cell);
        }
    }
    // Check win
    let correct = true;
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            if (puzzle[r][c] !== solution[r][c]) correct = false;
        }
    }
    if (correct && puzzle.flat().every(x => x !== 0)) showGameOver();
}
const base = [[5,3,4,6,7,8,9,1,2],[6,7,2,1,9,5,3,4,8],[1,9,8,3,4,2,5,6,7],
              [8,5,9,7,6,1,4,2,3],[4,2,6,8,5,3,7,9,1],[7,1,3,9,2,4,8,5,6],
              [9,6,1,5,3,7,2,8,4],[2,8,7,4,1,9,6,3,5],[3,4,5,2,8,6,1,7,9]];
''',
            render_code="renderSudoku();",
            update_code="",
            input_handlers='''
const num = parseInt(e.key);
if (selected && num >= 1 && num <= 9) {
    puzzle[selected[0]][selected[1]] = num;
    if (num === solution[selected[0]][selected[1]]) updateScore(10);
    renderSudoku();
}
''',
        ))

        # ===== CONNECT FOUR =====
        self.register(GameConfig(
            id="connect_four",
            name="Connect Four",
            render_type="grid",
            grid_rows=6,
            grid_cols=7,
            state={"board": [], "currentPlayer": 1},
            loop_type="event",
            
            init_code='''
board = Array(6).fill(null).map(() => Array(7).fill(0));
currentPlayer = 1;
renderConnect4();
''',

            helpers='''
function dropPiece(col) {
    if (gameOver) return;
    for (let row = 5; row >= 0; row--) {
        if (board[row][col] === 0) {
            board[row][col] = currentPlayer;
            if (checkWin4(row, col)) {
                updateScore(currentPlayer === 1 ? 100 : 0);
                setTimeout(showGameOver, 500);
            } else {
                currentPlayer = currentPlayer === 1 ? 2 : 1;
            }
            break;
        }
    }
    renderConnect4();
}

function checkWin4(row, col) {
    const dirs = [[0,1],[1,0],[1,1],[1,-1]];
    for (const [dr, dc] of dirs) {
        let count = 1;
        for (let i = 1; i < 4; i++) {
            const r = row + dr * i, c = col + dc * i;
            if (r >= 0 && r < 6 && c >= 0 && c < 7 && board[r][c] === currentPlayer) count++;
            else break;
        }
        for (let i = 1; i < 4; i++) {
            const r = row - dr * i, c = col - dc * i;
            if (r >= 0 && r < 6 && c >= 0 && c < 7 && board[r][c] === currentPlayer) count++;
            else break;
        }
        if (count >= 4) return true;
    }
    return false;
}

function renderConnect4() {
    const g = document.getElementById('gameGrid');
    g.style.gridTemplateColumns = 'repeat(7, 1fr)';
    g.innerHTML = '';
    for (let r = 0; r < 6; r++) {
        for (let c = 0; c < 7; c++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.style.background = '#1e3a8a';
            const piece = document.createElement('div');
            piece.style.width = '80%';
            piece.style.height = '80%';
            piece.style.borderRadius = '50%';
            piece.style.background = board[r][c] === 1 ? '#ef4444' : board[r][c] === 2 ? '#fbbf24' : '#0f172a';
            cell.appendChild(piece);
            cell.onclick = () => dropPiece(c);
            g.appendChild(cell);
        }
    }
    document.getElementById('score').textContent = (currentPlayer === 1 ? 'Red' : 'Yellow') + "'s turn";
}
''',
            render_code="renderConnect4();",
            update_code="",
            input_handlers="",
        ))

        # ===== BLACKJACK =====
        self.register(GameConfig(
            id="blackjack",
            name="Blackjack",
            render_type="cards",
            state={"deck": [], "playerHand": [], "dealerHand": [], "standing": False},
            loop_type="event",
            
            init_code='''
deck = [];
const suits = ['♠','♥','♦','♣'];
const values = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
for (const s of suits) for (const v of values) deck.push({suit: s, value: v});
deck = deck.sort(() => Math.random() - 0.5);
playerHand = [deck.pop(), deck.pop()];
dealerHand = [deck.pop(), deck.pop()];
standing = false;
renderBlackjack();
''',

            helpers='''
function cardValue(card) {
    if (['J','Q','K'].includes(card.value)) return 10;
    if (card.value === 'A') return 11;
    return parseInt(card.value);
}

function handValue(hand) {
    let val = hand.reduce((s, c) => s + cardValue(c), 0);
    let aces = hand.filter(c => c.value === 'A').length;
    while (val > 21 && aces > 0) { val -= 10; aces--; }
    return val;
}

function hit() {
    if (standing || gameOver) return;
    playerHand.push(deck.pop());
    if (handValue(playerHand) > 21) {
        standing = true;
        setTimeout(showGameOver, 500);
    }
    renderBlackjack();
}

function stand() {
    if (standing || gameOver) return;
    standing = true;
    while (handValue(dealerHand) < 17) dealerHand.push(deck.pop());
    const pv = handValue(playerHand), dv = handValue(dealerHand);
    if (dv > 21 || pv > dv) updateScore(100);
    setTimeout(showGameOver, 500);
    renderBlackjack();
}

function renderBlackjack() {
    const area = document.getElementById('cardArea');
    area.innerHTML = '<div style="margin-bottom:20px"><h3>Dealer: ' + (standing ? handValue(dealerHand) : '?') + '</h3></div>';
    const dealerCards = document.createElement('div');
    dealerCards.style.display = 'flex';
    dealerCards.style.gap = '10px';
    dealerCards.style.marginBottom = '30px';
    dealerHand.forEach((c, i) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.color = ['♥','♦'].includes(c.suit) ? 'red' : 'black';
        if (!standing && i > 0) {
            card.textContent = '?';
            card.style.background = '#2d3436';
            card.style.color = 'white';
        } else {
            card.textContent = c.value + c.suit;
        }
        dealerCards.appendChild(card);
    });
    area.appendChild(dealerCards);
    
    area.innerHTML += '<h3>You: ' + handValue(playerHand) + '</h3>';
    const playerCards = document.createElement('div');
    playerCards.style.display = 'flex';
    playerCards.style.gap = '10px';
    playerHand.forEach(c => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.color = ['♥','♦'].includes(c.suit) ? 'red' : 'black';
        card.textContent = c.value + c.suit;
        playerCards.appendChild(card);
    });
    area.appendChild(playerCards);
    
    if (!standing && !gameOver) {
        const btns = document.createElement('div');
        btns.style.marginTop = '20px';
        btns.innerHTML = '<button onclick="hit()">Hit</button> <button onclick="stand()">Stand</button>';
        area.appendChild(btns);
    }
}
''',
            render_code="renderBlackjack();",
            update_code="",
            input_handlers="",
        ))

        # ===== COOKIE CLICKER =====
        self.register(GameConfig(
            id="cookie_clicker",
            name="Cookie Clicker",
            render_type="custom",
            state={"cookies": 0, "cps": 0, "upgrades": []},
            loop_type="interval",
            tick_ms=1000,
            
            init_code='''
cookies = 0;
cps = 0;
upgrades = [
    {name: "Cursor", cost: 15, cps: 0.1, owned: 0},
    {name: "Grandma", cost: 100, cps: 1, owned: 0},
    {name: "Farm", cost: 500, cps: 5, owned: 0},
    {name: "Factory", cost: 3000, cps: 25, owned: 0}
];
renderClicker();
''',

            helpers='''
function clickCookie() {
    cookies++;
    updateScore(1);
    renderClicker();
}

function buyUpgrade(i) {
    const u = upgrades[i];
    if (cookies >= u.cost) {
        cookies -= u.cost;
        u.owned++;
        cps += u.cps;
        u.cost = Math.floor(u.cost * 1.15);
        renderClicker();
    }
}

function renderClicker() {
    const area = document.getElementById('gameArea');
    area.innerHTML = `
        <div style="text-align:center;padding:20px">
            <h2>🍪 ${Math.floor(cookies)} cookies</h2>
            <p>per second: ${cps.toFixed(1)}</p>
            <div style="font-size:80px;cursor:pointer;user-select:none" onclick="clickCookie()">🍪</div>
            <div style="margin-top:20px">
                ${upgrades.map((u, i) => `
                    <button onclick="buyUpgrade(${i})" ${cookies < u.cost ? 'disabled' : ''} style="margin:5px;padding:10px">
                        ${u.name} (${u.owned}) - ${u.cost} 🍪 [+${u.cps}/s]
                    </button>
                `).join('')}
            </div>
        </div>
    `;
}
''',
            render_code="renderClicker();",
            update_code="cookies += cps; updateScore(Math.floor(cps)); renderClicker();",
            input_handlers="",
            click_enabled=False,
        ))

        # ===== REACTION GAME =====
        self.register(GameConfig(
            id="reaction_game",
            name="Reaction Time",
            render_type="custom",
            state={"waiting": False, "startTime": 0, "times": []},
            loop_type="event",
            primary_color="#e74c3c",
            
            init_code='''
waiting = false;
startTime = 0;
times = [];
renderReaction();
''',

            helpers='''
function startWait() {
    document.getElementById('gameArea').innerHTML = '<div style="background:#e74c3c;height:300px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:2em;color:white" onclick="tooEarly()">Wait for green...</div>';
    const delay = 2000 + Math.random() * 3000;
    setTimeout(() => {
        if (!gameOver) {
            waiting = true;
            startTime = Date.now();
            document.getElementById('gameArea').innerHTML = '<div style="background:#2ecc71;height:300px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:2em;color:white" onclick="clicked()">CLICK NOW!</div>';
        }
    }, delay);
}

function tooEarly() {
    document.getElementById('gameArea').innerHTML = '<div style="background:#e74c3c;height:300px;display:flex;align-items:center;justify-content:center;font-size:2em;color:white"><div>Too early!<br><button onclick="startWait()">Try Again</button></div></div>';
}

function clicked() {
    if (!waiting) return;
    waiting = false;
    const time = Date.now() - startTime;
    times.push(time);
    updateScore(Math.max(0, 500 - time));
    const avg = Math.round(times.reduce((a,b) => a+b, 0) / times.length);
    document.getElementById('gameArea').innerHTML = `<div style="background:#3498db;height:300px;display:flex;align-items:center;justify-content:center;font-size:2em;color:white;flex-direction:column"><div>${time}ms</div><div style="font-size:0.6em">Average: ${avg}ms</div><button onclick="startWait()" style="margin-top:20px">Again</button></div>`;
}

function renderReaction() {
    document.getElementById('gameArea').innerHTML = '<div style="background:#3498db;height:300px;display:flex;align-items:center;justify-content:center;font-size:2em;color:white;cursor:pointer" onclick="startWait()">Click to Start</div>';
}
''',
            render_code="renderReaction();",
            update_code="",
            input_handlers="",
        ))

        # ===== TYPING TEST =====
        self.register(GameConfig(
            id="typing_test",
            name="Typing Test",
            render_type="custom",
            state={"words": [], "currentWord": 0, "input": "", "startTime": 0, "started": False},
            loop_type="event",
            
            init_code='''
const WORD_LIST = ["the","be","to","of","and","a","in","that","have","I","it","for","not","on","with","he","as","you","do","at","this","but","his","by","from","they","we","say","her","she","or","an","will","my","one","all","would","there","their","what","so","up","out","if","about","who","get","which","go","me"];
words = [];
for (let i = 0; i < 20; i++) words.push(WORD_LIST[Math.floor(Math.random() * WORD_LIST.length)]);
currentWord = 0;
input = "";
started = false;
startTime = 0;
renderTyping();
''',

            helpers='''
function renderTyping() {
    const area = document.getElementById('gameArea');
    const elapsed = started ? (Date.now() - startTime) / 1000 : 0;
    const wpm = elapsed > 0 ? Math.round((currentWord / elapsed) * 60) : 0;
    
    area.innerHTML = `
        <div style="padding:20px;text-align:center">
            <p style="font-size:1.2em;color:#888">${wpm} WPM | ${currentWord}/${words.length} words</p>
            <div style="font-size:1.5em;margin:20px;line-height:2">
                ${words.map((w, i) => {
                    if (i < currentWord) return '<span style="color:#2ecc71">' + w + '</span>';
                    if (i === currentWord) return '<span style="background:#3498db;color:white;padding:2px 4px;border-radius:3px">' + w + '</span>';
                    return '<span style="color:#888">' + w + '</span>';
                }).join(' ')}
            </div>
            <input type="text" id="typeInput" value="${input}" style="font-size:1.5em;padding:10px;width:200px;text-align:center" autofocus>
        </div>
    `;
    document.getElementById('typeInput').focus();
    document.getElementById('typeInput').oninput = (e) => {
        if (!started) { started = true; startTime = Date.now(); }
        input = e.target.value;
        if (input.trim() === words[currentWord]) {
            currentWord++;
            input = "";
            updateScore(10);
            if (currentWord >= words.length) {
                setScore(wpm);
                showGameOver();
            }
        }
        renderTyping();
    };
}
''',
            render_code="renderTyping();",
            update_code="",
            input_handlers="",
        ))

        # ===== COIN FLIP =====
        self.register(GameConfig(
            id="coin_flip",
            name="Coin Flip",
            render_type="custom",
            state={"result": "", "flipping": False, "heads": 0, "tails": 0},
            loop_type="event",
            
            init_code='''
result = "";
flipping = false;
heads = 0;
tails = 0;
renderCoin();
''',

            helpers='''
function flipCoin() {
    if (flipping) return;
    flipping = true;
    let count = 0;
    const interval = setInterval(() => {
        result = Math.random() > 0.5 ? "HEADS" : "TAILS";
        renderCoin();
        count++;
        if (count > 10) {
            clearInterval(interval);
            flipping = false;
            if (result === "HEADS") heads++; else tails++;
            renderCoin();
        }
    }, 100);
}

function renderCoin() {
    document.getElementById('gameArea').innerHTML = `
        <div style="text-align:center;padding:40px">
            <div style="font-size:120px;cursor:pointer;user-select:none;transition:transform 0.1s;${flipping ? 'transform:rotateY(' + Math.random() * 360 + 'deg)' : ''}" onclick="flipCoin()">
                ${result === "HEADS" ? '🪙' : result === "TAILS" ? '⚪' : '🪙'}
            </div>
            <h2 style="margin-top:20px">${result || 'Click to flip!'}</h2>
            <p style="color:#888">Heads: ${heads} | Tails: ${tails}</p>
        </div>
    `;
}
''',
            render_code="renderCoin();",
            update_code="",
            input_handlers="",
        ))

        # ===== DICE ROLLER =====
        self.register(GameConfig(
            id="dice_roller",
            name="Dice Roller",
            render_type="custom",
            state={"dice": [1], "rolling": False, "history": []},
            loop_type="event",
            
            init_code='''
dice = [1];
rolling = false;
history = [];
renderDice();
''',

            helpers='''
const DICE_FACES = ['⚀','⚁','⚂','⚃','⚄','⚅'];

function rollDice() {
    if (rolling) return;
    rolling = true;
    let count = 0;
    const interval = setInterval(() => {
        dice = dice.map(() => Math.floor(Math.random() * 6) + 1);
        renderDice();
        count++;
        if (count > 15) {
            clearInterval(interval);
            rolling = false;
            const total = dice.reduce((a,b) => a+b, 0);
            history.unshift(total);
            if (history.length > 5) history.pop();
            updateScore(total);
            renderDice();
        }
    }, 50);
}

function addDie() { if (dice.length < 5) { dice.push(1); renderDice(); } }
function removeDie() { if (dice.length > 1) { dice.pop(); renderDice(); } }

function renderDice() {
    document.getElementById('gameArea').innerHTML = `
        <div style="text-align:center;padding:20px">
            <div style="font-size:80px;cursor:pointer;user-select:none" onclick="rollDice()">
                ${dice.map(d => DICE_FACES[d-1]).join(' ')}
            </div>
            <h2>Total: ${dice.reduce((a,b) => a+b, 0)}</h2>
            <div style="margin:20px">
                <button onclick="removeDie()">-</button>
                <span style="margin:0 10px">${dice.length} dice</span>
                <button onclick="addDie()">+</button>
            </div>
            <p style="color:#888">Recent: ${history.join(', ') || 'none'}</p>
        </div>
    `;
}
''',
            render_code="renderDice();",
            update_code="",
            input_handlers="",
        ))

        # ===== ROCK PAPER SCISSORS =====
        self.register(GameConfig(
            id="rps",
            name="Rock Paper Scissors",
            render_type="custom",
            state={"playerWins": 0, "cpuWins": 0, "result": ""},
            loop_type="event",
            
            init_code='''
playerWins = 0;
cpuWins = 0;
result = "";
renderRPS();
''',

            helpers='''
const CHOICES = ['🪨', '📄', '✂️'];
const NAMES = ['Rock', 'Paper', 'Scissors'];

function play(playerIdx) {
    const cpuIdx = Math.floor(Math.random() * 3);
    const player = NAMES[playerIdx];
    const cpu = NAMES[cpuIdx];
    
    if (playerIdx === cpuIdx) {
        result = `${player} vs ${cpu} - Draw!`;
    } else if ((playerIdx + 1) % 3 === cpuIdx) {
        result = `${player} vs ${cpu} - You lose!`;
        cpuWins++;
    } else {
        result = `${player} vs ${cpu} - You win!`;
        playerWins++;
        updateScore(1);
    }
    renderRPS();
}

function renderRPS() {
    document.getElementById('gameArea').innerHTML = `
        <div style="text-align:center;padding:20px">
            <h2 style="margin-bottom:20px">You: ${playerWins} | CPU: ${cpuWins}</h2>
            <div style="font-size:60px;margin:20px">
                ${CHOICES.map((c, i) => `<span style="cursor:pointer;margin:10px" onclick="play(${i})">${c}</span>`).join('')}
            </div>
            <p style="font-size:1.2em;min-height:30px">${result}</p>
        </div>
    `;
}
''',
            render_code="renderRPS();",
            update_code="",
            input_handlers="",
        ))

        # ===== CALCULATOR =====
        self.register(GameConfig(
            id="calculator",
            name="Calculator",
            render_type="custom",
            state={"display": "0", "prev": None, "op": None, "newNum": True},
            loop_type="event",
            
            init_code='''
display = "0";
prev = null;
op = null;
newNum = true;
renderCalc();
''',

            helpers='''
function pressNum(n) {
    if (newNum) { display = n; newNum = false; }
    else display = display === "0" ? n : display + n;
    renderCalc();
}

function pressOp(o) {
    if (prev !== null && !newNum) calculate();
    prev = parseFloat(display);
    op = o;
    newNum = true;
    renderCalc();
}

function calculate() {
    if (prev === null || op === null) return;
    const curr = parseFloat(display);
    let result;
    switch(op) {
        case '+': result = prev + curr; break;
        case '-': result = prev - curr; break;
        case '*': result = prev * curr; break;
        case '/': result = curr !== 0 ? prev / curr : 'Error'; break;
    }
    display = String(result);
    prev = null;
    op = null;
    newNum = true;
    renderCalc();
}

function clear() {
    display = "0";
    prev = null;
    op = null;
    newNum = true;
    renderCalc();
}

function renderCalc() {
    const btns = ['7','8','9','/','4','5','6','*','1','2','3','-','0','.','=','+'];
    document.getElementById('gameArea').innerHTML = `
        <div style="max-width:300px;margin:auto;padding:20px">
            <div style="background:#333;color:white;font-size:2em;text-align:right;padding:20px;border-radius:5px;margin-bottom:10px">${display}</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px">
                <button onclick="clear()" style="grid-column:span 4;padding:15px;font-size:1.2em">C</button>
                ${btns.map(b => {
                    if (b === '=') return '<button onclick="calculate()" style="padding:15px;font-size:1.2em;background:#4CAF50;color:white">=</button>';
                    if (['+','-','*','/'].includes(b)) return '<button onclick="pressOp(\\''+b+'\\')" style="padding:15px;font-size:1.2em;background:#ff9800;color:white">'+b+'</button>';
                    return '<button onclick="pressNum(\\''+b+'\\')" style="padding:15px;font-size:1.2em">'+b+'</button>';
                }).join('')}
            </div>
        </div>
    `;
}
''',
            render_code="renderCalc();",
            update_code="",
            input_handlers="",
        ))

        # ===== TIMER =====
        self.register(GameConfig(
            id="timer",
            name="Timer / Pomodoro",
            render_type="custom",
            state={"seconds": 1500, "running": False, "mode": "pomodoro"},
            loop_type="interval",
            tick_ms=1000,
            
            init_code='''
seconds = 1500; // 25 minutes
running = false;
mode = "pomodoro";
renderTimer();
''',

            helpers='''
function setMode(m) {
    mode = m;
    if (m === 'pomodoro') seconds = 1500;
    else if (m === 'short') seconds = 300;
    else if (m === 'long') seconds = 900;
    running = false;
    renderTimer();
}

function toggleTimer() {
    running = !running;
    renderTimer();
}

function resetTimer() {
    setMode(mode);
}

function formatTime(s) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m.toString().padStart(2, '0') + ':' + sec.toString().padStart(2, '0');
}

function renderTimer() {
    document.getElementById('gameArea').innerHTML = `
        <div style="text-align:center;padding:20px">
            <div style="margin-bottom:20px">
                <button onclick="setMode('pomodoro')" style="${mode==='pomodoro'?'background:#4CAF50;color:white':''}">Pomodoro</button>
                <button onclick="setMode('short')" style="${mode==='short'?'background:#4CAF50;color:white':''}">Short Break</button>
                <button onclick="setMode('long')" style="${mode==='long'?'background:#4CAF50;color:white':''}">Long Break</button>
            </div>
            <div style="font-size:80px;font-family:monospace;margin:40px 0">${formatTime(seconds)}</div>
            <button onclick="toggleTimer()" style="font-size:1.5em;padding:15px 40px">${running ? 'Pause' : 'Start'}</button>
            <button onclick="resetTimer()" style="font-size:1.5em;padding:15px 40px;margin-left:10px">Reset</button>
        </div>
    `;
}
''',
            render_code="renderTimer();",
            update_code='''
if (running && seconds > 0) {
    seconds--;
    renderTimer();
    if (seconds === 0) {
        running = false;
        updateScore(1);
        alert('Time is up!');
    }
}
''',
            input_handlers="",
        ))

        # ===== CONVERTER =====
        self.register(GameConfig(
            id="converter",
            name="Unit Converter",
            render_type="custom",
            state={"value": 0, "fromUnit": "celsius", "toUnit": "fahrenheit"},
            loop_type="event",
            
            init_code='''
value = 0;
fromUnit = "celsius";
toUnit = "fahrenheit";
renderConverter();
''',

            helpers='''
const CONVERSIONS = {
    temp: {
        celsius_fahrenheit: v => v * 9/5 + 32,
        fahrenheit_celsius: v => (v - 32) * 5/9,
        celsius_kelvin: v => v + 273.15,
        kelvin_celsius: v => v - 273.15,
    },
    length: {
        meters_feet: v => v * 3.28084,
        feet_meters: v => v / 3.28084,
        km_miles: v => v * 0.621371,
        miles_km: v => v / 0.621371,
    },
    weight: {
        kg_lbs: v => v * 2.20462,
        lbs_kg: v => v / 2.20462,
    }
};

function convert() {
    const key = fromUnit + '_' + toUnit;
    for (const cat of Object.values(CONVERSIONS)) {
        if (cat[key]) return cat[key](value);
    }
    return value;
}

function renderConverter() {
    const result = convert();
    document.getElementById('gameArea').innerHTML = `
        <div style="max-width:400px;margin:auto;padding:20px">
            <h2 style="text-align:center;margin-bottom:20px">Unit Converter</h2>
            <div style="margin-bottom:20px">
                <input type="number" value="${value}" onchange="value=parseFloat(this.value);renderConverter()" style="width:100%;padding:15px;font-size:1.5em">
            </div>
            <div style="display:flex;gap:10px;margin-bottom:20px">
                <select onchange="fromUnit=this.value;renderConverter()" style="flex:1;padding:10px">
                    <option value="celsius" ${fromUnit==='celsius'?'selected':''}>Celsius</option>
                    <option value="fahrenheit" ${fromUnit==='fahrenheit'?'selected':''}>Fahrenheit</option>
                    <option value="meters" ${fromUnit==='meters'?'selected':''}>Meters</option>
                    <option value="feet" ${fromUnit==='feet'?'selected':''}>Feet</option>
                    <option value="kg" ${fromUnit==='kg'?'selected':''}>Kilograms</option>
                    <option value="lbs" ${fromUnit==='lbs'?'selected':''}>Pounds</option>
                </select>
                <span style="padding:10px">→</span>
                <select onchange="toUnit=this.value;renderConverter()" style="flex:1;padding:10px">
                    <option value="fahrenheit" ${toUnit==='fahrenheit'?'selected':''}>Fahrenheit</option>
                    <option value="celsius" ${toUnit==='celsius'?'selected':''}>Celsius</option>
                    <option value="feet" ${toUnit==='feet'?'selected':''}>Feet</option>
                    <option value="meters" ${toUnit==='meters'?'selected':''}>Meters</option>
                    <option value="lbs" ${toUnit==='lbs'?'selected':''}>Pounds</option>
                    <option value="kg" ${toUnit==='kg'?'selected':''}>Kilograms</option>
                </select>
            </div>
            <div style="text-align:center;font-size:2em;padding:20px;background:#333;color:white;border-radius:5px">
                ${result.toFixed(2)} ${toUnit}
            </div>
        </div>
    `;
}
''',
            render_code="renderConverter();",
            update_code="",
            input_handlers="",
        ))

        # ===== QUIZ =====
        self.register(GameConfig(
            id="quiz",
            name="Quiz Game",
            render_type="custom",
            state={"questions": [], "current": 0, "correct": 0},
            loop_type="event",
            
            init_code='''
questions = [
    {q: "What is the capital of France?", options: ["London", "Paris", "Berlin", "Madrid"], answer: 1},
    {q: "What is 7 x 8?", options: ["54", "56", "64", "48"], answer: 1},
    {q: "Who wrote Romeo and Juliet?", options: ["Dickens", "Austen", "Shakespeare", "Hemingway"], answer: 2},
    {q: "What planet is known as the Red Planet?", options: ["Venus", "Mars", "Jupiter", "Saturn"], answer: 1},
    {q: "What is the largest ocean?", options: ["Atlantic", "Indian", "Arctic", "Pacific"], answer: 3}
];
current = 0;
correct = 0;
renderQuiz();
''',

            helpers='''
function answer(idx) {
    if (idx === questions[current].answer) {
        correct++;
        updateScore(20);
    }
    current++;
    if (current >= questions.length) {
        setTimeout(showGameOver, 500);
    }
    renderQuiz();
}

function renderQuiz() {
    if (current >= questions.length) {
        document.getElementById('gameArea').innerHTML = `<div style="text-align:center;padding:40px"><h2>Quiz Complete!</h2><p>You got ${correct}/${questions.length} correct</p></div>`;
        return;
    }
    const q = questions[current];
    document.getElementById('gameArea').innerHTML = `
        <div style="padding:20px;max-width:500px;margin:auto">
            <p style="color:#888;margin-bottom:10px">Question ${current + 1} of ${questions.length}</p>
            <h2 style="margin-bottom:20px">${q.q}</h2>
            <div style="display:flex;flex-direction:column;gap:10px">
                ${q.options.map((opt, i) => `<button onclick="answer(${i})" style="padding:15px;font-size:1.1em;text-align:left">${opt}</button>`).join('')}
            </div>
        </div>
    `;
}
''',
            render_code="renderQuiz();",
            update_code="",
            input_handlers="",
        ))

        # ===== SLIDING PUZZLE =====
        self.register(GameConfig(
            id="sliding_puzzle",
            name="Sliding Puzzle",
            render_type="grid",
            grid_rows=4,
            grid_cols=4,
            state={"tiles": [], "moves": 0},
            loop_type="event",
            
            init_code='''
tiles = Array.from({length: 16}, (_, i) => i);
moves = 0;
// Shuffle
for (let i = tiles.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [tiles[i], tiles[j]] = [tiles[j], tiles[i]];
}
renderSliding();
''',

            helpers='''
function clickTile(idx) {
    const empty = tiles.indexOf(0);
    const row = Math.floor(idx / 4), col = idx % 4;
    const eRow = Math.floor(empty / 4), eCol = empty % 4;
    if ((Math.abs(row - eRow) === 1 && col === eCol) || (Math.abs(col - eCol) === 1 && row === eRow)) {
        [tiles[idx], tiles[empty]] = [tiles[empty], tiles[idx]];
        moves++;
        updateScore(1);
        // Check win
        let won = true;
        for (let i = 0; i < 15; i++) if (tiles[i] !== i + 1) won = false;
        if (tiles[15] !== 0) won = false;
        if (won) setTimeout(showGameOver, 300);
    }
    renderSliding();
}

function renderSliding() {
    const g = document.getElementById('gameGrid');
    g.innerHTML = '';
    document.getElementById('score').textContent = moves + ' moves';
    tiles.forEach((t, i) => {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.style.fontSize = '1.5em';
        cell.style.fontWeight = 'bold';
        if (t === 0) {
            cell.style.background = 'transparent';
        } else {
            cell.textContent = t;
            cell.style.background = '#3498db';
            cell.style.color = 'white';
            cell.onclick = () => clickTile(i);
        }
        g.appendChild(cell);
    });
}
''',
            render_code="renderSliding();",
            update_code="",
            input_handlers="",
        ))

        # ===== GUESS THE NUMBER =====
        self.register(GameConfig(
            id="guess_game",
            name="Guess the Number",
            render_type="custom",
            state={"target": 0, "guesses": 0, "message": "", "range": 100},
            loop_type="event",
            
            init_code='''
target = Math.floor(Math.random() * 100) + 1;
guesses = 0;
message = "Guess a number between 1 and 100";
range = 100;
renderGuess();
''',

            helpers='''
function makeGuess() {
    const input = document.getElementById('guessInput');
    const guess = parseInt(input.value);
    if (isNaN(guess) || guess < 1 || guess > 100) {
        message = "Please enter a number between 1 and 100";
        renderGuess();
        return;
    }
    guesses++;
    if (guess === target) {
        message = "🎉 Correct! You got it in " + guesses + " guesses!";
        updateScore(Math.max(10 - guesses, 1) * 10);
        setTimeout(showGameOver, 1000);
    } else if (guess < target) {
        message = "📈 Too low! Try higher.";
    } else {
        message = "📉 Too high! Try lower.";
    }
    input.value = '';
    renderGuess();
}

function renderGuess() {
    document.getElementById('gameArea').innerHTML = `
        <div style="text-align:center;padding:40px">
            <h2 style="margin-bottom:20px">${message}</h2>
            <p style="color:#888;margin-bottom:20px">Guesses: ${guesses}</p>
            <input type="number" id="guessInput" min="1" max="100" style="font-size:2em;width:100px;text-align:center;padding:10px">
            <button onclick="makeGuess()" style="font-size:1.5em;padding:15px 30px;margin-left:10px">Guess</button>
        </div>
    `;
    document.getElementById('guessInput').focus();
    document.getElementById('guessInput').onkeypress = (e) => { if (e.key === 'Enter') makeGuess(); };
}
''',
            render_code="renderGuess();",
            update_code="",
            input_handlers="",
        ))

        # ===== JIGSAW =====
        self.register(GameConfig(
            id="jigsaw",
            name="Jigsaw Puzzle",
            render_type="grid",
            grid_rows=3,
            grid_cols=3,
            state={"pieces": [], "selected": None, "solved": False},
            loop_type="event",
            
            init_code='''
// Create shuffled pieces with colors representing position
const colors = ['#e74c3c','#e67e22','#f1c40f','#2ecc71','#1abc9c','#3498db','#9b59b6','#34495e','#95a5a6'];
pieces = Array.from({length: 9}, (_, i) => ({id: i, color: colors[i]}));
// Shuffle
for (let i = pieces.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pieces[i], pieces[j]] = [pieces[j], pieces[i]];
}
selected = null;
solved = false;
renderJigsaw();
''',

            helpers='''
function clickPiece(idx) {
    if (solved) return;
    if (selected === null) {
        selected = idx;
    } else {
        [pieces[selected], pieces[idx]] = [pieces[idx], pieces[selected]];
        selected = null;
        // Check solved
        solved = pieces.every((p, i) => p.id === i);
        if (solved) {
            updateScore(100);
            setTimeout(showGameOver, 500);
        }
    }
    renderJigsaw();
}

function renderJigsaw() {
    const g = document.getElementById('gameGrid');
    g.innerHTML = '';
    pieces.forEach((p, i) => {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.style.background = p.color;
        cell.style.height = '100px';
        cell.textContent = p.id + 1;
        cell.style.fontSize = '2em';
        cell.style.color = 'white';
        if (selected === i) cell.style.border = '3px solid white';
        cell.onclick = () => clickPiece(i);
        g.appendChild(cell);
    });
}
''',
            render_code="renderJigsaw();",
            update_code="",
            input_handlers="",
        ))

        # ===== ALGORITHM VISUALIZER =====
        self.register(GameConfig(
            id="algorithm_visualizer",
            name="Algorithm Visualizer",
            render_type="canvas",
            canvas_width=600,
            canvas_height=400,
            state={"array": [], "sorting": False, "algorithm": "bubble"},
            loop_type="event",
            
            init_code='''
array = Array.from({length: 30}, () => Math.floor(Math.random() * 280) + 10);
sorting = false;
algorithm = "bubble";
render();
createControls();
''',

            helpers='''
async function bubbleSort() {
    for (let i = 0; i < array.length; i++) {
        for (let j = 0; j < array.length - i - 1; j++) {
            if (array[j] > array[j + 1]) {
                [array[j], array[j + 1]] = [array[j + 1], array[j]];
                render();
                await new Promise(r => setTimeout(r, 30));
            }
        }
    }
    sorting = false;
    updateScore(100);
}

async function selectionSort() {
    for (let i = 0; i < array.length; i++) {
        let min = i;
        for (let j = i + 1; j < array.length; j++) {
            if (array[j] < array[min]) min = j;
        }
        [array[i], array[min]] = [array[min], array[i]];
        render();
        await new Promise(r => setTimeout(r, 50));
    }
    sorting = false;
    updateScore(100);
}

function startSort() {
    if (sorting) return;
    sorting = true;
    if (algorithm === 'bubble') bubbleSort();
    else if (algorithm === 'selection') selectionSort();
}

function shuffle() {
    array = Array.from({length: 30}, () => Math.floor(Math.random() * 280) + 10);
    render();
}

function createControls() {
    const controls = document.createElement('div');
    controls.style.marginTop = '15px';
    controls.innerHTML = \`
        <select id="algoSelect" onchange="algorithm=this.value" style="padding:8px;margin-right:10px">
            <option value="bubble">Bubble Sort</option>
            <option value="selection">Selection Sort</option>
        </select>
        <button onclick="startSort()" style="padding:8px 16px">Sort</button>
        <button onclick="shuffle()" style="padding:8px 16px;margin-left:10px">Shuffle</button>
    \`;
    document.getElementById('gameContainer').appendChild(controls);
}
''',

            render_code='''
ctx.fillStyle = '#0f0f23';
ctx.fillRect(0, 0, canvas.width, canvas.height);
const barWidth = canvas.width / array.length - 2;
array.forEach((val, i) => {
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(i * (barWidth + 2), canvas.height - val, barWidth, val);
});
''',
            
            input_handlers="",
            click_enabled=False,
        ))


# Singleton instance
engine = GameEngine()


def generate_game(game_id: str, title: str, desc: str = "") -> str:
    """Generate a game using the component engine."""
    return engine.generate(game_id, title, desc)


# Quick test
if __name__ == "__main__":
    print("=== Game Engine Test ===")
    for gid in engine.configs:
        html = engine.generate(gid, f"{gid.title()} Game")
        print(f"  {gid}: {len(html)} chars")
    print("Done!")
