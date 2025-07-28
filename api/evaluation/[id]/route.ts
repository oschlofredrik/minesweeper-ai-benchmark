import { runGameEvaluation, GameConfig } from '../../ai/evaluation';
import { createClient } from '@supabase/supabase-js';

// Enable Fluid Compute for long-running evaluations
export const runtime = 'nodejs';
export const maxDuration = 300; // 5 minutes

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  const evaluationId = params.id;
  
  try {
    const body = await request.json();
    const { games, sessionId } = body;
    
    // Update evaluation status
    await updateEvaluationStatus(evaluationId, 'running');
    
    // Create workflow for multiple games
    const results = [];
    let completedGames = 0;
    
    for (const game of games) {
      try {
        // Run individual game evaluation
        const config: GameConfig = {
          gameType: game.type,
          provider: game.provider,
          modelName: game.model,
          difficulty: game.difficulty,
          sessionId
        };
        
        const result = await runGameEvaluation(config, game.initialState);
        
        results.push({
          gameId: game.id,
          success: true,
          result: result.toDataStreamResponse()
        });
        
        completedGames++;
        
        // Update progress
        await updateEvaluationProgress(evaluationId, completedGames, games.length);
        
      } catch (error) {
        results.push({
          gameId: game.id,
          success: false,
          error: error.message
        });
      }
    }
    
    // Update final status
    await updateEvaluationStatus(evaluationId, 'completed', results);
    
    return Response.json({
      evaluationId,
      totalGames: games.length,
      completedGames,
      results
    });
    
  } catch (error) {
    await updateEvaluationStatus(evaluationId, 'failed', { error: error.message });
    
    return Response.json(
      { error: error.message },
      { status: 500 }
    );
  }
}

// Helper functions for status updates
async function updateEvaluationStatus(evaluationId: string, status: string, data?: any) {
  const update = {
    status,
    updated_at: new Date().toISOString(),
    ...(data && { result_data: data })
  };
  
  await supabase
    .from('evaluations')
    .update(update)
    .eq('id', evaluationId);
    
  // Broadcast status update
  await supabase
    .from('realtime_events')
    .insert({
      channel: `evaluation:${evaluationId}`,
      event: 'status_update',
      data: { evaluationId, status, timestamp: new Date().toISOString() }
    });
}

async function updateEvaluationProgress(evaluationId: string, completed: number, total: number) {
  const progress = completed / total;
  
  await supabase
    .from('evaluations')
    .update({
      progress,
      games_completed: completed,
      updated_at: new Date().toISOString()
    })
    .eq('id', evaluationId);
    
  // Broadcast progress update
  await supabase
    .from('realtime_events')
    .insert({
      channel: `evaluation:${evaluationId}`,
      event: 'progress_update',
      data: {
        evaluationId,
        progress,
        completed,
        total,
        timestamp: new Date().toISOString()
      }
    });
}