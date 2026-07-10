# Multi-Source Candidate Data Transformer

Deterministic candidate data transformation pipeline.

## Overview

Recruiting pipelines pull candidate data from many places, recruiter CSVs, ATS systems, GitHub, LinkedIn, and resumes, and the same person can appear differently or with conflicting information across sources. This project turns that mess into one trustworthy profile per candidate, where every field is traceable to where it came from, how it was produced, and how confident the system is in it.

**Sources implemented:**
- **Recruiter CSV** (structured)
- **GitHub Public Profile API** (unstructured, field names do not map directly to the canonical schema, the bio is free text, and skills are inferred from repository languages rather than directly stated)

---

## Features

- Multi-source candidate ingestion (CSV + GitHub)
- Canonical candidate schema
- Deterministic merge & conflict resolution
- Field-level provenance tracking
- Rule-based confidence scoring
- Runtime-configurable output schema
- Validation and graceful error handling

---

## Architecture

```text
Recruiter CSV        GitHub URL
      │                  │
      ▼                  ▼
CSV Parser         GitHub Parser
      │                  │
      └────────┬─────────┘
               ▼
      Raw Candidate Data
               │
               ▼
          Normalizer
               │
               ▼
             Merger
               │
               ▼
     Canonical Candidate
               │
               ▼
     Confidence Scorer
               │
               ▼
 Projection Layer (config.json)
               │
               ▼
      Schema Validator
               │
               ▼
          Final JSON
```
---

## Merge / Conflict-Resolution Policy

| Field | Strategy |
|---|---|
| `full_name` | Priority pick: CSV → GitHub | 
| `emails` | Union, deduplicated, normalized |
| `phones` | Union, normalized to E.164, deduplicated |
| `location` | First non-null in priority order |
| `links` | Merge by type (linkedin/github/portfolio)|
| `skills` | Union, confidence-weighted |

Source priority order: `recruiter_csv → linkedin → github → resume → recruiter_notes`. Recruiter-entered data is trusted most because it reflects direct human verification. GitHub-inferred data, such as repository languages used as inferred skills, is treated as weaker evidence.

**Provenance** is recorded per field as `{field, value, source, method}`, not just a source name, so every value is fully traceable to the method that produced it (`priority_pick`, `union_deduplicated`, `union_weighted`, `merge_by_type`).

---


## Configurable Output (Projection Layer)

The projection layer reads a runtime `config.json` and reshapes the canonical candidate into different output schemas without changing the transformation engine.

Runtime behaviour is controlled by `config.json`, supporting:

- Field selection/remapping
- Nested path access
- Per-field normalization
- Provenance/confidence toggles
- Missing-value policies (`null`, `omit`, `error`)


Two configs are included: `config.json` (full canonical output) and `config_custom.json` (subset, renamed fields, no provenance/confidence, omits missing values). This demonstrates the same engine producing multiple valid output schemas without any code changes.

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run with default config
```bash
python main.py --csv data/samples/candidates.csv --config config.json --output data/outputs/output.json
```

### 3. Run with custom config (demonstrates reshaping)
```bash
python main.py --csv data/samples/candidates.csv --config config_custom.json --output data/outputs/custom_output.json
```


### 4. Run tests

Run the test suite:

```bash
pytest tests/ -v
```

The test suite covers:
- Normalization
- Merge logic
- Pipeline edge cases

**CLI arguments:**
| Flag | Default | Description |
|---|---|---|
| `--csv` | required | Path to recruiter CSV |
| `--config` | `config.json` | Path to output config JSON |
| `--output` | `data/outputs/output.json` | Where to write the result |

---

## Sample Output

Running the provided sample dataset generates:

- `data/outputs/output.json` (default canonical output)
- `data/outputs/custom_output.json` (custom projected output using `config_custom.json`)

---

## Folder Structure

```text
eightfold-candidate-transformer/
├── data/
│   ├── samples/
│   │   └── candidates.csv
│   └── outputs/
├── docs/
│   └── ShirinPrarthanaJohn_shirinxjohn@gmail.com_Eightfold.pdf
├── src/
│   ├── models/
│   ├── parsers/
│   ├── normalizers/
│   ├── merger/
│   ├── confidence/
│   ├── projection/
│   ├── validator/
│   └── pipeline.py
├── tests/
├── config.json
├── config_custom.json
├── main.py
├── requirements.txt
└── README.md
```

---

