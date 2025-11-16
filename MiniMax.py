import helper

def is_game_over(board):
    return all(board[r][c] != ' ' for r in range(helper.ROWS) for c in range(helper.COLS))

def MiniMax(board, depth, maximizing_player):
    if depth == 0 or is_game_over(board):
        return helper.heuristic(board), None

    valid_moves= helper.get_valid_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None

        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.AI)

            tmp_eval, _ = MiniMax(new_board, depth - 1, False)

            if tmp_eval > max_eval:
                max_eval = tmp_eval
                best_move = col

        return max_eval, best_move

    else:
        min_eval = float('inf')
        best_move = None

        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.HUMAN)

            tmp_eval, _ = MiniMax(new_board, depth - 1, True)

            if tmp_eval < min_eval:
                min_eval = tmp_eval
                best_move = col

        return min_eval, best_move


board = [
    ['.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.'],
    ['.', '.', 'X', 'O', '.', '.', '.'],
    ['.', 'X', 'O', 'X', 'O', '.', '.'],
    ['X', 'O', 'X', 'O', 'X', 'O', '.'],
    ['O', 'X', 'O', 'X', 'O', 'X', '.']
]

best = MiniMax(board, 5, True)
print("Best score and move:", best)
