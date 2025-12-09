import time
import helper
from MiniMax import MiniMax as MiniMaxNormal
from MiniMaxprune import MiniMax as MiniMaxPrune
from expectedMinMax import choose_move_expected, max_value_expected, min_value_expected
from expectedMinMaxPrune import choose_move_expected_prune

# Global counters for tracking nodes
nodes_explored = 0

def reset_counter():
    global nodes_explored
    nodes_explored = 0

def increment_counter():
    global nodes_explored
    nodes_explored += 1

# Modified MiniMax with node counting
def MiniMaxNormalCounted(board, depth, maximizing_player):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board), None

    valid_moves = helper.get_valid_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.AI)
            tmp_eval, _ = MiniMaxNormalCounted(new_board, depth - 1, False)
            if tmp_eval > max_eval:
                max_eval = tmp_eval
                best_move = col
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.HUMAN)
            tmp_eval, _ = MiniMaxNormalCounted(new_board, depth - 1, True)
            if tmp_eval < min_eval:
                min_eval = tmp_eval
                best_move = col
        return min_eval, best_move

# Modified MiniMax with pruning and node counting
def MiniMaxPruneCounted(board, depth, maximizing_player, alpha, beta):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board), None

    valid_moves = helper.get_valid_moves(board)

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.AI)
            tmp_eval, _ = MiniMaxPruneCounted(new_board, depth - 1, False, alpha, beta)
            if tmp_eval > max_eval:
                max_eval = tmp_eval
                best_move = col
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        for col in valid_moves:
            new_board = helper.move_to(board, col, helper.HUMAN)
            tmp_eval, _ = MiniMaxPruneCounted(new_board, depth - 1, True, alpha, beta)
            if tmp_eval < min_eval:
                min_eval = tmp_eval
                best_move = col
            beta = min(beta, min_eval)
            if alpha >= beta:
                break
        return min_eval, best_move

# Modified Expected MiniMax functions with node counting
def max_value_expected_counted(board, depth):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board)

    v = -float('inf')
    for col in helper.get_valid_moves(board):
        from expectedMinMax import _chance_outcomes_for_choice
        outcomes = _chance_outcomes_for_choice(board, col)
        expected_score = 0.0
        for actual_col, prob in outcomes:
            child = helper.move_to(board, actual_col, helper.AI)
            expected_score += prob * min_value_expected_counted(child, depth - 1)
        v = max(v, expected_score)
    return v

def min_value_expected_counted(board, depth):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board)

    v = float('inf')
    for col in helper.get_valid_moves(board):
        child = helper.move_to(board, col, helper.HUMAN)
        v = min(v, max_value_expected_counted(child, depth - 1))
    return v

def choose_move_expected_counted(board, depth):
    valid = helper.get_valid_moves(board)
    if not valid:
        return None, helper.heuristic(board)

    best_col = None
    best_val = -float('inf')

    from expectedMinMax import _chance_outcomes_for_choice
    for col in valid:
        outcomes = _chance_outcomes_for_choice(board, col)
        expected = 0.0
        for actual_col, prob in outcomes:
            child = helper.move_to(board, actual_col, helper.AI)
            expected += prob * min_value_expected_counted(child, depth - 1)
        
        if best_col is None or expected > best_val:
            best_val = expected
            best_col = col
    return best_col, best_val

# Modified Expected MiniMax with pruning and node counting
def max_value_expected_prune_counted(board, depth, alpha, beta):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board)

    v = -float('inf')
    for col in helper.get_valid_moves(board):
        from expectedMinMaxPrune import _chance_outcomes_for_choice
        outcomes = _chance_outcomes_for_choice(board, col)
        expected_score = 0.0
        for actual_col, prob in outcomes:
            child = helper.move_to(board, actual_col, helper.AI)
            expected_score += prob * min_value_expected_prune_counted(child, depth - 1, alpha, beta)
        v = max(v, expected_score)
        alpha = max(alpha, v)
        if alpha >= beta:
            return v
    return v

def min_value_expected_prune_counted(board, depth, alpha, beta):
    increment_counter()
    if depth == 0 or helper.is_full(board):
        return helper.heuristic(board)
    
    v = float('inf')
    for col in helper.get_valid_moves(board):
        child = helper.move_to(board, col, helper.HUMAN)
        v = min(v, max_value_expected_prune_counted(child, depth - 1, alpha, beta))
        beta = min(beta, v)
        if alpha >= beta:
            return v
    return v

def choose_move_expected_prune_counted(board, depth):
    valid = helper.get_valid_moves(board)
    if not valid:
        return None, helper.heuristic(board)

    best_col = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    from expectedMinMaxPrune import _chance_outcomes_for_choice
    for col in valid:
        outcomes = _chance_outcomes_for_choice(board, col)
        expected = 0.0
        for actual_col, prob in outcomes:
            child = helper.move_to(board, actual_col, helper.AI)
            expected += prob * min_value_expected_prune_counted(child, depth - 1, alpha, beta)
        
        if best_col is None or expected > best_val:
            best_val = expected
            best_col = col
        
        alpha = max(alpha, best_val)
        if alpha >= beta:
            break
    return best_col, best_val


