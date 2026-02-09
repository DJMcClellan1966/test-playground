"""
Simple Calculator
Learn functions and error handling
"""

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Division by zero!"
    return a / b

def calculator():
    """Interactive calculator"""
    operations = {
        '+': add,
        '-': subtract,
        '*': multiply,
        '/': divide
    }
    
    print("🧮 Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            expr = input("\nEnter expression (e.g., 5 + 3): ").strip()
            if expr.lower() == 'quit':
                break
            
            # Parse expression
            parts = expr.split()
            if len(parts) != 3:
                print("Format: number operator number")
                continue
            
            a, op, b = float(parts[0]), parts[1], float(parts[2])
            
            if op in operations:
                result = operations[op](a, b)
                print(f"Result: {result}")
            else:
                print(f"Unknown operator: {op}")
                
        except ValueError:
            print("Invalid numbers!")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    calculator()
