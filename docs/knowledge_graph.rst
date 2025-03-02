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