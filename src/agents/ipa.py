# tta/ipa.py

"""
Input Processor Agent (IPA) for the Therapeutic Text Adventure (TTA).

The IPA is responsible for:

1.  **Parsing Player Input:**  Breaking down the player's raw text input into
    its constituent parts (words, phrases).
2.  **Identifying Intent:** Determining the player's intention (e.g., move,
    examine, talk, quit).  This is the primary function of the IPA.
3.  **Extracting Key Entities:**  Identifying relevant entities mentioned in the
    input, such as:
    *   Direction (for movement commands)
    *   Object (for examination or interaction)
    *   NPC (for conversations)
4.  **Structuring Data:** Transforming the parsed input into a structured format
    (JSON) that can be easily used by other agents.
5. **Handling Ambiguity/Errors:**  Dealing with unclear or invalid input
    gracefully, potentially prompting the player for clarification.
6. **CoRAG Integration:** Using Chain-of-Retrieval Augmented Generation (CoRAG)
    to iteratively refine its understanding of the player's input by querying
    the knowledge graph.

The IPA uses a combination of:

*   **LangChain:** For prompt templates, LLM interaction, and output parsing.
*   **Qwen2.5:**  The Large Language Model (LLM) that performs the core
    natural language understanding.
*   **Neo4j (via tools):**  For querying the knowledge graph to resolve
    ambiguities and identify entities.
*   **Pydantic:** For defining the expected output schema (JSON).

"""

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
import json
import logging
from typing import Dict, Optional
try:
    from tta.utils.neo4j_utils import execute_query  # Import Neo4j utility functions
except ImportError as e:
    logging.error("Could not import 'execute_query' from 'tta.utils.neo4j_utils'. Please ensure the module exists and is correctly installed.")
    raise e
from tta import settings  # Import settings
from tta.schema import QueryKnowledgeGraphInput, QueryKnowledgeGraphOutput  # Import schemas

# --- 1. LLM Setup (LM Studio) ---
llm = ChatOpenAI(
    openai_api_base=settings.LLM_API_BASE,  # Your LM Studio endpoint
    api_key=settings.LLM_API_KEY,  # Placeholder, not used by LM Studio
    model=settings.LLM_MODEL_NAME  # Optional, but good practice to specify.
)

# --- 2. Prompt Template ---
# Note:  This is a *simplified* prompt for initial demonstration.
#        A production-ready prompt would be much more detailed and robust.
prompt_template = PromptTemplate.from_template(
    """You are the Input Processor Agent (IPA) for a text adventure game.
    Your task is to analyze the player's input and determine their intent.

    Possible Intents:
    - look:      The player wants to observe their surroundings (e.g., "look", "look around").
    - move:      The player wants to move in a specific direction (e.g., "go north", "north").
    - examine:   The player wants to examine an object more closely (e.g., "examine table").
    - talk to:   The player wants to initiate dialogue with a character (e.g., "talk to Elara").
    - quit:      The player wants to quit the game (e.g., "quit", "exit").
    - unknown:   The player's intent cannot be determined from the input.

    Output Format:
    Return a JSON object, and NOTHING ELSE.  The JSON object MUST have an "intent" key.
    The "direction", "object", and "npc" keys are OPTIONAL and should ONLY be included
    if they are relevant to the intent.

    {{
      "intent": "...",     // REQUIRED. One of the intents listed above.
      "direction": "...",  // OPTIONAL.  One of: "north", "south", "east", "west". Include ONLY if intent is "move".
      "object": "...",     // OPTIONAL.  The object the player wants to examine. Include ONLY if intent is "examine".
      "npc": "..."        // OPTIONAL.  The name of the NPC the player wants to talk to. Include ONLY if intent is "talk to".
    }}

    Examples:

    Player Input: look around
    Output: {{"intent": "look"}}

    Player Input: go north
    Output: {{"intent": "move", "direction": "north"}}

    Player Input: examine the rusty key
    Output: {{"intent": "examine", "object": "rusty key"}}

    Player Input: talk to the blacksmith
    Output: {{"intent": "talk to", "npc": "blacksmith"}}

    Player Input: quit
    Output: {{"intent": "quit"}}

    Player Input: asdfghjkl
    Output: {{"intent": "unknown"}}

    Player Input: {player_input}
    Output:
    """
)

# --- 3. Output Parser (String Output) ---
output_parser = StrOutputParser()

# --- 4. LangChain Chain (The IPA) ---
ipa_chain = prompt_template | llm | output_parser

