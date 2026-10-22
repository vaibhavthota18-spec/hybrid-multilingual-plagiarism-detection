# Dataset Design, Taxonomy, and Provenance

## 1. Overview of Benchmark Dataset V1

The primary evaluation artifact is `data/evaluation/benchmark_dataset_v1.json`. It is a machine-readable, schema-validated corpus containing **40 carefully constructed passage pairs** spanning multiple domains, difficulty tiers, and language combinations across **English, Hindi, and Telugu**.

```
Total Examples: 40
├── Calibration Partition: 20 examples (11 Positives, 9 Negatives)
└── Held-Out Evaluation Partition: 20 examples (11 Positives, 9 Negatives)
```

---

## 2. Plagiarism Taxonomy Breakdown

The corpus spans 6 distinct categories:

| Category | Count (Calib + Held) | Ground Truth Label | Description |
| :--- | :---: | :---: | :--- |
| `exact` | 3 (1 + 2) | `True` | Verbatim copied text (English, Hindi, Telugu). |
| `near_exact` | 2 (1 + 1) | `True` | Minor synonym substitutions, punctuation insertion. |
| `paraphrase` | 9 (5 + 4) | `True` | Structural rephrasing, clause inversion, semantic equivalence. |
| `translation` | 8 (4 + 4) | `True` | Cross-lingual translations (EN↔HI, EN↔TE, HI↔TE). |
| `hard_negative` | 12 (6 + 6) | `False` | Shared domain terminology but opposite meaning or negated facts. |
| `unrelated_control`| 6 (3 + 3) | `False` | Completely disjoint domains (e.g., Cryptography vs. Gardening). |

---

## 3. Multilingual Coverage Matrix

| Language Pair | Calibration Examples | Held-Out Examples | Total Examples |
| :---: | :---: | :---: | :---: |
| **English - English (`en-en`)** | 8 | 8 | 16 |
| **Hindi - Hindi (`hi-hi`)** | 3 | 3 | 6 |
| **Telugu - Telugu (`te-te`)** | 3 | 3 | 6 |
| **English - Hindi (`en-hi` / `hi-en`)** | 3 | 2 | 5 |
| **English - Telugu (`en-te` / `te-en`)** | 2 | 3 | 5 |
| **Hindi - Telugu (`hi-te` / `te-hi`)** | 1 | 1 | 2 |
| **Total** | **20** | **20** | **40** |

---

## 4. Provenance and Knowledge Domains

All texts originate from verifiable public academic, technical, and regulatory literature:
- **Computer Science & AI**: Attention mechanisms (Vaswani et al.), Paxos consensus (Lamport), Reinforcement Learning (Sutton & Barto), Pattern Recognition (Bishop).
- **Academic Ethics**: UGC Academic Integrity Guidelines (English, Hindi, Telugu), Research Ethics Review Board policies.
- **Physical & Earth Sciences**: Climate reports (IPCC), Hydrology (Ministry of Jal Shakti), Renewable energy (TERI), Photonics and Astrophysics (ISRO).
- **Life Sciences & Health**: OpenStax Biology 2e, Medical Immunology, Nutrition and Cardiovascular physiology.
- **Humanities & Cultural Heritage**: Classical Telugu poetry (Kavitrayam), Sanskrit epics (Kalidasa's Meghadutam), Kuchipudi classical arts.
