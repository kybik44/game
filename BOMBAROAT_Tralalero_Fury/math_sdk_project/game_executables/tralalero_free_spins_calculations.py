# tralalero_free_spins_calculations.py
import random # For random transformations and placeholder grid generation
# Assume win_calculations.py and game_config.py are accessible in the SDK's environment
import win_calculations 
# from .. import game_config # This relative import would be typical if run by SDK as part of a package

# For standalone testing, we'll mock or pass game_params
# For this subtask, assume game_params is passed in.

def generate_grid_for_free_spin(game_params):
    """
    Placeholder for generating a grid during a free spin.
    In a real SDK, this would use the defined reel strips and a PRNG.
    For now, creates a random grid for structural simulation.
    """
    # Ensure all symbol IDs used are valid keys in game_params.SYMBOLS
    valid_symbol_ids = list(game_params.SYMBOLS.keys())
    if not valid_symbol_ids:
        # Fallback if SYMBOLS is empty, though this shouldn't happen with proper GameParams
        print("Error: No symbols defined in game_params.SYMBOLS for grid generation.")
        return [["L1"] * game_params.GRID_COLS for _ in range(game_params.GRID_ROWS)] # Default to L1

    grid = [[random.choice(valid_symbol_ids) for _ in range(game_params.GRID_COLS)] for _ in range(game_params.GRID_ROWS)]
    # print("Warning: Free spin grid generation is using random.choice (placeholder).")
    return grid

def apply_symbol_transformations(grid, game_params):
    """
    Applies random symbol transformations based on config.
    """
    transformed_grid = [row[:] for row in grid] # Create a copy
    
    # Ensure config exists and has the necessary keys
    if not hasattr(game_params, 'tralalero_free_spins_config') or \
       not isinstance(game_params.tralalero_free_spins_config, dict):
        print("Warning: tralalero_free_spins_config not found or invalid in game_params.")
        return transformed_grid
        
    config = game_params.tralalero_free_spins_config
    transformation_symbols = config.get("transformation_symbols", [])
    target_symbol = config.get("transformation_target_symbol")

    if not transformation_symbols or not target_symbol:
        # print("Debug: No transformation_symbols or transformation_target_symbol defined in config.")
        return transformed_grid # No transformation possible if config is missing

    num_transformations = random.randint(1, 3) # Example: 1 to 3 transformations per spin
    
    for _ in range(num_transformations):
        # Find candidate symbols to transform
        candidates = []
        for r_idx, row in enumerate(transformed_grid):
            for c_idx, symbol_id in enumerate(row):
                if symbol_id in transformation_symbols:
                    candidates.append((r_idx, c_idx))
        
        if candidates:
            r, c = random.choice(candidates)
            transformed_grid[r][c] = target_symbol
            # print(f"Debug: Transformed symbol at ({r},{c}) to {target_symbol}")
            
    return transformed_grid

