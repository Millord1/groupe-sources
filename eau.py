import sys
import requests
import collect
import clean
import load
from time import sleep


DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)
    
print(f"=== Qualité eau potable département {DEPT} ===")
SEARCH = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
PER_PAGE = 20000


session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)
try:
    raw_communes = collect.fetch_communes(DEPT)
except requests.RequestException as e:
    print(f"  géographie indisponible ({type(e).name}), relance eau.py {DEPT}")
    raise SystemExit
known_communes = load.insert_geography(cur, raw_communes)
conn.commit()

already = load.count_rows(cur, "public.eau", DEPT)
page = already // PER_PAGE + 1
seen = set() 

while True:
    try:
        resp = session.get(
            SEARCH,
            params={
                "code_departement": DEPT,
                "page": page,
                "size": PER_PAGE,
            },
            timeout=(10, 300),
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"API indisponible ({type(e).__name__}), relance eau.py {DEPT} pour reprendre")
        break

    data = resp.json()
    results = data.get("data", [])
    if not results:
        break  # plus de page

    chunk = []
    for r in results:
        if r["identifiant"] and r["insee_code"] in known_communes and r["identifiant"] not in seen:
            seen.add(r["identifiant"])
            chunk.append(r)
    load.insert_chunk(cur, "public.eau", chunk)
    conn.commit() 

    if not data.get("next"):
        break
    page += 1
    sleep(1)
    

print(f"qualite_eau_potable: {load.count_rows(cur, 'public.eau', DEPT)}")
conn.commit()
conn.close()