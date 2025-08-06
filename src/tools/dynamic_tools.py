"""
Dynamic Tools for the TTA Project.

This module provides functionality for creating and managing dynamic tools.
"""

import logging
import json
import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple

from .base import BaseTool, ToolParameter
from ..knowledge import get_neo4j_manager, Neo4jManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicTool(BaseTool):
    """
    A dynamically created tool with a function defined at runtime.

    This class extends BaseTool to add support for dynamically created tools
    with functions defined at runtime.
    """

    def __init__(
        self,
        name: str,
        description: str,
        function_code: str,
        parameters: List[ToolParameter] = None,
        therapeutic_value: str = "",
        created_by: str = "system",
        tags: List[str] = None,
        kg_read: bool = False,
        kg_write: bool = False,
        usage_count: int = 0,
        average_rating: float = 0.0,
        created_at: str = None,
        action_fn: Optional[Callable] = None,
        tool_type: str = "dynamic"
    ):
        """
        Initialize the DynamicTool.

        Args:
            name: Name of the tool
            description: Description of what the tool does
            function_code: Python code for the tool's function
            parameters: Parameters for the tool
            therapeutic_value: How this tool contributes to therapeutic goals
            created_by: Who created the tool (system, user, or LLM)
            tags: Tags for categorizing the tool
            kg_read: Whether the tool reads from the knowledge graph
            kg_write: Whether the tool writes to the knowledge graph
            usage_count: Number of times the tool has been used
            average_rating: Average user rating of the tool (0-5)
            created_at: Timestamp when the tool was created
            action_fn: Function to call when the tool is used
            tool_type: Type of tool
        """
        super().__init__(
            name=name,
            description=description,
            parameters=parameters or [],
            action_fn=action_fn,
            kg_read=kg_read,
            kg_write=kg_write,
            tool_type=tool_type
        )

        self.function_code = function_code
        self.therapeutic_value = therapeutic_value
        self.created_by = created_by
        self.tags = tags or []
        self.usage_count = usage_count
        self.average_rating = average_rating
        self.created_at = created_at or datetime.datetime.now().isoformat()

        # Compile the function code
        self._compile_function()

    def _compile_function(self) -> None:
        """
        Compile the function code and set the action_fn.

        Raises:
            SyntaxError: If the function code has syntax errors
            ValueError: If the function code doesn't define the expected function
        """
        try:
            # Create a local environment for the function
            local_env = {}

            # Execute the function code in the local environment
            exec(self.function_code, globals(), local_env)

            # Get the function from the local environment
            function_name = f"{self.name}_action"
            if function_name in local_env:
                self.action_fn = local_env[function_name]
            else:
                raise ValueError(
                    f"Function '{function_name}' not found in the function code"
                )
        except SyntaxError as e:
            logger.error(f"Syntax error in function code: {e}")
            raise
        except Exception as e:
            logger.error(f"Error compiling function: {e}")
            raise

    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Parameters to pass to the action function

        Returns:
            The result of the action function
        """
        # Increment usage count
        self.usage_count += 1

        # Execute the tool
        return super().execute(**kwargs)

    def rate(self, rating: float) -> None:
        """
        Rate the tool.

        Args:
            rating: Rating value (0-5)

        Raises:
            ValueError: If the rating is not between 0 and 5
        """
        if not 0 <= rating <= 5:
            raise ValueError("Rating must be between 0 and 5")

        # Update the average rating
        if self.usage_count > 0:
            self.average_rating = (
                self.average_rating * (self.usage_count - 1) + rating
            ) / self.usage_count
        else:
            self.average_rating = rating

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary representation.

        Returns:
            A dictionary representation of the tool
        """
        # Get the base dictionary
        tool_dict = super().to_dict()

        # Add dynamic tool specific fields
        tool_dict.update({
            "function_code": self.function_code,
            "therapeutic_value": self.therapeutic_value,
            "created_by": self.created_by,
            "tags": self.tags,
            "usage_count": self.usage_count,
            "average_rating": self.average_rating,
            "created_at": self.created_at
        })

        return tool_dict


