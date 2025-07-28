"""Risk board implementation."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
import random
from enum import Enum

from .territories import Territory, Continent, TERRITORIES, calculate_reinforcements


class GamePhase(Enum):
    """Risk game phases."""
    SETUP = "setup"  # Initial army placement
    REINFORCE = "reinforce"  # Place reinforcement armies
    ATTACK = "attack"  # Attack enemy territories
    FORTIFY = "fortify"  # Move armies between connected territories
    GAME_OVER = "game_over"


@dataclass
class TerritoryState:
    """State of a territory during the game."""
    territory_id: str
    owner: Optional[str] = None
    armies: int = 0
    
    @property
    def territory(self) -> Territory:
        return TERRITORIES[self.territory_id]


@dataclass
class PlayerState:
    """State of a player."""
    player_id: str
    color: str
    territories: Set[str] = field(default_factory=set)
    cards: List[str] = field(default_factory=list)
    reinforcements_available: int = 0
    eliminated: bool = False


class RiskBoard:
    """Risk game board with game logic."""
    
    def __init__(self, player_ids: List[str], seed: Optional[int] = None):
        """Initialize a new Risk game."""
        if seed is not None:
            random.seed(seed)
            
        self.players = {
            pid: PlayerState(
                player_id=pid,
                color=self._get_player_color(i)
            ) for i, pid in enumerate(player_ids)
        }
        
        self.territories = {
            tid: TerritoryState(territory_id=tid)
            for tid in TERRITORIES.keys()
        }
        
        self.current_player_index = 0
        self.phase = GamePhase.SETUP
        self.turn_number = 0
        self.attack_history: List[Dict] = []
        self.cards_traded = 0
        
        # Setup initial game state
        self._distribute_territories()
        self._place_initial_armies()
        
    def _get_player_color(self, index: int) -> str:
        """Get player color by index."""
        colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"]
        return colors[index % len(colors)]
    
    def _distribute_territories(self):
        """Randomly distribute territories among players."""
        territory_ids = list(TERRITORIES.keys())
        random.shuffle(territory_ids)
        
        player_ids = list(self.players.keys())
        for i, tid in enumerate(territory_ids):
            player_id = player_ids[i % len(player_ids)]
            self.territories[tid].owner = player_id
            self.territories[tid].armies = 1  # Start with 1 army
            self.players[player_id].territories.add(tid)
    
    def _place_initial_armies(self):
        """Place initial armies based on player count."""
        # Standard Risk initial army counts
        player_count = len(self.players)
        initial_armies = {
            2: 40,  # Not standard, but for 2-player variant
            3: 35,
            4: 30,
            5: 25,
            6: 20
        }
        
        armies_per_player = initial_armies.get(player_count, 20)
        
        for player in self.players.values():
            # Already placed 1 army per territory
            remaining = armies_per_player - len(player.territories)
            
            # Randomly distribute remaining armies
            for _ in range(remaining):
                territory_id = random.choice(list(player.territories))
                self.territories[territory_id].armies += 1
    
    @property
    def current_player(self) -> PlayerState:
        """Get the current player."""
        player_ids = list(self.players.keys())
        return self.players[player_ids[self.current_player_index]]
    
    def start_turn(self):
        """Start a new turn."""
        self.turn_number += 1
        self.phase = GamePhase.REINFORCE
        
        # Calculate reinforcements
        player = self.current_player
        territory_owners = {
            tid: state.owner for tid, state in self.territories.items()
        }
        player.reinforcements_available = calculate_reinforcements(
            player.player_id, territory_owners
        )
    
    def place_reinforcement(self, territory_id: str, armies: int) -> Tuple[bool, str]:
        """Place reinforcement armies."""
        if self.phase != GamePhase.REINFORCE:
            return False, "Not in reinforcement phase"
        
        territory = self.territories[territory_id]
        player = self.current_player
        
        if territory.owner != player.player_id:
            return False, f"You don't own {TERRITORIES[territory_id].name}"
        
        if armies > player.reinforcements_available:
            return False, f"You only have {player.reinforcements_available} reinforcements"
        
        territory.armies += armies
        player.reinforcements_available -= armies
        
        # Move to attack phase when all reinforcements placed
        if player.reinforcements_available == 0:
            self.phase = GamePhase.ATTACK
        
        return True, f"Placed {armies} armies in {TERRITORIES[territory_id].name}"
    
    def attack(self, from_territory: str, to_territory: str, 
               attacking_armies: int) -> Tuple[bool, str, Dict]:
        """Execute an attack."""
        if self.phase != GamePhase.ATTACK:
            return False, "Not in attack phase", {}
        
        # Validate territories
        from_state = self.territories[from_territory]
        to_state = self.territories[to_territory]
        
        if from_state.owner != self.current_player.player_id:
            return False, f"You don't own {TERRITORIES[from_territory].name}", {}
        
        if to_state.owner == self.current_player.player_id:
            return False, "Cannot attack your own territory", {}
        
        if to_territory not in TERRITORIES[from_territory].neighbors:
            return False, f"{TERRITORIES[from_territory].name} doesn't border {TERRITORIES[to_territory].name}", {}
        
        if from_state.armies <= 1:
            return False, "Must have at least 2 armies to attack", {}
        
        if attacking_armies >= from_state.armies:
            return False, "Must leave at least 1 army behind", {}
        
        if attacking_armies > 3:
            return False, "Maximum 3 armies can attack at once", {}
        
        # Execute combat
        defending_armies = min(2, to_state.armies)
        attack_result = self._resolve_combat(attacking_armies, defending_armies)
        
        # Apply results
        from_state.armies -= attack_result['attacker_losses']
        to_state.armies -= attack_result['defender_losses']
        
        # Check if territory conquered
        conquered = False
        if to_state.armies == 0:
            conquered = True
            # Transfer territory
            old_owner = to_state.owner
            self.players[old_owner].territories.remove(to_territory)
            
            to_state.owner = self.current_player.player_id
            self.current_player.territories.add(to_territory)
            
            # Move armies (minimum of attacking armies)
            armies_to_move = min(attacking_armies, from_state.armies - 1)
            from_state.armies -= armies_to_move
            to_state.armies = armies_to_move
            
            # Check if player eliminated
            if len(self.players[old_owner].territories) == 0:
                self.players[old_owner].eliminated = True
                attack_result['player_eliminated'] = old_owner
        
        attack_result['conquered'] = conquered
        self.attack_history.append(attack_result)
        
        return True, self._format_attack_result(attack_result), attack_result
    
    def _resolve_combat(self, attacking_armies: int, defending_armies: int) -> Dict:
        """Resolve combat with dice rolls."""
        # Roll dice
        attack_dice = sorted([random.randint(1, 6) for _ in range(attacking_armies)], reverse=True)
        defend_dice = sorted([random.randint(1, 6) for _ in range(defending_armies)], reverse=True)
        
        # Compare dice
        attacker_losses = 0
        defender_losses = 0
        
        for i in range(min(len(attack_dice), len(defend_dice))):
            if attack_dice[i] > defend_dice[i]:
                defender_losses += 1
            else:
                attacker_losses += 1
        
        return {
            'attack_dice': attack_dice,
            'defend_dice': defend_dice,
            'attacker_losses': attacker_losses,
            'defender_losses': defender_losses
        }
    
    def _format_attack_result(self, result: Dict) -> str:
        """Format attack result for display."""
        msg = f"Attack dice: {result['attack_dice']}, Defense dice: {result['defend_dice']}. "
        msg += f"Attacker lost {result['attacker_losses']}, Defender lost {result['defender_losses']}."
        
        if result.get('conquered'):
            msg += " Territory conquered!"
        if result.get('player_eliminated'):
            msg += f" {result['player_eliminated']} eliminated!"
        
        return msg
    
    def end_attack_phase(self):
        """End attack phase and move to fortify."""
        if self.phase == GamePhase.ATTACK:
            self.phase = GamePhase.FORTIFY
    
    def fortify(self, from_territory: str, to_territory: str, armies: int) -> Tuple[bool, str]:
        """Move armies between connected territories."""
        if self.phase != GamePhase.FORTIFY:
            return False, "Not in fortify phase"
        
        from_state = self.territories[from_territory]
        to_state = self.territories[to_territory]
        
        if from_state.owner != self.current_player.player_id:
            return False, f"You don't own {TERRITORIES[from_territory].name}"
        
        if to_state.owner != self.current_player.player_id:
            return False, f"You don't own {TERRITORIES[to_territory].name}"
        
        if from_state.armies <= armies:
            return False, "Must leave at least 1 army behind"
        
        # Check if territories are connected through owned territories
        if not self._territories_connected(from_territory, to_territory):
            return False, "Territories not connected through your territories"
        
        # Move armies
        from_state.armies -= armies
        to_state.armies += armies
        
        return True, f"Moved {armies} armies from {TERRITORIES[from_territory].name} to {TERRITORIES[to_territory].name}"
    
    def _territories_connected(self, from_tid: str, to_tid: str) -> bool:
        """Check if two territories are connected through owned territories."""
        if from_tid == to_tid:
            return True
        
        owner = self.territories[from_tid].owner
        visited = set()
        queue = [from_tid]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == to_tid:
                return True
            
            # Add owned neighbors to queue
            for neighbor in TERRITORIES[current].neighbors:
                if self.territories[neighbor].owner == owner:
                    queue.append(neighbor)
        
        return False
    
    def end_turn(self):
        """End current turn."""
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Skip eliminated players
        while self.current_player.eliminated:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # Check victory
        active_players = [p for p in self.players.values() if not p.eliminated]
        if len(active_players) == 1:
            self.phase = GamePhase.GAME_OVER
        else:
            self.start_turn()
    
    def get_valid_attacks(self) -> List[Tuple[str, str]]:
        """Get all valid attack options for current player."""
        valid_attacks = []
        player = self.current_player
        
        for from_tid in player.territories:
            from_state = self.territories[from_tid]
            if from_state.armies > 1:  # Can attack
                for to_tid in TERRITORIES[from_tid].neighbors:
                    if self.territories[to_tid].owner != player.player_id:
                        valid_attacks.append((from_tid, to_tid))
        
        return valid_attacks
    
    def get_valid_fortifications(self) -> List[Tuple[str, str]]:
        """Get all valid fortification moves."""
        valid_moves = []
        player = self.current_player
        
        for from_tid in player.territories:
            if self.territories[from_tid].armies > 1:
                for to_tid in player.territories:
                    if from_tid != to_tid and self._territories_connected(from_tid, to_tid):
                        valid_moves.append((from_tid, to_tid))
        
        return valid_moves
    
    def get_board_state(self) -> Dict:
        """Get complete board state."""
        return {
            'territories': {
                tid: {
                    'owner': state.owner,
                    'armies': state.armies,
                    'name': TERRITORIES[tid].name,
                    'continent': TERRITORIES[tid].continent.name
                } for tid, state in self.territories.items()
            },
            'players': {
                pid: {
                    'territories': list(player.territories),
                    'eliminated': player.eliminated,
                    'reinforcements': player.reinforcements_available,
                    'color': player.color
                } for pid, player in self.players.items()
            },
            'current_player': self.current_player.player_id,
            'phase': self.phase.value,
            'turn': self.turn_number
        }