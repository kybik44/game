# base_game_calculations.py
# from . import win_calculations # Relative import if SDK structure allows, otherwise direct if run standalone
# For subtask, assume win_calculations can be imported if this were part of a larger package run by SDK
# If run directly for testing, this might need sys.path manipulation or for win_calculations to be in same dir / PYTHONPATH

# To ensure it works for subtask if run directly as script, let's assume win_calculations.py is in path
import win_calculations # Simpler for now

def evaluate_base_spin_outcome(grid, game_params):
    """
    Evaluates a single base game spin.
    - grid: The 5x4 grid of symbol IDs.
    - game_params: An instance of GameParams from game_config.py (or a mock).
    """
    
    if not grid or not game_params:
        print("Error: Missing grid or game_params for base spin evaluation.")
        return {
            "line_wins": [], "scatter_wins": [], 
            "total_payout_multiplier": 0, "triggered_features": [],
            "grid_played": grid or []
        }

    all_line_wins, total_line_payout = win_calculations.calculate_line_wins(
        grid,
        game_params.PAYLINES,
        game_params.PAYTABLE,
        game_params.SYMBOLS
    )
    
    # Ensure SCATTER_MULT symbol ID exists before trying to use it
    scatter_mult_symbol_id = None
    for sid, sdata in game_params.SYMBOLS.items():
        if sdata.get("name", "").lower() == "lirili larila":
            scatter_mult_symbol_id = sid
            break
    if not scatter_mult_symbol_id: # Fallback if not found by name
         if "SCATTER_MULT" in game_params.SYMBOLS:
              scatter_mult_symbol_id = "SCATTER_MULT"


    scatter_wins, total_scatter_payout = [], 0
    if scatter_mult_symbol_id:
        scatter_wins, total_scatter_payout = win_calculations.calculate_scatter_wins(
            grid,
            game_params.PAYTABLE,
            scatter_mult_symbol_id, 
            game_params.SYMBOLS
        )
    
    total_payout_for_spin = total_line_payout + total_scatter_payout
    
    triggered_features = []
    
    # Check for Free Spins trigger (Tralalero)
    fs_scatter_count = 0
    if hasattr(game_params, 'FREE_SPINS_SYMBOL_ID') and game_params.FREE_SPINS_SYMBOL_ID:
        for r in grid:
            for symbol_id_on_grid in r:
                if symbol_id_on_grid == game_params.FREE_SPINS_SYMBOL_ID:
                    fs_scatter_count += 1
        
        if fs_scatter_count >= game_params.FREE_SPINS_TRIGGER_COUNT:
            triggered_features.append({
                "feature_type": "TRALALERO_FREE_SPINS", # Standardized name
                "symbol_id": game_params.FREE_SPINS_SYMBOL_ID,
                "count": fs_scatter_count
            })
    else:
        # print("Debug: FREE_SPINS_SYMBOL_ID not defined in game_params.")
        pass
        
    # Check for Bombardino Bonus trigger
    bonus_symbol_count = 0
    if hasattr(game_params, 'BOMBAROAT_BONUS_SYMBOL_ID') and game_params.BOMBAROAT_BONUS_SYMBOL_ID:
        for r in grid:
            for symbol_id_on_grid in r:
                if symbol_id_on_grid == game_params.BOMBAROAT_BONUS_SYMBOL_ID:
                    bonus_symbol_count += 1
                    
        if bonus_symbol_count >= game_params.BOMBAROAT_BONUS_TRIGGER_COUNT:
            triggered_features.append({
                "feature_type": "BOMBAROAT_BONUS", # Standardized name
                "symbol_id": game_params.BOMBAROAT_BONUS_SYMBOL_ID,
                "count": bonus_symbol_count
            })
    else:
        # print("Debug: BOMBAROAT_BONUS_SYMBOL_ID not defined in game_params.")
        pass

    return {
        "line_wins": all_line_wins,
        "scatter_wins": scatter_wins,
        "total_payout_multiplier": total_payout_for_spin,
        "triggered_features": triggered_features,
        "grid_played": grid # For reference
    }

# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Need to import GameParams from game_config.py.
    # This requires game_config.py to be in Python's path.
    # For simple testing, we might need to adjust sys.path or mock GameParams.
    
    # Simplified Mock GameParams for direct testing of this file
    class MockGameParams:
        def __init__(self):
            self.GRID_ROWS = 4
            self.GRID_COLS = 5
            self.SYMBOLS = {
                "H1": {"id": "H1", "name": "Brainroat"}, 
                "WILD": {"id": "WILD", "name": "Crocodrillo", "type": "wild"},
                "M1": {"id": "M1", "name": "Spaghetti"}, 
                "L1": {"id": "L1", "name": "Mask"},
                "SCATTER_FS": {"id": "SCATTER_FS", "name": "Tralalero"},
                "BONUS": {"id": "BONUS", "name": "Bombardino"},
                "SCATTER_MULT": {"id": "SCATTER_MULT", "name": "Lirili Larila"}
            }
            # Using only first 4 horizontal lines for simplicity in mock test
            self.PAYLINES = [ 
                [(0,0),(0,1),(0,2),(0,3),(0,4)], 
                [(1,0),(1,1),(1,2),(1,3),(1,4)],
                [(2,0),(2,1),(2,2),(2,3),(2,4)],
                [(3,0),(3,1),(3,2),(3,3),(3,4)],
            ]
            self.PAYTABLE = {
                "H1": {3: 25, 4: 100, 5: 500}, 
                "WILD": {3:25, 4:100, 5:500},
                "M1": {3: 10, 4: 40, 5: 150}, 
                "L1": {3: 5, 4: 20, 5: 100},
                "SCATTER_MULT": {3: 5, 4: 15, 5: 50}
            }
            self.FREE_SPINS_SYMBOL_ID = "SCATTER_FS" # Corrected from FREE_SPINS_SYMBOL
            self.FREE_SPINS_TRIGGER_COUNT = 3
            self.BOMBAROAT_BONUS_SYMBOL_ID = "BONUS" # Corrected from BOMBAROAT_BONUS_SYMBOL
            self.BOMBAROAT_BONUS_TRIGGER_COUNT = 3

    mock_params = MockGameParams()
    
    test_grid_base = [
        ["H1", "H1", "H1", "M1", "L1"], # Line 0: H1 x3 = 25
        ["SCATTER_FS", "M1", "SCATTER_FS", "BONUS", "L1"],
        ["M1", "SCATTER_FS", "BONUS", "L1", "BONUS"], # 3 SCATTER_FS, 3 BONUS
        ["L1", "M1", "L1", "M1", "SCATTER_MULT"], # 1 SCATTER_MULT (no scatter win)
    ]
    
    outcome = evaluate_base_spin_outcome(test_grid_base, mock_params)
    print("\nBase Game Spin Outcome Test:")
    # print(f"  Grid: {test_grid_base}") # Can be verbose
    print(f"  Line Wins: {outcome['line_wins']}")
    print(f"  Scatter Wins: {outcome['scatter_wins']}")
    print(f"  Total Payout Multiplier: {outcome['total_payout_multiplier']}") # Expected: 25
    print(f"  Triggered Features: {outcome['triggered_features']}") # Expected: FS and Bonus

    test_grid_no_bonus = [
        ["H1", "M1", "L1", "M1", "L1"],
        ["L1", "M1", "L1", "M1", "L1"],
        ["M1", "L1", "M1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "L1"],
    ]
    outcome_no_bonus = evaluate_base_spin_outcome(test_grid_no_bonus, mock_params)
    print("\nBase Game Spin Outcome (No Bonus) Test:")
    print(f"  Line Wins: {outcome_no_bonus['line_wins']}")
    print(f"  Total Payout Multiplier: {outcome_no_bonus['total_payout_multiplier']}") # Expected: 0
    print(f"  Triggered Features: {outcome_no_bonus['triggered_features']}") # Expected: []

    test_grid_scatter_win = [
        ["SCATTER_MULT", "M1", "L1", "M1", "L1"],
        ["L1", "SCATTER_MULT", "L1", "M1", "L1"],
        ["M1", "L1", "SCATTER_MULT", "L1", "M1"], # 3 SCATTER_MULT
        ["L1", "M1", "L1", "M1", "L1"],
    ]
    outcome_scatter = evaluate_base_spin_outcome(test_grid_scatter_win, mock_params)
    print("\nBase Game Spin Outcome (Scatter Win) Test:")
    print(f"  Line Wins: {outcome_scatter['line_wins']}")
    print(f"  Scatter Wins: {outcome_scatter['scatter_wins']}")
    print(f"  Total Payout Multiplier: {outcome_scatter['total_payout_multiplier']}") # Expected: 5
    print(f"  Triggered Features: {outcome_scatter['triggered_features']}")
