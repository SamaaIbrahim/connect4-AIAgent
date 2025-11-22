"""
Connect4 GUI with selectable AI mode

This gui.py builds on the previous robust GUI and adds an AI-mode selector so
you can choose between the three AI modules in your repo:
- minmax
- minmaxprune
- expectedminmax

Behavior:
- Attempts to import the three AI modules from the repository (importlib import).
- Shows a dropdown (Combo) in the UI to select which AI implementation to use.
- When the GUI asks for an AI move, it calls the selected module using a
  best-effort strategy:
    - First tries module.get_move(board, player, depth)
    - Then tries module.choose_move(board, player, depth)
    - Then tries calling the module itself if it's a callable (module(board, player, depth))
    - Otherwise scans for any callable in the module with 'move' or 'best' in the name
      and attempts to call it with (board, player, depth).
- For search-tree display, it will try module.get_search_tree(board, player, depth)
  or module.get_tree(...) if available; otherwise falls back to the sample tree.
- Works with either PySimpleGUI (if a full install is available) or falls back to a
  Tkinter UI when PySimpleGUI is absent or broken.

Run:
    python gui.py

If you'd like, I can commit this file to your repository and open a PR — tell me
if you want that and I'll prepare the branch and PR.
"""
import importlib
import threading
import time
import random
from typing import Any, Dict, List, Optional, Tuple

# Board constants
BOARD_ROWS = 6
BOARD_COLS = 7
EMPTY = 0
PLAYER_HUMAN = 1
PLAYER_AI = 2

COLOR_MAP = {
    EMPTY: "#1f2630",
    PLAYER_HUMAN: "#ffcc00",
    PLAYER_AI: "#ff4d4d",
}

# Default AI options (module names expected in repo)
AI_OPTIONS = ["minmax", "minmaxprune", "expectedminmax"]

