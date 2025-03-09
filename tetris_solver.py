import numpy as np
import random
import time

# Tetris Constants
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
LINE_CLEAR_POINTS = {
    1: 100,   # Single line
    2: 300,   # Double
    3: 500,   # Triple
    4: 800    # Tetris
}

def get_rotations(piece):
    """Return a list of unique rotations for the given tetromino piece."""
    rotations = []
    for i in range(4):
        rotated = np.rot90(piece, i)
        # Check for duplicate rotations
        if not any(np.array_equal(rotated, r) for r in rotations):
            rotations.append(rotated)
    return rotations

# Define tetromino base shapes
BASE_TETROMINOS = {
    'I': np.array([[1, 1, 1, 1]]),
    'O': np.array([[1, 1],
                   [1, 1]]),
    'T': np.array([[0, 1, 0],
                   [1, 1, 1]]),
    'L': np.array([[0, 0, 1],
                   [1, 1, 1]]),
    'J': np.array([[1, 0, 0],
                   [1, 1, 1]]),
    'S': np.array([[0, 1, 1],
                   [1, 1, 0]]),
    'Z': np.array([[1, 1, 0],
                   [0, 1, 1]])
}

# Precompute all rotations for each tetromino
TETROMINOS = { k: get_rotations(shape) for k, shape in BASE_TETROMINOS.items() }

