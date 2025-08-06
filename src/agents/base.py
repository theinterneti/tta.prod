"""
Base Agent for the TTA Project.

This module provides the base agent class for all agents in the TTA project.
Updated to use the modernized model provider system.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, Tuple, Union

from ..models import UnifiedModelClient, TaskType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents in the TTA project with modernized model support."""

    def __init__(
        self,
        name: str,
        description: str,
        task_type: TaskType = TaskType.NARRATIVE,
        neo4j_manager=None,
        tools: Dict[str, Callable] = None,
        system_prompt: str = None,
        model_client: Optional[UnifiedModelClient] = None
    ):
        """
        Initialize the base agent.

        Args:
            name: Name of the agent
            description: Description of the agent
            task_type: Type of task this agent performs (affects model selection)
            neo4j_manager: Neo4j manager for knowledge graph operations
            tools: Dictionary of tools available to the agent
            system_prompt: System prompt for the agent
            model_client: Model client for LLM interactions
        """
        self.name = name
        self.description = description
        self.task_type = task_type
        self.neo4j_manager = neo4j_manager
        self.tools = tools or {}
        self.system_prompt = system_prompt or f"You are {name}, {description}."
        self.model_client = model_client or UnifiedModelClient()

        logger.info(f"Initialized {name} agent with task type {task_type}")

    def process(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input data and return a response.

        Args:
            input_data: Input data to process
            context: Additional context information

        Returns:
            The result of processing the input data
        """
        # This is a placeholder method that should be overridden by subclasses
        raise NotImplementedError("Subclasses must implement process method")

    def add_tool(self, name: str, tool: Callable) -> None:
        """
        Add a tool to the agent.

        Args:
            name: Name of the tool
            tool: Tool function
        """
        self.tools[name] = tool
        logger.info(f"Added tool {name} to {self.name} agent")

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the agent.

        Args:
            name: Name of the tool

        Returns:
            True if the tool was removed, False otherwise
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"Removed tool {name} from {self.name} agent")
            return True
        return False

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get a list of available tools.

        Returns:
            List of available tools with name and description
        """
        return [
            {
                "name": name,
                "description": getattr(tool, "__doc__", "No description")
            }
            for name, tool in self.tools.items()
        ]

    def update_system_prompt(self, system_prompt: str) -> None:
        """
        Update the system prompt.

        Args:
            system_prompt: New system prompt
        """
        self.system_prompt = system_prompt
        logger.info(f"Updated system prompt for {self.name} agent")

    def __str__(self) -> str:
        """Return a string representation of the agent."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Return a string representation of the agent."""
        return f"Agent(name='{self.name}', description='{self.description}', tools={list(self.tools.keys())})"

    def to_mcp_server(self, server_name: Optional[str] = None, server_description: Optional[str] = None):
        """
        Convert this agent to an MCP server.

        Args:
            server_name: Name for the MCP server (defaults to agent.name + " MCP Server")
            server_description: Description for the MCP server

        Returns:
            An AgentMCPAdapter instance
        """
        # Import here to avoid circular imports
        from ..mcp import create_agent_mcp_server

        return create_agent_mcp_server(
            agent=self,
            server_name=server_name,
            server_description=server_description
        )

    def get_mcp_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for MCP.

        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.get_available_tools(),
            "system_prompt": self.system_prompt
        }

    async def generate_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response using the modernized model client.

        Args:
            prompt: The prompt to send to the model
            context: Additional context for the generation
            temperature: Temperature override for this generation
            max_tokens: Max tokens override for this generation
            **kwargs: Additional arguments for the model

        Returns:
            Generated response string
        """
        # Combine system prompt with user prompt
        full_prompt = f"{self.system_prompt}\n\n{prompt}"

        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"{self.system_prompt}\n\nContext:\n{context_str}\n\n{prompt}"

        return await self.model_client.generate(
            prompt=full_prompt,
            task_type=self.task_type,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def stream_response(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Stream a response using the modernized model client.

        Args:
            prompt: The prompt to send to the model
            context: Additional context for the generation
            temperature: Temperature override for this generation
            max_tokens: Max tokens override for this generation
            **kwargs: Additional arguments for the model

        Yields:
            Response chunks as they are generated
        """
        # Combine system prompt with user prompt
        full_prompt = f"{self.system_prompt}\n\n{prompt}"

        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"{self.system_prompt}\n\nContext:\n{context_str}\n\n{prompt}"

        async for chunk in self.model_client.stream_generate(
            prompt=full_prompt,
            task_type=self.task_type,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            yield chunk

    def to_json(self) -> str:
        """
        Convert this agent to a JSON string.

        Returns:
            JSON string representation of the agent
        """
        return json.dumps(self.get_mcp_info(), indent=2)
