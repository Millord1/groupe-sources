import pandas as pd
import sys

import os
from sqlalchemy import create_engine, text
import load



# postgresql+psycopg2://postgres:Mkilo1990@localhost:5432/megabase0

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/megabase0")
engine = create_engine(DB_URL.replace("postgres://", "postgresql://", 1))

with engine.begin() as conn:
#    conn.execute(text("DROP TABLE IF EXISTS dvf"))  

    conn.execute(
        text(
            """
           CREATE TABLE IF NOT EXISTS dvf (
                id_dvf          SERIAL PRIMARY KEY,
                id_mutation     TEXT,
                date_mutation   TEXT,
                nature_mutation TEXT,
                valeur_fonciere  DOUBLE PRECISION,  
                id_parcelle     TEXT,
                type_local      TEXT,
                nombre_pieces_principales INTEGER,
                nom_commune      TEXT,
                longitude       DOUBLE PRECISION,
                latitude        DOUBLE PRECISION,
                insee_code       TEXT REFERENCES commune (insee_code))
            """
        )
    )

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

url = f"https://files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/{DEPT}.csv.gz"

# collecte les données brutes

df = pd.read_csv(url, dtype=str)
# filtre les ventes

df.rename(columns={'code_commune': 'insee_code'}, inplace=True) 
df = df[["id_mutation",
        "date_mutation",
        "nature_mutation", 
        "valeur_fonciere",
        "id_parcelle",
        "type_local",
        "nombre_pieces_principales",
        "longitude",
        "latitude",
        "insee_code",
        "nom_commune"]]
# convertit les colonnes numériques en type numérique

df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors='coerce')
df["nombre_pieces_principales"] = df["nombre_pieces_principales"].astype("Int64")
df["latitude"] = pd.to_numeric(df["latitude"], errors='coerce')
df["longitude"] = pd.to_numeric(df["longitude"], errors='coerce')

codes_valides = set(
    pd.read_sql("SELECT insee_code FROM commune", engine)["insee_code"]
)

df.loc[~df["insee_code"].isin(codes_valides), "insee_code"] = "99999"

#print(df.head())

#conn = psycopg2.connect("postgresql://postgres:Mkilo1990@localhost:5432/megabase0")

conn = load.connect()
cur = conn.cursor()

nb_lignes = len(df)

nb_lignes_in_db = load.count_rows(cur, 'DVF', DEPT)

print(f"=== département {DEPT} ===")

if nb_lignes_in_db > 0:
    print(f"Déjà {nb_lignes_in_db} lignes DVF pour le département {DEPT}, pas d'insertion nécessaire.")
    sys.exit(0)

with engine.begin() as conn:
    conn.exec_driver_sql("""
        INSERT INTO region (code_region, name)
        VALUES ('99', 'Inconnue')
        ON CONFLICT (code_region) DO NOTHING;

        INSERT INTO departement (code_departement, name, code_region)
        VALUES ('99', 'Inconnu', '99')
        ON CONFLICT (code_departement) DO NOTHING;

        INSERT INTO commune (insee_code, name, population, code_departement)
        VALUES ('99999', 'Commune inconnue', 0, '99')
        ON CONFLICT (insee_code) DO NOTHING;
    """)




df.to_sql("dvf", engine, if_exists="append", index=False, method="multi", chunksize=1000)



print(f"Réussite : {load.count_rows(cur, 'DVF', DEPT)} lignes DVF insérées pour le département {DEPT}")


#print(pd.read_sql("SELECT * FROM dvf LIMIT 10", engine))