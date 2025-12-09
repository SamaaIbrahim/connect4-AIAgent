from helper import (
    COLS, AI, HUMAN,
    is_full, heuristic, is_valid_move,
    get_valid_moves, move_to, create_board, print_board
)

K = 5


def _chance_outcomes_for_choice(board, chosen_col):
    outcomes = []
    outcomes.append((chosen_col, 0.6))

    left_valid = (chosen_col - 1 >= 0 and is_valid_move(board, chosen_col - 1))
    right_valid = (chosen_col + 1 < COLS and is_valid_move(board, chosen_col + 1))

    if left_valid and right_valid:
        outcomes.append((chosen_col - 1, 0.2))
        outcomes.append((chosen_col + 1, 0.2))
    elif left_valid:
        outcomes.append((chosen_col - 1, 0.4))
    elif right_valid:
        outcomes.append((chosen_col + 1, 0.4))

    return outcomes


def max_value_expected(board, depth, alpha, beta):
    if depth == 0 or is_full(board):
        return heuristic(board)

    v = -float('inf')
    for col in get_valid_moves(board):
        outcomes = _chance_outcomes_for_choice(board, col)

        expected_score = 0.0
        for actual_col, prob in outcomes:
            child = move_to(board, actual_col, AI)
            expected_score += prob * min_value_expected(child, depth - 1, alpha, beta)

        v = max(v, expected_score)
        alpha = max(alpha, v)
        if alpha >= beta:
            return v

    return v


def min_value_expected(board, depth, alpha, beta):
    if depth == 0 or is_full(board):
        return heuristic(board)
    v = float('inf')
    for col in get_valid_moves(board):
        child = move_to(board, col, HUMAN)
        v = min(v, max_value_expected(child, depth - 1, alpha, beta))
        beta = min(beta, v)
        if alpha >= beta:
            return v

    return v


def choose_move_expected(board, depth=K):
    valid = get_valid_moves(board)
    if not valid:
        return None, heuristic(board)

    best_col = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for col in valid:
        outcomes = _chance_outcomes_for_choice(board, col)

        expected = 0.0
        for actual_col, prob in outcomes:
            child = move_to(board, actual_col, AI)
            expected += prob * min_value_expected(child, depth - 1, alpha, beta)

        if best_col is None or expected > best_val or \
           (expected == best_val and abs(col - COLS//2) < abs(best_col - COLS//2)):
            best_val = expected
            best_col = col
        
        alpha = max(alpha, best_val)

    return best_col, best_val


def choose_move_expected_prune(board, depth=K):
    """Choose best move using expected values with alpha-beta pruning.

    Returns (best_col, best_val). This mirrors `choose_move_expected`
    but actively updates alpha to allow pruning in the tree builder.
    """
    valid = get_valid_moves(board)
    if not valid:
        return None, heuristic(board)

    best_col = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for col in valid:
        outcomes = _chance_outcomes_for_choice(board, col)

        expected = 0.0
        for actual_col, prob in outcomes:
            child = move_to(board, actual_col, AI)
            expected += prob * min_value_expected(child, depth - 1, alpha, beta)

        if best_col is None or expected > best_val or \
           (expected == best_val and abs(col - COLS//2) < abs(best_col - COLS//2)):
            best_val = expected
            best_col = col

        alpha = max(alpha, best_val)
        if alpha >= beta:
            break

    return best_col, best_val


if __name__ == "__main__":
    b = create_board()
    b = move_to(b, 3, HUMAN)
    b = move_to(b, 2, HUMAN)
    b = move_to(b, 3, AI)
    b = move_to(b, 4, AI)
    print_board(b)
    col, val = choose_move_expected(b)
 