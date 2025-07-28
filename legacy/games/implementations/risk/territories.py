"""Territory and continent definitions for Risk game."""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum


class Continent(Enum):
    """Risk continents with their army bonuses."""
    NORTH_AMERICA = ("North America", 5)
    SOUTH_AMERICA = ("South America", 2)
    EUROPE = ("Europe", 5)
    AFRICA = ("Africa", 3)
    ASIA = ("Asia", 7)
    AUSTRALIA = ("Australia", 2)
    
    def __init__(self, display_name: str, bonus: int):
        self.display_name = display_name
        self.bonus = bonus


@dataclass
class Territory:
    """Represents a territory on the Risk board."""
    id: str
    name: str
    continent: Continent
    neighbors: List[str]  # List of territory IDs
    
    def __hash__(self):
        return hash(self.id)


# Classic Risk board territories
TERRITORIES = {
    # North America (9 territories)
    "alaska": Territory("alaska", "Alaska", Continent.NORTH_AMERICA, 
                       ["northwest_territory", "alberta", "kamchatka"]),
    "northwest_territory": Territory("northwest_territory", "Northwest Territory", Continent.NORTH_AMERICA,
                                   ["alaska", "alberta", "ontario", "greenland"]),
    "greenland": Territory("greenland", "Greenland", Continent.NORTH_AMERICA,
                          ["northwest_territory", "ontario", "eastern_canada", "iceland"]),
    "alberta": Territory("alberta", "Alberta", Continent.NORTH_AMERICA,
                        ["alaska", "northwest_territory", "ontario", "western_us"]),
    "ontario": Territory("ontario", "Ontario", Continent.NORTH_AMERICA,
                        ["northwest_territory", "greenland", "alberta", "western_us", 
                         "eastern_us", "eastern_canada"]),
    "eastern_canada": Territory("eastern_canada", "Eastern Canada", Continent.NORTH_AMERICA,
                               ["greenland", "ontario", "eastern_us"]),
    "western_us": Territory("western_us", "Western United States", Continent.NORTH_AMERICA,
                           ["alberta", "ontario", "eastern_us", "central_america"]),
    "eastern_us": Territory("eastern_us", "Eastern United States", Continent.NORTH_AMERICA,
                           ["ontario", "eastern_canada", "western_us", "central_america"]),
    "central_america": Territory("central_america", "Central America", Continent.NORTH_AMERICA,
                                ["western_us", "eastern_us", "venezuela"]),
    
    # South America (4 territories)
    "venezuela": Territory("venezuela", "Venezuela", Continent.SOUTH_AMERICA,
                          ["central_america", "brazil", "peru"]),
    "brazil": Territory("brazil", "Brazil", Continent.SOUTH_AMERICA,
                       ["venezuela", "peru", "argentina", "north_africa"]),
    "peru": Territory("peru", "Peru", Continent.SOUTH_AMERICA,
                     ["venezuela", "brazil", "argentina"]),
    "argentina": Territory("argentina", "Argentina", Continent.SOUTH_AMERICA,
                          ["peru", "brazil"]),
    
    # Europe (7 territories)
    "iceland": Territory("iceland", "Iceland", Continent.EUROPE,
                        ["greenland", "great_britain", "scandinavia"]),
    "great_britain": Territory("great_britain", "Great Britain", Continent.EUROPE,
                              ["iceland", "scandinavia", "northern_europe", "western_europe"]),
    "scandinavia": Territory("scandinavia", "Scandinavia", Continent.EUROPE,
                            ["iceland", "great_britain", "northern_europe", "ukraine"]),
    "ukraine": Territory("ukraine", "Ukraine", Continent.EUROPE,
                        ["scandinavia", "northern_europe", "southern_europe", "middle_east",
                         "afghanistan", "ural"]),
    "northern_europe": Territory("northern_europe", "Northern Europe", Continent.EUROPE,
                                ["great_britain", "scandinavia", "ukraine", "southern_europe",
                                 "western_europe"]),
    "western_europe": Territory("western_europe", "Western Europe", Continent.EUROPE,
                               ["great_britain", "northern_europe", "southern_europe", "north_africa"]),
    "southern_europe": Territory("southern_europe", "Southern Europe", Continent.EUROPE,
                                ["western_europe", "northern_europe", "ukraine", "middle_east",
                                 "egypt", "north_africa"]),
    
    # Africa (6 territories)
    "north_africa": Territory("north_africa", "North Africa", Continent.AFRICA,
                             ["brazil", "western_europe", "southern_europe", "egypt", 
                              "east_africa", "central_africa"]),
    "egypt": Territory("egypt", "Egypt", Continent.AFRICA,
                      ["southern_europe", "middle_east", "north_africa", "east_africa"]),
    "east_africa": Territory("east_africa", "East Africa", Continent.AFRICA,
                            ["egypt", "middle_east", "north_africa", "central_africa",
                             "south_africa", "madagascar"]),
    "central_africa": Territory("central_africa", "Central Africa", Continent.AFRICA,
                               ["north_africa", "east_africa", "south_africa"]),
    "south_africa": Territory("south_africa", "South Africa", Continent.AFRICA,
                             ["central_africa", "east_africa", "madagascar"]),
    "madagascar": Territory("madagascar", "Madagascar", Continent.AFRICA,
                           ["east_africa", "south_africa"]),
    
    # Asia (12 territories)
    "ural": Territory("ural", "Ural", Continent.ASIA,
                     ["ukraine", "siberia", "afghanistan", "china"]),
    "siberia": Territory("siberia", "Siberia", Continent.ASIA,
                        ["ural", "yakutsk", "irkutsk", "mongolia", "china"]),
    "yakutsk": Territory("yakutsk", "Yakutsk", Continent.ASIA,
                        ["siberia", "kamchatka", "irkutsk"]),
    "kamchatka": Territory("kamchatka", "Kamchatka", Continent.ASIA,
                          ["yakutsk", "alaska", "japan", "mongolia", "irkutsk"]),
    "irkutsk": Territory("irkutsk", "Irkutsk", Continent.ASIA,
                        ["siberia", "yakutsk", "kamchatka", "mongolia"]),
    "mongolia": Territory("mongolia", "Mongolia", Continent.ASIA,
                         ["siberia", "irkutsk", "kamchatka", "japan", "china"]),
    "japan": Territory("japan", "Japan", Continent.ASIA,
                      ["kamchatka", "mongolia"]),
    "afghanistan": Territory("afghanistan", "Afghanistan", Continent.ASIA,
                           ["ukraine", "ural", "china", "india", "middle_east"]),
    "china": Territory("china", "China", Continent.ASIA,
                      ["afghanistan", "ural", "siberia", "mongolia", "siam", "india"]),
    "middle_east": Territory("middle_east", "Middle East", Continent.ASIA,
                            ["ukraine", "southern_europe", "egypt", "east_africa",
                             "afghanistan", "india"]),
    "india": Territory("india", "India", Continent.ASIA,
                      ["middle_east", "afghanistan", "china", "siam"]),
    "siam": Territory("siam", "Siam", Continent.ASIA,
                     ["india", "china", "indonesia"]),
    
    # Australia (4 territories)
    "indonesia": Territory("indonesia", "Indonesia", Continent.AUSTRALIA,
                          ["siam", "new_guinea", "western_australia"]),
    "new_guinea": Territory("new_guinea", "New Guinea", Continent.AUSTRALIA,
                           ["indonesia", "eastern_australia", "western_australia"]),
    "western_australia": Territory("western_australia", "Western Australia", Continent.AUSTRALIA,
                                  ["indonesia", "new_guinea", "eastern_australia"]),
    "eastern_australia": Territory("eastern_australia", "Eastern Australia", Continent.AUSTRALIA,
                                  ["new_guinea", "western_australia"])
}


