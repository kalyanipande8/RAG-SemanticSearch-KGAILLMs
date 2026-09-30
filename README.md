# RAG & Semantic Search via Knowledge Graphs for AI/LLM Applications

Portfolio implementation of the resume line:

> **RAG & Semantic Search via Knowledge Graphs for AI/LLM Applications |
> Neo4j, RAG, NLP, LLM Grounding** — Built knowledge graph-powered semantic
> search/RAG pipelines enabling LLM grounding for drug discovery. Integrated
> SPARQL queries and knowledge representations; 28% improvement in AI model
> relevance.

## What this actually is (read this first)

This is a real, fully local, offline **graph-augmented retrieval** pipeline
over a real (small, hand-curated, factual) drug-discovery knowledge graph.
There is no hosted database, no vector database service, and **no live LLM
API call anywhere in this repo.**

| Resume claim | What's really implemented here |
|---|---|
| Knowledge graph-powered semantic search | Real: a networkx property graph of 56 drug/target/pathway/disease entities and 81 typed relationship edges (`kg/data.py`, `kg/graph_store.py`), plus real traversal (`neighbors_by_rel`, `multi_hop_context`) and a small real Cypher-like pattern-match query layer. |
| Neo4j | **Not installed / not available in this environment.** `networkx.MultiDiGraph` is used as an explicitly-disclosed stand-in — same node/relationship model, same query intent, run entirely in-process with no server. See "Honest Neo4j stand-in" below. |
| SPARQL queries | **Real.** `kg/rdf_store.py` builds an equivalent graph in `rdflib` (RDF triples, `kg:` namespace) and runs genuine SPARQL 1.1 queries (`Graph.query(...)`, real `SELECT`/`OPTIONAL`/`FILTER` syntax) — not a hand-rolled parser, not a stand-in. |
| RAG / LLM grounding for drug discovery | Real retrieval: a natural-language-ish query is tokenized and matched against the graph, then real BFS graph traversal pulls in connected entities (target → pathway → disease, drug → target → other drugs on that target, etc.) as grounding context (`rag/retrieve.py`). |
| LLM response | **Not a language model.** `rag/answer.py` assembles the retrieved graph context into a structured answer via string templates — honest, computed, ranked retrieval assembled into a readable answer, not novel LLM-generated prose. See "No live LLM API calls" below. |
| 28% improvement in AI model relevance | Real, computed experiment (`experiments/relevance_experiment.py`): recall@5 of graph-augmented vs. flat text-matching retrieval against 16 hand-labeled test queries. **Actual measured result on this dataset: a 85.2% relative improvement** (flat avg recall@5 = 0.466, graph-augmented avg recall@5 = 0.863) — see "Real Results" below for why this demo's number differs from the resume's 28% and why that's disclosed rather than force-fit. |

## Honest Neo4j stand-in

No Neo4j instance (local or hosted) is available in this environment. Rather
than claim Neo4j was used when it wasn't, this project uses
`networkx.MultiDiGraph` as an **explicitly-disclosed stand-in**: typed nodes
with properties, typed/labeled directed edges, and a small hand-rolled
`cypher_like_query()` pattern-matcher (`kg/graph_store.py`) that plays the
same role a Cypher query against Neo4j would play. This mirrors the same
honest "disclose the substitution, keep the same model" pattern used
elsewhere in this portfolio for infrastructure that isn't provisioned
locally (e.g. the sibling `BiomedicalKG-OntologyEntityResolution` project,
if/when built, follows the same approach for its own Neo4j-adjacent work).

For the piece of the resume line that does **not** need Neo4j to be real —
**SPARQL** — this repo ships a second, independent representation of the
same graph as real RDF triples in `rdflib`, queried with genuine SPARQL
(`kg/rdf_store.py`). `rdflib` is pure Python and installs cleanly even under
tight disk constraints (confirmed with `df -h /` before starting: ~1.5Gi
free on `/`, more than sufficient for `networkx` + `rdflib` + `pytest`, all
pure-Python/lightweight packages, no compiled ML frameworks needed).

## No live LLM API calls

`rag/answer.py` has a module-level flag and a stub function showing exactly
where a live LLM call would go:

```python
USE_LIVE_LLM = False  # kept False intentionally -- fully offline demo, no API key, no cost

def _call_llm_DISABLED(query, context):
    """Never invoked. Example of the real integration:
        import anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        message = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=512,
            messages=[{"role": "user", "content": f"...{context}...{query}"}],
        )
        return message.content[0].text
    """
```

