# BOMBAROAT_Tralalero_Fury/math/GameMath.py
import hashlib
from abc import ABC, abstractmethod

# --- Interface Definitions ---

class IGameMath(ABC):
    @abstractmethod
    def get_game_parameters(self):
        """Returns basic game parameters like grid size, symbol definitions, etc."""
        pass

    @abstractmethod
    def get_paytable(self):
        """Returns the game's paytable."""
        pass

    @abstractmethod
    def get_paylines(self):
        """Returns the game's payline definitions."""
        pass

    @abstractmethod
    def calculate_spin_outcome(self, client_seed: str, server_seed: str, nonce: int, bet_amount: float, selections: dict = None):
        """
        Calculates a single spin result including grid, wins, and bonus events.
        'selections' could be used for player choices in bonus rounds or features.
        Should return a dictionary containing at least:
        - grid: The symbol matrix
        - wins: A list of win details
        - total_win_multiplier: Total multiplier for the spin
        - bonus_events: Any triggered bonus events
        - next_nonce: The nonce for the next spin
        """
        pass

class IMathAdapter(ABC):
    @abstractmethod
    def __init__(self, math_logic: IGameMath, game_config: dict = None):
        """
        Initializes the adapter with core math logic and optional game configuration.
        """
        self.math_logic = math_logic
        self.game_config = game_config if game_config else {}
        pass

    @abstractmethod
    def spin(self, client_seed: str, server_seed: str, nonce: int, bet_amount: float, selections: dict = None):
        """
        Main method to simulate a game round.
        'selections' could be used for player choices in bonus rounds or features like Bonus Buy.
        """
        pass

    @abstractmethod
    def get_rtp(self):
        """Returns the theoretical Return to Player of the game."""
        pass

    @abstractmethod
    def get_max_win(self):
        """Returns the maximum possible win multiplier for the game."""
        pass
    
    @abstractmethod
    def get_game_info(self):
        """Returns a dictionary with general game information (paytable, paylines, features, RTP, etc.)."""
        pass

    @abstractmethod
    def validate_configuration(self, game_config: dict):
        """Validates a given game configuration against the math logic."""
        pass

# --- Core Game Logic ---

