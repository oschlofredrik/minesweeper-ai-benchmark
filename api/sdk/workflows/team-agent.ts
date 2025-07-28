/**
 * Team-based agent workflows for collaborative gameplay
 * Multiple AI models work together to solve games
 */

import { generateText, streamText } from 'ai';
import { z } from 'zod';
import { tool } from 'ai';
import { 
  getModel, 
  ModelProvider, 
  ModelName 
} from '../models';
import { GameInstance } from '../evaluation';

export interface TeamMember {
  role: 'strategist' | 'analyst' | 'executor';
  provider: ModelProvider;
  model: ModelName;
  name?: string;
}

export interface TeamConfig {
  name: string;
  members: TeamMember[];
  communicationStyle: 'sequential' | 'consensus' | 'hierarchical';
}

export interface TeamDecision {
  proposedMove: any;
  reasoning: string;
  confidence: number;
  member: string;
}

/**
 * Tools for team communication
 */
const teamTools = {
  proposeMove: tool({
    description: 'Propose a move for the team to consider',
    parameters: z.object({
      move: z.any().describe('The proposed move'),
      reasoning: z.string().describe('Reasoning for this move'),
      confidence: z.number().min(0).max(1).describe('Confidence level (0-1)')
    }),
    execute: async ({ move, reasoning, confidence }) => {
      return { proposed: true, move, reasoning, confidence };
    }
  }),
  
  analyzeProposal: tool({
    description: 'Analyze a proposed move from a teammate',
    parameters: z.object({
      proposal: z.any().describe('The proposal to analyze'),
      analysis: z.string().describe('Analysis of the proposal'),
      support: z.boolean().describe('Whether you support this move'),
      alternativeMove: z.any().optional().describe('Alternative move if you disagree')
    }),
    execute: async ({ proposal, analysis, support, alternativeMove }) => {
      return { analyzed: true, analysis, support, alternativeMove };
    }
  }),
  
  requestAnalysis: tool({
    description: 'Request analysis of the current game state',
    parameters: z.object({
      focusArea: z.string().describe('Specific area to analyze'),
      urgency: z.enum(['low', 'medium', 'high']).describe('How urgent is this analysis')
    }),
    execute: async ({ focusArea, urgency }) => {
      return { requested: true, focusArea, urgency };
    }
  })
};

/**
 * Run a game with a team of AI agents collaborating
 */
export async function runTeamGame(
  game: GameInstance,
  team: TeamConfig,
  gameTools: any
): Promise<{
  won: boolean;
  moves: number;
  teamDecisions: TeamDecision[];
  transcript: string[];
}> {
  const teamDecisions: TeamDecision[] = [];
  const transcript: string[] = [];
  let moves = 0;
  
  while (!game.isGameOver() && moves < 50) {
    moves++;
    
    // Get current game state
    const gameState = game.getPrompt();
    
    // Collect proposals based on communication style
    let finalDecision: TeamDecision | null = null;
    
    switch (team.communicationStyle) {
      case 'sequential':
        finalDecision = await sequentialDecisionMaking(
          team,
          gameState,
          gameTools,
          transcript
        );
        break;
        
      case 'consensus':
        finalDecision = await consensusDecisionMaking(
          team,
          gameState,
          gameTools,
          transcript
        );
        break;
        
      case 'hierarchical':
        finalDecision = await hierarchicalDecisionMaking(
          team,
          gameState,
          gameTools,
          transcript
        );
        break;
    }
    
    if (!finalDecision) {
      transcript.push('Team failed to reach a decision');
      break;
    }
    
    teamDecisions.push(finalDecision);
    
    // Execute the decided move
    const moveResult = await executeTeamMove(
      game,
      finalDecision.proposedMove,
      gameTools
    );
    
    transcript.push(
      `Move ${moves}: ${finalDecision.member} decided ${JSON.stringify(finalDecision.proposedMove)} - ${moveResult.message}`
    );
  }
  
  const result = game.getResult();
  
  return {
    won: result.won,
    moves,
    teamDecisions,
    transcript
  };
}

/**
 * Sequential decision making - each member builds on previous analysis
 */
async function sequentialDecisionMaking(
  team: TeamConfig,
  gameState: string,
  gameTools: any,
  transcript: string[]
): Promise<TeamDecision | null> {
  let context = `Game state:\n${gameState}\n\n`;
  let bestProposal: TeamDecision | null = null;
  
  for (const member of team.members) {
    const memberName = member.name || `${member.role}-${member.model}`;
    const model = getModel(member.provider, member.model);
    
    // Build on previous context
    const prompt = `${context}You are the ${member.role} in a team. ${
      bestProposal 
        ? `The current best proposal is: ${bestProposal.reasoning}`
        : 'You are the first to analyze.'
    } What is your recommendation?`;
    
    const result = await generateText({
      model,
      system: getRolePrompt(member.role),
      messages: [{ role: 'user', content: prompt }],
      tools: { ...teamTools, ...gameTools },
      maxSteps: 3
    });
    
    // Extract proposal from tool calls
    const proposalCall = result.toolCalls?.find(
      tc => tc.toolName === 'proposeMove'
    );
    
    if (proposalCall) {
      const proposal: TeamDecision = {
        proposedMove: proposalCall.args.move,
        reasoning: proposalCall.args.reasoning,
        confidence: proposalCall.args.confidence,
        member: memberName
      };
      
      transcript.push(`${memberName}: ${proposal.reasoning}`);
      
      // Update best proposal if this one is more confident
      if (!bestProposal || proposal.confidence > bestProposal.confidence) {
        bestProposal = proposal;
      }
      
      // Add to context for next member
      context += `\n${memberName} (${member.role}): ${proposal.reasoning}\n`;
    }
  }
  
  return bestProposal;
}