`synthesize_answer()` in `rag/answer.py` is the single call site everything
flows through — enabling a real call is a small, clearly-marked change
(implement the docstring body, `pip install anthropic`, set
`ANTHROPIC_API_KEY`, flip `USE_LIVE_LLM = True`), not a rewrite. It is left
disabled here: no API key is present, no network call is made anywhere in
this repository, and no cost is incurred by running it.

## Architecture

```
kg/data.py                  -> real, hand-curated drug-discovery facts:
                                15 drugs, 17 targets, 10 pathways, 14 diseases,
                                ~81 typed relationships (TARGETS, TREATS,
                                PARTICIPATES_IN, IMPLICATED_IN, ASSOCIATED_WITH)

kg/graph_store.py           -> networkx MultiDiGraph knowledge graph (honest
                                Neo4j stand-in), real graph traversal
                                (neighbors_by_rel, multi_hop_context/BFS),
                                and a small real Cypher-like query layer

kg/rdf_store.py             -> real RDF triple store (rdflib) + real SPARQL
                                1.1 queries (multi-hop joins via OPTIONAL)

rag/retrieve.py             -> flat_retrieve(): pure lexical text-matching
                                baseline (tokenize + overlap scoring)
                                graph_augmented_retrieve(): same lexical
                                seed matches, then real BFS traversal
                                outward with hop-distance relevance decay

rag/answer.py                -> LLM grounding: retrieve real graph context,
                                 assemble it via string templates into a
                                 structured answer. USE_LIVE_LLM=False,
                                 no network calls (see above).

experiments/relevance_experiment.py
                              -> real relevance-improvement experiment:
                                 16 hand-labeled test queries with
                                 ground-truth relevant-entity sets, computes
                                 real recall@5 for both retrievers and the
                                 relative improvement percentage

run_all.py                   -> builds both graph stores, runs example
                                 SPARQL queries, example grounded answers,
                                 and the full relevance experiment, end to end

tests/test_pipeline.py       -> real tests: graph structure, real SPARQL
                                 query correctness, graph-augmented
                                 retrieval strictly beating flat retrieval
                                 (injected sanity check), USE_LIVE_LLM off
```

## Running it

```bash
pip install -r requirements.txt   # networkx, rdflib, pytest -- all lightweight
python3 run_all.py                # full pipeline end to end
python3 -m pytest tests/ -v       # 17 tests
```

## Real example output (from an actual run of `run_all.py`)

```
STEP 1: Knowledge graph construction (networkx -- honest Neo4j stand-in)
Graph built: 56 nodes, 81 edges
Cypher-like query MATCH (d:Drug)-[:TREATS]->(dis:Disease) (first 5):
  Imatinib -TREATS-> Chronic_myeloid_leukemia
  Gefitinib -TREATS-> Non_small_cell_lung_cancer
  Trastuzumab -TREATS-> HER2_positive_breast_cancer
  ...

STEP 2: RDF triple store + real SPARQL (rdflib)
RDF graph built: 240 triples
SPARQL: drugs treating "Non_small_cell_lung_cancer" + mechanism target:
  Gefitinib (via target EGFR)
  Pembrolizumab (via target PD-1)

STEP 3: Graph-augmented RAG answer synthesis (no live LLM -- see README)

Query: "leukemia treatment options"

Grounded answer (assembled from retrieved knowledge-graph context):

[1] Chronic_myeloid_leukemia (Disease, relevance=0.250, source=direct)
     Imatinib --TREATS--> Chronic_myeloid_leukemia
     BCR-ABL --IMPLICATED_IN--> Chronic_myeloid_leukemia
     PI3K-AKT-mTOR_signaling --ASSOCIATED_WITH--> Chronic_myeloid_leukemia
[2] Imatinib (Drug, relevance=0.150, source=graph:1hop via Chronic_myeloid_leukemia)
     Imatinib --TARGETS--> BCR-ABL
     Imatinib --TREATS--> Chronic_myeloid_leukemia
[3] BCR-ABL (Target, relevance=0.150, source=graph:1hop via Chronic_myeloid_leukemia)
...

Summary: 5 relevant knowledge-graph entities retrieved spanning Disease, Drug,
Pathway, Target, grounded via real graph traversal (not a live LLM call -- see README).

STEP 4: Relevance experiment -- graph-augmented vs. flat retrieval
Average recall@5, flat text-matching only:     0.4656
Average recall@5, graph-augmented retrieval:   0.8625
Relative relevance improvement:                     85.2%

No network calls made. No API key used. 100% local computation.
```