# ---------------------------
# Fallback engine (safe)
# ---------------------------
class FallbackEngine:
    def __init__(self, rows=BOARD_ROWS, cols=BOARD_COLS):
        self.rows = rows
        self.cols = cols
        self.reset()

    def reset(self):
        self.board = [[EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        self.history: List[Tuple[int,int]] = []

    def get_board(self):
        return [row[:] for row in self.board]

    def available_cols(self):
        return [c for c in range(self.cols) if self.board[0][c] == EMPTY]

    def make_move(self, col: int, player: int) -> bool:
        if col < 0 or col >= self.cols or self.board[0][col] != EMPTY:
            return False
        for r in range(self.rows-1, -1, -1):
            if self.board[r][col] == EMPTY:
                self.board[r][col] = player
                self.history.append((col, r))
                return True
        return False

    def undo(self) -> bool:
        if not self.history:
            return False
        col, row = self.history.pop()
        self.board[row][col] = EMPTY
        return True

    def check_winner(self) -> int:
        B = self.board
        R, C = self.rows, self.cols
        dirs = [(0,1),(1,0),(1,1),(1,-1)]
        for r in range(R):
            for c in range(C):
                if B[r][c] == EMPTY:
                    continue
                p = B[r][c]
                for dr,dc in dirs:
                    cnt = 0
                    rr,cc = r,c
                    while 0<=rr<R and 0<=cc<C and B[rr][cc]==p:
                        cnt += 1
                        rr += dr
                        cc += dc
                    if cnt >= 4:
                        return p
        return EMPTY

    def simple_ai_move(self, player: int, depth: int = 1) -> int:
        choices = self.available_cols()
        if not choices:
            return -1
        center = self.cols // 2
        if center in choices:
            return center
        return random.choice(choices)

    def sample_search_tree(self, depth: int = 2) -> Dict[str,Any]:
        def make_node(name, d):
            if d == 0:
                return {"name": name, "eval": round(random.uniform(-1,1),2)}
            children = []
            for i in range(min(3, self.cols)):
                children.append(make_node(f"{name}.{i}", d-1))
            return {"name": name, "eval": round(random.uniform(-1,1),2), "children": children}
        return make_node("root", depth)

# ---------------------------
# Repo detection helpers
# ---------------------------
def try_import_repo_engine() -> Tuple[Optional[Any], Optional[Dict[str, Optional[Any]]]]:
    """
    Try to import a connect4 engine module (common filename 'connect4' or 'game')
    and also import the AI modules listed in AI_OPTIONS. Returns (engine_module or None, ai_modules_dict).
    ai_modules_dict maps module_name -> module object or None if import failed.
    """
    engine_mod = None
    for candidate in ("connect4", "game", "engine"):
        try:
            engine_mod = importlib.import_module(candidate)
            break
        except Exception:
            engine_mod = None
    ai_modules = {}
    for name in AI_OPTIONS:
        try:
            ai_modules[name] = importlib.import_module(name)
        except Exception:
            ai_modules[name] = None
    return engine_mod, ai_modules

def choose_callable_from_module(mod):
    """
    Find a likely callable in the module for picking a move.
    Preference order:
      1) get_move
      2) choose_move
      3) best_move
      4) any callable with 'move' or 'best' in the name
      5) None
    """
    if mod is None:
        return None
    for attr in ("get_move", "choose_move", "best_move", "minimax_move", "select_move"):
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    # scan names
    for name in dir(mod):
        if name.lower().find("move") >= 0 or name.lower().find("best") >= 0:
            fn = getattr(mod, name)
            if callable(fn):
                return fn
    # if module itself is callable (rare), return it
    if callable(mod):
        return mod
    return None

def choose_tree_callable_from_module(mod):
    if mod is None:
        return None
    for attr in ("get_search_tree", "get_tree", "search_tree", "make_tree"):
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    return None

# ---------------------------
# Determine which UI to use
# ---------------------------
USE_PYSIMPLE = False
_try_sg_exc = None
try:
    import PySimpleGUI as sg  # type: ignore
    # Some installs print a message and return a shim object without UI classes.
    if not (hasattr(sg, "Button") and hasattr(sg, "Window") and hasattr(sg, "Combo")):
        raise ImportError("PySimpleGUI installed but missing expected attributes")
    USE_PYSIMPLE = True
except Exception as e:
    _try_sg_exc = e
    USE_PYSIMPLE = False

# ---------------------------
# PySimpleGUI implementation
# ---------------------------
if USE_PYSIMPLE:
    import PySimpleGUI as sg  # re-import for type clarity
    try:
        sg.theme("DarkBlue14")
    except Exception:
        try:
            if hasattr(sg, "ChangeLookAndFeel"):
                sg.ChangeLookAndFeel("DarkBlue14")
        except Exception:
            pass

    class Connect4GUI:
        def __init__(self):
            self.repo_engine, self.ai_modules = try_import_repo_engine()
            if self.repo_engine:
                self.engine = self.repo_engine
                self.using_repo = True
            else:
                self.engine = FallbackEngine()
                self.using_repo = False

            self.current_player = PLAYER_HUMAN
            self.ai_enabled = True
            self.ai_depth = 2
            self.lock = threading.Lock()

            self.board_elem_keys = [[f"cell_{r}_{c}" for c in range(BOARD_COLS)] for r in range(BOARD_ROWS)]
            self.column_btn_keys = [f"col_btn_{c}" for c in range(BOARD_COLS)]

            # selected AI default (choose the first available module or the first option)
            self.selected_ai_name = next((n for n in AI_OPTIONS if self.ai_modules.get(n)), AI_OPTIONS[0])
            self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
            self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
            self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)

            # build UI
            sample_tree = self.engine.sample_search_tree(self.ai_depth) if not self.using_repo else {"name":"root","eval":0,"children":[]}
            # build TreeData if available
            try:
                from PySimpleGUI import TreeData
                td = TreeData()
                def add(node, parent=""):
                    key = node.get("name", f"node_{random.random()}")
                    disp = f"{node.get('name','')} [{node.get('eval','')}]"
                    td.Insert(parent, key, disp, [])
                    for ch in node.get("children",[]) or []:
                        add(ch, key)
                add(sample_tree)
            except Exception:
                td = []

            # column drop row + board rows
            board_grid = []
            board_grid.append([sg.Button("↓", key=self.column_btn_keys[c], size=(4,1)) for c in range(BOARD_COLS)])
            for r in range(BOARD_ROWS):
                row = []
                for c in range(BOARD_COLS):
                    row.append(sg.Button("", key=self.board_elem_keys[r][c], size=(4,2), pad=(1,1)))
                board_grid.append(row)

            # Controls: AI selector
            controls = [
                [sg.Text("AI mode:"), sg.Combo(AI_OPTIONS, default_value=self.selected_ai_name, key="-AI_MODE-", enable_events=True, readonly=True)],
                [sg.Button("Reload AI modules", key="-RELOAD_AI-")],
                [sg.Button("New Game", key="-NEW-"), sg.Button("Undo", key="-UNDO-"), sg.Button("AI Move", key="-AI_MOVE-")],
                [sg.Checkbox("AI enabled (auto)", default=True, key="-AI_ENABLED-", enable_events=True)],
                [sg.Text("AI depth:"), sg.Slider(range=(1, 6), orientation="h", size=(20, 15), default_value=self.ai_depth, key="-AI_DEPTH-", enable_events=True)],
                [sg.Text("", key="-STATUS-", size=(40, 1))]
            ]

            tree_col = [
                [sg.Text("AI Search Tree")],
                [sg.Tree(data=td, headings=[], auto_size_columns=True, num_rows=20, col0_width=40, key="-TREE-", show_expanded=False)]
            ]

            layout = [
                [sg.Column(board_grid, element_justification="center"), sg.VSeparator(), sg.Column(tree_col + controls)]
            ]

            self.window = sg.Window("Connect4 - Modern GUI (AI modes)", layout, finalize=True)
            self.update_board_visual()
            self.set_status("Repo engine detected." if self.using_repo else "Using fallback engine.")

        def reload_ai_modules(self):
            # Reimport ai modules and update selected module/callable
            self.repo_engine, self.ai_modules = try_import_repo_engine()
            self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
            self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
            self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)

        def set_status(self, text: str):
            try:
                self.window["-STATUS-"].update(text)
            except Exception:
                pass

        def get_board_state(self):
            if self.using_repo:
                try:
                    return self.engine.get_board()
                except Exception:
                    if hasattr(self.engine, "board"):
                        return self.engine.board
                    return [[EMPTY]*BOARD_COLS for _ in range(BOARD_ROWS)]
            else:
                return self.engine.get_board()

        def make_move(self, col: int, player: int) -> bool:
            if self.using_repo:
                try:
                    return self.engine.make_move(col, player)
                except Exception:
                    return False
            else:
                return self.engine.make_move(col, player)

        def undo(self) -> bool:
            if self.using_repo:
                try:
                    return self.engine.undo()
                except Exception:
                    return False
            else:
                return self.engine.undo()

        def get_winner(self) -> int:
            if self.using_repo:
                try:
                    return self.engine.get_winner()
                except Exception:
                    try:
                        return self.engine.check_winner()
                    except Exception:
                        return EMPTY
            else:
                return self.engine.check_winner()

        def get_ai_move(self, player: int, depth: int = 2) -> int:
            # Use selected ai callable if possible
            if self.selected_ai_callable:
                try:
                    # many implementations accept (board, player, depth)
                    return int(self.selected_ai_callable(self.get_board_state(), player, depth))
                except TypeError:
                    # maybe (board, depth) or (board) or (board, player)
                    try:
                        return int(self.selected_ai_callable(self.get_board_state(), depth))
                    except Exception:
                        try:
                            return int(self.selected_ai_callable(self.get_board_state()))
                        except Exception:
                            pass
                except Exception:
                    pass
            # fallback: if repo_ai is a module with get_move function (not preselected)
            mod = self.selected_ai_module
            if mod:
                fn = choose_callable_from_module(mod)
                if fn:
                    try:
                        return int(fn(self.get_board_state(), player, depth))
                    except Exception:
                        pass
            # ultimate fallback
            if hasattr(self.engine, "simple_ai_move"):
                return self.engine.simple_ai_move(player, depth)
            choices = [c for c in range(BOARD_COLS) if self.get_board_state()[0][c] == EMPTY]
            return random.choice(choices) if choices else -1

        def get_search_tree(self):
            # try selected tree callable
            if self.selected_tree_callable:
                try:
                    return self.selected_tree_callable(self.get_board_state(), PLAYER_AI, self.ai_depth)
                except Exception:
                    try:
                        return self.selected_tree_callable(self.get_board_state(), self.ai_depth)
                    except Exception:
                        pass
            # fallback
            if hasattr(self.engine, "sample_search_tree"):
                return self.engine.sample_search_tree(self.ai_depth)
            return {"name":"root","eval":0,"children":[]}

        def update_board_visual(self):
            board = self.get_board_state()
            for r in range(BOARD_ROWS):
                for c in range(BOARD_COLS):
                    val = board[r][c]
                    color = COLOR_MAP.get(val, "#222222")
                    key = self.board_elem_keys[r][c]
                    symbol = "●" if val != EMPTY else ""
                    try:
                        self.window[key].update(symbol, button_color=("black", color))
                    except Exception:
                        try:
                            self.window[key].update(symbol)
                        except Exception:
                            pass
            # update tree
            try:
                tree = self.get_search_tree()
                from PySimpleGUI import TreeData
                td = TreeData()
                def add(node, parent=""):
                    key = node.get("name", f"node_{random.random()}")
                    disp = f"{node.get('name','')} [{node.get('eval','')}]"
                    td.Insert(parent, key, disp, [])
                    for ch in node.get("children",[]) or []:
                        add(ch, key)
                add(tree)
                try:
                    self.window["-TREE-"].update(td)
                except Exception:
                    try:
                        self.window["-TREE-"].update(data=td)
                    except Exception:
                        pass
            except Exception:
                pass

        def trigger_ai_move(self):
            def ai_thread():
                with self.lock:
                    if self.get_winner() != EMPTY:
                        return
                    col = self.get_ai_move(PLAYER_AI, self.ai_depth)
                    if col is None or col < 0:
                        return
                    self.make_move(col, PLAYER_AI)
                    self.set_status(f"AI played column {col}")
                    self.update_board_visual()
            threading.Thread(target=ai_thread, daemon=True).start()

        def run(self):
            while True:
                event, values = self.window.read(timeout=100)
                if event == sg.WIN_CLOSED:
                    break
                if event == "-NEW-":
                    if self.using_repo:
                        try:
                            self.engine.reset()
                        except Exception:
                            pass
                    else:
                        self.engine.reset()
                    self.update_board_visual()
                    self.set_status("New game started.")
                elif event == "-UNDO-":
                    ok = self.undo()
                    self.update_board_visual()
                    self.set_status("Undo." if ok else "Nothing to undo.")
                elif event == "-AI_MOVE-":
                    self.trigger_ai_move()
                elif event == "-RELOAD_AI-":
                    self.reload_ai_modules()
                    self.set_status("AI modules reloaded.")
                elif event == "-AI_MODE-":
                    self.selected_ai_name = values["-AI_MODE-"]
                    self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
                    self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
                    self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)
                    self.set_status(f"Selected AI: {self.selected_ai_name}")
                elif event == "-AI_ENABLED-":
                    self.ai_enabled = values["-AI_ENABLED-"]
                    self.set_status(f"AI enabled: {self.ai_enabled}")
                elif event == "-AI_DEPTH-":
                    self.ai_depth = int(values["-AI_DEPTH-"])
                    self.set_status(f"AI depth set to {self.ai_depth}")
                    self.update_board_visual()
                elif isinstance(event, str) and event.startswith("col_btn_"):
                    try:
                        col = int(event.split("_")[-1])
                    except Exception:
                        continue
                    moved = self.make_move(col, PLAYER_HUMAN)
                    if not moved:
                        self.set_status(f"Can't play column {col}")
                    else:
                        self.set_status(f"You played column {col}")
                    self.update_board_visual()
                    if self.ai_enabled and self.get_winner() == EMPTY:
                        self.trigger_ai_move()
                winner = self.get_winner()
                if winner != EMPTY:
                    if winner == PLAYER_HUMAN:
                        self.set_status("Human wins!")
                    else:
                        self.set_status("AI wins!")
            self.window.close()

