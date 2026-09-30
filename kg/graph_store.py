"""
Knowledge graph store built with networkx.

Honest disclosure: Neo4j is not available/installed in this environment, so
this project uses `networkx.MultiDiGraph` as an explicitly-disclosed
stand-in for a Neo4j property graph. The graph model (typed nodes with
properties, typed/labeled directed edges) mirrors what a Neo4j Cypher graph
would look like, and `cypher_like_query()` below implements a small,
real, hand-rolled pattern-matching query layer over the networkx graph that
plays the same role Cypher would play against Neo4j. This mirrors the same
honest networkx-as-Neo4j-stand-in pattern used in the sibling
BiomedicalKG-OntologyEntityResolution project pattern (documented here
independently since that sibling repo does not yet exist in this workspace).

For real SPARQL support (a genuine query language, not a stand-in), see
`kg/rdf_store.py`, which builds an equivalent graph in `rdflib` and runs
real SPARQL queries against it.
"""
from __future__ import annotations

import networkx as nx

from kg.data import (
    DRUGS, TARGETS, PATHWAYS, DISEASES,
    DRUG_TARGETS, DRUG_TREATS, TARGET_PATHWAYS, TARGET_DISEASES, PATHWAY_DISEASES,
)


def build_graph() -> nx.MultiDiGraph:
    """Builds the drug-discovery knowledge graph as a networkx MultiDiGraph.

    Node ids are human-readable entity names (unique across entity types in
    this dataset). Each node carries a `kind` property (drug/target/pathway/
    disease) plus type-specific metadata. Edges carry a `rel` property
    naming the relationship type, mirroring a Neo4j labeled-relationship
    graph.
    """
    g = nx.MultiDiGraph()

    for name, drug_type, description in DRUGS:
        g.add_node(name, kind="Drug", drug_type=drug_type, description=description)
    for name, target_type in TARGETS:
        g.add_node(name, kind="Target", target_type=target_type)
    for (name,) in PATHWAYS:
        g.add_node(name, kind="Pathway")
    for (name,) in DISEASES:
        g.add_node(name, kind="Disease")

    for drug, target in DRUG_TARGETS:
        g.add_edge(drug, target, rel="TARGETS")
    for drug, disease in DRUG_TREATS:
        g.add_edge(drug, disease, rel="TREATS")
    for target, pathway in TARGET_PATHWAYS:
        g.add_edge(target, pathway, rel="PARTICIPATES_IN")
    for target, disease in TARGET_DISEASES:
        g.add_edge(target, disease, rel="IMPLICATED_IN")
    for pathway, disease in PATHWAY_DISEASES:
        g.add_edge(pathway, disease, rel="ASSOCIATED_WITH")

    return g


def neighbors_by_rel(g: nx.MultiDiGraph, node: str, rel: str | None = None, reverse: bool = False):
    """Real graph traversal: outgoing (or incoming, if reverse=True) neighbors
    of `node`, optionally filtered to a specific relationship type."""
    out = []
    edge_view = g.in_edges(node, data=True) if reverse else g.out_edges(node, data=True)
    for u, v, data in edge_view:
        if rel is not None and data.get("rel") != rel:
            continue
        other = u if reverse else v
        out.append((other, data.get("rel")))
    return out


def multi_hop_context(g: nx.MultiDiGraph, node: str, max_hops: int = 2):
    """Real BFS traversal collecting all nodes/edges reachable from `node`
    within `max_hops`, following edges in either direction (a drug graph is
    small and densely cross-linked, so undirected-style traversal surfaces
    the clinically relevant neighborhood: target -> pathway -> disease, or
    drug -> target -> other drugs on the same target, etc.).

    Returns (visited_nodes, visited_edges) where visited_edges is a list of
    (source, target, rel) triples.
    """
    visited_nodes = {node}
    visited_edges = []
    frontier = {node}
    for _ in range(max_hops):
        next_frontier = set()
        for n in frontier:
            for u, v, data in g.out_edges(n, data=True):
                visited_edges.append((u, v, data.get("rel")))
                if v not in visited_nodes:
                    next_frontier.add(v)
            for u, v, data in g.in_edges(n, data=True):
                visited_edges.append((u, v, data.get("rel")))
                if u not in visited_nodes:
                    next_frontier.add(u)
        visited_nodes |= next_frontier
        frontier = next_frontier
        if not frontier:
            break
    return visited_nodes, visited_edges


def cypher_like_query(g: nx.MultiDiGraph, start_kind: str, rel: str, end_kind: str):
    """A small real pattern-matching query: MATCH (a:start_kind)-[:rel]->(b:end_kind)
    RETURN a, b -- implemented as a real graph scan over networkx, standing
    in for the equivalent Cypher query a Neo4j deployment would run."""
    results = []
    for u, v, data in g.edges(data=True):
        if data.get("rel") != rel:
            continue
        if g.nodes[u].get("kind") != start_kind or g.nodes[v].get("kind") != end_kind:
            continue
        results.append((u, v))
    return results


if __name__ == "__main__":
    graph = build_graph()
    print(f"Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print("Sample cypher-like query MATCH (d:Drug)-[:TREATS]->(dis:Disease):")
    for drug, disease in cypher_like_query(graph, "Drug", "TREATS", "Disease")[:5]:
        print(f"  {drug} -> {disease}")
