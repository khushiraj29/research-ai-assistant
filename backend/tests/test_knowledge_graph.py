"""Tests for backend/knowledge_graph/extractor.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.knowledge_graph.extractor import KnowledgeGraphExtractor


def _make_entity(text: str, label: str, start: int = 0, end: int = 5) -> MagicMock:
    """Helper: create a mock spaCy Span (entity)."""
    ent = MagicMock()
    ent.text = text
    ent.label_ = label
    ent.start_char = start
    ent.end_char = end
    return ent


def _make_doc(entities=(), sentences=()) -> MagicMock:
    """Helper: create a mock spaCy Doc."""
    doc = MagicMock()
    doc.ents = list(entities)
    doc.sents = list(sentences)
    return doc


def _make_sent(entities) -> MagicMock:
    sent = MagicMock()
    sent.ents = list(entities)
    return sent


@pytest.fixture()
def extractor() -> KnowledgeGraphExtractor:
    """KnowledgeGraphExtractor with a real-ish nlp stub."""
    kg = KnowledgeGraphExtractor.__new__(KnowledgeGraphExtractor)
    kg.nlp = MagicMock()
    return kg


# ---------------------------------------------------------------------------
# extract_entities
# ---------------------------------------------------------------------------


class TestExtractEntities:
    def test_empty_doc_returns_empty_list(self, extractor: KnowledgeGraphExtractor):
        extractor.nlp.return_value = _make_doc(entities=[])
        assert extractor.extract_entities("no entities here") == []

    def test_single_entity_returned(self, extractor: KnowledgeGraphExtractor):
        ent = _make_entity("NASA", "ORG", start=0, end=4)
        extractor.nlp.return_value = _make_doc(entities=[ent])
        results = extractor.extract_entities("NASA launched a rocket.")
        assert len(results) == 1
        assert results[0]["text"] == "NASA"
        assert results[0]["label"] == "ORG"

    def test_multiple_entities(self, extractor: KnowledgeGraphExtractor):
        ents = [
            _make_entity("Solar Energy", "ORG", 0, 12),
            _make_entity("Battery", "PRODUCT", 13, 20),
        ]
        extractor.nlp.return_value = _make_doc(entities=ents)
        results = extractor.extract_entities("Solar Energy Battery storage.")
        assert len(results) == 2

    def test_duplicate_entities_deduplicated(self, extractor: KnowledgeGraphExtractor):
        ent1 = _make_entity("AI", "ORG", 0, 2)
        ent2 = _make_entity("AI", "ORG", 10, 12)  # same text + label
        extractor.nlp.return_value = _make_doc(entities=[ent1, ent2])
        results = extractor.extract_entities("AI and AI again.")
        assert len(results) == 1

    def test_entity_dict_has_required_keys(self, extractor: KnowledgeGraphExtractor):
        ent = _make_entity("Tesla", "ORG")
        extractor.nlp.return_value = _make_doc(entities=[ent])
        results = extractor.extract_entities("Tesla makes cars.")
        assert set(results[0].keys()) >= {"text", "label", "start", "end"}


# ---------------------------------------------------------------------------
# extract_relationships
# ---------------------------------------------------------------------------


class TestExtractRelationships:
    def test_empty_doc_no_relationships(self, extractor: KnowledgeGraphExtractor):
        extractor.nlp.return_value = _make_doc(entities=[], sentences=[_make_sent([])])
        results = extractor.extract_relationships("Nothing here.")
        assert results == []

    def test_two_entities_one_relationship(self, extractor: KnowledgeGraphExtractor):
        ent_a = _make_entity("Solar Energy", "ORG")
        ent_b = _make_entity("Battery", "PRODUCT")
        sent = _make_sent([ent_a, ent_b])
        extractor.nlp.return_value = _make_doc(sentences=[sent])
        results = extractor.extract_relationships("Solar Energy uses Battery storage.")
        assert len(results) == 1
        assert results[0]["source"] == "Solar Energy"
        assert results[0]["target"] == "Battery"
        assert results[0]["relationship"] == "CO_OCCURS_WITH"

    def test_three_entities_three_pairs(self, extractor: KnowledgeGraphExtractor):
        ents = [_make_entity(n, "ORG") for n in ["A", "B", "C"]]
        sent = _make_sent(ents)
        extractor.nlp.return_value = _make_doc(sentences=[sent])
        results = extractor.extract_relationships("A B C together.")
        # Pairs: (A,B), (A,C), (B,C)
        assert len(results) == 3

    def test_same_entity_not_related_to_itself(self, extractor: KnowledgeGraphExtractor):
        ent = _make_entity("AI", "ORG")
        sent = _make_sent([ent, ent])
        extractor.nlp.return_value = _make_doc(sentences=[sent])
        results = extractor.extract_relationships("AI and AI.")
        assert all(r["source"] != r["target"] for r in results)


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------


class TestBuildGraph:
    def test_returns_required_keys(self, extractor: KnowledgeGraphExtractor):
        extractor.nlp.return_value = _make_doc(entities=[], sentences=[])
        graph = extractor.build_graph("Some text.", document_id="doc-1")
        assert "nodes" in graph
        assert "edges" in graph
        assert "document_id" in graph

    def test_document_id_propagated(self, extractor: KnowledgeGraphExtractor):
        extractor.nlp.return_value = _make_doc(entities=[], sentences=[])
        graph = extractor.build_graph("text", document_id="my-doc")
        assert graph["document_id"] == "my-doc"

    def test_nodes_and_edges_built_correctly(self, extractor: KnowledgeGraphExtractor):
        ent_a = _make_entity("Solar Energy", "ORG")
        ent_b = _make_entity("Battery", "PRODUCT")
        sent = _make_sent([ent_a, ent_b])

        def nlp_side_effect(text: str):
            doc = _make_doc(entities=[ent_a, ent_b], sentences=[sent])
            return doc

        extractor.nlp.side_effect = nlp_side_effect
        graph = extractor.build_graph(
            "Solar Energy uses Battery storage.", document_id="doc-1"
        )
        node_ids = {n["id"] for n in graph["nodes"]}
        assert "Solar Energy" in node_ids
        assert "Battery" in node_ids
        assert len(graph["edges"]) >= 1
        assert graph["edges"][0]["relationship"] == "CO_OCCURS_WITH"

    def test_nodes_have_document_id(self, extractor: KnowledgeGraphExtractor):
        ent = _make_entity("AI", "ORG")
        extractor.nlp.return_value = _make_doc(entities=[ent], sentences=[])
        graph = extractor.build_graph("AI research.", document_id="test-doc")
        for node in graph["nodes"]:
            assert node["document_id"] == "test-doc"
