// Formatting utilities

import { GameType, GameStatus, ModelProvider } from '../types';

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatGameStatus(status: GameStatus): string {
  const statusMap: Record<GameStatus, string> = {
    'in_progress': 'In Progress',
    'won': 'Won',
    'lost': 'Lost',
    'error': 'Error'
  };
  return statusMap[status] || status;
}

export function formatModelName(provider: ModelProvider, modelName: string): string {
  const providerPrefixes: Record<ModelProvider, string> = {
    'openai': 'GPT',
    'anthropic': 'Claude'
  };
  
  // Remove provider prefix if already in model name
  const prefix = providerPrefixes[provider];
  if (modelName.toLowerCase().includes(prefix.toLowerCase())) {
    return modelName;
  }
  
  return `${prefix} ${modelName}`;
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatGameType(gameType: GameType): string {
  const gameTypeMap: Record<GameType, string> = {
    'minesweeper': 'Minesweeper',
    'risk': 'Risk',
    'number_puzzle': 'Number Puzzle'
  };
  return gameTypeMap[gameType] || gameType;
}