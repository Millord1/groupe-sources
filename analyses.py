import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

url_db = os.getenv("DATABASE_URL")
engine = create_engine(url_db.replace("postgres://", "postgresql+psycopg2://", 1))
print("reseau_eau \n")
compte_reseau = pd.read_sql(
    """
    SELECT
        d.name,
        d.code_departement,
        COUNT(*) AS nb_reseaux
    FROM reseau_eau AS r
    JOIN commune AS c
        ON r.code_commune = c.insee_code
    JOIN departement AS d
        ON c.code_departement = d.code_departement
    GROUP BY
        d.name,
        d.code_departement;
    """,
    engine
)
print(compte_reseau)

print("qualite_eau \n")
eau= pd.read_sql(
    """
    SELECT
       d.name,
       d.code_departement,
       COUNT(*) AS nb_result
   FROM eau AS e
   JOIN commune AS c
       ON e.insee_code = c.insee_code
   JOIN departement AS d
       ON c.code_departement = d.code_departement
   GROUP BY
       d.name,
       d.code_departement;
    """,
    engine
)

print(eau)
print("geo_risque \n")
geo_risque= pd.read_sql(
    """
    SELECT
       d.name,
       d.code_departement,
       COUNT(*) AS nb_result
   FROM geo_risque AS g
   JOIN commune AS c
       ON g.insee_code = c.insee_code
   JOIN departement AS d
       ON c.code_departement = d.code_departement
   GROUP BY
       d.name,
       d.code_departement;
    """,
    engine
)

print(geo_risque)

print("dvf\n")
DVF= pd.read_sql(
    """
    SELECT
        d.name,
        d.code_departement,
        COUNT(*) AS nb_result
    FROM dvf AS dv
    JOIN commune AS c
        ON dv.insee_code = c.insee_code
    JOIN departement AS d
        ON c.code_departement = d.code_departement
    GROUP BY
        d.name,
        d.code_departement;
    """,
    engine
)
print(DVF)

DVF.to_csv("dvf.csv", index=False)
geo_risque.to_csv("geo_risque.csv", index=False)
eau.to_csv("eau.csv", index=False)
compte_reseau.to_csv("compte_reseau.csv", index=False)


