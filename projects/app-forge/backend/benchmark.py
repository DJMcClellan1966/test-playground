"""Benchmark: Old Templates vs New Game Engine"""
import time
import statistics
from game_engine import engine
import codegen

g = codegen.generator

# Games available in both systems
games = [
    ('snake', lambda: g._snake_html('Snake', 'snake'), lambda: engine.generate('snake', 'Snake')),
    ('pong', lambda: g._pong_html('Pong', 'pong'), lambda: engine.generate('pong', 'Pong')),
    ('tictactoe', lambda: g._tictactoe_html('TTT', 'ttt'), lambda: engine.generate('tictactoe', 'TTT')),
    ('memory', lambda: g._memory_game_html('Mem', 'mem'), lambda: engine.generate('memory', 'Memory')),
    ('flappy', lambda: g._flappy_html('Flap', 'flap'), lambda: engine.generate('flappy', 'Flappy')),
]

print('=' * 65)
print('PERFORMANCE COMPARISON: Old Templates vs New Engine')
print('=' * 65)

iterations = 100

results = []
for name, old_fn, new_fn in games:
    # Warm up
    old_fn(); new_fn()
    
    # Old timing
    old_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        html = old_fn()
        old_times.append(time.perf_counter() - start)
    old_avg = statistics.mean(old_times) * 1000
    old_size = len(html)
    
    # New timing
    new_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        html = new_fn()
        new_times.append(time.perf_counter() - start)
    new_avg = statistics.mean(new_times) * 1000
    new_size = len(html)
    
    speedup = old_avg / new_avg if new_avg > 0 else 1
    results.append((name, old_avg, new_avg, speedup, old_size, new_size))

print(f'\nGeneration Speed ({iterations} iterations each):')
print(f"{'Game':12} {'Old (ms)':>10} {'New (ms)':>10} {'Speedup':>10}")
print('-' * 45)
for name, old_t, new_t, speedup, _, _ in results:
    winner = 'OLD' if speedup < 1 else 'NEW'
    print(f'{name:12} {old_t:10.4f} {new_t:10.4f} {speedup:9.2f}x  <- {winner}')

avg_speedup = statistics.mean([r[3] for r in results])
print(f'\nAverage: {"New engine" if avg_speedup > 1 else "Old templates"} is {max(avg_speedup, 1/avg_speedup):.2f}x faster')

print(f'\n\nOutput Size (characters):')
print(f"{'Game':12} {'Old':>8} {'New':>8} {'Diff':>10}")
print('-' * 42)
total_old = total_new = 0
for name, _, _, _, old_s, new_s in results:
    diff = new_s - old_s
    pct = (diff / old_s) * 100 if old_s else 0
    print(f'{name:12} {old_s:>8} {new_s:>8} {diff:>+10} ({pct:+.0f}%)')
    total_old += old_s
    total_new += new_s

print('-' * 42)
print(f"{'TOTAL':12} {total_old:>8} {total_new:>8} {total_new-total_old:>+10}")

# Test functional equivalence
print('\n\nFunctional Check:')
print('-' * 42)
checks = [
    'init()',
    'gameOver',
    'score',
    'restart',
    'addEventListener',
]
for name, old_fn, new_fn in games:
    old_html = old_fn()
    new_html = new_fn()
    passes = sum(1 for c in checks if c in new_html)
    print(f'{name:12} {passes}/{len(checks)} core features present')
