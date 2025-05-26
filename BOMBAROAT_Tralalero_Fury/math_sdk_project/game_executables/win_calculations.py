# win_calculations.py

def get_symbol_type(symbol_id, symbols_data):
    """Helper to get symbol type, e.g., 'wild'."""
    if symbol_id in symbols_data:
        return symbols_data[symbol_id].get("type", "normal") # Assuming 'type' field in symbol definition
    return "normal"

def calculate_line_wins(grid, paylines, paytable, symbols_data):
    """
    Calculates wins based on paylines.
    - grid: A 2D list (4x5) representing the visible symbol IDs.
    - paylines: A list of payline definitions (list of (row, col) tuples).
    - paytable: A dictionary defining payouts {symbol_id: {match_count: payout_multiplier}}.
    - symbols_data: A dictionary of symbol properties {symbol_id: {..., 'type': 'wild'/'normal'}}.
    """
    line_wins = []
    total_payout_multiplier = 0

    if not grid or not paylines or not paytable or not symbols_data:
        print("Error: Missing critical data for win calculation.")
        return [], 0

    wild_symbol_id = None
    for sid, sdata in symbols_data.items():
        if sdata.get("name", "").lower() == "crocodrillo": # Assuming Crocodrillo is WILD
             wild_symbol_id = sid
             break
    if not wild_symbol_id: # Fallback if not found by name
        for sid, sdata in symbols_data.items():
            # Check for 'type' field if 'name' logic fails or isn't specific enough
            if sdata.get("type", "").lower() == "wild" or \
               "wild" in sdata.get("name","").lower() or \
               sid.upper() == "WILD":
                wild_symbol_id = sid
                break
    # print(f"Debug: Wild symbol identified as: {wild_symbol_id}")


    for i, line_coords in enumerate(paylines):
        line_symbols_ids = []
        try:
            for r, c in line_coords:
                line_symbols_ids.append(grid[r][c])
        except IndexError:
            # print(f"Warning: Payline {i} coordinates out of bounds for grid {grid}")
            continue

        # Determine the symbol to check for wins (first non-wild from left)
        # or if all wilds, take the wild symbol.
        line_eval_symbol_id = None
        for sym_id in line_symbols_ids:
            if sym_id != wild_symbol_id:
                line_eval_symbol_id = sym_id
                break
        if line_eval_symbol_id is None and wild_symbol_id in line_symbols_ids: # All wilds on the line
            line_eval_symbol_id = wild_symbol_id
        
        if not line_eval_symbol_id or line_eval_symbol_id not in paytable:
            continue # Not a paying symbol or no symbol to evaluate

        # Count matches from left
        match_count = 0
        for sym_id in line_symbols_ids:
            if sym_id == line_eval_symbol_id or sym_id == wild_symbol_id:
                match_count += 1
            else:
                break # Streak broken

        if match_count > 0 and line_eval_symbol_id in paytable and match_count in paytable[line_eval_symbol_id]:
            payout = paytable[line_eval_symbol_id][match_count]
            win_info = {
                "line_index": i,
                "symbol_id": line_eval_symbol_id,
                "match_count": match_count,
                "payout_multiplier": payout,
                "line_coordinates": line_coords
            }
            line_wins.append(win_info)
            total_payout_multiplier += payout
            
    return line_wins, total_payout_multiplier

def calculate_scatter_wins(grid, paytable, scatter_mult_symbol_id, symbols_data):
    """
    Calculates wins for scatter symbols (e.g., SCATTER_MULT).
    These symbols pay based on their count anywhere on the grid, not on paylines.
    """
    scatter_wins_list = []
    total_scatter_payout_multiplier = 0
    
    # Check if scatter_mult_symbol_id is defined in symbols_data and paytable
    if not grid or not paytable or not scatter_mult_symbol_id or \
       scatter_mult_symbol_id not in symbols_data or \
       scatter_mult_symbol_id not in paytable:
        # print(f"Debug: Scatter win check skipped. Scatter ID: {scatter_mult_symbol_id}, Present in paytable: {scatter_mult_symbol_id in paytable}")
        return [], 0

    count = 0
    positions = []
    for r_idx, row in enumerate(grid):
        for c_idx, symbol_id_on_grid in enumerate(row):
            if symbol_id_on_grid == scatter_mult_symbol_id:
                count += 1
                positions.append((r_idx, c_idx))
    
    if count > 0 and count in paytable[scatter_mult_symbol_id]:
        payout = paytable[scatter_mult_symbol_id][count]
        scatter_win_info = {
            "symbol_id": scatter_mult_symbol_id,
            "count": count,
            "payout_multiplier": payout,
            "positions": positions
        }
        scatter_wins_list.append(scatter_win_info)
        total_scatter_payout_multiplier = payout # Assuming one type of scatter_mult win at a time

    return scatter_wins_list, total_scatter_payout_multiplier

# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Mock data based on game_config.py structure
    mock_symbols = {
        "H1": {"id": "H1", "name": "Brainroat"}, 
        "WILD": {"id": "WILD", "name": "Crocodrillo", "type": "wild"}, # Added type for better wild ID
        "M1": {"id": "M1", "name": "Spaghetti"}, 
        "L1": {"id": "L1", "name": "Mask"},
        "SCATTER_MULT": {"id": "SCATTER_MULT", "name": "Lirili Larila"}
    }
    mock_paytable = {
        "H1": {3: 25, 4: 100, 5: 500}, 
        "WILD": {3:25, 4:100, 5:500}, # WILD can also form its own wins
        "M1": {3: 10, 4: 40, 5: 150}, 
        "L1": {3: 5, 4: 20, 5: 100},
        "SCATTER_MULT": {3: 5, 4: 15, 5: 50}
    }
    mock_paylines = [
        [(0,0),(0,1),(0,2),(0,3),(0,4)], # Line 0
        [(1,0),(1,1),(1,2),(1,3),(1,4)], # Line 1
    ]
    
    # Test grid 1: H1 win on line 0
    test_grid_1 = [
        ["H1", "H1", "H1", "M1", "L1"],
        ["L1", "M1", "L1", "M1", "L1"],
        ["M1", "L1", "M1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "L1"],
    ]
    
    line_wins_1, total_line_payout_1 = calculate_line_wins(test_grid_1, mock_paylines, mock_paytable, mock_symbols)
    print("Test Grid 1 Line Wins:", line_wins_1)
    print("Test Grid 1 Total Line Payout:", total_line_payout_1) # Expected: 25

    # Test grid 2: Wilds completing H1 win on line 1
    test_grid_2 = [
        ["M1", "M1", "M1", "M1", "L1"],
        ["H1", "WILD", "WILD", "H1", "L1"], 
        ["M1", "L1", "M1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "L1"],
    ]
    # Expected: H1, 3 matches on line_index 1 (H1, WILD, WILD counts as 3xH1)
    line_wins_2, total_line_payout_2 = calculate_line_wins(test_grid_2, mock_paylines, mock_paytable, mock_symbols)
    print("\nTest Grid 2 Line Wins:", line_wins_2) 
    print("Test Grid 2 Total Line Payout:", total_line_payout_2) # Expected: 25

    # Test grid 3: Scatter win
    test_grid_3 = [
        ["SCATTER_MULT", "M1", "SCATTER_MULT", "M1", "L1"],
        ["L1", "SCATTER_MULT", "L1", "M1", "L1"],
        ["M1", "L1", "H1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "SCATTER_MULT"], # 4 SCATTER_MULT
    ]
    scatter_wins_3, total_scatter_payout_3 = calculate_scatter_wins(test_grid_3, mock_paytable, "SCATTER_MULT", mock_symbols)
    print("\nTest Grid 3 Scatter Wins:", scatter_wins_3)
    print("Test Grid 3 Total Scatter Payout:", total_scatter_payout_3) # Expected: 15

    # Test grid 4: All wilds on a line
    test_grid_4 = [
        ["WILD", "WILD", "WILD", "WILD", "WILD"],
        ["L1", "M1", "L1", "M1", "L1"],
        ["M1", "L1", "M1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "L1"],
    ]
    line_wins_4, total_line_payout_4 = calculate_line_wins(test_grid_4, mock_paylines, mock_paytable, mock_symbols)
    print("\nTest Grid 4 (All Wilds) Line Wins:", line_wins_4)
    print("Test Grid 4 Total Line Payout:", total_line_payout_4) # Expected: 500 (if WILD pays like H1)
    
    # Test grid 5: No wins
    test_grid_5 = [
        ["L1", "M1", "H1", "M1", "L1"],
        ["M1", "L1", "M1", "L1", "M1"],
        ["L1", "M1", "L1", "M1", "L1"],
        ["H1", "L1", "H1", "L1", "H1"],
    ]
    line_wins_5, total_line_payout_5 = calculate_line_wins(test_grid_5, mock_paylines, mock_paytable, mock_symbols)
    print("\nTest Grid 5 (No Wins) Line Wins:", line_wins_5)
    print("Test Grid 5 Total Line Payout:", total_line_payout_5) # Expected: 0
    scatter_wins_5, total_scatter_payout_5 = calculate_scatter_wins(test_grid_5, mock_paytable, "SCATTER_MULT", mock_symbols)
    print("Test Grid 5 Scatter Wins:", scatter_wins_5) # Expected: []
    print("Test Grid 5 Total Scatter Payout:", total_scatter_payout_5) # Expected: 0`win_calculations.py` has been updated. I've made a few minor adjustments to the provided code for robustness:
- Added a more comprehensive fallback for `wild_symbol_id` detection, checking for a `type: "wild"` in `symbols_data` or "wild" in the name/ID as fallbacks.
- Ensured `line_eval_symbol_id` is in `paytable` before attempting to access `paytable[line_eval_symbol_id]`.
- Added more checks in `calculate_scatter_wins` to ensure `scatter_mult_symbol_id` is valid and present in `symbols_data` and `paytable` before proceeding.
- Added `type: "wild"` to the "WILD" symbol in the `if __name__ == "__main__":` mock data for testing the improved wild detection.

Now, I will update `BOMBAROAT_Tralalero_Fury/math_sdk_project/game_executables/base_game_calculations.py`.
