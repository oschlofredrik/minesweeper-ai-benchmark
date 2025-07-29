"""AI Models HTTP integration for calling OpenAI and Anthropic."""
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

def call_ai_model(provider: str, model: str, messages: List[Dict], 
                  functions: Optional[List[Dict]] = None, temperature: float = 0.7) -> Dict:
    """Call AI model via HTTP API."""
    print(f"[AI] Calling {provider} model {model}")
    print(f"[AI] OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
    print(f"[AI] ANTHROPIC_API_KEY exists: {'ANTHROPIC_API_KEY' in os.environ}")
    print(f"[AI] Message count: {len(messages)}")
    
    if provider == 'openai':
        return call_openai(model, messages, functions, temperature)
    elif provider == 'anthropic':
        return call_anthropic(model, messages, functions, temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")

def call_openai(model: str, messages: List[Dict], functions: Optional[List[Dict]] = None, 
                temperature: float = 0.7) -> Dict:
    """Call OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")
    
    url = "https://api.openai.com/v1/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    if functions:
        payload["functions"] = functions
        payload["function_call"] = "auto"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"[AI] OpenAI request to {url}")
    print(f"[AI] Using model: {model}")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[AI] OpenAI response received")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[AI] OpenAI error: {e.code} - {error_body}")
        raise Exception(f"OpenAI API error: {e.code} - {error_body}")

def call_anthropic(model: str, messages: List[Dict], functions: Optional[List[Dict]] = None,
                   temperature: float = 0.7) -> Dict:
    """Call Anthropic API."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    url = "https://api.anthropic.com/v1/messages"
    
    # Convert OpenAI format to Anthropic format
    anthropic_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            # Anthropic uses system as a separate parameter
            continue
        anthropic_messages.append({
            "role": msg['role'] if msg['role'] != 'assistant' else 'assistant',
            "content": msg['content']
        })
    
    # Extract system message if present
    system_msg = next((msg['content'] for msg in messages if msg['role'] == 'system'), None)
    
    payload = {
        "model": model,
        "messages": anthropic_messages,
        "temperature": temperature,
        "max_tokens": 1024
    }
    
    if system_msg:
        payload["system"] = system_msg
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    print(f"[AI] Anthropic request to {url}")
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[AI] Anthropic response received")
            
            # Convert Anthropic response to OpenAI format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": result.get("content", [{"text": ""}])[0].get("text", "")
                    }
                }]
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[AI] Anthropic error: {e.code} - {error_body}")
        raise

def format_game_messages(game_type: str, prompt: str) -> List[Dict]:
    """Format messages for the game."""
    system_prompt = f"You are an AI playing {game_type}. Make strategic decisions based on the game state."
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

def extract_function_call(response: Dict) -> Optional[Dict]:
    """Extract function call from AI response."""
    if not response or 'choices' not in response:
        return None
    
    choice = response['choices'][0]
    message = choice.get('message', {})
    
    # Check for function call
    if 'function_call' in message:
        func_call = message['function_call']
        try:
            args = json.loads(func_call.get('arguments', '{}'))
            return args
        except json.JSONDecodeError:
            print(f"[AI] Failed to parse function arguments: {func_call.get('arguments')}")
            return None
    
    # Try to extract from content (for models without function calling)
    content = message.get('content', '')
    
    # Simple extraction for moves like "reveal 5 7" or "flag 3 4"
    parts = content.lower().split()
    if len(parts) >= 3:
        action = parts[0]
        if action in ['reveal', 'flag']:
            try:
                row = int(parts[1])
                col = int(parts[2])
                return {"action": action, "row": row, "col": col}
            except (ValueError, IndexError):
                pass
    
    return None