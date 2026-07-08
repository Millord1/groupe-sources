# 1.2, ez vénère
SELECT COUNT(commune) as total_commune, departement, region
FROM dim_commune
GROUP BY region, departement;

# 1.3, vénère
SELECT SUM(fe.nb) as total_etablissements, dc.departement, dt.libelle
FROM fait_etablissement AS fe
INNER JOIN dim_commune AS dc ON fe.insee_code = dc.insee_code
LEFT JOIN dim_type AS dt ON fe.type = dt.type
GROUP BY dc.departement, dt.libelle;

# 2.1
SELECT SUM(dc.population) as total_population, dc.departement, dc.region
FROM dim_commune AS dc
GROUP BY dc.departement, dc.region;

# 2.2
SELECT sum(fe.nb) as total_pharmacie, dc.departement
FROM fait_etablissement AS fe
INNER JOIN dim_commune AS dc ON fe.insee_code = dc.insee_code
WHERE type = 'pharmacie'
GROUP BY dc.departement
ORDER BY total_pharmacie DESC;

# 2.3
SELECT SUM(fe.nb) as total_etabliseement, fe.type, dc.commune, dc.departement
FROM fait_etablissement AS fe
INNER JOIN dim_commune AS dc ON fe.insee_code = dc.insee_code
GROUP BY dc.departement, dc.commune, fe.type
ORDER BY dc.departement ASC

# 3.1
SELECT c.insee_code, c.commune, c.departement, 
    SUM(CASE WHEN f.type = 'lycee' THEN f.nb END) AS total_lycee,
    COALESCE(SUM(CASE WHEN f.type = 'pharmacie' THEN f.nb END), 0) AS total_pharmacie
FROM fait_etablissement f
JOIN dim_commune c ON c.insee_code = f.insee_code
GROUP BY c.insee_code, c.commune, c.departement
HAVING 
    COUNT(CASE WHEN f.type = 'lycee' AND f.nb > 0 THEN 1 END) > 0
    AND 
    COUNT(CASE WHEN f.type = 'pharmacie' AND f.nb > 0 THEN 1 END) = 0;

# 3.2
SELECT c.insee_code, c.commune, f.nb, f.type
FROM fait_etablissement AS f
INNER JOIN dim_commune AS c ON f.insee_code = c.insee_code
GROUP BY f.type, c.insee_code, f.nb;

# 3.3
SELECT c.commune, c.population, 
    COALESCE(SUM(f.nb) ,0) AS total_services,
    ROUND( (COALESCE(SUM(f.nb), 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k
FROM dim_commune AS c
LEFT JOIN fait_etablissement AS f ON c.insee_code = f.insee_code
WHERE c.population > 0
GROUP BY c.insee_code, c.commune, c.population
ORDER BY services_for_10k DESC, c.population ASC;

# 4.1
SELECT c.departement, 
    ROUND(c.population / COALESCE(COUNT(CASE WHEN f.type = 'pharmacie' THEN f.nb END), 0), 2) AS hab_per_pharmacie
FROM dim_commune AS c
LEFT JOIN fait_etablissement AS f ON c.insee_code = f.insee_code
WHERE c.population > 0 AND CASE WHEN f.type = 'pharmacie' AND f.nb > 0 THEN TRUE ELSE FALSE END
GROUP BY c.departement, c.population
ORDER BY hab_per_pharmacie DESC

# 4.2 
# Gros doute sur le calcul
SET search_path TO entrepot, public;
SELECT b.name, COALESCE(ROUND(NULLIF(b.borrowers, 0) / c.population, 2), 0) AS taux, c.commune
FROM public.bibliotheque AS b
INNER JOIN dim_commune AS c ON b.insee_code = c.insee_code
WHERE borrowers IS NOT NULL
ORDER BY taux DESC

# 4.3
SELECT c.departement, c.commune, f.type,
    ROUND(COALESCE(SUM(f.nb)::NUMERIC, 0) / NULLIF(c.population, 0) * 10000, 2) AS services_for_10k
FROM dim_commune AS c
INNER JOIN fait_etablissement AS f ON c.insee_code = f.insee_code
WHERE c.population > 0 
    -- AND f.type = 'club_boxe_thai'
GROUP BY c.departement, f.type, c.commune, c.population
ORDER BY c.departement ASC, services_for_10k DESC

# Bonus
WITH ranked AS (
    SELECT c.departement AS dept_name, c.commune AS commune_name, f.type AS type,
        ROUND(COALESCE(SUM(f.nb)::numeric, 0) / NULLIF(c.population, 0) * 10000, 2) AS services_for_10k,
        ROW_NUMBER() OVER(PARTITION BY c.departement ORDER BY COALESCE(SUM(f.nb)::numeric, 0)::NUMERIC / NULLIF(c.population, 0)) AS rn
    FROM dim_commune AS c
    INNER JOIN fait_etablissement AS f ON c.insee_code = f.insee_code
    WHERE c.population > 0 
    GROUP BY c.departement, c.commune, f.type, c.population
)
SELECT dept_name, commune_name, type, services_for_10k, rn
FROM ranked AS r
WHERE rn <= 3
GROUP BY dept_name, commune_name, type, services_for_10k, rn
ORDER BY dept_name ASC, services_for_10k DESC;