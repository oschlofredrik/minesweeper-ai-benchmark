import { tool } from 'ai';
import { z } from 'zod';

/**
 * Minesweeper tool definitions for Vercel AI SDK
 * These tools allow AI models to interact with the Minesweeper game
 */

export const minesweeperTools = {
  reveal: tool({
    description: 'Reveal a cell on the Minesweeper board. This will uncover the cell and show either a number (indicating adjacent mines), an empty space, or a mine (game over).',
    parameters: z.object({
      row: z.number()
        .min(0)
        .describe('Row index of the cell to reveal (0-indexed)'),
      col: z.number()
        .min(0)
        .describe('Column index of the cell to reveal (0-indexed)'),
      reasoning: z.string()
        .describe('Strategic reasoning for revealing this cell. Explain why this cell is safe based on the current board state.')
    }),
    execute: async ({ row, col, reasoning }, { game }) => {
      // This will be connected to the actual game instance
      const result = await game.reveal(row, col);
      
      return {
        success: result.valid,
        revealed: result.revealed,
        gameStatus: result.gameStatus,
        message: result.message,
        boardState: result.boardState
      };
    }
  }),
  
  flag: tool({
    description: 'Place a flag on a suspected mine. Use this when you are confident a cell contains a mine based on the numbers around it.',
    parameters: z.object({
      row: z.number()
        .min(0)
        .describe('Row index of the cell to flag (0-indexed)'),
      col: z.number()
        .min(0)
        .describe('Column index of the cell to flag (0-indexed)'),
      reasoning: z.string()
        .describe('Logical reasoning for why this cell must contain a mine based on adjacent numbers and revealed cells.')
    }),
    execute: async ({ row, col, reasoning }, { game }) => {
      const result = await game.flag(row, col);
      
      return {
        success: result.valid,
        flagsRemaining: result.flagsRemaining,
        gameStatus: result.gameStatus,
        message: result.message
      };
    }
  }),
  
  unflag: tool({
    description: 'Remove a flag from a cell. Use this when you realize a flag was placed incorrectly.',
    parameters: z.object({
      row: z.number()
        .min(0)
        .describe('Row index of the flagged cell (0-indexed)'),
      col: z.number()
        .min(0)
        .describe('Column index of the flagged cell (0-indexed)'),
      reasoning: z.string()
        .describe('Explanation for why this flag should be removed.')
    }),
    execute: async ({ row, col, reasoning }, { game }) => {
      const result = await game.unflag(row, col);
      
      return {
        success: result.valid,
        flagsRemaining: result.flagsRemaining,
        gameStatus: result.gameStatus,
        message: result.message
      };
    }
  }),
  
  analyzeBoard: tool({
    description: 'Get a detailed analysis of the current board state without making a move. Useful for planning your strategy.',
    parameters: z.object({
      focusArea: z.enum(['corners', 'edges', 'numbers', 'patterns', 'all'])
        .describe('What aspect of the board to analyze')
    }),
    execute: async ({ focusArea }, { game }) => {
      const analysis = await game.analyzeBoard(focusArea);
      
      return {
        revealedCells: analysis.revealedCells,
        flaggedCells: analysis.flaggedCells,
        safeCells: analysis.safeCells,
        riskyAreas: analysis.riskyAreas,
        suggestedMoves: analysis.suggestedMoves,
        boardCoverage: analysis.boardCoverage
      };
    }
  })
};

// Export tool names for type safety
export type MinesweeperToolName = keyof typeof minesweeperTools;

// Export a function to get tools with game context
export function getMinesweeperTools(gameInstance: any) {
  return Object.entries(minesweeperTools).reduce((acc, [name, toolDef]) => {
    acc[name] = {
      ...toolDef,
      execute: (params: any) => toolDef.execute(params, { game: gameInstance })
    };
    return acc;
  }, {} as typeof minesweeperTools);
}