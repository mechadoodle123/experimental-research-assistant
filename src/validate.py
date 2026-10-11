# src/validate.py
from pathlib import Path
import pandas as pd

def validate_clean_dataset():
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "processed" / "clean_silver_nanoparticles.csv"
    rejects_csv = base_dir / "processed" / "rejects.csv"

    if not clean_csv.exists():
        print(f"Error: {clean_csv} does not exist. Run src/clean.py first.")
        return

    df = pd.read_csv(clean_csv)
    print(f"Validating {len(df)} clean records against domain rules...\n")

    # 1. Provenance Columns
    assert "source_row" in df.columns, "FAIL: 'source_row' column missing."
    assert "cleaning_flags" in df.columns, "FAIL: 'cleaning_flags' column missing."

    # 2. Rule 3: Temperature 0–100 °C (non-nulls must be within bounds)
    valid_temp = df["temperature"].dropna()
    assert (valid_temp >= 0).all() and (valid_temp <= 100).all(), (
        f"FAIL: Temperature out of bounds! Range: [{valid_temp.min()}, {valid_temp.max()}]"
    )

    # 3. Rule 6: pH 0–14, PDI 0–1, Yield 0–100
    valid_ph = df["ph"].dropna()
    assert (valid_ph >= 0).all() and (valid_ph <= 14).all(), "FAIL: pH out of [0, 14] bounds."

    valid_pdi = df["pdi"].dropna()
    assert (valid_pdi >= 0).all() and (valid_pdi <= 1.0).all(), "FAIL: PDI out of [0, 1] bounds."

    valid_yield = df["yield_percent"].dropna()
    assert (valid_yield >= 0).all() and (valid_yield <= 100.0).all(), "FAIL: Yield out of [0, 100] bounds."

    # 4. Rule 6: Reaction time > 0 and Particle size > 0
    valid_time = df["reaction_time_min"].dropna()
    assert (valid_time > 0).all(), "FAIL: Reaction time <= 0 detected."

    valid_size = df["particle_size_nm"].dropna()
    assert (valid_size > 0).all(), "FAIL: Particle size <= 0 detected."

    # 5. Rule 7: Solvents standardized
    allowed_solvents = {"water", "ethanol", "water-ethanol 1:1"}
    actual_solvents = set(df["solvent"].dropna().unique())
    assert actual_solvents.issubset(allowed_solvents), (
        f"FAIL: Non-standardized solvents found: {actual_solvents - allowed_solvents}"
    )

    # 6. Rule 8: Date format YYYY-MM-DD
    valid_dates = df["date"].dropna()
    is_iso = valid_dates.str.match(r"^\d{4}-\d{2}-\d{2}$").all()
    assert is_iso, "FAIL: Non-ISO date format found."

    # 7. Rule 10: Check Rejection handling
    if rejects_csv.exists():
        rej_df = pd.read_csv(rejects_csv)
        print(f"Rejects file verified: {len(rej_df)} conflicting rows moved to {rejects_csv.name}.")

    print("=" * 50)
    print("ALL VALIDATION CHECKS PASSED: Dataset is clean, bounded, and traceable.")
    print("=" * 50)


if __name__ == "__main__":
    validate_clean_dataset()