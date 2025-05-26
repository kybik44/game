# run.py for BOMBAROAT™: Tralalero Fury
import json
import random

# Assuming game_config and game_executables are in the same package or PYTHONPATH is set up
# For the subtask environment, we hope these imports work directly.
# If this script were in the parent of game_config etc., it would be:
# from .game_config import GameParams
# from .game_executables.base_game_calculations import evaluate_base_spin_outcome
# etc.
# However, given it's in the same directory as game_config.py for this project:
from game_config import GameParams
from game_executables.base_game_calculations import evaluate_base_spin_outcome
from game_executables.tralalero_free_spins_calculations import simulate_tralalero_free_spins_feature
from game_executables.bombardino_bonus_calculations import simulate_bombardino_bonus_feature

# --- SDK-like Simulation Parameters ---
NUM_SIM_ARGS = {
    "base": int(1e5),  # 100,000 base game spins
    "tralalero_free_spins": int(1e4), # 10,000 full free spin features
    "bombardino_bonus": int(1e4),    # 10,000 full bonus features
}

RUN_CONDITIONS = {
    "run_sims": True,
    "run_optimization": True, # Set to True for the conceptual RTP tuning stage
    "run_analysis": True,     # Set to True for PAR sheet generation
    "compression": True,      # Production runs would use compression
}

# --- Placeholder for SDK's Reel/Grid Generation ---
def sdk_generate_grid_from_reels(game_params_obj):
    """
    Placeholder: Simulates generating a grid from reel strips.
    The real SDK would use its own PRNG and reel strip definitions.
    Output is a 4x5 grid of symbol IDs.
    """
    grid = [[None for _ in range(game_params_obj.GRID_COLS)] for _ in range(game_params_obj.GRID_ROWS)]
    for c in range(game_params_obj.GRID_COLS):
        reel_id = f"reel_{c+1}"
        strip = game_params_obj.REEL_STRIPS.get(reel_id, [])
        if not strip:
            # Fallback if specific reel not found or empty, use a generic list of symbols
            # This ensures robustness if REEL_STRIPS is not perfectly defined
            all_possible_symbols = list(game_params_obj.SYMBOLS.keys())
            if not all_possible_symbols: # Should not happen with valid GameParams
                all_possible_symbols = ["L1"] # Absolute fallback
            strip = all_possible_symbols * (game_params_obj.GRID_ROWS + 5) # Make strip long enough
        
        # Ensure strip is not empty before random.randint
        if not strip: # This case should ideally be prevented by the fallback above
             print(f"Error: Reel strip for {reel_id} is empty even after fallback.")
             # Fill column with a default symbol if strip is truly empty
             for r in range(game_params_obj.GRID_ROWS):
                 grid[r][c] = "L1" # Default symbol
             continue


        start_pos = random.randint(0, len(strip) - 1)
        for r in range(game_params_obj.GRID_ROWS):
            pos = (start_pos + r) % len(strip) # Ensure wrap-around for reel effect
            grid[r][c] = strip[pos]
    return grid

