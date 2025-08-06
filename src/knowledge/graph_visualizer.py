"""
Graph Visualizer for the TTA Project.

This module provides utilities for visualizing the Neo4j knowledge graph.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Set, Tuple
import tempfile
import webbrowser

from .neo4j_manager import Neo4jManager, get_neo4j_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphVisualizer:
    """
    Visualizes the Neo4j knowledge graph.
    
    This class provides methods for generating visualizations of the Neo4j knowledge graph.
    """
    
    def __init__(self, neo4j_manager: Optional[Neo4jManager] = None):
        """
        Initialize the graph visualizer.
        
        Args:
            neo4j_manager: Neo4j manager (optional)
        """
        self.neo4j_manager = neo4j_manager or get_neo4j_manager()
    
    def generate_d3_visualization(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        title: str = "Knowledge Graph Visualization",
        output_file: Optional[str] = None,
        open_browser: bool = True
    ) -> str:
        """
        Generate a D3.js visualization of the knowledge graph.
        
        Args:
            query: Cypher query to execute
            parameters: Query parameters (optional)
            title: Title of the visualization (default: "Knowledge Graph Visualization")
            output_file: Output file path (optional)
            open_browser: Whether to open the visualization in a browser (default: True)
            
        Returns:
            Path to the generated HTML file
        """
        # Execute the query
        result = self.neo4j_manager.query(query, parameters)
        
        # Extract nodes and relationships
        nodes = set()
        links = []
        
        for record in result:
            # Process each path in the record
            for key, value in record.items():
                if hasattr(value, "nodes") and hasattr(value, "relationships"):
                    # This is a path
                    for node in value.nodes:
                        nodes.add(self._node_to_dict(node))
                    
                    for rel in value.relationships:
                        links.append(self._relationship_to_dict(rel))
                elif hasattr(value, "id") and hasattr(value, "labels"):
                    # This is a node
                    nodes.add(self._node_to_dict(value))
                elif hasattr(value, "type") and hasattr(value, "start") and hasattr(value, "end"):
                    # This is a relationship
                    links.append(self._relationship_to_dict(value))
        
        # Convert nodes to list
        nodes_list = list(nodes)
        
        # Create the visualization data
        vis_data = {
            "nodes": nodes_list,
            "links": links
        }
        
        # Generate the HTML
        html = self._generate_html(vis_data, title)
        
        # Save to file
        if output_file is None:
            # Create a temporary file
            fd, output_file = tempfile.mkstemp(suffix=".html", prefix="graph_vis_")
            os.close(fd)
        
        with open(output_file, "w") as f:
            f.write(html)
        
        logger.info(f"Visualization saved to {output_file}")
        
        # Open in browser if requested
        if open_browser:
            webbrowser.open(f"file://{os.path.abspath(output_file)}")
        
        return output_file
    
    def visualize_entity_neighborhood(
        self,
        entity_id: str,
        entity_label: str,
        depth: int = 2,
        output_file: Optional[str] = None,
        open_browser: bool = True
    ) -> str:
        """
        Visualize the neighborhood of an entity.
        
        Args:
            entity_id: ID of the entity
            entity_label: Label of the entity
            depth: Depth of the neighborhood (default: 2)
            output_file: Output file path (optional)
            open_browser: Whether to open the visualization in a browser (default: True)
            
        Returns:
            Path to the generated HTML file
        """
        # Create the query
        query = f"""
        MATCH path = (n:{entity_label} {{id: $entity_id}})-[*1..{depth}]-(m)
        RETURN path
        """
        
        parameters = {"entity_id": entity_id}
        
        # Generate the visualization
        return self.generate_d3_visualization(
            query=query,
            parameters=parameters,
            title=f"Neighborhood of {entity_id}",
            output_file=output_file,
            open_browser=open_browser
        )
    
    def visualize_entity_type(
        self,
        entity_type: str,
        limit: int = 100,
        output_file: Optional[str] = None,
        open_browser: bool = True
    ) -> str:
        """
        Visualize entities of a specific type.
        
        Args:
            entity_type: Type of entity to visualize
            limit: Maximum number of entities to include (default: 100)
            output_file: Output file path (optional)
            open_browser: Whether to open the visualization in a browser (default: True)
            
        Returns:
            Path to the generated HTML file
        """
        # Create the query
        query = f"""
        MATCH (n:{entity_type})
        WITH n LIMIT {limit}
        MATCH path = (n)-[r]-(m)
        RETURN path
        """
        
        # Generate the visualization
        return self.generate_d3_visualization(
            query=query,
            title=f"{entity_type} Entities",
            output_file=output_file,
            open_browser=open_browser
        )
    
    def visualize_relationship_type(
        self,
        relationship_type: str,
        limit: int = 100,
        output_file: Optional[str] = None,
        open_browser: bool = True
    ) -> str:
        """
        Visualize relationships of a specific type.
        
        Args:
            relationship_type: Type of relationship to visualize
            limit: Maximum number of relationships to include (default: 100)
            output_file: Output file path (optional)
            open_browser: Whether to open the visualization in a browser (default: True)
            
        Returns:
            Path to the generated HTML file
        """
        # Create the query
        query = f"""
        MATCH (n)-[r:{relationship_type}]->(m)
        WITH r LIMIT {limit}
        MATCH path = (n)-[r]->(m)
        RETURN path
        """
        
        # Generate the visualization
        return self.generate_d3_visualization(
            query=query,
            title=f"{relationship_type} Relationships",
            output_file=output_file,
            open_browser=open_browser
        )
    
    def visualize_full_graph(
        self,
        limit: int = 1000,
        output_file: Optional[str] = None,
        open_browser: bool = True
    ) -> str:
        """
        Visualize the full knowledge graph.
        
        Args:
            limit: Maximum number of nodes to include (default: 1000)
            output_file: Output file path (optional)
            open_browser: Whether to open the visualization in a browser (default: True)
            
        Returns:
            Path to the generated HTML file
        """
        # Create the query
        query = f"""
        MATCH (n)
        WITH n LIMIT {limit}
        MATCH path = (n)-[r]-(m)
        RETURN path
        """
        
        # Generate the visualization
        return self.generate_d3_visualization(
            query=query,
            title="Full Knowledge Graph",
            output_file=output_file,
            open_browser=open_browser
        )
    
    def _node_to_dict(self, node) -> Dict[str, Any]:
        """
        Convert a Neo4j node to a dictionary.
        
        Args:
            node: Neo4j node
            
        Returns:
            Dictionary representation of the node
        """
        # Extract properties
        properties = dict(node.items())
        
        # Add ID and labels
        node_dict = {
            "id": node.id,
            "labels": list(node.labels),
            "properties": properties
        }
        
        # Add name for display
        if "name" in properties:
            node_dict["name"] = properties["name"]
        elif "id" in properties:
            node_dict["name"] = properties["id"]
        else:
            node_dict["name"] = f"Node {node.id}"
        
        return node_dict
    
    def _relationship_to_dict(self, relationship) -> Dict[str, Any]:
        """
        Convert a Neo4j relationship to a dictionary.
        
        Args:
            relationship: Neo4j relationship
            
        Returns:
            Dictionary representation of the relationship
        """
        # Extract properties
        properties = dict(relationship.items())
        
        # Add type, source, and target
        rel_dict = {
            "id": relationship.id,
            "type": relationship.type,
            "source": relationship.start,
            "target": relationship.end,
            "properties": properties
        }
        
        return rel_dict
    
    def _generate_html(self, data: Dict[str, Any], title: str) -> str:
        """
        Generate HTML for the visualization.
        
        Args:
            data: Visualization data
            title: Title of the visualization
            
        Returns:
            HTML string
        """
        # Convert data to JSON
        data_json = json.dumps(data)
        
        # Create the HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                
                #container {{
                    width: 100%;
                    height: 100vh;
                    overflow: hidden;
                }}
                
                #graph {{
                    width: 100%;
                    height: 100%;
                }}
                
                .node {{
                    stroke: #fff;
                    stroke-width: 1.5px;
                }}
                
                .link {{
                    stroke: #999;
                    stroke-opacity: 0.6;
                }}
                
                .node text {{
                    pointer-events: none;
                    font-size: 10px;
                }}
                
                .tooltip {{
                    position: absolute;
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 12px;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.3s;
                }}
                
                .controls {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background-color: rgba(255, 255, 255, 0.8);
                    border-radius: 4px;
                    padding: 10px;
                }}
                
                .controls button {{
                    margin-right: 5px;
                }}
            </style>
        </head>
        <body>
            <div id="container">
                <div class="controls">
                    <button id="zoom-in">Zoom In</button>
                    <button id="zoom-out">Zoom Out</button>
                    <button id="reset">Reset</button>
                </div>
                <div id="graph"></div>
                <div class="tooltip" id="tooltip"></div>
            </div>
            
            <script>
                // Graph data
                const data = {data_json};
                
                // Create the visualization
                const width = window.innerWidth;
                const height = window.innerHeight;
                
                // Create the SVG
                const svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                // Create the zoom behavior
                const zoom = d3.zoom()
                    .scaleExtent([0.1, 10])
                    .on("zoom", (event) => {{
                        g.attr("transform", event.transform);
                    }});
                
                svg.call(zoom);
                
                // Create a group for the graph
                const g = svg.append("g");
                
                // Create the simulation
                const simulation = d3.forceSimulation(data.nodes)
                    .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("collide", d3.forceCollide().radius(50));
                
                // Create the links
                const link = g.append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(data.links)
                    .enter()
                    .append("line")
                    .attr("class", "link")
                    .attr("stroke-width", 1);
                
                // Create the nodes
                const node = g.append("g")
                    .attr("class", "nodes")
                    .selectAll("g")
                    .data(data.nodes)
                    .enter()
                    .append("g")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));
                
                // Add circles to the nodes
                node.append("circle")
                    .attr("r", 10)
                    .attr("fill", d => getNodeColor(d))
                    .on("mouseover", showTooltip)
                    .on("mouseout", hideTooltip);
                
                // Add labels to the nodes
                node.append("text")
                    .attr("dx", 12)
                    .attr("dy", ".35em")
                    .text(d => d.name);
                
                // Update the simulation on tick
                simulation.on("tick", () => {{
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);
                    
                    node
                        .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
                }});
                
                // Drag functions
                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}
                
                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}
                
                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}
                
                // Tooltip functions
                function showTooltip(event, d) {{
                    const tooltip = d3.select("#tooltip");
                    
                    // Create tooltip content
                    let content = `<strong>${{d.name}}</strong><br>`;
                    content += `Labels: ${{d.labels.join(", ")}}<br>`;
                    content += `<hr>`;
                    
                    // Add properties
                    for (const [key, value] of Object.entries(d.properties)) {{
                        if (key !== "name") {{
                            content += `${{key}}: ${{value}}<br>`;
                        }}
                    }}
                    
                    // Set tooltip content and position
                    tooltip
                        .html(content)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px")
                        .style("opacity", 1);
                }}
                
                function hideTooltip() {{
                    d3.select("#tooltip").style("opacity", 0);
                }}
                
                // Get node color based on label
                function getNodeColor(node) {{
                    const labelColors = {{
                        "Location": "#4CAF50",
                        "Character": "#2196F3",
                        "Item": "#FFC107",
                        "Memory": "#9C27B0",
                        "Quest": "#F44336"
                    }};
                    
                    // Find the first label that has a defined color
                    for (const label of node.labels) {{
                        if (labelColors[label]) {{
                            return labelColors[label];
                        }}
                    }}
                    
                    // Default color
                    return "#999";
                }}
                
                // Control buttons
                d3.select("#zoom-in").on("click", () => {{
                    svg.transition().call(zoom.scaleBy, 1.5);
                }});
                
                d3.select("#zoom-out").on("click", () => {{
                    svg.transition().call(zoom.scaleBy, 0.75);
                }});
                
                d3.select("#reset").on("click", () => {{
                    svg.transition().call(zoom.transform, d3.zoomIdentity);
                }});
            </script>
        </body>
        </html>
        """
        
        return html


# Singleton instance
_GRAPH_VISUALIZER = None

def get_graph_visualizer() -> GraphVisualizer:
    """
    Get the singleton instance of the GraphVisualizer.
    
    Returns:
        GraphVisualizer instance
    """
    global _GRAPH_VISUALIZER
    if _GRAPH_VISUALIZER is None:
        _GRAPH_VISUALIZER = GraphVisualizer()
    return _GRAPH_VISUALIZER
