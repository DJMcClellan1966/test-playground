"""
Universal Reasoning Kernel - Interactive Demo
=============================================
Demonstrates the kernel's capabilities through practical examples.
"""

from kernel import (
    UniversalKernel, create_kernel,
    PatternRecognizer, BayesianReasoner, ConstraintPropagator,
    MemorySystem, CompositionalGenerator, Template,
    entropy, information_gain, compression_distance, softmax
)


def demo_intelligent_assistant():
    """Demo: Build an intelligent assistant that learns"""
    print("\n" + "="*60)
    print("DEMO 1: Intelligent Learning Assistant")
    print("="*60)
    
    kernel = create_kernel("Assistant")
    
    # Teach it some facts
    knowledge = [
        "Python is a programming language",
        "Flask is a Python web framework",
        "SQLite is a database",
        "REST APIs use HTTP methods",
        "JSON is a data format",
    ]
    
    print("\n--- Teaching Knowledge ---")
    for fact in knowledge:
        kernel.learn(fact)
        print(f"Learned: {fact}")
    
    # Ask questions
    print("\n--- Question Answering ---")
    questions = [
        "What is Python?",
        "Tell me about Flask",
        "What database should I use?",
    ]
    
    for q in questions:
        answer = kernel.ask(q)
        print(f"Q: {q}")
        print(f"A: {answer}\n")
    
    # Interactive conversation
    print("--- Conversation ---")
    conversation = [
        "Django is also a Python framework",
        "I prefer Flask for small projects",
        "What frameworks do you know about?",
    ]
    
    for msg in conversation:
        result = kernel.process(msg)
        print(f"User: {msg}")
        print(f"URK:  {result['response']}")
        print(f"      (Confidence: {result['confidence']:.0%})\n")


def demo_problem_solver():
    """Demo: Constraint-based problem solving"""
    print("\n" + "="*60)
    print("DEMO 2: Constraint-Based Problem Solving")
    print("="*60)
    
    # Classic: Map Coloring Problem
    print("\n--- Map Coloring (Australia) ---")
    csp = ConstraintPropagator()
    
    regions = ['WA', 'NT', 'SA', 'Q', 'NSW', 'V', 'T']
    colors = ['red', 'green', 'blue']
    
    for region in regions:
        csp.add_variable(region, colors)
    
    # Adjacent regions must have different colors
    adjacent = [
        ('WA', 'NT'), ('WA', 'SA'), ('NT', 'SA'), ('NT', 'Q'),
        ('SA', 'Q'), ('SA', 'NSW'), ('SA', 'V'), ('Q', 'NSW'), ('NSW', 'V')
    ]
    
    for r1, r2 in adjacent:
        csp.add_constraint([r1, r2], lambda a, b: a != b, f"{r1} ≠ {r2}")
    
    solution = csp.solve()
    print(f"Solution: {solution}")
    
    # Verify solution
    valid = all(solution[r1] != solution[r2] for r1, r2 in adjacent)
    print(f"Valid coloring: {valid}")
    
    # Sudoku-like puzzle (4x4)
    print("\n--- Mini Sudoku (4x4) ---")
    csp2 = ConstraintPropagator()
    
    # 4x4 grid, values 1-4
    for r in range(4):
        for c in range(4):
            csp2.add_variable(f"c{r}{c}", [1, 2, 3, 4])
    
    # Row constraints
    for r in range(4):
        for c1 in range(4):
            for c2 in range(c1+1, 4):
                csp2.add_constraint([f"c{r}{c1}", f"c{r}{c2}"], 
                    lambda a, b: a != b, f"row{r}")
    
    # Column constraints
    for c in range(4):
        for r1 in range(4):
            for r2 in range(r1+1, 4):
                csp2.add_constraint([f"c{r1}{c}", f"c{r2}{c}"], 
                    lambda a, b: a != b, f"col{c}")
    
    # Pre-fill some values (simulate given puzzle)
    csp2.variables['c00'].domain = {1}
    csp2.variables['c11'].domain = {2}
    csp2.variables['c22'].domain = {3}
    csp2.variables['c33'].domain = {4}
    
    solution2 = csp2.solve()
    if solution2:
        print("Solution:")
        for r in range(4):
            row = [solution2[f"c{r}{c}"] for c in range(4)]
            print(f"  {row}")


