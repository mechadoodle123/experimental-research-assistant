import pandas as pd

CSV_PATH = "../raw/silver_nanoparticle_experiments.csv"

df_default = pd.read_csv(CSV_PATH)                    # pandas defaults only
df = pd.read_csv(CSV_PATH, na_values=["-"])           # defaults + "-" as missing

def section(title):
    print("\n" + "=" * 60 + f"\n{title}\n" + "=" * 60)

section("SHAPE / DTYPES")
print(df.shape)
print(df.dtypes)

section("MISSING VALUES (default vs with '-')")
missing = pd.DataFrame({"default": df_default.isna().sum(), "with_dash": df.isna().sum()})
print(missing)
print("total:", missing["default"].sum(), "->", missing["with_dash"].sum())

section("DUPLICATES")
print("exact duplicate rows:", df.duplicated().sum())
print("extra rows sharing an experiment_id:", df["experiment_id"].duplicated().sum())
deduped = df.drop_duplicates()
conflicts = deduped[deduped.duplicated("experiment_id", keep=False)].sort_values("experiment_id")
print("rows in conflicting-ID groups (same ID, different content):", len(conflicts))
for eid, g in conflicts.groupby("experiment_id"):
    differing = [c for c in g.columns if g[c].astype(str).nunique() > 1]
    print(eid, "-> differs in:", differing)

section("CATEGORICAL VALUES")
print("solvent:", [repr(v) for v in df["solvent"].unique()])
print("stabilizer:\n", df["stabilizer"].value_counts(dropna=False))
print("reducing_agent:", list(df["reducing_agent"].unique()))

section("NON-NUMERIC TOKENS IN NUMERIC COLUMNS")
numeric_cols = ["temperature", "ph", "reaction_time_min", "agno3_conc",
                "particle_size_nm", "pdi", "zeta_potential_mv", "uvvis_peak_nm", "yield_percent"]
for col in numeric_cols:
    coerced = pd.to_numeric(df[col], errors="coerce")
    bad = df.loc[coerced.isna() & df[col].notna(), col].unique()
    if len(bad):
        print(f"[{col}] {list(bad)}")

section("DATE FORMATS")
dates = df["date"].dropna().astype(str).str.strip()
patterns = (dates.str.replace(r"[a-zA-Z]+", "A", regex=True)
                 .str.replace(r"\d+", "D", regex=True))
print(patterns.value_counts())
slash = dates[dates.str.contains("/")].str.split("/")
first = pd.to_numeric(slash.str[0]); second = pd.to_numeric(slash.str[1])
print("D/D/D dates: max of 1st part =", first.max(), "| max of 2nd part =", second.max())

section("RANGES AFTER UNIT NORMALIZATION (inspection only, not final cleaning)")
def split_value(series):
    parts = (series.astype("string").str.strip()
             .str.extract(r"^(-?\d+(?:\.\d+)?)\s*(°C|C|K|uM|nm)?$"))
    return pd.to_numeric(parts[0]), parts[1]

t, t_unit = split_value(df["temperature"])
is_kelvin = t_unit.eq("K").fillna(False).astype(bool)
temp_c = t.mask(is_kelvin, t - 273.15).round(0)
c, c_unit = split_value(df["agno3_conc"])
is_um = c_unit.eq("uM").fillna(False).astype(bool)
conc_mM = c.mask(is_um, c / 1000)
size, _ = split_value(df["particle_size_nm"])

norm = pd.DataFrame({
    "temp_C": temp_c, "agno3_mM": conc_mM, "size_nm": size,
    "ph": pd.to_numeric(df["ph"], errors="coerce"),
    "reaction_time_min": df["reaction_time_min"],
    "pdi": pd.to_numeric(df["pdi"], errors="coerce"),
    "zeta_mV": pd.to_numeric(df["zeta_potential_mv"], errors="coerce"),
    "uvvis_nm": pd.to_numeric(df["uvvis_peak_nm"], errors="coerce"),
    "yield_pct": pd.to_numeric(df["yield_percent"], errors="coerce"),
})
print(norm.agg(["min", "mean", "max"]).T)

section("PROVISIONAL OUT-OF-RANGE CHECKS (adjust bounds when you write your rules)")
checks = {
    "temp_C outside 0-100": (norm.temp_C < 0) | (norm.temp_C > 100),
    "ph outside 0-14": (norm.ph < 0) | (norm.ph > 14),
    "reaction_time <= 0": norm.reaction_time_min <= 0,
    "size <= 0": norm.size_nm <= 0,
    "pdi outside 0-1": (norm.pdi < 0) | (norm.pdi > 1),
    "yield outside 0-100": (norm.yield_pct < 0) | (norm.yield_pct > 100),
}
for name, mask in checks.items():
    print(f"{name}: {mask.sum()} ->", sorted(set(df.loc[mask, 'experiment_id'])))