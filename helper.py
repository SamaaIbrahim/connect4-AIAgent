import copy

ROWS = 6
COLS = 7
AI = 'X'
HUMAN = 'O'
EMPTY = '.'
K = 5

def is_full(board):
    return len(get_valid_moves(board)) == 0

def create_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

def print_board(board):
    for r in range(ROWS):
        print(" ".join(board[r]))
    print()

def is_valid_move(board, col):
    return 0 <= col < COLS and board[0][col] == EMPTY

def get_valid_moves(board):
    moves = []
    for col in range(COLS):
        if is_valid_move(board, col):
            moves.append(col)
    return moves

def move_to(board, col, player):
    new_board = copy.deepcopy(board)
    for r in range(ROWS - 1, -1, -1):
        if new_board[r][col] == EMPTY:
            new_board[r][col] = player
            break
    return new_board

def heuristic(board):

    score = 0.0

    def score_window(win):
        ai_count = win.count(AI)
        hu_count = win.count(HUMAN)
        if ai_count > 0 and hu_count > 0:
            return 0
        weights = {0: 0, 1: 1, 2: 10, 3: 100, 4: 100000}
        if ai_count > 0:
            return weights[ai_count]
        if hu_count > 0:
            return -weights[hu_count]
        return 0

    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if board[r][center_col] == AI)
    score += center_count * 3

    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += score_window(window)

    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += score_window(window)

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window)

    for r in range(3, ROWS):
        for c in range(COLS - 3):
            window = [board[r - i][c + i] for i in range(4)]
            score += score_window(window)

    return float(score)
