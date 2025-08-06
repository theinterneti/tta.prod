"""
Dynamic Agents for TTA.

This module implements specialized agents for dynamic content generation:
- World Building Agent (WBA): Generates and modifies worlds/locations
- Character Creation Agent (CCA): Generates and modifies characters
- Lore Keeper Agent (LKA): Validates content against the knowledge graph
- Narrative Management Agent (NMA): Manages Nexus connections
"""

from typing import Dict, List, Any, Optional, Callable, Tuple, Union
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Base Dynamic Agent ---

class DynamicAgent:
    """Base class for dynamic agents."""
    
    def __init__(
        self,
        name: str,
        description: str,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        system_prompt: str = None,
        tools_llm_model: str = None,
        narrative_llm_model: str = None,
        api_base: str = None
    ):
        """
        Initialize the dynamic agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent
            neo4j_manager: Neo4j manager for knowledge graph operations
            tools: Dictionary of tools available to the agent
            system_prompt: System prompt for the agent
            tools_llm_model: Model to use for tools (planning, reasoning)
            narrative_llm_model: Model to use for narrative generation
            api_base: Base URL for the LLM API
        """
        self.name = name
        self.description = description
        self.neo4j_manager = neo4j_manager
        self.tools = tools or {}
        self.system_prompt = system_prompt or f"You are {name}, {description}."
        self.tools_llm_model = tools_llm_model
        self.narrative_llm_model = narrative_llm_model
        self.api_base = api_base
        
        logger.info(f"Initialized {name} agent")
    
    def process(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a goal using the agent.
        
        Args:
            goal: The objective to achieve
            context: Additional context information
            
        Returns:
            The result of processing the goal
        """
        # Add agent-specific context
        agent_context = {
            "agent_name": self.name,
            "agent_description": self.description,
            "agent_system_prompt": self.system_prompt,
            **context
        }
        
        # This is a placeholder method that should be overridden by subclasses
        # or implemented when the AgenticRAG is available
        logger.warning(f"Process method not fully implemented for {self.name}")
        
        return {
            "goal": goal,
            "context": agent_context,
            "result": "Not implemented yet",
            "status": "pending"
        }


# --- World Building Agent (WBA) ---

class WorldBuildingAgent(DynamicAgent):
    """
    World Building Agent (WBA).
    
    Generates and modifies worlds/locations dynamically.
    """
    
    def __init__(
        self,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        tools_llm_model: str = None,
        narrative_llm_model: str = None,
        api_base: str = None
    ):
        """Initialize the World Building Agent."""
        
        # Define the system prompt
        system_prompt = """You are the World Building Agent (WBA) for a text adventure game.
Your job is to create and modify worlds, locations, and environments.

You excel at:
1. Generating rich, detailed location descriptions
2. Creating consistent and immersive environments
3. Designing locations that support meaningful player interactions
4. Ensuring locations fit within the broader universe and its rules
5. Dynamically modifying locations based on player actions and game events

When creating or modifying locations, consider:
- The physical characteristics (geography, architecture, atmosphere)
- The sensory details (sights, sounds, smells, textures)
- The cultural and historical context
- The potential for exploration and interaction
- The emotional tone and narrative significance

Always maintain consistency with existing lore and ensure locations serve both gameplay and narrative purposes."""
        
        super().__init__(
            name="World Building Agent",
            description="Generates and modifies worlds/locations dynamically",
            neo4j_manager=neo4j_manager,
            tools=tools,
            system_prompt=system_prompt,
            tools_llm_model=tools_llm_model,
            narrative_llm_model=narrative_llm_model,
            api_base=api_base
        )
    
    def generate_location(
        self, 
        location_name: str, 
        universe_context: Dict[str, Any],
        nearby_locations: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new location.
        
        Args:
            location_name: Name of the location to generate
            universe_context: Context about the universe/world
            nearby_locations: Information about nearby locations
            
        Returns:
            The generated location
        """
        # Create the goal
        goal = f"Generate a detailed description for the location '{location_name}'"
        
        # Create the context
        context = {
            "location_name": location_name,
            "universe_context": universe_context,
            "nearby_locations": nearby_locations or []
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def modify_location(
        self,
        location_id: str,
        modification_reason: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Modify an existing location.
        
        Args:
            location_id: ID of the location to modify
            modification_reason: Reason for the modification
            current_state: Current state of the location
            
        Returns:
            The modified location
        """
        # Create the goal
        goal = f"Modify the location '{location_id}' because: {modification_reason}"
        
        # Create the context
        context = {
            "location_id": location_id,
            "modification_reason": modification_reason,
            "current_state": current_state
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result


# --- Character Creation Agent (CCA) ---

class CharacterCreationAgent(DynamicAgent):
    """
    Character Creation Agent (CCA).
    
    Generates and modifies characters dynamically.
    """
    
    def __init__(
        self,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        tools_llm_model: str = None,
        narrative_llm_model: str = None,
        api_base: str = None
    ):
        """Initialize the Character Creation Agent."""
        
        # Define the system prompt
        system_prompt = """You are the Character Creation Agent (CCA) for a text adventure game.
Your job is to create and modify characters with depth, personality, and purpose.

You excel at:
1. Generating complex, believable characters with distinct personalities
2. Creating backstories that fit within the game world
3. Designing characters that serve narrative and gameplay purposes
4. Ensuring characters have realistic motivations and behaviors
5. Dynamically modifying characters based on player interactions and game events

When creating or modifying characters, consider:
- Their physical appearance and distinguishing features
- Their personality traits, values, and beliefs
- Their background, history, and formative experiences
- Their goals, motivations, and conflicts
- Their relationships with other characters and the player
- Their role in the narrative and gameplay

Always maintain consistency with existing lore and ensure characters feel authentic within their world."""
        
        super().__init__(
            name="Character Creation Agent",
            description="Generates and modifies characters dynamically",
            neo4j_manager=neo4j_manager,
            tools=tools,
            system_prompt=system_prompt,
            tools_llm_model=tools_llm_model,
            narrative_llm_model=narrative_llm_model,
            api_base=api_base
        )
    
    def generate_character(
        self, 
        character_name: str, 
        location_context: Dict[str, Any],
        narrative_purpose: str = None
    ) -> Dict[str, Any]:
        """
        Generate a new character.
        
        Args:
            character_name: Name of the character to generate
            location_context: Context about the location
            narrative_purpose: Purpose of the character in the narrative
            
        Returns:
            The generated character
        """
        # Create the goal
        goal = f"Generate a detailed profile for the character '{character_name}'"
        
        # Create the context
        context = {
            "character_name": character_name,
            "location_context": location_context,
            "narrative_purpose": narrative_purpose or "To provide an interesting interaction for the player"
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def modify_character(
        self,
        character_id: str,
        modification_reason: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Modify an existing character.
        
        Args:
            character_id: ID of the character to modify
            modification_reason: Reason for the modification
            current_state: Current state of the character
            
        Returns:
            The modified character
        """
        # Create the goal
        goal = f"Modify the character '{character_id}' because: {modification_reason}"
        
        # Create the context
        context = {
            "character_id": character_id,
            "modification_reason": modification_reason,
            "current_state": current_state
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def generate_dialogue(
        self,
        character_id: str,
        player_input: str,
        conversation_history: List[Dict[str, str]],
        character_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate dialogue for a character.
        
        Args:
            character_id: ID of the character
            player_input: Input from the player
            conversation_history: History of the conversation
            character_state: Current state of the character
            
        Returns:
            The generated dialogue
        """
        # Create the goal
        goal = f"Generate dialogue for character '{character_id}' in response to: {player_input}"
        
        # Create the context
        context = {
            "character_id": character_id,
            "player_input": player_input,
            "conversation_history": conversation_history,
            "character_state": character_state
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result


# --- Lore Keeper Agent (LKA) ---

class LoreKeeperAgent(DynamicAgent):
    """
    Lore Keeper Agent (LKA).
    
    Validates content against the knowledge graph and ensures consistency.
    """
    
    def __init__(
        self,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        tools_llm_model: str = None,
        narrative_llm_model: str = None,
        api_base: str = None
    ):
        """Initialize the Lore Keeper Agent."""
        
        # Define the system prompt
        system_prompt = """You are the Lore Keeper Agent (LKA) for a text adventure game.
Your job is to maintain the consistency and integrity of the game world.

You excel at:
1. Validating new content against existing lore
2. Identifying inconsistencies and contradictions
3. Suggesting corrections to maintain world coherence
4. Recognizing opportunities to expand the lore
5. Ensuring all content adheres to the established rules of the universe

When validating content, consider:
- Consistency with established facts and history
- Alignment with the physical laws and magic systems of the universe
- Coherence with cultural norms and societal structures
- Logical relationships between entities
- Potential implications for other aspects of the world

Always prioritize maintaining a coherent, believable world that supports immersive gameplay."""
        
        super().__init__(
            name="Lore Keeper Agent",
            description="Validates content against the knowledge graph and ensures consistency",
            neo4j_manager=neo4j_manager,
            tools=tools,
            system_prompt=system_prompt,
            tools_llm_model=tools_llm_model,
            narrative_llm_model=narrative_llm_model,
            api_base=api_base
        )
    
    def validate_content(
        self, 
        content: str, 
        content_type: str,
        related_entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate content against existing lore.
        
        Args:
            content: The content to validate
            content_type: Type of content (location, character, item, etc.)
            related_entities: Entities related to the content
            
        Returns:
            Validation results
        """
        # Create the goal
        goal = f"Validate {content_type} content for consistency with existing lore"
        
        # Create the context
        context = {
            "content": content,
            "content_type": content_type,
            "related_entities": related_entities
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def identify_new_concepts(
        self,
        content: str,
        existing_concepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify new concepts in content that should be added to the knowledge graph.
        
        Args:
            content: The content to analyze
            existing_concepts: Existing concepts in the knowledge graph
            
        Returns:
            Identified new concepts
        """
        # Create the goal
        goal = "Identify new concepts in content that should be added to the knowledge graph"
        
        # Create the context
        context = {
            "content": content,
            "existing_concepts": existing_concepts
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def infer_relationships(
        self,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any],
        existing_relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Infer relationships between entities.
        
        Args:
            entity1: First entity
            entity2: Second entity
            existing_relationships: Existing relationships between entities
            
        Returns:
            Inferred relationships
        """
        # Create the goal
        goal = f"Infer relationships between '{entity1.get('name', 'entity1')}' and '{entity2.get('name', 'entity2')}'"
        
        # Create the context
        context = {
            "entity1": entity1,
            "entity2": entity2,
            "existing_relationships": existing_relationships
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result


# --- Narrative Management Agent (NMA) ---

class NarrativeManagementAgent(DynamicAgent):
    """
    Narrative Management Agent (NMA).
    
    Manages Nexus connections and inter-universe narrative elements.
    """
    
    def __init__(
        self,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        tools_llm_model: str = None,
        narrative_llm_model: str = None,
        api_base: str = None
    ):
        """Initialize the Narrative Management Agent."""
        
        # Define the system prompt
        system_prompt = """You are the Narrative Management Agent (NMA) for a text adventure game.
Your job is to manage connections between different universes and maintain the Nexus.

You excel at:
1. Creating meaningful connections between different universes
2. Managing the Nexus as a central hub for inter-universe travel
3. Ensuring narrative coherence across multiple universes
4. Designing universe-specific rules and characteristics
5. Creating thematic links that support the player's journey

When managing narrative elements, consider:
- The unique characteristics of each universe
- The thematic connections between universes
- The player's journey and character development
- The balance between consistency and variety
- The potential for meaningful choices and consequences

Always ensure that the multiverse feels cohesive while still offering diverse and distinct experiences."""
        
        super().__init__(
            name="Narrative Management Agent",
            description="Manages Nexus connections and inter-universe narrative elements",
            neo4j_manager=neo4j_manager,
            tools=tools,
            system_prompt=system_prompt,
            tools_llm_model=tools_llm_model,
            narrative_llm_model=narrative_llm_model,
            api_base=api_base
        )
    
    def create_nexus_connection(
        self,
        source_location_id: str,
        target_universe_id: str,
        connection_type: str,
        narrative_purpose: str
    ) -> Dict[str, Any]:
        """
        Create a connection between a location and the Nexus.
        
        Args:
            source_location_id: ID of the source location
            target_universe_id: ID of the target universe
            connection_type: Type of connection (portal, rift, etc.)
            narrative_purpose: Purpose of the connection in the narrative
            
        Returns:
            The created connection
        """
        # Create the goal
        goal = f"Create a {connection_type} connection from location '{source_location_id}' to universe '{target_universe_id}'"
        
        # Create the context
        context = {
            "source_location_id": source_location_id,
            "target_universe_id": target_universe_id,
            "connection_type": connection_type,
            "narrative_purpose": narrative_purpose
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result
    
    def generate_universe(
        self,
        universe_name: str,
        theme: str,
        core_concepts: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a new universe.
        
        Args:
            universe_name: Name of the universe
            theme: Central theme of the universe
            core_concepts: Core concepts that define the universe
            
        Returns:
            The generated universe
        """
        # Create the goal
        goal = f"Generate a new universe named '{universe_name}' with theme: {theme}"
        
        # Create the context
        context = {
            "universe_name": universe_name,
            "theme": theme,
            "core_concepts": core_concepts
        }
        
        # Process the goal
        result = self.process(goal, context)
        
        return result


# --- Factory function to create all dynamic agents ---

def create_dynamic_agents(
    neo4j_manager=None,
    tools: Dict[str, Callable] = None
) -> Dict[str, DynamicAgent]:
    """
    Create all dynamic agents.
    
    Args:
        neo4j_manager: Neo4j manager for knowledge graph operations
        tools: Dictionary of tools available to the agents
        
    Returns:
        Dictionary of dynamic agents
    """
    return {
        "wba": WorldBuildingAgent(neo4j_manager, tools),
        "cca": CharacterCreationAgent(neo4j_manager, tools),
        "lka": LoreKeeperAgent(neo4j_manager, tools),
        "nma": NarrativeManagementAgent(neo4j_manager, tools)
    }
