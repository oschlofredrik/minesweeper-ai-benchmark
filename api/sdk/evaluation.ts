import { generateText, streamText } from 'ai';
import { 
  getModel, 
  modelSupportsStreaming, 
  modelSupportsTools,
  getProviderOptions,
  getModelHeaders,
  ModelProvider,
  ModelName
} from './models';
import { getMinesweeperTools } from './tools/minesweeper';
import { getRiskTools } from './tools/risk';
import { 
  createGameStreamData,
  EvaluationProgress,
  GameMoveEvent
} from './streaming';

/**
 * Main evaluation runner using Vercel AI SDK
 * Handles game evaluation with streaming and multi-step capabilities
 */

export interface EvaluationConfig {
  gameType: 'minesweeper' | 'risk';
  provider: ModelProvider;
  model: ModelName;
  difficulty?: string;
  scenario?: string;
  numGames?: number;
  streaming?: boolean;
  temperature?: number;
  maxSteps?: number;
}

export interface GameInstance {
  id: string;
  type: string;
  getState: () => any;
  getPrompt: () => string;
  isGameOver: () => boolean;
  getResult: () => { won: boolean; moves: number; coverage?: number };
  reveal?: (row: number, col: number) => any;
  flag?: (row: number, col: number) => any;
  unflag?: (row: number, col: number) => any;
  analyzeBoard?: (focusArea: string) => any;
  placeReinforcements?: (territory: string, troops: number) => any;
  attack?: (from: string, to: string, dice: number) => any;
  fortify?: (from: string, to: string, troops: number) => any;
  endPhase?: (skipFortify?: boolean) => any;
  analyzeMap?: (focusArea: string, player?: string) => any;
  useCards?: (cards: string[]) => any;
}

/**
 * Create a game instance based on type and configuration
 */