# --- Main Simulation Logic ---
def run_simulations(game_params_obj):
    all_book_entries = {"base": [], "tralalero_free_spins": [], "bombardino_bonus": []}
    all_lookup_entries = {"base": [], "tralalero_free_spins": [], "bombardino_bonus": []}
    sim_id_counter = 1 # Ensure unique IDs across all simulation types for this run

    # 1. Base Game Simulations
    if RUN_CONDITIONS["run_sims"] and NUM_SIM_ARGS.get("base", 0) > 0:
        print(f"\n--- Simulating Base Game ({NUM_SIM_ARGS['base']} spins) ---")
        for i in range(NUM_SIM_ARGS["base"]):
            current_sim_id = sim_id_counter + i
            grid = sdk_generate_grid_from_reels(game_params_obj)
            base_game_outcome = evaluate_base_spin_outcome(grid, game_params_obj)
            
            # Construct book entry (simplified for this subtask)
            book_entry = {
                "id": current_sim_id,
                "mode": "base",
                "payoutMultiplier": base_game_outcome["total_payout_multiplier"],
                "events": [
                    {"type": "grid_reveal", "grid": grid}, # Changed from "reveal"
                    {"type": "wins_info", "line_wins": base_game_outcome["line_wins"], "scatter_wins": base_game_outcome["scatter_wins"]}, # Changed from "winsInfo"
                    {"type": "feature_triggers", "features": base_game_outcome["triggered_features"]} # Changed from "triggers"
                ]
            }
            all_book_entries["base"].append(book_entry)
            
            # Construct lookup entry (weight is 1 before optimization)
            lookup_entry = f"{current_sim_id},1,{base_game_outcome['total_payout_multiplier']}"
            all_lookup_entries["base"].append(lookup_entry)
        sim_id_counter += NUM_SIM_ARGS["base"]

    # 2. Tralalero Free Spins Feature Simulations
    if RUN_CONDITIONS["run_sims"] and NUM_SIM_ARGS.get("tralalero_free_spins", 0) > 0:
        print(f"\n--- Simulating Tralalero Free Spins ({NUM_SIM_ARGS['tralalero_free_spins']} features) ---")
        for i in range(NUM_SIM_ARGS["tralalero_free_spins"]):
            current_sim_id = sim_id_counter + i
            # Assume triggered by 3 scatters for simulation purposes
            triggering_scatter_count = 3 
            fs_outcome = simulate_tralalero_free_spins_feature(triggering_scatter_count, game_params_obj)
            
            book_entry = {
                "id": current_sim_id,
                "mode": "tralalero_free_spins",
                "triggering_scatters": triggering_scatter_count,
                "payoutMultiplier": fs_outcome["total_feature_payout"],
                "spins_played": fs_outcome["spins_played"],
                "retriggered_times": fs_outcome["retriggered_times"],
                "detailed_events": fs_outcome["events"] # Contains log from feature
            }
            all_book_entries["tralalero_free_spins"].append(book_entry)
            lookup_entry = f"{current_sim_id},1,{fs_outcome['total_feature_payout']}"
            all_lookup_entries["tralalero_free_spins"].append(lookup_entry)
        sim_id_counter += NUM_SIM_ARGS["tralalero_free_spins"]

    # 3. Bombardino Bonus Feature Simulations
    if RUN_CONDITIONS["run_sims"] and NUM_SIM_ARGS.get("bombardino_bonus", 0) > 0:
        print(f"\n--- Simulating Bombardino Bonus ({NUM_SIM_ARGS['bombardino_bonus']} features) ---")
        for i in range(NUM_SIM_ARGS["bombardino_bonus"]):
            current_sim_id = sim_id_counter + i
            # Assume triggered by 3 bonus symbols
            triggering_bonus_count = 3 
            bonus_outcome = simulate_bombardino_bonus_feature(game_params_obj, triggering_bonus_count=triggering_bonus_count)
            
            book_entry = {
                "id": current_sim_id,
                "mode": "bombardino_bonus",
                "triggering_bonus_symbols": triggering_bonus_count,
                "payoutMultiplier": bonus_outcome["total_feature_payout"],
                "spins_played": bonus_outcome["spins_played"],
                "detailed_events": bonus_outcome["events"]
            }
            all_book_entries["bombardino_bonus"].append(book_entry)
            lookup_entry = f"{current_sim_id},1,{bonus_outcome['total_feature_payout']}"
            all_lookup_entries["bombardino_bonus"].append(lookup_entry)
        # sim_id_counter += NUM_SIM_ARGS["bombardino_bonus"] # Not needed after last loop

    # Outputting (Conceptual - real SDK would write to files)
    print("\n--- Conceptual Output ---")
    if not RUN_CONDITIONS["compression"]: # Based on SDK docs, compression=false means JSONL
        print("\nBook Entries (JSONL format - first entry sample per mode):")
        for mode, entries in all_book_entries.items():
            if entries:
                print(f"--- {mode} mode (first entry) ---")
                print(json.dumps(entries[0])) 
    
    print("\nLookup Table Entries (CSV format - first entry sample per mode):")
    for mode, entries in all_lookup_entries.items():
        if entries:
            print(f"--- {mode} mode (first entry) ---")
            print(f"id,probability_weight,payoutMultiplier") # Header
            print(entries[0])

    print("\nTODO: Implement actual SDK file writing for books and lookup tables.")
    print("TODO: Integrate SDK's optimization and analysis phases (e.g., PAR sheet generation).")

if __name__ == "__main__":
    print("Starting BOMBAROAT Math SDK project simulation run...")
    # Initialize GameParams (assuming game_config.py is in the same directory or python path)
    game_params = GameParams() 
    
    print("\nPreparing for large-scale simulation and SDK optimization...")
    print(f"Target RTP: ~96.5%, Volatility: Medium-High (from game design)") # Target info
    print(f"Simulating with: {NUM_SIM_ARGS}")
    print(f"Run conditions (conceptual for SDK): {RUN_CONDITIONS}")
    
    if RUN_CONDITIONS["run_sims"]:
        run_simulations(game_params) # This generates the initial books/lookups
    else:
        print("Simulations skipped as per RUN_CONDITIONS.")

    print("\n--- SDK Post-Simulation Steps (Conceptual) ---")
    print("1. The generated 'lookup_tables/*.csv' would now be processed by the Math SDK's optimization tool.")
    print("2. The optimization tool adjusts symbol/event probabilities (weights in lookup tables) to meet the target RTP.")
    print("3. The Math SDK's analysis tool would generate a PAR sheet from the optimized tables and simulation books.")
    print("4. Iteration: If RTP or volatility targets are not met, adjust game_config.py (reel_strips, paytable, feature logic) " + \
           "and re-run simulations and optimization until targets are achieved.")
    
    print("\nRun complete.")
