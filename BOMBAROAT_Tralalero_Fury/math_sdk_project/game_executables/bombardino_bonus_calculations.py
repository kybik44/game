# bombardino_bonus_calculations.py
import random
import win_calculations # Assumed accessible

# Placeholder for grid generation, similar to free spins module
def generate_grid_for_bonus_spin(game_params):
    # Ensure all symbol IDs used are valid keys in game_params.SYMBOLS
    valid_symbol_ids = list(game_params.SYMBOLS.keys())
    if not valid_symbol_ids:
        print("Error: No symbols defined in game_params.SYMBOLS for grid generation.")
        return [["L1"] * game_params.GRID_COLS for _ in range(game_params.GRID_ROWS)]

    grid = [[random.choice(valid_symbol_ids) for _ in range(game_params.GRID_COLS)] for _ in range(game_params.GRID_ROWS)]
    # print("Warning: Bonus spin grid generation is using random.choice (placeholder).")
    return grid

def apply_wild_expansions(grid, game_params):
    """
    Applies random wild expansions based on config.
    """
    transformed_grid = [row[:] for row in grid] # Create a copy
    
    if not hasattr(game_params, 'bombardino_bonus_config') or \
       not isinstance(game_params.bombardino_bonus_config, dict):
        print("Warning: bombardino_bonus_config not found or invalid in game_params.")
        return transformed_grid
        
    config = game_params.bombardino_bonus_config
    
    wild_symbol_id = None # Determine WILD symbol ID from game_params.SYMBOLS
    for sid, sdata in game_params.SYMBOLS.items():
        if sdata.get("name", "").lower() == "crocodrillo": # Crocodrillo is WILD
             wild_symbol_id = sid
             break
    if not wild_symbol_id: # Fallback
        for sid, sdata in game_params.SYMBOLS.items():
            if sdata.get("type", "").lower() == "wild" or \
               "wild" in sdata.get("name","").lower() or \
               sid.upper() == "WILD":
                wild_symbol_id = sid
                break
    if not wild_symbol_id:
        print("Error: WILD symbol ID could not be determined for wild expansion.")
        return transformed_grid # Cannot proceed without knowing what a WILD is


    if config.get("wild_expansion_type") == "add_random_wilds":
        min_add = config.get("min_wilds_to_add", 1) # Default to 1 if not specified
        max_add = config.get("max_wilds_to_add", 1) # Default to 1 if not specified
        num_wilds_to_add = random.randint(min_add, max_add)
        
        empty_positions = []
        for r_idx, row in enumerate(transformed_grid):
            for c_idx, symbol_id_on_grid in enumerate(row):
                if symbol_id_on_grid != wild_symbol_id: # Don't replace existing wilds ideally
                    empty_positions.append((r_idx, c_idx))
        
        random.shuffle(empty_positions)
        for i in range(min(num_wilds_to_add, len(empty_positions))):
            r, c = empty_positions[i]
            transformed_grid[r][c] = wild_symbol_id
            # print(f"Debug: Added WILD at ({r},{c}) for Bombardino Bonus")

    elif config.get("wild_expansion_type") == "expand_existing_wilds":
        # Placeholder for expanding existing wilds (e.g., full reel or pattern)
        # This would require more complex logic to find existing wilds and expand them.
        # For now, let's just add 1-2 extra wilds like the other mode for simplicity of this subtask.
        num_wilds_to_add = random.randint(1, 2) # Simplified placeholder
        empty_positions = []
        for r_idx, row in enumerate(transformed_grid):
            for c_idx, symbol_id_on_grid in enumerate(row):
                if symbol_id_on_grid != wild_symbol_id:
                    empty_positions.append((r_idx, c_idx))
        random.shuffle(empty_positions)
        for i in range(min(num_wilds_to_add, len(empty_positions))):
            r, c = empty_positions[i]
            transformed_grid[r][c] = wild_symbol_id
        # print("Warning: 'expand_existing_wilds' in Bombardino is using placeholder logic (adds 1-2 random wilds).")
        pass
            
    return transformed_grid