class GameMath(IGameMath): # Inherit from IGameMath
    # Win Category Thresholds (as multipliers of bet_amount)
    NO_WIN_THRESHOLD = 0
    SMALL_WIN_THRESHOLD_MAX = 1  # Wins > 0x and <= 1x
    MEDIUM_WIN_THRESHOLD_MAX = 5 # Wins > 1x and <= 5x
    LARGE_WIN_THRESHOLD_MAX = 15 # Wins > 5x and <= 15x
    # MEGA_WIN is > 15x

    def __init__(self):
        self.RTP = 0.965  # Target RTP
        self.VOLATILITY = "Medium-High" # Target volatility
        self.GRID_ROWS = 4
        self.GRID_COLS = 5
        self.PAYLINES = self.define_paylines() # 20 fixed paylines
        self.SYMBOLS = self.define_symbols()
        self.PAYTABLE = self.define_paytable()
        self.SYMBOL_WEIGHTS = self.define_symbol_weights() # For reel generation

        # Bonus Triggers
        self.FREE_SPINS_TRIGGER_SYMBOL = "Tralalero"
        self.FREE_SPINS_TRIGGER_COUNT = 3
        self.BONUS_ROUND_TRIGGER_SYMBOL = "Bombardino"
        self.BONUS_ROUND_TRIGGER_COUNT = 3

        # Placeholder for clientSeed, serverSeed, nonce - will be used for PRNG
        self.client_seed = None
        self.server_seed = None
        self.nonce = 0

    def define_symbols(self):
        """Defines all symbols in the game."""
        return {
            "H1": {"name": "Brainroat", "type": "high_paying"},
            "WILD": {"name": "Crocodrillo", "type": "wild"},
            "BONUS": {"name": "Bombardino", "type": "bonus_trigger"},
            "SCATTER_FS": {"name": "Tralalero", "type": "scatter_fs"}, # Free Spins
            "SCATTER_MULT": {"name": "Lirili Larila", "type": "scatter_multiplier"},
            "M1": {"name": "Flying Spaghetti", "type": "medium_paying"},
            "M2": {"name": "Cursed Espresso", "type": "medium_paying"},
            "L1": {"name": "Opera Mask", "type": "low_paying"},
            # Add more filler symbols as needed
        }

    def define_paylines(self):
        """Defines the 20 fixed paylines.
        Each payline is a list of (row, col) tuples.
        Rows and columns are 0-indexed.
        Example: [[(0,0), (0,1), (0,2), (0,3), (0,4)], # Top row
                  [(1,0), (1,1), (1,2), (1,3), (1,4)], # Second row
                  ...]
        This needs to be filled with the actual 20 payline definitions.
        """
        paylines = [
            # Horizontal lines (4 lines)
            [(0,0), (0,1), (0,2), (0,3), (0,4)],  # Line 1 (Top row)
            [(1,0), (1,1), (1,2), (1,3), (1,4)],  # Line 2 (Second row)
            [(2,0), (2,1), (2,2), (2,3), (2,4)],  # Line 3 (Third row)
            [(3,0), (3,1), (3,2), (3,3), (3,4)],  # Line 4 (Bottom row)

            # Diagonal lines (2 lines)
            [(0,0), (1,1), (2,2), (3,3), (3,4)],  # Line 5 (Diagonal down-rightish) - modified to fit 4 rows
            [(3,0), (2,1), (1,2), (0,3), (0,4)],  # Line 6 (Diagonal up-rightish) - modified to fit 4 rows
            
            # V-shapes (4 lines)
            [(0,0), (1,1), (2,2), (1,3), (0,4)],  # Line 7 (V-shape)
            [(3,0), (2,1), (1,2), (2,3), (3,4)],  # Line 8 (Inverted V-shape)
            # [(0,2), (1,1), (2,0), (1,1), (0,2)],  # Line 9 (V-shape centered) - REMOVED to fix payline count
            [(0,1), (1,2), (2,3), (1,2), (0,1)],  # Line 9 (Small V pointing right) - This is the true Line 9 now.
            [(1,0), (2,1), (3,2), (2,3), (1,4)],  # Line 10 (Wide inverted V)

            # Z-shapes / N-shapes (2 lines)
            [(0,0), (0,1), (1,2), (2,3), (2,4)],  # Line 11 (Z-shape variant)
            [(3,0), (3,1), (2,2), (1,3), (1,4)],  # Line 12 (Mirrored Z-shape variant)

            # Bridge/U-shapes (4 lines)
            [(0,0), (1,0), (2,0), (2,1), (2,2)],  # Line 13 (L-shape variant start)
            [(0,4), (1,4), (2,4), (2,3), (2,2)],  # Line 14 (Reversed L-shape variant end)
            [(0,0), (0,1), (1,2), (0,3), (0,4)],  # Line 15 (Shallow W 'top')
            [(1,0), (1,1), (0,2), (1,3), (1,4)],  # Line 16 (Shallow M on row 1) - similar to line 15 but one row down


            # More complex/custom shapes (4 lines)
            [(0,0), (1,1), (0,2), (1,3), (0,4)],  # Line 17 (W-shape top)
            [(1,0), (0,1), (1,2), (0,3), (1,4)],  # Line 18 (M-shape row 1/0)
            [(2,0), (3,1), (2,2), (3,3), (2,4)],  # Line 19 (W-shape bottom)
            [(3,0), (2,1), (3,2), (2,3), (3,4)]   # Line 20 (M-shape row 3/2)
        ]
        # Ensure all paylines have 5 positions
        for i, p in enumerate(paylines):
            if len(p) != self.GRID_COLS:
                print(f"Error: Payline {i} has {len(p)} points, expected {self.GRID_COLS}")
        
        if len(paylines) != 20:
            print(f"Warning: Defined {len(paylines)} paylines, but expected 20.")
            
        return paylines


    def define_paytable(self):
        """Defines the payout for each symbol for different match counts.
        Format: {symbol_id: {match_count: payout_multiplier}}
        """
        return {
            "H1": {3: 1, 4: 2, 5: 5},         # Was 0.2, 1, 5 (Slightly increased H1)
            "WILD": {3: 0.1, 4: 0.5, 5: 1},   # Was 0.2, 1, 5 (Reduced WILD)
            "M1": {3: 0.1, 4: 0.2, 5: 0.5},  # Was 0.1, 0.4, 1.5
            "M2": {3: 0.1, 4: 0.2, 5: 0.5},  # Was 0.1, 0.4, 1.5
            "L1": {3: 0.01, 4: 0.05, 5: 0.2}, # Was 0.05, 0.2, 1 (L1 pays almost nothing)
            # SCATTER_FS and BONUS typically don't have direct line payouts
            # SCATTER_MULT might have payouts or just apply multipliers
            "SCATTER_MULT": {3: 0.01, 4: 0.02, 5: 0.1} # Was 0.05, 0.1, 0.5
        }

    def define_symbol_weights(self):
        """Defines the weights for each symbol on each reel.
        This determines the probability of a symbol appearing.
        Format: {reel_index: {symbol_id: weight}}
        These are crucial for RTP and volatility.
        Needs careful balancing.
        """
        # Placeholder weights - these need to be carefully designed
        default_weights = {
            "H1": 1,           # Was 2 (Extremely Rare)
            "WILD": 1,         # Was 1 (Extremely Rare)
            "BONUS": 1,        # Unchanged (Extremely Rare)
            "SCATTER_FS": 1,   # Unchanged (Extremely Rare)
            "SCATTER_MULT": 1, # Unchanged (Extremely Rare)
            "M1": 2,           # Was 10 (Very Rare)
            "M2": 2,           # Was 10 (Very Rare)
            "L1": 200          # Was 100 (L1 is vast majority)
        }
        reels = []
        for _ in range(self.GRID_COLS):
            reels.append(default_weights.copy())
        # Example: Make Reel 2 have more H1
        # reels[1]["H1"] = 10
        print("Warning: Symbol weights are placeholders and need balancing for RTP.")
        return reels

    # --- IGameMath Implementation ---

    def get_game_parameters(self):
        """Returns basic game parameters like grid size, symbol definitions, etc."""
        return {
            "grid_rows": self.GRID_ROWS,
            "grid_cols": self.GRID_COLS,
            "symbols": self.SYMBOLS, # Exposing symbol definitions
            "free_spins_trigger_symbol": self.FREE_SPINS_TRIGGER_SYMBOL,
            "free_spins_trigger_count": self.FREE_SPINS_TRIGGER_COUNT,
            "bonus_round_trigger_symbol": self.BONUS_ROUND_TRIGGER_SYMBOL,
            "bonus_round_trigger_count": self.BONUS_ROUND_TRIGGER_COUNT,
        }

    def get_paytable(self):
        """Returns the game's paytable."""
        return self.PAYTABLE

    def get_paylines(self):
        """Returns the game's payline definitions."""
        return self.PAYLINES
    
    # --- Core Game Logic Methods --- (these are called by calculate_spin_outcome)

    def _generate_reels(self, client_seed, server_seed, nonce): # Renamed to indicate internal use
        """Generates the symbol matrix for a spin using PRNG based on seeds and nonce.
        Symbols for each cell are generated independently for this version.
        """
        self.client_seed = client_seed
        self.server_seed = server_seed
        self.nonce = nonce

        grid = [['' for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]

        for c in range(self.GRID_COLS):  # For each column (reel)
            reel_weights = self.SYMBOL_WEIGHTS[c]
            # Sort items for deterministic iteration if weights are ever equal
            # (though order of items in dict is stable in Python 3.7+)
            sorted_symbols = sorted(reel_weights.items(), key=lambda item: item[0]) 
            total_reel_weight = sum(w for _, w in sorted_symbols)

            if total_reel_weight == 0:
                # Handle case with no weights or all zero weights for a reel
                # Fallback to a default symbol or raise an error
                # For now, let's fill with a known symbol or skip (might cause issues)
                print(f"Warning: Reel {c} has total weight of 0. Using 'L1' as fallback.")
                for r_idx in range(self.GRID_ROWS):
                    grid[r_idx][c] = "L1" # Fallback symbol
                continue

            for r in range(self.GRID_ROWS):  # For each row in the current column
                # 1. Combine Seeds and Nonce (unique for each cell)
                input_str = f"{self.server_seed}-{self.client_seed}-{self.nonce}-{c}-{r}"
                
                # 2a. Use a cryptographic hash function (SHA256)
                hash_obj = hashlib.sha256(input_str.encode('utf-8'))
                hex_hash = hash_obj.hexdigest()
                
                # 2b. Convert a portion of the hash output into an integer
                # Using the first 8 characters (32 bits) of the hex hash
                hash_int = int(hex_hash[:8], 16) 
                
                # 2c. Use this integer to select a symbol based on weights
                value = hash_int % total_reel_weight
                
                chosen_symbol_id = None
                for symbol_id, weight in sorted_symbols:
                    if value < weight:
                        chosen_symbol_id = symbol_id
                        break
                    value -= weight
                
                if chosen_symbol_id is None: # Should not happen if total_reel_weight > 0
                    print(f"Error: Could not select symbol for cell ({r},{c}). Defaulting to L1.")
                    chosen_symbol_id = "L1" # Fallback

                grid[r][c] = chosen_symbol_id
        
        # print("Generated grid with PRNG:", grid) # Optional: for debugging
        return grid

    def calculate_wins(self, grid):
        """Calculates wins based on the grid and paylines."""
        wins = []
        total_win_multiplier = 0

        # Line wins
        for i, line in enumerate(self.PAYLINES):
            line_symbols = []
            try:
                for r, c in line:
                    line_symbols.append(grid[r][c])
            except IndexError:
                print(f"Error: Payline {i} definition is out of bounds for the grid.")
                continue


            # Determine the winning symbol and count for this line
            # This logic needs to handle wilds correctly.
            # For simplicity, let's find the first non-wild symbol to determine the line type.
            first_symbol = None
            for sym_code in line_symbols:
                if self.SYMBOLS[sym_code]["type"] != "wild":
                    first_symbol = sym_code
                    break
            
            if not first_symbol or first_symbol not in self.PAYTABLE:
                continue # No win or not a paying symbol

            match_count = 0
            for sym_code in line_symbols:
                if sym_code == first_symbol or sym_code == "WILD":
                    match_count += 1
                else:
                    break # Streak broken

            if match_count > 0 and match_count in self.PAYTABLE[first_symbol]:
                payout = self.PAYTABLE[first_symbol][match_count]
                wins.append({
                    "line_index": i,
                    "symbol": first_symbol,
                    "count": match_count,
                    "payout_multiplier": payout
                })
                total_win_multiplier += payout
        
        # Scatter wins (Tralalero for Free Spins, Lirili Larila for Multiplier/Scatter Payout)
        scatter_counts = {}
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                symbol_code = grid[r][c]
                if self.SYMBOLS[symbol_code]["type"].startswith("scatter"):
                    scatter_counts[symbol_code] = scatter_counts.get(symbol_code, 0) + 1
        
        # Lirili Larila (SCATTER_MULT) scatter payout
        if "SCATTER_MULT" in scatter_counts and \
            scatter_counts["SCATTER_MULT"] in self.PAYTABLE.get("SCATTER_MULT", {}):
            payout = self.PAYTABLE["SCATTER_MULT"][scatter_counts["SCATTER_MULT"]]
            wins.append({
                "type": "scatter_win",
                "symbol": "SCATTER_MULT",
                "count": scatter_counts["SCATTER_MULT"],
                "payout_multiplier": payout
            })
            total_win_multiplier += payout

        return {"wins": wins, "total_win_multiplier": total_win_multiplier}

    def check_bonus_triggers(self, grid):
        """Checks for bonus game triggers."""
        bonus_events = []
        
        # Count Tralalero symbols for Free Spins
        tralalero_count = 0
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                if grid[r][c] == self.FREE_SPINS_TRIGGER_SYMBOL:
                    tralalero_count +=1
        
        if tralalero_count >= self.FREE_SPINS_TRIGGER_COUNT:
            bonus_events.append({
                "type": "free_spins",
                "symbol": self.FREE_SPINS_TRIGGER_SYMBOL,
                "count": tralalero_count
                # Potentially add number of free spins awarded, e.g., 10 spins
            })

        # Count Bombardino symbols for Bonus Round
        bombardino_count = 0
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                if grid[r][c] == self.BONUS_ROUND_TRIGGER_SYMBOL:
                    bombardino_count +=1

        if bombardino_count >= self.BONUS_ROUND_TRIGGER_COUNT:
            bonus_events.append({
                "type": "bombardino_bonus",
                "symbol": self.BONUS_ROUND_TRIGGER_SYMBOL,
                "count": bombardino_count
            })
            
        return bonus_events

    # calculate_wins and check_bonus_triggers remain as previously defined internal methods
    # They are called by calculate_spin_outcome

    def calculate_spin_outcome(self, client_seed: str, server_seed: str, nonce: int, bet_amount: float, selections: dict = None):
        """
        Calculates a single spin result including grid, wins, and bonus events.
        'selections' could be used for player choices in bonus rounds or features.
        """
        grid = self._generate_reels(client_seed, server_seed, nonce) 
        win_results = self.calculate_wins(grid) 
        bonus_events = self.check_bonus_triggers(grid)
        
        return {
            "grid": grid,
            "wins": win_results["wins"],
            "total_win_multiplier": win_results["total_win_multiplier"],
            "bonus_events": bonus_events,
            "next_nonce": nonce + 1,
            # bet_amount is not used for core multiplier calculation but acknowledged
            "bet_amount_for_this_spin": bet_amount, 
            "selections_received": selections # Store received selections
        }

    def _get_win_category(self, payout_multiplier: float) -> str:
        if payout_multiplier == self.NO_WIN_THRESHOLD:
            return "no_win"
        elif payout_multiplier <= self.SMALL_WIN_THRESHOLD_MAX:
            return "small_win"
        elif payout_multiplier <= self.MEDIUM_WIN_THRESHOLD_MAX:
            return "medium_win"
        elif payout_multiplier <= self.LARGE_WIN_THRESHOLD_MAX:
            return "large_win"
        else:
            return "mega_win"

    def run_simulation(self, num_spins: int, bet_amount: float = 1.0):
        """Runs a simulation for a given number of spins to estimate RTP and win distribution."""
        total_bet = 0
        total_payout = 0
        
        win_distribution = {
            "no_win": 0,      # 0x
            "small_win": 0,   # >0x to 1x
            "medium_win": 0,  # >1x to 5x
            "large_win": 0,   # >5x to 15x
            "mega_win": 0     # >15x
        }
        
        # Track min/max multipliers for volatility insights (optional bonus)
        min_multiplier_seen = float('inf')
        max_multiplier_seen = float('-inf')

        for i in range(num_spins):
            client_seed = f"sim_client_{i}"
            server_seed = f"sim_server_{i}"
            # Nonce should ideally be unique per seed pair, but for simulation using i is common
            nonce = i 

            spin_result = self.calculate_spin_outcome(client_seed, server_seed, nonce, bet_amount)
            
            payout_multiplier = spin_result["total_win_multiplier"]
            current_payout = payout_multiplier * bet_amount
            
            total_bet += bet_amount
            total_payout += current_payout
            
            category = self._get_win_category(payout_multiplier)
            win_distribution[category] += 1
            
            if payout_multiplier < min_multiplier_seen:
                min_multiplier_seen = payout_multiplier
            if payout_multiplier > max_multiplier_seen:
                max_multiplier_seen = payout_multiplier

        actual_rtp = (total_payout / total_bet) * 100 if total_bet > 0 else 0
        
        # Prepare distribution percentages
        win_distribution_percent = {k: (v / num_spins) * 100 for k, v in win_distribution.items()}

        return {
            "simulated_rtp": actual_rtp,
            "total_spins": num_spins,
            "total_bet": total_bet,
            "total_payout": total_payout,
            "win_distribution_counts": win_distribution,
            "win_distribution_percentage": win_distribution_percent,
            "hit_frequency_percent": (1 - (win_distribution["no_win"] / num_spins)) * 100 if num_spins > 0 else 0,
            "min_win_multiplier_seen": min_multiplier_seen if min_multiplier_seen != float('inf') else 0,
            "max_win_multiplier_seen": max_multiplier_seen if max_multiplier_seen != float('-inf') else 0,
        }

# --- Adapter for Stake Platform ---

class StakeMathAdapter(IMathAdapter):
    def __init__(self, math_logic: IGameMath, game_config: dict = None):
        super().__init__(math_logic, game_config) # Calls IMathAdapter.__init__
        # Optional: initial validation or setup based on game_config
        if not self.validate_configuration(self.game_config): # Using self.game_config from super
            # Depending on strictness, could raise error or just log
            print("Warning: Initial game configuration failed validation.")
            # raise ValueError("Invalid game configuration provided to StakeMathAdapter.")


    def spin(self, client_seed: str, server_seed: str, nonce: int, bet_amount: float, selections: dict = None):
        """
        Main method to simulate a game round.
        'selections' could be used for player choices in bonus rounds or features like Bonus Buy.
        """
        # Example: selections might indicate a specific bonus buy
        # if selections and "feature_buy" in selections:
        #    # Modify behavior or pass to math_logic if it supports feature buys
        #    pass

        spin_outcome = self.math_logic.calculate_spin_outcome(
            client_seed=client_seed,
            server_seed=server_seed,
            nonce=nonce,
            bet_amount=bet_amount,
            selections=selections
        )
        
        # Adapter can transform or add data if needed for the platform
        # For example, calculating actual payout from multiplier and bet_amount
        spin_outcome['payout_amount'] = spin_outcome['total_win_multiplier'] * bet_amount
        
        return spin_outcome

    def get_rtp(self):
        """Returns the theoretical Return to Player of the game."""
        # Assuming RTP is a direct attribute of the math_logic instance
        if hasattr(self.math_logic, 'RTP'):
            return self.math_logic.RTP
        return "N/A" # Fallback if RTP attribute doesn't exist

    def get_max_win(self):
        """Returns the maximum possible win multiplier for the game."""
        # This is often a configured value or derived from paytable analysis
        # Using a placeholder value from game_config or a default
        return self.game_config.get("max_win_multiplier", 5000) # Example placeholder

    def get_game_info(self):
        """Returns a dictionary with general game information."""
        params = self.math_logic.get_game_parameters()
        game_info = {
            "game_name": self.game_config.get("game_name", "BOMBAROAT_Tralalero_Fury"),
            "rtp": self.get_rtp(),
            "volatility": getattr(self.math_logic, 'VOLATILITY', "N/A"), # Assumes VOLATILITY attribute
            "max_win_multiplier": self.get_max_win(),
            "grid_rows": params.get("grid_rows"),
            "grid_cols": params.get("grid_cols"),
            "paylines_count": len(self.math_logic.get_paylines()),
            "paytable_symbols_count": len(self.math_logic.get_paytable()),
            # For brevity, not including full paylines/paytable here, but could.
            # "paylines": self.math_logic.get_paylines(),
            # "paytable": self.math_logic.get_paytable(),
            "symbols": list(params.get("symbols", {}).keys()), # List of symbol names
            "features": [] # Placeholder for feature descriptions
        }
        if params.get("free_spins_trigger_symbol"):
            game_info["features"].append(f"Free Spins ({params['free_spins_trigger_symbol']})")
        if params.get("bonus_round_trigger_symbol"):
            game_info["features"].append(f"Bonus Round ({params['bonus_round_trigger_symbol']})")
        return game_info

    def validate_configuration(self, game_config: dict):
        """Validates a given game configuration against the math logic."""
        # Placeholder: In a real scenario, this would be much more thorough.
        # e.g., check if all symbols in paytable are defined in general symbols,
        # if payline coordinates are valid for grid dimensions, etc.
        if game_config is None: # An empty or None config might be valid (use defaults)
            return True 
        
        # Example: Check if configured RTP matches the math logic's RTP
        if "expected_rtp" in game_config:
            math_rtp = self.get_rtp()
            if math_rtp != "N/A" and game_config["expected_rtp"] != math_rtp:
                print(f"Configuration Warning: Expected RTP {game_config['expected_rtp']} "
                      f"does not match Math Logic RTP {math_rtp}.")
                # return False # Decide if this is a critical failure
        
        # Add more checks as needed
        return True


# Example Usage (for testing purposes)
if __name__ == "__main__":
    # 1. Instantiate Core Game Logic
    core_game_math = GameMath()

    # 2. Define a game configuration (optional)
    game_specific_config = {
        "game_name": "BOMBAROAT Tralalero Fury Deluxe",
        "version": "1.0.1",
        "max_win_multiplier": 7500, # Override default max win
        "expected_rtp": 0.965
    }

    # 3. Instantiate Stake Math Adapter
    # Pass the core math logic and the specific game config
    adapter = StakeMathAdapter(math_logic=core_game_math, game_config=game_specific_config)

    # 4. Test get_game_info
    print("--- Game Info (via Adapter) ---")
    game_details = adapter.get_game_info()
    for key, value in game_details.items():
        print(f"  {key}: {value}")

    # 5. Test a spin via the adapter
    print("\n--- Simulating Spin (via Adapter) ---")
    client_seed = "test_client_seed_123"
    server_seed = "test_server_seed_abc"
    nonce = 1
    bet_amount = 1.0  # Example: 1 unit of currency

    spin_result = adapter.spin(client_seed, server_seed, nonce, bet_amount)

    print("  Generated Grid:")
    for r_idx, row in enumerate(spin_result["grid"]):
        print(f"    Row {r_idx}: {row}")
    
    print("  Wins:")
    if spin_result["wins"]:
        for win_info in spin_result["wins"]:
            print(f"    {win_info}")
    else:
        print("    No line wins.")
    
    print(f"  Total Win Multiplier: {spin_result['total_win_multiplier']}")
    print(f"  Payout Amount (bet * multiplier): {spin_result['payout_amount']}")

    print("  Bonus Events:")
    if spin_result["bonus_events"]:
        for event_info in spin_result["bonus_events"]:
            print(f"    {event_info}")
    else:
        print("    No bonus events triggered.")
    
    print(f"  Next Nonce: {spin_result['next_nonce']}")
    print(f"  Bet Amount Processed: {spin_result['bet_amount_for_this_spin']}")
    print(f"  Selections Received: {spin_result['selections_received']}")


    # Example of using the TestGameMath variant for guaranteed bonus, via adapter
    print("\n--- Simulating Spin with Guaranteed Bonus (via Adapter) ---")
    class TestGameMathForBonusAdapter(GameMath): # Inherits IGameMath through GameMath
        def _generate_reels(self, client_seed, server_seed, nonce): # Override internal reel gen
            # Grid designed to trigger bonuses using correct symbol keys
            return [
                ["SCATTER_FS", "BONUS", "L1", "SCATTER_FS", "H1"],
                ["M1", "SCATTER_FS", "BONUS", "L1", "SCATTER_MULT"],
                ["L1", "M1", "SCATTER_FS", "BONUS", "WILD"],
                ["BONUS", "L1", "M2", "H1", "M1"],
            ]
    
    test_bonus_math = TestGameMathForBonusAdapter()
    # Ensure paylines are simple for predictable wins with the test grid
    test_bonus_math.PAYLINES = [[(i, col) for col in range(test_bonus_math.GRID_COLS)] for i in range(test_bonus_math.GRID_ROWS)]
    
    adapter_for_bonus_test = StakeMathAdapter(math_logic=test_bonus_math, game_config=game_specific_config)
    
    bonus_spin_result = adapter_for_bonus_test.spin(client_seed, server_seed, nonce + 1, bet_amount) # Increment nonce

    print("  Generated Grid (Bonus Test):")
    for r_idx, row in enumerate(bonus_spin_result["grid"]):
        print(f"    Row {r_idx}: {row}")

    print("  Wins (Bonus Test):")
    if bonus_spin_result["wins"]:
        for win_info in bonus_spin_result["wins"]:
            print(f"    {win_info}")
    else:
        print("    No line wins.")
    print(f"  Total Win Multiplier (Bonus Test): {bonus_spin_result['total_win_multiplier']}")
    
    print("  Bonus Events (Bonus Test):")
    if bonus_spin_result["bonus_events"]:
        for event_info in bonus_spin_result["bonus_events"]:
            print(f"    {event_info}")
    else:
        print("    No bonus events triggered.")

    # Test configuration validation (optional)
    print("\n--- Configuration Validation Test ---")
    valid_conf = {"expected_rtp": 0.965} # Assumes core_game_math.RTP is 0.965
    invalid_conf = {"expected_rtp": 0.900}
    print(f"  Validating config (matches math): {adapter.validate_configuration(valid_conf)}")
    print(f"  Validating config (mismatches math): {adapter.validate_configuration(invalid_conf)}")
    # print(f"  Paytable: {core_game_math.PAYTABLE}") # Access through core_game_math instance
    # print(f"  Symbol Weights: {core_game_math.SYMBOL_WEIGHTS[0]} (Reel 0)")


    # 6. Run Simulation (using core_game_math instance)
    print("\n--- Running Simulation (via GameMath instance) ---")
    # Using a smaller number of spins for quick testing in this environment
    # For more accurate RTP, 1,000,000+ spins would be better.
    num_simulation_spins = 100000 # Increased to 100,000 for RTP tuning
    
    simulation_results = core_game_math.run_simulation(num_spins=num_simulation_spins, bet_amount=1.0)

    print(f"  Simulation completed for {simulation_results['total_spins']} spins.")
    print(f"  Total Bet: {simulation_results['total_bet']}")
    print(f"  Total Payout: {simulation_results['total_payout']}")
    print(f"  Simulated RTP: {simulation_results['simulated_rtp']:.4f}%")
    print(f"  Hit Frequency: {simulation_results['hit_frequency_percent']:.2f}%")
    print(f"  Min Win Multiplier Seen: {simulation_results['min_win_multiplier_seen']}")
    print(f"  Max Win Multiplier Seen: {simulation_results['max_win_multiplier_seen']}")
    
    print("  Win Distribution (Counts):")
    for category, count in simulation_results['win_distribution_counts'].items():
        print(f"    {category}: {count}")
        
    print("  Win Distribution (Percentage):")
    for category, percentage in simulation_results['win_distribution_percentage'].items():
        print(f"    {category}: {percentage:.2f}%")

    # The old direct GameMath spin simulation tests are now superseded by adapter tests
    # and the new run_simulation method.
    # Keeping them commented out or removing them would be fine.
    # For example, the following were old tests:
    # print("\n--- Simulating a Spin ---") 
    # ... (old GameMath().simulate_spin() calls) ...