def test_minimax_performance():
    """Test performance of regular MiniMax vs Alpha-Beta Pruning"""
    
    # Test board configuration
    board = [
        ['.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', 'X', 'O', '.', '.', '.'],
        ['.', 'X', 'O', 'X', 'O', '.', '.'],
        ['X', 'O', 'X', 'O', 'X', 'O', '.'],
        ['O', 'X', 'O', 'X', 'O', 'X', '.']
    ]
    
    print("="*70)
    print("PERFORMANCE TESTING: MINIMAX vs ALPHA-BETA PRUNING")
    print("="*70)
    print("\nTest Board Configuration:")
    helper.print_board(board)
    
    depths = [1, 2, 3, 4, 5]
    
    print("\n" + "="*70)
    print("DETERMINISTIC MINIMAX")
    print("="*70)
    
    for depth in depths:
        print(f"\n--- Depth K = {depth} ---")
        
        # Test regular MiniMax
        reset_counter()
        start_time = time.time()
        score, move = MiniMaxNormalCounted(board, depth, True)
        end_time = time.time()
        normal_time = end_time - start_time
        normal_nodes = nodes_explored
        
        print(f"MiniMax (Normal):")
        print(f"  Time taken: {normal_time:.6f} seconds")
        print(f"  Nodes explored: {normal_nodes}")
        print(f"  Best move: Column {move}, Score: {score}")
        
        # Test MiniMax with Alpha-Beta Pruning
        reset_counter()
        start_time = time.time()
        score, move = MiniMaxPruneCounted(board, depth, True, float('-inf'), float('inf'))
        end_time = time.time()
        prune_time = end_time - start_time
        prune_nodes = nodes_explored
        
        print(f"\nMiniMax (Alpha-Beta Pruning):")
        print(f"  Time taken: {prune_time:.6f} seconds")
        print(f"  Nodes explored: {prune_nodes}")
        print(f"  Best move: Column {move}, Score: {score}")
        
        # Calculate improvement
        time_speedup = normal_time / prune_time if prune_time > 0 else 0
        nodes_reduction = ((normal_nodes - prune_nodes) / normal_nodes * 100) if normal_nodes > 0 else 0
        
        print(f"\nImprovement:")
        print(f"  Time speedup: {time_speedup:.2f}x faster")
        print(f"  Nodes reduction: {nodes_reduction:.2f}% fewer nodes")


def test_expected_minimax_performance():
    """Test performance of Expected MiniMax vs Expected MiniMax with Pruning"""
    
    # Test board configuration
    board = helper.create_board()
    board = helper.move_to(board, 3, helper.HUMAN)
    board = helper.move_to(board, 2, helper.HUMAN)
    board = helper.move_to(board, 3, helper.AI)
    board = helper.move_to(board, 4, helper.AI)
    
    print("\n\n" + "="*70)
    print("PERFORMANCE TESTING: EXPECTED MINIMAX (STOCHASTIC)")
    print("="*70)
    print("\nTest Board Configuration:")
    helper.print_board(board)
    
    depths = [1, 2, 3, 4, 5]
    
    for depth in depths:
        print(f"\n--- Depth K = {depth} ---")
        
        # Test Expected MiniMax
        reset_counter()
        start_time = time.time()
        move, score = choose_move_expected_counted(board, depth)
        end_time = time.time()
        expected_time = end_time - start_time
        expected_nodes = nodes_explored
        
        print(f"Expected MiniMax (Normal):")
        print(f"  Time taken: {expected_time:.6f} seconds")
        print(f"  Nodes explored: {expected_nodes}")
        print(f"  Best move: Column {move}, Expected Score: {score:.4f}")
        
        # Test Expected MiniMax with Pruning
        reset_counter()
        start_time = time.time()
        move, score = choose_move_expected_prune_counted(board, depth)
        end_time = time.time()
        prune_time = end_time - start_time
        prune_nodes = nodes_explored
        
        print(f"\nExpected MiniMax (Alpha-Beta Pruning):")
        print(f"  Time taken: {prune_time:.6f} seconds")
        print(f"  Nodes explored: {prune_nodes}")
        print(f"  Best move: Column {move}, Expected Score: {score:.4f}")
        
        # Calculate improvement
        time_speedup = expected_time / prune_time if prune_time > 0 else 0
        nodes_reduction = ((expected_nodes - prune_nodes) / expected_nodes * 100) if expected_nodes > 0 else 0
        
        print(f"\nImprovement:")
        print(f"  Time speedup: {time_speedup:.2f}x faster")
        print(f"  Nodes reduction: {nodes_reduction:.2f}% fewer nodes")


if __name__ == "__main__":
    test_minimax_performance()
    test_expected_minimax_performance()
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)