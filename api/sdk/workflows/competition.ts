/**
 * Competition workflows using Vercel AI SDK
 * Implements multi-round tournaments and agent competitions
 */

import { generateText, streamText } from 'ai';
import { z } from 'zod';
import { 
  getModel, 
  ModelProvider, 
  ModelName 
} from '../models';
import { createGameInstance, GameInstance } from '../evaluation';
import { getMinesweeperTools } from '../tools/minesweeper';
import { getRiskTools } from '../tools/risk';

export interface CompetitionConfig {
  name: string;
  gameType: 'minesweeper' | 'risk';
  participants: Array<{
    provider: ModelProvider;
    model: ModelName;
    name?: string;
  }>;
  rounds: number;
  difficulty?: string;
  scenario?: string;
  rules?: {
    timeLimit?: number;
    maxMoves?: number;
    allowRetries?: boolean;
  };
}

export interface RoundResult {
  round: number;
  games: Array<{
    participant: string;
    won: boolean;
    moves: number;
    duration: number;
    reasoning?: string[];
  }>;
  standings: Array<{
    participant: string;
    wins: number;
    totalMoves: number;
    avgMoves: number;
  }>;
}

export interface CompetitionResult {
  id: string;
  name: string;
  startTime: Date;
  endTime: Date;
  rounds: RoundResult[];
  finalStandings: Array<{
    rank: number;
    participant: string;
    wins: number;
    winRate: number;
    avgMoves: number;
    totalGames: number;
  }>;
  winner: string;
}

/**
 * Run a multi-round competition between AI models
 */
