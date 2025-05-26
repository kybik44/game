// src/components/Grid.tsx
import React from 'react';
import SymbolDisplay from './Symbol';
import './Grid.css';

interface WinCoordinate {
  r: number;
  c: number;
}
interface ActiveWin {
  // For line wins
  line_coordinates?: WinCoordinate[] | [number, number][]; // Array of [row, col] or {r, c}
  // For scatter wins (if we want to highlight them on the grid)
  positions?: WinCoordinate[] | [number, number][]; 
  symbol_id?: string; // To highlight specific scatter symbols
  // Add other properties if needed from your win objects
}

interface GridProps {
  gridData: string[][];
  activeWins?: ActiveWin[]; // Array of win objects
}

const Grid: React.FC<GridProps> = ({ gridData, activeWins = [] }) => {
  if (!gridData || gridData.length === 0 || gridData[0].length === 0) {
    return <div className="grid-container">Loading Grid...</div>;
  }

  const isCellWinning = (rowIndex: number, colIndex: number): boolean => {
    if (!activeWins || activeWins.length === 0) {
      return false;
    }

    for (const win of activeWins) {
      // Check line wins
      if (win.line_coordinates) {
        for (const coord of win.line_coordinates) {
          // Handle both [r, c] and {r, c} formats for coordinates
          if (Array.isArray(coord) && coord[0] === rowIndex && coord[1] === colIndex) {
            return true;
          } else if (!Array.isArray(coord) && coord.r === rowIndex && coord.c === colIndex) {
            return true;
          }
        }
      }
      // Check scatter wins (if positions are provided for highlighting)
      if (win.positions && win.symbol_id === gridData[rowIndex][colIndex]) {
         for (const coord of win.positions) {
            if (Array.isArray(coord) && coord[0] === rowIndex && coord[1] === colIndex) {
              return true;
            } else if (!Array.isArray(coord) && coord.r === rowIndex && coord.c === colIndex) {
              return true;
            }
          }
      }
    }
    return false;
  };

  return (
    <div 
      className="grid-container"
      style={{
        gridTemplateRows: `repeat(${gridData.length}, 1fr)`,
        gridTemplateColumns: `repeat(${gridData[0].length}, 1fr)`,
      }}
    >
      {gridData.map((row, rowIndex) =>
        row.map((symbolId, colIndex) => (
          <SymbolDisplay
            key={`${rowIndex}-${colIndex}`}
            symbolId={symbolId || ""}
            isWinning={isCellWinning(rowIndex, colIndex)} // Pass isWinning prop
          />
        ))
      )}
    </div>
  );
};

export default Grid;
