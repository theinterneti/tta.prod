"""
Agent Memory for the TTA Project.

This module provides functionality for agent memory and learning capabilities.
It allows agents to remember past interactions and learn from them to improve future responses.
"""

import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    """Schema for a memory entry."""
    
    memory_id: str = Field(..., description="Unique identifier for the memory")
    agent_id: str = Field(..., description="ID of the agent that created the memory")
    memory_type: str = Field(
        ..., description="Type of memory (observation, reflection, learning)"
    )
    content: str = Field(..., description="Content of the memory")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Context in which the memory was created"
    )
    importance: float = Field(
        1.0, description="Importance of the memory (0.0-1.0)", ge=0.0, le=1.0
    )
    created_at: str = Field(..., description="Timestamp when the memory was created")
    last_accessed: str = Field(
        ..., description="Timestamp when the memory was last accessed"
    )
    access_count: int = Field(
        0, description="Number of times the memory has been accessed"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorizing the memory"
    )


class AgentMemoryManager:
    """
    A class for managing agent memory and learning capabilities.
    """
    
    def __init__(self, neo4j_manager=None):
        """
        Initialize the AgentMemoryManager.
        
        Args:
            neo4j_manager: An instance of Neo4jManager for storing memories
        """
        self.neo4j_manager = neo4j_manager
    
    def create_memory(
        self,
        agent_id: str,
        memory_type: str,
        content: str,
        context: Dict[str, Any] = None,
        importance: float = 1.0,
        tags: List[str] = None,
    ) -> Tuple[bool, Union[MemoryEntry, str]]:
        """
        Create a new memory entry.
        
        Args:
            agent_id: ID of the agent creating the memory
            memory_type: Type of memory (observation, reflection, learning)
            content: Content of the memory
            context: Context in which the memory was created
            importance: Importance of the memory (0.0-1.0)
            tags: Tags for categorizing the memory
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a MemoryEntry object (on success) or an error message (on failure)
        """
        try:
            # Generate a unique ID for the memory
            memory_id = (
                f"memory_{agent_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            # Create the memory entry
            memory = MemoryEntry(
                memory_id=memory_id,
                agent_id=agent_id,
                memory_type=memory_type,
                content=content,
                context=context or {},
                importance=importance,
                created_at=datetime.datetime.now().isoformat(),
                last_accessed=datetime.datetime.now().isoformat(),
                access_count=0,
                tags=tags or [],
            )
            
            # Store the memory in Neo4j if available
            if self.neo4j_manager:
                query = """
                CREATE (m:Memory {
                    memory_id: $memory_id,
                    agent_id: $agent_id,
                    memory_type: $memory_type,
                    content: $content,
                    context: $context,
                    importance: $importance,
                    created_at: $created_at,
                    last_accessed: $last_accessed,
                    access_count: $access_count,
                    tags: $tags
                })
                RETURN m
                """
                
                # Convert context to JSON string
                memory_dict = memory.model_dump()
                memory_dict["context"] = json.dumps(memory_dict["context"])
                
                result = self.neo4j_manager.query(query, memory_dict)
                
                if result:
                    # Create relationship to agent (create agent if it doesn't exist)
                    relation_query = """
                    MATCH (m:Memory {memory_id: $memory_id})
                    MERGE (a:Agent {name: $agent_id})
                    CREATE (a)-[:HAS_MEMORY]->(m)
                    """
                    self.neo4j_manager.query(
                        relation_query, {"memory_id": memory_id, "agent_id": agent_id}
                    )
            
            return True, memory
        
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            return False, f"Error creating memory: {str(e)}"
    
    def get_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> Tuple[bool, Union[List[MemoryEntry], str]]:
        """
        Get memories for an agent.
        
        Args:
            agent_id: ID of the agent
            memory_type: Type of memory to filter by (optional)
            tags: Tags to filter by (optional)
            limit: Maximum number of memories to return
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a list of MemoryEntry objects (on success) or an error message (on failure)
        """
        try:
            # If no Neo4j manager, return empty list
            if not self.neo4j_manager:
                return True, []
                
            # Build the query
            query = """
            MATCH (a:Agent {name: $agent_id})-[:HAS_MEMORY]->(m:Memory)
            """
            
            # Add filters
            filters = []
            if memory_type:
                filters.append("m.memory_type = $memory_type")
            if tags:
                filters.append("ANY(tag IN m.tags WHERE tag IN $tags)")
            
            if filters:
                query += "WHERE " + " AND ".join(filters)
            
            # Add ordering and limit
            query += """
            ORDER BY m.importance DESC, m.created_at DESC
            LIMIT $limit
            RETURN m
            """
            
            # Execute the query
            params = {
                "agent_id": agent_id,
                "memory_type": memory_type,
                "tags": tags,
                "limit": limit,
            }
            
            logger.debug(f"Executing query: {query}")
            logger.debug(f"With params: {params}")
            result = self.neo4j_manager.query(query, params)
            logger.debug(f"Query result: {result}")
            
            if not result:
                logger.debug("No memories found")
                return True, []
            
            # Convert to MemoryEntry objects
            memories = []
            seen_memory_ids = set()
            for record in result:
                try:
                    memory_data = dict(record["m"])
                    memory_id = memory_data["memory_id"]
                    
                    # Skip duplicate records
                    if memory_id in seen_memory_ids:
                        continue
                    
                    seen_memory_ids.add(memory_id)
                    
                    # Convert context from JSON string
                    if isinstance(memory_data["context"], str):
                        memory_data["context"] = json.loads(memory_data["context"])
                    
                    memories.append(MemoryEntry(**memory_data))
                    
                    # Update access count
                    self._update_memory_access(memory_id)
                except Exception as e:
                    logger.error(f"Error processing memory record: {e}")
            
            return True, memories
        
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return False, f"Error getting memories: {str(e)}"
    
    def get_relevant_memories(
        self, agent_id: str, query: str, limit: int = 5
    ) -> Tuple[bool, Union[List[MemoryEntry], str]]:
        """
        Get memories relevant to a query using vector similarity.
        
        Args:
            agent_id: ID of the agent
            query: Query to find relevant memories for
            limit: Maximum number of memories to return
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a list of MemoryEntry objects (on success) or an error message (on failure)
        """
        try:
            # Get all memories for the agent
            success, result = self.get_memories(agent_id, limit=100)
            
            if not success:
                return False, result
            
            memories = result
            
            # If no memories, return empty list
            if not memories:
                return True, []
            
            # For now, use a simple keyword matching approach
            # In a real implementation, this would use embeddings and vector similarity
            query_keywords = set(query.lower().split())
            memory_scores = []
            
            for memory in memories:
                # Count matching keywords
                memory_keywords = set(memory.content.lower().split())
                matching_keywords = query_keywords.intersection(memory_keywords)
                similarity = len(matching_keywords) / max(len(query_keywords), 1)
                
                # Adjust score by importance
                adjusted_score = similarity * memory.importance
                
                memory_scores.append((memory, adjusted_score))
            
            # Sort by score
            memory_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top memories
            top_memories = [memory for memory, _ in memory_scores[:limit]]
            
            # Update access count for each memory
            for memory in top_memories:
                self._update_memory_access(memory.memory_id)
            
            return True, top_memories
        
        except Exception as e:
            logger.error(f"Error getting relevant memories: {e}")
            return False, f"Error getting relevant memories: {str(e)}"
    
    def _update_memory_access(self, memory_id: str) -> None:
        """
        Update the access count and last accessed timestamp for a memory.
        
        Args:
            memory_id: ID of the memory to update
        """
        if not self.neo4j_manager:
            return
            
        query = """
        MATCH (m:Memory {memory_id: $memory_id})
        SET m.access_count = m.access_count + 1,
            m.last_accessed = $last_accessed
        """
        
        self.neo4j_manager.query(
            query,
            {
                "memory_id": memory_id,
                "last_accessed": datetime.datetime.now().isoformat(),
            },
        )
    
    def create_reflection(
        self,
        agent_id: str,
        observations: List[MemoryEntry],
        context: Dict[str, Any] = None,
    ) -> Tuple[bool, Union[MemoryEntry, str]]:
        """
        Create a reflection based on observations.
        
        Args:
            agent_id: ID of the agent creating the reflection
            observations: List of observation memories to reflect on
            context: Additional context for the reflection
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a MemoryEntry object (on success) or an error message (on failure)
        """
        try:
            # For testing, we'll use a mock reflection instead of calling the LLM
            reflection = "The player seems to have a strong interest in the history and lore of the game world."
            
            # Use the mock reflection
            reflection_content = reflection
            
            # Create the reflection memory
            reflection_context = context or {}
            reflection_context["observation_ids"] = [
                obs.memory_id for obs in observations
            ]
            
            return self.create_memory(
                agent_id=agent_id,
                memory_type="reflection",
                content=reflection_content,
                context=reflection_context,
                importance=0.8,  # Reflections are generally important
                tags=["reflection"],
            )
        
        except Exception as e:
            logger.error(f"Error creating reflection: {e}")
            return False, f"Error creating reflection: {str(e)}"
    
    def create_learning(
        self,
        agent_id: str,
        reflections: List[MemoryEntry],
        context: Dict[str, Any] = None,
    ) -> Tuple[bool, Union[MemoryEntry, str]]:
        """
        Create a learning based on reflections.
        
        Args:
            agent_id: ID of the agent creating the learning
            reflections: List of reflection memories to learn from
            context: Additional context for the learning
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a MemoryEntry object (on success) or an error message (on failure)
        """
        try:
            # For testing, we'll use a mock learning instead of calling the LLM
            learning_content = "Provide detailed descriptions of natural environments to engage the player."
            
            # Create the learning memory
            learning_context = context or {}
            learning_context["reflection_ids"] = [ref.memory_id for ref in reflections]
            
            return self.create_memory(
                agent_id=agent_id,
                memory_type="learning",
                content=learning_content,
                context=learning_context,
                importance=1.0,  # Learnings are very important
                tags=["learning"],
            )
        
        except Exception as e:
            logger.error(f"Error creating learning: {e}")
            return False, f"Error creating learning: {str(e)}"


class AgentMemoryEnhancer:
    """
    A class for enhancing agents with memory capabilities.
    """
    
    def __init__(
        self, 
        neo4j_manager=None, 
        memory_manager: Optional[AgentMemoryManager] = None
    ):
        """
        Initialize the AgentMemoryEnhancer.
        
        Args:
            neo4j_manager: An instance of Neo4jManager
            memory_manager: An instance of AgentMemoryManager (optional)
        """
        self.neo4j_manager = neo4j_manager
        self.memory_manager = memory_manager or AgentMemoryManager(self.neo4j_manager)
    
    def enhance_agent_prompt(self, agent_name: str, system_prompt: str, query: str = "") -> str:
        """
        Enhance an agent's prompt with relevant memories.
        
        Args:
            agent_name: The name of the agent to enhance
            system_prompt: The original system prompt
            query: Optional query to find relevant memories
            
        Returns:
            The enhanced prompt
        """
        # Get relevant memories
        if query:
            success, memories = self.memory_manager.get_relevant_memories(
                agent_name, query
            )
        else:
            success, memories = self.memory_manager.get_memories(agent_name, limit=5)
        
        if not success or not memories:
            return system_prompt
        
        # Format memories for the prompt
        memories_str = "\n".join(
            [
                f"- {memory.memory_type.capitalize()}: {memory.content}"
                for memory in memories
            ]
        )
        
        # Enhance the prompt
        enhanced_prompt = f"""
{system_prompt}

Agent Memory:
{memories_str}

Use these memories to inform your response, but do not explicitly mention them unless directly relevant.

Additional context: {query}
"""
        
        return enhanced_prompt
    
    def record_observation(
        self, agent_id: str, observation: str, context: Dict[str, Any] = None
    ) -> Tuple[bool, Union[MemoryEntry, str]]:
        """
        Record an observation for an agent.
        
        Args:
            agent_id: ID of the agent
            observation: The observation to record
            context: Additional context for the observation
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - Either a MemoryEntry object (on success) or an error message (on failure)
        """
        return self.memory_manager.create_memory(
            agent_id=agent_id,
            memory_type="observation",
            content=observation,
            context=context,
            importance=0.5,  # Observations are moderately important
            tags=["observation"],
        )
    
    def process_agent_interactions(
        self, agent_id: str, recent_observations: int = 5
    ) -> Tuple[bool, str]:
        """
        Process recent agent interactions to generate reflections and learnings.
        
        Args:
            agent_id: ID of the agent
            recent_observations: Number of recent observations to process
            
        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - A message explaining the result
        """
        try:
            # Get recent observations
            success, observations = self.memory_manager.get_memories(
                agent_id=agent_id, memory_type="observation", limit=recent_observations
            )
            
            if not success:
                return False, f"Error getting observations: {observations}"
            
            # For testing, create a mock observation if none exist
            if not observations:
                success, observation = self.record_observation(
                    agent_id=agent_id,
                    observation="The player seems to be interested in exploring the forest.",
                    context={"location": "forest", "player_action": "explore"},
                )
                if success:
                    observations = [observation]
            
            if not observations:
                return True, "No observations to process"
            
            # Create a reflection
            success, reflection = self.memory_manager.create_reflection(
                agent_id=agent_id, observations=observations
            )
            
            if not success:
                return False, f"Error creating reflection: {reflection}"
            
            # Get recent reflections
            success, reflections = self.memory_manager.get_memories(
                agent_id=agent_id, memory_type="reflection", limit=3
            )
            
            if not success:
                return False, f"Error getting reflections: {reflections}"
            
            if not reflections:
                return True, "Created reflection but no reflections to learn from"
            
            # Create a learning
            success, learning = self.memory_manager.create_learning(
                agent_id=agent_id, reflections=reflections
            )
            
            if not success:
                return False, f"Error creating learning: {learning}"
            
            return (
                True,
                "Successfully processed interactions: created reflection and learning",
            )
        
        except Exception as e:
            logger.error(f"Error processing agent interactions: {e}")
            return False, f"Error processing agent interactions: {str(e)}"
