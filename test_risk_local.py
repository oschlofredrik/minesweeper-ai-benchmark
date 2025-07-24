#!/usr/bin/env python3
"""Test Risk game locally without the API."""

import asyncio
from src.games.registry import GameRegistry, register_builtin_games
from src.games.implementations.risk import RiskGame

async def test_risk():
    """Test Risk game directly."""
    
    # Register built-in games
    print("Registering built-in games...")
    register_builtin_games()
    
    # Check if Risk is registered
    print("\nChecking game registry...")
    from src.games.registry import game_registry
    available_games = game_registry.list_games()
    print(f"Available games: {[g['name'] for g in available_games]}")
    
    # Get Risk game
    risk_game = game_registry.get_game("risk")
    if risk_game:
        print(f"\nRisk game found: {risk_game.name}")
        print(f"Description: {risk_game.description}")
        
        # Create a game instance
        print("\nCreating game instance...")
        from src.games.base import GameConfig, GameMode
        config = GameConfig(
            difficulty="medium",
            mode=GameMode.MIXED,
            custom_settings={
                "players": ["AI", "Computer"],
                "scenario": "north_america_conquest"
            }
        )
        instance = risk_game.create_instance(config)
        
        # Get initial state
        state = instance.get_initial_state()
        print(f"\nInitial game phase: {state.state_data.get('phase')}")
        print(f"Current player: {state.state_data.get('current_player')}")
        
        # Get board state from the Risk board
        if hasattr(instance, 'board'):
            board_state = instance.board.get_board_state()
            
            # Create AI representation
            from src.games.implementations.risk.ai_representation import RiskAIInterface
            ai_rep = RiskAIInterface()
            # Set the board state
            ai_rep.board_state = board_state
            # Format state for AI
            prompt = ai_rep.format_state_for_ai(state, config)
            print("\nAI Representation:")
            print(prompt[:500] + "...")
            
            # Get function schema
            if hasattr(ai_rep, 'get_function_calling_schema'):
                schema = ai_rep.get_function_calling_schema()
                print(f"\nFunction schema: {schema['name']}")
                print(f"Description: {schema['description']}")
                print(f"Parameters: {list(schema['parameters']['properties'].keys())}")
    else:
        print("Risk game not found in registry!")

if __name__ == "__main__":
    asyncio.run(test_risk())