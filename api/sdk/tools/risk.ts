import { tool } from 'ai';
import { z } from 'zod';

/**
 * Risk tool definitions for Vercel AI SDK
 * These tools allow AI models to interact with the Risk game
 */

export const riskTools = {
  placeReinforcements: tool({
    description: 'Place reinforcement troops on your territories during the reinforcement phase.',
    parameters: z.object({
      territory: z.string()
        .describe('Name of the territory to reinforce (e.g., "Brazil", "Western Europe")'),
      troops: z.number()
        .min(1)
        .describe('Number of troops to place on this territory'),
      reasoning: z.string()
        .describe('Strategic reasoning for reinforcing this territory')
    }),
    execute: async ({ territory, troops, reasoning }, { game }) => {
      const result = await game.placeReinforcements(territory, troops);
      
      return {
        success: result.valid,
        troopsPlaced: result.troopsPlaced,
        remainingReinforcements: result.remainingReinforcements,
        territoryStrength: result.territoryStrength,
        message: result.message
      };
    }
  }),
  
  attack: tool({
    description: 'Attack an enemy territory from one of your adjacent territories.',
    parameters: z.object({
      fromTerritory: z.string()
        .describe('Your territory to attack from'),
      toTerritory: z.string()
        .describe('Enemy territory to attack'),
      attackingDice: z.number()
        .min(1)
        .max(3)
        .describe('Number of dice to use for attack (1-3)'),
      reasoning: z.string()
        .describe('Strategic reasoning for this attack')
    }),
    execute: async ({ fromTerritory, toTerritory, attackingDice, reasoning }, { game }) => {
      const result = await game.attack(fromTerritory, toTerritory, attackingDice);
      
      return {
        success: result.valid,
        attackerLosses: result.attackerLosses,
        defenderLosses: result.defenderLosses,
        conquered: result.conquered,
        diceResults: result.diceResults,
        message: result.message
      };
    }
  }),
  
  fortify: tool({
    description: 'Move troops from one of your territories to another connected territory at the end of your turn.',
    parameters: z.object({
      fromTerritory: z.string()
        .describe('Territory to move troops from'),
      toTerritory: z.string()
        .describe('Territory to move troops to'),
      troops: z.number()
        .min(1)
        .describe('Number of troops to move'),
      reasoning: z.string()
        .describe('Strategic reasoning for this fortification')
    }),
    execute: async ({ fromTerritory, toTerritory, troops, reasoning }, { game }) => {
      const result = await game.fortify(fromTerritory, toTerritory, troops);
      
      return {
        success: result.valid,
        troopsMoved: result.troopsMoved,
        fromStrength: result.fromStrength,
        toStrength: result.toStrength,
        message: result.message
      };
    }
  }),
  
  endPhase: tool({
    description: 'End the current phase and move to the next one (reinforcement -> attack -> fortify).',
    parameters: z.object({
      skipFortify: z.boolean()
        .optional()
        .describe('Whether to skip the fortify phase (only valid during fortify phase)'),
      reasoning: z.string()
        .describe('Reasoning for ending this phase')
    }),
    execute: async ({ skipFortify, reasoning }, { game }) => {
      const result = await game.endPhase(skipFortify);
      
      return {
        success: result.valid,
        previousPhase: result.previousPhase,
        newPhase: result.newPhase,
        message: result.message
      };
    }
  }),
  
  analyzeMap: tool({
    description: 'Get a strategic analysis of the current game state.',
    parameters: z.object({
      focusArea: z.enum(['continents', 'borders', 'strength', 'opportunities', 'threats', 'all'])
        .describe('What aspect of the map to analyze'),
      player: z.string()
        .optional()
        .describe('Specific player to analyze (default: current player)')
    }),
    execute: async ({ focusArea, player }, { game }) => {
      const analysis = await game.analyzeMap(focusArea, player);
      
      return {
        continentControl: analysis.continentControl,
        borderTerritories: analysis.borderTerritories,
        strongholds: analysis.strongholds,
        weakPoints: analysis.weakPoints,
        attackOpportunities: analysis.attackOpportunities,
        defensePriorities: analysis.defensePriorities,
        troopBalance: analysis.troopBalance
      };
    }
  }),
  
  useCards: tool({
    description: 'Trade in territory cards for bonus reinforcements.',
    parameters: z.object({
      cards: z.array(z.string())
        .length(3)
        .describe('Three territory card IDs to trade in'),
      reasoning: z.string()
        .describe('Reasoning for trading these cards now')
    }),
    execute: async ({ cards, reasoning }, { game }) => {
      const result = await game.useCards(cards);
      
      return {
        success: result.valid,
        bonusTroops: result.bonusTroops,
        remainingCards: result.remainingCards,
        message: result.message
      };
    }
  })
};

// Export tool names for type safety
export type RiskToolName = keyof typeof riskTools;

// Export a function to get tools with game context
export function getRiskTools(gameInstance: any) {
  return Object.entries(riskTools).reduce((acc, [name, toolDef]) => {
    acc[name] = {
      ...toolDef,
      execute: (params: any) => toolDef.execute(params, { game: gameInstance })
    };
    return acc;
  }, {} as typeof riskTools);
}