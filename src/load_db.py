import sqlite3
from pathlib import Path
import pandas as pd


def get_paths():
    base_dir = Path(__file__).resolve().parent.parent
    clean_csv = base_dir / "processed" / "clean_silver_nanoparticles.csv"
    db_path = base_dir / "processed" / "experiments.db"
    return clean_csv, db_path


def create_schema(cursor: sqlite3.Cursor):
    cursor.execute("DROP TABLE IF EXISTS experiments;")
    cursor.execute("""
    CREATE TABLE experiments (
        experiment_id       TEXT PRIMARY KEY NOT NULL,
        date                TEXT NOT NULL,
        researcher          TEXT NOT NULL,
        reducing_agent      TEXT NOT NULL,
        stabilizer          TEXT NOT NULL,
        solvent             TEXT NOT NULL,
        temperature         REAL,
        ph                  REAL,
        reaction_time_min   REAL NOT NULL,
        agno3_conc          REAL NOT NULL,
        particle_size_nm    REAL,
        pdi                 REAL,
        zeta_potential_mv   REAL,
        uvvis_peak_nm       REAL,
        yield_percent       REAL,
        source_row          INTEGER NOT NULL,
        cleaning_flags      TEXT
    );
    """)


def load_cleaned_data_to_sqlite():
    clean_csv, db_path = get_paths()

    if not clean_csv.exists():
        raise FileNotFoundError(f"Cleaned CSV not found at {clean_csv}. Run clean.py first.")

    print(f"Reading cleaned data from: {clean_csv}")
    df = pd.read_csv(clean_csv)

    # Convert pandas NaN to None so sqlite3 driver inserts them as SQL NULL
    df = df.where(pd.notna(df), None)

    print(f"Connecting to SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create schema
        create_schema(cursor)
        print("Table 'experiments' initialized.")

        # Prepare batch insert statement
        columns = list(df.columns)
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        insert_query = f"INSERT INTO experiments ({col_names}) VALUES ({placeholders})"

        # Convert records to list of tuples for execute_many
        records = [tuple(row) for row in df.itertuples(index=False, name=None)]

        cursor.executemany(insert_query, records)
        conn.commit()

        print(f"Successfully loaded {len(records)} records into 'experiments'.")

        # Basic database verification
        cursor.execute("SELECT COUNT(*) FROM experiments;")
        total_rows = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM experiments WHERE particle_size_nm IS NULL;")
        null_sizes = cursor.fetchone()[0]

        print(f"Verification -> Total records: {total_rows}, Rows with NULL particle_size_nm: {null_sizes}")

    except sqlite3.IntegrityError as e:
        print(f"Database Integrity Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    load_cleaned_data_to_sqlite()