async function createGameInstance(
  gameType: string, 
  difficulty?: string, 
  scenario?: string
): Promise<GameInstance> {
  // This will be connected to the actual game implementations
  // For now, returning a mock structure
  const gameId = `game_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Import the actual game implementation
  if (gameType === 'minesweeper') {
    const { SimpleMinesweeper } = await import('./games/minesweeper');
    const difficultyConfigs = {
      easy: { rows: 9, cols: 9, mines: 10 },
      medium: { rows: 16, cols: 16, mines: 40 },
      hard: { rows: 16, cols: 30, mines: 99 }
    };
    const config = difficultyConfigs[difficulty as keyof typeof difficultyConfigs] || difficultyConfigs.medium;
    const game = new SimpleMinesweeper(config.rows, config.cols, config.mines);
    
    return {
      id: gameId,
      type: 'minesweeper',
      getState: () => game.to_json_state(),
      getPrompt: () => game.get_board_state(),
      isGameOver: () => game.game_over,
      getResult: () => ({
        won: game.won,
        moves: game.moves,
        coverage: game.get_coverage()
      }),
      reveal: (row, col) => game.reveal(row, col),
      flag: (row, col) => game.flag(row, col),
      unflag: (row, col) => game.unflag(row, col),
      analyzeBoard: (focusArea) => game.analyze_board(focusArea)
    };
  } else if (gameType === 'risk') {
    // Risk implementation would go here
    // For now, throw an error as Risk is not yet implemented in TypeScript
    throw new Error('Risk game not yet implemented in TypeScript SDK');
  }
  
  throw new Error(`Unknown game type: ${gameType}`);
}

/**
 * Get the appropriate tools for a game type
 */
function getGameTools(gameType: string, gameInstance: GameInstance) {
  switch (gameType) {
    case 'minesweeper':
      return getMinesweeperTools(gameInstance);
    case 'risk':
      return getRiskTools(gameInstance);
    default:
      throw new Error(`Unknown game type: ${gameType}`);
  }
}

/**
 * Format the system prompt for the game
 */
function getSystemPrompt(gameType: string): string {
  if (gameType === 'minesweeper') {
    return `You are an expert Minesweeper player. Your goal is to clear the board without hitting any mines.
    
    Strategy tips:
    - Start with corners or edges where you have fewer adjacent cells
    - Use number clues to deduce mine locations
    - Flag cells you're certain contain mines
    - Look for patterns and guaranteed safe cells
    - Be systematic and logical in your approach
    
    Always provide clear reasoning for each move.`;
  } else if (gameType === 'risk') {
    return `You are an expert Risk strategist. Your goal is to conquer territories and defeat your opponents.
    
    Strategy tips:
    - Control continents for bonus reinforcements
    - Maintain strong borders
    - Don't spread your forces too thin
    - Attack when you have advantage
    - Fortify strategic positions
    
    Always provide clear strategic reasoning for each action.`;
  }
  
  return 'You are an expert game player. Play strategically and explain your reasoning.';
}

/**
 * Run a single game evaluation with streaming
 */
export async function streamGameEvaluation(config: EvaluationConfig) {
  const { gameType, provider, model, difficulty, scenario } = config;
  
  // Check if streaming is supported
  const supportsStreaming = modelSupportsStreaming(provider, model);
  const supportsTools = modelSupportsTools(provider, model);
  
  if (!supportsStreaming) {
    throw new Error(`Model ${model} does not support streaming`);
  }
  
  if (!supportsTools && gameType !== 'minesweeper') {
    throw new Error(`Model ${model} does not support tools required for ${gameType}`);
  }
  
  // Create game instance
  const game = await createGameInstance(gameType, difficulty, scenario);
  const tools = getGameTools(gameType, game);
  
  // Create stream data handler
  const { streamData, sendMove, sendStatus, sendComplete, sendError } = createGameStreamData();
  
  try {
    // Get model instance
    const modelInstance = getModel(provider, model);
    
    // Send initial status
    sendStatus('Starting game evaluation', { gameNumber: 1, totalGames: 1 });
    
    // Stream the game with multi-step tool calling
    const result = await streamText({
      model: modelInstance,
      system: getSystemPrompt(gameType),
      messages: [
        {
          role: 'user',
          content: `Here is the current game state:\n\n${game.getPrompt()}\n\nPlay the game step by step, making one move at a time.`
        }
      ],
      tools: tools as any,
      maxSteps: config.maxSteps || 50,
      temperature: config.temperature || 0.7,
      providerOptions: getProviderOptions(provider, model),
      headers: getModelHeaders(provider, model),
      onStepFinish: async (event) => {
        // Handle each tool call as a move
        if (event.toolCalls && event.toolCalls.length > 0) {
          const toolCall = event.toolCalls[0];
          const moveEvent: GameMoveEvent = {
            type: 'move',
            moveNumber: event.stepNumber || 1,
            action: toolCall.toolName,
            reasoning: toolCall.args.reasoning,
            valid: true, // Will be updated based on result
            boardState: game.getPrompt()
          };
          
          // Add position/territory info
          if (gameType === 'minesweeper' && toolCall.args.row !== undefined) {
            moveEvent.position = { 
              row: toolCall.args.row, 
              col: toolCall.args.col 
            };
          }
          
          sendMove(moveEvent);
        }
        
        // Check if game is over
        if (game.isGameOver()) {
          const result = game.getResult();
          sendComplete({
            gameId: game.id,
            won: result.won,
            moves: result.moves,
            duration: 0, // Will be calculated
            coverage: result.coverage
          });
          return; // Stop evaluation
        }
      }
    });
    
    return result.toDataStreamResponse();
    
  } catch (error: any) {
    sendError(error.message, error.code);
    throw error;
  } finally {
    streamData.close();
  }
}

/**
 * Run a complete evaluation with multiple games
 */
export async function runEvaluation(config: EvaluationConfig) {
  const numGames = config.numGames || 1;
  const progress = new EvaluationProgress(numGames);
  const results = [];
  
  for (let i = 0; i < numGames; i++) {
    try {
      // For multi-game evaluations, we might want to use generateText instead of streaming
      // to avoid overwhelming the client with too many events
      const game = await createGameInstance(config.gameType, config.difficulty, config.scenario);
      const tools = getGameTools(config.gameType, game);
      const modelInstance = getModel(config.provider, config.model);
      
      const result = await generateText({
        model: modelInstance,
        system: getSystemPrompt(config.gameType),
        messages: [
          {
            role: 'user',
            content: `Play a complete game of ${config.gameType}. Current state:\n\n${game.getPrompt()}`
          }
        ],
        tools: tools as any,
        maxSteps: config.maxSteps || 50,
        temperature: config.temperature || 0.7,
        providerOptions: getProviderOptions(config.provider, config.model),
        headers: getModelHeaders(config.provider, config.model)
      });
      
      const gameResult = game.getResult();
      progress.completeGame(gameResult.won, gameResult.moves);
      
      results.push({
        gameId: game.id,
        ...gameResult,
        reasoning: result.text,
        toolCalls: result.toolCalls,
        usage: result.usage
      });
      
    } catch (error) {
      console.error(`Game ${i + 1} failed:`, error);
      results.push({
        gameId: `error_${i}`,
        error: error.message,
        won: false,
        moves: 0
      });
    }
  }
  
  return {
    summary: progress.getStats(),
    games: results
  };
}