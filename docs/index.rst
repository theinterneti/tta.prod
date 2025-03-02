.. Therapeutic Text Adventure documentation master file

====================================
Therapeutic Text Adventure (TTA)
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   architecture
   agents
   knowledge_graph
   modules

Welcome to the documentation for the Therapeutic Text Adventure (TTA) project!

TTA is an AI-driven text adventure game designed to provide a personalized and
potentially therapeutic experience for players.  The game leverages a
knowledge graph, large language models (LLMs), and a robust agent architecture
to create a dynamic and engaging world.

This documentation provides a comprehensive overview of the project, including:

*   **Architecture:**  An overview of the system's design and key components.
*   **AI Agents:**  Detailed descriptions of the AI agents and their roles.
*   **Knowledge Graph:**  The schema and conventions for the Neo4j knowledge graph.
*   **Modules:** Documentation for individual Python modules and classes.

Getting Started
===============

To get started with TTA development, you'll need to:

1.  **Set up the development environment:**  See the `Project Overview and Setup`
    document (linked from the code) for instructions on setting up VS Code,
    Docker, and Poetry.
2.  **Install the required dependencies:**  Use Poetry to install the project's
    dependencies (see `pyproject.toml`).
3.  **Configure the environment variables:**  Create a `.env` file and set the
    necessary environment variables (e.g., Neo4j connection details, API keys).
4.  **Run the game:**  Execute the `main.py` script to start the game.

Contributing
============

Contributions to the TTA project are welcome!  Please see the `CONTRIBUTING.md`
file (not yet created) for guidelines on how to contribute.

License
=======

This project is licensed under the MIT License - see the `LICENSE` file (not yet created) for details.

.. _architecture:

=====================
System Architecture
=====================

This document provides a high-level overview of the Therapeutic Text Adventure (TTA) system architecture. It describes the key components, their interactions, and the data flow within the game.

.. image:: architecture.png
   :alt: TTA System Architecture Diagram
   :width: 800px

Overview
========

TTA is built upon a modular, AI-driven architecture that leverages several key technologies:

*   **Qwen2.5 (Large Language Model):**  The core intelligence of the system, responsible for natural language understanding, text generation, and reasoning.  Qwen2.5 acts as a universal agent engine, dynamically assuming different agent roles based on context.
*   **LangGraph:**  The orchestration framework that manages the interactions between AI agent roles and maintains the overall game state.  It defines workflows as state machines, where nodes represent agent roles and edges represent transitions.
*   **Neo4j (Graph Database):**  The persistent storage for the TTA knowledge graph, representing the game world, its entities, and their relationships.  Provides a structured and queryable representation of all game knowledge.
*   **LangChain:**  A library that provides tools and abstractions for building applications with LLMs.  Used for tool definition, prompt template management, and agent creation.
*   **Pydantic:**  A Python library for data validation and settings management.  Used to define data schemas and ensure data consistency.
*   **Python:** The primary programming language used for implementing game logic, AI agents, and database interactions.

Data Flow
=========

The following steps describe a typical interaction cycle within the TTA system:

1.  **Player Input:** The player enters a text command through the user interface.
2.  **Input Processing (IPA):** The Input Processor Agent (IPA) receives the raw player input.  It uses Qwen2.5 and NLP techniques (potentially spaCy) to:
    *   Parse the input.
    *   Identify the player's intent (e.g., move, examine, talk).
    *   Extract key entities (e.g., direction, object, character name).
    *   Structure the parsed input into a JSON format.
3.  **Agent Activation (LangGraph):** LangGraph receives the parsed input from the IPA (via the shared `AgentState`).  Based on the identified intent and the current game state, LangGraph activates the appropriate AI agent role.  This involves:
    *   Setting the `current_agent` field in the `AgentState`.
    *   Selecting the appropriate prompt template for the activated agent role.
    *   Populating the prompt template with data from the `AgentState`.
    *   Providing Qwen2.5 with access to the necessary tools (via LangChain).