class ToolRegistry:
    """
    Registry for managing tools in the TTA project.

    This class provides methods for:
    1. Registering tools
    2. Getting tools by name
    3. Creating standard tools
    4. Managing tool configurations
    """

    def __init__(self, neo4j_manager: Optional[Neo4jManager] = None):
        """
        Initialize the ToolRegistry.

        Args:
            neo4j_manager: Neo4j manager for knowledge graph operations
        """
        self.neo4j_manager = neo4j_manager or get_neo4j_manager()
        self.tools = {}

        logger.info("Initialized ToolRegistry")

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Name of the tool to get

        Returns:
            The tool, or None if not found
        """
        if name in self.tools:
            return self.tools[name]

        logger.warning(f"Tool not found: {name}")
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            List of tool dictionaries
        """
        return [tool.to_dict() for tool in self.tools.values()]

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools.

        Returns:
            Dictionary of all registered tools
        """
        return self.tools.copy()

    def load_tools_from_neo4j(self) -> None:
        """
        Load tools from Neo4j.

        This method loads all tools stored in Neo4j and registers them with the registry.
        """
        try:
            # Query for all tools
            query = """
            MATCH (t:DynamicTool)
            RETURN t
            """

            result = self.neo4j_manager.query(query)

            if not result:
                logger.info("No tools found in Neo4j")
                return

            # Register each tool
            for record in result:
                try:
                    tool_data = dict(record["t"])

                    # Convert parameters from JSON string to list of dicts
                    if "parameters" in tool_data and isinstance(tool_data["parameters"], str):
                        tool_data["parameters"] = json.loads(tool_data["parameters"])

                    # Create the tool
                    tool = DynamicTool(**tool_data)

                    # Register the tool
                    self.register_tool(tool)

                except Exception as e:
                    logger.error(f"Error loading tool: {e}")

            logger.info(f"Loaded {len(result)} tools from Neo4j")

        except Exception as e:
            logger.error(f"Error loading tools from Neo4j: {e}")

    def save_tool_to_neo4j(self, tool: BaseTool) -> Tuple[bool, str]:
        """
        Save a tool to Neo4j.

        Args:
            tool: Tool to save

        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - A message explaining the result
        """
        try:
            # Convert the tool to a dictionary
            tool_dict = tool.to_dict()

            # Convert parameters to a JSON string
            tool_dict["parameters"] = json.dumps(tool_dict["parameters"])

            # Store the tool in Neo4j
            query = """
            MERGE (t:DynamicTool {name: $name})
            ON CREATE SET
                t.description = $description,
                t.parameters = $parameters,
                t.function_code = $function_code,
                t.therapeutic_value = $therapeutic_value,
                t.created_at = $created_at,
                t.created_by = $created_by,
                t.tags = $tags,
                t.usage_count = $usage_count,
                t.average_rating = $average_rating,
                t.tool_type = $tool_type,
                t.kg_read = $kg_read,
                t.kg_write = $kg_write
            ON MATCH SET
                t.description = $description,
                t.parameters = $parameters,
                t.function_code = $function_code,
                t.therapeutic_value = $therapeutic_value,
                t.tags = $tags,
                t.usage_count = $usage_count,
                t.average_rating = $average_rating,
                t.tool_type = $tool_type,
                t.kg_read = $kg_read,
                t.kg_write = $kg_write
            RETURN t
            """

            result = self.neo4j_manager.query(query, tool_dict)

            if result:
                return True, f"Tool '{tool.name}' saved successfully"
            else:
                return False, f"Failed to save tool '{tool.name}'"

        except Exception as e:
            logger.error(f"Error saving tool to Neo4j: {e}")
            return False, f"Error saving tool to Neo4j: {str(e)}"

    def delete_tool(self, name: str) -> Tuple[bool, str]:
        """
        Delete a tool from the registry and Neo4j.

        Args:
            name: Name of the tool to delete

        Returns:
            A tuple containing:
            - A boolean indicating success or failure
            - A message explaining the result
        """
        try:
            # Check if the tool exists
            if name not in self.tools:
                return False, f"Tool '{name}' not found"

            # Delete the tool from Neo4j
            query = """
            MATCH (t:DynamicTool {name: $name})
            DETACH DELETE t
            """

            self.neo4j_manager.query(query, {"name": name})

            # Delete the tool from the registry
            del self.tools[name]

            return True, f"Tool '{name}' deleted successfully"

        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            return False, f"Error deleting tool: {str(e)}"

    def __str__(self) -> str:
        """Return a string representation of the registry."""
        return f"ToolRegistry with {len(self.tools)} tools: {', '.join(self.tools.keys())}"

    def __repr__(self) -> str:
        """Return a string representation of the registry."""
        return f"ToolRegistry(tools={list(self.tools.keys())})"


# Singleton instance
_TOOL_REGISTRY = None

def get_tool_registry() -> ToolRegistry:
    """
    Get the singleton instance of the ToolRegistry.

    Returns:
        ToolRegistry instance
    """
    global _TOOL_REGISTRY
    if _TOOL_REGISTRY is None:
        _TOOL_REGISTRY = ToolRegistry()
    return _TOOL_REGISTRY
