import sys
import requests
import load
import collect
from time import sleep
from dotenv import load_dotenv
import os

load_dotenv()

depts = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '2A', '2B', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '971', '972', '973', '974', '976']
  
# DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

SEARCH = 'https://georisques.gouv.fr/api/v1/gaspar/risques'
PER_PAGE = 20

session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

for dept in depts:
    
    conn = load.connect()
    cur = conn.cursor()
    load.create_schema(cur)
    
    print(f"=== Geo Risque département {dept} ===")

    try:
        raw_communes = collect.fetch_communes(dept)
    except requests.RequestException as e:
        print(f"géographie indisponible ({type(e).__name__}), relance geo_risque.py {dept}")
        raise SystemExit
    known_communes = list(load.insert_geography(cur, raw_communes))
    conn.commit()

    already = load.count_rows(cur, "geo_risque", dept)
    page = already // PER_PAGE + 1
    seen = set() 
        
    n = 10
    splitted = res = [known_communes[i:i + n] for i in range(0, len(known_communes), n)]
    chunk = []
    for split in splitted:
        communes = ",".join(split)
        print(communes)
        str_communes = ",".join([f"'{val}'" for val in split])
        
        nb_rows = load.count_geo(cur=cur, table="geo_risque", communes=str_communes)
        
        # while True:
        try:
            resp = session.get(
                SEARCH,
                params= {
                    "code_insee": communes, "page_size": 100
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

        for risque in results:
            risque_detail = risque.get('risques_detail')
            for risq_d in risque_detail:
                risq_d.update({'insee_code': risque['code_insee']})
            chunk.append(risque_detail)
            
        sleep(0.5)
            
    chunk_plat = [item for sublist in chunk for item in sublist]
    load.insert_chunk(cur, "geo_risque", chunk_plat)

    print(f"geo_risques: {load.count_rows(cur, 'geo_risque', dept)}")
    conn.commit()
    conn.close()
