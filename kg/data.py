"""
Real (hand-curated, factual, small) drug-discovery domain data.

Entities: Drug, Target (protein/gene), Pathway, Disease.
Relationships:
    Drug   --TARGETS-->        Target
    Drug   --TREATS-->         Disease
    Target --PARTICIPATES_IN--> Pathway
    Target --IMPLICATED_IN-->  Disease
    Pathway--ASSOCIATED_WITH--> Disease

The facts below are real, publicly known drug/target/pathway/disease
relationships (simplified for a compact demo graph) -- not synthetic
placeholder text. Kept intentionally small (~50 entities, ~70 edges) so the
graph, SPARQL store, and retrieval logic are easy to inspect and verify by
hand.
"""

DRUGS = [
    ("Imatinib", "small_molecule", "Tyrosine kinase inhibitor"),
    ("Gefitinib", "small_molecule", "EGFR tyrosine kinase inhibitor"),
    ("Trastuzumab", "monoclonal_antibody", "Anti-HER2 antibody"),
    ("Vemurafenib", "small_molecule", "BRAF kinase inhibitor"),
    ("Pembrolizumab", "monoclonal_antibody", "Anti-PD-1 checkpoint inhibitor"),
    ("Metformin", "small_molecule", "Biguanide antihyperglycemic"),
    ("Atorvastatin", "small_molecule", "HMG-CoA reductase inhibitor"),
    ("Sildenafil", "small_molecule", "PDE5 inhibitor"),
    ("Aspirin", "small_molecule", "COX inhibitor / NSAID"),
    ("Levodopa", "small_molecule", "Dopamine precursor"),
    ("Donepezil", "small_molecule", "Acetylcholinesterase inhibitor"),
    ("Infliximab", "monoclonal_antibody", "Anti-TNF-alpha antibody"),
    ("Ruxolitinib", "small_molecule", "JAK1/JAK2 inhibitor"),
    ("Olaparib", "small_molecule", "PARP inhibitor"),
    ("Semaglutide", "peptide", "GLP-1 receptor agonist"),
]

TARGETS = [
    ("BCR-ABL", "fusion_kinase"),
    ("EGFR", "receptor_tyrosine_kinase"),
    ("HER2", "receptor_tyrosine_kinase"),
    ("BRAF", "serine_threonine_kinase"),
    ("PD-1", "immune_checkpoint_receptor"),
    ("AMPK", "kinase"),
    ("HMG-CoA_reductase", "enzyme"),
    ("PDE5", "enzyme"),
    ("COX-1", "enzyme"),
    ("COX-2", "enzyme"),
    ("Dopamine_receptor_D2", "gpcr"),
    ("Acetylcholinesterase", "enzyme"),
    ("TNF-alpha", "cytokine"),
    ("JAK1", "kinase"),
    ("JAK2", "kinase"),
    ("PARP1", "enzyme"),
    ("GLP-1_receptor", "gpcr"),
]

PATHWAYS = [
    ("RAS-RAF-MEK-ERK_signaling",),
    ("PI3K-AKT-mTOR_signaling",),
    ("JAK-STAT_signaling",),
    ("Cholesterol_biosynthesis",),
    ("cGMP_signaling",),
    ("Arachidonic_acid_metabolism",),
    ("Dopaminergic_signaling",),
    ("DNA_damage_response",),
    ("Insulin_signaling",),
    ("Immune_checkpoint_regulation",),
]

DISEASES = [
    ("Chronic_myeloid_leukemia",),
    ("Non_small_cell_lung_cancer",),
    ("HER2_positive_breast_cancer",),
    ("Melanoma",),
    ("Type_2_diabetes",),
    ("Hypercholesterolemia",),
    ("Erectile_dysfunction",),
    ("Cardiovascular_disease",),
    ("Parkinsons_disease",),
    ("Alzheimers_disease",),
    ("Rheumatoid_arthritis",),
    ("Myelofibrosis",),
    ("Ovarian_cancer",),
    ("Obesity",),
]

# Drug -> Target
DRUG_TARGETS = [
    ("Imatinib", "BCR-ABL"),
    ("Gefitinib", "EGFR"),
    ("Trastuzumab", "HER2"),
    ("Vemurafenib", "BRAF"),
    ("Pembrolizumab", "PD-1"),
    ("Metformin", "AMPK"),
    ("Atorvastatin", "HMG-CoA_reductase"),
    ("Sildenafil", "PDE5"),
    ("Aspirin", "COX-1"),
    ("Aspirin", "COX-2"),
    ("Levodopa", "Dopamine_receptor_D2"),
    ("Donepezil", "Acetylcholinesterase"),
    ("Infliximab", "TNF-alpha"),
    ("Ruxolitinib", "JAK1"),
    ("Ruxolitinib", "JAK2"),
    ("Olaparib", "PARP1"),
    ("Semaglutide", "GLP-1_receptor"),
]

