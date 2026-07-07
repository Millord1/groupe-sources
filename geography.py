import collect
import requests
import load
import sys

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

conn = load.connect()
cur = conn.cursor()

try:
    raw_communes = collect.fetch_communes(DEPT)
except requests.RequestException as e:
    print(f"  géographie indisponible ({type(e).__name__}), relance le département {DEPT}")
    raise SystemExit
known_communes = load.insert_geography(cur, raw_communes)
conn.commit()
print(f"{len(raw_communes)} rows inserted for {DEPT}")