4.  **Agent Processing (Qwen2.5):** Qwen2.5, acting as the designated agent role, processes the prompt and context.  This may involve:
    *   Generating text (descriptions, dialogue, etc.).
    *   Reasoning about the game world.
    *   Making decisions based on the current state and metaconcepts.
    *   Using tools to interact with the knowledge graph (Neo4j) or external systems.
    *   Employing CoRAG (Chain-of-Retrieval Augmented Generation) for iterative information retrieval.
5.  **Output Generation:** The agent generates output, typically in JSON format. This output may include:
    *   Generated text to be displayed to the player.
    *   Updates to the game state.
    *   Tool call requests.
    *   Error messages.
6.  **State Update (LangGraph):** LangGraph updates the `AgentState` with the agent's output.
7.  **Tool Execution (LangChain):** If the agent's output includes a tool call, LangChain executes the corresponding function (e.g., querying Neo4j, accessing a web API). The tool's output is then added to the `AgentState`.
8.  **Loop/Branching (LangGraph):** LangGraph determines the next step based on the updated `AgentState` and the defined workflow.  This may involve:
    *   Looping back to the IPA for further player input.
    *   Transitioning to a different agent role.
    *   Executing conditional logic based on the game state or agent output.
9.  **Output to Player:** The generated text (from the `response` field of the `AgentState`) is presented to the player through the user interface.
10. **Persistence (Neo4j):** The game state is periodically saved to Neo4j, allowing for persistence across sessions and enabling features like long-term memory.

Key Components
==============

*   **AI Agents:** See :doc:`agents` for detailed descriptions of each agent role.
*   **Knowledge Graph:** See :doc:`knowledge_graph` for details on the knowledge graph schema and data representation.
*   **LangGraph State:** The `AgentState` (defined using Pydantic) is the central data structure that is passed between agents. It contains all relevant information about the current game state, including player input, parsed input, character information, location details, conversation history, and more.
*   **Tools:** Tools are functions that allow AI agents to interact with external systems (e.g., Neo4j, web APIs). They are defined using LangChain's `Tool` class.
*   **Prompts:** Prompts are the instructions given to Qwen2.5 to guide its behavior. They are carefully crafted using prompt templates (managed by LangChain) and include metaconcepts, agent role definitions, contextual information, and output format instructions.
* **Metaconcepts:** These are high-level principles or guidelines that govern the behaviour of the AI agents.

This architecture enables a highly dynamic, responsive, and personalized game experience, where the narrative and game world evolve based on player choices and AI-driven content generation.
content_copy
download
Use code with caution.
Restructuredtext

12. docs/agents.rst (AI Agents - Optional)

.. _agents:

==========
AI Agents
==========

This document provides detailed descriptions of the AI agent roles within the
Therapeutic Text Adventure (TTA) system.  Each agent is a specialized role
assumed by the Qwen2.5 Large Language Model (LLM), guided by specific prompts
and tools.

Agent Architecture
==================

TTA employs a model-powered interface architecture, where Qwen2.5 acts as a
unified intelligence capable of assuming different agent roles dynamically.
LangGraph orchestrates the interactions between these roles and manages the
overall game state.  This approach offers several advantages:

*   **Flexibility:** New agent roles can be easily defined by creating new
    prompts and tools.
*   **Consistency:** Using a single underlying model ensures greater consistency
    in language style and reasoning.
*   **Simplified Development:**  Reduces code complexity compared to managing
    multiple independent AI agents.

Agent Roles
===========

.. contents::
   :local:
   :depth: 2

Input Processor Agent (IPA)
----------------------------

*   **Primary Role:** The entry point for all player interactions.  Parses
    player input, identifies intent, and initiates the appropriate workflow.

*   **Key Responsibilities:**

    *   Parse player input (text).
    *   Identify player intent (e.g., move, examine, talk, quit).
    *   Extract key entities (e.g., direction, object, NPC name).
    *   Structure the parsed input into JSON format.
    *   Handle ambiguity and invalid input.
    *   Initiate CoRAG (Chain-of-Retrieval Augmented Generation) for
        clarification or additional information retrieval.

