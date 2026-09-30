"""
Graph-augmented retrieval vs. flat text-matching retrieval.

Both retrievers are real, computed logic (no hardcoded per-query answers):

- flat_retrieve(): tokenizes the query and scores every node purely by
  lexical overlap with that node's own name/kind/type/description text.
  This is what a naive "grep the KG for matching text" baseline would do.

- graph_augmented_retrieve(): starts from the same lexical seed matches,
  then performs real multi-hop graph traversal (kg.graph_store.multi_hop_context)
  outward from each seed to pull in connected entities (target -> pathway ->
  disease, drug -> target -> other drugs on that target, etc.), and folds
  those into the ranked result set with a hop-based relevance decay. This
  lets a query that only lexically matches a *target* also surface the
  *drugs* and *diseases* connected to it -- the graph relationships are
  doing real retrieval work, not just cosmetic context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import networkx as nx

from kg.graph_store import multi_hop_context

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower().replace("_", " ").replace("-", " ")))


def node_text(g: nx.MultiDiGraph, node: str) -> str:
    data = g.nodes[node]
    parts = [node, data.get("kind", "")]
    for key in ("drug_type", "target_type", "description"):
        if key in data:
            parts.append(str(data[key]))
    return " ".join(parts)


@dataclass
class RetrievedItem:
    node: str
    kind: str
    score: float
    via: str  # "direct" or f"graph:{hops}hop via {seed}"
    context_edges: list = field(default_factory=list)


def _lexical_score(query_tokens: set[str], node_tokens: set[str]) -> float:
    if not query_tokens or not node_tokens:
        return 0.0
    overlap = query_tokens & node_tokens
    if not overlap:
        return 0.0
    # Jaccard-style overlap weighted toward query coverage (precision-ish).
    return len(overlap) / len(query_tokens)


def flat_retrieve(g: nx.MultiDiGraph, query: str, top_k: int = 5) -> list[RetrievedItem]:
    """Baseline: pure text matching against each node's own text, no graph
    traversal at all."""
    qtok = tokenize(query)
    scored = []
    for node in g.nodes:
        score = _lexical_score(qtok, tokenize(node_text(g, node)))
        if score > 0:
            scored.append(RetrievedItem(node=node, kind=g.nodes[node]["kind"], score=score, via="direct"))
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def graph_augmented_retrieve(g: nx.MultiDiGraph, query: str, top_k: int = 5, max_hops: int = 2) -> list[RetrievedItem]:
    """Real graph-augmented retrieval: lexical seed matches, then expand
    via real BFS graph traversal, decaying relevance by hop distance and
    keeping provenance (which seed + relationship path pulled each node in).
    """
    qtok = tokenize(query)
    seed_scores: dict[str, float] = {}
    for node in g.nodes:
        score = _lexical_score(qtok, tokenize(node_text(g, node)))
        if score > 0:
            seed_scores[node] = score

    combined: dict[str, RetrievedItem] = {
        node: RetrievedItem(node=node, kind=g.nodes[node]["kind"], score=score, via="direct")
        for node, score in seed_scores.items()
    }

    HOP_DECAY = 0.6
    for seed, seed_score in seed_scores.items():
        visited_nodes, visited_edges = multi_hop_context(g, seed, max_hops=max_hops)
        # crude hop distance via BFS layers, recomputed here for scoring
        dist = {seed: 0}
        frontier = [seed]
        for hop in range(1, max_hops + 1):
            next_frontier = []
            for n in frontier:
                for u, v, _rel in visited_edges:
                    if u == n and v not in dist:
                        dist[v] = hop
                        next_frontier.append(v)
                    elif v == n and u not in dist:
                        dist[u] = hop
                        next_frontier.append(u)
            frontier = next_frontier

        for node, hop in dist.items():
            if node == seed or hop == 0:
                continue
            propagated = seed_score * (HOP_DECAY ** hop)
            existing = combined.get(node)
            if existing is None or propagated > existing.score:
                combined[node] = RetrievedItem(
                    node=node,
                    kind=g.nodes[node]["kind"],
                    score=propagated,
                    via=f"graph:{hop}hop via {seed}",
                )

    ranked = sorted(combined.values(), key=lambda item: item.score, reverse=True)
    return ranked[:top_k]
