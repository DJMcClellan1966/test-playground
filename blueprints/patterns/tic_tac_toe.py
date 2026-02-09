"""
Tic-Tac-Toe Game
Learn 2D arrays and game logic
"""

def print_board(board):
    """Display the game board"""
    print()
    for i, row in enumerate(board):
        print(f"  {row[0]} | {row[1]} | {row[2]}")
        if i < 2:
            print(" ---|---|---")
    print()

def check_winner(board):
    """Check if there's a winner"""
    # Rows
    for row in board:
        if row[0] == row[1] == row[2] != ' ':
            return row[0]
    
    # Columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != ' ':
            return board[0][col]
    
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]
    
    return None

def is_full(board):
    """Check if board is full"""
    return all(cell != ' ' for row in board for cell in row)

def play_game():
    """Main game loop"""
    board = [[' ' for _ in range(3)] for _ in range(3)]
    current = 'X'
    
    print("🎮 Tic-Tac-Toe")
    print("Enter position as row,col (0-2)")
    print("Example: 1,1 for center")
    
    while True:
        print_board(board)
        print(f"Player {current}'s turn")
        
        try:
            move = input("Enter row,col: ")
            row, col = map(int, move.split(','))
            
            if not (0 <= row <= 2 and 0 <= col <= 2):
                print("Position must be 0-2!")
                continue
            
            if board[row][col] != ' ':
                print("Cell already taken!")
                continue
            
            board[row][col] = current
            
            winner = check_winner(board)
            if winner:
                print_board(board)
                print(f"🎉 Player {winner} wins!")
                break
            
            if is_full(board):
                print_board(board)
                print("🤝 It's a tie!")
                break
            
            current = 'O' if current == 'X' else 'X'
            
        except (ValueError, IndexError):
            print("Invalid input! Use format: row,col")
        except KeyboardInterrupt:
            print("\nGame ended.")
            break

if __name__ == "__main__":
    play_game()
