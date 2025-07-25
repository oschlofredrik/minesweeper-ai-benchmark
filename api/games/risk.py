"""Simplified Risk game implementation for Vercel."""
import random
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from .base import BaseGame, GameMove, GameState

class RiskGame(BaseGame):
    """Simplified Risk game for AI evaluation."""
    
    # Simplified map with fewer territories for faster games
    TERRITORIES = {
        # North America (5 territories)
        "Alaska": {"continent": "North America", "borders": ["Northwest Territory", "Kamchatka"]},
        "Northwest Territory": {"continent": "North America", "borders": ["Alaska", "Western United States", "Eastern United States"]},
        "Western United States": {"continent": "North America", "borders": ["Northwest Territory", "Eastern United States", "Central America"]},
        "Eastern United States": {"continent": "North America", "borders": ["Northwest Territory", "Western United States", "Central America"]},
        "Central America": {"continent": "North America", "borders": ["Western United States", "Eastern United States", "Venezuela"]},
        
        # South America (3 territories)
        "Venezuela": {"continent": "South America", "borders": ["Central America", "Brazil", "Peru"]},
        "Brazil": {"continent": "South America", "borders": ["Venezuela", "Peru", "North Africa"]},
        "Peru": {"continent": "South America", "borders": ["Venezuela", "Brazil"]},
        
        # Europe (4 territories)
        "Iceland": {"continent": "Europe", "borders": ["Scandinavia", "Great Britain"]},
        "Great Britain": {"continent": "Europe", "borders": ["Iceland", "Scandinavia", "Western Europe"]},
        "Scandinavia": {"continent": "Europe", "borders": ["Iceland", "Great Britain", "Western Europe", "Ukraine"]},
        "Western Europe": {"continent": "Europe", "borders": ["Great Britain", "Scandinavia", "North Africa"]},
        
        # Africa (3 territories)
        "North Africa": {"continent": "Africa", "borders": ["Western Europe", "Brazil", "East Africa"]},
        "East Africa": {"continent": "Africa", "borders": ["North Africa", "South Africa", "Middle East"]},
        "South Africa": {"continent": "Africa", "borders": ["East Africa"]},
        
        # Asia (5 territories)
        "Middle East": {"continent": "Asia", "borders": ["East Africa", "Ukraine", "India"]},
        "Ukraine": {"continent": "Asia", "borders": ["Scandinavia", "Middle East", "Ural", "China"]},
        "Ural": {"continent": "Asia", "borders": ["Ukraine", "China", "Siberia"]},
        "China": {"continent": "Asia", "borders": ["Ukraine", "Ural", "Siberia", "India", "Kamchatka"]},
        "India": {"continent": "Asia", "borders": ["Middle East", "China"]},
        
        # Asia continued
        "Siberia": {"continent": "Asia", "borders": ["Ural", "China", "Kamchatka"]},
        "Kamchatka": {"continent": "Asia", "borders": ["Siberia", "China", "Alaska"]},
    }
    
    CONTINENT_BONUSES = {
        "North America": 3,
        "South America": 2,
        "Europe": 3,
        "Africa": 2,
        "Asia": 4
    }
    
    def __init__(self, difficulty: str = "medium", **kwargs):
        super().__init__(difficulty, **kwargs)
        self.territories = {}  # territory -> {"owner": player, "armies": count}
        self.players = ["Player", "AI"]
        self.current_player = 0
        self.phase = "placement"  # placement, attack, fortify
        self.turn_count = 0
        self.reinforcements = 0
    
    def new_game(self) -> GameState:
        """Start a new Risk game."""
        # Initialize territories
        territory_list = list(self.TERRITORIES.keys())
        random.shuffle(territory_list)
        
        # Distribute territories evenly
        for i, territory in enumerate(territory_list):
            self.territories[territory] = {
                "owner": self.players[i % 2],
                "armies": 1
            }
        
        # Give each player starting armies
        starting_armies = 20 if self.difficulty == "easy" else 15
        for player in self.players:
            armies_to_place = starting_armies
            player_territories = [t for t, info in self.territories.items() if info["owner"] == player]
            
            while armies_to_place > 0:
                territory = random.choice(player_territories)
                self.territories[territory]["armies"] += 1
                armies_to_place -= 1
        
        self.phase = "reinforcement"
        self.current_player = 0
        self._calculate_reinforcements()
        
        self.state = GameState(
            board=self._get_board_state(),
            status="in_progress",
            moves=[],
            turn_count=0
        )
        return self.state
    
    def _calculate_reinforcements(self):
        """Calculate reinforcements for current player."""
        player = self.players[self.current_player]
        
        # Base reinforcements (territories / 3)
        territories_owned = sum(1 for t in self.territories.values() if t["owner"] == player)
        self.reinforcements = max(3, territories_owned // 3)
        
        # Continent bonuses
        for continent, bonus in self.CONTINENT_BONUSES.items():
            continent_territories = [t for t, info in self.TERRITORIES.items() if info["continent"] == continent]
            if all(self.territories[t]["owner"] == player for t in continent_territories):
                self.reinforcements += bonus
    
    def _get_board_state(self) -> Dict[str, Any]:
        """Get current board state."""
        return {
            "territories": self.territories.copy(),
            "current_player": self.players[self.current_player],
            "phase": self.phase,
            "reinforcements": self.reinforcements
        }
    
    def make_move(self, move: GameMove) -> Tuple[bool, str]:
        """Make a move in Risk."""
        if self.state.status != "in_progress":
            return False, "Game is already over"
        
        player = self.players[self.current_player]
        action = move.action
        
        if self.phase == "reinforcement":
            if action != "reinforce":
                return False, f"Must reinforce during reinforcement phase"
            
            territory = move.position[0] if isinstance(move.position[0], str) else list(self.territories.keys())[move.position[0]]
            armies = move.position[1] if len(move.position) > 1 else 1
            
            if self.territories[territory]["owner"] != player:
                return False, f"You don't own {territory}"
            
            if armies > self.reinforcements:
                return False, f"Only {self.reinforcements} reinforcements available"
            
            self.territories[territory]["armies"] += armies
            self.reinforcements -= armies
            
            if self.reinforcements == 0:
                self.phase = "attack"
        
        elif self.phase == "attack":
            if action == "end_attack":
                self.phase = "fortify"
                return True, "Attack phase ended"
            
            if action != "attack":
                return False, "Must attack or end attack phase"
            
            from_territory = move.position[0] if isinstance(move.position[0], str) else list(self.territories.keys())[move.position[0]]
            to_territory = move.position[1] if isinstance(move.position[1], str) else list(self.territories.keys())[move.position[1]]
            
            # Validate attack
            if self.territories[from_territory]["owner"] != player:
                return False, f"You don't own {from_territory}"
            
            if self.territories[to_territory]["owner"] == player:
                return False, f"Cannot attack your own territory"
            
            if to_territory not in self.TERRITORIES[from_territory]["borders"]:
                return False, f"{from_territory} doesn't border {to_territory}"
            
            if self.territories[from_territory]["armies"] < 2:
                return False, f"Need at least 2 armies to attack"
            
            # Simulate battle
            attacker_dice = min(3, self.territories[from_territory]["armies"] - 1)
            defender_dice = min(2, self.territories[to_territory]["armies"])
            
            attacker_rolls = sorted([random.randint(1, 6) for _ in range(attacker_dice)], reverse=True)
            defender_rolls = sorted([random.randint(1, 6) for _ in range(defender_dice)], reverse=True)
            
            # Compare rolls
            for i in range(min(len(attacker_rolls), len(defender_rolls))):
                if attacker_rolls[i] > defender_rolls[i]:
                    self.territories[to_territory]["armies"] -= 1
                else:
                    self.territories[from_territory]["armies"] -= 1
            
            # Check if territory conquered
            if self.territories[to_territory]["armies"] == 0:
                self.territories[to_territory]["owner"] = player
                # Move armies
                armies_to_move = min(attacker_dice, self.territories[from_territory]["armies"] - 1)
                self.territories[to_territory]["armies"] = armies_to_move
                self.territories[from_territory]["armies"] -= armies_to_move
                
                # Check for win
                if all(t["owner"] == player for t in self.territories.values()):
                    self.state.status = "won"
        
        elif self.phase == "fortify":
            if action == "end_turn":
                self.current_player = (self.current_player + 1) % 2
                self.phase = "reinforcement"
                self._calculate_reinforcements()
                self.turn_count += 1
                return True, "Turn ended"
            
            if action != "fortify":
                return False, "Must fortify or end turn"
            
            from_territory = move.position[0] if isinstance(move.position[0], str) else list(self.territories.keys())[move.position[0]]
            to_territory = move.position[1] if isinstance(move.position[1], str) else list(self.territories.keys())[move.position[1]]
            armies = move.position[2] if len(move.position) > 2 else 1
            
            if self.territories[from_territory]["owner"] != player:
                return False, f"You don't own {from_territory}"
            
            if self.territories[to_territory]["owner"] != player:
                return False, f"You don't own {to_territory}"
            
            if to_territory not in self.TERRITORIES[from_territory]["borders"]:
                return False, f"{from_territory} doesn't border {to_territory}"
            
            if armies >= self.territories[from_territory]["armies"]:
                return False, f"Must leave at least 1 army in {from_territory}"
            
            self.territories[from_territory]["armies"] -= armies
            self.territories[to_territory]["armies"] += armies
            
            # Auto end turn after fortify
            self.current_player = (self.current_player + 1) % 2
            self.phase = "reinforcement"
            self._calculate_reinforcements()
            self.turn_count += 1
        
        # Update state
        self.state.moves.append(move)
        self.state.turn_count = self.turn_count
        self.state.board = self._get_board_state()
        
        return True, "Move successful"
    
    def get_board_state_for_ai(self) -> str:
        """Get board state formatted for AI."""
        player = self.players[self.current_player]
        board_str = f"Risk Game - {player}'s Turn\n"
        board_str += f"Phase: {self.phase}\n"
        
        if self.phase == "reinforcement":
            board_str += f"Reinforcements available: {self.reinforcements}\n"
        
        board_str += "\nTerritories by Continent:\n"
        
        # Group by continent
        continents = defaultdict(list)
        for territory, info in self.TERRITORIES.items():
            continents[info["continent"]].append(territory)
        
        # Display territories
        for continent in sorted(continents.keys()):
            board_str += f"\n{continent} (bonus: {self.CONTINENT_BONUSES[continent]}):\n"
            for territory in sorted(continents[continent]):
                owner = self.territories[territory]["owner"]
                armies = self.territories[territory]["armies"]
                borders = ", ".join(self.TERRITORIES[territory]["borders"])
                board_str += f"  {territory}: {owner} ({armies} armies) - borders: {borders}\n"
        
        # Summary
        board_str += "\nSummary:\n"
        for p in self.players:
            territories = sum(1 for t in self.territories.values() if t["owner"] == p)
            armies = sum(t["armies"] for t in self.territories.values() if t["owner"] == p)
            board_str += f"  {p}: {territories} territories, {armies} total armies\n"
        
        return board_str
    
    def get_valid_moves(self) -> List[Dict[str, Any]]:
        """Get valid moves for current state."""
        player = self.players[self.current_player]
        moves = []
        
        if self.phase == "reinforcement":
            # Can reinforce any owned territory
            for territory, info in self.territories.items():
                if info["owner"] == player:
                    moves.append({
                        "action": "reinforce",
                        "territory": territory,
                        "armies": min(3, self.reinforcements)  # Suggest reasonable amount
                    })
        
        elif self.phase == "attack":
            # Can attack from any territory with 2+ armies
            for from_t, from_info in self.territories.items():
                if from_info["owner"] == player and from_info["armies"] >= 2:
                    for to_t in self.TERRITORIES[from_t]["borders"]:
                        if self.territories[to_t]["owner"] != player:
                            moves.append({
                                "action": "attack",
                                "from": from_t,
                                "to": to_t
                            })
            
            # Can always end attack phase
            moves.append({"action": "end_attack"})
        
        elif self.phase == "fortify":
            # Can fortify between adjacent owned territories
            for from_t, from_info in self.territories.items():
                if from_info["owner"] == player and from_info["armies"] > 1:
                    for to_t in self.TERRITORIES[from_t]["borders"]:
                        if self.territories[to_t]["owner"] == player:
                            moves.append({
                                "action": "fortify",
                                "from": from_t,
                                "to": to_t,
                                "armies": from_info["armies"] - 1
                            })
            
            # Can always end turn
            moves.append({"action": "end_turn"})
        
        return moves
    
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.state.status != "in_progress"
    
    def get_function_schema(self) -> Dict[str, Any]:
        """Get function calling schema for Risk."""
        if self.phase == "reinforcement":
            return {
                "name": "reinforce",
                "description": "Place reinforcement armies on a territory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "territory": {"type": "string", "description": "Territory to reinforce"},
                        "armies": {"type": "integer", "description": "Number of armies to place"},
                        "reasoning": {"type": "string", "description": "Strategic reasoning"}
                    },
                    "required": ["territory", "armies", "reasoning"]
                }
            }
        elif self.phase == "attack":
            return {
                "name": "attack_action",
                "description": "Attack an enemy territory or end attack phase",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["attack", "end_attack"]},
                        "from_territory": {"type": "string", "description": "Territory to attack from (if attacking)"},
                        "to_territory": {"type": "string", "description": "Territory to attack (if attacking)"},
                        "reasoning": {"type": "string", "description": "Strategic reasoning"}
                    },
                    "required": ["action", "reasoning"]
                }
            }
        else:  # fortify phase
            return {
                "name": "fortify_action",
                "description": "Move armies between territories or end turn",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["fortify", "end_turn"]},
                        "from_territory": {"type": "string", "description": "Territory to move from (if fortifying)"},
                        "to_territory": {"type": "string", "description": "Territory to move to (if fortifying)"},
                        "armies": {"type": "integer", "description": "Number of armies to move (if fortifying)"},
                        "reasoning": {"type": "string", "description": "Strategic reasoning"}
                    },
                    "required": ["action", "reasoning"]
                }
            }