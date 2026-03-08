"""Named-entity and relationship extraction for knowledge graph construction."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class KnowledgeGraphExtractor:
    """Extracts entities and simple co-occurrence relationships from text
    using spaCy's ``en_core_web_sm`` model.

    Attributes:
        nlp: Loaded spaCy language model.
    """

    def __init__(self) -> None:
        """Load the spaCy English model."""
        import spacy

        logger.info("Loading spaCy model: en_core_web_sm")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            raise
        logger.info("spaCy model loaded.")

    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities from *text*.

        Args:
            text: Input document or passage text.

        Returns:
            A list of dicts, each with keys:
                - ``text``: Surface form of the entity.
                - ``label``: spaCy entity type (e.g. "ORG", "PERSON").
                - ``start``: Character start offset in *text*.
                - ``end``: Character end offset in *text*.
        """
        doc = self.nlp(text)
        seen: set = set()
        entities: List[Dict] = []
        for ent in doc.ents:
            key = (ent.text.strip(), ent.label_)
            if key in seen:
                continue
            seen.add(key)
            entities.append(
                {
                    "text": ent.text.strip(),
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
            )
        return entities

    def extract_relationships(self, text: str) -> List[Dict]:
        """Derive simple co-occurrence relationships between entities in the
        same sentence.

        For each sentence that contains at least two named entities, every
        ordered pair of entities is recorded as a ``CO_OCCURS_WITH``
        relationship.  This is a lightweight heuristic; replace with a
        dedicated relation-extraction model for higher precision.

        Args:
            text: Input document or passage text.

        Returns:
            A list of dicts with keys ``source``, ``target``, and
            ``relationship``.
        """
        doc = self.nlp(text)
        relationships: List[Dict] = []
        seen_pairs: set = set()

        for sent in doc.sents:
            sent_ents = [ent for ent in sent.ents]
            for i, ent_a in enumerate(sent_ents):
                for ent_b in sent_ents[i + 1 :]:
                    pair = (ent_a.text.strip(), ent_b.text.strip())
                    if pair in seen_pairs or pair[0] == pair[1]:
                        continue
                    seen_pairs.add(pair)
                    relationships.append(
                        {
                            "source": pair[0],
                            "target": pair[1],
                            "relationship": "CO_OCCURS_WITH",
                        }
                    )
        return relationships

    def build_graph(self, text: str, document_id: str) -> Dict:
        """Build a graph dict containing nodes (entities) and edges (relationships).

        Args:
            text: Full document text to process.
            document_id: Identifier attached to each node for provenance.

        Returns:
            A dict with keys:
                - ``nodes``: List of entity dicts (id, label, entity_type).
                - ``edges``: List of edge dicts (source, target, relationship).
                - ``document_id``: The supplied document identifier.
        """
        entities = self.extract_entities(text)
        relationships = self.extract_relationships(text)

        # Build deduplicated node list
        seen_nodes: set = set()
        nodes: List[Dict] = []
        for ent in entities:
            node_id = ent["text"]
            if node_id in seen_nodes:
                continue
            seen_nodes.add(node_id)
            nodes.append(
                {
                    "id": node_id,
                    "label": node_id,
                    "entity_type": ent["label"],
                    "document_id": document_id,
                }
            )

        edges: List[Dict] = [
            {
                "source": rel["source"],
                "target": rel["target"],
                "relationship": rel["relationship"],
                "document_id": document_id,
            }
            for rel in relationships
            # Only include edges whose endpoints are in the node set
            if rel["source"] in seen_nodes and rel["target"] in seen_nodes
        ]

        logger.info(
            "Graph built for document '%s': %d nodes, %d edges.",
            document_id,
            len(nodes),
            len(edges),
        )
        return {"nodes": nodes, "edges": edges, "document_id": document_id}
