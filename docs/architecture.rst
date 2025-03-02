.. _architecture:

=================================
System Architecture (Detailed)
=================================

This document provides a detailed overview of the Therapeutic Text Adventure (TTA) system architecture. It describes the key components, their interactions, the data flow within the game, and the technologies used.

.. contents:: :local:
    :depth: 3

.. image:: architecture.png
   :alt: TTA System Architecture Diagram
   :width: 800px
   :align: center

Overview
========

TTA is built upon a modular, AI-driven architecture that leverages several key technologies to create a dynamic, responsive, and personalized text adventure game.  The core design principles are:

*   **Player Agency:** The player's choices have significant impact on the narrative and game world.
*   **AI-Driven Content Generation:**  AI agents, powered by a Large Language Model (LLM), generate most of the game's content dynamically.
*   **Knowledge Graph Foundation:**  A Neo4j graph database stores all game data, providing a rich and interconnected representation of the world.
*   **Therapeutic Integration:**  Therapeutic concepts are subtly woven into the narrative and game mechanics.
*   **Ethical AI:**  The system is designed to be ethical, avoiding harmful stereotypes and biases.
*   **Extensibility:** The architecture is designed to be modular and extensible, allowing for future expansion and addition of new features.

Key Technologies
================

*   **Qwen2.5 (Large Language Model):** The core intelligence of the system.  Hosted locally using LM Studio.  Provides natural language understanding, text generation, and reasoning capabilities.  Acts as a "universal agent engine," dynamically assuming different agent roles.  (See `tta/settings.py` for LLM configuration).
*   **LangGraph:**  The orchestration framework.  Manages the interactions between AI agent roles and maintains the game state.  Defines workflows as state machines.  (See `tta/main.py` for a basic example, and future agent files for more complex workflows).
*   **Neo4j (Graph Database):**  Persistent storage for the knowledge graph.  Stores all game data (concepts, characters, locations, events, relationships, etc.).  (See `tta/utils/neo4j_utils.py` for database interaction functions).
*   **LangChain:**  A library for building LLM applications.  Used for:
    *   **Tool Definition:** Defining tools that agents can use to interact with the knowledge graph and other systems.
    *   **Prompt Template Management:** Creating and managing reusable prompt templates.
    *   **Agent Creation:** Providing a framework for structuring AI agents.
*   **Pydantic:**  A Python library for data validation and settings management.  Used to define data schemas (in `tta/schema.py`) and ensure data consistency throughout the system.
*   **Python:** The primary programming language for all aspects of the project.
*   **spaCy:**  A Natural Language Processing (NLP) library used for efficient text processing, particularly in the Input Processor Agent (IPA).
* **Guidance:** (Optional) For fine-grained control over LLM output.
* **Firecrawl:** (Optional, "Our Universe" and "Alternate Earths" only) For web scraping.
* **TensorFlow:** (Optional) For custom model training.

Data Flow
=========

A typical player interaction cycle proceeds as follows:

1.  **Player Input:** The player enters a text command (e.g., "go north", "examine the rusty key", "talk to Elara") through the user interface (currently a simple text-based interface in `tta/main.py`).

2.  **Input Processing (IPA):**
    *   The Input Processor Agent (IPA) (`app/tta/ipa.py`) receives the raw player input.
    *   The IPA uses Qwen2.5 (via LangChain) and, potentially, spaCy for Natural Language Understanding (NLU).
    *   The IPA performs the following tasks:
        *   **Parsing:** Breaks down the input into its components (words, phrases).
        *   **Intent Recognition:** Determines the player's intention (e.g., `move`, `examine`, `talk_to`, `quit`, `unknown`).
        *   **Entity Extraction:** Identifies relevant entities (e.g., `direction: north`, `object: rusty key`, `npc: Elara`).
        *   **Structuring:** Transforms the parsed input into a structured JSON format, defined by Pydantic models in `app/tta/schema.py`.  Example: `{"intent": "move", "direction": "north"}`.
        *   **CoRAG (Optional):**  If the input is ambiguous or requires more information, the IPA may use Chain-of-Retrieval Augmented Generation (CoRAG) to query the knowledge graph (using the `query_knowledge_graph` tool) and refine its understanding.
    *   The IPA updates the `AgentState` with the `parsed_input`.

