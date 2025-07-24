"""Predefined Risk game scenarios for focused AI challenges."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .risk_board import RiskBoard, TerritoryState, PlayerState, GamePhase


@dataclass
class RiskScenario:
    """A predefined Risk game scenario."""
    name: str
    description: str
    setup: Dict[str, Any]
    objectives: List[str]
    turn_limit: Optional[int] = None


# Scenario definitions
SCENARIOS = {
    "north_america_conquest": RiskScenario(
        name="North America Conquest",
        description="You control most of North America. Complete the conquest!",
        setup={
            "territories": {
                # Player 0 (AI) controls most of North America
                "alaska": {"owner": "player_0", "armies": 5},
                "northwest_territory": {"owner": "player_0", "armies": 3},
                "alberta": {"owner": "player_0", "armies": 4},
                "ontario": {"owner": "player_0", "armies": 6},
                "eastern_canada": {"owner": "player_0", "armies": 3},
                "western_us": {"owner": "player_0", "armies": 7},
                "eastern_us": {"owner": "player_0", "armies": 5},
                # Player 1 holds out in Central America and Greenland
                "central_america": {"owner": "player_1", "armies": 8},
                "greenland": {"owner": "player_1", "armies": 6},
                # Player 1 also has a foothold in South America
                "venezuela": {"owner": "player_1", "armies": 4},
                "brazil": {"owner": "player_1", "armies": 5},
                # Some other territories
                "iceland": {"owner": "player_1", "armies": 3},
                "great_britain": {"owner": "player_1", "armies": 4},
            },
            "phase": "reinforce",
            "reinforcements": 5
        },
        objectives=[
            "Conquer all of North America",
            "Minimize army losses",
            "Complete within 5 turns"
        ],
        turn_limit=5
    ),
    
    "defend_australia": RiskScenario(
        name="Defend Australia",
        description="You control Australia but enemies are massing in Asia. Defend your continent!",
        setup={
            "territories": {
                # Player 0 controls Australia
                "indonesia": {"owner": "player_0", "armies": 8},
                "new_guinea": {"owner": "player_0", "armies": 4},
                "western_australia": {"owner": "player_0", "armies": 3},
                "eastern_australia": {"owner": "player_0", "armies": 3},
                # Player 1 threatens from Asia
                "siam": {"owner": "player_1", "armies": 12},
                "india": {"owner": "player_1", "armies": 8},
                "china": {"owner": "player_1", "armies": 6},
                # Some scattered territories
                "japan": {"owner": "player_0", "armies": 2},
                "kamchatka": {"owner": "player_0", "armies": 2},
            },
            "phase": "reinforce",
            "reinforcements": 4
        },
        objectives=[
            "Maintain control of Australia",
            "Survive 10 turns",
            "Optional: Expand into Asia"
        ],
        turn_limit=10
    ),
    
    "europe_vs_asia": RiskScenario(
        name="Europe vs Asia",
        description="A classic continent showdown. You control Europe, opponent controls Asia.",
        setup={
            "territories": {
                # Player 0 controls Europe
                "iceland": {"owner": "player_0", "armies": 3},
                "great_britain": {"owner": "player_0", "armies": 4},
                "scandinavia": {"owner": "player_0", "armies": 5},
                "ukraine": {"owner": "player_0", "armies": 10},  # Border territory
                "northern_europe": {"owner": "player_0", "armies": 4},
                "western_europe": {"owner": "player_0", "armies": 4},
                "southern_europe": {"owner": "player_0", "armies": 6},
                # Player 1 controls Asia
                "ural": {"owner": "player_1", "armies": 8},  # Border territory
                "afghanistan": {"owner": "player_1", "armies": 8},  # Border territory
                "middle_east": {"owner": "player_1", "armies": 10},  # Border territory
                "siberia": {"owner": "player_1", "armies": 3},
                "china": {"owner": "player_1", "armies": 5},
                "india": {"owner": "player_1", "armies": 4},
                "siam": {"owner": "player_1", "armies": 3},
                "mongolia": {"owner": "player_1", "armies": 3},
                "japan": {"owner": "player_1", "armies": 2},
                "kamchatka": {"owner": "player_1", "armies": 2},
                "yakutsk": {"owner": "player_1", "armies": 2},
                "irkutsk": {"owner": "player_1", "armies": 2},
            },
            "phase": "reinforce",
            "reinforcements": 5
        },
        objectives=[
            "Break into Asia",
            "Maintain Europe control",
            "Achieve territorial advantage"
        ],
        turn_limit=15
    ),
    
    "blitzkrieg": RiskScenario(
        name="Blitzkrieg Challenge",
        description="You have overwhelming force. Conquer as much as possible in 3 turns!",
        setup={
            "territories": {
                # Player 0 has a strong position in South America and Africa
                "brazil": {"owner": "player_0", "armies": 15},
                "argentina": {"owner": "player_0", "armies": 8},
                "peru": {"owner": "player_0", "armies": 6},
                "venezuela": {"owner": "player_0", "armies": 10},
                "north_africa": {"owner": "player_0", "armies": 12},
                "egypt": {"owner": "player_0", "armies": 8},
                # Player 1 scattered
                "central_america": {"owner": "player_1", "armies": 3},
                "eastern_us": {"owner": "player_1", "armies": 4},
                "western_europe": {"owner": "player_1", "armies": 3},
                "southern_europe": {"owner": "player_1", "armies": 4},
                "middle_east": {"owner": "player_1", "armies": 3},
                "east_africa": {"owner": "player_1", "armies": 2},
                "central_africa": {"owner": "player_1", "armies": 2},
                "south_africa": {"owner": "player_1", "armies": 2},
                "madagascar": {"owner": "player_1", "armies": 1},
            },
            "phase": "attack",  # Start in attack phase
            "reinforcements": 0
        },
        objectives=[
            "Conquer at least 8 territories",
            "Complete conquest of Africa",
            "Do it in 3 turns"
        ],
        turn_limit=3
    ),
    
    "last_stand": RiskScenario(
        name="Last Stand",
        description="You're down to your last few territories. Can you turn it around?",
        setup={
            "territories": {
                # Player 0 has a small stronghold
                "australia": {"owner": "player_0", "armies": 12},
                "indonesia": {"owner": "player_0", "armies": 8},
                "new_guinea": {"owner": "player_0", "armies": 6},
                # Player 1 controls almost everything else (simplified)
                "siam": {"owner": "player_1", "armies": 4},
                "india": {"owner": "player_1", "armies": 3},
                "china": {"owner": "player_1", "armies": 3},
                "middle_east": {"owner": "player_1", "armies": 3},
                "ukraine": {"owner": "player_1", "armies": 3},
                "brazil": {"owner": "player_1", "armies": 4},
                # Give player 1 more territories but with fewer armies
            },
            "phase": "reinforce",
            "reinforcements": 3  # Minimum reinforcements
        },
        objectives=[
            "Survive 15 turns",
            "Control at least 6 territories",
            "Optional: Conquer a continent"
        ],
        turn_limit=15
    )
}


def load_scenario(scenario_name: str, board: RiskBoard) -> bool:
    """Load a scenario into a Risk board."""
    if scenario_name not in SCENARIOS:
        return False
    
    scenario = SCENARIOS[scenario_name]
    setup = scenario.setup
    
    # Clear existing state
    board.territories.clear()
    board.players.clear()
    
    # Set up territories
    territories_setup = setup.get("territories", {})
    all_territories = set(territories_setup.keys())
    
    # Determine players from setup
    players_in_setup = set()
    for territory_data in territories_setup.values():
        if "owner" in territory_data:
            players_in_setup.add(territory_data["owner"])
    
    # Initialize players
    for i, player_id in enumerate(sorted(players_in_setup)):
        board.players[player_id] = PlayerState(
            player_id=player_id,
            color=board._get_player_color(i)
        )
    
    # Set up all territories (even those not in setup)
    from .territories import TERRITORIES
    for tid in TERRITORIES.keys():
        if tid in territories_setup:
            data = territories_setup[tid]
            owner = data.get("owner", "player_1")
            armies = data.get("armies", 1)
        else:
            # Default unspecified territories to player_1
            owner = "player_1"
            armies = 2
        
        board.territories[tid] = TerritoryState(
            territory_id=tid,
            owner=owner,
            armies=armies
        )
        board.players[owner].territories.add(tid)
    
    # Set game phase
    phase_name = setup.get("phase", "reinforce")
    board.phase = GamePhase(phase_name)
    
    # Set current player (always player_0 for AI scenarios)
    board.current_player_index = 0
    
    # Set reinforcements if specified
    if "reinforcements" in setup:
        board.players["player_0"].reinforcements_available = setup["reinforcements"]
    
    return True


def get_scenario_description(scenario_name: str) -> str:
    """Get a detailed description of a scenario."""
    if scenario_name not in SCENARIOS:
        return "Unknown scenario"
    
    scenario = SCENARIOS[scenario_name]
    lines = [
        f"=== {scenario.name} ===",
        scenario.description,
        "",
        "Objectives:"
    ]
    
    for obj in scenario.objectives:
        lines.append(f"- {obj}")
    
    if scenario.turn_limit:
        lines.append(f"\nTurn Limit: {scenario.turn_limit}")
    
    return "\n".join(lines)