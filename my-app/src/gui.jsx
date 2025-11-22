import React, { useState, useEffect } from 'react';
import { Play, RotateCcw, Settings, Eye, EyeOff, Cpu, User } from 'lucide-react';

const ROWS = 6;
const COLS = 7;
const AI = 'X';
const HUMAN = 'O';
const EMPTY = '.';

// Helper functions
const createBoard = () => Array(ROWS).fill(null).map(() => Array(COLS).fill(EMPTY));

const isValidMove = (board, col) => col >= 0 && col < COLS && board[0][col] === EMPTY;

const getValidMoves = (board) => {
  const moves = [];
  for (let col = 0; col < COLS; col++) {
    if (isValidMove(board, col)) moves.push(col);
  }
  return moves;
};

const moveTo = (board, col, player) => {
  const newBoard = board.map(row => [...row]);
  for (let r = ROWS - 1; r >= 0; r--) {
    if (newBoard[r][col] === EMPTY) {
      newBoard[r][col] = player;
      break;
    }
  }
  return newBoard;
};

const heuristic = (board) => {
  let score = 0;
  
  const scoreWindow = (win) => {
    const aiCount = win.filter(c => c === AI).length;
    const huCount = win.filter(c => c === HUMAN).length;
    if (aiCount > 0 && huCount > 0) return 0;
    const weights = {0: 0, 1: 1, 2: 10, 3: 100, 4: 100000};
    if (aiCount > 0) return weights[aiCount];
    if (huCount > 0) return -weights[huCount];
    return 0;
  };

  const centerCol = Math.floor(COLS / 2);
  const centerCount = board.filter(row => row[centerCol] === AI).length;
  score += centerCount * 3;

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      const window = [board[r][c], board[r][c+1], board[r][c+2], board[r][c+3]];
      score += scoreWindow(window);
    }
  }

  for (let c = 0; c < COLS; c++) {
    for (let r = 0; r < ROWS - 3; r++) {
      const window = [board[r][c], board[r+1][c], board[r+2][c], board[r+3][c]];
      score += scoreWindow(window);
    }
  }

  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      const window = [board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3]];
      score += scoreWindow(window);
    }
  }

  for (let r = 3; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      const window = [board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3]];
      score += scoreWindow(window);
    }
  }

  return score;
};

// Minimax algorithms
const minimax = (board, depth, maximizing, alpha = -Infinity, beta = Infinity, usePruning = false) => {
  if (depth === 0 || getValidMoves(board).length === 0) {
    return { score: heuristic(board), move: null, nodes: 1 };
  }

  const validMoves = getValidMoves(board);
  let nodes = 1;

  if (maximizing) {
    let maxEval = -Infinity;
    let bestMove = null;

    for (const col of validMoves) {
      const newBoard = moveTo(board, col, AI);
      const result = minimax(newBoard, depth - 1, false, alpha, beta, usePruning);
      nodes += result.nodes;

      if (result.score > maxEval) {
        maxEval = result.score;
        bestMove = col;
      }

      if (usePruning) {
        alpha = Math.max(alpha, maxEval);
        if (alpha >= beta) break;
      }
    }

    return { score: maxEval, move: bestMove, nodes };
  } else {
    let minEval = Infinity;
    let bestMove = null;

    for (const col of validMoves) {
      const newBoard = moveTo(board, col, HUMAN);
      const result = minimax(newBoard, depth - 1, true, alpha, beta, usePruning);
      nodes += result.nodes;

      if (result.score < minEval) {
        minEval = result.score;
        bestMove = col;
      }

      if (usePruning) {
        beta = Math.min(beta, minEval);
        if (alpha >= beta) break;
      }
    }

    return { score: minEval, move: bestMove, nodes };
  }
};

const chanceOutcomes = (board, chosenCol) => {
  const outcomes = [];
  outcomes.push({ col: chosenCol, prob: 0.6 });

  const leftValid = chosenCol - 1 >= 0 && isValidMove(board, chosenCol - 1);
  const rightValid = chosenCol + 1 < COLS && isValidMove(board, chosenCol + 1);

  if (leftValid && rightValid) {
    outcomes.push({ col: chosenCol - 1, prob: 0.2 });
    outcomes.push({ col: chosenCol + 1, prob: 0.2 });
  } else if (leftValid) {
    outcomes.push({ col: chosenCol - 1, prob: 0.4 });
  } else if (rightValid) {
    outcomes.push({ col: chosenCol + 1, prob: 0.4 });
  }

  return outcomes;
};

