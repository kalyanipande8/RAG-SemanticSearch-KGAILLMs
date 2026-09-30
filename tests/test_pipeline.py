"""
Real tests over real computed output -- no mocked/hardcoded results.
Run with: python3 -m pytest tests/ -v
"""
import networkx as nx
import pytest

from kg.data import DRUGS, TARGETS, PATHWAYS, DISEASES
from kg.graph_store import build_graph, neighbors_by_rel, multi_hop_context, cypher_like_query
from kg.rdf_store import build_rdf_graph, sparql_drugs_for_disease, sparql_pathway_for_target
from rag.retrieve import flat_retrieve, graph_augmented_retrieve, tokenize
from rag.answer import synthesize_answer, USE_LIVE_LLM
from experiments.relevance_experiment import TEST_QUERIES, recall_at_k, run_experiment


# ---------------------------------------------------------------------------
# Knowledge graph (networkx) tests
# ---------------------------------------------------------------------------

def test_graph_node_and_edge_counts():
    g = build_graph()
    expected_nodes = len(DRUGS) + len(TARGETS) + len(PATHWAYS) + len(DISEASES)
    assert g.number_of_nodes() == expected_nodes
    assert g.number_of_edges() > 60  # real relationship count, not trivial


def test_graph_is_multidigraph_with_typed_nodes():
    g = build_graph()
    kinds = {g.nodes[n]["kind"] for n in g.nodes}
    assert kinds == {"Drug", "Target", "Pathway", "Disease"}


def test_cypher_like_query_returns_real_matches():
    g = build_graph()
    results = cypher_like_query(g, "Drug", "TREATS", "Disease")
    assert ("Imatinib", "Chronic_myeloid_leukemia") in results
    assert all(g.nodes[d]["kind"] == "Drug" and g.nodes[dis]["kind"] == "Disease" for d, dis in results)


def test_neighbors_by_rel_direct_and_reverse():
    g = build_graph()
    targets_of_imatinib = neighbors_by_rel(g, "Imatinib", rel="TARGETS")
    assert ("BCR-ABL", "TARGETS") in targets_of_imatinib

    drugs_targeting_egfr = neighbors_by_rel(g, "EGFR", rel="TARGETS", reverse=True)
    assert ("Gefitinib", "TARGETS") in drugs_targeting_egfr


def test_multi_hop_context_reaches_disease_from_drug():
    g = build_graph()
    visited_nodes, visited_edges = multi_hop_context(g, "Imatinib", max_hops=2)
    assert "BCR-ABL" in visited_nodes
    assert "Chronic_myeloid_leukemia" in visited_nodes
    assert len(visited_edges) > 0


# ---------------------------------------------------------------------------
# RDF / SPARQL (rdflib) tests
# ---------------------------------------------------------------------------

def test_rdf_graph_triple_count():
    rdf_g = build_rdf_graph()
    # >= 4 triples per entity (type + label + extras) + 1 triple per relation
    assert len(rdf_g) > 200


def test_sparql_drugs_for_disease_real_query():
    rdf_g = build_rdf_graph()
    rows = sparql_drugs_for_disease(rdf_g, "Chronic_myeloid_leukemia")
    labels = {str(r.drugLabel) for r in rows}
    assert "Imatinib" in labels
    # verify the multi-hop mechanism join actually resolved
    imatinib_rows = [r for r in rows if str(r.drugLabel) == "Imatinib"]
    assert any(str(r.targetLabel) == "BCR-ABL" for r in imatinib_rows)


def test_sparql_pathway_for_target_real_query():
    rdf_g = build_rdf_graph()
    rows = sparql_pathway_for_target(rdf_g, "BRAF")
    pathways = {str(r.pathwayLabel) for r in rows}
    assert "RAS-RAF-MEK-ERK_signaling" in pathways
    diseases = {str(r.diseaseLabel) for r in rows if r.diseaseLabel}
    assert "Melanoma" in diseases


# ---------------------------------------------------------------------------
# Retrieval tests
# ---------------------------------------------------------------------------

def test_tokenize_handles_underscores_and_hyphens():
    assert "myeloid" in tokenize("Chronic_myeloid_leukemia")
    assert "abl" in tokenize("BCR-ABL")


def test_flat_retrieve_finds_lexical_match():
    g = build_graph()
    results = flat_retrieve(g, "chronic myeloid leukemia", top_k=5)
    assert any(r.node == "Chronic_myeloid_leukemia" for r in results)


def test_graph_augmented_retrieve_reaches_beyond_lexical_match():
    """Sanity check: for a disease-only query, graph augmentation should
    surface the mechanistically relevant drug/target even though those
    node names share no words with the query -- something flat retrieval
    structurally cannot do."""
    g = build_graph()
    query = "chronic myeloid leukemia"
    flat = {r.node for r in flat_retrieve(g, query, top_k=5)}
    graph = {r.node for r in graph_augmented_retrieve(g, query, top_k=5)}
    assert "Imatinib" not in flat
    assert "Imatinib" in graph
    assert "BCR-ABL" in graph


# ---------------------------------------------------------------------------
# Answer synthesis (no live LLM) tests
# ---------------------------------------------------------------------------

def test_no_live_llm_flag_is_off():
    assert USE_LIVE_LLM is False


def test_synthesize_answer_is_grounded_template_text():
    g = build_graph()
    answer = synthesize_answer("leukemia treatment options", g=g)
    assert "Imatinib" in answer or "BCR-ABL" in answer
    assert "Grounded answer" in answer


def test_synthesize_answer_handles_no_match():
    g = build_graph()
    answer = synthesize_answer("zzz_nonexistent_query_zzz", g=g)
    assert "No knowledge-graph entities matched" in answer


# ---------------------------------------------------------------------------
# Relevance experiment: injected sanity check that graph-augmented beats flat
# ---------------------------------------------------------------------------

def test_relevance_experiment_graph_beats_flat_on_average():
    result = run_experiment(verbose=False)
    assert result["avg_graph_recall"] > result["avg_flat_recall"]
    assert result["improvement_pct"] > 0


def test_relevance_experiment_per_query_graph_never_worse_than_flat_on_majority():
    """Graph augmentation should never do worse, and should do strictly
    better on most of the hand-labeled test queries (it can only add
    context, never remove a flat match, given our combined-score logic)."""
    g = build_graph()
    worse_count = 0
    better_count = 0
    for case in TEST_QUERIES:
        query, relevant = case["query"], case["relevant"]
        flat = {r.node for r in flat_retrieve(g, query, top_k=5)}
        graph = {r.node for r in graph_augmented_retrieve(g, query, top_k=5)}
        fr = recall_at_k(flat, relevant)
        gr = recall_at_k(graph, relevant)
        assert gr >= fr - 1e-9, f"graph recall regressed for query: {query}"
        if gr > fr:
            better_count += 1
        elif gr < fr:
            worse_count += 1
    assert worse_count == 0
    assert better_count >= len(TEST_QUERIES) // 2


def test_relevance_improvement_is_a_real_positive_percentage():
    result = run_experiment(verbose=False)
    # Sanity bounds: a real, non-trivial, non-infinite improvement.
    assert 0 < result["improvement_pct"] < 1000


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