export async function runCompetition(config: CompetitionConfig): Promise<CompetitionResult> {
  const competitionId = `comp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const startTime = new Date();
  const rounds: RoundResult[] = [];
  
  // Track overall statistics
  const stats = new Map<string, {
    wins: number;
    totalMoves: number;
    gamesPlayed: number;
  }>();
  
  // Initialize stats for each participant
  config.participants.forEach(p => {
    const name = p.name || `${p.provider}-${p.model}`;
    stats.set(name, { wins: 0, totalMoves: 0, gamesPlayed: 0 });
  });
  
  // Run each round
  for (let round = 1; round <= config.rounds; round++) {
    console.log(`[Competition] Starting round ${round}/${config.rounds}`);
    
    const roundGames = [];
    const roundStart = Date.now();
    
    // Each participant plays one game per round
    for (const participant of config.participants) {
      const participantName = participant.name || `${participant.provider}-${participant.model}`;
      console.log(`[Competition] ${participantName} playing round ${round}`);
      
      try {
        // Create fresh game instance
        const game = await createGameInstance(
          config.gameType,
          config.difficulty,
          config.scenario
        );
        
        // Get appropriate tools
        const tools = config.gameType === 'minesweeper' 
          ? getMinesweeperTools(game)
          : getRiskTools(game);
        
        // Run the game
        const gameStart = Date.now();
        const result = await runSingleGame(
          game,
          participant,
          tools,
          config.gameType,
          config.rules
        );
        const gameDuration = (Date.now() - gameStart) / 1000;
        
        // Record result
        const gameResult = {
          participant: participantName,
          won: result.won,
          moves: result.moves,
          duration: gameDuration,
          reasoning: result.reasoning
        };
        
        roundGames.push(gameResult);
        
        // Update stats
        const participantStats = stats.get(participantName)!;
        participantStats.gamesPlayed++;
        participantStats.totalMoves += result.moves;
        if (result.won) participantStats.wins++;
        
      } catch (error) {
        console.error(`[Competition] Error for ${participantName}:`, error);
        // Record failed game
        roundGames.push({
          participant: participantName,
          won: false,
          moves: 0,
          duration: 0,
          reasoning: [`Error: ${error.message}`]
        });
      }
    }
    
    // Calculate round standings
    const standings = Array.from(stats.entries())
      .map(([name, s]) => ({
        participant: name,
        wins: s.wins,
        totalMoves: s.totalMoves,
        avgMoves: s.gamesPlayed > 0 ? s.totalMoves / s.gamesPlayed : 0
      }))
      .sort((a, b) => b.wins - a.wins || a.avgMoves - b.avgMoves);
    
    rounds.push({
      round,
      games: roundGames,
      standings
    });
  }
  
  // Calculate final standings
  const finalStandings = Array.from(stats.entries())
    .map(([name, s]) => ({
      participant: name,
      wins: s.wins,
      winRate: s.gamesPlayed > 0 ? s.wins / s.gamesPlayed : 0,
      avgMoves: s.gamesPlayed > 0 ? s.totalMoves / s.gamesPlayed : 0,
      totalGames: s.gamesPlayed
    }))
    .sort((a, b) => b.winRate - a.winRate || a.avgMoves - b.avgMoves)
    .map((standing, index) => ({
      rank: index + 1,
      ...standing
    }));
  
  const endTime = new Date();
  
  return {
    id: competitionId,
    name: config.name,
    startTime,
    endTime,
    rounds,
    finalStandings,
    winner: finalStandings[0]?.participant || 'No winner'
  };
}

/**
 * Run a single game for a participant
 */
async function runSingleGame(
  game: GameInstance,
  participant: { provider: ModelProvider; model: ModelName },
  tools: any,
  gameType: string,
  rules?: CompetitionConfig['rules']
): Promise<{ won: boolean; moves: number; reasoning: string[] }> {
  const model = getModel(participant.provider, participant.model);
  const reasoning: string[] = [];
  let moves = 0;
  const maxSteps = rules?.maxMoves || 50;
  
  // Generate complete game using multi-step
  const result = await generateText({
    model,
    system: getSystemPrompt(gameType),
    messages: [
      {
        role: 'user',
        content: `Play a complete game of ${gameType}. Current state:\n\n${game.getPrompt()}`
      }
    ],
    tools: tools as any,
    maxSteps,
    temperature: 0.7,
    onStepFinish: async (event) => {
      moves++;
      
      // Capture reasoning from each step
      if (event.text) {
        reasoning.push(event.text);
      }
      
      // Check if game is over
      if (game.isGameOver()) {
        return 'stop';
      }
    }
  });
  
  const gameResult = game.getResult();
  
  return {
    won: gameResult.won,
    moves,
    reasoning
  };
}

/**
 * Stream a live competition with real-time updates
 */
export async function streamCompetition(
  config: CompetitionConfig,
  onRoundComplete: (round: RoundResult) => void,
  onGameUpdate: (update: any) => void
): Promise<CompetitionResult> {
  // Similar to runCompetition but with streaming updates
  // This would emit events during the competition
  // Implementation details omitted for brevity
  return runCompetition(config); // Simplified for now
}

/**
 * Create a bracket-style tournament
 */
export function createTournamentBracket(participants: string[]): Array<[string, string]> {
  const shuffled = [...participants].sort(() => Math.random() - 0.5);
  const pairs: Array<[string, string]> = [];
  
  for (let i = 0; i < shuffled.length; i += 2) {
    if (i + 1 < shuffled.length) {
      pairs.push([shuffled[i], shuffled[i + 1]]);
    }
  }
  
  return pairs;
}

/**
 * Run an elimination tournament
 */
export async function runEliminationTournament(
  config: Omit<CompetitionConfig, 'rounds'>
): Promise<CompetitionResult> {
  // Create initial bracket
  const participantNames = config.participants.map(
    p => p.name || `${p.provider}-${p.model}`
  );
  
  let currentRound = participantNames;
  const allRounds: RoundResult[] = [];
  let roundNumber = 1;
  
  // Run elimination rounds until we have a winner
  while (currentRound.length > 1) {
    const pairs = createTournamentBracket(currentRound);
    const winners: string[] = [];
    
    for (const [player1, player2] of pairs) {
      // Run a mini-competition between the pair
      const pairConfig: CompetitionConfig = {
        ...config,
        name: `Round ${roundNumber}: ${player1} vs ${player2}`,
        participants: config.participants.filter(
          p => [player1, player2].includes(p.name || `${p.provider}-${p.model}`)
        ),
        rounds: 3 // Best of 3
      };
      
      const result = await runCompetition(pairConfig);
      const winner = result.winner;
      winners.push(winner);
      
      // Add to tournament rounds
      allRounds.push(...result.rounds.map(r => ({
        ...r,
        round: roundNumber
      })));
    }
    
    currentRound = winners;
    roundNumber++;
  }
  
  // Return tournament result
  return {
    id: `tournament_${Date.now()}`,
    name: config.name,
    startTime: new Date(),
    endTime: new Date(),
    rounds: allRounds,
    finalStandings: [{
      rank: 1,
      participant: currentRound[0],
      wins: 0,
      winRate: 0,
      avgMoves: 0,
      totalGames: 0
    }],
    winner: currentRound[0]
  };
}

function getSystemPrompt(gameType: string): string {
  if (gameType === 'minesweeper') {
    return `You are competing in a Minesweeper tournament. Play strategically to win efficiently.`;
  } else if (gameType === 'risk') {
    return `You are competing in a Risk tournament. Play strategically to conquer territories and defeat opponents.`;
  }
  return 'You are competing in a game tournament. Play to win.';
}