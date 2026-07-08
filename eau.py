import sys
import requests
import collect
import clean
import load


# DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

depts = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2A', '2B', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '971', '972', '973', '974', '976']
conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

for dept in depts:    
    
    print(f"=== Qualité eau potable département {dept} ===")
    SEARCH = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
    PER_PAGE = 20000

    session = requests.Session()
    session.headers["User-Agent"] = "megabase-corrige0 (formation)"
    
    try:
        raw_communes = collect.fetch_communes(dept)
    except requests.RequestException as e:
        print(f"  géographie indisponible ({type(e).name}), relance eau.py {dept}")
        raise SystemExit
    known_communes = load.insert_geography(cur, raw_communes)
    conn.commit()

    already = load.count_rows(cur, "eau", dept)
    page = already // PER_PAGE + 1
    seen = set() 
    
    while True:
        try:
            resp = session.get(
                SEARCH,
                params={
                    "code_departement": dept,
                    "page": page,
                    "size": PER_PAGE,
                },
                timeout=(10, 300),
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"API indisponible ({type(e).__name__}), relance eau.py {dept} pour reprendre")
            break

        data = resp.json()
        results = data.get("data", [])
        if not results:
            break  # plus de page

        chunk = []
        for row in results:
            r = clean.clean_eau(row)
            if(r['insee_code']) in known_communes:
                chunk.append(r)
            # if r["identifiant"] and r["insee_code"] in known_communes and r["identifiant"] not in seen:
            #     seen.add(r["identifiant"])
            
        load.insert_chunk(cur, "eau", chunk)
        conn.commit() 

        if not data.get("next"):
            break
        page += 1

    print(f"qualite_eau_potable: {load.count_rows(cur, 'eau', dept)}")
    conn.commit()
conn.close()