*   **Tools:**

    *   `query_knowledge_graph`: Queries the Neo4j knowledge graph.

*   **Interactions:**

    *   Receives raw player input from the `AgentState`.
    *   Outputs structured data (parsed intent) to the `AgentState`.
    *   Triggers the next node in the LangGraph workflow (e.g., NGA, LKA).

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
    *   `get_character_profile`: Retrieves character information.
    *   `get_location_details`: Retrieves location information.
    *   `generate_text`: (Internal) Generates text based on a prompt.

*   **Interactions:**

    *   Receives parsed input and game state from the `AgentState`.
    *   May request information from the WBA, CCA, and LKA (via tools).
    *   Updates the `AgentState` with generated text and any changes to the
        game state.

World Builder Agent (WBA)
--------------------------

*   **Primary Role:** Manages the static aspects of the game world, including
    locations, factions, and their relationships.

*   **Key Responsibilities:**

    *   Create, update, and retrieve information about locations.
    *   Manage factions and their relationships.
    *   Ensure world consistency.

*   **Tools:**

    *   `get_location_details`: Retrieves detailed information about a location.
    *   `create_location`: Creates a new location.
    *   `update_location`: Modifies an existing location.
    *   `query_knowledge_graph`: General-purpose query tool.

*   **Interactions:**

    *   Provides location details to the NGA.
    *   Consults the LKA for consistency checks.
    *   Updates the `game_state` in the `AgentState`.

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

Lore Keeper Agent (LKA)
------------------------

*   **Primary Role:** Maintains the consistency and integrity of the game's
    knowledge graph.  Acts as a "fact-checker" and "librarian."

*   **Key Responsibilities:**

    *   Check new content for consistency with existing lore.
    *   Retrieve information from the knowledge graph for other agents.
    *   Identify and resolve inconsistencies.
    *   Expand the lore based on new information.

*   **Tools:**

    *   `query_knowledge_graph`: Primary tool for accessing the knowledge graph.
    *   `check_consistency`: (Conceptual) Checks for contradictions.
    *   `update_node`: Updates node properties.
    *   `create_relationship`: Creates new relationships.

*   **Interactions:**

    *   Interacts with virtually all other agents to ensure consistency.
    *   Frequently invoked by LangGraph workflows.

Player Onboarding Agent (POA)
------------------------------
* **Primary Role:** Manages the initial player experience, including character creation and the tutorial.

* **Key Responsibilities:**
    *   Handles the initial interaction with the player.
    *   Guides players through character creation.
    *   Manages the tutorial sequence.
    *   Provides personalized support and guidance.
    *   Tracks player progress and preferences.

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
content_copy
download
Use code with caution.
Restructuredtext

13. docs/knowledge_graph.rst (Knowledge Graph - Optional)

.. _knowledge_graph:

================
Knowledge Graph
================

The knowledge graph is the foundation of the Therapeutic Text Adventure (TTA)
game world.  It's a structured representation of all game data, stored in a
Neo4j graph database.  The knowledge graph provides the context for AI agent
actions, narrative generation, and player interactions.

Key Concepts
============

*   **Nodes:** Represent entities or concepts within the game world (e.g.,
    Characters, Locations, Items, Concepts, Events).  Each node has a *label*
    (e.g., `:Character`, `:Location`) that identifies its type.
*   **Relationships:**  Represent connections between nodes (e.g.,
    `LIVES_IN`, `HAS_ITEM`, `RELATED_TO`).  Relationships have a *type*
    (e.g., `LIVES_IN`) that defines the nature of the connection.
*   **Properties:**  Key-value pairs that store data associated with nodes and
    relationships (e.g., `name: "Aella"`, `health: 100`, `strength: 0.8`).

Schema
======

