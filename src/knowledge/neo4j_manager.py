"""
Neo4j Manager for the TTA Project.

This module provides a manager for interacting with the Neo4j database.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # If dotenv is not available, we'll just use the environment variables as is
    pass

# Neo4j connection details from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "11111111")

# Player character ID
PLAYER_CHARACTER_ID = "player_001"

# Current location ID (for tracking player position)
CURRENT_LOCATION_ID = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jManager:
    """
    Manager for interacting with the Neo4j database.

    This class provides methods for querying the Neo4j database,
    managing locations, items, characters, and relationships.
    """

    def __init__(
        self,
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD
    ):
        """
        Initialize the Neo4j manager.

        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
        """
        self._driver = None
        self._mock_db = {"locations": {}, "items": {}, "characters": {}, "relationships": []}
        self._using_mock_db = False

        if GraphDatabase is None:
            logger.warning("Neo4j driver not available. Using mock database.")
            self._using_mock_db = True
            return

        try:
            self._driver = GraphDatabase.driver(uri, auth=(username, password))
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            logger.warning("Using mock database for testing")
            self._using_mock_db = True

    def clear_database(self) -> None:
        """Clear all data from the database."""
        if not self._driver:
            return

        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.query(query)
        logger.info("Database cleared")

    def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            self._driver.close()

    def query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a query against the Neo4j database.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            List of records
        """
        if not self._driver or self._using_mock_db:
            # If we're already using the mock DB or can't connect, use the mock DB
            self._using_mock_db = True
            return self._mock_query(query, parameters)

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # If we can't connect, switch to mock DB
            self._using_mock_db = True
            logger.warning("Switching to mock database mode for testing")
            return self._mock_query(query, parameters)

    def _mock_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a query against the mock database.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            List of mock records
        """
        # Create a mock record class for returning data
        class MockRecord:
            def __init__(self, data):
                self.data_dict = data

            def __getitem__(self, key):
                return self.data_dict[key]

            def data(self):
                return self.data_dict

            def get(self, key, default=None):
                return self.data_dict.get(key, default)

            def items(self):
                return self.data_dict.items()

            def keys(self):
                return self.data_dict.keys()

            def values(self):
                return self.data_dict.values()

            def __str__(self):
                return str(self.data_dict)

        # For create operations
        if query.strip().upper().startswith("CREATE") or query.strip().upper().startswith("MERGE"):
            # Just return an empty success result
            return []

        # For match operations
        elif query.strip().upper().startswith("MATCH"):
            # Special case for get_current_location
            if "MATCH (p:Character {id: $player_id})-[:LOCATED_AT]->(l:Location)" in query:
                # Return a mock forest edge location
                return [
                    MockRecord(
                        {
                            "id": "loc_001",
                            "name": "Forest Edge",
                            "description": "The edge of a mysterious forest. Tall trees loom ahead, while a meadow stretches behind you.",
                        }
                    )
                ]

            # Special case for get_items_at_location
            elif "MATCH (l:Location {id: $location_id})-[:CONTAINS]->(i:Item)" in query or "MATCH (l:Location {name: $location_id})-[:CONTAINS]->(i:Item)" in query:
                # Return mock items
                return [
                    MockRecord(
                        {
                            "id": "item_001",
                            "name": "Old Map",
                            "description": "A weathered map showing the forest and surrounding areas.",
                        }
                    ),
                    MockRecord(
                        {
                            "id": "item_002",
                            "name": "Glowing Berries",
                            "description": "Small berries that emit a soft blue glow. They look edible.",
                        }
                    ),
                ]

            # Special case for get_characters_at_location
            elif "MATCH (l:Location {id: $location_id})-[:CONTAINS]->(c:Character)" in query or "MATCH (l:Location {name: $location_id})-[:CONTAINS]->(c:Character)" in query:
                # Return mock characters
                return [
                    MockRecord(
                        {
                            "id": "char_001",
                            "name": "Forest Guardian",
                            "description": "A mysterious figure who protects the forest.",
                        }
                    )
                ]

            # Special case for get_player_inventory
            elif "MATCH (c:Character {id: $player_id})-[:HAS_ITEM]->(i:Item)" in query:
                # Return mock inventory
                return [
                    MockRecord(
                        {
                            "id": "item_003",
                            "name": "Rusty Key",
                            "description": "An old iron key with intricate patterns.",
                        }
                    )
                ]

            # Special case for get_location_details
            elif "MATCH (l:Location {name: $name})" in query:
                location_name = parameters.get("name", "Unknown")
                if location_name == "Forest Clearing":
                    return [
                        MockRecord(
                            {
                                "name": "Forest Clearing",
                                "description": "A peaceful clearing in the forest. Sunlight filters through the canopy above.",
                                "items": [],
                                "characters": [],
                            }
                        )
                    ]
                elif location_name == "Forest Edge":
                    return [
                        MockRecord(
                            {
                                "name": "Forest Edge",
                                "description": "The edge of a mysterious forest. Tall trees loom ahead, while a meadow stretches behind you.",
                                "items": [],
                                "characters": [],
                            }
                        )
                    ]

            # Special case for get_exits
            elif "MATCH (l:Location {name: $location_name})-[r:EXITS_TO]->(destination:Location)" in query:
                location_name = parameters.get("location_name", "Unknown")
                if location_name == "Forest Clearing":
                    return [
                        MockRecord(
                            {
                                "direction": "north",
                                "target": "Forest Edge",
                                "description": "A path leading deeper into the forest.",
                            }
                        ),
                        MockRecord(
                            {
                                "direction": "east",
                                "target": "River Bank",
                                "description": "A narrow trail leading to a river.",
                            }
                        )
                    ]
                elif location_name == "Forest Edge":
                    return [
                        MockRecord(
                            {
                                "direction": "south",
                                "target": "Forest Clearing",
                                "description": "A path leading back to the clearing.",
                            }
                        )
                    ]

            # Return empty list for other match queries
            return []

        # Default case
        return []

    def get_location_details(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a location.

        Args:
            location_name: Name of the location

        Returns:
            Location details or None if not found
        """
        query = """
        MATCH (l:Location {name: $name})
        RETURN l.name AS name, l.description AS description
        """

        result = self.query(query, {"name": location_name})

        if not result:
            return None

        # Get items at the location
        items_query = """
        MATCH (l:Location {name: $location_id})-[:CONTAINS]->(i:Item)
        RETURN i.name AS name, i.description AS description
        """

        items = self.query(items_query, {"location_id": location_name})

        # Get characters at the location
        characters_query = """
        MATCH (l:Location {name: $location_id})-[:CONTAINS]->(c:Character)
        WHERE c.character_id <> $player_id
        RETURN c.name AS name, c.description AS description
        """

        characters = self.query(
            characters_query, {"location_id": location_name, "player_id": PLAYER_CHARACTER_ID}
        )

        # Combine all data
        location_data = dict(result[0])
        location_data["items"] = [dict(item) for item in items]
        location_data["characters"] = [dict(char) for char in characters]

        return location_data

    def get_exits(self, location_name: str) -> List[Dict[str, Any]]:
        """
        Get exits from a location.

        Args:
            location_name: Name of the location

        Returns:
            List of exits
        """
        query = """
        MATCH (l:Location {name: $location_name})-[r:EXITS_TO]->(destination:Location)
        RETURN r.direction AS direction, destination.name AS target, r.description AS description
        """

        result = self.query(query, {"location_name": location_name})

        return [dict(exit) for exit in result]

    def get_items_at_location(self, location_name: str) -> List[Dict[str, Any]]:
        """
        Get items at a location.

        Args:
            location_name: Name of the location

        Returns:
            List of items
        """
        query = """
        MATCH (l:Location {name: $location_id})-[:CONTAINS]->(i:Item)
        RETURN i.name AS name, i.description AS description
        """

        result = self.query(query, {"location_id": location_name})

        return [dict(item) for item in result]

    def get_npcs_at_location(self, location_name: str) -> List[Dict[str, Any]]:
        """
        Get NPCs at a location.

        Args:
            location_name: Name of the location

        Returns:
            List of NPCs
        """
        query = """
        MATCH (l:Location {name: $location_id})-[:CONTAINS]->(c:Character)
        WHERE c.character_id <> $player_id
        RETURN c.name AS name, c.description AS description
        """

        result = self.query(
            query, {"location_id": location_name, "player_id": PLAYER_CHARACTER_ID}
        )

        return [dict(npc) for npc in result]

    def get_player_inventory(self, player_id: str) -> List[Dict[str, Any]]:
        """
        Get the player's inventory.

        Args:
            player_id: ID of the player

        Returns:
            List of items in the player's inventory
        """
        query = """
        MATCH (c:Character {character_id: $player_id})-[:HAS_ITEM]->(i:Item)
        RETURN i.name AS name, i.description AS description
        """

        result = self.query(query, {"player_id": player_id})

        return [dict(item) for item in result]

    def remove_item_from_location(self, item_name: str, location_name: str) -> bool:
        """
        Remove an item from a location and add it to the player's inventory.

        Args:
            item_name: Name of the item to remove
            location_name: Name of the location containing the item

        Returns:
            True if successful, False otherwise
        """
        # First, check if the item exists at the location
        check_query = """
        MATCH (l:Location {name: $location_name})-[:CONTAINS]->(i:Item {name: $item_name})
        RETURN i.name AS name, i.description AS description
        """

        result = self.query(check_query, {"location_name": location_name, "item_name": item_name})

        if not result:
            logger.warning(f"Item {item_name} not found at {location_name}")
            return False

        # Remove the CONTAINS relationship between the location and the item
        remove_query = """
        MATCH (l:Location {name: $location_name})-[r:CONTAINS]->(i:Item {name: $item_name})
        DELETE r
        """

        self.query(remove_query, {"location_name": location_name, "item_name": item_name})

        # Create a HAS_ITEM relationship between the player and the item
        add_to_inventory_query = """
        MATCH (c:Character {character_id: $player_id}), (i:Item {name: $item_name})
        CREATE (c)-[:HAS_ITEM]->(i)
        """

        self.query(add_to_inventory_query, {"player_id": PLAYER_CHARACTER_ID, "item_name": item_name})

        logger.info(f"Item {item_name} removed from {location_name} and added to player inventory")
        return True

    def create_item(self, name: str, description: str, location_name: Optional[str] = None) -> bool:
        """
        Create a new item.

        Args:
            name: Name of the item
            description: Description of the item
            location_name: Name of the location to place the item (optional)

        Returns:
            True if successful, False otherwise
        """
        # Create the item
        query = """
        CREATE (i:Item {name: $name, description: $description})
        """

        self.query(query, {"name": name, "description": description})

        # If a location is specified, place the item there
        if location_name:
            place_query = """
            MATCH (i:Item {name: $name}), (l:Location {name: $location_name})
            CREATE (l)-[:CONTAINS]->(i)
            """

            self.query(place_query, {"name": name, "location_name": location_name})

        return True

    def create_character(self, name: str, description: str, location_name: Optional[str] = None) -> bool:
        """
        Create a new character.

        Args:
            name: Name of the character
            description: Description of the character
            location_name: Name of the location to place the character (optional)

        Returns:
            True if successful, False otherwise
        """
        # Generate a unique ID
        character_id = f"char_{name.lower().replace(' ', '_')}"

        # Create the character
        query = """
        CREATE (c:Character {character_id: $character_id, name: $name, description: $description})
        """

        self.query(
            query,
            {"character_id": character_id, "name": name, "description": description}
        )

        # If a location is specified, place the character there
        if location_name:
            place_query = """
            MATCH (c:Character {character_id: $character_id}), (l:Location {name: $location_name})
            CREATE (l)-[:CONTAINS]->(c)
            """

            self.query(place_query, {"character_id": character_id, "location_name": location_name})

        return True

    def populate_initial_graph(self) -> None:
        """Populate the graph with initial data for testing."""
        logger.info("Populating initial graph data...")

        # Create locations
        locations = [
            {
                "name": "Forest Clearing",
                "description": "A peaceful clearing in the forest. Sunlight filters through the canopy above."
            },
            {
                "name": "Forest Edge",
                "description": "The edge of a mysterious forest. Tall trees loom ahead, while a meadow stretches behind you."
            },
            {
                "name": "River Bank",
                "description": "A serene river bank. The water flows gently, and fish can be seen swimming beneath the surface."
            },
            {
                "name": "Cave Entrance",
                "description": "A dark cave entrance. Stalactites hang from the ceiling, and the air feels cool and damp."
            }
        ]

        for location in locations:
            query = """
            CREATE (l:Location {name: $name, description: $description})
            """
            self.query(query, location)

        # Create exits between locations
        exits = [
            {
                "from": "Forest Clearing",
                "to": "Forest Edge",
                "direction": "north",
                "description": "A path leading deeper into the forest."
            },
            {
                "from": "Forest Edge",
                "to": "Forest Clearing",
                "direction": "south",
                "description": "A path leading back to the clearing."
            },
            {
                "from": "Forest Clearing",
                "to": "River Bank",
                "direction": "east",
                "description": "A narrow trail leading to a river."
            },
            {
                "from": "River Bank",
                "to": "Forest Clearing",
                "direction": "west",
                "description": "A trail leading back to the forest clearing."
            },
            {
                "from": "River Bank",
                "to": "Cave Entrance",
                "direction": "north",
                "description": "A rocky path leading to a cave."
            },
            {
                "from": "Cave Entrance",
                "to": "River Bank",
                "direction": "south",
                "description": "A path leading back to the river bank."
            }
        ]

        for exit in exits:
            query = """
            MATCH (from:Location {name: $from}), (to:Location {name: $to})
            CREATE (from)-[:EXITS_TO {direction: $direction, description: $description}]->(to)
            """
            self.query(query, exit)

        # Create items
        items = [
            {
                "name": "Old Map",
                "description": "A weathered map showing the forest and surrounding areas.",
                "location": "Forest Clearing"
            },
            {
                "name": "Glowing Berries",
                "description": "Small berries that emit a soft blue glow. They look edible.",
                "location": "Forest Edge"
            },
            {
                "name": "Fishing Rod",
                "description": "A simple fishing rod. Perfect for catching fish in the river.",
                "location": "River Bank"
            },
            {
                "name": "Torch",
                "description": "An unlit torch. It could be useful in dark places.",
                "location": "Cave Entrance"
            }
        ]

        for item in items:
            query = """
            MATCH (l:Location {name: $location})
            CREATE (i:Item {name: $name, description: $description})
            CREATE (l)-[:CONTAINS]->(i)
            """
            self.query(query, item)

        # Create characters
        characters = [
            {
                "id": "char_guardian",
                "name": "Forest Guardian",
                "description": "A mysterious figure who protects the forest.",
                "location": "Forest Edge"
            },
            {
                "id": "char_fisherman",
                "name": "Old Fisherman",
                "description": "An elderly man who spends his days fishing by the river.",
                "location": "River Bank"
            },
            {
                "id": PLAYER_CHARACTER_ID,
                "name": "Player",
                "description": "You, the player character.",
                "location": "Forest Clearing"
            }
        ]

        for character in characters:
            query = """
            MATCH (l:Location {name: $location})
            CREATE (c:Character {character_id: $id, name: $name, description: $description})
            CREATE (l)-[:CONTAINS]->(c)
            """
            self.query(query, character)

            # For the player, also create a LOCATED_AT relationship
            if character["id"] == PLAYER_CHARACTER_ID:
                query = """
                MATCH (c:Character {character_id: $id}), (l:Location {name: $location})
                CREATE (c)-[:LOCATED_AT]->(l)
                """
                self.query(query, {"id": character["id"], "location": character["location"]})

        # Give the player an initial inventory item
        query = """
        MATCH (c:Character {character_id: $player_id})
        CREATE (i:Item {name: 'Rusty Key', description: 'An old iron key with intricate patterns.'})
        CREATE (c)-[:HAS_ITEM]->(i)
        """
        self.query(query, {"player_id": PLAYER_CHARACTER_ID})

        logger.info("Initial graph data populated successfully.")


# Singleton instance
_NEO4J_MANAGER = None

def get_neo4j_manager() -> Neo4jManager:
    """
    Get the singleton instance of the Neo4jManager.

    Returns:
        Neo4jManager instance
    """
    global _NEO4J_MANAGER
    if _NEO4J_MANAGER is None:
        _NEO4J_MANAGER = Neo4jManager()
    return _NEO4J_MANAGER
