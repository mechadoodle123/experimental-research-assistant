import sqlite3
from pathlib import Path
import pandas as pd

# Point to the populated database
DB_PATH = Path(__file__).resolve().parent.parent / "processed" / "experiments.db"


def get_connection():
    """Returns a connection to the SQLite experiments database."""
    return sqlite3.connect(DB_PATH)


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Helper to execute SQL queries and return the result as a DataFrame."""
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


# -----------------------------------------------------------------------------
# 1. High-Level Summary Statistics
# -----------------------------------------------------------------------------
def get_dataset_summary() -> pd.DataFrame:
    """Returns overall aggregates across all valid experimental runs."""
    sql = """
    SELECT 
        COUNT(experiment_id) AS total_experiments,
        ROUND(AVG(particle_size_nm), 2) AS avg_size_nm,
        ROUND(MIN(particle_size_nm), 2) AS min_size_nm,
        ROUND(MAX(particle_size_nm), 2) AS max_size_nm,
        ROUND(AVG(yield_percent), 2) AS avg_yield_pct,
        ROUND(AVG(pdi), 3) AS avg_pdi
    FROM experiments;
    """
    return run_query(sql)


# -----------------------------------------------------------------------------
# 2. Optimal Reaction Retrieval
# -----------------------------------------------------------------------------
def get_smallest_particles(top_n: int = 5) -> pd.DataFrame:
    """Finds reaction conditions that produced the smallest silver nanoparticles."""
    sql = """
    SELECT 
        experiment_id,
        reducing_agent,
        stabilizer,
        solvent,
        temperature,
        ph,
        particle_size_nm,
        pdi,
        yield_percent
    FROM experiments
    WHERE particle_size_nm IS NOT NULL
    ORDER BY particle_size_nm ASC
    LIMIT ?;
    """
    return run_query(sql, (top_n,))


def get_highest_yield(min_yield: float = 95.0) -> pd.DataFrame:
    """Finds protocols that achieve maximum yield while keeping particle size reasonable."""
    sql = """
    SELECT 
        experiment_id,
        reducing_agent,
        stabilizer,
        solvent,
        temperature,
        reaction_time_min,
        yield_percent,
        particle_size_nm
    FROM experiments
    WHERE yield_percent >= ?
    ORDER BY yield_percent DESC, particle_size_nm ASC;
    """
    return run_query(sql, (min_yield,))


# -----------------------------------------------------------------------------
# 3. Categorical Aggregations & Chemical Analysis
# -----------------------------------------------------------------------------
def compare_reducing_agents() -> pd.DataFrame:
    """Compares average size, yield, and stability across reducing agents."""
    sql = """
    SELECT 
        reducing_agent,
        COUNT(experiment_id) AS run_count,
        ROUND(AVG(particle_size_nm), 2) AS avg_size_nm,
        ROUND(AVG(pdi), 3) AS avg_pdi,
        ROUND(AVG(yield_percent), 2) AS avg_yield_pct,
        ROUND(AVG(temperature), 1) AS avg_temp_c
    FROM experiments
    GROUP BY reducing_agent
    ORDER BY avg_size_nm ASC;
    """
    return run_query(sql)


def compare_stabilizers() -> pd.DataFrame:
    """Evaluates zeta potential (electrostatic stability) and PDI grouped by stabilizer."""
    sql = """
    SELECT 
        COALESCE(stabilizer, 'Unspecified') AS stabilizer,
        COUNT(experiment_id) AS run_count,
        ROUND(AVG(zeta_potential_mv), 2) AS avg_zeta_mv,
        ROUND(AVG(pdi), 3) AS avg_pdi,
        ROUND(AVG(particle_size_nm), 2) AS avg_size_nm
    FROM experiments
    GROUP BY stabilizer
    ORDER BY avg_zeta_mv ASC;
    """
    return run_query(sql)


# -----------------------------------------------------------------------------
# 4. Multi-Condition Parameter Search
# -----------------------------------------------------------------------------
def search_experiments(
    solvent: str = None,
    reducing_agent: str = None,
    max_size: float = None,
    min_yield: float = None
) -> pd.DataFrame:
    """Dynamic multi-parameter filter using parameterized SQL."""
    conditions = ["1=1"]
    params = []

    if solvent:
        conditions.append("solvent = ?")
        params.append(solvent.strip().lower())
    if reducing_agent:
        conditions.append("reducing_agent = ?")
        params.append(reducing_agent.strip().lower())
    if max_size is not None:
        conditions.append("particle_size_nm <= ?")
        params.append(max_size)
    if min_yield is not None:
        conditions.append("yield_percent >= ?")
        params.append(min_yield)

    sql = f"""
    SELECT 
        experiment_id,
        reducing_agent,
        stabilizer,
        solvent,
        temperature,
        particle_size_nm,
        yield_percent
    FROM experiments
    WHERE {' AND '.join(conditions)}
    ORDER BY particle_size_nm ASC;
    """
    return run_query(sql, tuple(params))


if __name__ == "__main__":
    print("=" * 65)
    print("EXPERIMENTAL RESEARCH ASSISTANT: SQL QUERY ENGINE")
    print("=" * 65)

    print("\n[1] Overall Database Metrics:")
    print(get_dataset_summary().to_string(index=False))

    print("\n[2] Top 5 Smallest Nanoparticle Experiments:")
    print(get_smallest_particles(top_n=5).to_string(index=False))

    print("\n[3] Performance by Reducing Agent:")
    print(compare_reducing_agents().to_string(index=False))

    print("\n[4] Stabilizer Impact on Zeta Potential & Particle Size:")
    print(compare_stabilizers().to_string(index=False))

    print("\n[5] Custom Filter: Water solvent, size <= 25 nm, yield >= 70%:")
    filtered = search_experiments(solvent="water", max_size=25.0, min_yield=70.0)
    print(filtered.to_string(index=False))