The knowledge graph schema defines the allowed node types, relationship types,
and their properties.  This schema is not fixed; it can evolve as the game
develops.  However, maintaining consistency and adhering to naming conventions
is crucial.

Node Types (Labels)
--------------------

The following table lists the core node types and their properties:

..  This table is a *simplified* representation.  A real implementation
    would have more detailed property definitions (including data types,
    optionality, and descriptions).  See `tta/schema.py` for the
    definitive Pydantic models.

+---------------------+-------------------------------------------------------+
| Node Label          | Properties                                            |
+=====================+=======================================================+
| :Concept            | concept_id (INT, unique), name (STRING), definition (STRING), |
|                     | category (STRING, optional)                           |
+---------------------+-------------------------------------------------------+
| :Metaconcept        | name (STRING, unique), description (STRING),          |
|                     | rules (LIST of STRING, optional),                      |
|                     | considerations (LIST of STRING, optional)             |
+---------------------+-------------------------------------------------------+
| :Scope              | name (STRING, unique), description (STRING, optional) |
+---------------------+-------------------------------------------------------+
| :Character          | character_id (INT, unique), name (STRING),             |
|                     | description (STRING), species (STRING),                |
|                     | personality (STRING), skills (LIST of STRING),       |
|                     | ... (other character attributes)                      |
+---------------------+-------------------------------------------------------+
| :Location           | location_id (INT, unique), name (STRING),              |
|                     | description (STRING), type (STRING),                   |
|                     | ... (other location attributes)                       |
+---------------------+-------------------------------------------------------+
| :Item               | item_id (INT, unique), name (STRING),                  |
|                     | description (STRING), type (STRING),                   |
|                     | ... (other item attributes)                            |
+---------------------+-------------------------------------------------------+
| :Event              | event_id (INT, unique), name (STRING),                 |
|                     | description (STRING), type (STRING),                   |
|                     | time (DATETIME), ... (other event attributes)         |
+---------------------+-------------------------------------------------------+
| :Universe           | universe_id (INT, unique), name (STRING),              |
|                     | description (STRING), physical_laws (STRING),         |
|                     | magic_system (STRING, optional),                       |
|                     | technology_level (STRING)                              |
+---------------------+-------------------------------------------------------+
| :World              | world_id (INT, unique), name (STRING),                  |
|                     | description (STRING), environment (STRING)             |
+---------------------+-------------------------------------------------------+
| :Player             | player_id (INT, unique), username (STRING, unique),   |
|                     | ... (other player attributes)                          |
+---------------------+-------------------------------------------------------+
| ...                 | (Other node types as needed)                           |
+---------------------+-------------------------------------------------------+

Relationship Types
--------------------
The following table lists *some* of the core relationship types.  This is
*not* exhaustive; new relationship types will be added as needed.

+-----------------------+----------------------------------------------------+
| Relationship Type     | Description                                        |
+=======================+====================================================+
| :LIVES_IN             | Connects a Character to a Location.                |
+-----------------------+----------------------------------------------------+
| :LOCATED_IN           | Connects a Location to a World or Universe.       |
+-----------------------+----------------------------------------------------+
| :HAS_ITEM             | Connects a Character to an Item.                   |
+-----------------------+----------------------------------------------------+
| :RELATED_TO           | A general relationship between Concepts.           |
+-----------------------+----------------------------------------------------+
| :PART_OF              | Indicates a part-whole relationship.              |
+-----------------------+----------------------------------------------------+
| :IS_A                 | Indicates a type/subtype relationship.             |
+-----------------------+----------------------------------------------------+
| :KNOWS                | Connects two Characters who know each other.      |
+-----------------------+----------------------------------------------------+
| :CONTAINS_EVENT       | Connects a Timeline to an Event.                   |
+-----------------------+----------------------------------------------------+
| :PRECEDES             | Orders events within a Timeline.                   |
+-----------------------+----------------------------------------------------+
| :APPLIES_TO           | Connects a Metaconcept to a Scope.                 |
+-----------------------+----------------------------------------------------+
| ...                   | (Many other relationship types)                     |
+-----------------------+----------------------------------------------------+

