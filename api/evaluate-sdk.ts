import { VercelRequest, VercelResponse } from '@vercel/node';
import { streamGameEvaluation, runEvaluation } from './sdk/evaluation';

/**
 * API endpoint for game evaluation using Vercel AI SDK
 * Supports both streaming (single game) and batch evaluation (multiple games)
 */

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const {
      gameType = 'minesweeper',
      provider = 'openai',
      model = 'gpt-4',
      difficulty = 'medium',
      scenario,
      numGames = 1,
      streaming = true,
      temperature = 0.7,
      maxSteps = 50
    } = req.body;
    
    // Validate inputs
    if (!['minesweeper', 'risk'].includes(gameType)) {
      return res.status(400).json({ error: 'Invalid game type' });
    }
    
    if (!['openai', 'anthropic'].includes(provider)) {
      return res.status(400).json({ error: 'Invalid provider' });
    }
    
    // Check API keys
    const apiKeyEnv = provider === 'openai' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY';
    if (!process.env[apiKeyEnv]) {
      return res.status(400).json({ error: `${apiKeyEnv} not configured` });
    }
    
    const config = {
      gameType,
      provider,
      model,
      difficulty,
      scenario,
      numGames,
      streaming,
      temperature,
      maxSteps
    };
    
    // For single game with streaming
    if (numGames === 1 && streaming) {
      const streamResponse = await streamGameEvaluation(config);
      
      // Set headers for streaming
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('Access-Control-Allow-Origin', '*');
      
      // Return the stream response
      return streamResponse;
    }
    
    // For multiple games or non-streaming
    const results = await runEvaluation(config);
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    return res.status(200).json({
      success: true,
      jobId: `eval_${Date.now()}`,
      ...results
    });
    
  } catch (error: any) {
    console.error('Evaluation error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(500).json({
      error: error.message || 'Internal server error',
      code: error.code
    });
  }
}