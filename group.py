import requests
import collect
import clean
import load

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

# URL = (
#     "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
# )
# PER_PAGE = 20000
# SELECT = ()

# cur.execute("SELECT count(*) FROM eau")
# offset = cur.fetchone()[0]
# seen = set()

# while True:
#     try:
#         rows = collect.fetch_page(url=URL, SELECT=SELECT, order_by='', offset=offset)
#     except requests.RequestException as e:
#         print(f"API indisponible ({type(e).__name__})")
#         break
#     if not rows:
#         break
    
#     chunk = []
#     for row in rows:
#         g = clean.clean_gare(row)
#         if g["code_uic"] and g["code_uic"] not in seen:
#             seen.add(g["code_uic"])
#             chunk.append(g)
#     load.insert_chunk(cur, "gare", chunk)
#     conn.commit()
    
#     offset += 100
    
#     if offset >= 10_000:
#         break
    
# cur.execute("SELECT count(*) FROM ")
# print({cur.fetchone()[0]})
conn.commit()
conn.close()