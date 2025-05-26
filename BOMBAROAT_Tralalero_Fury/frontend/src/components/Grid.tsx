// src/components/Grid.tsx
import React from 'react';
import SymbolDisplay from './Symbol'; // Assuming Symbol.tsx is in the same directory
import './Grid.css';

interface GridProps {
  gridData: string[][]; // Expects a 2D array of symbol IDs
}

const Grid: React.FC<GridProps> = ({ gridData }) => {
  if (!gridData || gridData.length === 0 || gridData[0].length === 0) {
    // Handle empty or malformed gridData
    return <div className="grid-container">Loading Grid...</div>;
  }

  // Assuming gridData is [row][col]
  // Number of rows = gridData.length
  // Number of columns = gridData[0].length (assuming all rows have same length)

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
            symbolId={symbolId || ""} // Pass empty string for null/undefined symbols
          />
        ))
      )}
    </div>
  );
};

export default Grid;
