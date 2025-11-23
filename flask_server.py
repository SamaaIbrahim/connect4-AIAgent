from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import math
from helper import heuristic, get_valid_moves, move_to, is_full, AI, HUMAN, COLS, is_valid_move
from MiniMax import MiniMax
from MiniMaxprune import MiniMax as MiniMaxPrune
import expectedMinMax as expected_no_prune
import expectedMinMaxPrune as expected_prune

app = Flask(__name__)
CORS(app)

def count_pieces(board):
    """Count pieces for each player"""
    count_o = sum(row.count('O') for row in board)
    count_x = sum(row.count('X') for row in board)
    return {'O': count_o, 'X': count_x}

def build_tree_minimax(board, depth, maximizing_player, use_pruning=False, alpha=float('-inf'), beta=float('inf'), level=0, parent_col=None):
    """Build minimax tree with visualization data"""
    
    if depth == 0 or is_full(board):
        h = heuristic(board)
        return {
            'score': h,
            'move': None,
            'tree': {
                'type': 'LEAF',
                'label': f'Col {parent_col + 1}' if parent_col is not None else 'Leaf',
                'score': h
            }
        }
    
    valid_moves = get_valid_moves(board)
    tree_node = {
        'type': 'MAX' if maximizing_player else 'MIN',
        'label': f'Col {parent_col + 1}' if parent_col is not None else 'Root',
        'children': [],
        'alpha': alpha if use_pruning else None,
        'beta': beta if use_pruning else None,
        'pruning_enabled': bool(use_pruning),
        'pruned': False
    }
    
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        
        for i, col in enumerate(valid_moves):
            new_board = move_to(board, col, 'X')
            result = build_tree_minimax(new_board, depth - 1, False, use_pruning, alpha, beta, level + 1, col)
            
            tree_node['children'].append(result['tree'])
            
            if result['score'] > max_eval:
                max_eval = result['score']
                best_move = col
            
            if use_pruning:
                alpha = max(alpha, max_eval)
                tree_node['alpha'] = alpha
                if alpha >= beta:
                    tree_node['pruned'] = True
                    for j in range(i + 1, len(valid_moves)):
                        tree_node['children'].append({
                            'type': 'PRUNED',
                            'label': f'Col {valid_moves[j] + 1}',
                            'score': '✂'
                        })
                    break
        
        tree_node['score'] = max_eval
        return {'score': max_eval, 'move': best_move, 'tree': tree_node}
    
    else:
        min_eval = float('inf')
        best_move = None
        
        for i, col in enumerate(valid_moves):
            new_board = move_to(board, col, 'O')
            result = build_tree_minimax(new_board, depth - 1, True, use_pruning, alpha, beta, level + 1, col)
            
            tree_node['children'].append(result['tree'])
            
            if result['score'] < min_eval:
                min_eval = result['score']
                best_move = col
            
            if use_pruning:
                beta = min(beta, min_eval)
                if alpha >= beta:
                    for j in range(i + 1, len(valid_moves)):
                        tree_node['children'].append({
                            'type': 'PRUNED',
                            'label': f'Col {valid_moves[j] + 1}',
                            'score': '✂'
                        })
                    break
        
        tree_node['score'] = min_eval
        return {'score': min_eval, 'move': best_move, 'tree': tree_node}


