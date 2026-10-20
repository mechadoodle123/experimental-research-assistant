# Experimental Research Assistant

A Python-based research assistant for analyzing silver nanoparticle experimental records. The project ingests raw experiment data, cleans and validates it, stores it in SQLite, and exposes a small interactive query interface for common research questions such as:

- Which experiments produced the smallest particles?
- Which conditions maximized yield?
- How do reducing agents or stabilizers compare?
- What experiments match a custom set of constraints?

## Architecture overview

The application is organized as a simple data-processing pipeline with a thin reporting layer.

1. Raw source data
   - `raw/silver_nanoparticle_experiments.csv`
   - This is the immutable source dataset.

2. Cleaning and normalization pipeline
   - `src/clean.py`
   - Parses and standardizes messy laboratory data such as:
     - temperature values like `95 C` or `368.1 K`
     - concentration values like `250 uM`
     - particle size values like `39.7 nm`
     - inconsistent solvent names and date formats
   - Removes exact duplicates, rejects conflicting rows for the same `experiment_id`, and writes:
     - `processed/clean_silver_nanoparticles.csv`
     - `processed/rejects.csv`

3. Validation layer
   - `src/validate.py`
   - Enforces domain rules such as:
     - temperature in the range 0–100 °C
     - pH in the range 0–14
     - PDI in the range 0–1
     - yield_percent in the range 0–100
     - standardized solvent names only
     - ISO-formatted dates

4. Database layer
   - `src/load_db.py`
   - Reads the cleaned CSV and loads it into SQLite at:
     - `processed/experiments.db`
   - The table is named `experiments` and contains the cleaned, normalized experimental records.

5. Query engine
   - `src/query.py`
   - Contains reusable SQL query functions for:
     - dataset summary statistics
     - smallest particle experiments
     - highest-yield protocols
     - comparisons by reducing agent and stabilizer
     - custom multi-condition searches

6. User interface / assistant layer
   - `src/assistant.py`
   - Presents an interactive console menu for the researcher to ask high-level questions without writing SQL.

## Repository layout

```text
.
├── design.txt                  # Project notes and requirements background
├── documentation/
│   ├── cleaning_rules.txt
│   ├── cleaning_results.txt
│   ├── inspection.txt
│   ├── queryresult.txt
│   └── validation_test.txt
├── processed/
│   ├── clean_silver_nanoparticles.csv
│   ├── experiments.db
│   └── rejects.csv
├── raw/
│   └── silver_nanoparticle_experiments.csv
├── src/
│   ├── assistant.py
│   ├── clean.py
│   ├── inspect_raw.py
│   ├── load_db.py
│   ├── query.py
│   └── validate.py
├── test/
│   └── test_pipeline.py
├── readme.md
└── .gitignore
```

## Data flow

```text
raw CSV
  ↓
clean.py
  ↓ (normalize values, flag issues, remove duplicates, reject conflicting IDs)
processed/clean_silver_nanoparticles.csv
  ↓
validate.py
  ↓ (assert domain integrity)
load_db.py
  ↓
processed/experiments.db
  ↓
query.py
  ↓
assistant.py
  ↓
interactive analysis in terminal
```

This keeps the raw dataset immutable while producing a cleaned dataset and a queryable database used by the assistant.

## Setup

This project uses Python 3 and standard scientific libraries.

### 1) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install pandas numpy
```

If you are on a machine with a different package manager or want a fully pinned environment later, you can add a `requirements.txt` file, but the core project currently depends on:

- pandas
- numpy

## How to run the project

### Clean and validate the dataset

```bash
python3 src/clean.py
python3 src/validate.py
```

This creates/updates the cleaned data in `processed/` and checks that the output matches the project rules.

### Load the cleaned dataset into SQLite

```bash
python3 src/load_db.py
```

This builds `processed/experiments.db` from `processed/clean_silver_nanoparticles.csv`.

### Run the interactive research assistant

```bash
python3 src/assistant.py
```

The assistant menu lets you:

1. View dataset summary statistics
2. Find experiments with the smallest nanoparticles
3. Find highly productive protocols
4. Compare reducing agents
5. Analyze stabilizers
6. Run custom SQL-style filters via the Python assistant
7. Exit

### Run the pipeline tests

```bash
python3 test/test_pipeline.py
```

This exercises the cleaning logic and verifies provenance/immutability assumptions.

## Typical workflow

For a fresh checkout, the usual order is:

```bash
python3 src/clean.py
python3 src/validate.py
python3 src/load_db.py
python3 src/assistant.py
```

## Notes

- The raw dataset is intentionally preserved as the source of truth.
- Cleaning and validation outputs are written into `processed/` to keep the pipeline reproducible.
- `rejects.csv` captures rows that were excluded due to conflicts or invalid values.
- The assistant reads from the SQLite database, not directly from the raw CSV.

## Project intent

This project is a lightweight portfolio-style experimental data assistant designed to demonstrate:

- data cleansing of messy scientific datasets
- validation against domain constraints
- provenance tracking via `source_row`
- SQLite-backed analytical queries
- command-line research tooling for experimental analysis

If you want, I can also add a more polished `requirements.txt` and a quick start section tailored for Windows/macOS/Linux shells.

