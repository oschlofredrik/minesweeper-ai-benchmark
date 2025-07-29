// Game-related types shared across the platform

export type GameType = 'minesweeper' | 'risk' | 'number_puzzle';
export type GameDifficulty = 'beginner' | 'intermediate' | 'expert' | 'custom';
export type GameStatus = 'in_progress' | 'won' | 'lost' | 'error';
export type MoveAction = 'reveal' | 'flag' | 'unflag' | 'reinforce' | 'attack' | 'fortify' | 'end_turn';

export interface GameConfig {
  gameType: GameType;
  difficulty: GameDifficulty;
  customSettings?: Record<string, any>;
}

export interface GameState {
  gameId: string;
  gameType: GameType;
  status: GameStatus;
  board: any; // Specific to each game type
  moves: GameMove[];
  startedAt: string;
  endedAt?: string;
}

export interface GameMove {
  moveNumber: number;
  action: MoveAction;
  position?: { row: number; col: number };
  from?: string;
  to?: string;
  armies?: number;
  reasoning: string;
  timestamp: string;
  valid: boolean;
  result?: any;
}

export interface GameResult {
  gameId: string;
  gameType: GameType;
  status: GameStatus;
  moves: number;
  duration: number;
  score?: number;
  transcript: GameMove[];
}