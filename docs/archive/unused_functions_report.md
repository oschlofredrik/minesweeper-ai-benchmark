# Unused Functions Analysis Report

## Summary
Analyzed the codebase for potentially unused functions in the specified directories. Found 32 potentially unused functions, but many have valid reasons for existing.

## Truly Unused Functions (Safe to Remove)

### 1. Core Utilities
- **`src/core/database.py`**
  - `evaluation_to_dict` (line 263) - Not used anywhere, the storage module imports it but doesn't use it

### 2. API Database Utilities  
- **`src/api/db_utils.py`**
  - `get_existing_columns` (line 10) - Only defined, never called

### 3. Evaluation Metrics
- **`src/evaluation/advanced_metrics.py`**
  - `calculate_all_metrics` (line 298) - Only referenced in docs, not in actual code
  - `create_leaderboard_entry` (line 436) - Not used in implementation

- **`src/evaluation/engine.py`**
  - `compare_models_with_significance` (line 349) - Not called anywhere

- **`src/evaluation/episode_logger.py`**
  - `save_batch_results` (line 73) - Not used

- **`src/evaluation/reasoning_judge.py`**
  - `judge_batch` (line 238) - Not used
  - `generate_feedback_summary` (line 322) - Not used
  - `judge_game_reasoning` (line 368) - Standalone function not used

### 4. Statistical Analysis
- **`src/evaluation/statistical_analysis.py`**
  - `calculate_sample_size` (line 232) - Not used
  - `analyze_metrics_comparison` (line 270) - Not used
  - `create_comparison_report` (line 339) - Not used
  - `quick_significance_test` (line 391) - Not used
  - `calculate_wilson_interval` (line 421) - Not used

### 5. Game Logic
- **`src/games/minesweeper/game.py`**
  - `get_valid_moves` (line 289) - Not used in current implementation

- **`src/games/minesweeper/solver.py`**
  - `find_mine_positions` (line 49) - Not used
  - `get_probabilities` (line 61) - Not used  
  - `is_solvable_without_guessing` (line 222) - Not used

### 6. Model Base Class
- **`src/models/base.py`**
  - `generate_with_retry` (line 64) - Not used (retry logic is elsewhere)

## Functions That Appear Unused But Are Actually Used

### 1. Background Task Functions (Used by asyncio)
- **`src/api/evaluation_endpoints.py`**
  - `run_task_generation` - Used as background task via asyncio.create_task
  - `run_evaluation_job` - Used as background task via asyncio.create_task

- **`src/api/play_endpoints.py`**
  - `run_play_session` - Used as background task via asyncio.create_task

### 2. Event Streaming Functions (Imported and Used)
- **`src/api/event_streaming.py`**
  - `publish_game_started` - Imported and used in streaming_runner.py and play_endpoints.py

### 3. Storage Backend Methods (Abstract Base Class)
- **`src/core/storage.py`**
  - `save_game` - Abstract method, implemented in subclasses
  - `save_evaluation` - Abstract method, implemented in subclasses
  - `load_task` - Abstract method, implemented in subclasses

### 4. Model Configuration (Imported and Used)
- **`src/models/model_config.py`**
  - `get_model_timeout` - Imported and used in openai.py

### 5. Logging Functions (May Be Used Later)
- **`src/core/logging_config.py`**
  - `log_evaluation_progress` - Imported in evaluation_endpoints.py (might be used)
  - `log_api_request` - Utility function for API logging
  - `log_model_error` - Utility function for error logging

### 6. Streaming Methods (Part of API)
- **`src/evaluation/streaming_runner.py`**
  - `stream_reasoning` - Method on streaming runner class

### 7. Property Method
- **`src/evaluation/statistical_analysis.py`**
  - `SignificanceTestResult.summary` - Property method, might be accessed

## Recommendations

### Safe to Remove:
1. All functions in the "Truly Unused Functions" section above
2. These appear to be leftover from earlier implementations or planned features that weren't completed

### Keep for Now:
1. Logging functions - might be useful for future debugging
2. Abstract methods - required for interface definition
3. Background task functions - actively used by async operations

### Consider Refactoring:
1. Statistical analysis functions - seem to be a comprehensive stats module that's not integrated
2. Solver methods - might be useful for AI opponents or hints feature
3. Advanced metrics - could be integrated into the evaluation pipeline

## Dead Code Patterns Found:
1. **Unused statistical analysis module** - Comprehensive but not integrated
2. **Solver capabilities** - Advanced solver methods not used by current AI evaluation
3. **Batch processing methods** - Several batch methods not used (single game processing used instead)
4. **Database serialization** - Some dict conversion functions not needed with current storage