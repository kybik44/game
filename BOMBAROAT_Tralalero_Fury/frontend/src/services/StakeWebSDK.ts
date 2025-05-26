// src/services/StakeWebSDK.ts

interface BookEntryEvent {
  type: string;
  [key: string]: any; // Allow other properties
}
export interface BookEntry {
  id: number;
  payoutMultiplier: number;
  mode: string;
  events: BookEntryEvent[];
  // other mode-specific fields like total_feature_payout for feature books
}

let serverBalance = 1000.00; // Keep a mock server balance for session start
let mockBook: BookEntry[] = [];
const SIMULATED_LATENCY_MS = 500;

// Function to load the mock book (call once)
async function loadMockBook() {
  if (mockBook.length === 0) {
    try {
      console.log("[StakeWebSDK Mock] Attempting to load mock_book.jsonl...");
      const response = await fetch('/mock_book.jsonl'); // Fetches from public folder
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const text = await response.text();
      mockBook = text.trim().split('\n').map(line => {
        try {
          return JSON.parse(line);
        } catch (e) {
          console.error("Failed to parse line in mock_book.jsonl:", line, e);
          return null; // Or handle error appropriately
        }
      }).filter(entry => entry !== null) as BookEntry[]; // Filter out nulls from parse errors
      console.log("[StakeWebSDK Mock] mock_book.jsonl loaded successfully. Entries:", mockBook.length);
      if (mockBook.length === 0) throw new Error("Mock book loaded but is empty.");

    } catch (error) {
      console.error("Failed to load or parse mock_book.jsonl:", error);
      // Fallback to a very simple entry if load fails
      mockBook = [{
        id: 0, 
        payoutMultiplier: 0, 
        mode: "base", 
        events: [
          {type: "reveal", grid: [["L1","L1","L1","L1","L1"],["L1","L1","L1","L1","L1"],["L1","L1","L1","L1","L1"],["L1","L1","L1","L1","L1"]]},
          {type: "winInfo", line_wins: [], scatter_wins: [], total_win_for_spin: 0}
        ]
      }];
      console.log("[StakeWebSDK Mock] Using fallback mock book entry.");
    }
  }
}
// Load on module initialization. Note: top-level await is not used here for broader compatibility.
// The first call to requestSpin might be slightly delayed if fetch is slow.
loadMockBook();


const mockStakeWebService = {
  initializeSession: (): Promise<{ balance: number; user: string }> => {
    console.log("[StakeWebSDK Mock] Initializing session...");
    // Ensure mockBook is loaded before session gives balance, or use a default.
    // For this example, we reset serverBalance here for consistent test runs.
    serverBalance = 1000.00; 
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ balance: serverBalance, user: "MockUser123" });
        console.log("[StakeWebSDK Mock] Session initialized. Balance:", serverBalance);
      }, SIMULATED_LATENCY_MS);
    });
  },

  requestSpin: (betAmount: number, requestedMode?: string): Promise<{ success: boolean; bookEntry?: BookEntry; newBalance?: number; error?: string }> => {
    console.log(`[StakeWebSDK Mock] Requesting spin with bet: ${betAmount}, mode: ${requestedMode || 'base'}`);
    return new Promise((resolve) => {
      setTimeout(async () => {
        if (mockBook.length === 0) {
            console.log("[StakeWebSDK Mock] Mock book not loaded, attempting load...");
            await loadMockBook();
            if (mockBook.length === 0) {
                 console.error("[StakeWebSDK Mock] CRITICAL: Mock book failed to load.");
                 resolve({ success: false, error: "Mock book data not available." });
                 return;
            }
        }

        if (serverBalance < betAmount && requestedMode !== "tralalero_free_spins" && requestedMode !== "bombardino_bonus") { // Bet deduction only for base game spins
          console.warn("[StakeWebSDK Mock] Insufficient funds for bet.");
          resolve({ success: false, error: "Insufficient funds", newBalance: serverBalance });
          return;
        }
        
        let applicableEntries = mockBook;
        if (requestedMode) {
          applicableEntries = mockBook.filter(entry => entry.mode === requestedMode);
          if (applicableEntries.length === 0) {
            console.warn(`[StakeWebSDK Mock] No entries for mode '${requestedMode}'. Falling back to 'base' mode.`);
            applicableEntries = mockBook.filter(entry => entry.mode === "base");
          }
        } else {
          // Default to base game if no mode specified
          applicableEntries = mockBook.filter(entry => entry.mode === "base");
        }

        if (applicableEntries.length === 0) {
          console.error("[StakeWebSDK Mock] No applicable entries in mock book for the request.");
          resolve({ success: false, error: "No suitable game entries in mock book."});
          return;
        }
        
        // Deduct bet only for base game spins that initiate a round.
        // Feature spins (free spins, bonus spins) typically don't deduct further bets.
        if (requestedMode === "base" || !requestedMode) { // Assuming undefined mode is a new base game spin
            serverBalance -= betAmount;
            serverBalance = parseFloat(serverBalance.toFixed(2));
            console.log(`[StakeWebSDK Mock] Bet deducted for base/new spin. Balance before win: ${serverBalance}`);
        } else {
            console.log(`[StakeWebSDK Mock] Bet not deducted for feature spin mode: ${requestedMode}`);
        }
        
        const selectedEntry = applicableEntries[Math.floor(Math.random() * applicableEntries.length)];
        
        // Winnings are always calculated based on the original bet that initiated the round or feature.
        // For feature spins, the `betAmount` parameter to `requestSpin` might be the original triggering bet.
        const winnings = selectedEntry.payoutMultiplier * betAmount; 
        serverBalance += winnings; 
        serverBalance = parseFloat(serverBalance.toFixed(2));
        console.log(`[StakeWebSDK Mock] Winnings applied: ${winnings}. New server balance: ${serverBalance}`);

        resolve({ success: true, bookEntry: selectedEntry, newBalance: serverBalance });
      }, SIMULATED_LATENCY_MS + 200); // Slightly longer latency for spin
    });
  },
  
  getBalance: (): Promise<number> => {
    console.log("[StakeWebSDK Mock] Fetching balance...");
    return new Promise(resolve => setTimeout(() => {
      console.log(`[StakeWebSDK Mock] Current server balance: ${serverBalance}`);
      resolve(serverBalance);
    }, SIMULATED_LATENCY_MS / 2));
  }
};

// Export _resetMockServerBalance for testing if needed, though direct balance mutation should be avoided in components
export const _resetMockServerBalance = (initialBalance = 1000.00) => {
  console.log(`[StakeWebSDK Mock] Test utility: Resetting server balance to ${initialBalance}`);
  serverBalance = initialBalance;
  mockBook = []; // Also clear mockBook to allow reloading if necessary in tests
  loadMockBook(); // Reload
};

export default mockStakeWebService;
