"""Stress test App Forge with various game types."""
import sys
sys.path.insert(0, '.')
from template_registry import match_template
from codegen import generator

# Test categories
simple = [
    'a simple clicker game',
    'number guessing game',
    'coin flip simulator',
    'dice roller',
    'rock paper scissors',
]

variety = [
    'a snake game',
    'tetris clone',
    '2048 puzzle',
    'tic tac toe',
    'memory card matching',
    'wordle clone',
    'hangman game',
    'quiz trivia app',
    'reaction time tester',
    'typing speed test',
    'pong game',
    'cookie clicker idle game',
    'sudoku puzzle',
    'connect four',
    'blackjack card game',
    'flappy bird',
]

# Targeted accuracy tests (expected template)
targeted = [
    ('coin flip simulator', 'coin_flip'),
    ('dice roller', 'dice_roller'),
    ('rock paper scissors', 'rps'),
    ('2048 puzzle', 'game_2048'),
    ('typing speed test', 'typing_test'),
    ('typing test', 'typing_test'),
    ('pong game', 'pong'),
    ('cookie clicker', 'cookie_clicker'),
    ('sudoku', 'sudoku'),
    ('connect four', 'connect_four'),
    ('blackjack', 'blackjack'),
    ('flappy bird', 'flappy'),
]

complex_games = [
    'mario style platformer with coins and enemies',
    'space invaders shooter with waves',
    'breakout brick breaker with power ups',
    'rpg with inventory and stats',
    'tower defense game',
    'roguelike dungeon crawler',
    'multiplayer chess game',
    'pokemon style battle system',
]

edge_cases = [
    '',  # empty
    'game',  # too vague
    'fun app',  # meaningless
    'asdfghjkl',  # gibberish
    'a game but also a todo list',  # mixed intent
    'snake tetris 2048 combined',  # multiple games
    'calculater gamee',  # typos
    'platformer shooter breakout all in one',  # conflicting
]

def test_category(name, tests):
    print(f'\n=== {name} ===')
    passed = 0
    for desc in tests:
        try:
            tid, _, scores = match_template(desc if desc else 'generic app')
            html = generator.generate_index_html(desc if desc else 'generic', {}, desc if desc else 'generic')
            status = 'OK' if len(html) > 100 else 'WEAK'
            print(f'{status} [{tid:15}] ({len(html):5} chars) "{desc[:40]}"')
            if status == 'OK':
                passed += 1
        except Exception as e:
            print(f'FAIL "{desc[:40]}" -> {type(e).__name__}: {str(e)[:50]}')
    return passed, len(tests)

if __name__ == '__main__':
    total_passed = 0
    total_tests = 0
    
    # Targeted accuracy tests first
    print('\n=== TARGETED ACCURACY ===')
    for desc, expected in targeted:
        actual = match_template(desc)[0]
        status = 'OK' if actual == expected else 'MISS'
        print(f'{status}: Expected {expected:12} got {actual:15} <- "{desc}"')
        if status == 'OK':
            total_passed += 1
        total_tests += 1
    
    p, t = test_category('SIMPLE GAMES', simple)
    total_passed += p; total_tests += t
    
    p, t = test_category('VARIETY', variety)
    total_passed += p; total_tests += t
    
    p, t = test_category('COMPLEX GAMES', complex_games)
    total_passed += p; total_tests += t
    
    p, t = test_category('EDGE CASES', edge_cases)
    total_passed += p; total_tests += t
    
    print(f'\n=== SUMMARY ===')
    print(f'{total_passed}/{total_tests} tests passed')
