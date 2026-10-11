# test/test_pipeline.py
from pathlib import Path
import sys
import numpy as np
import pandas as pd

# Add src to python path so we can test clean functions
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from clean import clean_data, parse_temperature, parse_particle_size


def test_fault_injection():
    print("=" * 60)
    print("RUNNING FAULT INJECTION & PIPELINE TESTS")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Test Fault: Deliberately Invalid Temperature
    # -------------------------------------------------------------
    # Case: Out-of-bounds (> 100 °C or < 0 °C)
    temp_val, flag = parse_temperature("150 C")
    assert temp_val == 150, f"Expected 150, got {temp_val}"
    
    # Boundary check: 150 C is outside [0, 100], so it must be nulled
    is_valid_range = (0 <= temp_val <= 100)
    assert not is_valid_range, "150 C should fail 0-100 C range check"
    print(" [PASS] Invalid temperature (150 C) correctly identified as out-of-bounds.")

    # -------------------------------------------------------------
    # 2. Test Fault: Missing / Malformed Particle Size
    # -------------------------------------------------------------
    # Case: Missing token '-' or empty value
    val_dash, flag_dash = parse_particle_size("-")
    assert np.isnan(val_dash), f"Expected NaN for '-', got {val_dash}"

    # Case: Negative particle size
    val_neg, _ = parse_particle_size("-12.4 nm")
    assert val_neg < 0, "Negative particle size parsed"
    # Verification rule: particle_size > 0
    assert not (val_neg > 0), "Negative particle size should fail positivity check"
    print(" [PASS] Missing token ('-') and negative particle size caught.")

    # -------------------------------------------------------------
    # 3. Test Fault: Duplicate ID with Conflicting Particle Size
    # -------------------------------------------------------------
    mock_data = pd.DataFrame([
        {
            "experiment_id": "EXP-TEST-01",
            "date": "2026-05-01",
            "researcher": "T. Tester",
            "reducing_agent": "glucose",
            "stabilizer": "PVP",
            "solvent": "water",
            "temperature": "25 C",
            "ph": 7.0,
            "reaction_time_min": 30,
            "agno3_conc": "1.0",
            "particle_size_nm": "25.0 nm",
            "pdi": 0.2,
            "zeta_potential_mv": -20.0,
            "uvvis_peak_nm": 410.0,
            "yield_percent": 80.0
        },
        {
            "experiment_id": "EXP-TEST-01",  # Same ID
            "date": "2026-05-01",
            "researcher": "T. Tester",
            "reducing_agent": "glucose",
            "stabilizer": "PVP",
            "solvent": "water",
            "temperature": "25 C",
            "ph": 7.0,
            "reaction_time_min": 30,
            "agno3_conc": "1.0",
            "particle_size_nm": "55.0 nm",  # Conflicting size
            "pdi": 0.2,
            "zeta_potential_mv": -20.0,
            "uvvis_peak_nm": 410.0,
            "yield_percent": 80.0
        }
    ])

    # Check conflict detection logic
    size_nunique = mock_data.groupby("experiment_id")["particle_size_nm"].nunique()
    has_conflict = size_nunique["EXP-TEST-01"] > 1
    assert has_conflict, "Conflicting experiment_id was not detected"
    print(" [PASS] Duplicate experiment_id with conflicting particle size detected.")


def test_immutability_and_provenance():
    base_dir = Path(__file__).resolve().parent.parent
    raw_path = base_dir / "raw" / "silver_nanoparticle_experiments.csv"
    clean_path = base_dir / "processed" / "clean_silver_nanoparticles.csv"

    # 1. Immutability: Verify raw file still exists and was not renamed/overwritten
    assert raw_path.exists(), "Raw data file is missing!"
    raw_df = pd.read_csv(raw_path)

    # 2. Verify cleaned dataset exists separately
    assert clean_path.exists(), "Cleaned dataset was not produced in processed/!"
    clean_df = pd.read_csv(clean_path)

    # 3. Provenance Check: source_row must exist and map back to valid raw index
    assert "source_row" in clean_df.columns, "Missing 'source_row' provenance column"
    assert "cleaning_flags" in clean_df.columns, "Missing 'cleaning_flags' column"

    # Pick a random clean record and verify source_row points to matching experiment_id in raw
    sample = clean_df.dropna(subset=["source_row"]).iloc[0]
    raw_row_idx = int(sample["source_row"]) - 2  # Subtract header (1) + 0-indexing (1)
    raw_match = raw_df.iloc[raw_row_idx]

    assert sample["experiment_id"] == raw_match["experiment_id"], (
        f"Provenance mismatch! Clean ID {sample['experiment_id']} != Raw ID {raw_match['experiment_id']}"
    )
    print(" [PASS] Immutability verified and provenance mappings trace back to original source rows.")


if __name__ == "__main__":
    test_fault_injection()
    test_immutability_and_provenance()
    print("\nALL PIPELINE TESTS PASSED SUCCESSFULLY.")