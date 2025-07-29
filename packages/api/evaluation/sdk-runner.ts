import type { VercelRequest, VercelResponse } from '@vercel/node';
import { runGameEvaluation } from '../src/evaluation-handler';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { evaluationId, games, config } = req.body;
    
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    
    // Process games sequentially (for now)
    const results = [];
    
    for (const game of games) {
      try {
        const result = await runGameEvaluation({
          gameType: config.game_type,
          provider: config.provider,
          modelName: config.model_name,
          difficulty: config.difficulty,
          gameId: game.id,
        });
        
        results.push(result);
      } catch (error) {
        console.error(`Error processing game ${game.id}:`, error);
        results.push({
          gameId: game.id,
          error: error.message,
          status: 'error'
        });
      }
    }
    
    return res.status(200).json({
      evaluationId,
      results,
      status: 'completed'
    });
    
  } catch (error) {
    console.error('SDK evaluation error:', error);
    return res.status(500).json({
      error: 'Evaluation failed',
      details: error.message
    });
  }
}