def build_tree_expected_recursive(board, depth, is_max, use_pruning=False, alpha=float('-inf'), beta=float('inf'), parent_col=None):
    """Build expected minimax tree recursively with proper MAX/CHANCE/MIN structure"""
    
    if depth == 0 or is_full(board):
        h = heuristic(board)
        return {
            'type': 'LEAF',
            'label': f'Col {parent_col + 1}' if parent_col is not None else 'Leaf',
            'score': h
        }
    
    if is_max:
        # MAX node - AI's turn
        valid_moves = get_valid_moves(board)
        max_node = {
            'type': 'MAX',
            'label': f'Col {parent_col + 1}' if parent_col is not None else 'Root',
            'children': [],
            'score': float('-inf'),
            'alpha': alpha if use_pruning else None,
            'beta': beta if use_pruning else None,
            'pruning_enabled': bool(use_pruning),
            'pruned': False
        }
        
        best_score = float('-inf')
        
        for col in valid_moves:
            # Create CHANCE node for this choice
            chance_node = build_chance_node(board, col, depth, use_pruning, alpha, beta)
            max_node['children'].append(chance_node)
            
            if chance_node['score'] > best_score:
                best_score = chance_node['score']
            
            if use_pruning:
                alpha = max(alpha, best_score)
                max_node['alpha'] = alpha
                if alpha >= beta:
                    max_node['pruned'] = True
                    break
        
        max_node['score'] = best_score
        return max_node
    
    else:
        # MIN node - Human's turn (deterministic)
        valid_moves = get_valid_moves(board)
        min_node = {
            'type': 'MIN',
            'label': f'Col {parent_col + 1}' if parent_col is not None else 'Min',
            'children': [],
            'score': float('inf'),
            'alpha': alpha if use_pruning else None,
            'beta': beta if use_pruning else None,
            'pruning_enabled': bool(use_pruning),
            'pruned': False
        }
        
        best_score = float('inf')
        
        for col in valid_moves:
            child_board = move_to(board, col, HUMAN)
            child_tree = build_tree_expected_recursive(child_board, depth - 1, True, use_pruning, alpha, beta, col)
            min_node['children'].append(child_tree)
            
            if child_tree['score'] < best_score:
                best_score = child_tree['score']
            
            if use_pruning:
                beta = min(beta, best_score)
                min_node['beta'] = beta
                if alpha >= beta:
                    min_node['pruned'] = True
                    break
        
        min_node['score'] = best_score
        return min_node


def build_chance_node(board, chosen_col, depth, use_pruning, alpha, beta):
    """Build a CHANCE node showing stochastic outcomes"""
    
    if use_pruning:
        outcomes = expected_prune._chance_outcomes_for_choice(board, chosen_col)
    else:
        outcomes = expected_no_prune._chance_outcomes_for_choice(board, chosen_col)
    
    chance_node = {
        'type': 'CHANCE',
        'label': f'Col {chosen_col + 1}',
        'children': [],
        'score': 0.0,
        'prune_applicable': False,
        'pruning_enabled': bool(use_pruning)
    }
    
    expected_score = 0.0
    
    for actual_col, prob in outcomes:
        child_board = move_to(board, actual_col, AI)
        
        # Build the subtree for this outcome: after the stochastic placement
        # it's the human's (MIN) turn, so recurse with is_max=False and depth-1
        child_subtree = build_tree_expected_recursive(child_board, depth - 1, False, use_pruning, alpha, beta, actual_col)

        # Directly append the MIN subtree as the child of this CHANCE node so
        # the structure reads: CHANCE -> MIN -> CHANCE -> MIN ... which is the
        # alternating pattern you requested. Add the probability into the
        # child's label for clarity and expose the probability value.
        if isinstance(child_subtree, dict):
            orig_label = child_subtree.get('label', f'Col {actual_col + 1}')
            child_subtree['label'] = f'{orig_label} ({prob:.1f})'
            child_subtree['prob'] = prob
            # mark that pruning is not applicable at CHANCE level but may be in descendants
            child_subtree['prune_applicable'] = True

        chance_node['children'].append(child_subtree)

        expected_score += prob * (child_subtree.get('score', 0.0) or 0.0)
    
    chance_node['score'] = expected_score
    return chance_node


def build_tree_expected(board, depth, use_pruning=False):
    """Build expected minimax tree with full structure"""
    # Compute the best move/score using the requested depth (full search)
    if use_pruning:
        best_move, best_score = expected_prune.choose_move_expected(board, depth)
    else:
        best_move, best_score = expected_no_prune.choose_move_expected(board, depth)

    # For visualization, cap the tree depth to avoid enormous trees that the
    # browser cannot render. Keep the computed move accurate but build a
    # shallower tree for display.
    VISUAL_MAX_DEPTH = 4
    vis_depth = min(depth, VISUAL_MAX_DEPTH)

    tree = build_tree_expected_recursive(board, vis_depth, True, use_pruning)

    return {'score': best_score, 'move': best_move, 'tree': tree, 'visual_depth': vis_depth}