Relationship Properties
-------------------------

Relationships can also have properties, just like nodes.  Some common
relationship properties include:

*   `strength`: (FLOAT) Represents the strength or intensity of the
    relationship (e.g., for friendships, rivalries, or the influence of one
    concept on another).
*   `start_time`: (DATETIME) The time when the relationship began.
*   `end_time`: (DATETIME) The time when the relationship ended (if applicable).
*   `relation_type`: (STRING)  A more specific description of the relationship
    type (used with general relationships like `RELATED_TO`).
*   `source`: (STRING)  Indicates the source of the information about the
    relationship (e.g., "player observation," "AI inference").
* `inferred`: (BOOLEAN) Indicates whether the relationship was inferred by an AI agent.

Cypher Conventions
==================

*   **Parameterized Queries:** Always use parameterized queries to prevent
    Cypher injection vulnerabilities and improve performance.
*   **Transactions:**  Perform database operations within transactions to
    ensure data integrity.
*   **Indexing:** Create indexes on frequently queried node properties.
*   **Naming Conventions:**
    *   Node Labels: `CamelCase` (e.g., `Character`, `Location`)
    *   Relationship Types: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `LIVES_IN`)
    *   Properties: `snake_case` (e.g., `character_name`, `location_description`)
*   **Avoid UNWIND (Generally):**  Use more specific Cypher patterns or multiple
    queries instead of `UNWIND` when possible.
* **Clarity and Documentation:** Write clear, concise, and well-documented Cypher code.

Example Cypher Queries
======================

Creating a Node:

.. code-block:: cypher

    CREATE (c:Character {id: "char001", name: "Aella", species: "Elf", health: 100})
    RETURN c

Creating a Relationship:

.. code-block:: cypher

    MATCH (c:Character {id: "char001"})
    MATCH (l:Location {id: "loc001"})
    CREATE (c)-[:LIVES_IN {start_time: datetime("2024-01-01T10:00:00Z")}]->(l)

Retrieving a Node by ID:

.. code-block:: cypher

    MATCH (c:Character {id: "char001"})
    RETURN c

Updating Node Properties:

.. code-block:: cypher

    MATCH (c:Character {id: "char001"})
    SET c.health = 90, c.mood = "pensive"

Finding Characters in a Location:

.. code-block:: cypher

    MATCH (c:Character)-[:LOCATED_IN]->(l:Location {name: "Whispering Woods"})
    RETURN c

Finding Related Concepts:

.. code-block:: cypher

    MATCH (c1:Concept {name: "Justice"})-[:RELATED_TO]-(c2:Concept)
    RETURN c2

These examples demonstrate basic Cypher operations. More complex queries will
be used for advanced features like CoRAG and dynamic content generation.
content_copy
download
Use code with caution.
Restructuredtext

14. README.md (Project README - High-Level Overview)

# Therapeutic Text Adventure (TTA)

## Overview

The Therapeutic Text Adventure (TTA) is an AI-driven text adventure game
designed to provide a personalized and potentially therapeutic experience for
players.  The game leverages a knowledge graph (Neo4j), a large language model
(Qwen2.5), and a robust agent architecture (LangGraph, LangChain) to create a
dynamic and engaging world.

**Key Features:**

*   **AI-Driven Narrative:**  The game's story and content are dynamically
    generated by AI agents, adapting to player choices and creating a unique
    experience for each playthrough.
*   **Knowledge Graph:**  A Neo4j graph database stores all game data,
    including concepts, characters, locations, events, and their relationships.
    This provides a rich and interconnected world for the AI agents to reason
    about.
*   **Agent Architecture:**  Specialized AI agents (Input Processor, Narrative
    Generator, World Builder, etc.) collaborate to handle different aspects of
    the game, from parsing player input to generating dialogue and managing
    the game world.