const expectedMinimax = (board, depth, maximizing) => {
  if (depth === 0 || getValidMoves(board).length === 0) {
    return { score: heuristic(board), move: null, nodes: 1 };
  }

  const validMoves = getValidMoves(board);
  let nodes = 1;

  if (maximizing) {
    let maxVal = -Infinity;
    let bestMove = null;

    for (const col of validMoves) {
      const outcomes = chanceOutcomes(board, col);
      let expectedScore = 0;

      for (const outcome of outcomes) {
        const newBoard = moveTo(board, outcome.col, AI);
        const result = expectedMinimax(newBoard, depth - 1, false);
        nodes += result.nodes;
        expectedScore += outcome.prob * result.score;
      }

      if (expectedScore > maxVal) {
        maxVal = expectedScore;
        bestMove = col;
      }
    }

    return { score: maxVal, move: bestMove, nodes };
  } else {
    let minVal = Infinity;
    let bestMove = null;

    for (const col of validMoves) {
      const newBoard = moveTo(board, col, HUMAN);
      const result = expectedMinimax(newBoard, depth - 1, true);
      nodes += result.nodes;

      if (result.score < minVal) {
        minVal = result.score;
        bestMove = col;
      }
    }

    return { score: minVal, move: bestMove, nodes };
  }
};

