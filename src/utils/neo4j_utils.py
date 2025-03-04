Okay, let's create the tools.py file with the execute_query function that your ipa.py script needs. Based on how ipa.py is using it, and your schema, here's an improved tools.py file:

# tools.py
"""
This file contains tools that interact with the Neo4j database for the TTA game.

It includes:
    - `execute_query`:  Executes a Cypher query and returns structured data.
    - `run_cypher_query`: Executes a Cypher query and returns raw string output (for Langchain Tool).
    - `neo4j_tool`: Langchain Tool object for `run_cypher_query`.

For more information on Langchain tools, see:
https://python.langchain.com/docs/modules/agents/tools/
For more information on Neo4jGraph in Langchain, see:
https://python.langchain.com/docs/integrations/graphs/neo4j_cypher
"""

from langchain_community.graphs import Neo4jGraph
from langchain import Tool
from src.utils.neo4j_utils import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from typing import List, Dict, Any

graph = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD
)

def execute_query(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Executes a Cypher query against the Neo4j database and returns a list of dictionaries.

    This function is designed to return structured data suitable for use by the IPA
    and other agents in the TTA game. It handles potential errors and returns an empty
    list if the query fails.

    Args:
        query: The Cypher query string to execute.
        params: An optional dictionary of parameters to pass to the query.

    Returns:
        A list of dictionaries, where each dictionary represents a row in the query result.
        Keys of the dictionary are the column names from the Cypher query.
        Returns an empty list if there are no results or if an error occurs.
    """
    try:
        result = graph.query(query, params)
        return result # Langchain Neo4jGraph already returns a list of dictionaries
    except Exception as e:
        print(f"Error executing query: {e}") # Print error for visibility, consider logging as well
        return []  # Return empty list on error

def run_cypher_query(query: str) -> str:
    """
    Runs a Cypher query against the Neo4j database and returns the raw string output.

    This function is primarily intended for use as a Langchain Tool, where string output
    is often required for agent interaction. For structured data, use `execute_query`.

    Args:
        query: The Cypher query string to execute.

    Returns:
        A string representation of the query result. Returns an error message string
        if the query fails.
    """
    try:
        result = graph.query(query)
        return str(result)  # Convert to string for Langchain Tool compatibility
    except Exception as e:
        return f"Error executing query: {e}"

neo4j_tool = Tool(
    name="Neo4j Cypher Query",
    func=run_cypher_query,
    description="Useful for executing Cypher queries against the Neo4j database. "
                "Input should be a valid Cypher query. Output is a string representing the query results."
)

if __name__ == '__main__':
    # Example Usage (for testing tools.py independently)
    example_query = """
    MATCH (n:Concept)
    WHERE n.name = 'Justice'
    RETURN n.name AS concept_name, n.definition AS concept_definition
    """

    results = execute_query(example_query)
    print("Structured Query Results (execute_query):")
    if results:
        for row in results:
            print(row)
    else:
        print("No results or error occurred with execute_query.")

    raw_output = run_cypher_query(example_query)
    print("\nRaw Query Output (run_cypher_query):")
    print(raw_output)
