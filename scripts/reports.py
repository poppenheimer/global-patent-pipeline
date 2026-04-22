import sqlite3
import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

DB_PATH     = Path("patent_intelligence.db")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)


def get_summary():
    total    = pd.read_sql("SELECT COUNT(*) AS n FROM patents", conn).iloc[0]["n"]
    inv_total = pd.read_sql("SELECT COUNT(DISTINCT inventor_id) AS n FROM inventors", conn).iloc[0]["n"]
    co_total  = pd.read_sql("SELECT COUNT(DISTINCT assignee_id) AS n FROM companies", conn).iloc[0]["n"]
    return {
        "total_patents":   int(total),
        "total_inventors": int(inv_total),
        "total_companies": int(co_total),
    }


def get_top_inventors(n=10):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM inventors
        GROUP BY inventor_id
        ORDER BY patents DESC
        LIMIT {n}
    """, conn)


def get_top_companies(n=10):
    return pd.read_sql(f"""
        SELECT name, COUNT(DISTINCT patent_id) AS patents
        FROM companies
        GROUP BY assignee_id
        ORDER BY patents DESC
        LIMIT {n}
    """, conn)


def get_country_trends():
    return pd.read_sql("""
        SELECT l.country, COUNT(DISTINCT i.patent_id) AS patents
        FROM inventors i
        JOIN locations l ON i.location_id = l.location_id
        GROUP BY l.country
        ORDER BY patents DESC
        LIMIT 20
    """, conn)


def get_yearly_trends():
    return pd.read_sql("""
        SELECT year, COUNT(*) AS patents_granted
        FROM patents
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """, conn)


def print_console_report(summary, top_inv, top_co, top_countries):
    print("\n" + "=" * 50)
    print("   GLOBAL PATENT INTELLIGENCE REPORT")
    print("=" * 50)
    print(f"  Total Patents   : {summary['total_patents']:,}")
    print(f"  Total Inventors : {summary['total_inventors']:,}")
    print(f"  Total Companies : {summary['total_companies']:,}")

    print("\n  TOP 10 INVENTORS")
    print("  " + "-" * 35)
    for i, row in top_inv.iterrows():
        print(f"  {i+1}. {row['name']} — {row['patents']:,}")

    print("\n  TOP 10 COMPANIES")
    print("  " + "-" * 35)
    for i, row in top_co.iterrows():
        print(f"  {i+1}. {row['name']} — {row['patents']:,}")

    print("\n  TOP 10 COUNTRIES")
    print("  " + "-" * 35)
    for i, row in top_countries.head(10).iterrows():
        print(f"  {i+1}. {row['country']} — {row['patents']:,}")

    print("=" * 50)


# Run it
summary      = get_summary()
top_inv      = get_top_inventors()
top_co       = get_top_companies()
top_countries = get_country_trends()
yearly       = get_yearly_trends()

print_console_report(summary, top_inv, top_co, top_countries)

def export_csvs(top_inv, top_co, top_countries, yearly):
    top_inv.to_csv(REPORTS_DIR / "top_inventors.csv", index=False)
    print("  ✓ top_inventors.csv")

    top_co.to_csv(REPORTS_DIR / "top_companies.csv", index=False)
    print("  ✓ top_companies.csv")

    top_countries.to_csv(REPORTS_DIR / "country_trends.csv", index=False)
    print("  ✓ country_trends.csv")

    yearly.to_csv(REPORTS_DIR / "yearly_trends.csv", index=False)
    print("  ✓ yearly_trends.csv")


def export_json(summary, top_inv, top_co, top_countries):
    report = {
        "total_patents":   summary["total_patents"],
        "total_inventors": summary["total_inventors"],
        "total_companies": summary["total_companies"],
        "top_inventors": [
            {"rank": i+1, "name": r["name"], "patents": int(r["patents"])}
            for i, r in top_inv.iterrows()
        ],
        "top_companies": [
            {"rank": i+1, "name": r["name"], "patents": int(r["patents"])}
            for i, r in top_co.iterrows()
        ],
        "top_countries": [
            {"rank": i+1, "country": r["country"], "patents": int(r["patents"])}
            for i, r in top_countries.head(10).iterrows()
        ],
    }
    with open(REPORTS_DIR / "summary_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("  ✓ summary_report.json")


print("\n[CSV exports]")
export_csvs(top_inv, top_co, top_countries, yearly)

print("\n[JSON export]")
export_json(summary, top_inv, top_co, top_countries)

def make_charts(top_inv, top_co, top_countries, yearly):
    print("\n[Charts]")

    # Chart 1 - Top Inventors
    fig, ax = plt.subplots(figsize=(12, 7))
    df = top_inv.iloc[::-1]  # flip so highest is on top
    ax.barh(df["name"], df["patents"], color="steelblue")
    ax.set_title("Top 10 Inventors by Patent Count (2015-2025)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Patents")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "top_inventors_chart.png", dpi=150)
    plt.close()
    print("  ✓ top_inventors_chart.png")

    # Chart 2 - Top Companies
    fig, ax = plt.subplots(figsize=(12, 7))
    df = top_co.iloc[::-1]
    ax.barh(df["name"], df["patents"], color="darkorange")
    ax.set_title("Top 10 Companies by Patent Count (2015-2025)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Patents")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "top_companies_chart.png", dpi=150)
    plt.close()
    print("  ✓ top_companies_chart.png")

    # Chart 3 - Yearly Trends
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.fill_between(yearly["year"], yearly["patents_granted"], alpha=0.3, color="green")
    ax.plot(yearly["year"], yearly["patents_granted"], color="green", linewidth=2)
    ax.set_title("Patents Granted Per Year (2015-2025)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Patents Granted")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "yearly_trends_chart.png", dpi=150)
    plt.close()
    print("  ✓ yearly_trends_chart.png")

    # Chart 4 - Country Pie
    fig, ax = plt.subplots(figsize=(9, 9))
    top10 = top_countries.head(10)
    ax.pie(top10["patents"], labels=top10["country"], autopct="%1.1f%%", startangle=140)
    ax.set_title("Patent Share by Country (Top 10)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "country_pie_chart.png", dpi=150)
    plt.close()
    print("  ✓ country_pie_chart.png")


make_charts(top_inv, top_co, top_countries, yearly)

conn.close()
print("\nAll reports saved to reports/")