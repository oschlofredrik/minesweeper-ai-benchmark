# Function Calling Integration

This document describes the function calling implementation for OpenAI and Anthropic models in the Minesweeper AI Benchmark.

## Overview

Function calling (OpenAI) and tool use (Anthropic) provide structured, reliable communication between AI models and the game engine. Instead of parsing text responses with regex, models return structured JSON with their moves.

## Benefits

1. **Reliability**: No more parsing errors that cause games to stop
2. **Consistency**: Guaranteed format for all responses
3. **Complete Games**: Games run to completion (win/loss)
4. **Rich Reasoning**: Built-in reasoning field with every move
5. **Better Performance**: Faster and more accurate than text parsing

## Implementation

### OpenAI Function Calling

OpenAI models use the `tools` parameter to define available functions:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "make_move",
            "description": "Make a move in Minesweeper",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reveal", "flag", "unflag"],
                        "description": "The action to perform"
                    },
                    "row": {
                        "type": "integer",
                        "description": "The row index (0-based)"
                    },
                    "col": {
                        "type": "integer",
                        "description": "The column index (0-based)"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation for this move"
                    }
                },
                "required": ["action", "row", "col", "reasoning"]
            }
        }
    }
]
```

### Anthropic Tool Use

Anthropic models use a similar tool definition format:

```python
tools = [
    {
        "name": "make_move",
        "description": "Make a move in Minesweeper",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["reveal", "flag", "unflag"]
                },
                "row": {"type": "integer"},
                "col": {"type": "integer"},
                "reasoning": {"type": "string"}
            },
            "required": ["action", "row", "col", "reasoning"]
        }
    }
]
```

## Response Processing

The system automatically:

1. **Extracts function calls** from the API response
2. **Parses parameters** into Action objects
3. **Captures reasoning** from the function call
4. **Falls back** to text parsing if needed

Example response processing:

```python
if response.function_call:
    # Parse structured response
    action = ActionType(response.function_call['action'])
    position = Position(
        row=response.function_call['row'],
        col=response.function_call['col']
    )
    reasoning = response.function_call['reasoning']
else:
    # Fall back to text parsing
    action = parse_action_from_text(response.content)
```

## Data Captured

Each move captures:

- **prompt_sent**: The exact prompt sent to the AI
- **full_response**: Complete response from the AI
- **function_call**: Structured move data (if using functions)
- **reasoning**: Why the AI made this move
- **action**: The action taken (reveal/flag/unflag)
- **position**: Row and column of the move
- **tokens_used**: Token count for the request
- **timestamp**: When the move was made

## Model Support

### Fully Supported
- GPT-4, GPT-3.5-turbo (OpenAI)
- Claude-3 models (Anthropic)
- Most modern models from both providers

### Special Handling
- **o1 models**: Function calling disabled, uses reasoning extraction
- **Claude with thinking**: Extracts thinking blocks separately

## Usage

Function calling is enabled by default. To disable:

```python
# Disable function calling
response = await model.play_move(board_state, use_functions=False)
```

## Debugging

Check if function calling was used:

```python
if response.function_call:
    print(f"Function call used: {response.function_call}")
else:
    print("Text parsing used")
```

## Future Enhancements

1. **Multi-move support**: Allow AI to plan multiple moves
2. **Strategy functions**: Let AI explain overall strategy
3. **Hint requests**: AI can ask for hints when uncertain
4. **Board analysis**: Structured analysis of game state