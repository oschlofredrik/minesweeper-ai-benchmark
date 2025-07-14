#!/usr/bin/env python3
"""
Re-evaluate reasoning scores for existing games in the database using the AI judge.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.storage import get_storage
from src.core.database import get_db, LeaderboardEntry
from src.evaluation.reasoning_judge import ReasoningJudge
from src.core.logging_config import setup_logging
from src.core.types import GameTranscript

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger("reevaluate")


async def load_game_transcripts(model_name: str = None) -> dict:
    """Load game transcripts from results files."""
    results_dir = Path("data/results")
    transcripts_by_model = {}
    
    if not results_dir.exists():
        logger.error("No results directory found")
        return {}
    
    for result_file in results_dir.glob("*.json"):
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
            
            # Skip if not a play result
            if 'model_name' not in data:
                continue
                
            model = data['model_name']
            
            # Filter by model if specified
            if model_name and model != model_name:
                continue
            
            # Extract transcripts if available
            if 'transcripts' in data:
                if model not in transcripts_by_model:
                    transcripts_by_model[model] = []
                
                # Convert transcript data to GameTranscript objects
                for t_data in data['transcripts']:
                    try:
                        transcript = GameTranscript.from_dict(t_data)
                        transcripts_by_model[model].append(transcript)
                    except Exception as e:
                        logger.warning(f"Failed to parse transcript: {e}")
                        
        except Exception as e:
            logger.error(f"Error reading {result_file}: {e}")
    
    return transcripts_by_model


async def evaluate_model_reasoning(model_name: str, transcripts: list) -> float:
    """Evaluate reasoning for a model's games."""
    logger.info(f"Evaluating reasoning for {model_name} ({len(transcripts)} games)")
    
    # Initialize reasoning judge
    judge = ReasoningJudge()
    all_judgments = []
    
    # Process each transcript
    for i, transcript in enumerate(transcripts):
        try:
            logger.info(f"  Game {i+1}/{len(transcripts)}: {transcript.game_id}")
            
            # Judge all moves in the transcript
            judgments = await judge.judge_transcript(transcript)
            all_judgments.extend(judgments)
            
            logger.info(f"    Judged {len(judgments)} moves")
            
        except Exception as e:
            logger.error(f"  Failed to judge game {transcript.game_id}: {e}")
    
    # Calculate aggregate score
    if all_judgments:
        avg_score = judge.calculate_aggregate_score(all_judgments)
        logger.info(f"✅ {model_name}: Average reasoning score = {avg_score:.3f} ({len(all_judgments)} moves judged)")
        return avg_score
    else:
        logger.warning(f"❌ {model_name}: No moves to judge")
        return 0.0


async def update_database_scores(scores: dict):
    """Update reasoning scores in the database."""
    storage = get_storage()
    
    if not storage.use_database:
        logger.error("Database not configured")
        return
    
    try:
        db = next(get_db())
        
        for model_name, score in scores.items():
            # Find model in leaderboard
            provider = "openai" if "gpt" in model_name or "o1" in model_name or "o3" in model_name else "anthropic"
            
            entry = db.query(LeaderboardEntry).filter_by(
                model_name=model_name
            ).first()
            
            if entry:
                old_score = entry.reasoning_score
                entry.reasoning_score = score
                entry.updated_at = datetime.utcnow()
                logger.info(f"Updated {model_name}: {old_score:.3f} → {score:.3f}")
            else:
                logger.warning(f"No leaderboard entry found for {model_name}")
        
        db.commit()
        logger.info("✅ Database updated successfully")
        
    except Exception as e:
        logger.error(f"Failed to update database: {e}")
        db.rollback()
    finally:
        db.close()


async def main():
    """Main function to re-evaluate reasoning scores."""
    logger.info("=== Starting Reasoning Score Re-evaluation ===")
    
    # Check if we have API key for GPT-4
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set - required for reasoning judge")
        return
    
    # Load transcripts
    logger.info("Loading game transcripts...")
    transcripts_by_model = await load_game_transcripts()
    
    if not transcripts_by_model:
        logger.error("No transcripts found")
        return
    
    logger.info(f"Found transcripts for {len(transcripts_by_model)} models")
    
    # Evaluate each model
    scores = {}
    for model_name, transcripts in transcripts_by_model.items():
        score = await evaluate_model_reasoning(model_name, transcripts)
        scores[model_name] = score
    
    # Update database
    logger.info("\nUpdating database with new scores...")
    await update_database_scores(scores)
    
    # Summary
    logger.info("\n=== Summary ===")
    for model, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"{model:30s}: {score:.3f}")


if __name__ == "__main__":
    # Set environment variable to use reasoning judge
    os.environ["USE_REASONING_JUDGE"] = "true"
    
    asyncio.run(main())