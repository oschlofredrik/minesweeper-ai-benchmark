import { StreamData, createStreamDataTransformer } from 'ai';

/**
 * Streaming utilities for Vercel AI SDK
 * Handles real-time streaming of game moves and evaluation progress
 */

export interface GameMoveEvent {
  type: 'move';
  moveNumber: number;
  action: string;
  position?: { row: number; col: number };
  territory?: string;
  reasoning?: string;
  valid: boolean;
  gameState?: any;
  boardState?: string;
}

export interface GameStatusEvent {
  type: 'status';
  message: string;
  gameNumber?: number;
  totalGames?: number;
}

export interface GameCompleteEvent {
  type: 'complete';
  gameId: string;
  won: boolean;
  moves: number;
  duration: number;
  coverage?: number;
  finalState?: any;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
  code?: string;
}

export type StreamEvent = GameMoveEvent | GameStatusEvent | GameCompleteEvent | ErrorEvent;

/**
 * Create a stream data handler for game events
 */
export function createGameStreamData() {
  const streamData = new StreamData();
  
  const sendEvent = (event: StreamEvent) => {
    streamData.append({
      timestamp: new Date().toISOString(),
      ...event
    });
  };
  
  const sendMove = (move: Omit<GameMoveEvent, 'type'>) => {
    sendEvent({ type: 'move', ...move });
  };
  
  const sendStatus = (message: string, extra?: Partial<GameStatusEvent>) => {
    sendEvent({ type: 'status', message, ...extra });
  };
  
  const sendComplete = (complete: Omit<GameCompleteEvent, 'type'>) => {
    sendEvent({ type: 'complete', ...complete });
  };
  
  const sendError = (message: string, code?: string) => {
    sendEvent({ type: 'error', message, code });
  };
  
  const close = () => {
    streamData.close();
  };
  
  return {
    streamData,
    sendMove,
    sendStatus,
    sendComplete,
    sendError,
    close
  };
}

/**
 * Transform tool call results into stream events
 */
export function createToolCallTransformer(gameType: string) {
  return createStreamDataTransformer({
    onToolCall: async ({ toolCall }) => {
      const { toolName, args } = toolCall;
      
      // Extract common fields
      const moveData: Partial<GameMoveEvent> = {
        action: toolName,
        reasoning: args.reasoning
      };
      
      // Add game-specific fields
      if (gameType === 'minesweeper') {
        if (args.row !== undefined && args.col !== undefined) {
          moveData.position = { row: args.row, col: args.col };
        }
      } else if (gameType === 'risk') {
        if (args.territory) {
          moveData.territory = args.territory;
        } else if (args.fromTerritory && args.toTerritory) {
          moveData.territory = `${args.fromTerritory} -> ${args.toTerritory}`;
        }
      }
      
      return moveData;
    }
  });
}

/**
 * Create a progress tracker for multi-game evaluations
 */
export class EvaluationProgress {
  private gamesCompleted = 0;
  private totalGames: number;
  private wins = 0;
  private totalMoves = 0;
  private startTime = Date.now();
  
  constructor(totalGames: number) {
    this.totalGames = totalGames;
  }
  
  completeGame(won: boolean, moves: number) {
    this.gamesCompleted++;
    if (won) this.wins++;
    this.totalMoves += moves;
  }
  
  getStats() {
    const duration = (Date.now() - this.startTime) / 1000;
    const winRate = this.gamesCompleted > 0 ? this.wins / this.gamesCompleted : 0;
    const avgMoves = this.gamesCompleted > 0 ? this.totalMoves / this.gamesCompleted : 0;
    
    return {
      gamesCompleted: this.gamesCompleted,
      totalGames: this.totalGames,
      wins: this.wins,
      winRate,
      avgMoves,
      duration,
      inProgress: this.gamesCompleted < this.totalGames
    };
  }
  
  getProgressPercentage() {
    return Math.round((this.gamesCompleted / this.totalGames) * 100);
  }
}