// AI Model-related types

export type ModelProvider = 'openai' | 'anthropic';

export interface ModelConfig {
  provider: ModelProvider;
  modelName: string;
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  timeout?: number;
}

export interface ModelCapabilities {
  functionCalling: boolean;
  streaming: boolean;
  vision: boolean;
  maxContextLength: number;
  reasoning: boolean;
}

export interface ModelResponse {
  content: string;
  reasoning?: string;
  toolCalls?: ToolCall[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  finishReason?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: any;
  result?: any;
}