/**
 * Consensus decision making - all members vote on proposals
 */
async function consensusDecisionMaking(
  team: TeamConfig,
  gameState: string,
  gameTools: any,
  transcript: string[]
): Promise<TeamDecision | null> {
  const proposals: TeamDecision[] = [];
  
  // Phase 1: Collect proposals from all members
  for (const member of team.members) {
    const memberName = member.name || `${member.role}-${member.model}`;
    const model = getModel(member.provider, member.model);
    
    const result = await generateText({
      model,
      system: getRolePrompt(member.role),
      messages: [{
        role: 'user',
        content: `Game state:\n${gameState}\n\nPropose your best move.`
      }],
      tools: { ...teamTools, ...gameTools },
      maxSteps: 2
    });
    
    const proposalCall = result.toolCalls?.find(
      tc => tc.toolName === 'proposeMove'
    );
    
    if (proposalCall) {
      proposals.push({
        proposedMove: proposalCall.args.move,
        reasoning: proposalCall.args.reasoning,
        confidence: proposalCall.args.confidence,
        member: memberName
      });
    }
  }
  
  // Phase 2: Vote on proposals
  const votes = new Map<number, number>();
  
  for (const member of team.members) {
    const memberName = member.name || `${member.role}-${member.model}`;
    const model = getModel(member.provider, member.model);
    
    const proposalSummary = proposals.map((p, i) => 
      `${i + 1}. ${p.member}: ${p.reasoning}`
    ).join('\n');
    
    const result = await generateText({
      model,
      messages: [{
        role: 'user',
        content: `Review these proposals and pick the best one:\n${proposalSummary}\n\nWhich number do you vote for?`
      }],
      temperature: 0.3
    });
    
    // Extract vote (simplified - in production would use tools)
    const voteMatch = result.text.match(/\b([1-9])\b/);
    if (voteMatch) {
      const vote = parseInt(voteMatch[1]) - 1;
      votes.set(vote, (votes.get(vote) || 0) + 1);
      transcript.push(`${memberName} votes for proposal ${vote + 1}`);
    }
  }
  
  // Find proposal with most votes
  let bestProposalIndex = 0;
  let maxVotes = 0;
  
  votes.forEach((voteCount, proposalIndex) => {
    if (voteCount > maxVotes) {
      maxVotes = voteCount;
      bestProposalIndex = proposalIndex;
    }
  });
  
  return proposals[bestProposalIndex] || null;
}

/**
 * Hierarchical decision making - strategist decides, others advise
 */
async function hierarchicalDecisionMaking(
  team: TeamConfig,
  gameState: string,
  gameTools: any,
  transcript: string[]
): Promise<TeamDecision | null> {
  const strategist = team.members.find(m => m.role === 'strategist');
  const advisors = team.members.filter(m => m.role !== 'strategist');
  
  if (!strategist) {
    throw new Error('Hierarchical teams require a strategist');
  }
  
  // Collect advice from advisors
  let advice = '';
  
  for (const advisor of advisors) {
    const memberName = advisor.name || `${advisor.role}-${advisor.model}`;
    const model = getModel(advisor.provider, advisor.model);
    
    const result = await generateText({
      model,
      system: getRolePrompt(advisor.role),
      messages: [{
        role: 'user',
        content: `Game state:\n${gameState}\n\nProvide your analysis and recommendations.`
      }],
      maxTokens: 200
    });
    
    advice += `\n${memberName}: ${result.text}\n`;
    transcript.push(`${memberName} advises: ${result.text}`);
  }
  
  // Strategist makes final decision
  const strategistName = strategist.name || `strategist-${strategist.model}`;
  const strategistModel = getModel(strategist.provider, strategist.model);
  
  const result = await generateText({
    model: strategistModel,
    system: getRolePrompt('strategist'),
    messages: [{
      role: 'user',
      content: `Game state:\n${gameState}\n\nAdvisor input:${advice}\n\nMake the final decision.`
    }],
    tools: { ...teamTools, ...gameTools },
    maxSteps: 2
  });
  
  const proposalCall = result.toolCalls?.find(
    tc => tc.toolName === 'proposeMove'
  );
  
  if (proposalCall) {
    return {
      proposedMove: proposalCall.args.move,
      reasoning: proposalCall.args.reasoning,
      confidence: proposalCall.args.confidence,
      member: strategistName
    };
  }
  
  return null;
}

/**
 * Execute a team's decided move
 */
async function executeTeamMove(
  game: GameInstance,
  move: any,
  gameTools: any
): Promise<{ success: boolean; message: string }> {
  // Find the appropriate tool and execute
  const toolName = move.action || move.type;
  const tool = gameTools[toolName];
  
  if (!tool) {
    return { success: false, message: 'Unknown move type' };
  }
  
  try {
    const result = await tool.execute(move);
    return { success: true, message: result.message || 'Move executed' };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

/**
 * Get role-specific system prompts
 */
function getRolePrompt(role: TeamMember['role']): string {
  switch (role) {
    case 'strategist':
      return `You are the team strategist. Focus on long-term planning and overall game strategy. Make decisive choices based on team input.`;
      
    case 'analyst':
      return `You are the team analyst. Focus on detailed analysis of the current game state, probabilities, and risk assessment. Provide data-driven insights.`;
      
    case 'executor':
      return `You are the team executor. Focus on tactical execution and immediate threats/opportunities. Ensure moves are valid and well-executed.`;
      
    default:
      return `You are a team member. Collaborate effectively to win the game.`;
  }
}