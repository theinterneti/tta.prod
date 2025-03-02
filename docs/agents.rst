.. _agents:

==========
AI Agents
==========

This document provides detailed descriptions of the AI agent roles within the
Therapeutic Text Adventure (TTA) system. Each agent is a specialized role
assumed by the Qwen2.5 Large Language Model (LLM), guided by specific prompts
and tools.

Agent Architecture
==================

TTA employs a model-powered interface architecture, where Qwen2.5 acts as a
unified intelligence capable of assuming different agent roles dynamically.
LangGraph orchestrates the interactions between these roles and manages the
overall game state. This approach offers several advantages:

*   **Flexibility:** New agent roles can be easily defined by creating new
    prompts and tools.
*   **Consistency:** Using a single underlying model ensures greater consistency
    in language style and reasoning.
*   **Simplified Development:** Reduces code complexity compared to managing
    multiple independent AI agents.

Agent Roles
===========

.. contents::
   :local:
   :depth: 2

Input Processor Agent (IPA)
----------------------------

*   **Primary Role:** The entry point for all player interactions. Parses
    player input, identifies intent, and initiates the appropriate workflow.

*   **Key Responsibilities:**

    *   Parse player input (text) using spaCy and other NLP techniques.
    *   Identify player intent (e.g., move, examine, talk, quit).
    *   Extract key entities (e.g., direction, object, NPC name).
    *   Structure the parsed input into JSON format (using Pydantic models defined in `app/tta/schema.py`).
    *   Handle ambiguity and invalid input.
    *   Initiate CoRAG (Chain-of-Retrieval Augmented Generation) for
        clarification or additional information retrieval, querying the Neo4j
        database as needed.

*   **Tools:**

    *   `query_knowledge_graph`: Queries the Neo4j knowledge graph (implementation in `app/tta/utils/neo4j_utils.py`).

*   **Interactions:**

    *   Receives raw player input from the `AgentState`.
    *   Outputs structured data (parsed intent) to the `AgentState`.
    *   Triggers the next node in the LangGraph workflow (e.g., NGA, LKA).

* **Code Location:** `app/tta/ipa.py`

Narrative Generator Agent (NGA)
-------------------------------

*   **Primary Role:** Generates the narrative text that the player experiences,
    including descriptions, dialogue, and responses to player actions.

*   **Key Responsibilities:**

    *   Generate descriptive text for locations, objects, and characters.
    *   Generate dialogue for Non-Player Characters (NPCs).
    *   Respond to player actions and choices.
    *   Maintain narrative consistency and coherence.
    *   Integrate therapeutic concepts subtly.
    *   Use CoRAG to retrieve additional information and refine its output.

*   **Tools:**

    *   `query_knowledge_graph`: Queries the Neo4j knowledge graph.
    *   `get_character_profile`: Retrieves character information (likely uses `query_knowledge_graph` internally).
    *   `get_location_details`: Retrieves location information (likely uses `query_knowledge_graph` internally).
    *   `generate_text`: (Internal) Generates text based on a prompt.

*   **Interactions:**

    *   Receives parsed input and game state from the `AgentState`.
    *   May request information from the WBA, CCA, and LKA (via tools).
    *   Updates the `AgentState` with generated text and any changes to the
        game state.

* **Code Location:** `app/tta/agents/narrative_generator.py`

World Builder Agent (WBA)
--------------------------

*   **Primary Role:** Manages the static and dynamic aspects of the game world, including
    locations, factions, and their relationships.  Responsible for both initial
    world generation and ongoing updates.

*   **Key Responsibilities:**

    *   Create, update, and retrieve information about locations.
    *   Manage factions and their relationships.
    *   Ensure world consistency.
    *   Respond to in-game events that alter the world (e.g., natural disasters,
        wars).

*   **Tools:**

    *   `get_location_details`: Retrieves detailed information about a location.
    *   `create_location`: Creates a new location.
    *   `update_location`: Modifies an existing location.
    *   `query_knowledge_graph`: General-purpose query tool.

