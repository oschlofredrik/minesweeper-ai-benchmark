// Validation utilities

import { GameType, ModelProvider } from '../types';

// Temporarily removed zod dependency - to be restored after workspace setup

// Helper functions
export function isValidGameType(value: string): value is GameType {
  return ['minesweeper', 'risk', 'number_puzzle'].includes(value);
}

export function isValidProvider(value: string): value is ModelProvider {
  return ['openai', 'anthropic'].includes(value);
}

export function getMoveSchema(_gameType: GameType) {
  // Temporary implementation without zod
  return null;
}