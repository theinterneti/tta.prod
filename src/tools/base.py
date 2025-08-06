"""
Base Tool for the TTA Project.

This module provides the base tool class for all tools in the TTA project.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback for environments without pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def dict(self, **kwargs):
            return {k: v for k, v in self.__dict__.items() if k not in kwargs.get("exclude", {})}
    
    def Field(*args, **kwargs):
        return None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolParameter:
    """Schema for a tool parameter."""
    
    def __init__(
        self,
        name: str,
        description: str,
        type: str = "string",
        required: bool = False,
        default: Any = None,
        enum: Optional[List[str]] = None
    ):
        """
        Initialize a tool parameter.
        
        Args:
            name: Name of the parameter
            description: Description of the parameter
            type: Type of the parameter
            required: Whether the parameter is required
            default: Default value for the parameter
            enum: Enumeration of allowed values
        """
        self.name = name
        self.description = description
        self.type = type
        self.required = required
        self.default = default
        self.enum = enum
    
    def dict(self) -> Dict[str, Any]:
        """
        Convert the parameter to a dictionary.
        
        Returns:
            Dictionary representation of the parameter
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "required": self.required,
            "default": self.default,
            "enum": self.enum
        }


class BaseTool:
    """Base class for all tools in the TTA project."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[ToolParameter] = None,
        action_fn: Optional[Callable] = None,
        kg_read: bool = False,
        kg_write: bool = False,
        tool_type: str = "standard"
    ):
        """
        Initialize a base tool.
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
            parameters: Parameters for the tool
            action_fn: Function to call when the tool is used
            kg_read: Whether the tool reads from the knowledge graph
            kg_write: Whether the tool writes to the knowledge graph
            tool_type: Type of tool
        """
        self.name = name
        self.description = description
        self.parameters = parameters or []
        self.action_fn = action_fn
        self.kg_read = kg_read
        self.kg_write = kg_write
        self.tool_type = tool_type
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given parameters.
        
        Args:
            **kwargs: Parameters to pass to the action function
            
        Returns:
            The result of the action function
        """
        # Validate parameters
        self._validate_parameters(kwargs)
        
        # Execute the action function
        if self.action_fn:
            return self.action_fn(**kwargs)
        else:
            raise ValueError(f"Tool {self.name} has no action function")
    
    def _validate_parameters(self, params: Dict[str, Any]) -> None:
        """
        Validate parameters against the tool's parameter schema.
        
        Args:
            params: Parameters to validate
            
        Raises:
            ValueError: If a required parameter is missing or a parameter has an invalid type
        """
        for param in self.parameters:
            # Check if required parameter is missing
            if param.required and param.name not in params:
                raise ValueError(f"Missing required parameter: {param.name}")
            
            # Check if parameter is present
            if param.name in params:
                value = params[param.name]
                
                # Check if parameter has a valid type
                if param.type == "string" and not isinstance(value, str):
                    raise ValueError(
                        f"Parameter {param.name} must be a string, got {type(value)}"
                    )
                elif param.type == "integer" and not isinstance(value, int):
                    raise ValueError(
                        f"Parameter {param.name} must be an integer, got {type(value)}"
                    )
                elif param.type == "boolean" and not isinstance(value, bool):
                    raise ValueError(
                        f"Parameter {param.name} must be a boolean, got {type(value)}"
                    )
                elif param.type == "array" and not isinstance(value, list):
                    raise ValueError(
                        f"Parameter {param.name} must be an array, got {type(value)}"
                    )
                elif param.type == "object" and not isinstance(value, dict):
                    raise ValueError(
                        f"Parameter {param.name} must be an object, got {type(value)}"
                    )
                
                # Check if parameter has a valid enum value
                if param.enum and value not in param.enum:
                    raise ValueError(
                        f"Parameter {param.name} must be one of {param.enum}, got {value}"
                    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary representation.
        
        Returns:
            A dictionary representation of the tool
        """
        # Convert to dict excluding action_fn
        tool_dict = {
            "name": self.name,
            "description": self.description,
            "parameters": [param.dict() for param in self.parameters],
            "kg_read": self.kg_read,
            "kg_write": self.kg_write,
            "tool_type": self.tool_type
        }
        
        return tool_dict
    
    def to_json(self) -> str:
        """
        Convert the tool to a JSON string.
        
        Returns:
            A JSON string representation of the tool
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseTool":
        """
        Create a tool from a dictionary.
        
        Args:
            data: Dictionary representation of the tool
            
        Returns:
            A BaseTool instance
        """
        # Convert parameters from dict to ToolParameter
        if "parameters" in data:
            data["parameters"] = [
                ToolParameter(**param) for param in data["parameters"]
            ]
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "BaseTool":
        """
        Create a tool from a JSON string.
        
        Args:
            json_str: JSON string representation of the tool
            
        Returns:
            A BaseTool instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
