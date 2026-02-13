import sys
import json
from imagination import creative_system
from template_registry import match_template, explain_match
from solver import solver  # Import the ConstraintSolver singleton

# Step 1: Generate app ideas
ideas = [
    "a recipe collection app",
    "a workout tracker with progress graphs",
    "a flashcard study app",
    "a collaborative whiteboard tool",
    "a personal finance tracker",
]

results = []

for idea in ideas:
    print(f"\n--- Exploring Idea: {idea} ---")

    # Step 2: Match templates
    best_id, features, scores = match_template(idea)
    print(f"Best Template: {best_id}")
    print(f"Features: {list(features.keys())}")
    print(f"Top 3 Scores: {scores[:3]}")

    # Step 3: Explain match
    explanation = explain_match(idea)
    print("Explanation:")
    print(explanation)

    # Step 4: Solve constraints (if applicable)
    constraints = {"has_data": True, "needs_auth": True}  # Example constraints
    solved = solver.solve(constraints, idea)  # Use the solver instance
    print("Constraint Solver Result:")
    print(solved.to_dict())  # Convert the result to a dictionary for display

    # Collect results
    results.append({
        "idea": idea,
        "best_template": best_id,
        "features": list(features.keys()),
        "top_scores": scores[:3],
        "explanation": explanation,
        "constraints_solved": solved.to_dict(),
    })

# Save results to a file
with open("exploration_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nExploration complete. Results saved to exploration_results.json.")