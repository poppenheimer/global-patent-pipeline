# Global Patent Intelligence Data Pipeline

A data engineering pipeline that collects, cleans, stores, and analyzes 
real U.S. patent data from the USPTO PatentsView dataset (2015-2025).

## What it does
- Cleans patent records using pandas
- Stores data in a SQLite database
- Answers 7 analytical SQL queries
- Generates console, CSV, and JSON reports with charts

## How to run

## Clean Data Files
The following sample files (10,000 rows each) are included:
- `data/clean/clean_patents.csv`
- `data/clean/clean_inventors.csv`
- `data/clean/clean_companies.csv`
- `data/clean/clean_locations.csv`

> To generate the full dataset (millions of rows), download the raw files
> from USPTO and run `scripts/cleaner.py`

### 1. Download data
Download these files from https://patentsview.org/download/data-download-tables
and place them in `data/raw/`:
- g_patent.tsv
- g_patent_abstract.tsv
- g_application.tsv
- g_inventor_disambiguated.tsv
- g_assignee_disambiguated.tsv
- g_location_disambiguated.tsv
- g_cpc_current.tsv

### 2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas matplotlib
```

### 3. Run the pipeline
```bash
python3 scripts/cleaner.py
python3 scripts/database.py
python3 scripts/reports.py
```

## Tools used
- Python, pandas, matplotlib
- SQLite
- USPTO PatentsView dataset

