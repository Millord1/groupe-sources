CREATE SCHEMA IF NOT EXISTS entrepot;

SET search_path TO entrepot, public;

CREATE TABLE IF NOT EXISTS dim_commune (
    insee_code VARCHAR(5) PRIMARY KEY,
    commune VARCHAR(150),
    departement VARCHAR(150),
    region VARCHAR(150),
    population INTEGER
);

CREATE TABLE IF NOT EXISTS dim_type (
    type TEXT PRIMARY KEY,
    libelle TEXT
);

CREATE TABLE IF NOT EXISTS fait_etablissement (
    insee_code VARCHAR(5) REFERENCES dim_commune (insee_code) ON DELETE CASCADE,
    type VARCHAR(50) REFERENCES dim_type (type) ON DELETE CASCADE,
    nb INTEGER NOT NULL,
    PRIMARY KEY (insee_code, type)
);

TRUNCATE TABLE dim_commune CASCADE;
INSERT INTO dim_commune (insee_code, commune, departement, region, population)
SELECT 
    c.insee_code,
    c.name AS commune,
    d.name AS departement,
    r.name AS region,
    c.population
FROM public.commune c
JOIN public.departement d ON d.code_departement = c.code_departement
JOIN public.region r ON r.code_region = d.code_region;

TRUNCATE TABLE dim_type CASCADE;
INSERT INTO dim_type (type, libelle) VALUES
('lycee', 'Lycée'),
('college', 'Collège'),
('pharmacie', 'Pharmacie'),
('ehpad', 'EHPAD'),
('bibliotheque', 'Bibliothèque'),
('club_boxe_thai', 'Club boxe Thai')
ON CONFLICT (type) DO NOTHING;

TRUNCATE TABLE fait_etablissement;
INSERT INTO fait_etablissement (insee_code, type, nb)
    SELECT insee_code, 'lycee' AS type, COUNT(*) AS nb FROM public.lycee WHERE insee_code IS NOT NULL GROUP BY insee_code
UNION ALL
    SELECT insee_code, 'college' AS type, COUNT(*) AS nb FROM public.college WHERE insee_code IS NOT NULL GROUP BY insee_code
UNION ALL
    SELECT insee_code, 'pharmacie' AS type, COUNT(*) AS nb FROM public.pharmacie WHERE insee_code IS NOT NULL GROUP BY insee_code
UNION ALL
    SELECT insee_code, 'ehpad' AS type, COUNT(*) AS nb FROM public.ehpad WHERE insee_code IS NOT NULL GROUP BY insee_code
UNION ALL
    SELECT insee_code, 'bibliotheque' AS type, COUNT(*) AS nb FROM public.bibliotheque WHERE insee_code IS NOT NULL GROUP BY insee_code
UNION ALL
    SELECT insee_code, 'club_boxe_thai' AS type, COUNT(*) AS nb FROM public.clubs_boxe_thai WHERE insee_code IS NOT NULL GROUP BY insee_code
ON CONFLICT (insee_code, type) DO UPDATE 
SET nb = EXCLUDED.nb;