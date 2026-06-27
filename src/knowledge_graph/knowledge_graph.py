"""
Knowledge Graph Implementation
"""

import logging
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple, Set
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """A knowledge graph for storing and querying entities and relationships"""

    def __init__(self):
        """Initialize an empty knowledge graph"""
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.node_id_counter = 0
        self.edge_id_counter = 0
        # Maps from entity names to node IDs for quick lookup
        self.entity_to_node_id: Dict[str, int] = {}
        # Maps from node IDs to node data
        self.node_id_to_data: Dict[int, Dict[str, Any]] = {}

    def add_entity(self, name: str, entity_type: str, properties: Optional[Dict[str, Any]] = None) -> int:
        """
        Add an entity to the knowledge graph

        Args:
            name: Name of the entity
            entity_type: Type of the entity (e.g., 'Person', 'Organization', 'Concept')
            properties: Additional properties for the entity

        Returns:
            int: Node ID of the added entity
        """
        if properties is None:
            properties = {}

        # Check if entity already exists (by name and type)
        key = f"{name}::{entity_type}"
        if key in self.entity_to_node_id:
            node_id = self.entity_to_node_id[key]
            # Update properties if needed
            self.node_id_to_data[node_id].update(properties)
            self.graph.nodes[node_id].update(properties)
            return node_id

        # Create new node
        node_id = self.node_id_counter
        self.node_id_counter += 1

        node_data = {
            "id": node_id,
            "name": name,
            "type": entity_type,
            "properties": properties,
            "created_at": datetime.now().isoformat()
        }

        self.graph.add_node(node_id, **node_data)
        self.entity_to_node_id[key] = node_id
        self.node_id_to_data[node_id] = node_data

        logger.debug(f"Added entity: {name} ({entity_type}) with ID {node_id}")
        return node_id

    def add_relation(self, source_name: str, source_type: str,
                     relation: str,
                     target_name: str, target_type: str,
                     properties: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a relationship between two entities

        Args:
            source_name: Name of the source entity
            source_type: Type of the source entity
            relation: Type of relationship (e.g., 'works_at', 'located_in')
            target_name: Name of the target entity
            target_type: Type of the target entity
            properties: Additional properties for the relationship

        Returns:
            int: Edge ID of the added relationship
        """
        if properties is None:
            properties = {}

        # Ensure both entities exist
        source_id = self.add_entity(source_name, source_type)
        target_id = self.add_entity(target_name, target_type)

        # Create edge ID
        edge_id = self.edge_id_counter
        self.edge_id_counter += 1

        edge_data = {
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "source_name": source_name,
            "target_name": target_name,
            "relation": relation,
            "properties": properties,
            "created_at": datetime.now().isoformat()
        }

        # Add edge to the graph
        self.graph.add_edge(source_id, target_id, key=edge_id, **edge_data)

        logger.debug(f"Added relation: {source_name} --[{relation}]--> {target_name} with ID {edge_id}")
        return edge_id

    def get_entity(self, name: str, entity_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get an entity by name and optionally type

        Args:
            name: Name of the entity
            entity_type: Type of the entity (optional)

        Returns:
            Entity data if found, None otherwise
        """
        if entity_type is not None:
            key = f"{name}::{entity_type}"
            node_id = self.entity_to_node_id.get(key)
            if node_id is not None:
                return self.node_id_to_data.get(node_id)
            return None
        else:
            # Find any node with this name regardless of type
            for key, node_id in self.entity_to_node_id.items():
                if key.startswith(f"{name}::"):
                    return self.node_id_to_data.get(node_id)
            return None

    def get_relations(self, source_name: str, source_type: Optional[str] = None,
                      relation: Optional[str] = None,
                      target_name: str = None, target_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relationships matching the criteria

        Args:
            source_name: Source entity name (optional)
            source_type: Source entity type (optional)
            relation: Relationship type (optional)
            target_name: Target entity name (optional)
            target_type: Target entity type (optional)

        Returns:
            List of matching relationships
        """
        results = []

        # Determine source node IDs
        source_ids = set()
        if source_name is not None and source_type is not None:
            key = f"{source_name}::{source_type}"
            source_id = self.entity_to_node_id.get(key)
            if source_id is not None:
                source_ids.add(source_id)
        elif source_name is not None:
            # Find all nodes with this name
            for key, node_id in self.entity_to_node_id.items():
                if key.startswith(f"{source_name}::"):
                    source_ids.add(node_id)
        else:
            # All nodes are potential sources
            source_ids = set(self.node_id_to_data.keys())

        # Determine target node IDs
        target_ids = set()
        if target_name is not None and target_type is not None:
            key = f"{target_name}::{target_type}"
            target_id = self.entity_to_node_id.get(key)
            if target_id is not None:
                target_ids.add(target_id)
        elif target_name is not None:
            # Find all nodes with this name
            for key, node_id in self.entity_to_node_id.items():
                if key.startswith(f"{target_name}::"):
                    target_ids.add(node_id)
        else:
            # All nodes are potential targets
            target_ids = set(self.node_id_to_data.keys())

        # Iterate through edges
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            if u in source_ids and v in target_ids:
                if relation is None or data.get('relation') == relation:
                    results.append(data)

        return results

    def get_neighbors(self, node_id: int, direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get neighboring nodes of a given node

        Args:
            node_id: ID of the node
            direction: 'in', 'out', or 'both'

        Returns:
            List of neighbor information
        """
        neighbors = []

        if direction in ["out", "both"]:
            for successor in self.graph.successors(node_id):
                edge_data = self.graph.get_edge_data(node_id, successor)
                # Since we're using MultiDiGraph, edge_data is a dict of key->data
                for key, data in edge_data.items():
                    neighbors.append({
                        "node_id": successor,
                        "node_data": self.node_id_to_data.get(successor, {}),
                        "relation": data.get('relation'),
                        "edge_id": key,
                        "direction": "out"
                    })

        if direction in ["in", "both"]:
            for predecessor in self.graph.predecessors(node_id):
                edge_data = self.graph.get_edge_data(predecessor, node_id)
                for key, data in edge_data.items():
                    neighbors.append({
                        "node_id": predecessor,
                        "node_data": self.node_id_to_data.get(predecessor, {}),
                        "relation": data.get('relation'),
                        "edge_id": key,
                        "direction": "in"
                    })

        return neighbors

    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities by name (case-insensitive substring match)

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching entities
        """
        query_lower = query.lower()
        results = []

        for key, node_id in self.entity_to_node_id.items():
            name, entity_type = key.split('::', 1)
            if query_lower in name.lower():
                node_data = self.node_id_to_data.get(node_id, {})
                results.append({
                    "node_id": node_id,
                    "name": name,
                    "type": entity_type,
                    "data": node_data
                })

                if len(results) >= limit:
                    break

        return results

    def get_subgraph(self, node_ids: List[int], depth: int = 1) -> nx.MultiDiGraph:
        """
        Extract a subgraph centered around the given nodes

        Args:
            node_ids: List of node IDs to center the subgraph around
            depth: How many hops out to include

        Returns:
            Subgraph as a NetworkX graph
        """
        # Start with the given nodes
        nodes_to_include = set(node_ids)

        # Expand by the specified depth
        for _ in range(depth):
            neighbors = set()
            for node in nodes_to_include:
                neighbors.update(self.graph.predecessors(node))
                neighbors.update(self.graph.successors(node))
            nodes_to_include.update(neighbors)

        # Return the subgraph
        return self.graph.subgraph(nodes_to_include).copy()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge graph to a dictionary representation

        Returns:
            Dictionary representation of the graph
        """
        nodes = []
        for node_id, data in self.node_id_to_data.items():
            nodes.append(data)

        edges = []
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            edges.append(data)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "generated_at": datetime.now().isoformat()
            }
        }

    def from_dict(self, data: Dict[str, Any]):
        """
        Load the knowledge graph from a dictionary representation

        Args:
            data: Dictionary representation of the graph
        """
        # Clear existing data
        self.graph.clear()
        self.node_id_to_data.clear()
        self.entity_to_node_id.clear()
        self.node_id_counter = 0
        self.edge_id_counter = 0

        # Add nodes
        for node_data in data.get("nodes", []):
            node_id = node_data.get("id", self.node_id_counter)
            self.node_id_counter = max(self.node_id_counter, node_id + 1)

            # Extract name and type
            name = node_data.get("name", "")
            entity_type = node_data.get("type", "Unknown")
            properties = node_data.get("properties", {})

            self.add_entity(name, entity_type, properties)
            # Note: add_entity will overwrite the ID we just set if we're not careful
            # So we need to handle this differently - for simplicity, let's assume
            # the IDs in the data are sequential starting from 0 and we're loading
            # into an empty graph

        # Actually, let's rebuild the mappings properly
        # Reset counters and rebuild from the loaded data
        self.node_id_counter = 0
        self.edge_id_counter = 0
        self.entity_to_node_id.clear()
        self.node_id_to_data.clear()

        # Re-add nodes with correct IDs
        id_mapping = {}  # Original ID -> New ID
        for i, node_data in enumerate(data.get("nodes", [])):
            original_id = node_data.get("id", i)
            name = node_data.get("name", "")
            entity_type = node_data.get("type", "Unknown")
            properties = node_data.get("properties", {})

            new_id = self.add_entity(name, entity_type, properties)
            id_mapping[original_id] = new_id

        # Re-add edges
        for edge_data in data.get("edges", []):
            source_original = edge_data.get("source_id")
            target_original = edge_data.get("target_id")
            relation = edge_data.get("relation", "related_to")
            properties = edge_data.get("properties", {})

            if source_original in id_mapping and target_original in id_mapping:
                source_id = id_mapping[source_original]
                target_id = id_mapping[target_original]
                self.add_relation(
                    self.node_id_to_data[source_id]["name"],
                    self.node_id_to_data[source_id]["type"],
                    relation,
                    self.node_id_to_data[target_id]["name"],
                    self.node_id_to_data[target_id]["type"],
                    properties
                )

        logger.info(f"Loaded knowledge graph with {len(self.node_id_to_data)} nodes and {self.edge_id_counter} edges")

    def save_to_file(self, filepath: str):
        """
        Save the knowledge graph to a JSON file

        Args:
            filepath: Path to save the file
        """
        data = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved knowledge graph to {filepath}")

    def load_from_file(self, filepath: str):
        """
        Load the knowledge graph from a JSON file

        Args:
            filepath: Path to the file to load
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.from_dict(data)
        logger.info(f"Loaded knowledge graph from {filepath}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph

        Returns:
            Dictionary with graph statistics
        """
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        # Count by type
        type_counts = {}
        for node_id, data in self.node_id_to_data.items():
            node_type = data.get("type", "Unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        # Count relation types
        relation_counts = {}
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            relation = data.get("relation", "unknown")
            relation_counts[relation] = relation_counts.get(relation, 0) + 1

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "type_distribution": type_counts,
            "relation_distribution": relation_counts,
            "density": nx.density(self.graph) if node_count > 1 else 0.0
        }