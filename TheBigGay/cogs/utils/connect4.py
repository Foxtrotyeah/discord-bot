import numpy as np

class Connect4():
    markers = ["⚪", "🔴", "⚫"]

    row_size = 6
    column_size = 7

    display_template = (
        "``` -----------------------------------"
        "\n| 35 | 36 | 37 | 38 | 39 | 40 | 41 |"
        "\n -----------------------------------"
        "\n| 28 | 29 | 30 | 31 | 32 | 33 | 34 |"
        "\n -----------------------------------"
        "\n| 21 | 22 | 23 | 24 | 25 | 26 | 27 |"
        "\n -----------------------------------"
        "\n| 14 | 15 | 16 | 17 | 18 | 19 | 20 |"
        "\n -----------------------------------"
        "\n| 7 | 8 | 9 | 10 | 11 | 12 | 13 |"
        "\n -----------------------------------"
        "\n| 0 | 1 | 2 | 3 | 4 | 5 | 6 | "
        "\n -----------------------------------```"
    )

    def __init__(self):
        self.board = np.zeros((self.row_size, self.column_size))

    def draw_board(self) -> str:
        board_display = self.display_template
        for i in range(42):
            value = int(self.board[i//7][i%7])
            marker = self.markers[value]
            board_display = board_display.replace(f" {i} ", f" {marker} ")

        return board_display

    def update_board(self, column: int, value: int) -> bool:
        for row in range(len(self.board)):
            if self.board[row][column] == 0:
                self.board[row][column] = value

                if row == len(self.board) - 1:
                    return True
                
                break

    def check_winner(self, value: int) -> bool:
        # Check horizontal win
        for c in range(self.column_size - 3):
            for r in range(self.row_size):
                if self.board[r][c] == value and self.board[r][c+1] == value and self.board[r][c+2] == value and self.board[r][c+3] == value:
                    return True
            
        # Check vertical win
        for c in range(self.column_size):
            for r in range(self.row_size - 3):
                if self.board[r][c] == value and self.board[r+1][c] == value and self.board[r+2][c] == value and self.board[r+3][c] == value:
                    return True
                
        # Check / win
        for c in range(self.column_size - 3):
            for r in range(self.row_size - 3):
                if self.board[r][c] == value and self.board[r+1][c+1] == value and self.board[r+2][c+2] == value and self.board[r+3][c+3] == value:
                    return True
                
        # Check \ win
        for c in range(self.column_size - 3):
            for r in range(3, self.row_size):
                if self.board[r][c] == value and self.board[r-1][c+1] == value and self.board[r-2][c+2] == value and self.board[r-3][c+3] == value:
                    return True
