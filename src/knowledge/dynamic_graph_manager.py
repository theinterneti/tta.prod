"""
Dynamic Graph Manager for the TTA Project.

This module provides a manager for dynamically updating the Neo4j knowledge graph
based on extracted objects from text.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Set, Tuple
import json

from .neo4j_manager import Neo4jManager, get_neo4j_manager
from .object_extractor import ObjectExtractor, get_object_extractor
from .schema_mapper import SchemaMapper, get_schema_mapper
from src.models.llm_client import LLMClient, get_llm_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicGraphManager:
    """
    Manager for dynamically updating the Neo4j knowledge graph.
    
    This class provides methods for extracting objects from text and
    updating the Neo4j knowledge graph accordingly.
    """
    
    def __init__(
        self,
        neo4j_manager: Optional[Neo4jManager] = None,
        object_extractor: Optional[ObjectExtractor] = None,
        schema_mapper: Optional[SchemaMapper] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize the dynamic graph manager.
        
        Args:
            neo4j_manager: Neo4j manager (optional)
            object_extractor: Object extractor (optional)
            schema_mapper: Schema mapper (optional)
            llm_client: LLM client (optional)
        """
        self.neo4j_manager = neo4j_manager or get_neo4j_manager()
        self.object_extractor = object_extractor or get_object_extractor()
        self.schema_mapper = schema_mapper or get_schema_mapper()
        self.llm_client = llm_client or get_llm_client()
        
        # Cache of extracted entities
        self._entity_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache of extracted relationships
        self._relationship_cache: List[Dict[str, Any]] = []
    
    async def process_text(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        update_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Process text to extract entities and relationships and update the graph.
        
        Args:
            text: Text to process
            entity_types: Types of entities to extract (optional, defaults to all registered types)
            relationship_types: Types of relationships to extract (optional, defaults to all registered types)
            update_graph: Whether to update the graph (default: True)
            
        Returns:
            Dictionary with extracted entities and relationships
        """
        # Clear caches
        self._entity_cache = {}
        self._relationship_cache = []
        
        # Get entity types to extract
        if entity_types is None:
            # Use all registered entity types
            entity_types = list(self.schema_mapper._entity_mappers.keys())
        
        # Extract entities
        entities_by_type = {}
        for entity_type in entity_types:
            try:
                # Get the schema for this entity type
                schema = self._get_entity_schema(entity_type)
                
                # Extract entities
                entities = await self.object_extractor.extract_objects(
                    text=text,
                    object_type=entity_type,
                    schema=schema
                )
                
                # Map entities to Neo4j nodes
                nodes = []
                for entity in entities:
                    try:
                        node = self.schema_mapper.map_to_node(entity_type, entity)
                        nodes.append(node)
                        
                        # Add to cache
                        self._entity_cache[node["id"]] = {
                            "type": entity_type,
                            "node": node,
                            "original": entity
                        }
                    except Exception as e:
                        logger.error(f"Error mapping entity to node: {e}")
                
                entities_by_type[entity_type] = nodes
                logger.info(f"Extracted {len(nodes)} {entity_type} entities")
            except Exception as e:
                logger.error(f"Error extracting {entity_type} entities: {e}")
                entities_by_type[entity_type] = []
        
        # Get relationship types to extract
        if relationship_types is None:
            # Use all registered relationship types
            relationship_types = list(self.schema_mapper._relationship_mappers.keys())
        
        # Extract relationships
        relationships_by_type = {}
        for relationship_type in relationship_types:
            try:
                # Get the mapper for this relationship type
                if relationship_type not in self.schema_mapper._relationship_mappers:
                    logger.warning(f"Relationship type {relationship_type} not registered")
                    continue
                
                mapper = self.schema_mapper._relationship_mappers[relationship_type]
                source_type = mapper["source_type"]
                target_type = mapper["target_type"]
                
                # Check if we have entities of the source and target types
                if source_type not in entities_by_type or not entities_by_type[source_type]:
                    logger.warning(f"No entities of source type {source_type} for relationship {relationship_type}")
                    relationships_by_type[relationship_type] = []
                    continue
                
                if target_type not in entities_by_type or not entities_by_type[target_type]:
                    logger.warning(f"No entities of target type {target_type} for relationship {relationship_type}")
                    relationships_by_type[relationship_type] = []
                    continue
                
                # Get the source and target entities
                source_entities = [e["original"] for e in [self._entity_cache[n["id"]] for n in entities_by_type[source_type]]]
                target_entities = [e["original"] for e in [self._entity_cache[n["id"]] for n in entities_by_type[target_type]]]
                
                # Extract relationships
                relationship_schema = self._get_relationship_schema(relationship_type)
                relationships = await self.object_extractor.extract_relationships(
                    text=text,
                    source_objects=source_entities,
                    target_objects=target_entities,
                    relationship_type=relationship_type,
                    relationship_schema=relationship_schema
                )
                
                # Map relationships to Neo4j relationships
                rel_objects = []
                for rel in relationships:
                    try:
                        # Get source and target IDs
                        source_id = rel.get("source_id")
                        target_id = rel.get("target_id")
                        properties = rel.get("properties", {})
                        
                        if not source_id or not target_id:
                            logger.warning(f"Relationship missing source_id or target_id: {rel}")
                            continue
                        
                        # Map to Neo4j relationship
                        rel_object = self.schema_mapper.map_to_relationship(
                            relationship_type=relationship_type,
                            source_id=source_id,
                            target_id=target_id,
                            properties=properties
                        )
                        
                        rel_objects.append(rel_object)
                        
                        # Add to cache
                        self._relationship_cache.append({
                            "type": relationship_type,
                            "relationship": rel_object,
                            "original": rel
                        })
                    except Exception as e:
                        logger.error(f"Error mapping relationship: {e}")
                
                relationships_by_type[relationship_type] = rel_objects
                logger.info(f"Extracted {len(rel_objects)} {relationship_type} relationships")
            except Exception as e:
                logger.error(f"Error extracting {relationship_type} relationships: {e}")
                relationships_by_type[relationship_type] = []
        
        # Update the graph if requested
        if update_graph:
            await self.update_graph(entities_by_type, relationships_by_type)
        
        return {
            "entities": entities_by_type,
            "relationships": relationships_by_type
        }
    
    async def update_graph(
        self,
        entities_by_type: Dict[str, List[Dict[str, Any]]],
        relationships_by_type: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """
        Update the Neo4j graph with extracted entities and relationships.
        
        Args:
            entities_by_type: Entities by type
            relationships_by_type: Relationships by type
        """
        # Create entities
        for entity_type, entities in entities_by_type.items():
            for entity in entities:
                try:
                    # Create the entity in Neo4j
                    await self._create_entity(entity_type, entity)
                except Exception as e:
                    logger.error(f"Error creating entity: {e}")
        
        # Create relationships
        for relationship_type, relationships in relationships_by_type.items():
            for relationship in relationships:
                try:
                    # Create the relationship in Neo4j
                    await self._create_relationship(relationship_type, relationship)
                except Exception as e:
                    logger.error(f"Error creating relationship: {e}")
    
    async def _create_entity(self, entity_type: str, entity: Dict[str, Any]) -> None:
        """
        Create an entity in Neo4j.
        
        Args:
            entity_type: Type of entity
            entity: Entity to create
        """
        label = entity["label"]
        properties = entity["properties"]
        
        # Create the entity
        query = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += $properties
        RETURN n
        """
        
        params = {
            "id": properties["id"],
            "properties": properties
        }
        
        try:
            self.neo4j_manager.query(query, params)
            logger.info(f"Created {label} entity with ID {properties['id']}")
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            raise
    
    async def _create_relationship(self, relationship_type: str, relationship: Dict[str, Any]) -> None:
        """
        Create a relationship in Neo4j.
        
        Args:
            relationship_type: Type of relationship
            relationship: Relationship to create
        """
        label = relationship["label"]
        source_id = relationship["source_id"]
        target_id = relationship["target_id"]
        properties = relationship["properties"]
        
        # Get the source and target entity types
        mapper = self.schema_mapper._relationship_mappers[relationship_type]
        source_type = mapper["source_type"]
        target_type = mapper["target_type"]
        
        # Get the Neo4j labels
        source_label = self.schema_mapper.get_entity_label(source_type)
        target_label = self.schema_mapper.get_entity_label(target_type)
        
        # Create the relationship
        query = f"""
        MATCH (source:{source_label} {{id: $source_id}}), (target:{target_label} {{id: $target_id}})
        MERGE (source)-[r:{label}]->(target)
        SET r += $properties
        RETURN r
        """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            "properties": properties
        }
        
        try:
            self.neo4j_manager.query(query, params)
            logger.info(f"Created {label} relationship from {source_id} to {target_id}")
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise
    
    def _get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """
        Get the JSON schema for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            JSON schema
        """
        if entity_type == "Location":
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {"type": "string"},
                    "atmosphere": {"type": "string"},
                    "therapeutic_purpose": {"type": "string"}
                },
                "required": ["name", "description"]
            }
        elif entity_type == "Character":
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {"type": "string"},
                    "traits": {"type": "array", "items": {"type": "string"}},
                    "backstory": {"type": "string"},
                    "therapeutic_role": {"type": "string"}
                },
                "required": ["name", "description"]
            }
        elif entity_type == "Item":
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "type": {"type": "string"},
                    "properties": {"type": "object"},
                    "therapeutic_purpose": {"type": "string"}
                },
                "required": ["name", "description"]
            }
        elif entity_type == "Memory":
            return {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "type": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 10},
                    "emotional_valence": {"type": "string"}
                },
                "required": ["content"]
            }
        elif entity_type == "Quest":
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "objective": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "completed", "failed"]},
                    "therapeutic_goal": {"type": "string"}
                },
                "required": ["name", "description", "objective"]
            }
        else:
            # Default schema
            return {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name"]
            }
    
    def _get_relationship_schema(self, relationship_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the JSON schema for a relationship type.
        
        Args:
            relationship_type: Type of relationship
            
        Returns:
            JSON schema or None
        """
        if relationship_type == "EXITS_TO":
            return {
                "type": "object",
                "properties": {
                    "direction": {"type": "string"},
                    "description": {"type": "string"},
                    "accessible": {"type": "boolean"}
                }
            }
        elif relationship_type == "HAS_ITEM":
            return {
                "type": "object",
                "properties": {
                    "equipped": {"type": "boolean"},
                    "quantity": {"type": "integer", "minimum": 1}
                }
            }
        elif relationship_type == "KNOWS":
            return {
                "type": "object",
                "properties": {
                    "relationship_type": {"type": "string"},
                    "trust_level": {"type": "integer", "minimum": 1, "maximum": 10},
                    "interaction_count": {"type": "integer", "minimum": 0}
                }
            }
        elif relationship_type == "HAS_MEMORY":
            return {
                "type": "object",
                "properties": {
                    "clarity": {"type": "integer", "minimum": 1, "maximum": 10},
                    "last_recalled": {"type": "string", "format": "date-time"}
                }
            }
        elif relationship_type == "ASSIGNED_TO":
            return {
                "type": "object",
                "properties": {
                    "date_assigned": {"type": "string", "format": "date-time"},
                    "progress": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                }
            }
        else:
            # No specific schema for this relationship type
            return None
    
    async def generate_graph_from_text(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a knowledge graph from text.
        
        Args:
            text: Text to process
            entity_types: Types of entities to extract (optional)
            relationship_types: Types of relationships to extract (optional)
            
        Returns:
            Dictionary with extracted entities and relationships
        """
        return await self.process_text(
            text=text,
            entity_types=entity_types,
            relationship_types=relationship_types,
            update_graph=True
        )
    
    async def analyze_text_for_graph_updates(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to determine what graph updates should be made.
        
        This method uses the LLM to analyze the text and determine what
        entities and relationships should be extracted.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # Create the system prompt
        system_prompt = """
        You are an expert at analyzing text to identify entities and relationships
        that should be added to a knowledge graph.
        
        Your task is to analyze the provided text and identify:
        1. What entity types should be extracted (e.g., Location, Character, Item)
        2. What relationship types should be extracted (e.g., EXITS_TO, CONTAINS, HAS_ITEM)
        
        Return your analysis as a JSON object with the following structure:
        {
            "entity_types": [
                {
                    "type": "entity_type",
                    "reason": "reason for extracting this entity type"
                }
            ],
            "relationship_types": [
                {
                    "type": "relationship_type",
                    "reason": "reason for extracting this relationship type"
                }
            ]
        }
        """
        
        # Create the user prompt
        user_prompt = f"""
        Please analyze the following text to identify what entity types and relationship types
        should be extracted for a knowledge graph:
        
        {text}
        
        Return only the JSON object with your analysis.
        """
        
        # Generate the analysis
        try:
            response = await self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Low temperature for more deterministic analysis
                expect_json=True
            )
            
            # Extract JSON from the response
            json_str = self._extract_json(response)
            
            # Parse the JSON
            try:
                analysis = json.loads(json_str)
                
                # Extract entity types and relationship types
                entity_types = [item["type"] for item in analysis.get("entity_types", [])]
                relationship_types = [item["type"] for item in analysis.get("relationship_types", [])]
                
                # Process the text with the identified types
                result = await self.process_text(
                    text=text,
                    entity_types=entity_types,
                    relationship_types=relationship_types,
                    update_graph=True
                )
                
                # Add the analysis to the result
                result["analysis"] = analysis
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                logger.error(f"JSON string: {json_str}")
                return {"error": "Error parsing analysis"}
                
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {"error": str(e)}
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain other content.
        
        Args:
            text: Text that might contain JSON
            
        Returns:
            json_str: Extracted JSON string
        """
        # Use the same method as in ObjectExtractor
        import re
        
        # Remove markdown code blocks if present
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()
        
        # Look for JSON object between curly braces
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # If no JSON object found, return the original text
        return text


# Singleton instance
_DYNAMIC_GRAPH_MANAGER = None

def get_dynamic_graph_manager() -> DynamicGraphManager:
    """
    Get the singleton instance of the DynamicGraphManager.
    
    Returns:
        DynamicGraphManager instance
    """
    global _DYNAMIC_GRAPH_MANAGER
    if _DYNAMIC_GRAPH_MANAGER is None:
        _DYNAMIC_GRAPH_MANAGER = DynamicGraphManager()
    return _DYNAMIC_GRAPH_MANAGER
