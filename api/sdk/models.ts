import { openai } from '@ai-sdk/openai';
import { anthropic } from '@ai-sdk/anthropic';
import { LanguageModel } from 'ai';

/**
 * Model provider configuration for Vercel AI SDK
 * Provides a unified interface for accessing different AI providers
 */

export type ModelProvider = 'openai' | 'anthropic';
export type ModelName = string;

// Model configurations with their specific settings
export const MODEL_CONFIGS = {
  openai: {
    'gpt-4-turbo-preview': { maxTokens: 128000, supportsTools: true, supportsStreaming: true },
    'gpt-4': { maxTokens: 8192, supportsTools: true, supportsStreaming: true },
    'gpt-4o': { maxTokens: 128000, supportsTools: true, supportsStreaming: true },
    'gpt-4o-mini': { maxTokens: 128000, supportsTools: true, supportsStreaming: true },
    'gpt-3.5-turbo': { maxTokens: 16385, supportsTools: true, supportsStreaming: true },
    'o1-preview': { maxTokens: 128000, supportsTools: false, supportsStreaming: false },
    'o1-mini': { maxTokens: 128000, supportsTools: false, supportsStreaming: false },
    'o3-mini': { maxTokens: 200000, supportsTools: true, supportsStreaming: true }
  },
  anthropic: {
    'claude-3-5-sonnet-20241022': { maxTokens: 8192, supportsTools: true, supportsStreaming: true },
    'claude-3-opus-20240229': { maxTokens: 4096, supportsTools: true, supportsStreaming: true },
    'claude-3-sonnet-20240229': { maxTokens: 4096, supportsTools: true, supportsStreaming: true },
    'claude-3-haiku-20240307': { maxTokens: 4096, supportsTools: true, supportsStreaming: true },
    'claude-4-sonnet-20250514': { maxTokens: 8192, supportsTools: true, supportsStreaming: true }
  }
};

/**
 * Get a configured model instance based on provider and model name
 */
export function getModel(provider: ModelProvider, modelName: ModelName): LanguageModel {
  switch (provider) {
    case 'openai':
      return openai(modelName);
    
    case 'anthropic':
      return anthropic(modelName);
    
    default:
      throw new Error(`Unknown provider: ${provider}`);
  }
}

/**
 * Get model configuration details
 */
export function getModelConfig(provider: ModelProvider, modelName: ModelName) {
  const providerConfigs = MODEL_CONFIGS[provider];
  if (!providerConfigs) {
    throw new Error(`Unknown provider: ${provider}`);
  }
  
  const config = providerConfigs[modelName as keyof typeof providerConfigs];
  if (!config) {
    throw new Error(`Unknown model: ${modelName} for provider ${provider}`);
  }
  
  return config;
}

/**
 * Check if a model supports function/tool calling
 */
export function modelSupportsTools(provider: ModelProvider, modelName: ModelName): boolean {
  try {
    const config = getModelConfig(provider, modelName);
    return config.supportsTools;
  } catch {
    return true; // Default to true if unknown
  }
}

/**
 * Check if a model supports streaming
 */
export function modelSupportsStreaming(provider: ModelProvider, modelName: ModelName): boolean {
  try {
    const config = getModelConfig(provider, modelName);
    return config.supportsStreaming;
  } catch {
    return true; // Default to true if unknown
  }
}

/**
 * Get provider-specific options for special models
 */
export function getProviderOptions(provider: ModelProvider, modelName: ModelName): any {
  // Special handling for OpenAI o3 models
  if (provider === 'openai' && modelName.includes('o3')) {
    return {
      openai: {
        reasoningEffort: 'medium' // Can be 'low', 'medium', or 'high'
      }
    };
  }
  
  // Special handling for Anthropic Claude 4
  if (provider === 'anthropic' && modelName.includes('claude-4')) {
    return {
      anthropic: {
        thinking: { 
          type: 'enabled', 
          budgetTokens: 15000 
        }
      }
    };
  }
  
  return {};
}

/**
 * Get headers for special model features
 */
export function getModelHeaders(provider: ModelProvider, modelName: ModelName): Record<string, string> {
  // Enable interleaved thinking for Claude 4
  if (provider === 'anthropic' && modelName.includes('claude-4')) {
    return {
      'anthropic-beta': 'interleaved-thinking-2025-05-14'
    };
  }
  
  return {};
}