*   **Therapeutic Integration:**  The game subtly integrates therapeutic
    concepts and techniques, encouraging self-reflection, emotional processing,
    and personal growth.  *TTA is not a replacement for professional therapy.*
*   **Player Agency:**  Player choices have meaningful consequences, shaping
    the narrative and the game world.
*   **Infinite Multiverse:** The game is set within an infinite multiverse,
    allowing for endless exploration and diverse experiences.
* **Local LLM:** Uses a locally hosted LLM (Qwen2.5) for enhanced privacy.

## Technology Stack

*   **Neo4j:** Graph database for storing the knowledge graph.
*   **Python:** Primary programming language.
*   **LangChain:** Framework for building LLM applications.
*   **LangGraph:** Framework for orchestrating AI agent workflows.
*   **Qwen2.5:** Large Language Model (hosted locally using LM Studio).
*   **Pydantic:** Data validation and schema definition.
* **Guidance** Library for controlling LLM output.
*   **spaCy:** Natural Language Processing library.
* **TensorFlow** Machine Learning library.
*   **FastAPI:** (Potentially) For creating a web interface.

## Getting Started

**Prerequisites:**

*   Python 3.10+
*   Poetry (for dependency management)
*   Neo4j Desktop (or a Neo4j AuraDB instance)
*   LM Studio (for local LLM hosting)
*   A suitable code editor (VS Code with Dev Containers recommended)
*   Git

**Installation:**

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Set up the development environment:**
    *   It is highly recommended to use the provided VS Code Dev Container. This will automatically set up a consistent development environment with all necessary dependencies. Open the project folder in VS Code, and it should prompt you to reopen in the container.
    *   If you are *not* using the Dev Container, you will need to manually install the dependencies using Poetry:
      ```bash
      poetry install
      ```
3.  **Configure environment variables:**

    *   Create a `.env` file in the project root.
    *   Add the necessary environment variables (see `.env.example` for a template).  *At a minimum, you'll need to configure the Neo4j connection settings.*
    *   **Important:**  The `.env` file should *never* be committed to version control.  It contains sensitive information (like API keys).

4.  **Run the game:**

    ```bash
    poetry run python tta/main.py
    ```
    (Or, if you're using the Dev Container, simply run `python tta/main.py` within the container's terminal.)

## Documentation

Detailed documentation is available within the codebase itself, using
docstrings formatted for Sphinx.  You can generate HTML documentation using:

```bash
# (From the project root)
cd docs
make html  # Or, on Windows:  make.bat html
content_copy
download
Use code with caution.
Markdown

The generated HTML documentation will be in docs/_build/html.

Contributing

Contributions to the TTA project are welcome! Please see the CONTRIBUTING.md
file (to be created) for guidelines.

License

This project is licensed under the MIT License.

**15. `.env.example` (Environment Variable Template)**
content_copy
download
Use code with caution.
.env.example - Template for environment variables
--- Neo4j Database ---

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password # !!CHANGE THIS!!

--- LLM Settings (LM Studio) ---

LLM_API_BASE=http://localhost:1234/v1
LLM_API_KEY=not-needed # Placeholder for local LLMs
LLM_MODEL_NAME=qwen2.5-0.5b-instruct # Or your chosen model

--- Other API Keys (Optional - Add as needed) ---
OPENAI_API_KEY=your_openai_key # If you use OpenAI (not recommended for privacy)
TAVILY_API_KEY=your_tavily_key # If you use Tavily for web search
... other API keys ...
--- Game Settings ---
(Add any game-specific settings here)
**16.  Testing Strategy (docs/testing.rst - Optional, but HIGHLY Recommended)**

```restructuredtext
.. _testing:

==============
Testing Strategy
==============

This document outlines the testing strategy for the Therapeutic Text
Adventure (TTA) project.  Thorough testing is crucial for ensuring the
quality, reliability, and stability of the game.  We employ a multi-layered
approach, including:

