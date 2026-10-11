from pathlib import Path
import re
import numpy as np
import pandas as pd


def get_paths():
    base_dir = Path(__file__).resolve().parent.parent
    raw_path = base_dir / "raw" / "silver_nanoparticle_experiments.csv"
    processed_dir = base_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_path, processed_dir


def add_flag(existing_flags: str, new_flag: str) -> str:
    if not existing_flags:
        return new_flag
    return f"{existing_flags}; {new_flag}"


def parse_temperature(val):
    """Rule 2: Convert to °C (K minus 273.15, rounded to nearest whole number)."""
    if pd.isna(val):
        return np.nan, None

    val_str = str(val).strip().replace("°", "").replace("deg", "")
    converted_unit = False

    if "K" in val_str:
        try:
            kelvin = float(val_str.replace("K", "").strip())
            celsius = round(kelvin - 273.15)
            return celsius, "temp_unit_K_to_C"
        except ValueError:
            return np.nan, "temp_parse_failed"

    val_str = val_str.replace("C", "").strip()
    try:
        celsius = round(float(val_str))
        flag = "temp_unit_stripped" if ("C" in str(val) or "°" in str(val)) else None
        return celsius, flag
    except ValueError:
        return np.nan, "temp_parse_failed"


def parse_agno3_conc(val):
    """Rule 4: Convert to mM (uM / 1000). Plain numbers assumed mM."""
    if pd.isna(val):
        return np.nan, None

    val_str = str(val).strip()
    if "uM" in val_str:
        try:
            num = float(val_str.replace("uM", "").strip())
            return num / 1000.0, "agno3_conc_uM_to_mM"
        except ValueError:
            return np.nan, "agno3_conc_parse_failed"

    try:
        return float(val_str), None
    except ValueError:
        return np.nan, "agno3_conc_parse_failed"


def parse_particle_size(val):
    """Rule 5: Strip 'nm' suffix and parse to float."""
    if pd.isna(val):
        return np.nan, None

    val_str = str(val).strip()
    had_unit = "nm" in val_str
    val_str = val_str.replace("nm", "").strip()

    try:
        val_float = float(val_str)
        flag = "particle_size_nm_stripped" if had_unit else None
        return val_float, flag
    except ValueError:
        return np.nan, "particle_size_parse_failed"


def clean_solvent(val):
    """Rule 7: Strip whitespace, lowercase, and map to 3 target canonical names."""
    if pd.isna(val):
        return np.nan, None

    s = str(val).strip().lower()
    # Normalize multiple separators and variants
    s = re.sub(r"\s+", " ", s)

    solvent_map = {
        "water": "water",
        "h2o": "water",
        "di water": "water",
        "ethanol": "ethanol",
        "etoh": "ethanol",
        "water-ethanol 1:1": "water-ethanol 1:1",
        "water/ethanol 1:1": "water-ethanol 1:1",
        "water:ethanol (1:1)": "water-ethanol 1:1",
    }

    canonical = solvent_map.get(s, s)
    flag = "solvent_standardized" if str(val) != canonical else None
    return canonical, flag


