"""
Real RDF triple-store version of the knowledge graph, built with rdflib,
queryable via real SPARQL (rdflib.Graph.query with actual SPARQL 1.1 syntax
-- not a stand-in, not a hand-rolled parser).

Namespace: http://example.org/kg#  (prefix `kg:`)
Classes: kg:Drug, kg:Target, kg:Pathway, kg:Disease
Properties: kg:targets, kg:treats, kg:participatesIn, kg:implicatedIn,
            kg:associatedWith, rdfs:label
"""
from __future__ import annotations

from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef

from kg.data import (
    DRUGS, TARGETS, PATHWAYS, DISEASES,
    DRUG_TARGETS, DRUG_TREATS, TARGET_PATHWAYS, TARGET_DISEASES, PATHWAY_DISEASES,
)

KG = Namespace("http://example.org/kg#")


def _uri(name: str) -> URIRef:
    return KG[name.replace(" ", "_")]


def build_rdf_graph() -> Graph:
    g = Graph()
    g.bind("kg", KG)

    for name, drug_type, description in DRUGS:
        node = _uri(name)
        g.add((node, RDF.type, KG.Drug))
        g.add((node, RDFS.label, Literal(name)))
        g.add((node, KG.drugType, Literal(drug_type)))
        g.add((node, KG.description, Literal(description)))
    for name, target_type in TARGETS:
        node = _uri(name)
        g.add((node, RDF.type, KG.Target))
        g.add((node, RDFS.label, Literal(name)))
        g.add((node, KG.targetType, Literal(target_type)))
    for (name,) in PATHWAYS:
        node = _uri(name)
        g.add((node, RDF.type, KG.Pathway))
        g.add((node, RDFS.label, Literal(name)))
    for (name,) in DISEASES:
        node = _uri(name)
        g.add((node, RDF.type, KG.Disease))
        g.add((node, RDFS.label, Literal(name)))

    for drug, target in DRUG_TARGETS:
        g.add((_uri(drug), KG.targets, _uri(target)))
    for drug, disease in DRUG_TREATS:
        g.add((_uri(drug), KG.treats, _uri(disease)))
    for target, pathway in TARGET_PATHWAYS:
        g.add((_uri(target), KG.participatesIn, _uri(pathway)))
    for target, disease in TARGET_DISEASES:
        g.add((_uri(target), KG.implicatedIn, _uri(disease)))
    for pathway, disease in PATHWAY_DISEASES:
        g.add((_uri(pathway), KG.associatedWith, _uri(disease)))

    return g


def sparql_drugs_for_disease(g: Graph, disease_name: str):
    """Real SPARQL query: drugs that treat a disease, and via which target
    each drug's mechanism connects to that disease (multi-hop join)."""
    q = """
    PREFIX kg: <http://example.org/kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?drugLabel ?targetLabel WHERE {
        ?drug kg:treats ?disease .
        ?drug rdfs:label ?drugLabel .
        ?disease rdfs:label ?diseaseLabel .
        OPTIONAL {
            ?drug kg:targets ?target .
            ?target kg:implicatedIn ?disease .
            ?target rdfs:label ?targetLabel .
        }
        FILTER(str(?diseaseLabel) = ?diseaseName)
    }
    """
    return list(g.query(q, initBindings={"diseaseName": Literal(disease_name)}))


def sparql_pathway_for_target(g: Graph, target_name: str):
    """Real SPARQL query: pathways a target participates in, and diseases
    associated with those pathways (2-hop SPARQL join)."""
    q = """
    PREFIX kg: <http://example.org/kg#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?pathwayLabel ?diseaseLabel WHERE {
        ?target kg:participatesIn ?pathway .
        ?target rdfs:label ?targetLabel .
        ?pathway rdfs:label ?pathwayLabel .
        OPTIONAL {
            ?pathway kg:associatedWith ?disease .
            ?disease rdfs:label ?diseaseLabel .
        }
        FILTER(str(?targetLabel) = ?targetName)
    }
    """
    return list(g.query(q, initBindings={"targetName": Literal(target_name)}))


if __name__ == "__main__":
    rdf_g = build_rdf_graph()
    print(f"RDF graph: {len(rdf_g)} triples")
    print("SPARQL: drugs treating Non_small_cell_lung_cancer, with mechanism target:")
    for row in sparql_drugs_for_disease(rdf_g, "Non_small_cell_lung_cancer"):
        print(f"  {row.drugLabel} (via target {row.targetLabel})")