def simulate_bombardino_bonus_feature(game_params, triggering_bonus_count=0, initial_grid=None):
    """
    Simulates the entire Bombardino Bonus feature.
    - game_params: Instance of GameParams.
    - triggering_bonus_count: Number of BONUS symbols that triggered (optional, for future extension)
    - initial_grid: The grid that triggered the feature (optional, for context).
    """
    if not hasattr(game_params, 'bombardino_bonus_config') or \
       not isinstance(game_params.bombardino_bonus_config, dict):
        print("Error: bombardino_bonus_config missing or invalid in game_params.")
        return {"total_feature_payout": 0, "spins_played": 0, "events": ["Bonus config error."]}

    bonus_config = game_params.bombardino_bonus_config
    num_bonus_spins = bonus_config.get("num_bonus_spins", 0) # Default to 0 if not specified
    
    if num_bonus_spins == 0:
         return {"total_feature_payout": 0, "spins_played": 0, "events": ["No bonus spins awarded due to config."]}

    total_feature_payout = 0
    feature_events = []
    spins_played_count = 0

    feature_events.append(f"Bombardino Bonus triggered with {triggering_bonus_count} symbols: {num_bonus_spins} bonus spins.")

    for i in range(num_bonus_spins):
        spins_played_count += 1
        
        spin_grid = generate_grid_for_bonus_spin(game_params)
        transformed_grid = apply_wild_expansions(spin_grid, game_params)
        
        feature_events.append({
            "spin_number": spins_played_count,
            "action": "wild_expansion",
            "expansion_type": bonus_config.get("wild_expansion_type", "unknown")
            # For detailed logging, one might include which wilds were added/expanded
        })
        
        line_wins, line_payout = win_calculations.calculate_line_wins(
            transformed_grid, game_params.PAYLINES, game_params.PAYTABLE, game_params.SYMBOLS
        )
        
        # Scatter wins are typically not part of these types of "sticky/expanding wild" bonus spins
        # unless specifically designed. Assuming only line wins contribute for Bombardino.
        spin_total_payout = line_payout 
        total_feature_payout += spin_total_payout
        
        if spin_total_payout > 0:
            feature_events.append({
                "spin_number": spins_played_count,
                "wins_this_spin": spin_total_payout,
                "line_wins_count": len(line_wins)
            })
            
    feature_events.append("Bombardino Bonus complete.")
            
    return {
        "total_feature_payout": total_feature_payout,
        "spins_played": spins_played_count,
        "events": feature_events,
        "final_grid_example_if_needed": transformed_grid # Example
    }

# Example Usage (for testing this module directly)
if __name__ == "__main__":
    class MockGameParams: 
        def __init__(self):
            self.GRID_ROWS = 4
            self.GRID_COLS = 5
            self.SYMBOLS = { 
                "H1": {"id": "H1", "name": "Brainroat"}, 
                "WILD": {"id": "WILD", "name": "Crocodrillo", "type": "wild"}, # Ensure type for wild ID logic
                "M1": {"id": "M1", "name": "Spaghetti"}, 
                "L1": {"id": "L1", "name": "Mask"},
                "SCATTER_FS": {"id": "SCATTER_FS", "name": "Tralalero"}, # Not used here but part of full set
                "BONUS": {"id": "BONUS", "name": "Bombardino"} # Not used here but part of full set
            }
            # Using simple horizontal lines for mock test
            self.PAYLINES = [ [(r,c) for c in range(self.GRID_COLS)] for r in range(self.GRID_ROWS) ] 
            self.PAYTABLE = {
                "H1": {3: 25, 4: 100, 5: 500}, 
                "WILD": {3:25, 4:100, 5:500}, # WILD can also form its own wins
                "M1": {3: 10, 4: 40, 5: 150}, 
                "L1": {3: 5, 4: 20, 5: 100}
            }
            self.bombardino_bonus_config = {
                "num_bonus_spins": 3, # Short for testing
                "wild_expansion_type": "add_random_wilds", # "add_random_wilds" or "expand_existing_wilds"
                "min_wilds_to_add": 2, 
                "max_wilds_to_add": 3
            }
            # REEL_STRIPS not strictly needed for this direct test as grid is random

    mock_params_bb = MockGameParams()
    
    print("\n--- Bombardino Bonus Feature Simulation Test ---")
    # Simulate with a triggering count of 3 (example)
    bonus_outcome = simulate_bombardino_bonus_feature(mock_params_bb, triggering_bonus_count=3) 
    print("Outcome for Bombardino Bonus:")
    print(f"  Total Payout: {bonus_outcome['total_feature_payout']}")
    print(f"  Spins Played: {bonus_outcome['spins_played']}")
    # print(f"  Events: {bonus_outcome['events']}") # Can be verbose

    # Test with 'expand_existing_wilds' (using its current placeholder logic)
    mock_params_bb.bombardino_bonus_config["wild_expansion_type"] = "expand_existing_wilds"
    bonus_outcome_expand = simulate_bombardino_bonus_feature(mock_params_bb, triggering_bonus_count=3)
    print("\nOutcome for Bombardino Bonus (expand_existing_wilds placeholder):")
    print(f"  Total Payout: {bonus_outcome_expand['total_feature_payout']}")
    print(f"  Spins Played: {bonus_outcome_expand['spins_played']}")

    # Test with 0 bonus spins in config
    mock_params_bb.bombardino_bonus_config["num_bonus_spins"] = 0
    bonus_outcome_zero_spins = simulate_bombardino_bonus_feature(mock_params_bb, triggering_bonus_count=3)
    print("\nOutcome for Bombardino Bonus (0 spins in config):")
    print(f"  Total Payout: {bonus_outcome_zero_spins['total_feature_payout']}")
    print(f"  Spins Played: {bonus_outcome_zero_spins['spins_played']}")
    print(f"  Events: {bonus_outcome_zero_spins['events']}")