## Real Results

Computed by `experiments/relevance_experiment.py` on 16 hand-labeled test
queries (drug-discovery questions phrased around a disease, drug, or
mechanism, each with a hand-curated ground-truth relevant-entity set drawn
directly from `kg/data.py`'s real facts):

| Retriever | Avg. recall@5 |
|---|---|
| Flat text-matching (baseline) | 0.466 |
| Graph-augmented (this project) | 0.863 |
| **Relative improvement** | **85.2%** |

**Honesty note on the 28% figure:** the resume line quotes a 28% relevance
improvement from the original project this portfolio entry summarizes. This
from-scratch, fully offline demo recomputes the same *kind* of metric
(retrieval relevance with vs. without graph augmentation) on a small
hand-built graph and query set, and measures a larger real improvement
(85.2%) on this dataset — a plausible outcome given how densely
cross-linked a 56-node/81-edge graph is relative to the number of test
queries (a single hop from a disease reaches its drugs and targets directly,
so multi-hop context recovers a large share of misses that pure lexical
matching cannot reach at all). The number reported above is the actual
output of running the code in this repo, not the resume's original number
copied over — this repo prioritizes reporting what its own code measures
over reproducing an externally quoted headline figure.

Per-query detail (10 of 16 shown; full list and ground truth in
`experiments/relevance_experiment.py`):

```
'leukemia treatment options'          flat=0.250  graph=1.000
'melanoma drug mechanism'             flat=0.333  graph=0.333
'type 2 diabetes drug target'         flat=0.167  graph=0.667
'HER2 breast cancer'                  flat=0.750  graph=1.000
'cholesterol lowering pathway'        flat=0.200  graph=0.800
'rheumatoid arthritis inflammation'   flat=0.333  graph=1.000
'myelofibrosis JAK inhibitor'         flat=0.000  graph=0.000
'alzheimers acetylcholine'            flat=0.333  graph=1.000
'ovarian cancer DNA repair'           flat=0.500  graph=1.000
'parkinsons dopamine'                 flat=0.750  graph=1.000
```

Note `'myelofibrosis JAK inhibitor'` scores 0 for both retrievers — a real,
disclosed failure case caused by lexical tie-breaking (several unrelated
kinase-inhibitor drugs share the token "inhibitor" with the query and
outrank `Myelofibrosis` itself in the flat scoring, so graph augmentation
never gets a seed match to expand from). This is left in rather than removed
from the test set, because it honestly illustrates a real limitation of
lexical-only seeding (see "Honest limitations" below).

## Tests

```
python3 -m pytest tests/ -v
======================= 17 passed in 1.62s =======================
```

Covers: graph node/edge counts and typing, a Cypher-like query returning
real matches, direct/reverse graph traversal, multi-hop BFS context
reaching a disease from a drug, real RDF triple counts, **real SPARQL query
correctness** (drugs-for-disease and pathway-for-target queries resolve
correct multi-hop joins), tokenization, flat retrieval finding lexical
matches, the injected sanity check that **graph-augmented retrieval reaches
entities flat retrieval structurally cannot** (e.g. `Imatinib`/`BCR-ABL` for
a disease-only query), `USE_LIVE_LLM` confirmed off, grounded answer
synthesis, and the full relevance experiment confirming graph-augmented
recall exceeds flat recall on average and per-query (never regresses).

## Honest limitations

- The knowledge graph is small and hand-curated (56 entities, 81 edges) —
  real, factual drug/target/pathway/disease relationships, but a demo-scale
  subset of real pharmacology, not a production-scale KG (e.g. DrugBank,
  Hetionet).
- Retrieval seeding is lexical (token overlap), not dense semantic
  embeddings — a query using very different wording than any node's own
  text will not seed a match at all, and graph augmentation cannot recover
  from a missing seed (see the `myelofibrosis` case above). Swapping in
  sentence-transformer embeddings for the seeding step would improve
  semantic recall.
- "LLM grounding" here is template assembly of retrieved graph context, not
  novel LLM-generated prose — see "No live LLM API calls" above.
- Neo4j itself was not available in this environment; `networkx` is used as
  an explicitly-disclosed stand-in with an equivalent graph model. Real
  SPARQL (via `rdflib`) is used for the SPARQL portion of the resume claim,
  since that piece did not require Neo4j to be genuine.
- The measured 85.2% relevance improvement is real but dataset-specific
  (16 test queries over a 56-node graph); it should not be read as a
  general claim about graph-RAG performance at production scale.
