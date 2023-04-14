import numpy as np
import copy
import random


row_count = 6
column_count = 7

infinity = float('inf')


class Connect4():
    markers = ["⚪", "🔴", "⚫"]

    display_template = (
        "``` --------------------------------------"
        "\n| 35 | 36 | 37 | 38 | 39 | 40 | 41 |"
        "\n --------------------------------------"
        "\n| 28 | 29 | 30 | 31 | 32 | 33 | 34 |"
        "\n --------------------------------------"
        "\n| 21 | 22 | 23 | 24 | 25 | 26 | 27 |"
        "\n --------------------------------------"
        "\n| 14 | 15 | 16 | 17 | 18 | 19 | 20 |"
        "\n --------------------------------------"
        "\n| 7 | 8 | 9 | 10 | 11 | 12 | 13 |"
        "\n --------------------------------------"
        "\n| 0 | 1 | 2 | 3 | 4 | 5 | 6 | "
        "\n --------------------------------------```"
    )

    def __init__(self):
        self.board = np.zeros((row_count, column_count))
        self.available_columns = list(range(0, column_count))

    def draw_board(self) -> str:
        board_display = self.display_template
        for i in range(42):
            value = int(self.board[i//7][i%7])
            marker = self.markers[value]
            board_display = board_display.replace(f" {i} ", f" {marker} ")

        return board_display

    def update_board(self, board: np.ndarray, column: int, piece: int, simulation: bool=False) -> bool:
        for row in range(len(board)):
            if board[row][column] == 0:
                board[row][column] = piece

                # Column will be removed from UI
                if not simulation and row == len(board) - 1:
                    self.available_columns.remove(column)
                
                break

    @staticmethod
    def check_winner(board: np.ndarray, piece: int) -> bool:
        # Check horizontal win
        for c in range(column_count - 3):
            for r in range(row_count):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
            
        # Check vertical win
        for c in range(column_count):
            for r in range(row_count - 3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
                
        # Check / win
        for c in range(column_count - 3):
            for r in range(row_count - 3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
                
        # Check \ win
        for c in range(column_count - 3):
            for r in range(3, row_count):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True


class Solver(Connect4):
    def __init__(self):
        self.piece = int()
        self.opponent_piece = int()

        super().__init__()

    @staticmethod
    def get_valid_columns(board: np.ndarray) -> list:
        valid = list()
        for col in range(len(board[-1])):
            if board[-1][col] == 0:
                valid.append(col)
        return valid

    def evaluate_window(self, window: list, piece: int) -> float:
        score = 0

        # Switch scoring based on turn
        opp_piece = self.opponent_piece
        if piece == self.opponent_piece:
            opp_piece = self.piece

        # Prioritise a winning move
        # Minimax makes this less important
        if window.count(piece) == 4:
            score += 100
        # Make connecting 3 second priority
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        # Make connecting 2 third priority
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        # Prioritise blocking an opponent's winning move (but not over bot winning)
        # Minimax makes this less important
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4

        return score

    def score_position(self, board: np.ndarray, piece: int) -> float:
        score = 0

        # Score centre column
        center_array = [int(i) for i in list(board[:, column_count // 2])]
        center_count = center_array.count(piece)
        score += center_count * 3

        # Score horizontal positions
        for r in range(row_count):
            row_array = [int(i) for i in list(board[r, :])]
            for c in range(column_count - 3):
                # Create a horizontal window of 4
                window = row_array[c:c + 4]
                score += self.evaluate_window(window, piece)

        # Score vertical positions
        for c in range(column_count):
            col_array = [int(i) for i in list(board[:, c])]
            for r in range(row_count - 3):
                # Create a vertical window of 4
                window = col_array[r:r + 4]
                score += self.evaluate_window(window, piece)

        # Score positive diagonals
        for r in range(row_count - 3):
            for c in range(column_count - 3):
                # Create a positive diagonal window of 4
                window = [board[r + i][c + i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        # Score negative diagonals
        for r in range(row_count - 3):
            for c in range(column_count - 3):
                # Create a negative diagonal window of 4
                window = [board[r + 3 - i][c + i] for i in range(4)]
                score += self.evaluate_window(window, piece)

        return score

    def is_terminal_node(self, board: np.ndarray) -> bool:
        return self.check_winner(board, self.opponent_piece) or self.check_winner(board, self.piece) or not any(0 in row for row in board)

    def minimax(self, board: np.array, depth: int, alpha: float, beta: float, is_maximizing: bool) -> tuple[int, float]:
        valid_locations = self.get_valid_columns(board)

        is_terminal = self.is_terminal_node(board)
        if depth == 0 or is_terminal:
            if is_terminal:
                # Weight winning really high
                if self.check_winner(board, self.piece):
                    return (None, infinity)
                # Weight the opponent winning really low
                elif self.check_winner(board, self.opponent_piece):
                    return (None, -infinity)
                else:  # No more valid moves
                    return (None, 0)
            # Return the bot's score
            else:
                return (None, self.score_position(board, self.piece))

        if is_maximizing:
            value = -infinity
            # Randomise column to start
            column = random.choice(valid_locations)
            for col in valid_locations:
                # Create a copy of the board
                board_copy = board.copy()
                # Drop a piece in the temporary board and record score
                self.update_board(board_copy, col, self.piece, simulation=True)
                new_score = self.minimax(board_copy, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    # Make 'column' the best scoring column we can get
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else:  # Minimising player
            value = infinity
            # Randomise column to start
            column = random.choice(valid_locations)
            for col in valid_locations:
                # Create a copy of the board
                board_copy = board.copy()
                # Drop a piece in the temporary board and record score
                self.update_board(board_copy, col, self.opponent_piece, simulation=True)
                new_score = self.minimax(board_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    # Make 'column' the best scoring column we can get
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
        
    def find_solution(self, game: Connect4, piece: int, depth: int) -> tuple[int, float]:
        board = copy.copy(game.board)

        self.piece = piece
        self.opponent_piece = int(2 / piece)

        return self.minimax(board, depth, -infinity, infinity, True)