def simulate_tralalero_free_spins_feature(triggering_scatter_count, game_params, initial_grid=None):
    """
    Simulates the entire Tralalero Free Spins feature.
    - triggering_scatter_count: Number of scatters that triggered the feature.
    - game_params: Instance of GameParams.
    - initial_grid: The grid that triggered the feature (optional, for context).
    """
    if not hasattr(game_params, 'tralalero_free_spins_config') or \
       not isinstance(game_params.tralalero_free_spins_config, dict):
        print("Error: tralalero_free_spins_config missing or invalid in game_params.")
        return {"total_feature_payout": 0, "spins_played": 0, "events": ["FS config error."]}
        
    fs_config = game_params.tralalero_free_spins_config
    spins_awarded_map = fs_config.get("spins_awarded_by_scatter_count", {})
    
    num_initial_spins = spins_awarded_map.get(triggering_scatter_count, 0)
    
    # Handle cases where scatter count might be higher than defined keys (e.g., 6 scatters if possible)
    if num_initial_spins == 0 and triggering_scatter_count > 0 and spins_awarded_map:
        max_defined_scatters = max(spins_awarded_map.keys(), default=0)
        if triggering_scatter_count > max_defined_scatters and max_defined_scatters > 0 :
            num_initial_spins = spins_awarded_map[max_defined_scatters]

    if num_initial_spins == 0:
        return {"total_feature_payout": 0, "spins_played": 0, "events": ["No spins awarded due to scatter count."]}

    current_spins_remaining = num_initial_spins
    total_feature_payout = 0
    feature_events = [] 
    spins_played_count = 0
    retrigger_count = 0

    feature_events.append(f"Initial: {num_initial_spins} free spins awarded for {triggering_scatter_count} {game_params.FREE_SPINS_SYMBOL_ID} scatters.")

    while current_spins_remaining > 0:
        spins_played_count += 1
        current_spins_remaining -= 1
        
        spin_grid = generate_grid_for_free_spin(game_params) 
        transformed_grid = apply_symbol_transformations(spin_grid, game_params)
        
        feature_events.append({
            "spin_number": spins_played_count,
            "action": "symbol_transformation",
            # "original_grid_segment_if_needed": spin_grid[0], 
            # "transformed_grid_segment_if_needed": transformed_grid[0]
        })
        
        line_wins, line_payout = win_calculations.calculate_line_wins(
            transformed_grid, game_params.PAYLINES, game_params.PAYTABLE, game_params.SYMBOLS
        )
        
        scatter_mult_id = getattr(game_params, 'SCATTER_MULT_SYMBOL_ID', "SCATTER_MULT") # Use a default or get from params
        scatter_wins, scatter_payout = win_calculations.calculate_scatter_wins(
            transformed_grid, game_params.PAYTABLE, scatter_mult_id, game_params.SYMBOLS
        )
        spin_total_payout = line_payout + scatter_payout
        total_feature_payout += spin_total_payout
        
        if spin_total_payout > 0:
            feature_events.append({
                "spin_number": spins_played_count,
                "wins_this_spin": spin_total_payout,
                "line_wins_count": len(line_wins), 
                "scatter_wins_count": len(scatter_wins)
            })

        if fs_config.get("can_retrigger", False) and retrigger_count < fs_config.get("max_retriggers", 0):
            fs_scatter_on_grid = 0
            for r in transformed_grid: 
                for symbol_id_on_grid in r:
                    if symbol_id_on_grid == game_params.FREE_SPINS_SYMBOL_ID: # Use ID from game_params
                        fs_scatter_on_grid += 1
            
            if fs_scatter_on_grid >= game_params.FREE_SPINS_TRIGGER_COUNT:
                additional_spins = spins_awarded_map.get(fs_scatter_on_grid, 0)
                if additional_spins == 0 and fs_scatter_on_grid > 0 and spins_awarded_map: # Handle > max defined
                    max_defined_scatters_retrigger = max(spins_awarded_map.keys(), default=0)
                    if fs_scatter_on_grid > max_defined_scatters_retrigger and max_defined_scatters_retrigger > 0:
                         additional_spins = spins_awarded_map[max_defined_scatters_retrigger]

                if additional_spins > 0:
                    current_spins_remaining += additional_spins
                    retrigger_count += 1
                    feature_events.append({
                        "spin_number": spins_played_count,
                        "action": "retrigger",
                        "scatters_found": fs_scatter_on_grid,
                        "additional_spins": additional_spins,
                        "spins_remaining": current_spins_remaining
                    })
        
        if current_spins_remaining <= 0:
            feature_events.append("All free spins complete.")
            break
            
    return {
        "total_feature_payout": total_feature_payout,
        "spins_played": spins_played_count,
        "retriggered_times": retrigger_count,
        "events": feature_events,
        "final_grid_example_if_needed": transformed_grid # Example of what could be returned
    }

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    class MockGameParams: 
        def __init__(self):
            self.GAME_NAME = "BOMBAROAT™ Mock"
            self.GRID_ROWS = 4
            self.GRID_COLS = 5
            self.SYMBOLS = {
                "H1": {"id": "H1", "name": "Brainroat"}, "WILD": {"id": "WILD", "name": "Crocodrillo"},
                "M1": {"id": "M1", "name": "Spaghetti"}, "M2": {"id": "M2", "name": "Espresso"}, 
                "L1": {"id": "L1", "name": "Mask"},
                "SCATTER_FS": {"id": "SCATTER_FS", "name": "Tralalero"},
                "SCATTER_MULT": {"id": "SCATTER_MULT", "name": "Lirili Larila"}
            }
            self.PAYLINES = [ [(r,c) for c in range(self.GRID_COLS)] for r in range(self.GRID_ROWS) ] 
            self.PAYTABLE = {
                "H1": {3: 25, 4: 100, 5: 500}, "WILD": {3:25, 4:100, 5:500},
                "M1": {3: 10, 4: 40, 5: 150}, "L1": {3: 5, 4: 20, 5: 100},
                "SCATTER_MULT": {3: 5, 4: 15, 5: 50}
            }
            self.FREE_SPINS_SYMBOL_ID = "SCATTER_FS" 
            self.FREE_SPINS_TRIGGER_COUNT = 3 
            self.tralalero_free_spins_config = {
                "spins_awarded_by_scatter_count": {3: 10, 4: 12, 5: 15},
                "can_retrigger": True, "max_retriggers": 1, 
                "transformation_symbols": ["M1", "M2", "L1"],
                "transformation_target_symbol": "H1"
            }
            self.SCATTER_MULT_SYMBOL_ID = "SCATTER_MULT" # For scatter win calc

    mock_params_fs = MockGameParams()
    
    print("\n--- Tralalero Free Spins Feature Simulation Test ---")
    fs_outcome_3_scatters = simulate_tralalero_free_spins_feature(3, mock_params_fs)
    print("Outcome for 3 triggering scatters:")
    print(f"  Total Payout: {fs_outcome_3_scatters['total_feature_payout']}")
    print(f"  Spins Played: {fs_outcome_3_scatters['spins_played']}")
    print(f"  Retriggered: {fs_outcome_3_scatters['retriggered_times']} times")
    # print(f"  Events: {fs_outcome_3_scatters['events']}")

    fs_outcome_4_scatters = simulate_tralalero_free_spins_feature(4, mock_params_fs)
    print("\nOutcome for 4 triggering scatters:")
    print(f"  Total Payout: {fs_outcome_4_scatters['total_feature_payout']}")
    print(f"  Spins Played: {fs_outcome_4_scatters['spins_played']}")
    
    fs_outcome_2_scatters = simulate_tralalero_free_spins_feature(2, mock_params_fs)
    print("\nOutcome for 2 triggering scatters (expect 0 spins):")
    print(f"  Total Payout: {fs_outcome_2_scatters['total_feature_payout']}")
    print(f"  Spins Played: {fs_outcome_2_scatters['spins_played']}")
    print(f"  Events: {fs_outcome_2_scatters['events']}")

    # Test for > 5 scatters
    fs_outcome_6_scatters = simulate_tralalero_free_spins_feature(6, mock_params_fs)
    print("\nOutcome for 6 triggering scatters (expect spins for max defined, e.g. 5):")
    print(f"  Total Payout: {fs_outcome_6_scatters['total_feature_payout']}")
    print(f"  Spins Played: {fs_outcome_6_scatters['spins_played']}")
    print(f"  Events[0]: {fs_outcome_6_scatters['events'][0] if fs_outcome_6_scatters['events'] else 'N/A'}")
