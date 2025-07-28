"""Risk game plugin implementation for Tilts platform."""

import json
import uuid
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from src.games.base import (
    BaseGame, GameInstance, GameState, GameAction, GameResult,
    GameConfig, GameMode, ScoringComponent, AIGameInterface
)
from .risk_board import RiskBoard, GamePhase
from .territories import TERRITORIES, Continent, get_territories_by_continent
from .ai_representation import RiskAIInterface, format_board_for_ai


class RiskGame(BaseGame):
    """Risk board game implementation as a Tilts plugin."""
    
    @property
    def name(self) -> str:
        return "risk"
    
    @property
    def display_name(self) -> str:
        return "Risk"
    
    @property
    def description(self) -> str:
        return "Strategic board game of diplomacy, conflict and conquest for 2-6 players"
    
    @property
    def supported_modes(self) -> List[GameMode]:
        return [
            GameMode.ACCURACY,  # Best strategic decisions
            GameMode.EFFICIENCY,  # Quickest conquest
            GameMode.REASONING,  # Best explained strategy
            GameMode.MIXED
        ]
    
    def get_scoring_components(self) -> List[ScoringComponent]:
        return [
            ScoringComponent(
                name="victory",
                description="Whether the game was won",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="territory_control",
                description="Percentage of territories controlled at game end",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="continent_control",
                description="Number of continents controlled",
                min_value=0.0,
                max_value=6.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="strategic_efficiency",
                description="Ratio of successful attacks to total attacks",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="army_efficiency",
                description="Armies remaining vs armies lost",
                min_value=0.0,
                max_value=2.0,
                higher_is_better=True
            ),
            ScoringComponent(
                name="turn_efficiency",
                description="Inverse of turns taken (1/turns)",
                min_value=0.0,
                max_value=1.0,
                higher_is_better=True
            )
        ]
    
    def create_instance(self, config: GameConfig) -> GameInstance:
        """Create a new Risk game instance."""
        return RiskInstance(config, str(uuid.uuid4()))
    
    def get_ai_prompt_template(self) -> str:
        return """You are playing Risk, the strategic board game. Your goal is to conquer all territories on the map.

Game Phases:
1. REINFORCE - Place new armies on your territories
2. ATTACK - Attack adjacent enemy territories  
3. FORTIFY - Move armies between your connected territories

Current Board State:
{board_state}

Valid Actions:
{valid_actions}

Rules:
- You must leave at least 1 army in each territory
- You can attack with 1-3 armies (defender defends with 1-2)
- Higher dice win, ties go to defender
- You can fortify once per turn between connected territories

Make your move using the provided action format."""
    
    def get_move_format_description(self) -> str:
        return """Risk moves use JSON format:

Reinforce Phase:
{
    "action": "reinforce",
    "territory": "brazil",
    "armies": 3
}

Attack Phase:
{
    "action": "attack",
    "from": "brazil", 
    "to": "argentina",
    "armies": 3
}
OR
{
    "action": "end_attack"
}

Fortify Phase:
{
    "action": "fortify",
    "from": "brazil",
    "to": "north_africa", 
    "armies": 5
}
OR
{
    "action": "skip_fortify"
}"""
    
    def get_visualization_data(self, state: GameState) -> Dict[str, Any]:
        """Get data for frontend visualization."""
        board_data = state.state_data.get('board_state', {})
        
        # Structure data for Risk board visualization
        territories = []
        for tid, tdata in board_data.get('territories', {}).items():
            territories.append({
                'id': tid,
                'name': tdata['name'],
                'owner': tdata['owner'],
                'armies': tdata['armies'],
                'continent': tdata['continent'],
                'x': 0,  # Would need actual coordinates
                'y': 0
            })
        
        return {
            'territories': territories,
            'connections': self._get_territory_connections(),
            'players': board_data.get('players', {}),
            'phase': board_data.get('phase'),
            'currentPlayer': board_data.get('current_player')
        }
    
    def _get_territory_connections(self) -> List[Dict]:
        """Get territory connection data for visualization."""
        connections = []
        seen = set()
        
        for tid, territory in TERRITORIES.items():
            for neighbor in territory.neighbors:
                # Avoid duplicates
                edge = tuple(sorted([tid, neighbor]))
                if edge not in seen:
                    seen.add(edge)
                    connections.append({
                        'from': tid,
                        'to': neighbor
                    })
        
        return connections


