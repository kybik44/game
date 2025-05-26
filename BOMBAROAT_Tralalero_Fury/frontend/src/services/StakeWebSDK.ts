// src/services/StakeWebSDK.ts

// Simulate a server-side balance for the mock service
let serverBalance = 1000.00;
const SIMULATED_LATENCY_MS = 500; // 0.5 seconds

interface SessionData {
  balance: number;
  user: string;
  // Add other session-related data if needed
}

interface BetResponse {
  success: boolean;
  newBalance?: number;
  error?: string;
}

interface SpinResolveResponse {
  success: boolean;
  newBalance?: number;
  error?: string;
}

export const mockStakeWebService = {
  initializeSession: (): Promise<SessionData> => {
    console.log("[StakeWebSDK Mock] Initializing session...");
    return new Promise((resolve) => {
      setTimeout(() => {
        const sessionData: SessionData = {
          balance: serverBalance,
          user: "MockUser123",
        };
        console.log("[StakeWebSDK Mock] Session initialized:", sessionData);
        resolve(sessionData);
      }, SIMULATED_LATENCY_MS);
    });
  },

  placeBet: (betAmount: number): Promise<BetResponse> => {
    console.log(`[StakeWebSDK Mock] Placing bet: ${betAmount}`);
    return new Promise((resolve) => {
      setTimeout(() => {
        if (betAmount <= 0) {
          console.error("[StakeWebSDK Mock] Bet amount must be positive.");
          resolve({ success: false, error: "Bet amount must be positive." });
          return;
        }
        if (serverBalance >= betAmount) {
          serverBalance -= betAmount;
          serverBalance = parseFloat(serverBalance.toFixed(2));
          console.log(`[StakeWebSDK Mock] Bet successful. New server balance: ${serverBalance}`);
          resolve({ success: true, newBalance: serverBalance });
        } else {
          console.warn("[StakeWebSDK Mock] Insufficient balance for bet.");
          resolve({ success: false, error: "Insufficient balance." });
        }
      }, SIMULATED_LATENCY_MS);
    });
  },

  // In a real slot, winAmount is determined by the server after the spin outcome is known.
  // For this mock, the frontend will calculate a win and then "report" it here.
  resolveSpin: (winAmount: number): Promise<SpinResolveResponse> => {
    console.log(`[StakeWebSDK Mock] Resolving spin with win: ${winAmount}`);
    return new Promise((resolve) => {
      setTimeout(() => {
        if (winAmount < 0) {
          console.error("[StakeWebSDK Mock] Win amount cannot be negative.");
          resolve({ success: false, error: "Win amount cannot be negative." });
          return;
        }
        serverBalance += winAmount;
        serverBalance = parseFloat(serverBalance.toFixed(2));
        console.log(`[StakeWebSDK Mock] Spin resolved. New server balance: ${serverBalance}`);
        resolve({ success: true, newBalance: serverBalance });
      }, SIMULATED_LATENCY_MS);
    });
  },

  getBalance: (): Promise<number> => {
    console.log("[StakeWebSDK Mock] Fetching balance...");
    return new Promise((resolve) => {
      setTimeout(() => {
        console.log(`[StakeWebSDK Mock] Current server balance: ${serverBalance}`);
        resolve(serverBalance);
      }, SIMULATED_LATENCY_MS / 2); // Faster for balance checks
    });
  },
};

// Example of how to potentially reset mock state if needed for testing, not part of SDK interface
export const _resetMockServerBalance = (initialBalance = 1000.00) => {
  console.log(`[StakeWebSDK Mock] Resetting server balance to ${initialBalance}`);
  serverBalance = initialBalance;
};