class TetrisSolver:
    def __init__(self):
        self.board = np.zeros((BOARD_HEIGHT, BOARD_WIDTH), dtype=int)
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
    
    def can_place(self, piece, x, y):
        """Checks if a piece can be placed at (x, y) without collision."""
        piece_h, piece_w = piece.shape
        # Check horizontal bounds
        if y < 0 or y + piece_w > BOARD_WIDTH:
            return False
        # Check vertical bounds
        if x + piece_h > BOARD_HEIGHT:
            return False
        
        for i in range(piece_h):
            for j in range(piece_w):
                if piece[i, j] == 1:
                    if self.board[x + i, y + j] == 1:
                        return False
        return True
    
    def place_piece(self, piece, x, y):
        """Places a piece on the board."""
        if not self.can_place(piece, x, y):
            return False
        piece_h, piece_w = piece.shape
        for i in range(piece_h):
            for j in range(piece_w):
                if piece[i, j] == 1:
                    self.board[x + i, y + j] = 1
        return True
    
    def clear_lines(self):
        """Clears completed lines and returns the number of lines cleared."""
        full_rows = np.all(self.board == 1, axis=1)
        num_cleared = np.sum(full_rows)
        if num_cleared > 0:
            new_board = np.zeros_like(self.board)
            new_idx = BOARD_HEIGHT - 1
            for idx in range(BOARD_HEIGHT - 1, -1, -1):
                if not full_rows[idx]:
                    new_board[new_idx] = self.board[idx]
                    new_idx -= 1
            self.board = new_board
            self.lines_cleared += num_cleared
            self.level = max(1, self.lines_cleared // 10 + 1)
            if 1 <= num_cleared <= 4:
                points = LINE_CLEAR_POINTS[num_cleared] * self.level
                self.score += points
                print(f"Cleared {num_cleared} lines! +{points} points")
            else:
                points = 1000 * self.level * num_cleared // 4
                self.score += points
                print(f"Cleared {num_cleared} lines! +{points} points")
        return num_cleared
    
    def evaluate_board(self):
        """Evaluates board state based on features such as holes and bumpiness."""
        full_rows = np.all(self.board == 1, axis=1)
        lines_cleared = np.sum(full_rows)
        
        column_heights = []
        holes = 0
        for col in range(BOARD_WIDTH):
            filled = np.where(self.board[:, col] == 1)[0]
            if filled.size > 0:
                height = BOARD_HEIGHT - filled[0]
                column_heights.append(height)
                holes += sum(1 for row in range(filled[0]+1, BOARD_HEIGHT) if self.board[row, col] == 0)
            else:
                column_heights.append(0)
        bumpiness = sum(abs(column_heights[i] - column_heights[i+1]) for i in range(len(column_heights)-1))
        agg_height = sum(column_heights)
        
        # Combine features into an evaluation score
        return (
            lines_cleared * 500 +
            (4 - lines_cleared) * -50 +
            holes * -50 +
            bumpiness * -10 +
            agg_height * -1
        )
    
    def best_move(self, rotations):
        """
        Finds the best move for the tetromino by considering every unique rotation and every valid column.
        Returns (best_x, best_y, rotation_index) and its evaluation score.
        """
        best_score = -np.inf
        best_move = None
        for r_idx, piece in enumerate(rotations):
            piece_h, piece_w = piece.shape
            for y in range(0, BOARD_WIDTH - piece_w + 1):
                x = 0
                if not self.can_place(piece, x, y):
                    continue
                # Drop piece using gravity
                while self.can_place(piece, x + 1, y):
                    x += 1
                # Evaluate the board after placing piece at (x,y)
                backup_board = self.board.copy()
                self.place_piece(piece, x, y)
                score = self.evaluate_board()
                self.board = backup_board  # Undo move
                if score > best_score:
                    best_score = score
                    best_move = (x, y, r_idx)
        return best_move, best_score
    
    def drop_piece(self, piece, y_pos):
        """Drops a piece from the top to the lowest valid position at y_pos."""
        x = 0
        while self.can_place(piece, x + 1, y_pos):
            x += 1
        return self.place_piece(piece, x, y_pos)
    
    def print_board(self):
        """Prints the current state of the board."""
        print("\nCurrent Board:")
        print("+" + "-" * BOARD_WIDTH + "+")
        for row in self.board:
            line = "|" + "".join("█" if cell else " " for cell in row) + "|"
            print(line)
        print("+" + "-" * BOARD_WIDTH + "+")
    
    def print_board_with_piece(self, piece, x, y):
        """Prints the board with a piece overlaid at position (x,y)."""
        if not self.can_place(piece, x, y):
            print("Cannot place piece at this position!")
            return
        vis_board = self.board.copy()
        piece_h, piece_w = piece.shape
        for i in range(piece_h):
            for j in range(piece_w):
                if piece[i, j] == 1:
                    vis_board[x + i, y + j] = 2  # Mark the piece cells with a 2
        print("\nBoard with Piece (█ = Board, ▒ = Piece):")
        print("+" + "-" * BOARD_WIDTH + "+")
        for row in vis_board:
            line = "|" + "".join("█" if cell == 1 else ("▒" if cell == 2 else " ") for cell in row) + "|"
            print(line)
        print("+" + "-" * BOARD_WIDTH + "+")
    
    def print_game_info(self):
        """Prints current game information."""
        print(f"\nScore: {self.score} | Lines: {self.lines_cleared} | Level: {self.level}")
    
    def game_over(self):
        """Checks if the game is over (i.e. no piece can be placed at the top row for any rotation)."""
        for rotations in TETROMINOS.values():
            for piece in rotations:
                for y in range(BOARD_WIDTH - piece.shape[1] + 1):
                    if self.can_place(piece, 0, y):
                        return False
        return True

def run_game(max_turns=100, delay=0.5):
    """Runs the Tetris game simulation for a specified number of turns."""
    solver = TetrisSolver()
    piece_types = list(TETROMINOS.keys())
    turn = 0
    
    print("Starting Tetris Solver Game...")
    print("Each piece will be automatically placed in its optimal drop position.")
    solver.print_game_info()
    solver.print_board()
    
    while turn < max_turns and not solver.game_over():
        # Select random piece type
        piece_type = random.choice(piece_types)
        rotations = TETROMINOS[piece_type]
        print(f"\n--- Turn {turn + 1} ---")
        print(f"Next Piece: {piece_type}")
        
        best_move_info, eval_score = solver.best_move(rotations)
        if best_move_info:
            best_x, best_y, best_r_idx = best_move_info
            chosen_piece = rotations[best_r_idx]
            print(f"Best Position: {(best_x, best_y)} with rotation index {best_r_idx} (Eval: {eval_score})")
            solver.print_board_with_piece(chosen_piece, best_x, best_y)
            solver.place_piece(chosen_piece, best_x, best_y)
            solver.clear_lines()
            solver.score += 10  # Bonus for placing a piece
            solver.print_game_info()
            solver.print_board()
            turn += 1
            time.sleep(delay)
        else:
            print("Game Over! No valid moves available.")
            break
    
    if solver.game_over():
        print("\nGame Over! No more valid moves.")
    elif turn >= max_turns:
        print(f"\nReached maximum turns ({max_turns}).")
    
    print("\nFinal Results:")
    solver.print_game_info()
    solver.print_board()
    print("Thank you for playing!")

if __name__ == "__main__":
    run_game(max_turns=10000, delay=0)