# Drug -> Disease (indication)
DRUG_TREATS = [
    ("Imatinib", "Chronic_myeloid_leukemia"),
    ("Gefitinib", "Non_small_cell_lung_cancer"),
    ("Trastuzumab", "HER2_positive_breast_cancer"),
    ("Vemurafenib", "Melanoma"),
    ("Pembrolizumab", "Melanoma"),
    ("Pembrolizumab", "Non_small_cell_lung_cancer"),
    ("Metformin", "Type_2_diabetes"),
    ("Atorvastatin", "Hypercholesterolemia"),
    ("Atorvastatin", "Cardiovascular_disease"),
    ("Sildenafil", "Erectile_dysfunction"),
    ("Aspirin", "Cardiovascular_disease"),
    ("Levodopa", "Parkinsons_disease"),
    ("Donepezil", "Alzheimers_disease"),
    ("Infliximab", "Rheumatoid_arthritis"),
    ("Ruxolitinib", "Myelofibrosis"),
    ("Olaparib", "Ovarian_cancer"),
    ("Semaglutide", "Type_2_diabetes"),
    ("Semaglutide", "Obesity"),
]

# Target -> Pathway
TARGET_PATHWAYS = [
    ("BCR-ABL", "RAS-RAF-MEK-ERK_signaling"),
    ("BCR-ABL", "PI3K-AKT-mTOR_signaling"),
    ("EGFR", "RAS-RAF-MEK-ERK_signaling"),
    ("EGFR", "PI3K-AKT-mTOR_signaling"),
    ("HER2", "PI3K-AKT-mTOR_signaling"),
    ("BRAF", "RAS-RAF-MEK-ERK_signaling"),
    ("PD-1", "Immune_checkpoint_regulation"),
    ("AMPK", "Insulin_signaling"),
    ("HMG-CoA_reductase", "Cholesterol_biosynthesis"),
    ("PDE5", "cGMP_signaling"),
    ("COX-1", "Arachidonic_acid_metabolism"),
    ("COX-2", "Arachidonic_acid_metabolism"),
    ("Dopamine_receptor_D2", "Dopaminergic_signaling"),
    ("JAK1", "JAK-STAT_signaling"),
    ("JAK2", "JAK-STAT_signaling"),
    ("PARP1", "DNA_damage_response"),
    ("GLP-1_receptor", "Insulin_signaling"),
]

# Target -> Disease (implicated in)
TARGET_DISEASES = [
    ("BCR-ABL", "Chronic_myeloid_leukemia"),
    ("EGFR", "Non_small_cell_lung_cancer"),
    ("HER2", "HER2_positive_breast_cancer"),
    ("BRAF", "Melanoma"),
    ("PD-1", "Melanoma"),
    ("PD-1", "Non_small_cell_lung_cancer"),
    ("AMPK", "Type_2_diabetes"),
    ("HMG-CoA_reductase", "Hypercholesterolemia"),
    ("TNF-alpha", "Rheumatoid_arthritis"),
    ("JAK1", "Myelofibrosis"),
    ("JAK2", "Myelofibrosis"),
    ("PARP1", "Ovarian_cancer"),
    ("Dopamine_receptor_D2", "Parkinsons_disease"),
    ("Acetylcholinesterase", "Alzheimers_disease"),
    ("GLP-1_receptor", "Obesity"),
]

# Pathway -> Disease
PATHWAY_DISEASES = [
    ("RAS-RAF-MEK-ERK_signaling", "Melanoma"),
    ("RAS-RAF-MEK-ERK_signaling", "Non_small_cell_lung_cancer"),
    ("PI3K-AKT-mTOR_signaling", "HER2_positive_breast_cancer"),
    ("PI3K-AKT-mTOR_signaling", "Chronic_myeloid_leukemia"),
    ("JAK-STAT_signaling", "Myelofibrosis"),
    ("Cholesterol_biosynthesis", "Hypercholesterolemia"),
    ("Cholesterol_biosynthesis", "Cardiovascular_disease"),
    ("cGMP_signaling", "Erectile_dysfunction"),
    ("Arachidonic_acid_metabolism", "Cardiovascular_disease"),
    ("Dopaminergic_signaling", "Parkinsons_disease"),
    ("DNA_damage_response", "Ovarian_cancer"),
    ("Insulin_signaling", "Type_2_diabetes"),
    ("Insulin_signaling", "Obesity"),
    ("Immune_checkpoint_regulation", "Melanoma"),
]
