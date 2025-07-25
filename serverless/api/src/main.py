from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from aws_lambda_powertools import Logger
import os
import boto3
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Initialize
app = FastAPI(title="Tilts API", version="1.0.0")
logger = Logger()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS Clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# Environment
TABLE_PREFIX = os.environ.get('DYNAMODB_TABLE_PREFIX', 'tilts-dev')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'tilts-data-dev')
QUEUE_URL = os.environ.get('SQS_QUEUE_URL', '')

# Models
class GameRequest(BaseModel):
    model_name: str
    num_games: int = 10
    board_size: int = 8
    num_mines: int = 10

class LeaderboardEntry(BaseModel):
    model_name: str
    win_rate: float
    valid_move_rate: float
    games_played: int
    last_updated: str

# Routes
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "tilts-api",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard():
    try:
        table = dynamodb.Table(f"{TABLE_PREFIX}-leaderboard")
        response = table.scan()
        
        entries = []
        for item in response.get('Items', []):
            entries.append(LeaderboardEntry(
                model_name=item['model_name'],
                win_rate=float(item.get('win_rate', 0)),
                valid_move_rate=float(item.get('valid_move_rate', 0)),
                games_played=int(item.get('games_played', 0)),
                last_updated=item.get('last_updated', '')
            ))
        
        # Sort by win rate
        entries.sort(key=lambda x: x.win_rate, reverse=True)
        return entries
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")

@app.post("/games/start")
def start_game(request: GameRequest):
    try:
        # Send to SQS for processing
        message = {
            "model_name": request.model_name,
            "num_games": request.num_games,
            "board_size": request.board_size,
            "num_mines": request.num_mines,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if QUEUE_URL:
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(message)
            )
        
        return {
            "status": "queued",
            "job_id": f"{request.model_name}-{datetime.utcnow().timestamp()}",
            "message": f"Evaluation of {request.num_games} games queued for {request.model_name}"
        }
        
    except Exception as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start game")

@app.get("/games/{game_id}")
def get_game(game_id: str):
    try:
        table = dynamodb.Table(f"{TABLE_PREFIX}-games")
        response = table.get_item(Key={'id': game_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Game not found")
            
        return response['Item']
        
    except Exception as e:
        logger.error(f"Error fetching game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch game")

@app.get("/models")
def get_supported_models():
    return {
        "models": [
            {"name": "gpt-4", "provider": "openai"},
            {"name": "gpt-4-turbo", "provider": "openai"},
            {"name": "claude-3-opus", "provider": "anthropic"},
            {"name": "claude-3-sonnet", "provider": "anthropic"},
            {"name": "o1-preview", "provider": "openai"},
            {"name": "o1-mini", "provider": "openai"}
        ]
    }

# Lambda handler
handler = Mangum(app, lifespan="off")