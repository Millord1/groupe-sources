import pandas as pd
import sys
import requests
import collect
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

depts = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2A', '2B', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '971', '972', '973', '974', '976']

for dept in depts:
    
    conn = load.connect()
    cur = conn.cursor()
    load.create_schema(cur)
    
    try:
        raw_communes = collect.fetch_communes(dept)
    except requests.RequestException as e:
        print(f"géographie indisponible ({type(e).__name__}), relance geo_risque.py {dept}")
        raise SystemExit
    known_communes = list(load.insert_geography(cur, raw_communes))
    
    conn.commit()
    conn.close()

    url = f"https://files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/{dept}.csv.gz"

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

    nb_lignes_in_db = load.count_rows(cur, 'DVF', dept)

    print(f"=== département {dept} ===")

    if nb_lignes_in_db > 0:
        print(f"Déjà {nb_lignes_in_db} lignes DVF pour le département {dept}, pas d'insertion nécessaire.")
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



    print(f"Réussite : {load.count_rows(cur, 'DVF', dept)} lignes DVF insérées pour le département {dept}")


#print(pd.read_sql("SELECT * FROM dvf LIMIT 10", engine))