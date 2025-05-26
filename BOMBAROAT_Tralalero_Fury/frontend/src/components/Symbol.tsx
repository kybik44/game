// src/components/Symbol.tsx
import React from 'react';
import './Symbol.css';

interface SymbolProps {
  symbolId: string;
  // Optional: add type or other properties for styling based on symbol later
}

const SymbolDisplay: React.FC<SymbolProps> = ({ symbolId }) => {
  // For now, just display the symbolId. Later, this could be an image or more complex rendering.
  // A real game would have a mapping from symbolId to visual asset.
  // Example: const imageSrc = symbolMap[symbolId]?.image;
  
  // Placeholder for symbol-specific styling or image
  let symbolContent = symbolId;
  let className = "symbol-cell";

  // Example: Different background for different placeholder symbols
  if (symbolId === "S1") {
    // className += " symbol-s1"; // If you add specific styles
    symbolContent = "S1"; // Or an emoji 🍓
  } else if (symbolId === "S2") {
    // className += " symbol-s2";
    symbolContent = "S2"; // Or an emoji 🍋
  } else if (symbolId === "S3") {
    // className += " symbol-s3";
    symbolContent = "S3"; // Or an emoji 🍉
  } else if (!symbolId || symbolId === "") {
    symbolContent = ""; // Empty cell
  }


  return (
    <div className={className} data-symbol-id={symbolId}>
      {symbolContent}
    </div>
  );
};

export default SymbolDisplay;
