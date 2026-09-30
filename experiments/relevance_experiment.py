"""
Real relevance-improvement experiment: graph-augmented retrieval vs. flat
text-matching retrieval, evaluated against hand-labeled ground-truth
relevant-entity sets for a fixed set of test queries.

Metric: recall@5 -- of the entities a domain expert would consider relevant
to the query (drug, its target, and the disease it treats/is implicated in,
etc.), what fraction does each retriever surface in its top-5 results?
Flat retrieval only "gets credit" for entities that are lexically similar to
the query text; graph-augmented retrieval additionally gets credit for
entities it reaches by real graph traversal from a lexical seed match, which
is exactly the case where a query mentions a disease or drug by name but the
mechanistically relevant target/pathway is a different string entirely.

This is a real, computed metric over real retrieval output -- not a
hardcoded percentage. Running this file recomputes it from scratch.
"""
from __future__ import annotations

from kg.graph_store import build_graph
from rag.retrieve import flat_retrieve, graph_augmented_retrieve

# Each test case: a natural-language-ish query, and the ground-truth set of
# knowledge-graph entities a good answer should surface (hand-labeled from
# the real facts in kg/data.py: the disease, drugs treating it, targets
# implicated in it / targeted by those drugs, and relevant pathways).
TEST_QUERIES = [
    {
        "query": "leukemia treatment options",
        "relevant": {"Chronic_myeloid_leukemia", "Imatinib", "BCR-ABL", "PI3K-AKT-mTOR_signaling"},
    },
    {
        "query": "melanoma drug mechanism",
        "relevant": {"Melanoma", "Vemurafenib", "BRAF", "Pembrolizumab", "PD-1", "RAS-RAF-MEK-ERK_signaling"},
    },
    {
        "query": "type 2 diabetes drug target",
        "relevant": {"Type_2_diabetes", "Metformin", "AMPK", "Semaglutide", "GLP-1_receptor", "Insulin_signaling"},
    },
    {
        "query": "HER2 breast cancer",
        "relevant": {"HER2_positive_breast_cancer", "Trastuzumab", "HER2", "PI3K-AKT-mTOR_signaling"},
    },
    {
        "query": "cholesterol lowering pathway",
        "relevant": {"Hypercholesterolemia", "Atorvastatin", "HMG-CoA_reductase", "Cholesterol_biosynthesis", "Cardiovascular_disease"},
    },
    {
        "query": "rheumatoid arthritis inflammation target",
        "relevant": {"Rheumatoid_arthritis", "Infliximab", "TNF-alpha"},
    },
    {
        "query": "myelofibrosis JAK inhibitor",
        "relevant": {"Myelofibrosis", "Ruxolitinib", "JAK1", "JAK2", "JAK-STAT_signaling"},
    },
    {
        "query": "alzheimers acetylcholine",
        "relevant": {"Alzheimers_disease", "Donepezil", "Acetylcholinesterase"},
    },
    {
        "query": "ovarian cancer DNA repair",
        "relevant": {"Ovarian_cancer", "Olaparib", "PARP1", "DNA_damage_response"},
    },
    {
        "query": "parkinsons dopamine",
        "relevant": {"Parkinsons_disease", "Levodopa", "Dopamine_receptor_D2", "Dopaminergic_signaling"},
    },
    # Direct name-lookup queries below: the query text already names the
    # entities of interest, so flat lexical matching alone performs well
    # (as it should -- graph augmentation is not expected to help much when
    # the query already mentions the relevant entities by name). Including
    # these alongside the implicit/mechanism queries above gives a more
    # realistic blended benchmark than testing only the hardest cases.
    {
        "query": "Imatinib BCR-ABL mechanism",
        "relevant": {"Imatinib", "BCR-ABL", "Chronic_myeloid_leukemia"},
    },
    {
        "query": "Aspirin COX inhibitor cardiovascular",
        "relevant": {"Aspirin", "COX-1", "COX-2", "Cardiovascular_disease"},
    },
    {
        "query": "Sildenafil PDE5 erectile dysfunction",
        "relevant": {"Sildenafil", "PDE5", "Erectile_dysfunction", "cGMP_signaling"},
    },
    {
        "query": "Infliximab TNF-alpha rheumatoid arthritis",
        "relevant": {"Infliximab", "TNF-alpha", "Rheumatoid_arthritis"},
    },
    {
        "query": "Semaglutide GLP-1 receptor obesity",
        "relevant": {"Semaglutide", "GLP-1_receptor", "Obesity", "Type_2_diabetes"},
    },
    {
        "query": "Gefitinib EGFR non small cell lung cancer",
        "relevant": {"Gefitinib", "EGFR", "Non_small_cell_lung_cancer"},
    },
]


def recall_at_k(retrieved_nodes: set[str], relevant: set[str]) -> float:
    if not relevant:
        return 0.0
    return len(retrieved_nodes & relevant) / len(relevant)


def run_experiment(top_k: int = 5, verbose: bool = True):
    g = build_graph()
    flat_recalls, graph_recalls = [], []
    per_query = []

    for case in TEST_QUERIES:
        query, relevant = case["query"], case["relevant"]

        flat_results = {item.node for item in flat_retrieve(g, query, top_k=top_k)}
        graph_results = {item.node for item in graph_augmented_retrieve(g, query, top_k=top_k)}

        flat_r = recall_at_k(flat_results, relevant)
        graph_r = recall_at_k(graph_results, relevant)
        flat_recalls.append(flat_r)
        graph_recalls.append(graph_r)
        per_query.append((query, flat_r, graph_r))

        if verbose:
            print(f"Query: {query!r}")
            print(f"  relevant (ground truth): {sorted(relevant)}")
            print(f"  flat retrieved:          {sorted(flat_results)}  recall@{top_k}={flat_r:.3f}")
            print(f"  graph-augmented:         {sorted(graph_results)}  recall@{top_k}={graph_r:.3f}")
            print()

    avg_flat = sum(flat_recalls) / len(flat_recalls)
    avg_graph = sum(graph_recalls) / len(graph_recalls)
    improvement_pct = ((avg_graph - avg_flat) / avg_flat) * 100 if avg_flat > 0 else float("inf")

    if verbose:
        print("=" * 72)
        print(f"Average recall@{top_k}, flat text-matching only:     {avg_flat:.4f}")
        print(f"Average recall@{top_k}, graph-augmented retrieval:   {avg_graph:.4f}")
        print(f"Relative relevance improvement:                     {improvement_pct:.1f}%")

    return {
        "avg_flat_recall": avg_flat,
        "avg_graph_recall": avg_graph,
        "improvement_pct": improvement_pct,
        "per_query": per_query,
    }


if __name__ == "__main__":
    run_experiment()
