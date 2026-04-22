import sqlite3
import pandas as pd
from pathlib import Path

CLEAN_DIR = Path("data/clean")
DB_PATH   = Path("patent_intelligence.db")

conn = sqlite3.connect(DB_PATH)
print(f"Database created: {DB_PATH}")


def load_table(filename, table_name):
    print(f"Loading {table_name}...")
    df = pd.read_csv(CLEAN_DIR / filename, dtype=str, low_memory=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False, chunksize=50_000)
    print(f"  Loaded {len(df):,} rows into {table_name}")


load_table("clean_patents.csv",       "patents")
load_table("clean_applications.csv",  "applications")
load_table("clean_inventors.csv",     "inventors")
load_table("clean_locations.csv",     "locations")
load_table("clean_companies.csv",     "companies")
load_table("clean_relationships.csv", "relationships")

conn.close()
print("\nDone! Database ready.")
