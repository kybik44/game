// src/components/Game.tsx
import React, { useState, useCallback, useEffect } from 'react';
import Grid from './Grid';
import Controls from './Controls';
import './Game.css'; // For Game component specific layout styles
import { mockStakeWebService, _resetMockServerBalance } from '../services/StakeWebSDK'; // Import the mock SDK

// Helper to generate a random symbol ID for placeholders
const getRandomSymbol = () => `S${Math.floor(Math.random() * 3) + 1}`;

// Initialize a 4-row, 5-column grid
const generateInitialGrid = (): string[][] => {
  const rows = 4;
  const cols = 5;
  return Array(rows).fill(null).map(() =>
    Array(cols).fill(null).map(() => getRandomSymbol())
  );
};

const Game: React.FC = () => {
  const [gridData, setGridData] = useState<string[][]>(generateInitialGrid());
  const [currentBet, setCurrentBet] = useState<number>(1.00);
  const [balance, setBalance] = useState<number>(0); // Initialized by SDK
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [user, setUser] = useState<string | null>(null);

  // Define bet limits and step (can be moved to config or constants)
  const MIN_BET = 0.10;
  const MAX_BET = 10.00;
  const BET_STEP = 0.10;

  // Initialize session on component mount
  useEffect(() => {
    _resetMockServerBalance(1000.00); // Ensure consistent starting balance for mock
    setIsLoading(true);
    mockStakeWebService.initializeSession()
      .then(sessionData => {
        setBalance(sessionData.balance);
        setUser(sessionData.user);
        console.log("Session initialized for user:", sessionData.user);
      })
      .catch(error => {
        console.error("Failed to initialize session:", error);
        alert("Could not initialize game session. Please try again.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []); // Empty dependency array means this runs once on mount

  const handleSpinClick = useCallback(async () => {
    if (isLoading) {
      console.log("Spin ignored, already loading/spinning.");
      return;
    }
    if (balance < currentBet) {
      alert("Not enough balance to spin!");
      return;
    }

    setIsLoading(true);
    console.log(`Attempting to place bet: ${currentBet}`);

    try {
      const betResponse = await mockStakeWebService.placeBet(currentBet);
      if (betResponse.success && betResponse.newBalance !== undefined) {
        setBalance(betResponse.newBalance); // Update balance after successful bet
        console.log("Bet successful. New balance:", betResponse.newBalance);

        // Simulate the spin animation and outcome determination
        // For now, just randomize the grid after a short delay
        await new Promise(resolve => setTimeout(resolve, 300)); // Simulate spin animation time
        const newGrid = generateInitialGrid();
        setGridData(newGrid);

        // Placeholder: Calculate win amount (replace with actual game logic later)
        let winAmount = 0;
        if (Math.random() > 0.5) { // 50% chance of winning for this mock
          // Simulate a random win amount (e.g., 0.5x to 3x the bet)
          winAmount = parseFloat((currentBet * (Math.random() * 2.5 + 0.5)).toFixed(2));
          console.log(`Mock win calculated: ${winAmount}`);
        } else {
          console.log("Mock spin resulted in no win.");
        }

        // Resolve the spin with the (mock) win amount
        const resolveResponse = await mockStakeWebService.resolveSpin(winAmount);
        if (resolveResponse.success && resolveResponse.newBalance !== undefined) {
          setBalance(resolveResponse.newBalance); // Update balance after win resolution
          console.log("Spin resolved. Final balance:", resolveResponse.newBalance);
          if (winAmount > 0) {
            // alert(`You won: ${winAmount.toFixed(2)}!`); // Optional win alert
          }
        } else {
          console.error("Failed to resolve spin:", resolveResponse.error);
          alert(`Error resolving spin: ${resolveResponse.error}. Please check balance or try again.`);
          // Potentially try to revert bet or fetch balance again if critical
        }

      } else {
        console.error("Failed to place bet:", betResponse.error);
        alert(`Bet failed: ${betResponse.error}`);
        // Refresh balance from SDK in case of desync
        mockStakeWebService.getBalance().then(setBalance);
      }
    } catch (error) {
      console.error("An unexpected error occurred during spin:", error);
      alert("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [balance, currentBet, isLoading]);

  const handleBetIncrease = useCallback(() => {
    if (isLoading) return;
    setCurrentBet(prevBet => {
      const newBet = parseFloat((prevBet + BET_STEP).toFixed(2));
      return newBet <= MAX_BET ? newBet : MAX_BET;
    });
  }, [isLoading]);

  const handleBetDecrease = useCallback(() => {
    if (isLoading) return;
    setCurrentBet(prevBet => {
      const newBet = parseFloat((prevBet - BET_STEP).toFixed(2));
      return newBet >= MIN_BET ? newBet : MIN_BET;
    });
  }, [isLoading]);

  return (
    <div className="game-container-main">
      <header className="game-header">
        <h1>BOMBAROAT™: Tralalero Fury</h1>
        {user && <p className="user-display">Player: {user}</p>}
      </header>
      <Grid gridData={gridData} />
      <Controls
        currentBet={currentBet}
        balance={balance}
        onSpinClick={handleSpinClick}
        onBetIncrease={handleBetIncrease}
        onBetDecrease={handleBetDecrease}
        isLoading={isLoading} // Pass isLoading to Controls
      />
      {isLoading && <div className="loading-overlay">Processing...</div>}
      {/* TODO: Add info display for wins, messages, etc. */}
    </div>
  );
};

export default Game;
