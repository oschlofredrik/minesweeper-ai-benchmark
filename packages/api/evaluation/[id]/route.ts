import { NextRequest, NextResponse } from 'next/server';
import { runGameEvaluation } from '../../src/evaluation-handler';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

export const runtime = 'edge';
export const maxDuration = 300; // 5 minutes for Vercel Pro

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const evaluationId = params.id;
  
  try {
    const body = await request.json();
    const { games, config } = body;
    
    // Update evaluation status
    await supabase
      .from('games')
      .update({ status: 'running' })
      .eq('job_id', evaluationId);
    
    // Process games
    const results = [];
    for (const game of games) {
      try {
        // Run game evaluation with streaming updates
        const result = await runGameEvaluation({
          gameType: config.game_type,
          provider: config.provider,
          modelName: config.model_name,
          difficulty: config.difficulty,
          gameId: game.id,
          onUpdate: async (update) => {
            // Stream updates back to client
            if (update.type === 'moveComplete') {
              await supabase
                .from('game_moves')
                .insert({
                  game_id: game.id,
                  move_number: update.moveNumber,
                  action: update.move.action,
                  row: update.move.row,
                  col: update.move.col,
                  reasoning: update.move.reasoning,
                  result: update.result
                });
            }
          }
        });
        
        // Update game with results
        await supabase
          .from('games')
          .update({
            status: result.won ? 'won' : 'lost',
            won: result.won,
            total_moves: result.totalMoves,
            duration: result.duration,
            final_board_state: result.finalState,
            completed_at: new Date().toISOString()
          })
          .eq('id', game.id);
        
        results.push(result);
        
      } catch (error) {
        console.error(`Error processing game ${game.id}:`, error);
        
        await supabase
          .from('games')
          .update({
            status: 'error',
            error: error.message,
            completed_at: new Date().toISOString()
          })
          .eq('id', game.id);
      }
    }
    
    return NextResponse.json({
      evaluationId,
      results,
      status: 'completed'
    });
    
  } catch (error) {
    console.error('Evaluation error:', error);
    
    // Update evaluation status to error
    await supabase
      .from('games')
      .update({ status: 'error', error: error.message })
      .eq('job_id', evaluationId);
    
    return NextResponse.json(
      { error: 'Evaluation failed', details: error.message },
      { status: 500 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const evaluationId = params.id;
  
  try {
    // Get evaluation status
    const { data: games, error } = await supabase
      .from('games')
      .select('*')
      .eq('job_id', evaluationId)
      .order('created_at', { ascending: true });
    
    if (error) throw error;
    
    const total = games.length;
    const completed = games.filter(g => 
      ['won', 'lost', 'error'].includes(g.status)
    ).length;
    const inProgress = games.filter(g => 
      ['running', 'in_progress'].includes(g.status)
    ).length;
    
    return NextResponse.json({
      evaluationId,
      status: completed === total ? 'completed' : 
              inProgress > 0 ? 'running' : 'queued',
      progress: total > 0 ? completed / total : 0,
      games_total: total,
      games_completed: completed,
      games: games.slice(0, 10) // Return first 10 for preview
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get evaluation status' },
      { status: 500 }
    );
  }
}