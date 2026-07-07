SELECT 
    r.name AS region_name, d.name AS dep_name, COUNT(c.insee_code) AS total_communes
FROM commune AS c
INNER JOIN departement AS d ON c.code_departement = d.code_departement
INNER JOIN region AS r ON d.code_region = r.code_region
GROUP BY ROLLUP(r.name, d.name)
ORDER BY r.name NULLS LAST, d.name NULLS LAST;

WITH total_service_commune AS (
    SELECT u.insee_code, u.service, SUM(u.nbr) AS total_services
    FROM (
      SELECT 'bibliotheque' AS service, insee_code, COUNT(code_bib) AS nbr FROM bibliotheque GROUP BY insee_code
      UNION ALL
      SELECT 'clubs_boxe_thai' AS service, insee_code, COUNT(id::text) AS nbr FROM clubs_boxe_thai GROUP BY insee_code
      UNION ALL
      SELECT 'college' AS service, insee_code, COUNT(uai) AS nbr FROM college GROUP BY insee_code
      UNION ALL
      SELECT 'dechets_radioactifs' AS service, insee_code, COUNT(id::text) AS nbr FROM dechets_radioactifs GROUP BY insee_code
      UNION ALL
      SELECT 'ehpad' AS service, insee_code, COUNT(finess) AS nbr FROM ehpad GROUP BY insee_code
      UNION ALL
      SELECT 'lycee' AS service, insee_code, COUNT(uai) AS nbr FROM lycee GROUP BY insee_code
      UNION ALL
      SELECT 'pharmacie' AS service, insee_code, COUNT(finess) AS nbr FROM pharmacie GROUP BY insee_code
    ) AS u
    GROUP BY u.insee_code, u.service
)

SELECT d.name AS dept_name, s.service AS service_name, SUM(s.total_services) AS nombre_etablissements
FROM commune AS c
LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
INNER JOIN departement AS d ON c.code_departement = d.code_departement
WHERE c.population > 0 AND s.service IS NOT NULL
GROUP BY d.name, s.service
ORDER BY d.name, nombre_etablissements DESC;

# 2.1
SET search_path TO entrepot, public;
SELECT r.name AS region_name, d.name AS dept_name, SUM(c.population) as total_population
FROM public.commune AS c
INNER JOIN public.departement AS d ON c.code_departement = d.code_departement
INNER JOIN public.region AS r ON d.code_region = r.code_region
GROUP BY ROLLUP(r.name, d.name)

SELECT COUNT(p.finess) as total_pharmacie, d.name as dept_name, d.code_departement as dept_code
FROM pharmacie AS p
INNER JOIN commune AS c ON p.insee_code = c.insee_code
INNER JOIN departement AS d ON c.code_departement = d.code_departement
GROUP BY d.name, d.code_departement
ORDER BY total_pharmacie DESC

WITH count_etab AS (
    SELECT c.code_departement, c.insee_code, c.name AS commune_name, COUNT(t.*) AS total_etab
    FROM commune AS c
    LEFT JOIN {table} AS t ON c.insee_code = t.insee_code
    GROUP BY c.code_departement, c.insee_code
)
SELECT ROUND(AVG(ce.total_etab), 1) as mean_etab , '{table}' AS table_name, d.name as dept_name, ce.commune_name
FROM count_etab AS ce
INNER JOIN departement AS d ON ce.code_departement = d.code_departement
GROUP BY d.name, ce.commune_name
ORDER BY d.name

SELECT c.name AS commune_name, COUNT(DISTINCT l.uai) AS total_lycee 
FROM commune AS c
INNER JOIN lycee AS l ON c.insee_code = l.insee_code
LEFT JOIN pharmacie AS p ON c.insee_code = p.insee_code
GROUP BY c.insee_code, c.name
HAVING COUNT(p.insee_code) = 0;

