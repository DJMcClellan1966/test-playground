"""
Guess the Number Game
A beginner-friendly project to learn loops and conditionals
"""
import random

def play_game():
    """Main game loop"""
    number = random.randint(1, 100)
    attempts = 0
    
    print("🎮 Guess the Number!")
    print("I'm thinking of a number between 1 and 100.")
    
    while True:
        try:
            guess = int(input("\nEnter your guess: "))
            attempts += 1
            
            if guess < number:
                print("📉 Too low! Try higher.")
            elif guess > number:
                print("📈 Too high! Try lower.")
            else:
                print(f"\n🎉 Congratulations! You guessed it in {attempts} attempts!")
                break
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nThanks for playing!")
            break

if __name__ == "__main__":
    play_game()