def demo_bayesian_diagnosis():
    """Demo: Bayesian reasoning for diagnosis"""
    print("\n" + "="*60)
    print("DEMO 3: Bayesian Diagnostic Reasoning")
    print("="*60)
    
    bayes = BayesianReasoner()
    
    # Medical-ish diagnosis (simplified)
    print("\n--- Symptom-Based Diagnosis ---")
    
    # Conditions and priors
    conditions = {
        'cold': 0.3,
        'flu': 0.1,
        'allergy': 0.2,
        'covid': 0.05,
    }
    
    for cond, prior in conditions.items():
        bayes.add_belief(cond, prior)
    
    # Observe symptoms
    print("Symptoms observed:")
    symptoms = [
        ("fever", ["flu", "covid"]),
        ("runny nose", ["cold", "allergy"]),
        ("fatigue", ["flu", "covid", "cold"]),
    ]
    
    for symptom, supports in symptoms:
        print(f"  + {symptom}")
        bayes.observe(symptom, supports=supports)
    
    print("\nDiagnosis probabilities:")
    results = [(cond, bayes.query(cond)) for cond in conditions]
    results.sort(key=lambda x: x[1][0], reverse=True)
    for cond, (prob, conf) in results:
        print(f"  {cond}: {prob:.0%} (confidence: {conf:.0%})")
    
    print("\nMost uncertain:", bayes.most_uncertain())


def demo_pattern_learning():
    """Demo: Learning patterns from examples"""
    print("\n" + "="*60)
    print("DEMO 4: Pattern Learning from Examples")
    print("="*60)
    
    recognizer = PatternRecognizer()
    
    # Learn email pattern
    print("\n--- Learning Email Pattern ---")
    email_examples = [
        "contact@example.com",
        "user.name@company.org",
        "support@service.net",
    ]
    recognizer.learn_pattern('email', email_examples, {'communication', 'identifier'})
    print(f"Learned from {len(email_examples)} examples")
    
    # Test recognition
    tests = [
        "Send to info@test.com",
        "My email is fake",
        "Contact support@help.org for assistance",
    ]
    print("\nRecognition tests:")
    for test in tests:
        matches = recognizer.recognize(test)
        print(f"  '{test}'")
        if matches:
            print(f"    → {matches[0][0]} (score: {matches[0][1]:.2f})")
        else:
            print(f"    → No pattern matched")


def demo_analogy():
    """Demo: Analogical reasoning"""
    print("\n" + "="*60)
    print("DEMO 5: Analogical Reasoning")
    print("="*60)
    
    kernel = create_kernel()
    
    analogies = [
        ("cat", "cats", "dog"),
        ("walk", "walked", "talk"),
        ("small", "smaller", "big"),
        ("hot", "cold", "up"),
        ("king", "queen", "prince"),
        ("Paris", "France", "Berlin"),
    ]
    
    print("\nAnalogy completion (A:B :: C:?):")
    for a, b, c in analogies:
        result = kernel.analogy(a, b, c)
        print(f"  {result}")


def demo_memory():
    """Demo: Memory system with association"""
    print("\n" + "="*60)
    print("DEMO 6: Memory System with Spreading Activation")
    print("="*60)
    
    mem = MemorySystem()
    
    # Store semantic memories with associations
    print("\n--- Storing Knowledge Graph ---")
    mem.store_semantic('dog', 'canine mammal', {'animal', 'pet', 'mammal'})
    mem.store_semantic('cat', 'feline mammal', {'animal', 'pet', 'mammal'})
    mem.store_semantic('mammal', 'warm-blooded vertebrate', {'animal', 'biology'})
    mem.store_semantic('pet', 'domesticated animal', {'animal', 'companion'})
    mem.store_semantic('animal', 'living organism', {'biology', 'life'})
    
    # Link associations
    mem.associate('dog', {'mammal', 'pet'})
    mem.associate('cat', {'mammal', 'pet'})
    
    print("Stored: dog, cat, mammal, pet, animal with associations")
    
    # Search
    print("\n--- Semantic Search ---")
    results = mem.search('furry pet')
    for r_id, content, sim in results:
        print(f"  [{r_id}] {content} (similarity: {sim:.2f})")
    
    # Spreading activation
    print("\n--- Spreading Activation from 'dog' ---")
    activated = mem.spread_activation('dog', depth=2)
    for node, strength in activated[:5]:
        print(f"  {node}: activation={strength:.2f}")


