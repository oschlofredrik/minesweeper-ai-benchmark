// Evaluation-related types

import { GameType, GameResult } from './game';
import { ModelConfig } from './model';

export interface EvaluationConfig {
  model: ModelConfig;
  gameType: GameType;
  numGames: number;
  difficulty: string;
  sessionId?: string;
  taskIds?: string[];
}

export interface EvaluationMetrics {
  winRate: number;
  validMoveRate: number;
  averageMoves: number;
  averageDuration: number;
  mineIdentificationPrecision?: number;
  mineIdentificationRecall?: number;
  boardCoverage?: number;
  reasoningScore?: number;
  compositeScore?: number;
}

export interface EvaluationResult {
  evaluationId: string;
  config: EvaluationConfig;
  games: GameResult[];
  metrics: EvaluationMetrics;
  startedAt: string;
  completedAt: string;
  errors?: string[];
}

export interface LeaderboardEntry {
  modelName: string;
  provider: string;
  gameType: GameType;
  metrics: EvaluationMetrics;
  gamesPlayed: number;
  lastUpdated: string;
  rank?: number;
}