3.  **Agent Activation (LangGraph):**
    *   LangGraph receives the updated `AgentState` from the IPA.
    *   Based on the `parsed_input.intent` and the `current_agent` field in the `AgentState`, LangGraph determines which AI agent role should be activated next.
    *   LangGraph selects the appropriate prompt template for the activated agent role.  (Prompt templates are currently defined within the agent code, but will likely be moved to a separate `data/` directory in the future.)
    *   LangGraph populates the prompt template with relevant data from the `AgentState` (e.g., `player_input`, `game_state`, `character_states`, `conversation_history`, `metaconcepts`).
    *   LangGraph provides Qwen2.5 with access to the tools available to the activated agent role (defined using LangChain's `Tool` class).

4.  **Agent Processing (Qwen2.5):**
    *   Qwen2.5, acting as the designated agent role (e.g., NGA, WBA, CCA, LKA), receives the prompt and context from LangGraph.
    *   The agent performs its designated task, which may involve:
        *   **Text Generation:** Generating descriptions, dialogue, or other narrative text.
        *   **Reasoning:**  Making inferences based on the current game state and knowledge graph data.
        *   **Decision-Making:**  Choosing between different actions or responses.
        *   **Tool Use:**  Calling tools (defined via LangChain) to interact with the knowledge graph (Neo4j) or other external systems.  This is how agents access and modify the game world.  Tool calls are typically formatted as JSON.
        *   **CoRAG:**  If necessary, the agent may use CoRAG to iteratively retrieve information from the knowledge graph and refine its response.  This involves generating sub-queries and using the `query_knowledge_graph` tool.

5.  **Output Generation:**
    *   The agent generates its output, typically in JSON format, conforming to a Pydantic schema defined in `app/tta/schema.py`.
    *   The output includes the generated text (if any), updates to the game state, and any tool call requests.

6.  **State Update (LangGraph):**
    *   LangGraph updates the `AgentState` with the agent's output.  This includes updating fields like `response` (for generated text), `game_state`, `character_states`, and `conversation_history`.

7.  **Tool Execution (LangChain):**
    *   If the agent's output includes a tool call, LangChain identifies the corresponding Python function (defined in `app/tta/utils/neo4j_utils.py` or other modules) and executes it.
    *   The tool's input is taken from the agent's output (typically a JSON object).
    *   The tool performs its action (e.g., querying Neo4j, updating the game state).
    *   The tool's output (also typically in JSON format) is returned to LangGraph and added to the `AgentState`.

8.  **Loop/Branching (LangGraph):**
    *   LangGraph determines the next step based on the updated `AgentState` and the defined workflow (state machine).
    *   The workflow can include:
        *   **Loops:**  Repeating a sequence of actions (e.g., for conversations or CoRAG).
        *   **Conditional Branches:**  Choosing different paths based on the player's input, the game state, or the agent's output.
        *   **Transitions:**  Moving between different agent roles.
    *   The workflow typically loops back to the IPA to await further player input.

9.  **Output to Player:**
    *   The generated text (from the `response` field of the `AgentState`) is presented to the player through the user interface.

10. **Persistence (Neo4j):**
    *   The game state (represented by the `AgentState`) is periodically saved to the Neo4j database. This allows for:
        *   **Saving and Loading:** Players can save their progress and resume later.
        *   **Long-Term Memory:** The game can remember past events, player choices, and character relationships across multiple sessions.
        *   **Human-in-the-Loop Review:**  The saved game state can be reviewed and potentially modified by human moderators (for quality control, ethical oversight, or error correction).

Key Components (Detailed)
========================

**AI Agents:**

See :doc:`agents` for detailed descriptions of each agent role, including their responsibilities, tools, and interactions.

**Knowledge Graph:**

See :doc:`knowledge_graph` for a detailed description of the knowledge graph schema, data representation, and Cypher query conventions.  The knowledge graph is the central data store for the game, and its structure is crucial for the AI agents' ability to reason and generate content.

**LangGraph State (`AgentState`):**

The `AgentState` (defined in `app/tta/schema.py` using Pydantic) is the *central data structure* that is passed between agents.  It represents the complete state of the game at any given point.  It includes:

*   `current_agent`: (str) The ID of the currently active agent role (e.g., "IPA", "NGA").
*   `player_input`: (Optional[str]) The raw player input text.
*   `parsed_input`: (Optional[Dict]) The structured representation of the player's input (output of the IPA).
*   `game_state`: (GameState) A nested Pydantic model containing information about the game world:
    *   `current_location_id`: (str) The ID of the player's current location.
    *   `nearby_characters`: (List[str]) A list of character IDs of NPCs in the same location.
    *   `world_state`: (Dict) A dictionary for tracking overall world state and parameters.
*   `character_states`: (Dict[str, CharacterState]) A dictionary mapping character IDs to `CharacterState` objects (another Pydantic model), which store information about individual characters (health, mood, relationships, etc.).
*   `conversation_history`: (List[Dict]) A list of dictionaries, each representing a turn in the conversation.
*   `metaconcepts`: (List[str]) A list of the currently active metaconcepts.
*   `memory`: (List[Dict])  A mechanism for storing and retrieving long-term information (using Neo4j).
*   `prompt_chain`: (List[Dict]) A history of prompts that have been used.
*   `response`: (str) The text generated by the current agent.

The use of Pydantic models for the `AgentState` and its nested components ensures type safety, automatic data validation, and clear documentation of the data structure.

**Tools:**

Tools are Python functions that allow AI agents to interact with external systems.  They are defined using LangChain's `Tool` class (or a similar custom implementation).  Each tool has:

*   `name`: A unique identifier (e.g., `query_knowledge_graph`).
*   `description`: A natural language description of the tool's function.
*   `args_schema`: A Pydantic model defining the expected input parameters.
*   `func`: The Python function that implements the tool's functionality.
* `return_direct`: (Optional) If true, returns output directly to LLM.

Example (Conceptual - from `app/tta/utils/neo4j_utils.py`):

.. code-block:: python

    from langchain.tools import Tool
    from pydantic import BaseModel, Field
    from typing import Optional

    class QueryKnowledgeGraphInput(BaseModel):
        query: str = Field(description="The Cypher query to execute.")
        agent: Optional[str] = Field(None, description="The agent making the request.")

    def query_knowledge_graph(query: str, agent: Optional[str] = None) -> str:
        # ... (Implementation to connect to Neo4j and execute the query) ...
        return result_string

    query_knowledge_graph_tool = Tool(
        name="query_knowledge_graph",
        description="Executes a Cypher query against the Neo4j knowledge graph.",
        args_schema=QueryKnowledgeGraphInput,
        func=query_knowledge_graph,
    )

The `query_knowledge_graph_tool` can then be made available to AI agents within LangGraph workflows.

**Prompts:**

Prompts are the instructions given to Qwen2.5 to guide its behavior.  They are carefully crafted to elicit the desired output from the LLM.  A prompt typically includes:

*   **Metaconcepts:** High-level principles that should guide the agent's behavior (e.g., "Prioritize Player Agency," "Maintain Narrative Consistency").
*   **Agent Role and Task:**  A clear statement of the agent's role (e.g., "You are the Narrative Generator Agent") and the specific task it should perform (e.g., "Generate a description of the current location").
*   **Context:**  Relevant information from the `AgentState` (e.g., `current_location`, `nearby_characters`, `player_input`).
*   **Available Tools:**  A list of the tools that the agent can use.
*   **Output Format:**  Instructions on how the output should be formatted (usually JSON, with a schema defined using Pydantic).

Prompt templates (using LangChain's `PromptTemplate` class) are used to manage the structure of prompts and dynamically insert data from the `AgentState`.

Example (Conceptual):

.. code-block:: python

    from langchain.prompts import PromptTemplate

    NGA_PROMPT_TEMPLATE = """
    Metaconcepts:
    {metaconcepts}

    Agent Role and Task:
    You are the Narrative Generator Agent (NGA). Your task is to generate
    a response to the player's action, considering the current game state.

    Context:
    - Current Location: {current_location}
    - Nearby Characters: {nearby_characters}
    - Player Input: {player_input}

    Output Format:
    {{"response": "...", "action": "..."}}
    """

    prompt_template = PromptTemplate.from_template(NGA_PROMPT_TEMPLATE)

This architecture provides a solid foundation for building a complex, dynamic, and engaging text adventure game. The combination of AI-driven content generation, a rich knowledge graph, and a flexible agent architecture allows for a high degree of player agency and a personalized, potentially therapeutic experience.