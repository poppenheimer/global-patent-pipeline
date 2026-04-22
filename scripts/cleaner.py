import pandas as pd
from pathlib import Path

RAW_DIR   = Path("data/raw")
CLEAN_DIR = Path("data/clean")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def clean_patents():
    print("Cleaning patents...")

    pat = pd.read_csv(
        RAW_DIR / "g_patent.tsv",
        sep="\t",
        usecols=["patent_id", "patent_type", "patent_date", "patent_title"],
        dtype=str,
        low_memory=False
    )
    print(f"  Loaded: {len(pat):,} rows")

    # Keep only 2015 onwards
    pat["year"] = pat["patent_date"].str[:4].astype(int, errors="ignore")
    pat = pat[pat["year"] >= 2015]
    print(f"  After 2015 filter: {len(pat):,} rows")

    pat.to_csv(CLEAN_DIR / "clean_patents.csv", index=False)
    print("  Saved clean_patents.csv")
    return set(pat["patent_id"])

def clean_abstracts(patent_ids):
    print("Cleaning abstracts...")

    chunks = []
    for chunk in pd.read_csv(
        RAW_DIR / "g_patent_abstract.tsv",
        sep="\t",
        usecols=["patent_id", "patent_abstract"],
        dtype=str,
        chunksize=200_000
    ):
        # Only keep rows that match our filtered patents
        filtered = chunk[chunk["patent_id"].isin(patent_ids)]
        chunks.append(filtered)
        print(f"  ...processed {len(chunks) * 200_000:,} rows", end="\r")

    abstracts = pd.concat(chunks)
    print(f"\n  Kept: {len(abstracts):,} matching abstracts")

    abstracts.to_csv(CLEAN_DIR / "clean_abstracts.csv", index=False)
    print("  Saved clean_abstracts.csv")
def clean_inventors(patent_ids):
    print("Cleaning inventors...")

    inv = pd.read_csv(
        RAW_DIR / "g_inventor_disambiguated.tsv",
        sep="\t",
        usecols=["patent_id", "inventor_id", "disambig_inventor_name_first",
                 "disambig_inventor_name_last", "location_id"],
        dtype=str,
        low_memory=False
    )
    print(f"  Loaded: {len(inv):,} rows")

    # Only keep inventors linked to our filtered patents
    inv = inv[inv["patent_id"].isin(patent_ids)]
    print(f"  After filter: {len(inv):,} rows")

    # Combine first and last name into one column
    inv["name"] = (inv["disambig_inventor_name_first"].fillna("") + " " +
                   inv["disambig_inventor_name_last"].fillna("")).str.strip()

    inv = inv[["patent_id", "inventor_id", "name", "location_id"]]
    inv = inv.drop_duplicates()

    inv.to_csv(CLEAN_DIR / "clean_inventors.csv", index=False)
    print(f"  Saved clean_inventors.csv")
    return inv

def clean_locations():
    print("Cleaning locations...")

    loc = pd.read_csv(
        RAW_DIR / "g_location_disambiguated.tsv",
        sep="\t",
        usecols=["location_id", "disambig_country"],
        dtype=str,
        low_memory=False
    )
    print(f"  Loaded: {len(loc):,} rows")

    loc = loc.dropna(subset=["disambig_country"])
    loc = loc.rename(columns={"disambig_country": "country"})
    loc = loc.drop_duplicates()

    loc.to_csv(CLEAN_DIR / "clean_locations.csv", index=False)
    print(f"  Saved clean_locations.csv")
    return loc

def clean_companies(patent_ids):
    print("Cleaning companies...")

    co = pd.read_csv(
        RAW_DIR / "g_assignee_disambiguated.tsv",
        sep="\t",
        usecols=["patent_id", "assignee_id", "disambig_assignee_organization", "assignee_type"],
        dtype=str,
        low_memory=False
    )
    print(f"  Loaded: {len(co):,} rows")

    co = co[co["patent_id"].isin(patent_ids)]
    co = co.dropna(subset=["disambig_assignee_organization"])
    co = co.rename(columns={"disambig_assignee_organization": "name"})
    co = co[["patent_id", "assignee_id", "name", "assignee_type"]]
    co = co.drop_duplicates()
    print(f"  After filter: {len(co):,} rows")

    co.to_csv(CLEAN_DIR / "clean_companies.csv", index=False)
    print(f"  Saved clean_companies.csv")
    return co
def clean_applications(patent_ids):
    print("Cleaning applications...")

    app = pd.read_csv(
        RAW_DIR / "g_application.tsv",
        sep="\t",
        usecols=["patent_id", "filing_date"],
        dtype=str,
        low_memory=False
    )
    print(f"  Loaded: {len(app):,} rows")

    app = app[app["patent_id"].isin(patent_ids)]

    # Filter out garbage dates (we saw "1074" earlier)
    app["year_check"] = app["filing_date"].str[:4].astype(int, errors="ignore")
    app = app[app["year_check"] >= 1900]
    app = app.drop(columns=["year_check"])
    app = app.drop_duplicates(subset=["patent_id"])
    print(f"  After filter: {len(app):,} rows")

    app.to_csv(CLEAN_DIR / "clean_applications.csv", index=False)
    print("  Saved clean_applications.csv")
    return app


def build_relationships(patent_ids):
    print("Building relationships...")

    inv = pd.read_csv(CLEAN_DIR / "clean_inventors.csv", dtype=str)
    co  = pd.read_csv(CLEAN_DIR / "clean_companies.csv", dtype=str)

    # patent <-> inventor links
    pi = inv[["patent_id", "inventor_id"]].drop_duplicates()

    # patent <-> company links
    pc = co[["patent_id", "assignee_id"]].drop_duplicates()
    pc = pc.rename(columns={"assignee_id": "company_id"})

    # Merge into one relationships table
    rel = pi.merge(pc, on="patent_id", how="outer")
    rel = rel.drop_duplicates()
    print(f"  Relationships: {len(rel):,} rows")

    rel.to_csv(CLEAN_DIR / "clean_relationships.csv", index=False)
    print("  Saved clean_relationships.csv")

patent_ids = clean_patents()
print("Skipping abstracts - not required for analysis")
clean_inventors(patent_ids)
clean_locations()
clean_companies(patent_ids)
clean_applications(patent_ids)
build_relationships(patent_ids)
print("\nAll done! Check data/clean/")
