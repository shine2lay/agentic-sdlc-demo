import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTicTacToeConfig } from '../api';

function checkWinner(board: string[][]): string | null {
  const size = board.length;
  // Check rows
  for (let r = 0; r < size; r++) {
    if (board[r][0] !== '' && board[r].every(c => c === board[r][0])) {
      return board[r][0];
    }
  }
  // Check columns
  for (let c = 0; c < size; c++) {
    if (board[0][c] !== '' && board.every(row => row[c] === board[0][c])) {
      return board[0][c];
    }
  }
  // Check diagonals
  if (board[0][0] !== '' && board.every((row, i) => row[i] === board[0][0])) {
    return board[0][0];
  }
  if (board[0][size - 1] !== '' && board.every((row, i) => row[size - 1 - i] === board[0][size - 1])) {
    return board[0][size - 1];
  }
  return null;
}

export function TicTacToePage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['tictactoe-config'],
    queryFn: fetchTicTacToeConfig,
  });

  const [board, setBoard] = useState<string[][]>(
    Array(3).fill(null).map(() => Array(3).fill(''))
  );
  const [currentPlayer, setCurrentPlayer] = useState(0);
  const [winner, setWinner] = useState<string | null>(null);
  const [isDraw, setIsDraw] = useState(false);

  if (isLoading) return <div className="flex items-center justify-center h-full">Loading...</div>;
  if (isError || !config) return <div className="flex items-center justify-center h-full">Failed to load game config.</div>;

  function handleCellClick(row: number, col: number) {
    if (winner !== null || isDraw || board[row][col] !== '') return;
    const newBoard = board.map(r => [...r]);
    newBoard[row][col] = config!.player_symbols[currentPlayer];
    setBoard(newBoard);
    const result = checkWinner(newBoard);
    if (result) {
      setWinner(result);
    } else if (newBoard.every(r => r.every(c => c !== ''))) {
      setIsDraw(true);
    } else {
      setCurrentPlayer(currentPlayer === 0 ? 1 : 0);
    }
  }

  function resetGame() {
    setBoard(Array(3).fill(null).map(() => Array(3).fill('')));
    setCurrentPlayer(0);
    setWinner(null);
    setIsDraw(false);
  }

  function getSymbolColor(symbol: string): string {
    const idx = config!.player_symbols.indexOf(symbol);
    return idx >= 0 ? config!.player_colors[idx] : 'inherit';
  }

  return (
    <div className="flex flex-col items-center justify-center h-full overflow-auto p-4">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] mb-4">{config.title}</h1>
      <div className="text-lg text-[var(--temper-text-muted)] mb-4">
        {winner ? (
          <span>Winner: <span style={{ color: getSymbolColor(winner) }}>{winner}</span>!</span>
        ) : isDraw ? (
          <span>Draw!</span>
        ) : (
          <span>Turn: <span style={{ color: getSymbolColor(config.player_symbols[currentPlayer]) }}>{config.player_symbols[currentPlayer]}</span></span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-1 mb-4" style={{ width: '192px', height: '192px' }}>
        {board.map((row, rIdx) =>
          row.map((cell, cIdx) => (
            <button
              key={`${rIdx}-${cIdx}`}
              className="w-16 h-16 text-2xl font-bold bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded cursor-pointer hover:bg-[var(--temper-border)] disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center"
              disabled={winner !== null || isDraw || cell !== ''}
              onClick={() => handleCellClick(rIdx, cIdx)}
              aria-label={cell ? `${cell} at row ${rIdx + 1} column ${cIdx + 1}` : `Empty cell row ${rIdx + 1} column ${cIdx + 1}`}
              style={{ color: getSymbolColor(cell) }}
            >
              {cell}
            </button>
          ))
        )}
      </div>
      <button
        className="px-4 py-2 bg-[var(--temper-accent)] text-white rounded hover:opacity-90"
        onClick={resetGame}
      >
        Reset
      </button>
    </div>
  );
}
