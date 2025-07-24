"""AI-friendly representations and interfaces for Risk game."""

from typing import Dict, Any, List, Optional
import json

from src.games.base import GameAction, GameState, GameConfig, GameMode, AIGameInterface
from .risk_board import GamePhase
from .territories import TERRITORIES, Continent, get_territories_by_continent


class RiskAIInterface(AIGameInterface):
    """Interface for AI models to interact with Risk game."""
    
    def get_function_calling_schema(self) -> Dict[str, Any]:
        """Get the function calling schema for structured AI responses."""
        return {
            "name": "make_risk_move",
            "description": "Make a move in the Risk game",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["reinforce", "attack", "end_attack", "fortify", "skip_fortify"],
                        "description": "The type of action to take"
                    },
                    "territory": {
                        "type": "string",
                        "description": "Territory ID for reinforce action"
                    },
                    "from": {
                        "type": "string", 
                        "description": "Source territory ID for attack/fortify"
                    },
                    "to": {
                        "type": "string",
                        "description": "Target territory ID for attack/fortify"
                    },
                    "armies": {
                        "type": "integer",
                        "description": "Number of armies to use",
                        "minimum": 1
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Explanation of your strategic thinking"
                    }
                },
                "required": ["action", "reasoning"]
            }
        }
    
    def parse_ai_response(self, response: Dict[str, Any]) -> GameAction:
        """Parse AI response into a game action."""
        action_type = response.get('action', '')
        reasoning = response.get('reasoning', '')
        
        # Build parameters based on action type
        parameters = {}
        
        if action_type == "reinforce":
            parameters = {
                'territory': response.get('territory', ''),
                'armies': response.get('armies', 1)
            }
        elif action_type == "attack":
            parameters = {
                'from': response.get('from', ''),
                'to': response.get('to', ''),
                'armies': response.get('armies', 1)
            }
        elif action_type == "fortify":
            parameters = {
                'from': response.get('from', ''),
                'to': response.get('to', ''),
                'armies': response.get('armies', 1)
            }
        # end_attack and skip_fortify have no parameters
        
        return GameAction(
            action_type=action_type,
            parameters=parameters,
            reasoning=reasoning
        )
    
    def format_state_for_ai(self, state: GameState, config: GameConfig) -> str:
        """Format game state for AI consumption."""
        board_state = state.state_data.get('board_state', {})
        
        # Use different detail levels based on mode
        if config.mode == GameMode.SPEED:
            return format_board_compact(board_state)
        else:
            return format_board_for_ai(board_state)