def _sanitize_for_json(obj):
    """Recursively replace non-JSON-safe floats (Infinity, -Infinity, NaN)
    with None so `jsonify` always produces valid JSON.
    This mutates dictionaries/lists in-place and returns a sanitized copy/value.
    """
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            obj[k] = _sanitize_for_json(v)
        return obj
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    return obj


@app.route('/health', methods=['GET'])
def health_check():
    """Check if server is running"""
    return jsonify({'status': 'ok'}), 200


@app.route('/ai_move', methods=['POST'])
def ai_move():
    """Calculate AI move using your Python functions"""
    try:
        data = request.json
        board = data['board']
        algorithm = data['algorithm']
        depth = data['depth']
        
        start_time = time.time()
        
        if algorithm == 'minimax':
            result = build_tree_minimax(board, depth, True, False)
            score = result['score']
            move = result['move']
            tree = result['tree']
            
        elif algorithm == 'alphabeta':
            result = build_tree_minimax(board, depth, True, True)
            score = result['score']
            move = result['move']
            tree = result['tree']
            
        elif algorithm == 'expected':
            result = build_tree_expected(board, depth, False)
            score = result['score']
            move = result['move']
            tree = result['tree']
            
        elif algorithm == 'expected_prune':
            result = build_tree_expected(board, depth, True)
            score = result['score']
            move = result['move']
            tree = result['tree']
        else:
            return jsonify({'error': 'Invalid algorithm'}), 400
        
        end_time = time.time()
        time_taken = int((end_time - start_time) * 1000)
        
        # Only check if board is full - NO WIN CHECKING
        game_over = is_full(board)
        
        response = {
            'move': move,
            'score': score,
            'time': time_taken,
            'nodes': 'N/A',
            'tree': tree,
            'game_over': game_over
        }
        
        # Only end game if board is full
        if game_over:
            final_scores = count_pieces(board)
            response['final_scores'] = final_scores
            
            # Determine winner based on piece count with detailed message
            if final_scores['X'] > final_scores['O']:
                response['winner'] = 'X'
                diff = final_scores['X'] - final_scores['O']
                response['reason'] = f"Board is full! Final Score - AI (X): {final_scores['X']} pieces vs You (O): {final_scores['O']} pieces. AI wins with {diff} more piece{'s' if diff > 1 else ''}!"
            elif final_scores['O'] > final_scores['X']:
                response['winner'] = 'O'
                diff = final_scores['O'] - final_scores['X']
                response['reason'] = f"Board is full! Final Score - You (O): {final_scores['O']} pieces vs AI (X): {final_scores['X']} pieces. You win with {diff} more piece{'s' if diff > 1 else ''}!"
            else:
                response['winner'] = None
                response['reason'] = f"Board is full! Final Score - You (O): {final_scores['O']} pieces vs AI (X): {final_scores['X']} pieces. It's a perfect tie!"
        
        # Sanitize response to ensure JSON validity (no Infinity/NaN values)
        try:
            _sanitize_for_json(response)
        except Exception:
            # If sanitization fails for any reason, fall back to returning
            # the response without modifications (Flask/json will still try).
            pass

        return jsonify(response)
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/heuristic', methods=['POST'])
def get_heuristic():
    """Get heuristic value for a board"""
    try:
        data = request.json
        board = data['board']
        h = heuristic(board)
        return jsonify({'heuristic': h})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("🎮 Connect 4 AI Flask Server - UPDATED VERSION")
    print("=" * 50)
    print("Server running on: http://localhost:5000")
    print("Open gui.html in your browser")
    print("NOTE: Game only ends when board is FULL")
    print("Winner determined by piece count")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)