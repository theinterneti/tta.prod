## langchain tools
# This file contains tools that interact with the Neo4j database.
# You can add more tools here, e.g., for specific graph operations.
#
# The `run_cypher_query` function executes a Cypher query against the Neo4j database.
# The `neo4j_tool` is a Tool object that can be used in the Langchain environment.
#
# For more information on Langchain tools, see the documentation:
# https://langchain.readthedocs.io/en/latest/tools.html
#
# For more information on Neo4jGraph, see the documentation:
# https://langchain.readthedocs.io/en/latest/graphs.html
#



from langchain_community.graphs import Neo4jGraph
from langchain_core.tools import Tool
from src.utils.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

graph = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD
)

def run_cypher_query(query: str) -> str:
    """Runs a Cypher query against the Neo4j database."""
    try:
        result = graph.query(query)
        return str(result)  # Convert to string for easier handling
    except Exception as e:
        return f"Error executing query: {e}"

neo4j_tool = Tool(
    name="Neo4j Cypher Query",
    func=run_cypher_query,
    description="Useful for executing Cypher queries against the Neo4j database.",
)

# You can add more tools here, e.g., for specific graph operations