def clean_data():
    raw_path, processed_dir = get_paths()
    print(f"Loading data from: {raw_path}")

    # Rule 1: Custom missing values while preserving "none" in stabilizer
    na_tokens = ["", " ", "NA", "N/A", "null", "NULL", "-"]
    df = pd.read_csv(raw_path, keep_default_na=False, na_values=na_tokens)

    # Convert any empty or whitespace-only strings left to genuine NaN
    df = df.replace(r"^\s*$", np.nan, regex=True)

    # Rule 11: Add provenance
    # Original CSV rows (header is row 1, data starts at row 2)
    df["source_row"] = df.index + 2
    df["cleaning_flags"] = ""

    # Rule 9: Exact duplicate rows
    initial_len = len(df)
    # Check duplicates across the original dataset columns
    original_cols = [c for c in df.columns if c not in ["source_row", "cleaning_flags"]]
    is_exact_dup = df.duplicated(subset=original_cols, keep="first")
    exact_dups_count = is_exact_dup.sum()

    if exact_dups_count > 0:
        print(f"Rule 9: Dropping {exact_dups_count} exact duplicate rows.")
        df = df[~is_exact_dup].copy()

    # Rule 8: Date conversion to ISO (YYYY-MM-DD), with dayfirst=True for slash dates
    parsed_dates = pd.to_datetime(df["date"], dayfirst=True, format="mixed", errors="coerce")
    date_changed = (df["date"] != parsed_dates.dt.strftime("%Y-%m-%d")) & parsed_dates.notna()
    df.loc[date_changed, "cleaning_flags"] = df.loc[date_changed, "cleaning_flags"].apply(
        lambda f: add_flag(f, "date_converted_to_iso")
    )
    df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    # Rule 2: Temperature parsing
    temp_results = df["temperature"].apply(parse_temperature)
    df["temperature"] = [res[0] for res in temp_results]
    for idx, (_, flag) in zip(df.index, temp_results):
        if flag:
            df.at[idx, "cleaning_flags"] = add_flag(df.at[idx, "cleaning_flags"], flag)

    # Rule 3: Temperature bounds (0–100 °C)
    temp_invalid = (df["temperature"] < 0) | (df["temperature"] > 100)
    for idx in df[temp_invalid].index:
        df.at[idx, "cleaning_flags"] = add_flag(
            df.at[idx, "cleaning_flags"], f"temperature_out_of_bounds({df.at[idx, 'temperature']}C)"
        )
        df.at[idx, "temperature"] = np.nan

    # Rule 4: agno3_conc parsing
    conc_results = df["agno3_conc"].apply(parse_agno3_conc)
    df["agno3_conc"] = [res[0] for res in conc_results]
    for idx, (_, flag) in zip(df.index, conc_results):
        if flag:
            df.at[idx, "cleaning_flags"] = add_flag(df.at[idx, "cleaning_flags"], flag)

    # Rule 5: particle_size_nm stripping
    size_results = df["particle_size_nm"].apply(parse_particle_size)
    df["particle_size_nm"] = [res[0] for res in size_results]
    for idx, (_, flag) in zip(df.index, size_results):
        if flag:
            df.at[idx, "cleaning_flags"] = add_flag(df.at[idx, "cleaning_flags"], flag)

    # Rule 7: Solvent standardization
    solvent_results = df["solvent"].apply(clean_solvent)
    df["solvent"] = [res[0] for res in solvent_results]
    for idx, (_, flag) in zip(df.index, solvent_results):
        if flag:
            df.at[idx, "cleaning_flags"] = add_flag(df.at[idx, "cleaning_flags"], flag)

    # Cast remaining numeric columns safely
    other_numeric = ["ph", "reaction_time_min", "pdi", "zeta_potential_mv", "uvvis_peak_nm", "yield_percent"]
    df[other_numeric] = df[other_numeric].apply(pd.to_numeric, errors="coerce")

    # Rule 6: Impossible values checking
    validation_bounds = {
        "ph": (0.0, 14.0, True),                # 0 <= ph <= 14
        "pdi": (0.0, 1.0, True),                # 0 <= pdi <= 1
        "yield_percent": (0.0, 100.0, True),    # 0 <= yield <= 100
        "reaction_time_min": (0.0, np.inf, False), # reaction_time > 0
        "particle_size_nm": (0.0, np.inf, False),  # particle_size > 0
    }

    for col, (min_val, max_val, inclusive_min) in validation_bounds.items():
        if inclusive_min:
            out_mask = (df[col] < min_val) | (df[col] > max_val)
        else:
            out_mask = (df[col] <= min_val) | (df[col] > max_val)

        for idx in df[out_mask].index:
            val_out = df.at[idx, col]
            df.at[idx, "cleaning_flags"] = add_flag(
                df.at[idx, "cleaning_flags"], f"{col}_out_of_bounds({val_out})"
            )
            df.at[idx, col] = np.nan

    # Rule 10: Same experiment_id, different particle_size_nm
    # Identify non-null particle sizes per experiment_id that have more than 1 distinct value
    size_nunique = df.dropna(subset=["particle_size_nm"]).groupby("experiment_id")["particle_size_nm"].nunique()
    conflicting_ids = size_nunique[size_nunique > 1].index.tolist()

    rejects_list = []
    clean_indices = []

    for exp_id, group in df.groupby("experiment_id", sort=False):
        if exp_id in conflicting_ids:
            # Keep first row in clean df, move remaining conflicting rows to rejects
            clean_indices.append(group.index[0])
            for reject_idx in group.index[1:]:
                reject_row = group.loc[reject_idx].to_dict()
                reject_row["rejection_reason"] = "conflict, needs review"
                rejects_list.append(reject_row)
        else:
            clean_indices.extend(group.index.tolist())

    df_clean = df.loc[clean_indices].sort_values("source_row").reset_index(drop=True)
    df_rejects = pd.DataFrame(rejects_list)

    # Save results
    clean_csv = processed_dir / "clean_silver_nanoparticles.csv"
    rejects_csv = processed_dir / "rejects.csv"

    df_clean.to_csv(clean_csv, index=False)
    if not df_rejects.empty:
        df_rejects.to_csv(rejects_csv, index=False)
    else:
        # Create empty rejects file with schema if none found
        pd.DataFrame(columns=list(df.columns) + ["rejection_reason"]).to_csv(rejects_csv, index=False)

    print("\n" + "=" * 50)
    print("CLEANING COMPLETE")
    print("=" * 50)
    print(f"Input records:       {initial_len}")
    print(f"Clean records saved: {len(df_clean)} -> {clean_csv}")
    print(f"Rejected records:    {len(df_rejects)} -> {rejects_csv}")
    print(f"Cleaning flags logged on { (df_clean['cleaning_flags'] != '').sum() } rows.")


if __name__ == "__main__":
    clean_data()