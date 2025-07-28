# Unused Functions Analysis

## Summary

Based on the grep analysis, the following functions appear to be unused in the codebase (only found in their definition files and the unused_functions_report.md):

### 1. `src/core/database.py`
- **Function**: `evaluation_to_dict`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

### 2. `src/api/db_utils.py`
- **Function**: `get_existing_columns`
- **Status**: UNUSED - Only found in definition file  
- **Safe to delete**: YES

### 3. `src/evaluation/advanced_metrics.py`
- **Function**: `calculate_all_metrics`
- **Status**: UNUSED - Only referenced in documentation (docs/evaluation.md), not in actual code
- **Safe to delete**: YES, but update documentation

- **Function**: `create_leaderboard_entry`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

### 4. `src/evaluation/engine.py`
- **Function**: `compare_models_with_significance`
- **Status**: USED - Found in test_advanced_evaluation.py
- **Safe to delete**: NO - Used in tests

### 5. `src/evaluation/episode_logger.py`
- **Function**: `save_batch_results`
- **Status**: UNUSED - Only referenced in documentation
- **Safe to delete**: YES, but update documentation

### 6. `src/evaluation/reasoning_judge.py`
- **Function**: `judge_batch`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

- **Function**: `generate_feedback_summary`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

- **Function**: `judge_game_reasoning`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

### 7. `src/evaluation/statistical_analysis.py`
Several methods in the `StatisticalAnalyzer` class are unused:
- **Function**: `calculate_sample_size`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

- **Function**: `analyze_metrics_comparison`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

- **Function**: `create_comparison_report`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

Note: The core methods `calculate_confidence_interval`, `test_proportion_difference`, and `test_mean_difference` ARE used by other parts of the codebase.

### 8. `src/games/minesweeper/game.py`
- **Function**: `get_valid_moves`
- **Status**: DOES NOT EXIST - This function doesn't exist in minesweeper/game.py (only in tilts/game.py)
- **Safe to delete**: N/A

### 9. `src/games/minesweeper/solver.py`
- **Function**: `find_mine_positions`
- **Status**: DOES NOT EXIST - Not found in minesweeper/solver.py
- **Safe to delete**: N/A

- **Function**: `get_probabilities`
- **Status**: DOES NOT EXIST - Not found in minesweeper/solver.py
- **Safe to delete**: N/A

- **Function**: `is_solvable_without_guessing`
- **Status**: DOES NOT EXIST - Not found in minesweeper/solver.py
- **Safe to delete**: N/A

### 10. `src/models/base.py`
- **Function**: `generate_with_retry`
- **Status**: UNUSED - Only found in definition file
- **Safe to delete**: YES

## Recommendations

1. **Safe to delete immediately** (12 functions):
   - `evaluation_to_dict`
   - `get_existing_columns`
   - `calculate_all_metrics` (update docs)
   - `create_leaderboard_entry`
   - `save_batch_results` (update docs)
   - `judge_batch`
   - `generate_feedback_summary`
   - `judge_game_reasoning`
   - `calculate_sample_size`
   - `analyze_metrics_comparison`
   - `create_comparison_report`
   - `generate_with_retry`

2. **Keep** (1 function):
   - `compare_models_with_significance` - Used in tests

3. **Non-existent** (4 functions):
   - The minesweeper game/solver functions listed don't exist in those files

## Notes
- Some functions are referenced in documentation but not used in actual code
- The statistical analysis module has several unused methods that could be removed
- The quick_significance_test and calculate_wilson_interval functions ARE used elsewhere