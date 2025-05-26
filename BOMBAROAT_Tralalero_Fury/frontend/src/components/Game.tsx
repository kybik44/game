// src/components/Game.tsx
import React, { useState, useCallback, useEffect } from 'react';
import Grid from './Grid';
import Controls from './Controls';
import './Game.css';
import mockStakeWebService, { BookEntry, BookEntryEvent, _resetMockServerBalance } from '../services/StakeWebSDK';

// Initialize a 4-row, 5-column grid with empty strings
const generateInitialGrid = (): string[][] => {
  const rows = 4;
  const cols = 5;
  return Array(rows).fill(null).map(() => Array(cols).fill("")); 
};

const Game: React.FC = () => {
  const [gridData, setGridData] = useState<string[][]>(generateInitialGrid());
  const [currentBet, setCurrentBet] = useState<number>(1.00);
  const [balance, setBalance] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [user, setUser] = useState<string | null>(null);
  
  // New state variables
  const [activeWins, setActiveWins] = useState<any[]>([]); // For line_wins and scatter_wins arrays
  const [gameMode, setGameMode] = useState<string>("base"); // "base", "tralalero_free_spins", "bombardino_bonus"
  const [featureSpinsRemaining, setFeatureSpinsRemaining] = useState<number>(0);
  const [lastWinAmount, setLastWinAmount] = useState<number>(0);
  const [currentTotalFeaturePayout, setCurrentTotalFeaturePayout] = useState<number>(0); // For accumulating feature wins

  const MIN_BET = 0.10;
  const MAX_BET = 10.00;
  const BET_STEP = 0.10;

  useEffect(() => {
    _resetMockServerBalance(1000.00); 
    setIsLoading(true);
    mockStakeWebService.initializeSession()
      .then(sessionData => {
        setBalance(sessionData.balance);
        setUser(sessionData.user);
        console.log("Session initialized for user:", sessionData.user, "Balance:", sessionData.balance);
      })
      .catch(error => {
        console.error("Failed to initialize session:", error);
        alert("Could not initialize game session. Please try again.");
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const processSpinEvents = (bookEntry: BookEntry) => {
    console.log("[Game.tsx] Processing spin events for bookEntry:", bookEntry);
    setActiveWins([]); // Clear previous wins first
    let currentSpinWin = 0;

    for (const event of bookEntry.events) {
      if (event.type === "grid_reveal" && event.grid) { // Updated from "reveal"
        console.log("[Game.tsx] Grid Reveal event, updating grid:", event.grid);
        setGridData(event.grid);
      } else if (event.type === "wins_info" && event.line_wins !== undefined && event.scatter_wins !== undefined) { // Updated from "winInfo"
        console.log("[Game.tsx] Wins Info event:", event);
        const allWins = [...(event.line_wins || []), ...(event.scatter_wins || [])];
        setActiveWins(allWins);
        // total_win_for_spin might be on the event or on the bookEntry directly
        currentSpinWin = event.total_win_for_spin || bookEntry.payoutMultiplier * currentBet; 
        setLastWinAmount(currentSpinWin);
      } else if (event.type === "feature_triggers" && event.features && event.features.length > 0) { // Updated from "triggers"
        console.log("[Game.tsx] Feature Triggers event:", event.features);
        const triggeredFeature = event.features[0]; // Assuming one trigger per spin for now
        alert(`Feature Triggered: ${triggeredFeature.feature_type}`);
        
        if (triggeredFeature.feature_type === "TRALALERO_FREE_SPINS") {
          setGameMode("tralalero_free_spins");
          // The number of spins will be dictated by the feature book entry from SDK
          // For now, we can anticipate this from the trigger event if it provides a count
          // Or wait for the first feature spin's book entry.
          // Let's assume the feature book entry will provide `total_spins_in_feature` or similar.
          // For now, we just set the mode. `featureSpinsRemaining` will be set by the feature book.
          setCurrentTotalFeaturePayout(0); // Reset feature payout accumulator
        } else if (triggeredFeature.feature_type === "BOMBAROAT_BONUS") {
          setGameMode("bombardino_bonus");
          setCurrentTotalFeaturePayout(0); // Reset feature payout accumulator
        }
      }
    }
    // If this is a feature spin, update feature-specific state
    if (bookEntry.mode === "tralalero_free_spins" || bookEntry.mode === "bombardino_bonus") {
        setGameMode(bookEntry.mode); // Ensure gameMode is set to the feature's mode
        setCurrentTotalFeaturePayout(prev => prev + currentSpinWin);

        if (bookEntry.spins_played !== undefined && bookEntry.total_spins_in_feature !== undefined) {
            setFeatureSpinsRemaining(bookEntry.total_spins_in_feature - bookEntry.spins_played);
            if ((bookEntry.total_spins_in_feature - bookEntry.spins_played) <= 0) {
                console.log(`[Game.tsx] ${bookEntry.mode} feature ended. Total payout: ${currentTotalFeaturePayout + currentSpinWin}`);
                // The final payout for the feature is on the feature book entry itself (payoutMultiplier)
                setGameMode("base"); 
                setFeatureSpinsRemaining(0);
                // alert(`${bookEntry.mode} feature ended. Total win: ${ (currentTotalFeaturePayout + currentSpinWin).toFixed(2)}`);
            }
        }
    } else { // If it's a base game spin that didn't trigger a feature
        if (!(bookEntry.events.some(e => e.type === "feature_triggers" && e.features && e.features.length > 0))) {
             setGameMode("base"); // Ensure mode is reset if no trigger
             setFeatureSpinsRemaining(0);
        }
    }
  };

  const handleSpinClick = useCallback(async () => {
    if (isLoading) return;
    
    let effectiveBet = currentBet;
    let modeToRequest = gameMode;

    if (gameMode === "base") {
        if (balance < currentBet) {
            alert("Not enough balance to spin!");
            return;
        }
    } else if (gameMode === "tralalero_free_spins" || gameMode === "bombardino_bonus") {
        if (featureSpinsRemaining <= 0) { // Should not happen if logic is correct, but as a safeguard
            console.log(`[Game.tsx] Attempted feature spin with 0 spins remaining. Resetting to base.`);
            setGameMode("base");
            modeToRequest = "base"; 
            if (balance < currentBet) {
                alert("Not enough balance to start a new base game spin!");
                return;
            }
        } else {
             // For feature spins, the bet amount sent to SDK might be the original triggering bet,
             // or 0 if cost is already handled. Mock SDK now handles no-cost for feature spins.
             effectiveBet = currentBet; // Send original bet for payout calculation reference
        }
    }
    
    setIsLoading(true);
    if (gameMode === "base") setActiveWins([]); // Clear wins only for new base spins

    try {
      // Pass the current gameMode if it's a feature, otherwise SDK defaults to "base"
      const response = await mockStakeWebService.requestSpin(effectiveBet, modeToRequest);
      console.log("[Game.tsx] Spin response from SDK:", response);

      if (response.success && response.bookEntry && response.newBalance !== undefined) {
        setBalance(response.newBalance); 
        processSpinEvents(response.bookEntry); // Process events, this will update grid, wins, mode, featureSpinsRemaining
        setLastSpinResult(response.bookEntry);

      } else {
        console.error("Spin request failed:", response.error);
        alert(`Spin failed: ${response.error || "Unknown error"}`);
        mockStakeWebService.getBalance().then(currentBal => setBalance(currentBal));
      }
    } catch (error) {
      console.error("An unexpected error occurred during spin:", error);
      alert("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [balance, currentBet, isLoading, gameMode, featureSpinsRemaining]);

  const handleBetIncrease = useCallback(() => {
    if (isLoading || gameMode !== "base") return; // Allow bet changes only in base game and not loading
    setCurrentBet(prevBet => {
      const newBet = parseFloat((prevBet + BET_STEP).toFixed(2));
      return newBet <= MAX_BET ? newBet : MAX_BET;
    });
  }, [isLoading, gameMode]);

  const handleBetDecrease = useCallback(() => {
    if (isLoading || gameMode !== "base") return; // Allow bet changes only in base game and not loading
    setCurrentBet(prevBet => {
      const newBet = parseFloat((prevBet - BET_STEP).toFixed(2));
      return newBet >= MIN_BET ? newBet : MIN_BET;
    });
  }, [isLoading, gameMode]);

  return (
    <div className="game-container-main">
      <header className="game-header">
        <h1>BOMBAROAT™: Tralalero Fury</h1>
        {user && <p className="user-display">Player: {user}</p>}
      </header>
      <div className="game-status-display">
        <p>Mode: <span className="value">{gameMode}</span></p>
        {gameMode !== "base" && <p>Feature Spins Left: <span className="value">{featureSpinsRemaining}</span></p>}
        <p>Last Win: <span className="value">{lastWinAmount.toFixed(2)}</span></p>
        {gameMode !== "base" && <p>Total Feature Win: <span className="value">{currentTotalFeaturePayout.toFixed(2)}</span></p>}
      </div>
      <Grid gridData={gridData} activeWins={activeWins} />
      <Controls
        currentBet={currentBet}
        balance={balance}
        onSpinClick={handleSpinClick}
        onBetIncrease={handleBetIncrease}
        onBetDecrease={handleBetDecrease}
        isLoading={isLoading}
        isFeatureActive={gameMode !== "base"} // Disable bet controls during features
      />
      {isLoading && <div className="loading-overlay">Processing...</div>}
      {lastSpinResult && (
        <div className="spin-result-display">
          <h3>Last Spin Result (Debug):</h3>
          <p>ID: {lastSpinResult.id}, Mode: {lastSpinResult.mode}, PayoutMult: {lastSpinResult.payoutMultiplier}x</p>
          <h4>Events:</h4>
          <pre style={{textAlign: 'left', background: '#222', padding: '10px', maxHeight: '200px', overflowY: 'auto'}}>
            {JSON.stringify(lastSpinResult.events, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default Game;
