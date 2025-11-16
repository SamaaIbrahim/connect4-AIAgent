import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
from helper import (
    COLS, ROWS, AI, HUMAN, EMPTY,
    is_full, heuristic, is_valid_move,
    get_valid_moves, move_to, create_board
)
from MiniMax import MiniMax as minimax_basic
from MiniMaxprune import MiniMax as minimax_prune
from expectedMinMax import choose_move_expected, _chance_outcomes_for_choice

class Connect4GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Connect 4 AI - Minimax Game Tree Visualizer")
        self.root.configure(bg='#0a0e27')
        
        # Game state
        self.board = create_board()
        self.current_player = HUMAN
        self.game_started = False
        self.algorithm = tk.StringVar(value="minimax")
        self.depth = tk.IntVar(value=4)
        self.ai_thinking = False
        self.last_move = None
        
        # Statistics
        self.nodes_expanded = 0
        self.time_taken = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0e27')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#0a0e27', height=100)
        header_frame.pack(fill=tk.X, pady=(20, 0))
        
        title = tk.Label(header_frame, text="CONNECT 4", 
                        font=('Helvetica', 48, 'bold'),
                        fg='#00d4ff', bg='#0a0e27')
        title.pack()
        
        subtitle = tk.Label(header_frame, text="AI Agent with Minimax Algorithm & Tree Visualization",
                           font=('Helvetica', 13),
                           fg='#8899aa', bg='#0a0e27')
        subtitle.pack()
        
        # Main content with three panels
        content_frame = tk.Frame(main_frame, bg='#0a0e27')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Left panel - Settings and Info
        self.setup_left_panel(content_frame)
        
        # Center panel - Game board
        self.setup_center_panel(content_frame)
        
        # Right panel - Tree Visualization
        self.setup_right_panel(content_frame)
        
    def setup_left_panel(self, parent):
        left_frame = tk.Frame(parent, bg='#0a0e27', width=320)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 15))
        left_frame.pack_propagate(False)
        
        # Settings card
        settings_card = tk.Frame(left_frame, bg='#162447', relief=tk.FLAT, bd=0)
        settings_card.pack(fill=tk.X, pady=(0, 15))
        
        settings_header = tk.Frame(settings_card, bg='#1f4068', height=50)
        settings_header.pack(fill=tk.X)
        
        settings_label = tk.Label(settings_header, text="⚙  Game Settings",
                                 font=('Helvetica', 16, 'bold'),
                                 fg='#ffffff', bg='#1f4068')
        settings_label.pack(pady=12, padx=20, anchor=tk.W)
        
        settings_body = tk.Frame(settings_card, bg='#162447')
        settings_body.pack(fill=tk.BOTH, padx=20, pady=20)
        
        # Algorithm selection
        algo_label = tk.Label(settings_body, text="Algorithm Selection",
                             font=('Helvetica', 11, 'bold'),
                             fg='#ffffff', bg='#162447')
        algo_label.pack(anchor=tk.W, pady=(0, 10))
        
        algorithms = [
            ("Minimax", "minimax"),
            ("Alpha-Beta Pruning", "alphabeta"),
            ("Expected Minimax", "expected")
        ]
        
        self.radio_canvases = []
        for i, (text, value) in enumerate(algorithms):
            radio_frame = tk.Frame(settings_body, bg='#1f4068', relief=tk.FLAT)
            radio_frame.pack(fill=tk.X, pady=4)
            
            radio_canvas = tk.Canvas(radio_frame, width=260, height=40, 
                                    bg='#162447', highlightthickness=0)
            radio_canvas.pack(padx=5, pady=2)
            
            def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
                points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                         x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
                         x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
                return canvas.create_polygon(points, smooth=True, **kwargs)
            
            bg_rect = create_rounded_rect(radio_canvas, 2, 2, 258, 38, radius=18,
                                         fill='#1f4068', outline='')
            
            circle = radio_canvas.create_oval(15, 12, 31, 28, fill='#0a0e27', outline='#00d4ff', width=2)
            inner_circle = radio_canvas.create_oval(18, 15, 28, 25, fill='#0a0e27', outline='')
            text_id = radio_canvas.create_text(45, 20, text=text, anchor=tk.W,
                                              font=('Helvetica', 10), fill='#e0e0e0')
            
            radio_canvas.bg_rect = bg_rect
            radio_canvas.circle = circle
            radio_canvas.inner_circle = inner_circle
            radio_canvas.text_id = text_id
            radio_canvas.value = value
            radio_canvas.selected = (value == self.algorithm.get())
            
            if radio_canvas.selected:
                radio_canvas.itemconfig(bg_rect, fill='#2a5a88')
                radio_canvas.itemconfig(inner_circle, fill='#00d4ff')
            
            def on_radio_click(event, canvas=radio_canvas, val=value):
                self.algorithm.set(val)
                self.update_radio_buttons(settings_body)
            
            radio_canvas.bind('<Button-1>', on_radio_click)
            radio_canvas.bind('<Enter>', lambda e, c=radio_canvas: 
                             c.itemconfig(c.bg_rect, fill='#2a5a88') if not c.selected else None)
            radio_canvas.bind('<Leave>', lambda e, c=radio_canvas: 
                             c.itemconfig(c.bg_rect, fill='#1f4068') if not c.selected else None)
            radio_canvas.config(cursor='hand2')
            
            self.radio_canvases.append(radio_canvas)
        
        # Depth slider
        depth_label = tk.Label(settings_body, text="Search Depth",
                              font=('Helvetica', 11, 'bold'),
                              fg='#ffffff', bg='#162447')
        depth_label.pack(anchor=tk.W, pady=(20, 5))
        
        depth_value_frame = tk.Frame(settings_body, bg='#1f4068', relief=tk.FLAT)
        depth_value_frame.pack(fill=tk.X, pady=5)
        
        depth_canvas = tk.Canvas(depth_value_frame, height=60, bg='#162447', highlightthickness=0)
        depth_canvas.pack(fill=tk.X)
        
        def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
            points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                     x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
                     x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, smooth=True, **kwargs)
        
        create_rounded_rect(depth_canvas, 5, 5, 255, 55, radius=15, fill='#1f4068', outline='')
        
        self.depth_label = tk.Label(depth_canvas, text=f"K = {self.depth.get()}",
                                    font=('Helvetica', 20, 'bold'),
                                    fg='#00d4ff', bg='#1f4068')
        depth_canvas.create_window(130, 30, window=self.depth_label)
        
        slider_frame = tk.Frame(settings_body, bg='#162447')
        slider_frame.pack(fill=tk.X, pady=(5, 0))
        
        depth_slider = tk.Scale(slider_frame, from_=1, to=6, 
                               variable=self.depth,
                               orient=tk.HORIZONTAL,
                               font=('Helvetica', 9),
                               fg='#ffffff', bg='#1f4068',
                               troughcolor='#0a0e27',
                               activebackground='#00d4ff',
                               highlightthickness=0,
                               showvalue=False,
                               cursor='hand2',
                               length=240,
                               sliderlength=30,
                               sliderrelief=tk.FLAT,
                               command=self.update_depth_label)
        depth_slider.pack(pady=(5, 10))
        
        depth_info = tk.Label(settings_body, text="⚠  Higher depth = More computation time",
                             font=('Helvetica', 8, 'italic'),
                             fg='#8899aa', bg='#162447')
        depth_info.pack(anchor=tk.W)
        
        # Control buttons
        btn_frame = tk.Frame(settings_body, bg='#162447')
        btn_frame.pack(fill=tk.X, pady=(25, 10))
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Start.TButton',
                       font=('Helvetica', 12, 'bold'),
                       foreground='#ffffff',
                       background='#06c270',
                       borderwidth=0,
                       focuscolor='none',
                       padding=15,
                       relief=tk.FLAT)
        style.map('Start.TButton',
                 background=[('active', '#05a85e'), ('disabled', '#555555')])
        
        style.configure('Reset.TButton',
                       font=('Helvetica', 12, 'bold'),
                       foreground='#ffffff',
                       background='#e63946',
                       borderwidth=0,
                       focuscolor='none',
                       padding=15,
                       relief=tk.FLAT)
        style.map('Reset.TButton',
                 background=[('active', '#d62839'), ('disabled', '#555555')])
        
        self.start_btn = ttk.Button(btn_frame, text="▶  START GAME",
                                    command=self.start_game,
                                    style='Start.TButton',
                                    cursor='hand2')
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.reset_btn = ttk.Button(btn_frame, text="↻  RESET GAME",
                                    command=self.reset_game,
                                    style='Reset.TButton',
                                    cursor='hand2',
                                    state=tk.DISABLED)
        self.reset_btn.pack(fill=tk.X, pady=5)
        
        # Game Status card
        status_card = tk.Canvas(left_frame, bg='#0a0e27', highlightthickness=0, height=380)
        status_card.pack(fill=tk.X, pady=(0, 15))
        
        def create_rounded_rect(canvas, x1, y1, x2, y2, radius=20, **kwargs):
            points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                     x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2,
                     x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, smooth=True, **kwargs)
        
        create_rounded_rect(status_card, 2, 2, 318, 378, radius=20, fill='#162447', outline='')
        create_rounded_rect(status_card, 2, 2, 318, 52, radius=20, fill='#1f4068', outline='')
        status_card.create_rectangle(2, 32, 318, 52, fill='#1f4068', outline='')
        
        status_card.create_text(20, 27, text="📊  Game Status",
                               font=('Helvetica', 16, 'bold'),
                               fill='#ffffff', anchor=tk.W)
        
        # Current turn container
        turn_container_canvas = tk.Canvas(status_card, bg='#162447', highlightthickness=0,
                                         width=280, height=90)
        status_card.create_window(160, 115, window=turn_container_canvas)
        
        create_rounded_rect(turn_container_canvas, 2, 2, 278, 88, radius=15, 
                           fill='#1f4068', outline='')
        
        turn_container_canvas.create_text(140, 25, text="Current Turn",
                                         font=('Helvetica', 10),
                                         fill='#8899aa')
        
        self.turn_label_widget = turn_container_canvas.create_text(140, 55, 
                                                                   text="Not Started",
                                                                   font=('Helvetica', 16, 'bold'),
                                                                   fill='#ffffff')
        self.turn_canvas = turn_container_canvas
        
        # Heuristic value container
        heur_container_canvas = tk.Canvas(status_card, bg='#162447', highlightthickness=0,
                                         width=280, height=90)
        status_card.create_window(160, 215, window=heur_container_canvas)
        
        create_rounded_rect(heur_container_canvas, 2, 2, 278, 88, radius=15,
                           fill='#1f4068', outline='')
        
        heur_container_canvas.create_text(140, 25, text="Board Heuristic",
                                         font=('Helvetica', 10),
                                         fill='#8899aa')
        
        self.heur_label_widget = heur_container_canvas.create_text(140, 55,
                                                                   text="0.0",
                                                                   font=('Helvetica', 20, 'bold'),
                                                                   fill='#00d4ff')
        self.heur_canvas = heur_container_canvas
        
        # AI Statistics container
        stats_container_canvas = tk.Canvas(status_card, bg='#162447', highlightthickness=0,
                                          width=280, height=90)
        status_card.create_window(160, 315, window=stats_container_canvas)
        
        create_rounded_rect(stats_container_canvas, 2, 2, 278, 88, radius=15,
                           fill='#1f4068', outline='')
        
        stats_container_canvas.create_text(140, 20, text="Last AI Move",
                                          font=('Helvetica', 10),
                                          fill='#8899aa')
        
        self.stats_label_widget = stats_container_canvas.create_text(140, 55,
                                                                     text="Waiting for first move...",
                                                                     font=('Helvetica', 9),
                                                                     fill='#e0e0e0',
                                                                     width=250)
        self.stats_canvas = stats_container_canvas
        
    def update_radio_buttons(self, settings_body):
        """Update radio button visual states"""
        current_value = self.algorithm.get()
        for canvas in self.radio_canvases:
            if canvas.value == current_value:
                canvas.selected = True
                canvas.itemconfig(canvas.bg_rect, fill='#2a5a88')
                canvas.itemconfig(canvas.inner_circle, fill='#00d4ff')
            else:
                canvas.selected = False
                canvas.itemconfig(canvas.bg_rect, fill='#1f4068')
                canvas.itemconfig(canvas.inner_circle, fill='#0a0e27')
    
    def setup_center_panel(self, parent):
        center_frame = tk.Frame(parent, bg='#0a0e27')
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15)
        
        # Board card
        board_card = tk.Frame(center_frame, bg='#162447', relief=tk.FLAT)
        board_card.pack(expand=True)
        
        board_header = tk.Frame(board_card, bg='#1f4068')
        board_header.pack(fill=tk.X)
        
        board_label = tk.Label(board_header, text="🎮  Game Board",
                              font=('Helvetica', 16, 'bold'),
                              fg='#ffffff', bg='#1f4068')
        board_label.pack(pady=12)
        
        # Column indicators
        col_indicator_frame = tk.Frame(board_card, bg='#162447')
        col_indicator_frame.pack(pady=(15, 5))
        
        self.col_indicators = []
        for col in range(COLS):
            indicator = tk.Label(col_indicator_frame, text='▼',
                                font=('Helvetica', 16),
                                fg='#162447', bg='#162447',
                                width=4)
            indicator.grid(row=0, column=col, padx=2)
            self.col_indicators.append(indicator)
        
        # Game board
        board_container = tk.Frame(board_card, bg='#2874a6', relief=tk.FLAT, bd=0)
        board_container.pack(padx=20, pady=(0, 20))
        
        self.board_frame = tk.Frame(board_container, bg='#2874a6', padx=15, pady=15)
        self.board_frame.pack()
        
        # Create board slots
        self.buttons = []
        for row in range(ROWS):
            button_row = []
            for col in range(COLS):
                btn = tk.Canvas(self.board_frame, width=70, height=70,
                               bg='#2874a6', highlightthickness=0)
                btn.grid(row=row, column=col, padx=4, pady=4)
                
                btn.create_oval(5, 5, 65, 65, fill='#0a0e27', outline='#1f4068', width=2)
                btn.circle_id = btn.create_oval(5, 5, 65, 65, fill='#0a0e27', outline='')
                
                btn.bind('<Button-1>', lambda e, c=col: self.human_move(c))
                btn.bind('<Enter>', lambda e, c=col: self.on_hover_enter(c))
                btn.bind('<Leave>', lambda e, c=col: self.on_hover_leave(c))
                
                btn.col = col
                btn.enabled = False
                
                button_row.append(btn)
            self.buttons.append(button_row)
        
        # Legend
        legend_frame = tk.Frame(board_card, bg='#162447')
        legend_frame.pack(pady=(10, 20))
        
        human_frame = tk.Frame(legend_frame, bg='#162447')
        human_frame.pack(side=tk.LEFT, padx=25)
        
        human_circle = tk.Canvas(human_frame, width=30, height=30, 
                                bg='#162447', highlightthickness=0)
        human_circle.pack(side=tk.LEFT, padx=(0, 8))
        human_circle.create_oval(2, 2, 28, 28, fill='#e63946', outline='#ff4d5a', width=2)
        
        human_label = tk.Label(human_frame, text="YOU (O)", 
                              font=('Helvetica', 11, 'bold'),
                              fg='#e63946', bg='#162447')
        human_label.pack(side=tk.LEFT)
        
        ai_frame = tk.Frame(legend_frame, bg='#162447')
        ai_frame.pack(side=tk.LEFT, padx=25)
        
        ai_circle = tk.Canvas(ai_frame, width=30, height=30,
                             bg='#162447', highlightthickness=0)
        ai_circle.pack(side=tk.LEFT, padx=(0, 8))
        ai_circle.create_oval(2, 2, 28, 28, fill='#00a8ff', outline='#00d4ff', width=2)
        
        ai_label = tk.Label(ai_frame, text="AI (X)",
                           font=('Helvetica', 11, 'bold'),
                           fg='#00a8ff', bg='#162447')
        ai_label.pack(side=tk.LEFT)
        
    def setup_right_panel(self, parent):
        right_frame = tk.Frame(parent, bg='#0a0e27', width=500)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(15, 0))
        right_frame.pack_propagate(False)
        
        # Tree visualization card
        tree_card = tk.Frame(right_frame, bg='#162447', relief=tk.FLAT)
        tree_card.pack(fill=tk.BOTH, expand=True)
        
        tree_header = tk.Frame(tree_card, bg='#1f4068')
        tree_header.pack(fill=tk.X)
        
        tree_label = tk.Label(tree_header, text="🌳  Minimax Tree Visualization",
                             font=('Helvetica', 16, 'bold'),
                             fg='#ffffff', bg='#1f4068')
        tree_label.pack(pady=12, padx=20, anchor=tk.W)
        
        tree_body = tk.Frame(tree_card, bg='#162447')
        tree_body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ScrolledText widget for tree display
        self.tree_text = scrolledtext.ScrolledText(tree_body,
                                                   bg='#0a0e27',
                                                   fg='#e0e0e0',
                                                   font=('Courier', 9),
                                                   wrap=tk.NONE,
                                                   relief=tk.FLAT,
                                                   padx=10,
                                                   pady=10)
        self.tree_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.tree_text.tag_config('max', foreground='#00d4ff', font=('Courier', 9, 'bold'))
        self.tree_text.tag_config('min', foreground='#e63946', font=('Courier', 9, 'bold'))
        self.tree_text.tag_config('move', foreground='#8899aa')
        self.tree_text.tag_config('score', foreground='#00ff88', font=('Courier', 9, 'bold'))
        self.tree_text.tag_config('pruned', foreground='#ff9900', font=('Courier', 9, 'italic'))
        
    def on_hover_enter(self, col):
        if self.game_started and self.current_player == HUMAN and not self.ai_thinking:
            if is_valid_move(self.board, col):
                self.col_indicators[col].config(fg='#e63946')
                
    def on_hover_leave(self, col):
        self.col_indicators[col].config(fg='#162447')
        
    def update_depth_label(self, value):
        self.depth_label.config(text=f"K = {value}")
        
    def start_game(self):
        self.game_started = True
        self.current_player = HUMAN
        self.start_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.NORMAL)
        
        # Enable board
        for row in range(ROWS):
            for col in range(COLS):
                if is_valid_move(self.board, col):
                    self.buttons[row][col].enabled = True
                    self.buttons[row][col].config(cursor='hand2')
        
        self.update_turn_display()
        self.display_tree_header()
        
    def reset_game(self):
        self.board = create_board()
        self.current_player = HUMAN
        self.game_started = False
        self.last_move = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.DISABLED)
        
        # Reset board display
        for row in range(ROWS):
            for col in range(COLS):
                canvas = self.buttons[row][col]
                canvas.itemconfig(canvas.circle_id, fill='#0a0e27', outline='')
                canvas.enabled = False
                canvas.config(cursor='')
        
        for indicator in self.col_indicators:
            indicator.config(fg='#162447')
        
        self.turn_canvas.itemconfig(self.turn_label_widget, text="Not Started", fill='#ffffff')
        self.heur_canvas.itemconfig(self.heur_label_widget, text="0.0", fill='#00d4ff')
        self.stats_canvas.itemconfig(self.stats_label_widget, text="Waiting for first move...")
        self.tree_text.delete(1.0, tk.END)
        
    def human_move(self, col):
        if not self.game_started or self.current_player != HUMAN or self.ai_thinking:
            return
        
        if not is_valid_move(self.board, col):
            return
        
        self.board = move_to(self.board, col, HUMAN)
        self.last_move = (col, HUMAN)
        self.update_board_display()
        
        self.col_indicators[col].config(fg='#162447')
        
        if is_full(self.board):
            self.game_over()
            return
        
        self.current_player = AI
        self.update_turn_display()
        self.root.after(800, self.ai_move)
        
    def ai_move(self):
        self.ai_thinking = True
        
        for col in range(COLS):
            self.col_indicators[col].config(fg='#162447')
        
        self.root.update()
        
        start_time = time.time()
        
        algo = self.algorithm.get()
        depth = self.depth.get()
        
        # Build and display tree
        self.tree_text.delete(1.0, tk.END)
        self.display_tree_header()
        
        if algo == "minimax":
            score, move = self.minimax_with_tree(self.board, depth, True, False)
        elif algo == "alphabeta":
            score, move = self.minimax_with_tree(self.board, depth, True, True)
        else:  # expected
            # For expected minimax, use lower depth (it's much slower)
            expected_depth = min(depth, 3)  # Cap at 3 for performance
            move, score = choose_move_expected(self.board, expected_depth)
            # Display simplified tree for expected minimax
            self.display_expected_tree_simplified(self.board, move, score, expected_depth)
        
        end_time = time.time()
        self.time_taken = (end_time - start_time) * 1000
        
        if move is not None:
            self.board = move_to(self.board, move, AI)
            self.last_move = (move, AI)
            self.update_board_display()
            
            stats_text = f"Column: {move + 1}\nScore: {score:.2f}\nTime: {self.time_taken:.0f}ms\nDepth: {depth}"
            self.stats_canvas.itemconfig(self.stats_label_widget, text=stats_text)
        
        self.ai_thinking = False
        
        if is_full(self.board):
            self.game_over()
            return
        
        self.current_player = HUMAN
        self.update_turn_display()
        
    def minimax_with_tree(self, board, depth, maximizing, use_pruning, 
                          alpha=-float('inf'), beta=float('inf'), 
                          level=0, parent_move=None, node_name="ROOT"):
        
        # Display current node
        if level == 0:
            self.tree_text.insert(tk.END, f"\n{'MAX' if maximizing else 'MIN'}: {node_name}\n", 
                                 'max' if maximizing else 'min')
        
        # Terminal node
        if depth == 0 or is_full(board):
            h = heuristic(board)
            if parent_move is not None:
                indent = "    " * level
                self.tree_text.insert(tk.END, f"{indent}└─ ", 'move')
                self.tree_text.insert(tk.END, f"[{h:.0f}]", 'score')
                self.tree_text.insert(tk.END, "\n")
            return h, None
        
        valid_moves = get_valid_moves(board)
        
        if maximizing:
            max_eval = -float('inf')
            best_move = None
            
            # Display node label if not root
            if level > 0:
                indent = "    " * (level - 1)
                self.tree_text.insert(tk.END, f"\n{indent}{'MAX' if maximizing else 'MIN'}: {node_name}\n", 
                                     'max' if maximizing else 'min')
            
            # Explore children
            for i, col in enumerate(valid_moves):
                new_board = move_to(board, col, AI)
                child_name = chr(65 + i) if level == 0 else f"{node_name}{chr(65 + i)}"
                
                # Display connection
                indent = "    " * level
                connector = "├─ " if i < len(valid_moves) - 1 else "└─ "
                self.tree_text.insert(tk.END, f"{indent}{connector}", 'move')
                self.tree_text.insert(tk.END, f"{child_name}", 'move')
                
                eval_score, _ = self.minimax_with_tree(new_board, depth - 1, False, 
                                                       use_pruning, alpha, beta, 
                                                       level + 1, col, child_name)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = col
                
                if use_pruning:
                    alpha = max(alpha, eval_score)
                    if alpha >= beta:
                        if i < len(valid_moves) - 1:
                            self.tree_text.insert(tk.END, f" [PRUNED α={alpha:.0f} β={beta:.0f}]", 'pruned')
                        break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            
            # Display node label if not root
            if level > 0:
                indent = "    " * (level - 1)
                self.tree_text.insert(tk.END, f"\n{indent}{'MAX' if maximizing else 'MIN'}: {node_name}\n", 
                                     'max' if maximizing else 'min')
            
            # Explore children
            for i, col in enumerate(valid_moves):
                new_board = move_to(board, col, HUMAN)
                child_name = chr(65 + i) if level == 0 else f"{node_name}{chr(65 + i)}"
                
                # Display connection
                indent = "    " * level
                connector = "├─ " if i < len(valid_moves) - 1 else "└─ "
                self.tree_text.insert(tk.END, f"{indent}{connector}", 'move')
                self.tree_text.insert(tk.END, f"{child_name}", 'move')
                
                eval_score, _ = self.minimax_with_tree(new_board, depth - 1, True,
                                                       use_pruning, alpha, beta,
                                                       level + 1, col, child_name)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = col
                
                if use_pruning:
                    beta = min(beta, eval_score)
                    if alpha >= beta:
                        if i < len(valid_moves) - 1:
                            self.tree_text.insert(tk.END, f" [PRUNED α={alpha:.0f} β={beta:.0f}]", 'pruned')
                        break
            
            return min_eval, best_move
    
    def expected_minimax_with_tree(self, board, depth, level=0, parent_move=None, is_chance=False):
        indent = "    " * level
        
        if level == 0:
            self.tree_text.insert(tk.END, "\nROOT: Expected MAX\n", 'max')
        
        if depth == 0 or is_full(board):
            h = heuristic(board)
            if parent_move is not None:
                self.tree_text.insert(tk.END, f"{indent}└─ ", 'move')
                self.tree_text.insert(tk.END, f"[{h:.0f}]", 'score')
                self.tree_text.insert(tk.END, "\n")
            return h, None
        
        valid_moves = get_valid_moves(board)
        
        max_val = -float('inf')
        best_move = None
        
        for i, col in enumerate(valid_moves):
            outcomes = _chance_outcomes_for_choice(board, col)
            expected = 0
            
            connector = "├─ " if i < len(valid_moves) - 1 else "└─ "
            self.tree_text.insert(tk.END, f"{indent}{connector}", 'move')
            self.tree_text.insert(tk.END, f"Try Col {col+1} [CHANCE]", 'move')
            self.tree_text.insert(tk.END, "\n")
            
            for j, (outcome_col, prob) in enumerate(outcomes):
                new_board = move_to(board, outcome_col, AI)
                
                sub_indent = indent + ("│   " if i < len(valid_moves) - 1 else "    ")
                sub_connector = "├─ " if j < len(outcomes) - 1 else "└─ "
                self.tree_text.insert(tk.END, f"{sub_indent}{sub_connector}", 'move')
                self.tree_text.insert(tk.END, f"→ Col {outcome_col+1} (p={prob:.1f})", 'move')
                
                # Min level for human
                min_score = self.expected_min_with_tree(new_board, depth - 1, level + 2)
                expected += prob * min_score
                
                self.tree_text.insert(tk.END, f" = {min_score:.1f}\n", 'score')
            
            sub_indent = indent + ("│   " if i < len(valid_moves) - 1 else "    ")
            self.tree_text.insert(tk.END, f"{sub_indent}→ ", 'score')
            self.tree_text.insert(tk.END, f"Expected: {expected:.2f}\n", 'score')
            
            if expected > max_val:
                max_val = expected
                best_move = col
        
        return best_move, max_val
    
    def display_expected_tree_simplified(self, board, chosen_move, score, depth):
        """Display simplified tree for expected minimax showing the chosen move path"""
        self.tree_text.insert(tk.END, "\nROOT: Expected MAX (AI)\n", 'max')
        self.tree_text.insert(tk.END, f"Search Depth: {depth}\n\n", 'move')
        
        valid_moves = get_valid_moves(board)
        
        for i, col in enumerate(valid_moves):
            connector = "├─ " if i < len(valid_moves) - 1 else "└─ "
            self.tree_text.insert(tk.END, f"{connector}", 'move')
            
            if col == chosen_move:
                self.tree_text.insert(tk.END, f"Col {col+1} ★ CHOSEN", 'score')
                self.tree_text.insert(tk.END, f" [E={score:.2f}]\n", 'score')
                
                # Show chance outcomes for chosen move
                outcomes = _chance_outcomes_for_choice(board, col)
                for j, (outcome_col, prob) in enumerate(outcomes):
                    sub_connector = "│   ├─ " if j < len(outcomes) - 1 else "│   └─ "
                    if i == len(valid_moves) - 1:
                        sub_connector = "    ├─ " if j < len(outcomes) - 1 else "    └─ "
                    
                    self.tree_text.insert(tk.END, f"{sub_connector}", 'move')
                    self.tree_text.insert(tk.END, f"Outcome: Col {outcome_col+1}", 'move')
                    self.tree_text.insert(tk.END, f" (p={prob:.1f})\n", 'score')
                    
                    # Show it leads to MIN layer
                    sub_indent = "│   │   " if j < len(outcomes) - 1 else "│   "
                    if i == len(valid_moves) - 1:
                        sub_indent = "    │   " if j < len(outcomes) - 1 else "    "
                    self.tree_text.insert(tk.END, f"{sub_indent}└─ MIN layer (Human)\n", 'min')
            else:
                self.tree_text.insert(tk.END, f"Col {col+1}\n", 'move')
        
        self.tree_text.insert(tk.END, "\n→ ", 'score')
        self.tree_text.insert(tk.END, f"Best Expected Value: {score:.2f}\n", 'score')
        self.tree_text.insert(tk.END, f"→ Chosen Column: {chosen_move + 1}\n", 'score')
        
        # Add note about depth capping
        if depth < self.depth.get():
            self.tree_text.insert(tk.END, f"\n⚠ Note: Expected Minimax depth capped at {depth} for performance\n", 'pruned')
    
    def expected_min_with_tree(self, board, depth, level):
        if depth == 0 or is_full(board):
            return heuristic(board)
        
        min_val = float('inf')
        for col in get_valid_moves(board):
            new_board = move_to(board, col, HUMAN)
            outcomes = _chance_outcomes_for_choice(new_board, col)
            expected = 0
            
            for outcome_col, prob in outcomes:
                new_board2 = move_to(new_board, outcome_col, AI)
                score = self.expected_min_with_tree(new_board2, depth - 1, level + 1)
                expected += prob * score
            
            min_val = min(min_val, expected)
        
        return min_val
    
    def display_tree_header(self):
        self.tree_text.insert(tk.END, "═" * 60 + "\n", 'score')
        self.tree_text.insert(tk.END, "  MINIMAX GAME TREE\n", 'max')
        self.tree_text.insert(tk.END, "═" * 60 + "\n", 'score')
        self.tree_text.insert(tk.END, f"  Algorithm: ", 'move')
        algo_name = {"minimax": "MINIMAX", "alphabeta": "ALPHA-BETA PRUNING", 
                     "expected": "EXPECTED MINIMAX"}
        self.tree_text.insert(tk.END, f"{algo_name[self.algorithm.get()]}\n", 'score')
        self.tree_text.insert(tk.END, f"  Search Depth: ", 'move')
        self.tree_text.insert(tk.END, f"{self.depth.get()}\n", 'score')
        self.tree_text.insert(tk.END, "═" * 60 + "\n\n", 'score')
        
    def update_board_display(self):
        for row in range(ROWS):
            for col in range(COLS):
                canvas = self.buttons[row][col]
                cell = self.board[row][col]
                
                if cell == HUMAN:
                    canvas.itemconfig(canvas.circle_id, fill='#e63946', outline='#ff4d5a', width=3)
                    if self.last_move and self.last_move[0] == col and self.last_move[1] == HUMAN:
                        canvas.itemconfig(canvas.circle_id, outline='#ffffff', width=4)
                elif cell == AI:
                    canvas.itemconfig(canvas.circle_id, fill='#00a8ff', outline='#00d4ff', width=3)
                    if self.last_move and self.last_move[0] == col and self.last_move[1] == AI:
                        canvas.itemconfig(canvas.circle_id, outline='#ffffff', width=4)
                else:
                    canvas.itemconfig(canvas.circle_id, fill='#0a0e27', outline='')
        
        # Update heuristic
        h = heuristic(self.board)
        self.heur_canvas.itemconfig(self.heur_label_widget, text=f"{h:.2f}")
        
        if h > 100:
            self.heur_canvas.itemconfig(self.heur_label_widget, fill='#00ff88')
        elif h > 0:
            self.heur_canvas.itemconfig(self.heur_label_widget, fill='#00d4ff')
        elif h < -100:
            self.heur_canvas.itemconfig(self.heur_label_widget, fill='#ff4d5a')
        elif h < 0:
            self.heur_canvas.itemconfig(self.heur_label_widget, fill='#e63946')
        else:
            self.heur_canvas.itemconfig(self.heur_label_widget, fill='#ffffff')
        
    def update_turn_display(self):
        if self.current_player == HUMAN:
            self.turn_canvas.itemconfig(self.turn_label_widget, text="YOUR TURN", fill='#e63946')
        else:
            if self.ai_thinking:
                self.turn_canvas.itemconfig(self.turn_label_widget, text="AI THINKING...", fill='#00d4ff')
            else:
                self.turn_canvas.itemconfig(self.turn_label_widget, text="AI TURN", fill='#00a8ff')
        
    def game_over(self):
        h = heuristic(self.board)
        
        # Disable all buttons
        for row in range(ROWS):
            for col in range(COLS):
                self.buttons[row][col].enabled = False
                self.buttons[row][col].config(cursor='')
        
        for indicator in self.col_indicators:
            indicator.config(fg='#162447')
        
        # Determine winner
        if h > 0:
            result = "🏆 AI WINS!"
            msg = f"AI wins with a heuristic score of {h:.2f}"
            color = "#00d4ff"
        elif h < 0:
            result = "🎉 YOU WIN!"
            msg = f"You win with a heuristic score of {h:.2f}"
            color = "#e63946"
        else:
            result = "🤝 DRAW!"
            msg = "The game ended in a draw!"
            color = "#ffd700"
        
        self.turn_canvas.itemconfig(self.turn_label_widget, text="GAME OVER", fill=color)
        
        # Add to tree display
        self.tree_text.insert(tk.END, "\n" + "═" * 60 + "\n", 'score')
        self.tree_text.insert(tk.END, f"  {result}\n", 'score')
        self.tree_text.insert(tk.END, f"  Final Heuristic: {h:.2f}\n", 'score')
        self.tree_text.insert(tk.END, "═" * 60 + "\n", 'score')
        
        messagebox.showinfo("Game Over", msg)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1600x900")
    root.resizable(True, True)
    root.minsize(1400, 800)
    app = Connect4GUI(root)
    root.mainloop()