def get_territories_by_continent(continent: Continent) -> List[Territory]:
    """Get all territories in a continent."""
    return [t for t in TERRITORIES.values() if t.continent == continent]


def get_continent_owner(territory_owners: Dict[str, str]) -> Dict[Continent, Optional[str]]:
    """Determine which player owns each continent."""
    continent_owners = {}
    
    for continent in Continent:
        territories = get_territories_by_continent(continent)
        territory_ids = {t.id for t in territories}
        
        # Check if one player owns all territories
        owners = {territory_owners.get(tid) for tid in territory_ids if tid in territory_owners}
        
        if len(owners) == 1 and None not in owners:
            continent_owners[continent] = owners.pop()
        else:
            continent_owners[continent] = None
    
    return continent_owners


def calculate_reinforcements(player: str, territory_owners: Dict[str, str]) -> int:
    """Calculate reinforcements for a player based on territories and continents."""
    # Base reinforcements from territories (minimum 3)
    player_territories = [tid for tid, owner in territory_owners.items() if owner == player]
    territory_bonus = max(3, len(player_territories) // 3)
    
    # Continent bonuses
    continent_bonus = 0
    continent_owners = get_continent_owner(territory_owners)
    
    for continent, owner in continent_owners.items():
        if owner == player:
            continent_bonus += continent.bonus
    
    return territory_bonus + continent_bonus