class RiskInstance(GameInstance):
    """A single instance of a Risk game."""
    
    def __init__(self, config: GameConfig, instance_id: str):
        super().__init__(config, instance_id)
        
        # Get number of AI players from config
        num_players = config.custom_settings.get('num_players', 2)
        player_ids = [f"player_{i}" for i in range(num_players)]
        
        # Initialize board
        seed = config.custom_settings.get('seed')
        self.board = RiskBoard(player_ids, seed=seed)
        self.ai_interface = RiskAIInterface()
        
        # Start first turn
        self.board.start_turn()
        
        # Track statistics
        self.total_attacks = 0
        self.successful_attacks = 0
        self.armies_lost = 0
        self.armies_killed = 0
    
    def get_initial_state(self) -> GameState:
        """Get the initial game state."""
        return self._create_game_state()
    
    def _create_game_state(self) -> GameState:
        """Create a GameState from current board."""
        board_state = self.board.get_board_state()
        is_terminal = self.board.phase == GamePhase.GAME_OVER
        
        # Determine victory
        is_victory = False
        if is_terminal:
            # In single-player AI evaluation, player_0 is the AI
            active_players = [p for p in self.board.players.values() if not p.eliminated]
            is_victory = len(active_players) == 1 and active_players[0].player_id == "player_0"
        
        # Get possible actions based on phase
        possible_actions = self._get_possible_actions()
        
        return GameState(
            state_data={
                'board_state': board_state,
                'phase': self.board.phase.value,
                'current_player': self.board.current_player.player_id
            },
            is_terminal=is_terminal,
            is_victory=is_victory,
            possible_actions=possible_actions
        )
    
    def _get_possible_actions(self) -> List[GameAction]:
        """Get all possible actions in current state."""
        actions = []
        phase = self.board.phase
        player = self.board.current_player
        
        if phase == GamePhase.REINFORCE:
            # Can reinforce any owned territory
            for tid in player.territories:
                for armies in range(1, player.reinforcements_available + 1):
                    actions.append(GameAction(
                        action_type="reinforce",
                        parameters={"territory": tid, "armies": armies}
                    ))
        
        elif phase == GamePhase.ATTACK:
            # Can attack or end attack phase
            actions.append(GameAction(action_type="end_attack", parameters={}))
            
            for from_tid, to_tid in self.board.get_valid_attacks():
                max_armies = min(3, self.board.territories[from_tid].armies - 1)
                for armies in range(1, max_armies + 1):
                    actions.append(GameAction(
                        action_type="attack",
                        parameters={"from": from_tid, "to": to_tid, "armies": armies}
                    ))
        
        elif phase == GamePhase.FORTIFY:
            # Can fortify or skip
            actions.append(GameAction(action_type="skip_fortify", parameters={}))
            
            for from_tid, to_tid in self.board.get_valid_fortifications():
                max_armies = self.board.territories[from_tid].armies - 1
                for armies in range(1, max_armies + 1):
                    actions.append(GameAction(
                        action_type="fortify",
                        parameters={"from": from_tid, "to": to_tid, "armies": armies}
                    ))
        
        return actions
    
    def apply_action(self, state: GameState, action: GameAction) -> Tuple[GameState, bool, str]:
        """Apply an action to the game state."""
        # Validate it's the AI's turn (player_0 in single-player evaluation)
        if self.board.current_player.player_id != "player_0":
            # Execute opponent moves automatically
            self._execute_opponent_turns()
        
        # Now apply the AI's action
        action_type = action.action_type
        params = action.parameters
        
        if action_type == "reinforce":
            success, message = self.board.place_reinforcement(
                params['territory'], params['armies']
            )
        
        elif action_type == "attack":
            success, message, result = self.board.attack(
                params['from'], params['to'], params['armies']
            )
            if success:
                self.total_attacks += 1
                if result.get('conquered'):
                    self.successful_attacks += 1
                self.armies_lost += result.get('attacker_losses', 0)
                self.armies_killed += result.get('defender_losses', 0)
        
        elif action_type == "end_attack":
            self.board.end_attack_phase()
            success, message = True, "Ended attack phase"
        
        elif action_type == "fortify":
            success, message = self.board.fortify(
                params['from'], params['to'], params['armies']
            )
            # End turn after fortify
            if success:
                self.board.end_turn()
        
        elif action_type == "skip_fortify":
            self.board.end_turn()
            success, message = True, "Skipped fortification"
        
        else:
            success, message = False, f"Unknown action type: {action_type}"
        
        # Create new state
        new_state = self._create_game_state()
        
        return new_state, success, message
    
    def _execute_opponent_turns(self):
        """Execute simple AI moves for opponents."""
        while self.board.current_player.player_id != "player_0" and self.board.phase != GamePhase.GAME_OVER:
            player = self.board.current_player
            phase = self.board.phase
            
            if phase == GamePhase.REINFORCE:
                # Place all reinforcements on territory with most armies
                best_territory = max(player.territories, 
                                   key=lambda t: self.board.territories[t].armies)
                self.board.place_reinforcement(best_territory, player.reinforcements_available)
            
            elif phase == GamePhase.ATTACK:
                # Simple aggressive AI - attack if possible
                valid_attacks = self.board.get_valid_attacks()
                if valid_attacks and self.turn_number < 100:  # Prevent infinite games
                    # Find best attack (most armies vs least armies)
                    best_attack = max(valid_attacks, 
                                    key=lambda a: self.board.territories[a[0]].armies - 
                                                 self.board.territories[a[1]].armies)
                    from_tid, to_tid = best_attack
                    armies = min(3, self.board.territories[from_tid].armies - 1)
                    self.board.attack(from_tid, to_tid, armies)
                else:
                    self.board.end_attack_phase()
            
            elif phase == GamePhase.FORTIFY:
                # Skip fortification for simplicity
                self.board.end_turn()
    
    def calculate_score_components(self, result: GameResult) -> Dict[str, float]:
        """Calculate scoring components for the game."""
        final_state = result.final_state.state_data['board_state']
        
        # Territory control
        total_territories = len(TERRITORIES)
        player_territories = len(final_state['players']['player_0']['territories'])
        territory_control = player_territories / total_territories
        
        # Continent control
        from .territories import get_continent_owner
        territory_owners = {
            tid: tdata['owner'] 
            for tid, tdata in final_state['territories'].items()
        }
        continent_owners = get_continent_owner(territory_owners)
        continents_controlled = sum(1 for owner in continent_owners.values() 
                                   if owner == 'player_0')
        
        # Strategic efficiency
        strategic_efficiency = (self.successful_attacks / self.total_attacks 
                               if self.total_attacks > 0 else 0.5)
        
        # Army efficiency
        army_efficiency = (self.armies_killed / (self.armies_lost + 1))  # +1 to avoid division by zero
        army_efficiency = min(2.0, army_efficiency)  # Cap at 2.0
        
        # Turn efficiency
        turn_efficiency = 1.0 / max(1, self.board.turn_number)
        
        return {
            'victory': 1.0 if result.victory else 0.0,
            'territory_control': territory_control,
            'continent_control': continents_controlled,
            'strategic_efficiency': strategic_efficiency,
            'army_efficiency': army_efficiency,
            'turn_efficiency': turn_efficiency
        }
    
    def get_optimal_moves(self, state: GameState) -> int:
        """Estimate optimal moves from this state."""
        # Risk doesn't have a clear optimal move count
        # Estimate based on territories left to conquer
        board_state = state.state_data['board_state']
        player_territories = len(board_state['players']['player_0']['territories'])
        total_territories = len(TERRITORIES)
        
        # Rough estimate: 2 moves per territory to conquer
        return (total_territories - player_territories) * 2


# Export the game class
__all__ = ['RiskGame']