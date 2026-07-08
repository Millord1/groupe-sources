import requests
import pandas as pd
import psycopg2
import requests
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url_db = os.getenv("URL_DB")
engine = create_engine(url_db)
print(url_db)
with engine.begin() as conn:
      conn.execute("""
        
        CREATE TABLE IF NOT EXISTS reseau_eau(
         
    code_commune VARCHAR(10) NOT NULL,
    nom_commune TEXT,
    nom_quartier VARCHAR(100),
    code_reseau VARCHAR(20),
    nom_reseau VARCHAR(100),
    debut_alim DATE,
    annee INTEGER,

    CONSTRAINT fk_commune
        FOREIGN KEY (code_commune)
        REFERENCES commune(insee_code)
            )
    """)

df = pd.read_sql(
    """
 SELECT c.name ,c.insee_code FROM commune AS c;
    """,
    engine)
print(df)
url = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi"

LIMIT = 100
for code_commune in df["insee_code"].unique():

    offset = 0

    while True:

        try:
            r = requests.get(
                url,
                params={
                    "annee": 2026,
                    "code_commune": code_commune,
                    "size": LIMIT,
                    "offset": offset,
                },
                timeout=10,
            )

            r.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"{code_commune}: {e}")
            break

        data = r.json()
        results = data.get("data", [])
        df=pd.DataFrame(results)
        print(df)
        print(list(df))
        df.to_sql(
            "reseau_eau",
          con=engine,
         if_exists="append",
          index=False
          )
        if not results:
            break

        if len(results) < LIMIT:
            break
        
        offset += LIMIT

