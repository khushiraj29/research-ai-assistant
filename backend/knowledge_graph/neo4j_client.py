"""Neo4j client for persisting and querying knowledge graph data."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Thin wrapper around the official Neo4j Python driver.

    Attributes:
        driver: Active Neo4j driver instance.
    """

    def __init__(self, uri: str, user: str, password: str) -> None:
        """Connect to the Neo4j database.

        Args:
            uri: Bolt or Neo4j URI (e.g. ``"bolt://localhost:7687"``).
            user: Neo4j username.
            password: Neo4j password.
        """
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Connected to Neo4j at '%s'.", uri)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store_graph(self, graph_data: Dict) -> None:
        """Persist nodes and edges from *graph_data* in Neo4j using MERGE
        to avoid duplicate entries.

        Args:
            graph_data: Dict with ``nodes`` (list), ``edges`` (list), and
                ``document_id`` (str) as produced by
                :meth:`~backend.knowledge_graph.extractor.KnowledgeGraphExtractor.build_graph`.
        """
        document_id: str = graph_data.get("document_id", "")
        nodes: List[Dict] = graph_data.get("nodes", [])
        edges: List[Dict] = graph_data.get("edges", [])

        with self.driver.session() as session:
            # Persist each entity node
            for node in nodes:
                session.run(
                    """
                    MERGE (e:Entity {id: $id})
                    SET e.label = $label,
                        e.entity_type = $entity_type,
                        e.document_id = $document_id
                    """,
                    id=node["id"],
                    label=node.get("label", node["id"]),
                    entity_type=node.get("entity_type", "UNKNOWN"),
                    document_id=document_id,
                )

            # Persist each relationship edge
            for edge in edges:
                session.run(
                    """
                    MATCH (a:Entity {id: $source})
                    MATCH (b:Entity {id: $target})
                    MERGE (a)-[r:RELATES_TO {relationship: $relationship,
                                              document_id: $document_id}]->(b)
                    """,
                    source=edge["source"],
                    target=edge["target"],
                    relationship=edge.get("relationship", "RELATED"),
                    document_id=document_id,
                )

        logger.info(
            "Stored %d nodes and %d edges for document '%s'.",
            len(nodes),
            len(edges),
            document_id,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_graph(self, document_id: Optional[str] = None) -> Dict:
        """Retrieve nodes and edges from Neo4j, optionally filtered by document.

        Args:
            document_id: If provided, only entities and relationships tagged
                with this document ID are returned.

        Returns:
            Dict with ``nodes`` and ``edges`` lists.
        """
        with self.driver.session() as session:
            if document_id:
                node_result = session.run(
                    "MATCH (e:Entity {document_id: $doc_id}) RETURN e",
                    doc_id=document_id,
                )
                edge_result = session.run(
                    """
                    MATCH (a:Entity)-[r:RELATES_TO {document_id: $doc_id}]->(b:Entity)
                    RETURN a.id AS source, b.id AS target,
                           r.relationship AS relationship
                    """,
                    doc_id=document_id,
                )
            else:
                node_result = session.run("MATCH (e:Entity) RETURN e")
                edge_result = session.run(
                    """
                    MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
                    RETURN a.id AS source, b.id AS target,
                           r.relationship AS relationship
                    """
                )

            nodes = [dict(record["e"]) for record in node_result]
            edges = [
                {
                    "source": record["source"],
                    "target": record["target"],
                    "relationship": record["relationship"],
                }
                for record in edge_result
            ]

        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self.driver.close()
        logger.info("Neo4j connection closed.")
