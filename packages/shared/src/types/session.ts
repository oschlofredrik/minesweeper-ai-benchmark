// Session and competition-related types

export interface Session {
  sessionId: string;
  joinCode: string;
  name: string;
  host: string;
  status: 'waiting' | 'active' | 'completed';
  gameType: string;
  difficulty: string;
  numGames: number;
  participants: Participant[];
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export interface Participant {
  playerId: string;
  name: string;
  modelName: string;
  provider: string;
  status: 'joined' | 'ready' | 'playing' | 'finished';
  currentGame?: number;
  results?: ParticipantResults;
}

export interface ParticipantResults {
  wins: number;
  losses: number;
  errors: number;
  averageMoves: number;
  averageDuration: number;
  totalScore: number;
}