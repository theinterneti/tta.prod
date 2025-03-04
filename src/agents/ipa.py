"""
Input Processor Agent (IPA) for the Therapeutic Text Adventure (TTA).

[ ... Docstring from original code ... ]
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import PydanticOutputParser
from langchain_openai import ChatOpenAI

# from pydantic import BaseModel, Field # No longer needed here - imported from schema.py

try:
    from tools import execute_query  # Import Neo4j utility functions
except ImportError as e:
    logging.error(
        "Could not import 'execute_query' from 'tools.py'. "
        "Please ensure the module exists and is correctly placed in the 'tta' directory."
    )
    raise e
import settings  # Import settings

from src.schema import (  # Import schemas
    IntentSchema,
    QueryKnowledgeGraphInput,
    QueryKnowledgeGraphOutput,
)

# --- 1. Logging Setup ---
logger = logging.getLogger(__name__)  # Set up logger for this module
logger.setLevel(logging.DEBUG if settings.DEBUG_MODE else logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


# --- 2. Define Pydantic Output Schema ---
# IntentSchema is now imported from src.schema


# --- 3. LLM Setup (LM Studio) ---
llm = ChatOpenAI(
    openai_api_base=settings.LLM_API_BASE,  # Your LM Studio endpoint
    api_key=settings.LLM_API_KEY,  # Placeholder, not used by LM Studio
    model=settings.LLM_MODEL_NAME,  # Optional, but good practice to specify.
    temperature=0,  # Set temperature to 0 for more deterministic output
)

# --- 4. Output Parser (Pydantic) ---
output_parser = PydanticOutputParser(pydantic_object=IntentSchema)

# --- 5. Enhanced Prompt Template ---
prompt_template = PromptTemplate(
    template="""You are the Input Processor Agent (IPA) for a therapeutic text adventure game.
    Your task is to analyze the player's text input and accurately determine their game intent.

    **Instructions:**

    1.  **Identify Intent:** Determine the player's primary intent from the input. The possible intents are strictly limited to the following categories:
        *   `look`:      The player wants to observe their current surroundings. Keywords: "look", "around", "describe", "environment".
        *   `move`:      The player wants to move in a direction. Keywords: "go", "move", "travel", "north", "south", "east", "west", and direction words.
        *   `examine`:   The player wants to examine a specific object in more detail. Keywords: "examine", "look at", "inspect", "describe", "check", and object names.
        *   `talk to`:   The player wants to initiate a conversation with a Non-Player Character (NPC). Keywords: "talk", "speak", "converse", "greet", "ask", "tell", "with", "to", and NPC names.
        *   `quit`:      The player wants to end the game session. Keywords: "quit", "exit", "end", "stop", "leave game".
        *   `unknown`:   If the player's intent cannot be clearly determined or does not fall into the above categories, classify it as "unknown".  This is for gibberish or unsupported commands.

    2.  **Extract Entities (Conditional):**
        *   If the intent is `move`, extract the `direction` (north, south, east, or west).
        *   If the intent is `examine`, extract the `object` name.
        *   If the intent is `talk to`, extract the `npc` name.
        *   Do NOT extract entities for `look`, `quit`, or `unknown` intents.

    3.  **Output Format:**  You MUST respond with a valid JSON object that conforms to the following Pydantic schema:

    ```json
    {output_format}
    ```

    Ensure the JSON object includes the REQUIRED "intent" key.
    Include "direction", "object", and "npc" keys ONLY when they are relevant to the identified intent (move, examine, talk to, respectively).  Leave them out for other intents.

    **Examples:**

    *   Player Input: "look around"  Output: `{{"intent": "look"}}`
    *   Player Input: "go north"     Output: `{{"intent": "move", "direction": "north"}}`
    *   Player Input: "examine the rusty key" Output: `{{"intent": "examine", "object": "rusty key"}}`
    *   Player Input: "talk to Elara" Output: `{{"intent": "talk to", "npc": "Elara"}}`
    *   Player Input: "quit game"    Output: `{{"intent": "quit"}}`
    *   Player Input: "xyzzy"        Output: `{{"intent": "unknown"}}`

    **Player Input:** {player_input}
    **Output (JSON):**
    """,
    input_variables=["player_input"],
    partial_variables={
        "output_format": output_parser.get_format_instructions()
    },  # Include output format instructions in prompt
)

# --- 6. LangChain Chain (The IPA) ---
ipa_chain = prompt_template | llm | output_parser  # Use PydanticOutputParser


# --- 7. CoRAG Function (Refined) ---
def perform_corag(initial_intent: IntentSchema, player_input: str) -> IntentSchema:
    """
    Performs Chain-of-Retrieval Augmented Generation (CoRAG) to refine the IPA's
    understanding of the player's input by querying the knowledge graph.

    Args:
        initial_intent: The initial IntentSchema object from the IPA.
        player_input: The original player input string.

    Returns:
        A refined IntentSchema object.
    """
    refined_intent_dict = (
        initial_intent.dict()
    )  # Convert Pydantic object to dict for easier modification

    if refined_intent_dict["intent"] == "examine" and refined_intent_dict["object"]:
        object_name = refined_intent_dict["object"]
        query_input = QueryKnowledgeGraphInput(
            query_type="retrieve_entity_by_name",
            entity_label="Item",  # Assuming objects are Items
            entity_name=object_name,
            properties=[
                "name",
                "description",
                "type",
                "rarity",
                "material",
            ],  # Example properties to retrieve
        )
        try:
            query_output = execute_query(
                query=query_input.query, params=query_input.params
            )
            if query_output:
                object_data_list = QueryKnowledgeGraphOutput.parse_neo4j_output(
                    query_output
                )  # Use schema for output parsing
                if object_data_list:  # Check if list is not empty after parsing
                    object_data = object_data_list[
                        0
                    ].dict()  # Take the first result and convert to dict
                    refined_intent_dict["object_details"] = (
                        object_data  # Add details to intent
                    )
                    logger.debug(
                        f"CoRAG: Found object details for '{object_name}': {object_data}"
                    )
                else:
                    logger.debug(
                        f"CoRAG: No valid object data parsed from KG for '{object_name}'."
                    )
            else:
                logger.debug(
                    f"CoRAG: Object '{object_name}' not found in knowledge graph."
                )
        except Exception as e:
            logger.error(
                f"CoRAG: Error during knowledge graph query for object '{object_name}': {e}"
            )

    elif refined_intent_dict["intent"] == "talk to" and refined_intent_dict["npc"]:
        npc_name = refined_intent_dict["npc"]
        query_input = QueryKnowledgeGraphInput(
            query_type="retrieve_entity_by_name",
            entity_label="Character",
            entity_name=npc_name,
            properties=[
                "name",
                "description",
                "species",
                "role",
                "faction",
            ],  # Example character properties
        )
        try:
            query_output = execute_query(
                query=query_input.query, params=query_input.params
            )
            if query_output:
                character_data_list = QueryKnowledgeGraphOutput.parse_neo4j_output(
                    query_output
                )  # Use schema for output parsing
                if character_data_list:  # Check if list is not empty after parsing
                    character_data = character_data_list[
                        0
                    ].dict()  # Take the first result and convert to dict
                    refined_intent_dict["npc_details"] = character_data
                    logger.debug(
                        f"CoRAG: Found character details for '{npc_name}': {character_data}"
                    )
                else:
                    logger.debug(
                        f"CoRAG: No valid character data parsed from KG for '{npc_name}'."
                    )
            else:
                logger.debug(f"CoRAG: NPC '{npc_name}' not found in knowledge graph.")
        except Exception as e:
            logger.error(
                f"CoRAG: Error during knowledge graph query for NPC '{npc_name}': {e}"
            )

    return IntentSchema(**refined_intent_dict)  # Return as Pydantic object


# --- 8. Main Input Processing Function ---
def process_input(player_input: str) -> IntentSchema:
    """
    Processes the player's input, determines the intent, extracts relevant
    information, and uses CoRAG to refine the understanding.

    Args:
        player_input: The raw text input from the player.

    Returns:
        An IntentSchema object representing the parsed intent, potentially with
        additional information from CoRAG. Returns IntentSchema with intent
        "unknown" if the input cannot be parsed.
    """
    logger.debug(f"Processing player input: '{player_input}'")
    try:
        response: IntentSchema = ipa_chain.invoke(
            {"player_input": player_input}
        )  # Chain now returns Pydantic object
        logger.debug(f"Initial LLM Intent: {response.to_json()}")

        # --- CoRAG ---
        refined_response: IntentSchema = perform_corag(response, player_input)
        logger.debug(f"Refined Intent after CoRAG: {refined_response.to_json()}")
        return refined_response

    except Exception as e:  # Catch any exceptions during processing
        logger.error(f"Error processing input: '{player_input}'. Error: {e}")
        logger.error("Returning unknown intent.")
        return IntentSchema(
            intent="unknown"
        )  # Return unknown intent as Pydantic object


# --- 9. Unit Tests (Moved to test_ipa.py) ---
# Example of how to run from command line:  python -m unittest test_ipa.py