SELECT '{table}' AS table_name, c.insee_code, c.name AS commune_name, COUNT(t.*) AS total_etab
FROM commune AS c
LEFT JOIN {table} AS t ON c.insee_code = t.insee_code
GROUP BY c.name, table_name, c.insee_code
HAVING COUNT(t.*) > 0

# 3.3
 WITH total_service_commune AS (
    SELECT u.insee_code, SUM(u.nbr) AS total_services
    FROM (
        SELECT insee_code, COUNT(code_bib) AS nbr FROM bibliotheque GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(id::text) AS nbr FROM clubs_boxe_thai GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(name) AS nbr FROM college GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(nom_du_site) AS nbr FROM dechets_radioactifs GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(name) AS nbr FROM ehpad GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(name) AS nbr FROM lycee GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(insee_code) AS nbr FROM mairie GROUP BY insee_code
        UNION ALL
        SELECT insee_code, COUNT(name) AS nbr FROM pharmacie GROUP BY insee_code
    ) AS u
    GROUP BY u.insee_code
)
SELECT c.name AS commune_name, c.population,
    COALESCE(s.total_services, 0) AS total_services,
    ROUND( (COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k
FROM commune AS c
LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
ORDER BY services_for_10k ASC
LIMIT 10;

# 4.1
-- EXPLAIN (ANALYSE, BUFFERS)
WITH phar_par_commune AS (
    SELECT insee_code, COUNT(finess) AS nb_pharmacies
    FROM public.pharmacie
    GROUP BY insee_code
)
SELECT ROUND(SUM(c.population) / SUM(p.nb_pharmacies), 2) AS hab_per_pharmacie, d.name AS dept_name
FROM public.commune AS c
INNER JOIN phar_par_commune AS p ON c.insee_code = p.insee_code
INNER JOIN public.departement AS d ON c.code_departement = d.code_departement
GROUP BY d.name
ORDER BY hab_per_pharmacie DESC;

# 4.2 Borrowers
SELECT b.name, ROUND(b.population / NULLIF(b.borrowers, 0), 0) AS taux
FROM public.bibliotheque AS b
WHERE b.borrowers IS NOT NULL AND b.population IS NOT NULL AND b.population > 0;

# 4.3 V1
WITH total_services AS (
	SELECT u.insee_code, u.service, SUM(u.nbr) AS total_service
	FROM (
      SELECT 'bibliotheque' AS service, insee_code, COUNT(code_bib) AS nbr FROM bibliotheque GROUP BY insee_code
      UNION ALL
      SELECT 'clubs_boxe_thai' AS service, insee_code, COUNT(id::text) AS nbr FROM clubs_boxe_thai GROUP BY insee_code
      UNION ALL
      SELECT 'college' AS service, insee_code, COUNT(uai) AS nbr FROM college GROUP BY insee_code
      UNION ALL
      SELECT 'dechets_radioactifs' AS service, insee_code, COUNT(id::text) AS nbr FROM dechets_radioactifs GROUP BY insee_code
      UNION ALL
      SELECT 'ehpad' AS service, insee_code, COUNT(finess) AS nbr FROM ehpad GROUP BY insee_code
      UNION ALL
      SELECT 'lycee' AS service, insee_code, COUNT(uai) AS nbr FROM lycee GROUP BY insee_code
      UNION ALL
      SELECT 'pharmacie' AS service, insee_code, COUNT(finess) AS nbr FROM pharmacie GROUP BY insee_code
    ) AS u
    GROUP BY u.insee_code, u.service
)
SELECT d.name AS dept_name, s.service,
	ROUND( (COALESCE(s.total_service, 0)::numeric / NULLIF(c.population, 0)), 10) AS service_per_hab
FROM commune AS c
LEFT JOIN total_services AS s ON c.insee_code = s.insee_code
INNER JOIN departement AS d ON c.code_departement = d.code_departement
WHERE c.population > 0
GROUP BY d.name, s.total_service, c.population, s.service
ORDER BY service_per_hab desc;

# 4.3 V2
WITH total_service_commune AS (
	SELECT u.insee_code, u.service, SUM(u.nbr) AS total_services
	FROM (
      SELECT 'bibliotheque' AS service, insee_code, COUNT(code_bib) AS nbr FROM bibliotheque GROUP BY insee_code
      UNION ALL
      SELECT 'clubs_boxe_thai' AS service, insee_code, COUNT(id::text) AS nbr FROM clubs_boxe_thai GROUP BY insee_code
      UNION ALL
      SELECT 'college' AS service, insee_code, COUNT(name) AS nbr FROM college GROUP BY insee_code
      UNION ALL
      SELECT 'dechets_radioactifs' AS service, insee_code, COUNT(nom_du_site) AS nbr FROM dechets_radioactifs GROUP BY insee_code
      UNION ALL
      SELECT 'ehpad' AS service, insee_code, COUNT(name) AS nbr FROM ehpad GROUP BY insee_code
      UNION ALL
      SELECT 'lycee' AS service, insee_code, COUNT(name) AS nbr FROM lycee GROUP BY insee_code
      UNION ALL
      SELECT 'pharmacie' AS service, insee_code, COUNT(name) AS nbr FROM pharmacie GROUP BY insee_code
    ) AS u
    GROUP BY u.insee_code, u.service
),   
ranked AS (
	SELECT d.name AS dept_name, c.name AS commune_name, s.service AS service_name,
		ROUND((COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 2) AS services_for_10k,
		ROW_NUMBER() OVER(PARTITION BY d.name ORDER BY COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) AS rn
	FROM commune AS c
	LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
	INNER JOIN departement AS d ON c.code_departement = d.code_departement
	WHERE c.population > 0
)
SELECT dept_name, commune_name, service_name, services_for_10k, rn
FROM ranked
WHERE rn <= 3
ORDER BY services_for_10k DESC, dept_name ASC;


# Bonus
WITH total_service_commune AS (
	SELECT u.insee_code, u.service, SUM(u.nbr) AS total_services
	FROM (
      SELECT 'bibliotheque' AS service, insee_code, COUNT(code_bib) AS nbr FROM bibliotheque GROUP BY insee_code
      UNION ALL
      SELECT 'clubs_boxe_thai' AS service, insee_code, COUNT(id::text) AS nbr FROM clubs_boxe_thai GROUP BY insee_code
      UNION ALL
      SELECT 'college' AS service, insee_code, COUNT(name) AS nbr FROM college GROUP BY insee_code
      UNION ALL
      SELECT 'dechets_radioactifs' AS service, insee_code, COUNT(nom_du_site) AS nbr FROM dechets_radioactifs GROUP BY insee_code
      UNION ALL
      SELECT 'ehpad' AS service, insee_code, COUNT(name) AS nbr FROM ehpad GROUP BY insee_code
      UNION ALL
      SELECT 'lycee' AS service, insee_code, COUNT(name) AS nbr FROM lycee GROUP BY insee_code
      UNION ALL
      SELECT 'pharmacie' AS service, insee_code, COUNT(name) AS nbr FROM pharmacie GROUP BY insee_code
    ) AS u
    GROUP BY u.insee_code, u.service
),   
ranked AS (
	SELECT d.name AS dept_name, c.name AS commune_name, s.service AS service_name,
		ROUND((COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) * 10000, 5) AS services_for_10k,
		ROW_NUMBER() OVER(PARTITION BY d.name ORDER BY COALESCE(s.total_services, 0)::numeric / NULLIF(c.population, 0)) AS rn
	FROM commune AS c
	LEFT JOIN total_service_commune AS s ON c.insee_code = s.insee_code
	INNER JOIN departement AS d ON c.code_departement = d.code_departement
	WHERE c.population > 0
  	ORDER BY services_for_10k DESC
)

SELECT dept_name, commune_name, service_name, services_for_10k, rn
FROM ranked
WHERE rn <= 3 AND service_name IS NOT NULL
GROUP BY service_name, dept_name, commune_name, services_for_10k, rn
ORDER BY dept_name ASC;