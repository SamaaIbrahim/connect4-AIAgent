import tkinter as tk
from tkinter import ttk, messagebox
import copy
from helper import (
    COLS, ROWS, AI, HUMAN, EMPTY,
    is_full, heuristic, is_valid_move,
    get_valid_moves, move_to, create_board
)
from MiniMax import MiniMax as minimax_basic
from MiniMaxprune import MiniMax as minimax_prune
from expectedMinMax import _chance_outcomes_for_choice


class Connect4GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Connect 4: AI vs Human")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        
        # Game state
        self.board = create_board()
        self.depth = 3  # Default to 3 for expected mode compatibility
        self.mode = 'minimax'
        self.game_started = False
        self.current_player = HUMAN
        self.score = {'ai': 0, 'human': 0}
        self.tree_data = None
        self.ai_chosen_col = None  # Track AI's chosen column
        self.memo = {}  # Memoization cache
        self.show_full_tree = False  # Option to show full tree
        
        # Colors
        # Board / piece colors (dark theme)
        self.bg_color = '#0b2540'     # board/background dark navy
        self.empty_color = '#07182d'  # empty cell deep navy
        self.human_color = '#f59e0b'   # bright yellow
        self.ai_color = '#ef4444'      # vivid red
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI"""
        # Modern ttk styling
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Palette (modern dark-blue + yellow/red)
        ACCENT = '#0b3d91'       # dark blue accent
        ACCENT_DARK = '#062a66'  # darker on active
        YELLOW = '#f59e0b'       # human / warning accent
        RED = '#ef4444'          # ai accent
        BG = '#071428'           # deep navy app background
        PANEL_BG = '#0b2540'     # slightly lighter panel background

        style.configure('Accent.TButton', background=ACCENT, foreground='white', font=('Segoe UI', 10, 'bold'), padding=6)
        style.map('Accent.TButton', background=[('active', ACCENT_DARK)])
        style.configure('Warning.TButton', background=YELLOW, foreground='#071428', font=('Segoe UI', 10, 'bold'), padding=6)
        style.map('Warning.TButton', background=[('active', '#d97706')])
        style.configure('Secondary.TButton', background='#164e8a', foreground='white', font=('Segoe UI', 10), padding=6)

        # Apply app background
        try:
            self.root.configure(bg=BG)
        except Exception:
            pass
        # Title (modern header)
        title_frame = tk.Frame(self.root, bg=ACCENT_DARK, height=64)
        title_frame.pack(fill='x', padx=8, pady=8)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="Connect 4: AI vs Human",
            font=('Segoe UI', 20, 'bold'),
            bg='#111827',
            fg='white'
        ).pack(side='left', padx=16)

        # (subtitle removed for cleaner game-style header)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=PANEL_BG)
        main_frame.pack(fill='both', expand=True, padx=10, pady=6)
        
        # Left side - Game board and controls
        left_frame = tk.Frame(main_frame, bg='#f0f0f0')
        left_frame.pack(side='left', fill='both', padx=(0, 5))
        
        # Compact settings and score panel
        top_panel = tk.Frame(left_frame, bg='white', relief='ridge', bd=2)
        top_panel.pack(fill='x', padx=5, pady=5)
        
        # Settings row
        settings_frame = tk.Frame(top_panel, bg='white')
        settings_frame.pack(fill='x', pady=8, padx=10)
        
        # Depth
        tk.Label(settings_frame, text="Depth (K):", font=('Arial', 10), bg='white').pack(side='left', padx=5)
        self.depth_var = tk.IntVar(value=3)
        self.depth_spinbox = tk.Spinbox(
            settings_frame,
            from_=1,
            to=8,
            textvariable=self.depth_var,
            width=5,
            font=('Arial', 10),
            command=self.update_depth
        )
        self.depth_spinbox.pack(side='left', padx=5)
        
        # Info label for expected mode
        self.depth_warning = tk.Label(
            settings_frame,
            text="ℹ️ Tree shows depth 3 when K>3",
            font=('Arial', 8),
            bg='white',
            fg='#3498db'
        )
        self.depth_warning.pack(side='left', padx=5)
        
        # Mode
        tk.Label(settings_frame, text="Mode:", font=('Arial', 10), bg='white').pack(side='left', padx=(15, 5))
        self.mode_var = tk.StringVar(value='minimax')
        self.mode_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.mode_var,
            values=['minimax', 'minimaxprune', 'expected', 'expectedprune'],
            state='readonly',
            width=20,
            font=('Arial', 9)
        )
        self.mode_combo.pack(side='left', padx=5)
        self.mode_combo.bind('<<ComboboxSelected>>', self.update_mode)
        
        # Full tree checkbox
        self.full_tree_var = tk.BooleanVar(value=False)
        self.full_tree_check = tk.Checkbutton(
            settings_frame,
            text="Full Tree",
            variable=self.full_tree_var,
            font=('Arial', 9),
            bg='white',
            command=self.update_full_tree
        )
        self.full_tree_check.pack(side='left', padx=(15, 5))
        
        # Score row
        score_frame = tk.Frame(top_panel, bg='white')
        score_frame.pack(fill='x', pady=5, padx=10)
        
        # Human score
        human_score_frame = tk.Frame(score_frame, bg='white')
        human_score_frame.pack(side='left', padx=20)
        tk.Label(human_score_frame, text="Human (O)", font=('Arial', 9), bg='white', fg='#7f8c8d').pack()
        self.human_score_label = tk.Label(
            human_score_frame,
            text="0",
            font=('Arial', 24, 'bold'),
            fg='#3498db',
            bg='white'
        )
        self.human_score_label.pack()
        
        # Message
        self.message_label = tk.Label(
            score_frame,
            text="Click a column to start",
            font=('Arial', 10, 'bold'),
            bg='white',
            wraplength=200
        )
        self.message_label.pack(side='left', padx=20)
        
        # AI score
        ai_score_frame = tk.Frame(score_frame, bg='white')
        ai_score_frame.pack(side='left', padx=20)
        tk.Label(ai_score_frame, text="AI (X)", font=('Arial', 9), bg='white', fg='#7f8c8d').pack()
        self.ai_score_label = tk.Label(
            ai_score_frame,
            text="0",
            font=('Arial', 24, 'bold'),
            fg='#e74c3c',
            bg='white'
        )
        self.ai_score_label.pack()
        
        # Board panel - fixed size, always fully visible
        board_frame = tk.Frame(left_frame, bg='#f0f0f0')
        board_frame.pack(pady=10, padx=5)
        
        board_panel = tk.Frame(board_frame, bg=self.bg_color, relief='ridge', bd=3)
        board_panel.pack()
        
        self.canvas = tk.Canvas(
            board_panel,
            width=COLS * 80 + 20,
            height=ROWS * 80 + 20,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        
        # Buttons frame
        buttons_frame = tk.Frame(left_frame, bg=PANEL_BG)
        buttons_frame.pack(pady=10)
        
        # Helper to create circular buttons using Canvas
        def create_circle_button(parent, text, command, diameter=56, bg_color=ACCENT, fg_color='white', active_color=None):
            c = tk.Canvas(parent, width=diameter, height=diameter, highlightthickness=0, bg=PANEL_BG)
            radius = diameter // 2
            pad = 2
            oval = c.create_oval(pad, pad, diameter-pad, diameter-pad, fill=bg_color, outline='')
            lbl = c.create_text(radius, radius, text=text, fill=fg_color, font=('Segoe UI', 9, 'bold'))

            # determine active color
            active = active_color or ACCENT_DARK

            def on_click(evt=None):
                try:
                    command()
                except Exception:
                    pass

            def on_enter(evt=None):
                try:
                    # enlarge slightly and darken
                    c.itemconfig(oval, fill=active)
                    c.scale(oval, radius, radius, 1.06, 1.06)
                    c.scale(lbl, radius, radius, 1.06, 1.06)
                except Exception:
                    pass

            def on_leave(evt=None):
                try:
                    c.itemconfig(oval, fill=bg_color)
                    # restore by resetting coords (simpler than inverse scale)
                    c.coords(oval, pad, pad, diameter-pad, diameter-pad)
                    c.coords(lbl, radius, radius)
                except Exception:
                    pass

            c.bind('<Button-1>', on_click)
            c.bind('<Enter>', on_enter)
            c.bind('<Leave>', on_leave)
            c.config(cursor='hand2')
            return c

        # Restart circular button
        self.restart_button = create_circle_button(buttons_frame, '⟲', self.restart_game, diameter=56, bg_color=YELLOW, fg_color='#071428')
        self.restart_button.pack(side='left', padx=8)
        
        # Start Game circular button
        # Starts the game without clearing the board (locks settings and enables play)
        self.start_button = create_circle_button(buttons_frame, '▶', self.start_game, diameter=56, bg_color='#10b981', fg_color='white', active_color='#0f766e')
        self.start_button.pack(side='left', padx=8)
        # New Game circular button
        self.new_game_button = create_circle_button(buttons_frame, '＋', self.reset_game, diameter=56, bg_color=ACCENT, fg_color='white', active_color=ACCENT_DARK)
        self.new_game_button.pack(side='left', padx=8)

        # Header reset button placed next to title for game-like layout
        try:
            self.header_reset = create_circle_button(title_frame, '⟲', self.reset_game, diameter=44, bg_color=ACCENT, fg_color='white', active_color=ACCENT_DARK)
            self.header_reset.pack(side='left', padx=8)
        except Exception:
            pass
        
        # Right side - Tree visualization
        right_frame = tk.Frame(main_frame, bg='white', relief='ridge', bd=2)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Tree header with AI choice info
        tree_header = tk.Frame(right_frame, bg='white')
        tree_header.pack(pady=10)
        
        tk.Label(
            tree_header,
            text="AI Decision Tree",
            font=('Segoe UI', 14, 'bold'),
            bg='white',
            fg='#111827'
        ).pack(side='left')
        
        self.ai_choice_label = tk.Label(
            tree_header,
            text="",
            font=('Arial', 11, 'bold'),
            bg='white',
            fg='#e74c3c'
        )
        self.ai_choice_label.pack(pady=5)
        
        self.tree_info_label = tk.Label(
            tree_header,
            text="",
            font=('Arial', 9),
            bg='white',
            fg='#7f8c8d'
        )
        self.tree_info_label.pack()

        # Reset button moved; header will host the button next to title
        
        # Tree canvas with scrollbar
        tree_container = tk.Frame(right_frame)
        tree_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        tree_scrollbar_y = tk.Scrollbar(tree_container)
        tree_scrollbar_y.pack(side='right', fill='y')
        
        tree_scrollbar_x = tk.Scrollbar(tree_container, orient='horizontal')
        tree_scrollbar_x.pack(side='bottom', fill='x')
        
        self.tree_canvas = tk.Canvas(
            tree_container,
            bg='white',
            yscrollcommand=tree_scrollbar_y.set,
            xscrollcommand=tree_scrollbar_x.set
        )
        self.tree_canvas.pack(side='left', fill='both', expand=True)
        
        tree_scrollbar_y.config(command=self.tree_canvas.yview)
        tree_scrollbar_x.config(command=self.tree_canvas.xview)
        
        self.draw_board()
    
    def update_depth(self):
        """Update depth from spinbox"""
        if not self.game_started:
            self.depth = self.depth_var.get()
    
    def update_mode(self, event=None):
        """Update mode from combobox"""
        if not self.game_started:
            self.mode = self.mode_var.get()
    
    def update_full_tree(self):
        """Update full tree option"""
        if not self.game_started:
            self.show_full_tree = self.full_tree_var.get()
            if self.show_full_tree and 'expected' in self.mode and self.depth > 4:
                response = messagebox.showwarning(
                    "Performance Warning",
                    f"Showing full tree at depth {self.depth} with expected minimax\n"
                    "may take a very long time and use significant memory.\n\n"
                    "The tree will be built after the AI makes its move.\n\n"
                    "Recommended: Use depth ≤ 4 with full tree option."
                )
    
    def lock_settings(self):
        """Lock settings when game starts"""
        self.depth_spinbox.config(state='disabled')
        self.mode_combo.config(state='disabled')
        self.full_tree_check.config(state='disabled')
    
    def unlock_settings(self):
        """Unlock settings for new game"""
        self.depth_spinbox.config(state='normal')
        self.mode_combo.config(state='readonly')
        self.full_tree_check.config(state='normal')
        
    def restart_game(self):
        """Restart the current game with same settings"""
        self.board = create_board()
        self.current_player = HUMAN
        self.score = {'ai': 0, 'human': 0}
        self.tree_data = None
        self.ai_chosen_col = None
        self.memo = {}
        
        self.update_score()
        self.draw_board()
        self.tree_canvas.delete('all')
        self.ai_choice_label.config(text="")
        
        self.message_label.config(text="Game restarted!\nYour turn")
        self.game_started = True
        self.lock_settings()

    def start_game(self):
        """Start the game (lock settings and begin play)."""
        if self.game_started:
            return

        # Begin using current board and settings
        self.game_started = True
        self.lock_settings()
        self.depth = self.depth_var.get()
        self.mode = self.mode_var.get()
        # Reset memo to be safe
        self.memo = {}

        # If AI is set to move first, schedule AI move
        if self.current_player == AI:
            self.message_label.config(text="AI starting... Thinking...")
            self.root.update()
            self.root.after(500, self.make_ai_move)
        else:
            self.message_label.config(text="Game started!\nYour turn")
    
    def board_to_tuple(self, board):
        """Convert board to hashable tuple for memoization"""
        return tuple(tuple(row) for row in board)
    
    def get_expected_move_fast(self, board, depth, maximizing, alpha, beta, use_prune):
        """Fast expected minimax without tree building - uses memoization"""
        # Create cache key
        board_tuple = self.board_to_tuple(board)
        cache_key = (board_tuple, depth, maximizing, alpha, beta)
        
        if cache_key in self.memo:
            return self.memo[cache_key]
        
        if depth == 0 or is_full(board):
            score = heuristic(board)
            return None, score
        
        valid_moves = get_valid_moves(board)
        
        if maximizing:
            max_val = float('-inf')
            best_move = None
            
            for col in valid_moves:
                outcomes = _chance_outcomes_for_choice(board, col)
                expected_score = 0.0
                
                for actual_col, prob in outcomes:
                    new_board = move_to(board, actual_col, AI)
                    _, score = self.get_expected_move_fast(
                        new_board, depth - 1, False, alpha, beta, use_prune
                    )
                    expected_score += prob * score
                
                if expected_score > max_val:
                    max_val = expected_score
                    best_move = col
                
                if use_prune:
                    alpha = max(alpha, max_val)
                    if alpha >= beta:
                        break
            
            self.memo[cache_key] = (best_move, max_val)
            return best_move, max_val
        else:
            min_val = float('inf')
            best_move = None
            
            for col in valid_moves:
                outcomes = _chance_outcomes_for_choice(board, col)
                expected_score = 0.0
                
                for actual_col, prob in outcomes:
                    new_board = move_to(board, actual_col, HUMAN)
                    _, score = self.get_expected_move_fast(
                        new_board, depth - 1, True, alpha, beta, use_prune
                    )
                    expected_score += prob * score
                
                if expected_score < min_val:
                    min_val = expected_score
                    best_move = col
                
                if use_prune:
                    beta = min(beta, min_val)
                    if alpha >= beta:
                        break
            
            self.memo[cache_key] = (best_move, min_val)
            return best_move, min_val
    
    def build_expected_tree_limited(self, board, depth, maximizing, alpha, beta, use_prune, path=[]):
        """Build expected minimax tree with limited depth for visualization"""
        if depth == 0 or is_full(board):
            return {
                'score': heuristic(board),
                'move': None,
                'type': 'LEAF',
                'path': path,
                'children': [],
                'pruned': False
            }
        
        valid_moves = get_valid_moves(board)
        children = []
        
        if maximizing:
            max_val = float('-inf')
            best_move = None
            
            for col in valid_moves:
                outcomes = _chance_outcomes_for_choice(board, col)
                expected_score = 0.0
                chance_children = []
                
                for actual_col, prob in outcomes:
                    new_board = move_to(board, actual_col, AI)
                    child_tree = self.build_expected_tree_limited(
                        new_board, depth - 1, False, alpha, beta, use_prune,
                        path + [f'Col {col}→{actual_col}({prob:.2f})']
                    )
                    expected_score += prob * child_tree['score']
                    chance_children.append({
                        'actual_col': actual_col,
                        'prob': prob,
                        'tree': child_tree
                    })
                
                children.append({
                    'col': col,
                    'score': expected_score,
                    'type': 'CHANCE',
                    'children': chance_children,
                    'pruned': False
                })
                
                if expected_score > max_val:
                    max_val = expected_score
                    best_move = col
                
                if use_prune:
                    alpha = max(alpha, max_val)
                    if alpha >= beta:
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'children': [],
                                'pruned': True
                            })
                        break
            
            return {
                'score': max_val,
                'move': best_move,
                'type': 'MAX',
                'path': path,
                'children': children,
                'pruned': False
            }
        else:
            # MIN node - deterministic human moves (no CHANCE under MIN)
            min_val = float('inf')
            best_move = None

            for col in valid_moves:
                new_board = move_to(board, col, HUMAN)
                child_tree = self.build_expected_tree_limited(
                    new_board, depth - 1, True, alpha, beta, use_prune,
                    path + [f'Col {col}']
                )
                # attach chosen column for clarity
                child_tree['col'] = col
                children.append(child_tree)

                if child_tree['score'] < min_val:
                    min_val = child_tree['score']
                    best_move = col

                if use_prune:
                    beta = min(beta, min_val)
                    if alpha >= beta:
                        # Mark remaining moves as pruned
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'children': [],
                                'pruned': True
                            })
                        break

            return {
                'score': min_val,
                'move': best_move,
                'type': 'MIN',
                'path': path,
                'children': children,
                'pruned': False
            }
        
    def reset_game(self):
        """Reset to setup screen"""
        self.game_started = False
        self.board = create_board()
        self.tree_data = None
        self.ai_chosen_col = None
        self.draw_board()
        self.tree_canvas.delete('all')
        self.ai_choice_label.config(text="")
        self.tree_info_label.config(text="")
        self.message_label.config(text="Click a column\nto start")
        self.unlock_settings()
        self.update_score()
        
    def draw_board(self):
        """Draw the Connect 4 board"""
        self.canvas.delete('all')
        
        cell_size = 80
        margin = 10
        
        for row in range(ROWS):
            for col in range(COLS):
                x1 = margin + col * cell_size
                y1 = margin + row * cell_size
                x2 = x1 + cell_size - 10
                y2 = y1 + cell_size - 10
                
                cell = self.board[row][col]
                
                if cell == AI:
                    color = self.ai_color
                elif cell == HUMAN:
                    color = self.human_color
                else:
                    color = self.empty_color
                
                self.canvas.create_oval(
                    x1, y1, x2, y2,
                    fill=color,
                    outline='#34495e',
                    width=3
                )
        
    def on_canvas_click(self, event):
        """Handle click on board"""
        if self.current_player != HUMAN:
            return
        
        col = (event.x - 10) // 80
        
        if col < 0 or col >= COLS or not is_valid_move(self.board, col):
            return
        
        # First move starts the game
        if not self.game_started:
            self.game_started = True
            self.lock_settings()
            self.depth = self.depth_var.get()
            self.mode = self.mode_var.get()
        
        self.make_human_move(col)
        
    def make_human_move(self, col):
        """Make human move"""
        self.board = move_to(self.board, col, HUMAN)
        self.draw_board()
        self.update_score()
        
        if is_full(self.board):
            self.end_game()
            return
        
        self.current_player = AI
        self.message_label.config(text="AI is thinking...")
        self.root.update()
        
        # AI move after short delay
        self.root.after(500, self.make_ai_move)
        
    def make_ai_move(self):
        """Make AI move"""
        # Show progress for expected mode with high depth
        if 'expected' in self.mode and self.depth > 3:
            if self.show_full_tree:
                self.message_label.config(text=f"AI computing...\nBuilding full tree\nDepth {self.depth}")
            else:
                self.message_label.config(text=f"AI computing...\nDepth {self.depth}")
            self.root.update()
        
        result = self.get_ai_move()
        
        if result is None:
            self.message_label.config(text="Error in AI move")
            return
        
        move, tree = result
        self.tree_data = tree
        self.ai_chosen_col = move
        
        self.board = move_to(self.board, move, AI)
        self.draw_board()
        self.update_score()
        self.draw_tree()
        
        # Update AI choice label and tree info
        self.ai_choice_label.config(text=f"AI chose Column {move}")
        if 'expected' in self.mode and self.depth > 3 and not self.show_full_tree:
            self.tree_info_label.config(
                text=f"(Computed at depth {self.depth}, showing depth 3 tree)"
            )
        else:
            self.tree_info_label.config(text="")
        
        if is_full(self.board):
            self.end_game()
            return
        
        self.current_player = HUMAN
        self.message_label.config(text="Your turn!\nClick a column")
        
    def get_ai_move(self):
        """Get AI move using selected algorithm"""
        use_prune = 'prune' in self.mode
        use_expected = 'expected' in self.mode
        
        # Clear memoization cache for new move
        self.memo = {}
        
        if use_expected:
            # Check if we should show full tree or limited tree
            if self.show_full_tree or self.depth <= 3:
                # Build full tree
                tree = self.build_expected_tree(
                    self.board, self.depth, True,
                    float('-inf'), float('inf'), use_prune
                )
            else:
                # For expected minimax with depth > 3, use optimized version
                # Get best move using fast algorithm without tree building
                best_move, best_score = self.get_expected_move_fast(
                    self.board, self.depth, True,
                    float('-inf'), float('inf'), use_prune
                )
                # Build shallow tree for visualization (depth 3)
                tree = self.build_expected_tree_limited(
                    self.board, 3, True,
                    float('-inf'), float('inf'), use_prune
                )
                tree['move'] = best_move
                tree['score'] = best_score
        else:
            tree = self.build_minimax_tree(
                self.board, self.depth, True,
                float('-inf'), float('inf'), use_prune
            )
        
        return tree['move'], tree
        
    def build_minimax_tree(self, board, depth, maximizing, alpha, beta, use_prune, path=[]):
        """Build minimax tree with pruning info"""
        if depth == 0 or is_full(board):
            return {
                'score': heuristic(board),
                'move': None,
                'type': 'LEAF',
                'path': path,
                'children': [],
                'pruned': False
            }
        
        valid_moves = get_valid_moves(board)
        children = []
        
        if maximizing:
            max_eval = float('-inf')
            best_move = None
            
            for col in valid_moves:
                new_board = move_to(board, col, AI)
                child_tree = self.build_minimax_tree(
                    new_board, depth - 1, False, alpha, beta, use_prune,
                    path + [f'Col {col}']
                )
                child_tree['col'] = col
                children.append(child_tree)
                
                if child_tree['score'] > max_eval:
                    max_eval = child_tree['score']
                    best_move = col
                
                if use_prune:
                    alpha = max(alpha, max_eval)
                    if alpha >= beta:
                        # Mark remaining moves as pruned
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'path': path + [f'Col {pruned_col}'],
                                'children': [],
                                'pruned': True
                            })
                        break
            
            return {
                'score': max_eval,
                'move': best_move,
                'type': 'MAX',
                'path': path,
                'children': children,
                'pruned': False
            }
        else:
            min_eval = float('inf')
            best_move = None
            
            for col in valid_moves:
                new_board = move_to(board, col, HUMAN)
                child_tree = self.build_minimax_tree(
                    new_board, depth - 1, True, alpha, beta, use_prune,
                    path + [f'Col {col}']
                )
                child_tree['col'] = col
                children.append(child_tree)
                
                if child_tree['score'] < min_eval:
                    min_eval = child_tree['score']
                    best_move = col
                
                if use_prune:
                    beta = min(beta, min_eval)
                    if alpha >= beta:
                        # Mark remaining moves as pruned
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'path': path + [f'Col {pruned_col}'],
                                'children': [],
                                'pruned': True
                            })
                        break
            
            return {
                'score': min_eval,
                'move': best_move,
                'type': 'MIN',
                'path': path,
                'children': children,
                'pruned': False
            }
    
    def build_expected_tree(self, board, depth, maximizing, alpha, beta, use_prune, path=[]):
        """Build expected minimax tree with pruning info"""
        if depth == 0 or is_full(board):
            return {
                'score': heuristic(board),
                'move': None,
                'type': 'LEAF',
                'path': path,
                'children': [],
                'pruned': False
            }
        
        valid_moves = get_valid_moves(board)
        children = []
        
        if maximizing:
            max_val = float('-inf')
            best_move = None
            
            for col in valid_moves:
                outcomes = _chance_outcomes_for_choice(board, col)
                expected_score = 0.0
                chance_children = []
                
                for actual_col, prob in outcomes:
                    new_board = move_to(board, actual_col, AI)
                    child_tree = self.build_expected_tree(
                        new_board, depth - 1, False, alpha, beta, use_prune,
                        path + [f'Col {col}→{actual_col}({prob})']
                    )
                    expected_score += prob * child_tree['score']
                    chance_children.append({
                        'actual_col': actual_col,
                        'prob': prob,
                        'tree': child_tree
                    })
                
                children.append({
                    'col': col,
                    'score': expected_score,
                    'type': 'CHANCE',
                    'children': chance_children,
                    'pruned': False
                })
                
                if expected_score > max_val:
                    max_val = expected_score
                    best_move = col
                
                if use_prune:
                    alpha = max(alpha, max_val)
                    if alpha >= beta:
                        # Mark remaining moves as pruned
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'children': [],
                                'pruned': True
                            })
                        break
            
            return {
                'score': max_val,
                'move': best_move,
                'type': 'MAX',
                'path': path,
                'children': children,
                'pruned': False
            }
        else:
            # MIN node - deterministic human moves (no CHANCE under MIN)
            min_val = float('inf')
            best_move = None

            for col in valid_moves:
                new_board = move_to(board, col, HUMAN)
                child_tree = self.build_expected_tree(
                    new_board, depth - 1, True, alpha, beta, use_prune,
                    path + [f'Col {col}']
                )
                child_tree['col'] = col
                children.append(child_tree)

                if child_tree['score'] < min_val:
                    min_val = child_tree['score']
                    best_move = col

                if use_prune:
                    beta = min(beta, min_val)
                    if alpha >= beta:
                        # Mark remaining moves as pruned
                        remaining_cols = [c for c in valid_moves if c > col]
                        for pruned_col in remaining_cols:
                            children.append({
                                'col': pruned_col,
                                'score': None,
                                'type': 'PRUNED',
                                'children': [],
                                'pruned': True
                            })
                        break

            return {
                'score': min_val,
                'move': best_move,
                'type': 'MIN',
                'path': path,
                'children': children,
                'pruned': False
            }
    
    def draw_tree(self):
        """Draw the decision tree with pruned nodes"""
        self.tree_canvas.delete('all')
        
        if self.tree_data is None:
            return
        
        # Calculate tree dimensions
        node_width = 100
        node_height = 50
        level_height = 80
        
        def count_leaves(node):
            if not node.get('children') or len(node['children']) == 0:
                return 1
            total = 0
            for child in node['children']:
                if 'tree' in child:
                    total += count_leaves(child['tree'])
                else:
                    total += count_leaves(child)
            return total
        
        leaves = count_leaves(self.tree_data)
        tree_width = max(leaves * (node_width + 20), 800)
        tree_height = (self.depth + 1) * level_height + 100
        
        self.tree_canvas.config(scrollregion=(0, 0, tree_width, tree_height))
        
        def draw_node(node, x, y, width):
            if node is None:
                return
            
            node_type = node.get('type', 'LEAF')
            score = node.get('score', 0)
            is_pruned = node.get('pruned', False)
            col = node.get('col')
            
            # Check if this node's column was chosen by AI
            is_chosen = (col is not None and col == self.ai_chosen_col and 
                        node.get('path', []) == [f'Col {col}'])
            
            # Node colors
            if is_pruned or node_type == 'PRUNED':
                fill_color = '#d3d3d3'
                outline_color = '#888888'
                text_color = '#666666'
            elif node_type == 'MAX':
                fill_color = '#ffcccc'
                outline_color = '#e74c3c'
                text_color = 'black'
            elif node_type == 'MIN':
                fill_color = '#cce5ff'
                outline_color = '#3498db'
                text_color = 'black'
            elif node_type == 'CHANCE':
                fill_color = '#fff4cc'
                outline_color = '#f39c12'
                text_color = 'black'
            else:
                fill_color = '#e8e8e8'
                outline_color = '#95a5a6'
                text_color = 'black'
            
            # Highlight chosen path
            if is_chosen:
                outline_color = '#27ae60'
                outline_width = 4
            else:
                outline_width = 2
            
            # Draw node
            self.tree_canvas.create_rectangle(
                x - node_width//2, y - node_height//2,
                x + node_width//2, y + node_height//2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width
            )
            
            # Draw text
            if is_pruned or node_type == 'PRUNED':
                self.tree_canvas.create_text(
                    x, y,
                    text="PRUNED",
                    font=('Arial', 9, 'bold'),
                    fill=text_color
                )
            else:
                self.tree_canvas.create_text(
                    x, y - 12,
                    text=node_type,
                    font=('Arial', 8, 'bold'),
                    fill=text_color
                )
                if score is not None:
                    self.tree_canvas.create_text(
                        x, y + 8,
                        text=f"Score: {score:.1f}",
                        font=('Arial', 8),
                        fill=text_color
                    )
            
            # Draw children
            children = node.get('children', [])
            if children and not is_pruned:
                num_children = len(children)
                child_width = width / num_children
                
                for i, child in enumerate(children):
                    child_x = x - width/2 + child_width/2 + i * child_width
                    child_y = y + level_height
                    
                    child_col = child.get('col')
                    child_is_chosen = (child_col == self.ai_chosen_col and 
                                     len(node.get('path', [])) == 0)
                    
                    # Draw line to child
                    line_color = '#27ae60' if child_is_chosen else '#7f8c8d'
                    line_width = 3 if child_is_chosen else 1
                    
                    self.tree_canvas.create_line(
                        x, y + node_height//2,
                        child_x, child_y - node_height//2,
                        fill=line_color,
                        width=line_width
                    )
                    
                    # Draw column label
                    if child_col is not None:
                        label_color = '#27ae60' if child_is_chosen else '#7f8c8d'
                        label_font = ('Arial', 8, 'bold') if child_is_chosen else ('Arial', 7)
                        self.tree_canvas.create_text(
                            (x + child_x) / 2,
                            (y + child_y) / 2 - 10,
                            text=f"Col {child_col}",
                            font=label_font,
                            fill=label_color
                        )
                    
                    # Recursively draw child
                    if 'tree' in child:
                        draw_node(child['tree'], child_x, child_y, child_width)
                    else:
                        draw_node(child, child_x, child_y, child_width)
        
        # Draw from root
        draw_node(self.tree_data, tree_width // 2, 50, tree_width - 100)
    
    def count_four_in_rows(self):
        """Count number of 4-in-a-rows for each player"""
        ai_count = 0
        human_count = 0
        
        def check_window(window):
            nonlocal ai_count, human_count
            if window.count(AI) == 4 and window.count(EMPTY) == 0:
                ai_count += 1
            if window.count(HUMAN) == 4 and window.count(EMPTY) == 0:
                human_count += 1
        
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [self.board[r][c + i] for i in range(4)]
                check_window(window)
        
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [self.board[r + i][c] for i in range(4)]
                check_window(window)
        
        # Diagonal /
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [self.board[r + i][c + i] for i in range(4)]
                check_window(window)
        
        # Diagonal \
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [self.board[r - i][c + i] for i in range(4)]
                check_window(window)
        
        return {'ai': ai_count, 'human': human_count}
    
    def update_score(self):
        """Update score display"""
        self.score = self.count_four_in_rows()
        
        self.human_score_label.config(text=str(self.score['human']))
        self.ai_score_label.config(text=str(self.score['ai']))
    
    def end_game(self):
        """End the game"""
        self.game_started = False
        
        if self.score['human'] > self.score['ai']:
            winner = "You win! "
        elif self.score['human'] < self.score['ai']:
            winner = "You lose! 🤖"
        else:
            winner = "It's a tie! 🤝"
        
        self.message_label.config(text=f"Game Over!\n{winner}")
        
        messagebox.showinfo(
            "Game Over",
            f"{winner}\n\nFinal Score:\nHuman: {self.score['human']}\nAI: {self.score['ai']}"
        )
        winner=""
        self.unlock_settings()


if __name__ == '__main__':
    root = tk.Tk()
    app = Connect4GUI(root)
    root.mainloop()