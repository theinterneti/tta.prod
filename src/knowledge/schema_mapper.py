"""
Schema Mapper for the TTA Project.

This module provides utilities for mapping between object schemas and Neo4j entities.
"""

import logging
from typing import Dict, Any, List, Optional, Union, TypeVar, Type, Callable
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic object types
T = TypeVar('T', bound=BaseModel)


class SchemaMapper:
    """
    Maps between object schemas and Neo4j entities.
    
    This class provides methods for mapping between object schemas and Neo4j entities,
    which is used for converting extracted objects to Neo4j nodes and relationships.
    """
    
    def __init__(self):
        """Initialize the schema mapper."""
        # Registry of entity type mappers
        self._entity_mappers: Dict[str, Dict[str, Any]] = {}
        
        # Registry of relationship type mappers
        self._relationship_mappers: Dict[str, Dict[str, Any]] = {}
    
    def register_entity_type(
        self,
        entity_type: str,
        label: str,
        id_field: str,
        property_mapping: Dict[str, str],
        transform_functions: Optional[Dict[str, Callable]] = None
    ) -> None:
        """
        Register an entity type mapping.
        
        Args:
            entity_type: Type of entity in the object schema
            label: Neo4j node label
            id_field: Field to use as the node ID
            property_mapping: Mapping from object fields to Neo4j properties
            transform_functions: Functions to transform property values (optional)
        """
        self._entity_mappers[entity_type] = {
            "label": label,
            "id_field": id_field,
            "property_mapping": property_mapping,
            "transform_functions": transform_functions or {}
        }
        
        logger.info(f"Registered entity type mapping for {entity_type} -> {label}")
    
    def register_relationship_type(
        self,
        relationship_type: str,
        label: str,
        source_type: str,
        target_type: str,
        property_mapping: Optional[Dict[str, str]] = None,
        transform_functions: Optional[Dict[str, Callable]] = None
    ) -> None:
        """
        Register a relationship type mapping.
        
        Args:
            relationship_type: Type of relationship in the object schema
            label: Neo4j relationship type
            source_type: Type of source entity
            target_type: Type of target entity
            property_mapping: Mapping from object fields to Neo4j properties (optional)
            transform_functions: Functions to transform property values (optional)
        """
        self._relationship_mappers[relationship_type] = {
            "label": label,
            "source_type": source_type,
            "target_type": target_type,
            "property_mapping": property_mapping or {},
            "transform_functions": transform_functions or {}
        }
        
        logger.info(f"Registered relationship type mapping for {relationship_type} -> {label}")
    
    def map_to_node(self, entity_type: str, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map an object to a Neo4j node.
        
        Args:
            entity_type: Type of entity
            obj: Object to map
            
        Returns:
            Neo4j node representation
        
        Raises:
            ValueError: If entity type is not registered
        """
        if entity_type not in self._entity_mappers:
            raise ValueError(f"Entity type {entity_type} not registered")
        
        mapper = self._entity_mappers[entity_type]
        
        # Get the node ID
        node_id = obj.get(mapper["id_field"])
        if not node_id:
            logger.warning(f"Object missing ID field {mapper['id_field']}: {obj}")
            # Generate a default ID
            node_id = f"{entity_type.lower()}_{hash(str(obj))}"
        
        # Map properties
        properties = {"id": node_id}
        for obj_field, neo4j_prop in mapper["property_mapping"].items():
            if obj_field in obj:
                value = obj[obj_field]
                
                # Apply transform function if available
                if obj_field in mapper["transform_functions"]:
                    try:
                        value = mapper["transform_functions"][obj_field](value)
                    except Exception as e:
                        logger.error(f"Error transforming {obj_field}: {e}")
                
                properties[neo4j_prop] = value
        
        return {
            "label": mapper["label"],
            "id": node_id,
            "properties": properties
        }
    
    def map_to_relationship(
        self,
        relationship_type: str,
        source_id: str,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Map to a Neo4j relationship.
        
        Args:
            relationship_type: Type of relationship
            source_id: ID of source node
            target_id: ID of target node
            properties: Relationship properties (optional)
            
        Returns:
            Neo4j relationship representation
        
        Raises:
            ValueError: If relationship type is not registered
        """
        if relationship_type not in self._relationship_mappers:
            raise ValueError(f"Relationship type {relationship_type} not registered")
        
        mapper = self._relationship_mappers[relationship_type]
        
        # Map properties
        rel_properties = {}
        if properties:
            for obj_field, neo4j_prop in mapper["property_mapping"].items():
                if obj_field in properties:
                    value = properties[obj_field]
                    
                    # Apply transform function if available
                    if obj_field in mapper["transform_functions"]:
                        try:
                            value = mapper["transform_functions"][obj_field](value)
                        except Exception as e:
                            logger.error(f"Error transforming {obj_field}: {e}")
                    
                    rel_properties[neo4j_prop] = value
        
        return {
            "label": mapper["label"],
            "source_id": source_id,
            "target_id": target_id,
            "properties": rel_properties
        }
    
    def get_entity_label(self, entity_type: str) -> str:
        """
        Get the Neo4j label for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Neo4j label
        
        Raises:
            ValueError: If entity type is not registered
        """
        if entity_type not in self._entity_mappers:
            raise ValueError(f"Entity type {entity_type} not registered")
        
        return self._entity_mappers[entity_type]["label"]
    
    def get_relationship_label(self, relationship_type: str) -> str:
        """
        Get the Neo4j label for a relationship type.
        
        Args:
            relationship_type: Type of relationship
            
        Returns:
            Neo4j relationship type
        
        Raises:
            ValueError: If relationship type is not registered
        """
        if relationship_type not in self._relationship_mappers:
            raise ValueError(f"Relationship type {relationship_type} not registered")
        
        return self._relationship_mappers[relationship_type]["label"]


# Singleton instance
_SCHEMA_MAPPER = None

def get_schema_mapper() -> SchemaMapper:
    """
    Get the singleton instance of the SchemaMapper.
    
    Returns:
        SchemaMapper instance
    """
    global _SCHEMA_MAPPER
    if _SCHEMA_MAPPER is None:
        _SCHEMA_MAPPER = SchemaMapper()
        _initialize_default_mappings(_SCHEMA_MAPPER)
    return _SCHEMA_MAPPER


def _initialize_default_mappings(mapper: SchemaMapper) -> None:
    """
    Initialize default mappings for common entity and relationship types.
    
    Args:
        mapper: SchemaMapper instance to initialize
    """
    # Register Location entity type
    mapper.register_entity_type(
        entity_type="Location",
        label="Location",
        id_field="name",
        property_mapping={
            "name": "name",
            "description": "description",
            "type": "type",
            "atmosphere": "atmosphere",
            "therapeutic_purpose": "therapeutic_purpose"
        }
    )
    
    # Register Character entity type
    mapper.register_entity_type(
        entity_type="Character",
        label="Character",
        id_field="name",
        property_mapping={
            "name": "name",
            "description": "description",
            "type": "type",
            "traits": "traits",
            "backstory": "backstory",
            "therapeutic_role": "therapeutic_role"
        }
    )
    
    # Register Item entity type
    mapper.register_entity_type(
        entity_type="Item",
        label="Item",
        id_field="name",
        property_mapping={
            "name": "name",
            "description": "description",
            "type": "type",
            "properties": "properties",
            "therapeutic_purpose": "therapeutic_purpose"
        }
    )
    
    # Register Memory entity type
    mapper.register_entity_type(
        entity_type="Memory",
        label="Memory",
        id_field="content",
        property_mapping={
            "content": "content",
            "type": "type",
            "timestamp": "timestamp",
            "importance": "importance",
            "emotional_valence": "emotional_valence"
        }
    )
    
    # Register Quest entity type
    mapper.register_entity_type(
        entity_type="Quest",
        label="Quest",
        id_field="name",
        property_mapping={
            "name": "name",
            "description": "description",
            "objective": "objective",
            "status": "status",
            "therapeutic_goal": "therapeutic_goal"
        }
    )
    
    # Register EXITS_TO relationship type
    mapper.register_relationship_type(
        relationship_type="EXITS_TO",
        label="EXITS_TO",
        source_type="Location",
        target_type="Location",
        property_mapping={
            "direction": "direction",
            "description": "description",
            "accessible": "accessible"
        }
    )
    
    # Register CONTAINS relationship type
    mapper.register_relationship_type(
        relationship_type="CONTAINS",
        label="CONTAINS",
        source_type="Location",
        target_type="Item",
        property_mapping={}
    )
    
    # Register CONTAINS relationship type for characters
    mapper.register_relationship_type(
        relationship_type="CONTAINS_CHARACTER",
        label="CONTAINS",
        source_type="Location",
        target_type="Character",
        property_mapping={}
    )
    
    # Register HAS_ITEM relationship type
    mapper.register_relationship_type(
        relationship_type="HAS_ITEM",
        label="HAS_ITEM",
        source_type="Character",
        target_type="Item",
        property_mapping={
            "equipped": "equipped",
            "quantity": "quantity"
        }
    )
    
    # Register KNOWS relationship type
    mapper.register_relationship_type(
        relationship_type="KNOWS",
        label="KNOWS",
        source_type="Character",
        target_type="Character",
        property_mapping={
            "relationship_type": "relationship_type",
            "trust_level": "trust_level",
            "interaction_count": "interaction_count"
        }
    )
    
    # Register HAS_MEMORY relationship type
    mapper.register_relationship_type(
        relationship_type="HAS_MEMORY",
        label="HAS_MEMORY",
        source_type="Character",
        target_type="Memory",
        property_mapping={
            "clarity": "clarity",
            "last_recalled": "last_recalled"
        }
    )
    
    # Register ASSIGNED_TO relationship type
    mapper.register_relationship_type(
        relationship_type="ASSIGNED_TO",
        label="ASSIGNED_TO",
        source_type="Quest",
        target_type="Character",
        property_mapping={
            "date_assigned": "date_assigned",
            "progress": "progress"
        }
    )
    
    # Register LOCATED_AT relationship type
    mapper.register_relationship_type(
        relationship_type="LOCATED_AT",
        label="LOCATED_AT",
        source_type="Character",
        target_type="Location",
        property_mapping={}
    )
