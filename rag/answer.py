"""
LLM grounding / answer synthesis.

USE_LIVE_LLM = False is intentional -- see README "No live LLM API" section.
No network calls are made anywhere in this repo. The "LLM grounding" step
is real: retrieved graph context (entities + relationship edges from
kg/graph_store.py) is assembled via string templates into a structured,
readable answer -- honest template-based synthesis, not a language model
generating novel prose.
"""
from __future__ import annotations

import networkx as nx

from kg.graph_store import build_graph, neighbors_by_rel
from rag.retrieve import RetrievedItem, graph_augmented_retrieve

USE_LIVE_LLM = False  # kept False intentionally -- fully offline demo, no API key, no cost


def _call_llm_DISABLED(query: str, context: str) -> str:
    """Never invoked. Example of the real integration this would enable:

        import anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content":
                f"Using only this knowledge graph context, answer the query.\\n\\n"
                f"Context:\\n{context}\\n\\nQuery: {query}"}],
        )
        return message.content[0].text
    """
    raise RuntimeError("Live LLM calls are disabled in this offline portfolio demo.")


def _describe_edges(g: nx.MultiDiGraph, node: str) -> list[str]:
    lines = []
    for other, rel in neighbors_by_rel(g, node):
        lines.append(f"{node} --{rel}--> {other}")
    for other, rel in neighbors_by_rel(g, node, reverse=True):
        lines.append(f"{other} --{rel}--> {node}")
    return lines


def synthesize_answer(query: str, g: nx.MultiDiGraph | None = None, top_k: int = 5) -> str:
    """Retrieves graph-augmented context for `query` and assembles a
    structured, template-based answer grounded in that context."""
    g = g or build_graph()
    results = graph_augmented_retrieve(g, query, top_k=top_k)

    if not results:
        return f'No knowledge-graph entities matched the query "{query}".'

    lines = [f'Query: "{query}"', "", "Grounded answer (assembled from retrieved knowledge-graph context):", ""]
    for i, item in enumerate(results, 1):
        edges = _describe_edges(g, item.node)
        lines.append(f"[{i}] {item.node} ({item.kind}, relevance={item.score:.3f}, source={item.via})")
        for edge_line in edges[:4]:
            lines.append(f"     {edge_line}")

    top_kinds = sorted({item.kind for item in results})
    lines.append("")
    lines.append(
        f"Summary: {len(results)} relevant knowledge-graph entit"
        f"{'y' if len(results) == 1 else 'ies'} retrieved spanning {', '.join(top_kinds)}, "
        f"grounded via real graph traversal (not a live LLM call -- see README)."
    )

    if USE_LIVE_LLM:  # pragma: no cover - intentionally disabled/unreachable
        context = "\n".join(lines)
        return _call_llm_DISABLED(query, context)

    return "\n".join(lines)
