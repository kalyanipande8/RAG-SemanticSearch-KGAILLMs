#!/usr/bin/env python3
"""
End-to-end demo runner. No network calls, no API keys, no live LLM.

1. Builds the networkx knowledge graph (drug/target/pathway/disease) and the
   rdflib RDF store, and runs a real SPARQL query against it.
2. Runs graph-augmented RAG answer synthesis for a few example queries.
3. Runs the flat-vs-graph-augmented relevance experiment and prints the
   real, computed relevance-improvement percentage.
"""
from kg.graph_store import build_graph, cypher_like_query
from kg.rdf_store import build_rdf_graph, sparql_drugs_for_disease, sparql_pathway_for_target
from rag.answer import synthesize_answer
from experiments.relevance_experiment import run_experiment

EXAMPLE_QUERIES = [
    "leukemia treatment options",
    "HER2 breast cancer",
    "myelofibrosis JAK inhibitor",
]


def main():
    print("=" * 72)
    print("STEP 1: Knowledge graph construction (networkx -- honest Neo4j stand-in)")
    print("=" * 72)
    g = build_graph()
    print(f"Graph built: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print("Cypher-like query MATCH (d:Drug)-[:TREATS]->(dis:Disease) (first 5):")
    for drug, disease in cypher_like_query(g, "Drug", "TREATS", "Disease")[:5]:
        print(f"  {drug} -TREATS-> {disease}")

    print()
    print("=" * 72)
    print("STEP 2: RDF triple store + real SPARQL (rdflib)")
    print("=" * 72)
    rdf_g = build_rdf_graph()
    print(f"RDF graph built: {len(rdf_g)} triples")
    print('SPARQL: drugs treating "Non_small_cell_lung_cancer" + mechanism target:')
    for row in sparql_drugs_for_disease(rdf_g, "Non_small_cell_lung_cancer"):
        print(f"  {row.drugLabel} (via target {row.targetLabel})")
    print('SPARQL: pathways for target "BRAF" + associated diseases:')
    for row in sparql_pathway_for_target(rdf_g, "BRAF"):
        print(f"  pathway={row.pathwayLabel} disease={row.diseaseLabel}")

    print()
    print("=" * 72)
    print("STEP 3: Graph-augmented RAG answer synthesis (no live LLM -- see README)")
    print("=" * 72)
    for query in EXAMPLE_QUERIES:
        print()
        print(synthesize_answer(query, g=g))
        print("-" * 72)

    print()
    print("=" * 72)
    print("STEP 4: Relevance experiment -- graph-augmented vs. flat retrieval")
    print("=" * 72)
    run_experiment()

    print()
    print("No network calls made. No API key used. 100% local computation.")


if __name__ == "__main__":
    main()
