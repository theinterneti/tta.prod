"""
Object Extractor for the TTA Project.

This module provides utilities for extracting structured objects from text using LLMs.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, TypeVar, Type
import re
from pydantic import BaseModel, Field, create_model

from src.models.llm_client import LLMClient, get_llm_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic object types
T = TypeVar('T', bound=BaseModel)


class ObjectExtractor:
    """
    Extracts structured objects from text using LLMs.

    This class provides methods for extracting structured objects from text,
    which can then be used to populate the knowledge graph.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the object extractor.

        Args:
            llm_client: LLM client to use for extraction (optional)
        """
        self.llm_client = llm_client or get_llm_client()

    def extract_objects(
        self,
        text: str,
        object_type: str,
        schema: Dict[str, Any],
        max_objects: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Extract objects of a specific type from text.

        Args:
            text: Text to extract objects from
            object_type: Type of object to extract (e.g., "Location", "Character", "Item")
            schema: JSON schema for the object type
            max_objects: Maximum number of objects to extract

        Returns:
            List of extracted objects
        """
        # Create the system prompt
        system_prompt = f"""
        You are an expert at extracting structured information from text.
        Your task is to identify and extract {object_type} objects from the provided text.

        Each {object_type} should be extracted according to this schema:
        {json.dumps(schema, indent=2)}

        Extract up to {max_objects} {object_type} objects from the text.
        Return the results as a JSON array of objects.
        If no objects of this type are found, return an empty array.
        """

        # Create the user prompt
        user_prompt = f"""
        Please extract {object_type} objects from the following text:

        {text}

        Return only the JSON array with the extracted objects.
        """

        # Generate the extraction
        try:
            response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Low temperature for more deterministic extraction
                expect_json=True
            )

            # Extract JSON from the response
            json_str = self._extract_json(response)

            # Parse the JSON
            try:
                objects = json.loads(json_str)

                # Ensure it's a list
                if not isinstance(objects, list):
                    if isinstance(objects, dict):
                        # Single object returned
                        objects = [objects]
                    else:
                        # Invalid format
                        logger.warning(f"Invalid format returned: {objects}")
                        objects = []

                return objects
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                logger.error(f"JSON string: {json_str}")
                return []

        except Exception as e:
            logger.error(f"Error extracting objects: {e}")
            return []

    def extract_typed_objects(
        self,
        text: str,
        model_class: Type[T],
        max_objects: int = 10
    ) -> List[T]:
        """
        Extract objects of a specific Pydantic model type from text.

        Args:
            text: Text to extract objects from
            model_class: Pydantic model class to extract
            max_objects: Maximum number of objects to extract

        Returns:
            List of extracted objects as Pydantic models
        """
        # Convert Pydantic model to JSON schema
        schema = model_class.model_json_schema()

        # Extract objects
        objects = self.extract_objects(
            text=text,
            object_type=model_class.__name__,
            schema=schema,
            max_objects=max_objects
        )

        # Convert to Pydantic models
        result = []
        for obj in objects:
            try:
                model_instance = model_class.model_validate(obj)
                result.append(model_instance)
            except Exception as e:
                logger.error(f"Error creating model instance: {e}")

        return result

    def extract_relationships(
        self,
        text: str,
        source_objects: List[Dict[str, Any]],
        target_objects: List[Dict[str, Any]],
        relationship_type: str,
        relationship_schema: Optional[Dict[str, Any]] = None,
        max_relationships: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between objects from text.

        Args:
            text: Text to extract relationships from
            source_objects: Source objects for relationships
            target_objects: Target objects for relationships
            relationship_type: Type of relationship to extract
            relationship_schema: JSON schema for relationship properties (optional)
            max_relationships: Maximum number of relationships to extract

        Returns:
            List of extracted relationships
        """
        # Create the system prompt
        system_prompt = f"""
        You are an expert at extracting relationships between entities from text.
        Your task is to identify and extract {relationship_type} relationships from the provided text.

        Source objects:
        {json.dumps(source_objects, indent=2)}

        Target objects:
        {json.dumps(target_objects, indent=2)}

        Each relationship should connect a source object to a target object.
        """

        if relationship_schema:
            system_prompt += f"""
            Each relationship should have these properties:
            {json.dumps(relationship_schema, indent=2)}
            """

        system_prompt += f"""
        Extract up to {max_relationships} {relationship_type} relationships from the text.
        Return the results as a JSON array of objects with "source_id", "target_id", and "properties" fields.
        If no relationships of this type are found, return an empty array.
        """

        # Create the user prompt
        user_prompt = f"""
        Please extract {relationship_type} relationships from the following text:

        {text}

        Return only the JSON array with the extracted relationships.
        """

        # Generate the extraction
        try:
            response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Low temperature for more deterministic extraction
                expect_json=True
            )

            # Extract JSON from the response
            json_str = self._extract_json(response)

            # Parse the JSON
            try:
                relationships = json.loads(json_str)

                # Ensure it's a list
                if not isinstance(relationships, list):
                    if isinstance(relationships, dict):
                        # Single relationship returned
                        relationships = [relationships]
                    else:
                        # Invalid format
                        logger.warning(f"Invalid format returned: {relationships}")
                        relationships = []

                return relationships
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                logger.error(f"JSON string: {json_str}")
                return []

        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that might contain other content.

        Args:
            text: Text that might contain JSON

        Returns:
            json_str: Extracted JSON string
        """
        # Remove markdown code blocks if present
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()

        # Look for JSON array between square brackets
        json_array_match = re.search(r"(\[.*\])", text, re.DOTALL)
        if json_array_match:
            return json_array_match.group(1)

        # Look for JSON object between curly braces
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # If no JSON object found, return the original text
        return text


# Singleton instance
_OBJECT_EXTRACTOR = None

def get_object_extractor() -> ObjectExtractor:
    """
    Get the singleton instance of the ObjectExtractor.

    Returns:
        ObjectExtractor instance
    """
    global _OBJECT_EXTRACTOR
    if _OBJECT_EXTRACTOR is None:
        _OBJECT_EXTRACTOR = ObjectExtractor()
    return _OBJECT_EXTRACTOR