def demo_information_theory():
    """Demo: Information theory applications"""
    print("\n" + "="*60)
    print("DEMO 7: Information Theory")
    print("="*60)
    
    # Entropy and uncertainty
    print("\n--- Entropy (Uncertainty) ---")
    scenarios = [
        ("Fair coin", [0.5, 0.5]),
        ("Biased coin (90/10)", [0.9, 0.1]),
        ("Fair die", [1/6]*6),
        ("Loaded die", [0.4, 0.2, 0.15, 0.1, 0.1, 0.05]),
    ]
    
    for name, probs in scenarios:
        H = entropy(probs)
        max_H = entropy([1/len(probs)]*len(probs))
        print(f"  {name}: H={H:.3f} bits (max possible: {max_H:.3f})")
    
    # Compression distance
    print("\n--- Compression Distance (Similarity) ---")
    strings = [
        ("hello world", "hello world"),  # identical
        ("hello world", "hello there"),  # similar
        ("hello world", "goodbye world"),  # somewhat similar
        ("hello world", "xyzzy plugh"),  # different
        ("aaaaaaaaaa", "bbbbbbbbbb"),  # structurally similar
    ]
    
    for a, b in strings:
        dist = compression_distance(a, b)
        print(f"  '{a}' vs '{b}': {1-dist:.2%} similar")
    
    # Softmax for decision making
    print("\n--- Softmax (Decision Making) ---")
    scores = [3.0, 1.0, 0.5, 0.2]
    options = ['Option A', 'Option B', 'Option C', 'Option D']
    
    for temp in [1.0, 0.5, 2.0]:
        probs = softmax(scores, temperature=temp)
        print(f"  Temperature={temp}:")
        for opt, prob in zip(options, probs):
            print(f"    {opt}: {prob:.1%}")


def demo_generator():
    """Demo: Compositional generation"""
    print("\n" + "="*60)
    print("DEMO 8: Compositional Generation")
    print("="*60)
    
    gen = CompositionalGenerator()
    
    # Add templates
    print("\n--- Template-Based Generation ---")
    gen.add_template(Template(
        id='greeting',
        pattern='Hello, {NAME}! Welcome to {PLACE}.',
        slots={
            'NAME': ['friend', 'user', 'developer', 'visitor'],
            'PLACE': ['our app', 'the system', 'URK', 'the future']
        }
    ))
    
    gen.add_template(Template(
        id='error',
        pattern='Error: {ERROR_TYPE} - {SUGGESTION}',
        slots={
            'ERROR_TYPE': ['Invalid input', 'Not found', 'Timeout'],
            'SUGGESTION': ['Please try again', 'Check your connection', 'Contact support']
        }
    ))
    
    for _ in range(3):
        print(f"  {gen.generate_from_template('greeting')}")
    
    # Grammar-based generation
    print("\n--- Grammar-Based Generation ---")
    gen.add_grammar_rule('S', ['<NP> <VP>'])
    gen.add_grammar_rule('NP', ['the <N>', 'a <ADJ> <N>'])
    gen.add_grammar_rule('VP', ['<V> <NP>', '<V>'])
    gen.add_grammar_rule('N', ['cat', 'dog', 'robot', 'programmer'])
    gen.add_grammar_rule('V', ['runs', 'sees', 'creates', 'debugs'])
    gen.add_grammar_rule('ADJ', ['clever', 'fast', 'blue', 'happy'])
    
    for _ in range(5):
        print(f"  {gen.generate_from_grammar('S')}")


def demo_full_system():
    """Demo: Full system integration"""
    print("\n" + "="*60)
    print("DEMO 9: Full System Integration")
    print("="*60)
    
    kernel = create_kernel("FullDemo")
    
    print("\n--- Interactive Session ---")
    
    interactions = [
        # Learning phase
        "Python was created by Guido van Rossum",
        "JavaScript runs in browsers",
        "Rust is a systems programming language",
        
        # Query phase
        "What programming languages do you know?",
        "Who created Python?",
        
        # Command phase
        "Calculate 42 + 17",
        "Remember this: My favorite color is blue",
        
        # Recall
        "What is my favorite color?",
    ]
    
    for msg in interactions:
        result = kernel.process(msg)
        print(f"\nUser: {msg}")
        print(f"URK:  {result['response']}")
        if result['patterns']:
            print(f"      Pattern: {result['patterns'][0][0]}")
        if result['entities']:
            print(f"      Entities: {result['entities'][:3]}")
    
    # Save and explain
    print("\n--- Knowledge Summary ---")
    print(kernel.explain("programming"))


def run_all_demos():
    """Run all demos"""
    demos = [
        demo_intelligent_assistant,
        demo_problem_solver,
        demo_bayesian_diagnosis,
        demo_pattern_learning,
        demo_analogy,
        demo_memory,
        demo_information_theory,
        demo_generator,
        demo_full_system,
    ]
    
    for demo in demos:
        demo()
    
    print("\n" + "="*60)
    print("All demos complete!")
    print("="*60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        demo_num = sys.argv[1]
        demos = {
            '1': demo_intelligent_assistant,
            '2': demo_problem_solver,
            '3': demo_bayesian_diagnosis,
            '4': demo_pattern_learning,
            '5': demo_analogy,
            '6': demo_memory,
            '7': demo_information_theory,
            '8': demo_generator,
            '9': demo_full_system,
        }
        if demo_num in demos:
            demos[demo_num]()
        else:
            print("Usage: python demo.py [1-9 | all]")
    else:
        run_all_demos()
