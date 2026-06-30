# Multi-Source Candidate Data Transformer

A deterministic pipeline that ingests candidate data from multiple sources (structured and unstructured), normalizes and merges it into one canonical profile, and projects it into a configurable output schema with full provenance and confidence tracking.

Developed as part of the Eightfold Engineering Intern Technical Assessment.

---

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

Each stage is implemented as an independent module with a single responsibility:

| Stage | File | Responsibility |
|---|---|---|
| Parsers | `src/parsers/csv_parser.py`, `github_parser.py` | Read raw source, map to canonical field names. No cleaning, no merging. |
| Normalizer | `src/normalizers/normalizer.py` | Clean one record at a time — emails, phones, skills, locations, URLs. No merging, no scoring. |
| Merger | `src/merger/merger.py` | Combine normalized records from multiple sources into one `Candidate`. Pure selection/union logic — no string cleaning. |
| Confidence Scorer | `src/confidence/scorer.py` | Rule-based score (0–1) for the merged profile, with human-readable reasons. |
| Projector | `src/projection/projector.py` | Reshape the canonical `Candidate` into whatever shape `config.json` requests. |
| Validator | `src/validator/validator.py` | Check the final output against required fields/formats before returning it. |
| Pipeline | `src/pipeline.py` | Orchestrates the above. No business logic of its own. |

---

## Canonical Schema

The internal representation is a single typed `Candidate` dataclass (`src/models/candidate.py`):

```python
candidate_id: str
full_name: Optional[str]
emails: list[str]
phones: list[str]                     # E.164 format
location: {city, region, country, country_code}   # country_code: ISO-3166 alpha-2
links: {linkedin, github, portfolio, other[]}
headline: Optional[str]
years_experience: Optional[float]
skills: [{name, confidence, sources[]}]
experience: [{company, title, start, end, summary}]
education: [{institution, degree, field, end_year}]
provenance: {field: {value, source, method}}
overall_confidence: float
```

Nested fields (`location`, `links`) are kept as plain dictionaries rather than nested dataclasses. This keeps path-based projection (`links.github`, `skills[].name`) simple while maintaining a strongly typed canonical model.

---

## Merge / Conflict-Resolution Policy

| Field | Strategy | Reasoning |
|---|---|---|
| `full_name` | Priority pick: CSV → GitHub | Recruiter-entered names are treated as ground truth |
| `headline` | Priority pick: CSV → GitHub bio | Same as above, falls back to GitHub bio if CSV has none |
| `years_experience` | Priority pick: CSV → GitHub | GitHub doesn't reliably expose this |
| `emails` | Union, deduplicated, normalized | More contact info is strictly better; no reason to drop one |
| `phones` | Union, normalized to E.164, deduplicated | Same reasoning as emails |
| `location` | First non-null in priority order | Ambiguous if both sources disagree; CSV wins if present |
| `links` | Merge by type (linkedin/github/portfolio) — first source to populate a key wins that key | Each link type is independent; no real conflict possible |
| `skills` | Union, confidence-weighted | A skill from multiple sources gets a confidence boost; CSV-listed skills score higher than GitHub-inferred ones |

Source priority order: `recruiter_csv → linkedin → github → resume → recruiter_notes`. Recruiter-entered data is trusted most because it reflects direct human verification. GitHub-inferred data, such as repository languages used as inferred skills, is treated as weaker evidence.

**Provenance** is recorded per field as `{field, value, source, method}`, not just a source name, so every value is fully traceable to the method that produced it (`priority_pick`, `union_deduplicated`, `union_weighted`, `merge_by_type`).

---

## Confidence Scoring

The confidence score is entirely rule-based and deterministic. No machine learning or randomness is involved.

- Each populated field contributes a fixed weight (for example `full_name`: 0.20, `emails`: 0.18, `skills`: 0.10), with greater weight assigned to fields most valuable for downstream hiring decisions.
- A field corroborated by more than one source receives a small bonus.
- Missing required fields (`full_name`, `emails`) apply a penalty.
- The final score is clamped to `[0,1]`.

The scorer also returns human-readable explanations (for example `+0.20 full_name populated`, `-0.15 required field emails missing`) to make every score explainable and easy to debug.

---

## Configurable Output (Projection Layer)

The projection layer reads a runtime `config.json` and reshapes the canonical candidate into different output schemas without changing the transformation engine.

```json
{
  "fields": [
    { "path": "full_name", "type": "string", "required": true },
    { "path": "primary_email", "from": "emails[0]", "type": "string", "required": true },
    { "path": "phone", "from": "phones[0]", "type": "string", "normalize": "E164" },
    { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical" }
  ],
  "include_confidence": true,
  "include_provenance": true,
  "on_missing": "null"
}
```

Supported config options:

- **Field subset / renaming:** `path` is the output key and `from` is the canonical source path (defaults to `path` if omitted).
- **Nested path access:** `links.github`, `emails[0]`, `skills[].name` via recursive `get_nested()` and `set_nested()` helpers.
- **Per-field normalization:** `"E164"` for phones and `"canonical"` for skills.
- **Toggle provenance / confidence:** `include_provenance`, `include_confidence`.
- **Missing-value policy:** `on_missing` supports `"null"`, `"omit"`, or `"error"` (only enforced for required fields).

Two configs are included: `config.json` (full canonical output) and `config_custom.json` (subset, renamed fields, no provenance/confidence, omits missing values). This demonstrates the same engine producing multiple valid output schemas without any code changes.

---

## Edge Cases Handled

1. **Missing source entirely** (e.g. no GitHub URL) — pipeline continues with just CSV data; confidence score reflects the gap.
2. **GitHub fetch failure** (network error, 404, rate limit) — caught and logged, pipeline continues without crashing.
3. **Malformed CSV row** (garbage email, invalid phone) — normalizer returns `None` rather than fabricating a value; validator flags it; the row still produces output instead of halting the whole run.
4. **Conflicting values across sources** (e.g. different headlines) — resolved via documented priority policy, recorded in provenance.
5. **Single-token location strings** (e.g. "San Francisco") are treated as cities unless they match a known country in the ISO lookup table. This avoids incorrectly classifying city names as countries while keeping the implementation lightweight.

---

## Deliberately Out of Scope (Time Constraints)

- Resume/PDF parsing and LinkedIn scraping (only CSV + GitHub implemented, satisfying "at least one structured + one unstructured")
- `country_code` (ISO-3166) resolution from free-text country names beyond a small hardcoded lookup table — would use `pycountry` given more time
- A UI — a CLI was built per the assignment's explicit lower-priority note on I/O surface

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

## Trade-offs

- **GitHub over resume parsing:** GitHub was chosen as the unstructured source because it is reproducible, avoids OCR and layout-dependent extraction, and allowed more effort to be spent on the transformation engine itself.
- **Dataclass over pure dictionaries:** The canonical `Candidate` is a typed dataclass to enforce schema discipline after merging, while parser output and projection remain dictionary-based for flexibility with runtime configuration.
- **Detector logic inside `pipeline.py`:** With only two supported source types, a dedicated detector module would be unnecessary abstraction. This would be extracted into its own module if additional sources were added.

---

## Demo Video

Approximately 2 minute walkthrough of the complete pipeline:

**Video:** [Paste YouTube / Drive link here]