# --- 5. CoRAG Function (Example - Simplified) ---
# In a real implementation, this would use LangGraph for iterative calls.
def perform_corag(initial_intent: Dict, player_input: str) -> Dict:
    """
    Performs a simplified version of Chain-of-Retrieval Augmented Generation (CoRAG)
    to refine the IPA's understanding of the player's input.

    Args:
        initial_intent: The initial intent dictionary from the IPA.
        player_input: The original player input string.

    Returns:
        A refined intent dictionary.
    """
    refined_intent = initial_intent.copy()

    if initial_intent["intent"] == "examine" and initial_intent["object"]:
        # Example: If the intent is "examine", try to get more info about the object.
        object_name = initial_intent["object"]
        query = """
            MATCH (o:Item {name: $object_name})  // Assuming objects are Items
            RETURN o
            LIMIT 1
        """
        params = {"object_name": object_name}
        try:
            result = execute_query(query, params)
            if result:
                # Object found in the knowledge graph. Add details to the intent.
                object_data = result[0]['o']
                refined_intent["object_details"] = object_data  # Add details
                logging.debug(f"CoRAG: Found object details: {object_data}")
            else:
                logging.debug(f"CoRAG: Object '{object_name}' not found in knowledge graph.")
        except Exception as e:
            logging.error(f"CoRAG: Error during knowledge graph query: {e}")

    elif initial_intent["intent"] == "talk to" and initial_intent["npc"]:
        # Example: If intent is "talk to", try to get character info
        npc_name = initial_intent["npc"]
        query = """
            MATCH (c:Character {name: $npc_name})
            RETURN c
            LIMIT 1
        """
        params = {"npc_name": npc_name}
        try:
            result = execute_query(query, params)
            if result:
                character_data = result[0]['c']
                refined_intent["npc_details"] = character_data
                logging.debug(f"CoRAG: Found character details: {character_data}")
            else:
                logging.debug(f"CoRAG: NPC '{npc_name}' not found in knowledge graph.")
        except Exception as e:
            logging.error(f"CoRAG: Error during knowledge graph query: {e}")

    # Add more CoRAG steps as needed for other intents and scenarios.

    return refined_intent

# --- 6. Main Input Processing Function ---

def process_input(player_input: str) -> Dict:
    """
    Processes the player's input, determines the intent, extracts relevant
    information, and potentially uses CoRAG to refine the understanding.

    Args:
        player_input: The raw text input from the player.

    Returns:
        A dictionary representing the parsed intent, potentially with additional
        information from CoRAG.  Returns {"intent": "unknown"} if the input
        cannot be parsed.
    """
    response_str = ipa_chain.invoke({"player_input": player_input})
    # logging.debug(f"Raw LLM output: {response_str}")  # Uncomment for debugging

    try:
        response_dict = json.loads(response_str)  # Parse the JSON string

        # --- Basic Validation ---
        if "intent" not in response_dict:
            return {"intent": "unknown"}

        # Ensure valid intent
        valid_intents = ["look", "move", "examine", "talk to", "quit", "unknown"]
        if response_dict["intent"] not in valid_intents:
            return {"intent": "unknown"}

        # Further validation and cleanup based on intent:
        if response_dict["intent"] == "move":
            if "direction" not in response_dict or response_dict["direction"] not in ["north", "south", "east", "west"]:
                return {"intent": "unknown"}

        # Remove extraneous keys.
        valid_keys = ["intent"]
        if response_dict["intent"] == "move":
            valid_keys.append("direction")
        elif response_dict["intent"] == "examine":
            valid_keys.append("object")
        elif response_dict["intent"] == "talk to":
            valid_keys.append("npc")

        # Create a new dictionary with only the necessary keys
        clean_response = {key: response_dict[key] for key in valid_keys if key in response_dict}

        # --- CoRAG ---
        refined_response = perform_corag(clean_response, player_input)

        return refined_response

    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from LLM response: {response_str}")
        return {"intent": "unknown"}

# --- 7. Unit Tests (Example - move to test_ipa.py) ---
if __name__ == '__main__':
    import unittest

    class TestIPA(unittest.TestCase):
        def test_process_input(self):
            test_cases = [
                ("look around", {"intent": "look"}),
                ("go north", {"intent": "move", "direction": "north"}),
                ("examine the rusty key", {"intent": "examine", "object": "the rusty key"}),
                ("talk to the blacksmith", {"intent": "talk to", "npc": "the blacksmith"}),
                ("quit", {"intent": "quit"}),
                ("invalid input", {"intent": "unknown"}),
            ]

            for player_input, expected_output in test_cases:
                with self.subTest(player_input=player_input):
                    actual_output = process_input(player_input)
                    self.assertEqual(actual_output, expected_output)

    unittest.main()