*   **Interactions:**

    *   Provides location details to the NGA upon request.
    *   Consults the LKA for consistency checks.
    *   Updates the `game_state` in the `AgentState`.

* **Code Location:** `app/tta/agents/world_builder.py`

Character Creator Agent (CCA)
-----------------------------

*   **Primary Role:** Creates and manages Non-Player Characters (NPCs).

*   **Key Responsibilities:**

    *   Generate new NPCs, including their personalities, backstories,
        relationships, and skills.
    *   Update character information based on game events.

*   **Tools:**

    *   `create_character`: Creates a new character.
    *   `get_character_profile`: Retrieves character information.
    *   `update_character_profile`: Modifies an existing character.
    *   `query_knowledge_graph`: General-purpose query tool.

*   **Interactions:**

    *   Provides character information to the NGA for dialogue generation.
    *   Updates the `character_states` in the `AgentState`.
    *   May interact with the WBA to place characters in locations.

* **Code Location:**  (Implicitly part of other agents, particularly the NGA and POA.  Could be a separate module in the future if complexity warrants.)

Lore Keeper Agent (LKA)
------------------------

*   **Primary Role:** Maintains the consistency and integrity of the game's
    knowledge graph. Acts as a "fact-checker" and "librarian."

*   **Key Responsibilities:**

    *   Check new content for consistency with existing lore.
    *   Retrieve information from the knowledge graph for other agents.
    *   Identify and resolve inconsistencies.
    *   Expand the lore based on new information.
    *   Ensure adherence to metaconcepts.

*   **Tools:**

    *   `query_knowledge_graph`: Primary tool for accessing the knowledge graph.
    *   `check_consistency`: (Conceptual - may be implemented as part of `query_knowledge_graph` or a separate tool) Checks for contradictions.
    *   `update_node`: Updates node properties.
    *   `create_relationship`: Creates new relationships.

*   **Interactions:**

    *   Interacts with virtually all other agents to ensure consistency.
    *   Frequently invoked by LangGraph workflows.

* **Code Location:** (Likely integrated into other agents, especially NGA and WBA, and utilizes `neo4j_utils.py` extensively.  Could be a separate module in the future.)

Player Onboarding Agent (POA)
------------------------------
* **Primary Role:** Manages the initial player experience, including character creation and the tutorial.

* **Key Responsibilities:**
    *   Handles the initial interaction with the player.
    *   Guides players through character creation, utilizing the CCA's capabilities.
    *   Manages the tutorial sequence.
    *   Provides personalized support and guidance.
    *   Tracks player progress and preferences, updating the `player_profile` in the `AgentState`.
    *   Identifies potential triggers and tailors the experience.

*   **Tools:**
        *   `get_player_profile`
        *   `update_player_profile`
        *   `generate_tutorial_text`
        *   `query_knowledge_graph`
        *   `create_character`

*   **Interactions:**
        *   IPA: The IPA parses player input during onboarding.
        *   NGA: The POA collaborates with the NGA to present information.
        *   CCA: The POA utilizes the CCA’s capabilities.
        * LKA: Consults for consistency.

* **Code Location:** (Likely a separate module, potentially `app/tta/onboarding.py`, or integrated into `main.py` for the initial prototype.)

Nexus Manager Agent (NMA) - Optional
------------------------------------
* **Primary Role:** Manages connections between universes and the Nexus (if implemented).

* **Key Responsibilities:**
    *   Create, update, and maintain records of universe connections.
    *   Manage how universes are represented in the Nexus.
    *   (Potentially) Handle inter-universe travel mechanics.

* **Tools:**
    *   `query_knowledge_graph`: Retrieves information about universes.
    *   `create_universe_connection`: Creates new connections.
    *   `get_universe_details`: Retrieves universe details.
    *   `update_nexus_representation`: Updates Nexus representations.

* **Interactions:**
    *   UGA (Universe Generator Agent): Receives information about new universes.
    *   LKA: Consults for consistency.
    *   LangGraph: Updates game state with connection information.

* **Code Location:** (If implemented, likely a separate module, e.g., `app/tta/nexus.py`)