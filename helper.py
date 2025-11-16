import copy
ROWS = 6
COLS = 7
AI = 'X'
HUMAN = 'O'
EMPTY = '.'
K = 5
class Helper:
    @staticmethod
    def is_valid_move(self, board, col):
        return 0 <= col < COLS and board[0][col] == EMPTY
    @staticmethod
    def get_valid_moves(self, board):
        moves = []
        for col in range(COLS):
            if self.is_valid_move(board, col):
                moves.append(col)
        return moves
    @staticmethod
    def move_to(board, col, player):
        new_board = copy.deepcopy(board)
        for r in range(ROWS - 1, -1, -1):
            if new_board[r][col] == EMPTY:
                new_board[r][col] = player
                break
        return new_board

    @staticmethod
    def heuristic(board):
        
        score = 0.0

        def score_window(win):
            ai_count = win.count(AI)
            hu_count = win.count(HUMAN)
            # contested window -> 0
            if ai_count > 0 and hu_count > 0:
                return 0
            # weights: 1->1, 2->10, 3->100, 4->100000
            weights = {0: 0, 1: 1, 2: 10, 3: 100, 4: 100000}
            if ai_count > 0:
                return weights[ai_count]
            if hu_count > 0:
                return -weights[hu_count]
            return 0 #fully empty

        # center column bonus 
        center_col = COLS // 2
        center_count = sum(1 for r in range(ROWS) if board[r][center_col] == AI)
        score += center_count * 3

        # horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [board[r][c + i] for i in range(4)]
                score += score_window(window)

        # vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [board[r + i][c] for i in range(4)]
                score += score_window(window)

        # diagonal down-right windows
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += score_window(window)

        # diagonal up-right windows
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += score_window(window)

        return float(score)