*   **Unit Tests:**  Testing individual functions and classes in isolation.
*   **Integration Tests:**  Testing the interactions between different
    components (e.g., AI agents, the knowledge graph).
*   **End-to-End Tests:**  Testing complete game scenarios from the player's
    perspective.
*   **User Testing:**  Gathering feedback from real players.

Testing Framework
=================

We use the `unittest` framework for structuring and running tests.  Tests are
located in the `tta/tests` directory.

Running Tests
=============

To run all tests:

```bash
python -m unittest discover tta/tests
content_copy
download
Use code with caution.

To run tests for a specific module (e.g., ipa.py):

python -m unittest tta/tests/test_ipa.py
content_copy
download
Use code with caution.
Bash
Test Organization

Each module should have a corresponding test file (e.g., ipa.py has
test_ipa.py).

Test files should contain test classes (e.g., TestIPA) that inherit from
unittest.TestCase.

Each test method within a test class should focus on testing a specific
aspect of the code.

Test method names should be descriptive and start with test_ (e.g.,
test_parse_move_command, test_create_character).

Use the setup and teardown methods to create a consistent environment.

Types of Tests
Unit Tests

Unit tests focus on testing individual functions and classes in isolation.
They verify that each unit of code behaves as expected, given specific inputs
and conditions. Examples:

Testing the process_input function in ipa.py with various player
inputs.

Testing the create_node and get_node_by_id functions in
neo4j_utils.py with different node types and properties.

Testing individual methods of an AI agent class.

Integration Tests

Integration tests verify that different components of the system work together
correctly. Examples:

Testing the interaction between the IPA and the NGA.

Testing that an AI agent can correctly query and update the Neo4j
knowledge graph.

Testing that a LangGraph workflow executes as expected.

End-to-End Tests

End-to-end tests simulate complete game scenarios from the player's
perspective. They verify that the entire system works together to create the
intended gameplay experience. Examples:

Testing a complete character creation sequence.

Testing a simple exploration scenario (e.g., moving between locations,
examining objects).

Testing a conversation with an NPC.

Testing a combat encounter.

User Testing

User testing involves gathering feedback from real players. This is crucial
for identifying usability issues, gameplay imbalances, and areas for
improvement.

Test Coverage

We strive for high test coverage, meaning that a large percentage of the
codebase is executed during testing. Tools like coverage.py can be used to
measure test coverage and identify areas that need more testing.

Continuous Integration (Future)

We plan to implement continuous integration (CI) to automatically run tests
whenever code is pushed to the repository. This will help ensure that new
changes don't introduce regressions.

Writing Good Tests

Test-Driven Development (TDD): Consider writing tests before writing
the code. This helps clarify requirements and ensures that the code is
testable.

Keep Tests Small and Focused: Each test should focus on a specific
aspect of the code.

Use Descriptive Names: Test names should clearly indicate what is
being tested.

Use Assertions: Use assertion methods (e.g., assertEqual,
assertTrue, assertRaises) to verify that the code behaves as expected.

Handle Edge Cases: Test with a variety of inputs, including edge
cases and invalid inputs.

Isolate Tests: Tests should be independent of each other. One test
should not affect the outcome of another test.

Mock External Dependencies (When Appropriate): For unit tests, consider
using mocking to isolate the code being tested from external dependencies
(e.g., the Neo4j database). However, for integration tests, you should
test the actual interaction with external systems.

Don't Over-Mock: Avoid excessive mocking, as it can make tests brittle and less representative of real-world behavior.

Test for Errors: Ensure that your code handles errors gracefully, and write tests to verify this.

This comprehensive testing strategy will help ensure the quality and reliability of the TTA project.

This completes the 8k token documentation expansion. I've covered the core files, provided detailed explanations, included code examples, and formatted everything for readability and maintainability. I've also added a testing strategy document. Remember to adapt and expand this documentation as your project evolves. Good documentation is an ongoing process.
content_copy
download
Use code with caution.