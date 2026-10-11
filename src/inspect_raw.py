import pandas as pd 

df = pd.read_csv("../raw/silver_nanoparticle_experiments.csv")

print("ROWS AND COLUMNS: ",df.shape)
print("DATATYPES FOR EACH COLUMN: ",end= '\n\n')
print(df.dtypes)
print(" \n\n")
print("Count of null values per column ")
print(df.isna().sum())

print("total : ",df.isna().sum().sum())

print("duplicate rows : ", df.duplicated().sum())

print("Number of duplicate experiment_ids: ",df["experiment_id"].duplicated().sum())

unique_solvent = df["solvent"].unique()
unique_stabi  = df["stabilizer"].unique()
unique_reducing = df["reducing_agent"].unique()

print("unique solvents: ",unique_solvent)
print("unique stabilizers: ",unique_stabi)
print("unique reducing agents: ",unique_reducing)

numeric_cols = [
    "temperature", "ph", "reaction_time_min", "agno3_conc",
    "particle_size_nm", "pdi", "zeta_potential_mv",
    "uvvis_peak_nm", "yield_percent"
]

print("\n" + "=" * 60)
print("STRING / TOKEN ISSUES IN NUMERIC COLUMNS")
print("=" * 60)
for col in numeric_cols:
    if col in df.columns:
        # Find non-null values that fail float conversion
        coerced = pd.to_numeric(df[col], errors="coerce")
        bad_mask = coerced.isna() & df[col].notna()
        bad_values = df.loc[bad_mask, col].unique()
        if len(bad_values) > 0:
            print(f"[{col}] contains non-numeric tokens: {bad_values}")

print("\n" + "=" * 60)
print("MIN / MAX SUMMARY (WITH COERCION)")
print("=" * 60)
# Convert safely using errors='coerce' so bad tokens become NaN rather than raising an error
df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
summary = df_numeric.agg(["min", "mean", "max"]).T
print(summary)


dates = df['date'].dropna().astype(str).str.strip()

# Replace runs of digits with 'D' and words with 'A'
# Examples: '2026-02-18' -> 'D-D-D', 'Jun 25, 2026' -> 'A D, D', '25/09/2026' -> 'D/D/D'
date_patterns = dates.str.replace(r'\d+', 'D', regex=True).str.replace(r'[a-zA-Z]+', 'A', regex=True)

# Count distinct patterns
pattern_counts = date_patterns.value_counts()
print(f"Number of distinct date formats: {len(pattern_counts)}\n")
print("Format breakdown:")
print(pattern_counts)