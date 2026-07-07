"""Rapatrier toutes les gares de France, en un seul passage global.

Pourquoi un script à part, et pas une source par département comme les autres :
le dataset SNCF (frequentation-gares) n'a NI code commune NI coordonnées, et son
code postal ne permet pas de filtrer proprement les départements 01-09. Comme il
n'y a que ~3000 gares, on les rapatrie TOUTES d'un coup, sans les relier à une
commune. La liaison (par exemple un géocodage via la BAN) sera une étape séparée,
faite plus tard. Pour l'instant, on ne fait qu'écrire.

    python3 gares.py

C'est l'API Opendatasoft de la SNCF (même forme que les autres sources), donc on
réutilise tel quel collect.fetch_page (avec un where vide = toutes les gares),
clean et load. La reprise marche aussi : on repart du nombre de gares déjà chargées.
"""

import requests

import collect
import clean
import load

# Dataset SNCF, hébergé sur une instance Opendatasoft (même API que data.education).
URL = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets"
    "/frequentation-gares/records"
)
SELECT = (
    "code_uic_complet,nom_gare,code_postal,direction_regionale_gares,"
    "total_voyageurs_2024,total_voyageurs_2023"
)

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

# Reprise : on repart du nombre de gares déjà chargées (pas de notion de département).
cur.execute("SELECT count(*) FROM gare")
offset = cur.fetchone()[0]
seen = set()  # code_uic déjà vus (deduplication)

while True:
    try:
        # where vide : toutes les gares, sans filtre département. Tri sur la clé pour
        # une pagination stable. (voir collect.fetch_page : c'est le même appel ODS)
        rows = collect.fetch_page(URL, "", SELECT, "code_uic_complet", offset)
    except requests.RequestException as e:
        print(f"gare: API indisponible ({type(e).__name__}), relance gares.py pour reprendre")
        break
    if not rows:
        break  # plus de page

    chunk = []
    for row in rows:
        g = clean.clean_gare(row)
        if g["code_uic"] and g["code_uic"] not in seen:
            seen.add(g["code_uic"])
            chunk.append(g)
    load.insert_chunk(cur, "gare", chunk)
    conn.commit()  # on valide chaque page : si ça s'interrompt, c'est gardé

    offset += 100
    # Garde-fou Opendatasoft (offset + limit <= 10000) ; large vu les ~3000 gares.
    # Doc : https://help.opendatasoft.com/apis/ods-explore-v2/
    if offset >= 10_000:
        break

cur.execute("SELECT count(*) FROM gare")
print(f"gare: {cur.fetchone()[0]}")
conn.commit()
conn.close()
