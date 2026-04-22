-- Patent Intelligence Database Schema

CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT PRIMARY KEY,
    patent_type  TEXT,
    patent_date  TEXT,
    patent_title TEXT,
    year         TEXT
);

CREATE TABLE IF NOT EXISTS inventors (
    patent_id   TEXT,
    inventor_id TEXT,
    name        TEXT,
    location_id TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    patent_id     TEXT,
    assignee_id   TEXT,
    name          TEXT,
    assignee_type TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    country     TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    patent_id   TEXT PRIMARY KEY,
    filing_date TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    patent_id   TEXT,
    inventor_id TEXT,
    company_id  TEXT
);

-- Indexes
CREATE INDEX idx_patents_year     ON patents(year);
CREATE INDEX idx_rel_patent       ON relationships(patent_id);
CREATE INDEX idx_rel_inventor     ON relationships(inventor_id);
CREATE INDEX idx_rel_company      ON relationships(company_id);
CREATE INDEX idx_inventors_loc    ON inventors(location_id);