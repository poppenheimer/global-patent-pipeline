-- Q1: Top Inventors (who has the most patents?)
SELECT 
    name,
    COUNT(DISTINCT patent_id) AS patent_count
FROM inventors
GROUP BY inventor_id
ORDER BY patent_count DESC
LIMIT 20;


-- Q2: Top Companies (which companies own the most patents?)
SELECT 
    name,
    COUNT(DISTINCT patent_id) AS patent_count
FROM companies
GROUP BY assignee_id
ORDER BY patent_count DESC
LIMIT 20;
-- Q3: Countries (which countries produce the most patents?)
SELECT 
    l.country AS country,
    COUNT(DISTINCT i.patent_id) AS patent_count
FROM inventors i
JOIN locations l ON i.location_id = l.location_id
GROUP BY l.country
ORDER BY patent_count DESC
LIMIT 20;


-- Q4: Trends Over Time (patents per year)
SELECT 
    year,
    COUNT(*) AS patents_granted
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;


-- Q5: JOIN Query (patents with inventors and companies)
SELECT 
    p.patent_id,
    p.patent_title,
    p.year,
    i.name AS inventor_name,
    l.country AS country,
    c.name AS company_name
FROM patents p
JOIN inventors i ON p.patent_id = i.patent_id
JOIN locations l ON i.location_id = l.location_id
LEFT JOIN companies c ON p.patent_id = c.patent_id
LIMIT 20;


-- Q6: CTE Query (top inventor per country)
WITH inventor_counts AS (
    SELECT 
        i.inventor_id,
        i.name,
        l.country AS country,
        COUNT(DISTINCT i.patent_id) AS patent_count
    FROM inventors i
    JOIN locations l ON i.location_id = l.location_id
    GROUP BY i.inventor_id
),
country_ranks AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY country 
            ORDER BY patent_count DESC
        ) AS rank_in_country
    FROM inventor_counts
)
SELECT country, name, patent_count
FROM country_ranks
WHERE rank_in_country = 1
ORDER BY patent_count DESC
LIMIT 20;


-- Q7: Ranking Query (rank inventors with window functions)
WITH inventor_counts AS (
    SELECT 
        inventor_id,
        name,
        COUNT(DISTINCT patent_id) AS patent_count
    FROM inventors
    GROUP BY inventor_id
)
SELECT 
    RANK() OVER (ORDER BY patent_count DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY patent_count DESC) AS dense_rank,
    NTILE(10) OVER (ORDER BY patent_count DESC) AS decile,
    name,
    patent_count
FROM inventor_counts
ORDER BY rank
LIMIT 20;