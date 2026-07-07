"""Rapatrier les entreprises du BTP, par département.

recherche-entreprises.api.gouv.fr n'est PAS une API Opendatasoft : pagination par
PAGE (per_page max 25), réponse {results, total_pages}, et la commune est dans
matching_etablissements (l'établissement présent dans le département). On ne passe
donc pas par collect.fetch_page : ce fichier a son propre fetch. Pas de géocodage,
la commune (code INSEE) est déjà fournie.

    python3 btp.py 69

On charge d'abord la géographie du département (pour relier les entreprises à leur
commune par clé étrangère), puis on parcourt les pages. Reprise : on repart de la
page déduite du nombre d'entreprises déjà chargées pour ce département.
"""

import sys

import requests

import collect
import clean
import load

SEARCH = "https://recherche-entreprises.api.gouv.fr/search"
PER_PAGE = 25  # maximum autorisé par l'API

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

print(f"=== BTP département {DEPT} ===")

# Géographie d'abord : il faut les communes pour relier les entreprises (clé étrangère).
try:
    raw_communes = collect.fetch_communes(DEPT)
except requests.RequestException as e:
    print(f"  géographie indisponible ({type(e).__name__}), relance btp.py {DEPT}")
    raise SystemExit
known_communes = load.insert_geography(cur, raw_communes)
conn.commit()

# Reprise : page de départ déduite du nombre d'entreprises déjà chargées pour ce dept.
already = load.count_rows(cur, "entreprise_btp", DEPT)
page = already // PER_PAGE + 1
seen = set()  # SIRET déjà vus (deduplication)

while True:
    try:
        resp = session.get(
            SEARCH,
            params={
                "section_activite_principale": "F",  # construction = codes NAF 41/42/43
                "departement": DEPT,
                "page": page,
                "per_page": PER_PAGE,
            },
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  API indisponible ({type(e).__name__}), relance btp.py {DEPT} pour reprendre")
        break

    data = resp.json()
    results = data.get("results", [])
    if not results:
        break  # plus de page

    chunk = []
    for entreprise in results:
        nom = entreprise.get("nom_complet")
        # la commune est dans les établissements présents dans le département
        for etab in entreprise.get("matching_etablissements") or []:
            if etab.get("etat_administratif") != "A":
                continue  # on ne garde que les établissements actifs
            b = clean.clean_btp(etab, nom)
            if b["siret"] and b["insee_code"] in known_communes and b["siret"] not in seen:
                seen.add(b["siret"])
                chunk.append(b)
    load.insert_chunk(cur, "entreprise_btp", chunk)
    conn.commit()  # on valide chaque page : si ça s'interrompt, c'est gardé

    if page >= data.get("total_pages", 0):
        break
    page += 1
    if page * PER_PAGE >= 10_000:  # plafond de recherche-entreprises (10000 résultats)
        break

print(f"entreprise_btp: {load.count_rows(cur, 'entreprise_btp', DEPT)}")
conn.commit()
conn.close()