const Connect4Game = () => {
  const [board, setBoard] = useState(createBoard());
  const [gameStarted, setGameStarted] = useState(false);
  const [algorithm, setAlgorithm] = useState('minimax');
  const [usePruning, setUsePruning] = useState(false);
  const [depth, setDepth] = useState(5);
  const [currentPlayer, setCurrentPlayer] = useState(HUMAN);
  const [gameLog, setGameLog] = useState([]);
  const [showSettings, setShowSettings] = useState(true);
  const [showLog, setShowLog] = useState(false);
  const [aiThinking, setAiThinking] = useState(false);
  const [lastMove, setLastMove] = useState(null);

  const resetGame = () => {
    setBoard(createBoard());
    setCurrentPlayer(HUMAN);
    setGameLog([]);
    setLastMove(null);
    setGameStarted(false);
    setShowSettings(true);
  };

  const startGame = () => {
    setGameStarted(true);
    setShowSettings(false);
    addLog('Game started! You are O (Red), AI is X (Yellow)');
  };

  const addLog = (message) => {
    setGameLog(prev => [...prev, { time: new Date().toLocaleTimeString(), message }]);
  };

  const handleHumanMove = (col) => {
    if (!gameStarted || currentPlayer !== HUMAN || !isValidMove(board, col) || aiThinking) return;

    const newBoard = moveTo(board, col, HUMAN);
    setBoard(newBoard);
    setLastMove({ col, player: HUMAN });
    setCurrentPlayer(AI);
    addLog(`You placed disc in column ${col + 1}`);
  };

  useEffect(() => {
    if (currentPlayer === AI && gameStarted && !aiThinking) {
      setAiThinking(true);
      
      setTimeout(() => {
        const startTime = performance.now();
        let result;

        if (algorithm === 'expected') {
          result = expectedMinimax(board, depth, true);
          addLog(`Expected Minimax: Col ${result.move + 1}, Score: ${result.score.toFixed(2)}, Nodes: ${result.nodes}`);
        } else {
          result = minimax(board, depth, true, -Infinity, Infinity, usePruning);
          const algName = usePruning ? 'Alpha-Beta Pruning' : 'Minimax';
          addLog(`${algName}: Col ${result.move + 1}, Score: ${result.score.toFixed(2)}, Nodes: ${result.nodes}`);
        }

        const endTime = performance.now();
        addLog(`AI computed in ${(endTime - startTime).toFixed(2)}ms`);

        if (result.move !== null) {
          const newBoard = moveTo(board, result.move, AI);
          setBoard(newBoard);
          setLastMove({ col: result.move, player: AI });
          setCurrentPlayer(HUMAN);
          addLog(`AI placed disc in column ${result.move + 1}`);
        }

        setAiThinking(false);
      }, 500);
    }
  }, [currentPlayer, gameStarted, aiThinking]);

  const isGameOver = getValidMoves(board).length === 0;
  const boardHeuristic = heuristic(board);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 flex items-center justify-center">
      <div className="max-w-7xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-red-500 mb-2">
            Connect 4 AI
          </h1>
          <p className="text-gray-300 text-lg">Minimax Algorithm Implementation</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Panel */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/30 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Settings className="w-6 h-6 text-purple-400" />
                  Settings
                </h2>
                {gameStarted && (
                  <button
                    onClick={() => setShowSettings(!showSettings)}
                    className="p-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 transition-colors"
                  >
                    {showSettings ? <EyeOff className="w-5 h-5 text-purple-300" /> : <Eye className="w-5 h-5 text-purple-300" />}
                  </button>
                )}
              </div>

              {(!gameStarted || showSettings) && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-3">Algorithm</label>
                    <div className="space-y-2">
                      {[
                        { value: 'minimax', label: 'Minimax' },
                        { value: 'alphabeta', label: 'Alpha-Beta Pruning' },
                        { value: 'expected', label: 'Expected Minimax' }
                      ].map(opt => (
                        <button
                          key={opt.value}
                          onClick={() => {
                            setAlgorithm(opt.value);
                            if (opt.value === 'alphabeta') setUsePruning(true);
                            else if (opt.value === 'minimax') setUsePruning(false);
                          }}
                          disabled={gameStarted}
                          className={`w-full p-3 rounded-xl font-medium transition-all ${
                            (algorithm === opt.value || (opt.value === 'alphabeta' && usePruning && algorithm === 'minimax'))
                              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                              : 'bg-slate-700/50 text-gray-300 hover:bg-slate-700'
                          } ${gameStarted ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-3">
                      Depth (K): {depth}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="8"
                      value={depth}
                      onChange={(e) => setDepth(parseInt(e.target.value))}
                      disabled={gameStarted}
                      className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>Fast</span>
                      <span>Deep</span>
                    </div>
                  </div>

                  {!gameStarted ? (
                    <button
                      onClick={startGame}
                      className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2"
                    >
                      <Play className="w-5 h-5" />
                      Start Game
                    </button>
                  ) : (
                    <button
                      onClick={resetGame}
                      className="w-full bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2"
                    >
                      <RotateCcw className="w-5 h-5" />
                      Reset Game
                    </button>
                  )}
                </div>
              )}

              {/* Game Info */}
              {gameStarted && (
                <div className="mt-6 space-y-4">
                  <div className="bg-slate-900/50 rounded-xl p-4 border border-purple-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-400 text-sm">Current Turn</span>
                      {currentPlayer === HUMAN ? (
                        <User className="w-5 h-5 text-red-400" />
                      ) : (
                        <Cpu className="w-5 h-5 text-yellow-400" />
                      )}
                    </div>
                    <div className={`text-2xl font-bold ${currentPlayer === HUMAN ? 'text-red-400' : 'text-yellow-400'}`}>
                      {currentPlayer === HUMAN ? 'Your Turn' : aiThinking ? 'AI Thinking...' : 'AI Turn'}
                    </div>
                  </div>

                  <div className="bg-slate-900/50 rounded-xl p-4 border border-purple-500/20">
                    <div className="text-gray-400 text-sm mb-2">Board Heuristic</div>
                    <div className={`text-2xl font-bold ${boardHeuristic > 0 ? 'text-green-400' : boardHeuristic < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                      {boardHeuristic.toFixed(2)}
                    </div>
                  </div>

                  {isGameOver && (
                    <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4 text-center">
                      <div className="text-white font-bold text-xl">Game Over!</div>
                      <div className="text-white/90 text-sm mt-1">
                        {boardHeuristic > 0 ? 'AI Wins!' : boardHeuristic < 0 ? 'You Win!' : 'Draw!'}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Game Board */}
          <div className="lg:col-span-2">
            <div className="bg-gradient-to-b from-blue-600 to-blue-800 rounded-3xl p-8 shadow-2xl border-4 border-blue-900">
              <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${COLS}, 1fr)` }}>
                {board[0].map((_, colIndex) => (
                  <button
                    key={`hover-${colIndex}`}
                    onClick={() => handleHumanMove(colIndex)}
                    disabled={!gameStarted || currentPlayer !== HUMAN || !isValidMove(board, colIndex) || aiThinking}
                    className={`h-12 rounded-t-xl transition-all ${
                      gameStarted && currentPlayer === HUMAN && isValidMove(board, colIndex) && !aiThinking
                        ? 'bg-red-400/30 hover:bg-red-400/50 cursor-pointer'
                        : 'bg-blue-900/30 cursor-not-allowed'
                    }`}
                  >
                    {gameStarted && currentPlayer === HUMAN && isValidMove(board, colIndex) && !aiThinking && (
                      <div className="w-full h-full flex items-center justify-center">
                        <div className="w-10 h-10 rounded-full bg-red-500 opacity-50"></div>
                      </div>
                    )}
                  </button>
                ))}

                {board.map((row, rowIndex) =>
                  row.map((cell, colIndex) => (
                    <div
                      key={`${rowIndex}-${colIndex}`}
                      className={`aspect-square rounded-full transition-all ${
                        lastMove && lastMove.col === colIndex && 
                        board[rowIndex][colIndex] === lastMove.player
                          ? 'ring-4 ring-white animate-pulse'
                          : ''
                      } ${
                        cell === EMPTY
                          ? 'bg-slate-900'
                          : cell === HUMAN
                          ? 'bg-gradient-to-br from-red-400 to-red-600 shadow-lg shadow-red-500/50'
                          : 'bg-gradient-to-br from-yellow-400 to-yellow-600 shadow-lg shadow-yellow-500/50'
                      }`}
                    />
                  ))
                )}
              </div>

              <div className="flex justify-center gap-8 mt-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-600 shadow-lg"></div>
                  <span className="text-white font-semibold">You (O)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 shadow-lg"></div>
                  <span className="text-white font-semibold">AI (X)</span>
                </div>
              </div>
            </div>

            {/* Game Log */}
            {gameStarted && (
              <div className="mt-6 bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/30 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white">Game Log</h3>
                  <button
                    onClick={() => setShowLog(!showLog)}
                    className="text-purple-400 hover:text-purple-300 transition-colors"
                  >
                    {showLog ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {showLog && (
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {gameLog.slice().reverse().map((log, idx) => (
                      <div key={idx} className="bg-slate-900/50 rounded-lg p-3 text-sm">
                        <span className="text-purple-400 font-mono">{log.time}</span>
                        <span className="text-gray-300 ml-3">{log.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Connect4Game;