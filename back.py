from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from helper import heuristic, get_valid_moves, move_to, is_full 

app = Flask(__name__); 
CORS(app)  # Enable CORS for frontend communication

def count_fours(board, player):
    """Count number of 4-in-a-rows for a player"""
    count = 0
    rows, cols = len(board), len(board[0])
    
    # Horizontal
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c + i] == player for i in range(4)):
                count += 1
    
    # Vertical
    for r in range(rows - 3):
        for c in range(cols):
            if all(board[r + i][c] == player for i in range(4)):
                count += 1
    
    # Diagonal (down-right)
    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                count += 1
    
    # Diagonal (down-left)
    for r in range(rows - 3):
        for c in range(3, cols):
            if all(board[r + i][c - i] == player for i in range(4)):
                count += 1
    
    return count

def get_game_result(board):
    """Determine game winner and scores - only game over when board is full"""
    x_fours = count_fours(board, 'X')
    o_fours = count_fours(board, 'O')
    
    result = {
        'x_fours': x_fours,
        'o_fours': o_fours,
        'winner': None,
        'isGameOver': False
    }
    
    # Game is only over when board is full
    if is_full(board):
        result['isGameOver'] = True
        # Determine winner based on who has more 4-in-a-rows
        if x_fours > o_fours:
            result['winner'] = 'X'
        elif o_fours > x_fours:
            result['winner'] = 'O'
        elif x_fours == o_fours and x_fours > 0:
            result['winner'] = 'Tie'
        else:
            result['winner'] = 'Draw'
    
    return result

def build_tree_minimax(board, depth, maximizing_player, use_pruning=False, alpha=float('-inf'), beta=float('inf'), level=0, parent_col=None):
    """Build minimax tree with visualization data"""
    
    if depth == 0 or is_full(board):
        h = heuristic(board)
        game_result = get_game_result(board)
        return {
            'score': h,
            'move': None,
            'tree': {
                'type': 'LEAF',
                'label': f'Col {parent_col + 1}' if parent_col is not None else 'Leaf',
                'score': h,
                'gameResult': game_result
            }
        }
    
    valid_moves = get_valid_moves(board)
    tree_node = {
        'type': 'MAX' if maximizing_player else 'MIN',
        'label': f'Col {parent_col + 1}' if parent_col is not None else 'Root',
        'children': []
    }
    
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        
        for i, col in enumerate(valid_moves):
            new_board = move_to(board, col, 'X')  # AI
            result = build_tree_minimax(new_board, depth - 1, False, use_pruning, alpha, beta, level + 1, col)
            
            tree_node['children'].append(result['tree'])
            
            if result['score'] > max_eval:
                max_eval = result['score']
                best_move = col
            
            if use_pruning:
                alpha = max(alpha, max_eval)
                if alpha >= beta:
                    # Add pruned nodes
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
            new_board = move_to(board, col, 'O')  # Human
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


def build_tree_expected(board, depth, maximizing=True, parent_col=None):
    """Build expected minimax tree with full expected value calculations"""
    
    if depth == 0 or is_full(board):
        h = heuristic(board)
        game_result = get_game_result(board)
        return {
            'score': h,
            'move': None,
            'tree': {
                'type': 'LEAF',
                'label': f'Col {parent_col + 1}' if parent_col is not None else 'Leaf',
                'score': h,
                'gameResult': game_result
            }
        }
    
    valid_moves = get_valid_moves(board)
    
    if maximizing:
        # MAX node
        tree_node = {
            'type': 'MAX',
            'label': f'Col {parent_col + 1}' if parent_col is not None else 'Root',
            'children': []
        }
        
        max_eval = float('-inf')
        best_move = None
        
        for col in valid_moves:
            new_board = move_to(board, col, 'X')
            result = build_tree_expected(new_board, depth - 1, False, col)
            
            tree_node['children'].append(result['tree'])
            
            if result['score'] > max_eval:
                max_eval = result['score']
                best_move = col
        
        tree_node['score'] = max_eval
        return {'score': max_eval, 'move': best_move, 'tree': tree_node}
    
    else:
        # EXPECTED (chance) node for opponent
        tree_node = {
            'type': 'EXPECTED',
            'label': f'Expected (Col {parent_col + 1})' if parent_col is not None else 'Expected',
            'children': []
        }
        
        expected_value = 0
        probability = 1.0 / len(valid_moves)
        
        for col in valid_moves:
            new_board = move_to(board, col, 'O')
            result = build_tree_expected(new_board, depth - 1, True, col)
            
            child_node = result['tree'].copy()
            child_node['probability'] = probability
            tree_node['children'].append(child_node)
            
            expected_value += probability * result['score']
        
        tree_node['score'] = round(expected_value, 2)
        return {'score': expected_value, 'move': None, 'tree': tree_node}


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
            # Use your MiniMax function and build tree
            result = build_tree_minimax(board, depth, True, False)
            score = result['score']
            move = result['move']
            tree = result['tree']
            
        elif algorithm == 'alphabeta':
            # Use your MiniMaxPrune function and build tree
            result = build_tree_minimax(board, depth, True, True)
            score = result['score']
            move = result['move']
            tree = result['tree']
            
        elif algorithm == 'expected':
            # Use expected minimax with full tree
            result = build_tree_expected(board, depth, True)
            score = result['score']
            move = result['move']
            tree = result['tree']
        else:
            return jsonify({'error': 'Invalid algorithm'}), 400
        
        end_time = time.time()
        time_taken = int((end_time - start_time) * 1000)  # Convert to ms
        
        # IMPORTANT: Apply the AI move to the board BEFORE checking game result
        board_after_move = board
        if move is not None:
            board_after_move = move_to(board, move, 'X')
        
        # Get game result AFTER the AI move is applied
        game_result = get_game_result(board_after_move)
        
        return jsonify({
            'move': move,
            'score': score,
            'time': time_taken,
            'nodes': 'N/A',
            'tree': tree,
            'gameResult': game_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/heuristic', methods=['POST'])
def get_heuristic():
    """Get heuristic value for a board"""
    try:
        data = request.json
        board = data['board']
        h = heuristic(board)
        game_result = get_game_result(board)
        return jsonify({
            'heuristic': h,
            'gameResult': game_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("🎮 Connect 4 AI Flask Server")
    print("=" * 50)
    print("Server running on: http://localhost:5000")
    print("Open connect4.html in your browser")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)