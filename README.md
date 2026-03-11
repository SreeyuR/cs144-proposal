# CS 144 Project Proposal — Proof of Concept

Proof-of-concept implementations for our CS 144 Networks project proposal.

---

## Overview

This repo contains two exploratory projects demonstrating network analysis techniques:

| Project | Description |
|---------|-------------|
| **epstein/** | Extracts person names from court document PDFs and builds a name co-occurrence network (who appears in the same documents). Uses baby-name data to filter likely person names. |
| **fashion/** | Heterogeneous graph of users and sellers with friendship and purchase edges. Explores user–seller relationships and style-based recommendations. |

---

## Running

### Epstein (name extraction + co-occurrence graph)

```bash
cd epstein
python main.py
```

### Fashion (user–seller network)

```bash
cd fashion
python main.py
```

---

## Output

- **epstein**: `name_network.png`
- **fashion**: `fashion_graph.png`, `soft_bipartite_fashion_network.png`
