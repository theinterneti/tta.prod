# tta/main.py

from .settings import *  # Import all settings

print(f"Using Neo4j URI: {NEO4J_URI}")
print(f"Using LLM API Base: {LLM_API_BASE}")
# ... use other settings as needed

# --- Main Game Loop ---
# This is where the game loop would go.  For now, we'll just print a message.
print("Welcome to the Therapeutic Text Adventure!")

import sys
sys.path.append('/workspaces/tta.prod', '/workspaces/tta.prod/src')
"""
Main game loop for the Therapeutic Text Adventure (TTA).

This module contains the main entry point for the game and the core
game loop.  It handles:

*   Initializing the game state.
*   Getting player input.
*   Processing player input (using the IPA).
*   Generating narrative responses (using the NGA).
*   Updating the game state.
*   Presenting output to the player.
*   Handling game termination.

The current implementation is a *very* basic prototype.  It demonstrates
the interaction between the player, the IPA, and a simplified NGA.  It does
*not* yet include the full complexity of the knowledge graph, CoRAG,
multiple agents, or LangGraph integration.  These are the next steps in
development.
"""

from agents.ipa import process_input
from agents.narrative_generator import generate_narrative
from schema import AgentState, GameState, CharacterState
from typing import Dict

def main():
    """
    The main function for the TTA game.  This contains the core game loop.
    """
    print("Welcome to the Therapeutic Text Adventure Prototype!")

    # --- Initialize Game State (Simplified for now) ---
    # In a full implementation, this would load data from the knowledge graph.
    initial_game_state = GameState(
        current_location_id="village_square",
        nearby_characters=["npc_blacksmith"],
        world_state={}
    )

    initial_character_states = {
        "npc_blacksmith": CharacterState(
            character_id="npc_blacksmith",
            name="Torvin Stonehand",
            location_id="village_square",
            health=100,
            mood="neutral",
            relationship_scores={}
        )
    }

    initial_agent_state = AgentState(
        current_agent="ipa",
        game_state=initial_game_state,
        character_states=initial_character_states,
        conversation_history=[],
        metaconcepts=["Prioritize Player Agency", "Maintain Narrative Consistency"],
        memory=[],
        prompt_chain=[],
        response=""
    )

    print("You are standing in a small, quiet village square. Sunlight filters through the leaves of an ancient oak tree.")  # Initial description
    print("Type 'look' to examine your surroundings, 'quit' to exit, 'go [direction]' to move, or 'examine [object]' to examine.")

    current_state = initial_agent_state  # Set the starting state.

    while True:
        player_input = input("> ").strip()  # Get player input
        current_state.player_input = player_input  # Update the state with the input.

        # --- Process Input (IPA) ---
        parsed_input = process_input(player_input)
        current_state.parsed_input = parsed_input  # Update the state.

        if parsed_input["intent"] == "quit":
            print("Goodbye!")
            break

        # --- Generate Narrative (NGA - Simplified) ---
        # In a full implementation, LangGraph would handle agent switching.
        elif parsed_input["intent"] == "look":
            # Simplified handling of the "look" intent.
            current_state.current_agent = "nga"  # Pretend we switched to the NGA.
            nga_response = generate_narrative(current_state)
            print(nga_response["response"])
            current_state.response = nga_response["response"]  # Update the state

        elif parsed_input["intent"] == "move":
            current_state.current_agent = "nga"  # Pretend we switched to the NGA
            if "direction" in parsed_input:
                nga_response = generate_narrative(current_state)
                print(nga_response["response"])
                current_state.response = nga_response["response"]  # Update the state
            else:
                print("Move where?")

        elif parsed_input["intent"] == "examine":
            current_state.current_agent = "nga"
            if "object" in parsed_input:
                nga_response = generate_narrative(current_state)
                print(nga_response["response"])
                current_state.response = nga_response["response"]
            else:
                print("Examine what?")

        elif parsed_input["intent"] == "talk to":
            current_state.current_agent = "nga"
            if "npc" in parsed_input:
                nga_response = generate_narrative(current_state)
                print(nga_response["response"])
                current_state.response = nga_response["response"]
            else:
                print("Talk to whom?")
        else:
            print("I don't understand that command.")

if __name__ == "__main__":
    main()