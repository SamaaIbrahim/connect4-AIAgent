from helper import (
     COLS, AI, HUMAN,
    is_full, heuristic, is_valid_move,
    get_valid_moves, move_to, create_board, print_board
)

K = 5   


def _chance_outcomes_for_choice(board, chosen_col):
    outcomes = []

    outcomes.append((chosen_col, 0.6))

    left_valid  = (chosen_col - 1 >= 0 and is_valid_move(board, chosen_col - 1))
    right_valid = (chosen_col + 1 < COLS and is_valid_move(board, chosen_col + 1))

   
    if left_valid and right_valid:
        outcomes.append((chosen_col - 1, 0.2))
        outcomes.append((chosen_col + 1, 0.2))

    elif left_valid:
        outcomes.append((chosen_col - 1, 0.4))


    elif right_valid:
        outcomes.append((chosen_col + 1, 0.4))

    return outcomes


def max_value_expected(board, depth):
    if depth == K or is_full(board):
        return heuristic(board)

    v = -float('inf')
    for col in get_valid_moves(board):

        outcomes = _chance_outcomes_for_choice(board, col)

        expected_score = 0.0
        for actual_col, prob in outcomes:
            child = move_to(board, actual_col, AI)
            expected_score += prob * min_value_expected(child, depth + 1)

        v = max(v, expected_score)

    return v


def min_value_expected(board, depth):

    if depth == K or is_full(board):
        return heuristic(board)

    v = float('inf')

    for col in get_valid_moves(board):
        child = move_to(board, col, HUMAN)
        v = min(v, max_value_expected(child, depth + 1))

    return v


def choose_move_expected(board):
    valid = get_valid_moves(board)
    if not valid:
        return None, heuristic(board)

    best_col = None
    best_val = -float('inf')

    for col in valid:
        outcomes = _chance_outcomes_for_choice(board, col)

        expected = 0.0
        for actual_col, prob in outcomes:
            child = move_to(board, actual_col, AI)
            expected += prob * min_value_expected(child, 1)

        
        if best_col is None or expected > best_val or \
           (expected == best_val and abs(col - COLS//2) < abs(best_col - COLS//2)):
            best_val = expected
            best_col = col

    return best_col, best_val



if __name__ == "__main__":
    b = create_board()

    b = move_to(b, 3, HUMAN)
    b = move_to(b, 2, HUMAN)
    b = move_to(b, 3, AI)
    b = move_to(b, 4, AI)

    print("Board:")
    print_board(b)
    print("Heuristic =", heuristic(b))

    best_col, best_val = choose_move_expected(b)
    print("AI chooses column:", best_col, "expected:", best_val)
