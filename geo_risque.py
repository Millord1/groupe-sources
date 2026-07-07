import sys
import requests
import load
import collect
import clean

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

SEARCH = 'https://georisques.gouv.fr/api/v1/gaspar/risques'
PER_PAGE = 20

session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

print(f"=== Geo Risque département {DEPT} ===")

try:
    raw_communes = collect.fetch_communes(DEPT)
except requests.RequestException as e:
    print(f"géographie indisponible ({type(e).__name__}), relance geo_risque.py {DEPT}")
    raise SystemExit
known_communes = load.insert_geography(cur, raw_communes)
conn.commit()

already = load.count_rows(cur, "geo_risque", DEPT)
page = already // PER_PAGE + 1
seen = set() 


while True:
    # for commune in known_communes:
    try:
        resp = session.get(
            SEARCH,
            params= {
                "code_insee": ",".join(known_communes), "page_size": 100
            }
            # timeout=30
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(e)
        break
    
    data = resp.json()
    results = data.get("data", [])
    if not results:
        break
    
    chunk = []
    for risque in results:
        
    
    
    load.insert_chunk(cur, "geo_risque", chunk)
    conn.commit() 
    
    if page >= data.get("total_pages", 0):
        break
    page += 1
    if page * PER_PAGE >= 10_000:  # plafond de recherche-entreprises (10000 résultats)
        break
    
    

while True:
    try:
        resp = session.get(
            SEARCH,
            params={
                "code_departement": DEPT,
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

print(f"geo_risques: {load.count_rows(cur, 'geo_risque', DEPT)}")
conn.commit()
conn.close()
