/**
 * Migration utilities for transitioning from legacy API to Vercel AI SDK
 * Provides compatibility layer and feature flags
 */

// Feature flag to control SDK adoption
export const USE_VERCEL_SDK = process.env.USE_VERCEL_SDK === 'true';

// Feature flags for gradual migration
export const FEATURE_FLAGS = {
  // Phase 1: Enable SDK for specific models
  USE_SDK_FOR_GPT4: process.env.USE_SDK_FOR_GPT4 !== 'false',
  USE_SDK_FOR_CLAUDE: process.env.USE_SDK_FOR_CLAUDE !== 'false',
  
  // Phase 2: Enable SDK for specific games
  USE_SDK_FOR_MINESWEEPER: process.env.USE_SDK_FOR_MINESWEEPER !== 'false',
  USE_SDK_FOR_RISK: process.env.USE_SDK_FOR_RISK === 'true', // Opt-in for Risk initially
  
  // Phase 3: Enable advanced features
  USE_SDK_STREAMING: process.env.USE_SDK_STREAMING !== 'false',
  USE_SDK_TELEMETRY: process.env.USE_SDK_TELEMETRY === 'true',
  USE_SDK_MULTI_STEP: process.env.USE_SDK_MULTI_STEP !== 'false'
};

/**
 * Determine if SDK should be used for a specific evaluation
 */
export function shouldUseSDK(config: {
  provider: string;
  model: string;
  gameType: string;
  streaming?: boolean;
}): boolean {
  // Global override
  if (!USE_VERCEL_SDK) return false;
  
  // Check model-specific flags
  if (config.provider === 'openai' && !FEATURE_FLAGS.USE_SDK_FOR_GPT4) return false;
  if (config.provider === 'anthropic' && !FEATURE_FLAGS.USE_SDK_FOR_CLAUDE) return false;
  
  // Check game-specific flags
  if (config.gameType === 'minesweeper' && !FEATURE_FLAGS.USE_SDK_FOR_MINESWEEPER) return false;
  if (config.gameType === 'risk' && !FEATURE_FLAGS.USE_SDK_FOR_RISK) return false;
  
  // Check feature-specific flags
  if (config.streaming && !FEATURE_FLAGS.USE_SDK_STREAMING) return false;
  
  return true;
}

/**
 * Convert legacy API response to SDK format
 */
export function convertLegacyResponse(legacyResponse: any): any {
  return {
    text: legacyResponse.content || legacyResponse.text,
    reasoning: legacyResponse.reasoning,
    toolCalls: legacyResponse.function_calls?.map((call: any) => ({
      toolCallId: call.id,
      toolName: call.function.name,
      args: call.function.arguments
    })),
    usage: {
      promptTokens: legacyResponse.usage?.prompt_tokens,
      completionTokens: legacyResponse.usage?.completion_tokens,
      totalTokens: legacyResponse.usage?.total_tokens
    },
    finishReason: legacyResponse.finish_reason
  };
}

/**
 * Convert SDK tool call to legacy function call format
 */
export function convertSDKToolCall(toolCall: any): any {
  return {
    id: toolCall.toolCallId,
    type: 'function',
    function: {
      name: toolCall.toolName,
      arguments: toolCall.args
    }
  };
}

/**
 * Telemetry wrapper for tracking SDK adoption
 */
export function trackSDKUsage(config: {
  provider: string;
  model: string;
  gameType: string;
  usedSDK: boolean;
  success: boolean;
  duration: number;
}) {
  if (!FEATURE_FLAGS.USE_SDK_TELEMETRY) return;
  
  // In production, this would send to analytics service
  console.log('[SDK_TELEMETRY]', {
    timestamp: new Date().toISOString(),
    ...config
  });
}

/**
 * Compare results between legacy and SDK implementations
 */
export async function compareImplementations(config: any) {
  const results = {
    legacy: null as any,
    sdk: null as any,
    differences: [] as string[]
  };
  
  try {
    // Run legacy implementation
    const legacyStart = Date.now();
    const { evaluateWithLegacyAPI } = await import('../ai_models_http');
    results.legacy = await evaluateWithLegacyAPI(config);
    const legacyDuration = Date.now() - legacyStart;
    
    // Run SDK implementation
    const sdkStart = Date.now();
    const { runEvaluation } = await import('./evaluation');
    results.sdk = await runEvaluation(config);
    const sdkDuration = Date.now() - sdkStart;
    
    // Compare results
    if (results.legacy.won !== results.sdk.summary.wins > 0) {
      results.differences.push('Different win outcomes');
    }
    
    if (Math.abs(results.legacy.moves - results.sdk.summary.avgMoves) > 2) {
      results.differences.push('Significant difference in move count');
    }
    
    // Log comparison
    console.log('[SDK_COMPARISON]', {
      config,
      legacyDuration,
      sdkDuration,
      speedup: legacyDuration / sdkDuration,
      differences: results.differences
    });
    
  } catch (error) {
    console.error('[SDK_COMPARISON] Error:', error);
  }
  
  return results;
}