// src/components/Controls.tsx
import React from 'react';
import './Controls.css';

interface ControlsProps {
  currentBet: number;
  balance: number;
  onSpinClick: () => void;
  onBetIncrease: () => void;
  onBetDecrease: () => void;
  isLoading: boolean; // New prop for loading state
}

const Controls: React.FC<ControlsProps> = ({
  currentBet,
  balance,
  onSpinClick,
  onBetIncrease,
  onBetDecrease,
  isLoading, // Use the isLoading prop
}) => {
  return (
    <div className="controls-container">
      <div className="balance-bet-display">
        <div className="display-item">
          <span>Balance:</span>
          <span className="value">{balance.toFixed(2)}</span>
        </div>
        <div className="display-item">
          <span>Bet:</span>
          <span className="value">{currentBet.toFixed(2)}</span>
        </div>
      </div>

      <div className="bet-adjust-controls">
        <button 
          onClick={onBetDecrease} 
          className="control-button bet-button"
          disabled={isLoading} // Disable if loading
        >
          Bet -
        </button>
        <button 
          onClick={onBetIncrease} 
          className="control-button bet-button"
          disabled={isLoading} // Disable if loading
        >
          Bet +
        </button>
      </div>

      <button 
        onClick={onSpinClick} 
        className="control-button spin-button"
        disabled={isLoading} // Disable if loading
      >
        {isLoading ? 'Spinning...' : 'Spin!'} {/* Change text if loading */}
      </button>
    </div>
  );
};

export default Controls;