def format_board_for_ai(board_state: Dict) -> str:
    """Format board state in detailed, AI-friendly text."""
    lines = ["=== RISK BOARD STATE ==="]
    
    # Current player and phase
    current_player = board_state.get('current_player', 'unknown')
    phase = board_state.get('phase', 'unknown')
    turn = board_state.get('turn', 0)
    
    lines.append(f"\nTurn {turn} - {phase.upper()} Phase")
    lines.append(f"Current Player: {current_player}")
    
    # Player information
    players = board_state.get('players', {})
    current_player_data = players.get(current_player, {})
    
    if phase == "reinforce" and current_player_data.get('reinforcements', 0) > 0:
        lines.append(f"Reinforcements Available: {current_player_data['reinforcements']}")
    
    # Your territories (current player)
    lines.append(f"\n=== YOUR TERRITORIES ({current_player_data.get('color', 'Unknown')} Player) ===")
    your_territories = current_player_data.get('territories', [])
    territories_data = board_state.get('territories', {})
    
    # Group by continent
    by_continent = {}
    for tid in your_territories:
        territory = TERRITORIES.get(tid)
        tdata = territories_data.get(tid, {})
        if territory:
            continent = territory.continent
            if continent not in by_continent:
                by_continent[continent] = []
            by_continent[continent].append((tid, territory, tdata))
    
    for continent, terr_list in sorted(by_continent.items(), key=lambda x: x[0].value[0]):
        lines.append(f"\n{continent.display_name}:")
        for tid, territory, tdata in sorted(terr_list, key=lambda x: x[1].name):
            armies = tdata.get('armies', 0)
            # List neighbors with owner info
            neighbor_info = []
            for n_id in territory.neighbors:
                n_data = territories_data.get(n_id, {})
                n_owner = n_data.get('owner', 'unknown')
                n_armies = n_data.get('armies', 0)
                if n_owner != current_player:
                    neighbor_info.append(f"{TERRITORIES[n_id].name} ({n_owner}: {n_armies})")
            
            neighbor_str = ", ".join(neighbor_info) if neighbor_info else "All neighbors owned"
            lines.append(f"  - {territory.name}: {armies} armies | Borders: {neighbor_str}")
    
    # Continent control
    lines.append("\n=== CONTINENT CONTROL ===")
    from .territories import get_continent_owner
    territory_owners = {tid: tdata.get('owner') for tid, tdata in territories_data.items()}
    continent_owners = get_continent_owner(territory_owners)
    
    for continent, owner in sorted(continent_owners.items(), key=lambda x: x[0].value[0]):
        if owner:
            bonus = continent.bonus
            lines.append(f"- {continent.display_name}: {owner} (+{bonus} armies/turn)")
        else:
            territories_in_continent = get_territories_by_continent(continent)
            owners_in_continent = set(territory_owners.get(t.id) for t in territories_in_continent)
            lines.append(f"- {continent.display_name}: Disputed ({len(owners_in_continent)} players)")
    
    # Other players summary
    lines.append("\n=== OTHER PLAYERS ===")
    for pid, pdata in sorted(players.items()):
        if pid != current_player and not pdata.get('eliminated', False):
            territory_count = len(pdata.get('territories', []))
            total_armies = sum(territories_data.get(tid, {}).get('armies', 0) 
                             for tid in pdata.get('territories', []))
            lines.append(f"- {pdata.get('color', pid)}: {territory_count} territories, {total_armies} total armies")
    
    # Phase-specific information
    if phase == "attack":
        lines.append("\n=== POSSIBLE ATTACKS ===")
        attack_options = []
        for tid in your_territories:
            territory = TERRITORIES[tid]
            tdata = territories_data[tid]
            if tdata.get('armies', 0) > 1:
                for neighbor_id in territory.neighbors:
                    neighbor_data = territories_data.get(neighbor_id, {})
                    if neighbor_data.get('owner') != current_player:
                        attack_options.append(
                            f"- {territory.name} ({tdata['armies']}) → "
                            f"{TERRITORIES[neighbor_id].name} ({neighbor_data.get('armies', 0)})"
                        )
        
        if attack_options:
            lines.extend(attack_options[:10])  # Limit to 10 to avoid overwhelming
            if len(attack_options) > 10:
                lines.append(f"... and {len(attack_options) - 10} more options")
        else:
            lines.append("No attacks possible - all neighbors are owned by you")
    
    elif phase == "fortify":
        lines.append("\n=== FORTIFICATION OPTIONS ===")
        lines.append("You can move armies between your connected territories")
        # Show territories with multiple armies
        fortify_sources = [
            f"- {TERRITORIES[tid].name}: {territories_data[tid]['armies']} armies"
            for tid in your_territories
            if territories_data.get(tid, {}).get('armies', 0) > 1
        ]
        if fortify_sources:
            lines.append("Territories with moveable armies:")
            lines.extend(fortify_sources[:5])
    
    return "\n".join(lines)


def format_board_compact(board_state: Dict) -> str:
    """Format board state in compact form for speed mode."""
    current_player = board_state.get('current_player', 'unknown')
    phase = board_state.get('phase', 'unknown')
    players = board_state.get('players', {})
    territories = board_state.get('territories', {})
    
    lines = [
        f"Phase: {phase}, Player: {current_player}",
        f"Your territories: {len(players.get(current_player, {}).get('territories', []))}",
    ]
    
    if phase == "reinforce":
        reinforcements = players.get(current_player, {}).get('reinforcements', 0)
        lines.append(f"Reinforcements: {reinforcements}")
    
    # List territories with armies
    your_territories = players.get(current_player, {}).get('territories', [])
    territory_list = []
    for tid in sorted(your_territories):
        tdata = territories.get(tid, {})
        territory_list.append(f"{tid}:{tdata.get('armies', 0)}")
    
    lines.append("Territories: " + ", ".join(territory_list))
    
    return "\n".join(lines)


def format_valid_actions(possible_actions: List[GameAction]) -> str:
    """Format possible actions for AI."""
    if not possible_actions:
        return "No valid actions available"
    
    # Group by action type
    by_type = {}
    for action in possible_actions:
        action_type = action.action_type
        if action_type not in by_type:
            by_type[action_type] = []
        by_type[action_type].append(action)
    
    lines = []
    for action_type, actions in by_type.items():
        if action_type == "reinforce":
            # Summarize reinforce options
            territories = set(a.parameters['territory'] for a in actions)
            max_armies = max(a.parameters['armies'] for a in actions)
            lines.append(f"- Reinforce: Any of your territories with 1-{max_armies} armies")
        
        elif action_type == "attack":
            # Show a few attack options
            lines.append("- Attack options:")
            for action in actions[:5]:
                params = action.parameters
                lines.append(f"  {params['from']} → {params['to']} (with {params['armies']} armies)")
            if len(actions) > 5:
                lines.append(f"  ... and {len(actions) - 5} more attack options")
        
        elif action_type == "fortify":
            # Summarize fortify options
            lines.append("- Fortify: Move armies between connected territories")
            unique_routes = set((a.parameters['from'], a.parameters['to']) for a in actions)
            lines.append(f"  {len(unique_routes)} possible routes available")
        
        else:
            # Simple actions
            lines.append(f"- {action_type.replace('_', ' ').title()}")
    
    return "\n".join(lines)