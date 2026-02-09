"""
Sliding Puzzle Game
A complete web-based puzzle game teaching:
- HTML structure
- CSS Grid layout  
- JavaScript arrays and DOM manipulation
- Game state management
- Event handling

Save this as puzzle.html and open in a browser!
"""

HTML_CODE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sliding Puzzle</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .game-container {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            text-align: center;
        }
        
        h1 {
            color: #333;
            margin-bottom: 16px;
        }
        
        .stats {
            display: flex;
            gap: 24px;
            justify-content: center;
            margin-bottom: 16px;
            color: #666;
        }
        
        .puzzle-grid {
            display: grid;
            grid-template-columns: repeat(4, 80px);
            grid-template-rows: repeat(4, 80px);
            gap: 4px;
            margin: 20px auto;
            background: #ddd;
            padding: 4px;
            border-radius: 8px;
        }
        
        .tile {
            background: #4a90d9;
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.15s, background 0.15s;
        }
        
        .tile:hover:not(.empty) {
            background: #357abd;
            transform: scale(0.95);
        }
        
        .tile.empty {
            background: transparent;
            cursor: default;
        }
        
        .controls {
            margin-top: 16px;
        }
        
        button.shuffle {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 32px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        button.shuffle:hover {
            background: #5a6fd6;
        }
        
        .win-message {
            color: #27ae60;
            font-size: 24px;
            font-weight: bold;
            margin-top: 16px;
            display: none;
        }
        
        .win-message.show {
            display: block;
            animation: bounce 0.5s ease;
        }
        
        @keyframes bounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🧩 Sliding Puzzle</h1>
        
        <div class="stats">
            <span>Moves: <strong id="moves">0</strong></span>
            <span>Time: <strong id="time">0:00</strong></span>
        </div>
        
        <div class="puzzle-grid" id="grid"></div>
        
        <div class="controls">
            <button class="shuffle" onclick="shuffle()">Shuffle</button>
        </div>
        
        <div class="win-message" id="win">🎉 You Win!</div>
    </div>

    <script>
        // Game State
        let tiles = [];
        let moves = 0;
        let timer = null;
        let seconds = 0;
        
        // Initialize solved state: [1,2,3,...,15,0]
        function initTiles() {
            tiles = [...Array(15).keys()].map(i => i + 1);
            tiles.push(0); // 0 = empty
        }
        
        // Find empty tile index
        function findEmpty() {
            return tiles.indexOf(0);
        }
        
        // Get valid moves (adjacent to empty)
        function getValidMoves() {
            const empty = findEmpty();
            const row = Math.floor(empty / 4);
            const col = empty % 4;
            const moves = [];
            
            if (row > 0) moves.push(empty - 4); // Up
            if (row < 3) moves.push(empty + 4); // Down
            if (col > 0) moves.push(empty - 1); // Left
            if (col < 3) moves.push(empty + 1); // Right
            
            return moves;
        }
        
        // Move tile at index if valid
        function moveTile(index) {
            const empty = findEmpty();
            const valid = getValidMoves();
            
            if (valid.includes(index)) {
                // Swap
                tiles[empty] = tiles[index];
                tiles[index] = 0;
                
                moves++;
                document.getElementById("moves").textContent = moves;
                
                render();
                checkWin();
                return true;
            }
            return false;
        }
        
        // Shuffle (make 100 random valid moves)
        function shuffle() {
            initTiles();
            for (let i = 0; i < 100; i++) {
                const valid = getValidMoves();
                const randomMove = valid[Math.floor(Math.random() * valid.length)];
                const empty = findEmpty();
                tiles[empty] = tiles[randomMove];
                tiles[randomMove] = 0;
            }
            
            moves = 0;
            seconds = 0;
            document.getElementById("moves").textContent = "0";
            document.getElementById("time").textContent = "0:00";
            document.getElementById("win").classList.remove("show");
            
            // Start timer
            if (timer) clearInterval(timer);
            timer = setInterval(() => {
                seconds++;
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                document.getElementById("time").textContent = 
                    mins + ":" + secs.toString().padStart(2, "0");
            }, 1000);
            
            render();
        }
        
        // Check for win
        function checkWin() {
            for (let i = 0; i < 15; i++) {
                if (tiles[i] !== i + 1) return false;
            }
            if (tiles[15] !== 0) return false;
            
            // Win!
            clearInterval(timer);
            document.getElementById("win").classList.add("show");
            return true;
        }
        
        // Render the grid
        function render() {
            const grid = document.getElementById("grid");
            grid.innerHTML = "";
            
            tiles.forEach((tile, index) => {
                const btn = document.createElement("button");
                btn.className = "tile" + (tile === 0 ? " empty" : "");
                btn.textContent = tile || "";
                btn.onclick = () => moveTile(index);
                grid.appendChild(btn);
            });
        }
        
        // Initialize
        initTiles();
        render();
    </script>
</body>
</html>
'''

def save_puzzle():
    """Save the puzzle game to an HTML file"""
    with open("puzzle.html", "w") as f:
        f.write(HTML_CODE)
    print("Saved puzzle.html - open in browser to play!")
    print("\nGame teaches:")
    print("  - HTML structure & semantic elements")
    print("  - CSS Grid for 2D layouts")
    print("  - JavaScript arrays & state management")
    print("  - DOM manipulation & event handling")
    print("  - Game logic & win detection")

if __name__ == "__main__":
    save_puzzle()