# ---------------------------
# Tkinter fallback implementation
# ---------------------------
else:
    import tkinter as tk
    from tkinter import ttk

    class Connect4GUI:
        def __init__(self):
            self.repo_engine, self.ai_modules = try_import_repo_engine()
            if self.repo_engine:
                self.engine = self.repo_engine
                self.using_repo = True
            else:
                self.engine = FallbackEngine()
                self.using_repo = False

            self.current_player = PLAYER_HUMAN
            self.ai_enabled = True
            self.ai_depth = 2
            self.lock = threading.Lock()

            # select default ai
            self.selected_ai_name = next((n for n in AI_OPTIONS if self.ai_modules.get(n)), AI_OPTIONS[0])
            self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
            self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
            self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)

            self.root = tk.Tk()
            self.root.title("Connect4 - Fallback Tkinter GUI (AI modes)")
            self.cell_size = 60
            self.margin = 10
            width = BOARD_COLS * self.cell_size + 2*self.margin
            height = (BOARD_ROWS+1) * self.cell_size + 2*self.margin  # +1 for column buttons row

            # Top frame: column buttons
            top_frame = tk.Frame(self.root)
            top_frame.pack(side=tk.TOP, pady=4)
            for c in range(BOARD_COLS):
                b = tk.Button(top_frame, text=str(c), width=4, command=lambda col=c: self.on_column_press(col))
                b.pack(side=tk.LEFT, padx=2)

            # Canvas for board
            self.canvas = tk.Canvas(self.root, width=width, height=height, bg="#0b1220")
            self.canvas.pack(side=tk.LEFT, padx=8, pady=8)
            self.canvas.bind("<Configure>", lambda e: self.redraw_board())

            # Right frame: controls and tree text
            right = tk.Frame(self.root)
            right.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

            # AI mode selector
            tk.Label(right, text="AI mode:").pack(anchor="w")
            self.ai_mode_var = tk.StringVar(value=self.selected_ai_name)
            self.ai_mode_combo = ttk.Combobox(right, values=AI_OPTIONS, textvariable=self.ai_mode_var, state="readonly")
            self.ai_mode_combo.pack(fill=tk.X)
            self.ai_mode_combo.bind("<<ComboboxSelected>>", lambda e: self.on_ai_mode_change())

            tk.Button(right, text="Reload AI modules", command=self.reload_ai_modules).pack(fill=tk.X, pady=2)

            tk.Button(right, text="New Game", command=self.on_new).pack(fill=tk.X, pady=2)
            tk.Button(right, text="Undo", command=self.on_undo).pack(fill=tk.X, pady=2)
            tk.Button(right, text="AI Move", command=self.trigger_ai_move).pack(fill=tk.X, pady=2)
            self.ai_enabled_var = tk.BooleanVar(value=True)
            tk.Checkbutton(right, text="AI enabled (auto)", variable=self.ai_enabled_var, command=self.on_toggle_ai).pack(anchor="w", pady=4)

            tk.Label(right, text="AI depth").pack(anchor="w")
            self.depth_scale = tk.Scale(right, from_=1, to=6, orient=tk.HORIZONTAL, command=self.on_depth_change)
            self.depth_scale.set(self.ai_depth)
            self.depth_scale.pack(fill=tk.X)

            tk.Label(right, text="Status:").pack(anchor="w", pady=(8,0))
            self.status_label = tk.Label(right, text="Using fallback engine." if not self.using_repo else "Repo engine detected.")
            self.status_label.pack(anchor="w", pady=(0,8))

            tk.Label(right, text="AI Search Tree:").pack(anchor="w")
            self.tree_text = tk.Text(right, width=30, height=20)
            self.tree_text.pack(fill=tk.BOTH, expand=True)

            self.redraw_board()

            # If repo engine detected, show message
            if self.using_repo:
                self.set_status("Repo engine detected.")
            else:
                self.set_status("Using fallback engine.")

            # Start periodic UI update (tree updates)
            self.root.after(500, self._periodic_update)

        def reload_ai_modules(self):
            self.repo_engine, self.ai_modules = try_import_repo_engine()
            self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
            self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
            self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)
            self.set_status("AI modules reloaded.")

        def on_ai_mode_change(self):
            self.selected_ai_name = self.ai_mode_var.get()
            self.selected_ai_module = self.ai_modules.get(self.selected_ai_name)
            self.selected_ai_callable = choose_callable_from_module(self.selected_ai_module)
            self.selected_tree_callable = choose_tree_callable_from_module(self.selected_ai_module)
            self.set_status(f"Selected AI: {self.selected_ai_name}")

        def set_status(self, text: str):
            try:
                self.status_label.config(text=text)
            except Exception:
                pass

        def get_board_state(self):
            if self.using_repo:
                try:
                    return self.engine.get_board()
                except Exception:
                    if hasattr(self.engine, "board"):
                        return self.engine.board
                    return [[EMPTY]*BOARD_COLS for _ in range(BOARD_ROWS)]
            else:
                return self.engine.get_board()

        def make_move(self, col:int, player:int)->bool:
            if self.using_repo:
                try:
                    return self.engine.make_move(col, player)
                except Exception:
                    return False
            else:
                return self.engine.make_move(col, player)

        def undo(self)->bool:
            if self.using_repo:
                try:
                    return self.engine.undo()
                except Exception:
                    return False
            else:
                return self.engine.undo()

        def get_winner(self)->int:
            if self.using_repo:
                try:
                    return self.engine.get_winner()
                except Exception:
                    try:
                        return self.engine.check_winner()
                    except Exception:
                        return EMPTY
            else:
                return self.engine.check_winner()

        def get_ai_move(self, player:int, depth:int=2)->int:
            if self.selected_ai_callable:
                try:
                    return int(self.selected_ai_callable(self.get_board_state(), player, depth))
                except TypeError:
                    try:
                        return int(self.selected_ai_callable(self.get_board_state(), depth))
                    except Exception:
                        try:
                            return int(self.selected_ai_callable(self.get_board_state()))
                        except Exception:
                            pass
                except Exception:
                    pass
            mod = self.selected_ai_module
            if mod:
                fn = choose_callable_from_module(mod)
                if fn:
                    try:
                        return int(fn(self.get_board_state(), player, depth))
                    except Exception:
                        pass
            if hasattr(self.engine, "simple_ai_move"):
                return self.engine.simple_ai_move(player, depth)
            choices = [c for c in range(BOARD_COLS) if self.get_board_state()[0][c]==EMPTY]
            return random.choice(choices) if choices else -1

        def get_search_tree(self):
            if self.selected_tree_callable:
                try:
                    return self.selected_tree_callable(self.get_board_state(), PLAYER_AI, self.ai_depth)
                except Exception:
                    try:
                        return self.selected_tree_callable(self.get_board_state(), self.ai_depth)
                    except Exception:
                        pass
            if hasattr(self.engine, "sample_search_tree"):
                return self.engine.sample_search_tree(self.ai_depth)
            return {"name":"root","eval":0,"children":[]}

        def on_column_press(self, col:int):
            moved = self.make_move(col, PLAYER_HUMAN)
            if not moved:
                self.set_status(f"Can't play column {col}")
            else:
                self.set_status(f"You played column {col}")
            self.redraw_board()
            if self.ai_enabled_var.get() and self.get_winner() == EMPTY:
                self.trigger_ai_move()

        def on_new(self):
            if self.using_repo:
                try:
                    self.engine.reset()
                except Exception:
                    pass
            else:
                self.engine.reset()
            self.redraw_board()
            self.set_status("New game started.")

        def on_undo(self):
            ok = self.undo()
            self.redraw_board()
            self.set_status("Undo." if ok else "Nothing to undo.")

        def on_toggle_ai(self):
            self.ai_enabled = self.ai_enabled_var.get()
            self.set_status(f"AI enabled: {self.ai_enabled}")

        def on_depth_change(self, v):
            try:
                self.ai_depth = int(float(v))
            except Exception:
                self.ai_depth = 1
            self.set_status(f"AI depth set to {self.ai_depth}")

        def redraw_board(self):
            self.canvas.delete("all")
            w = BOARD_COLS * self.cell_size
            h = (BOARD_ROWS+1) * self.cell_size
            # background
            self.canvas.create_rectangle(0,0,w+self.margin*2,h+self.margin*2, fill="#0b1220", outline="")
            board = self.get_board_state()
            # draw cells: leave one extra row at top for visuals (buttons)
            for r in range(BOARD_ROWS):
                for c in range(BOARD_COLS):
                    x0 = self.margin + c*self.cell_size
                    y0 = self.margin + (r+1)*self.cell_size
                    x1 = x0 + self.cell_size - 4
                    y1 = y0 + self.cell_size - 4
                    # Draw cell background
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill="#123", outline="#234")
                    val = board[r][c]
                    if val != EMPTY:
                        color = COLOR_MAP.get(val, "#fff")
                        cx = (x0+x1)/2
                        cy = (y0+y1)/2
                        rad = (self.cell_size-14)/2
                        self.canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad, fill=color, outline="")
            # status / winner check
            winner = self.get_winner()
            if winner != EMPTY:
                if winner == PLAYER_HUMAN:
                    self.set_status("Human wins!")
                else:
                    self.set_status("AI wins!")

        def trigger_ai_move(self):
            def ai_thread():
                with self.lock:
                    if self.get_winner() != EMPTY:
                        return
                    col = self.get_ai_move(PLAYER_AI, self.ai_depth)
                    if col is None or col < 0:
                        return
                    self.make_move(col, PLAYER_AI)
                    self.set_status(f"AI played column {col}")
                    self.root.after(1, self.redraw_board)
            threading.Thread(target=ai_thread, daemon=True).start()

        def _periodic_update(self):
            # Update tree text and scheduled redraw
            try:
                tree = self.get_search_tree()
                text = self._format_tree(tree)
                self.tree_text.delete("1.0", tk.END)
                self.tree_text.insert(tk.END, text)
            except Exception:
                pass
            self.root.after(500, self._periodic_update)

        def _format_tree(self, node, depth=0):
            indent = "  " * depth
            s = f"{indent}{node.get('name','')} (eval={node.get('eval','')})\n"
            for ch in node.get("children",[]) or []:
                s += self._format_tree(ch, depth+1)
            return s

        def run(self):
            self.root.mainloop()

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    if USE_PYSIMPLE:
        gui = Connect4GUI()
        gui.run()
    else:
        if _try_sg_exc is not None:
            print("PySimpleGUI could not be used; falling back to Tkinter GUI.")
            print("Original PySimpleGUI import error/exception:", repr(_try_sg_exc))
        gui = Connect4GUI()
        gui.run()