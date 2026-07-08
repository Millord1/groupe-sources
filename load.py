"""Load: Créer le schéma et écrire dans les tables SQL."""

import os
import pathlib
from dotenv import load_dotenv

import psycopg2
# DATABASE_URL='postgres:-//theau_megab_2687:tYzotg_Otd73igwtHdDifW_8HEAmhmIAMpuSJqKV2NDgzmrz9N_GIEG09oyc7vCL@theau-megab-2687.postgresql.c.osc-fr1.scalingo-dbs.com:33397/theau_megab_2687?sslmode=prefer'

load_dotenv()
DB_URL = os.environ.get('DATABASE_URL')
SCHEMA = pathlib.Path(__file__).resolve().parent / "schema.sql"


def connect():
    return psycopg2.connect(DB_URL)

def create_schema(cur):
    cur.execute(SCHEMA.read_text())


def count_rows(cur, table, dept):
    """Lignes de CE département déjà dans la table (le code INSEE commence par dept).

    Sert à la reprise par département : une commune du 69 a un code INSEE en 69xxx,
    donc on les compte pour savoir où relancer la pagination.
    """
    cur.execute(f"SELECT count(*) FROM {table} WHERE insee_code LIKE %s", (dept + "%",))
    return cur.fetchone()[0]

def count_geo(cur, table, communes):
    cur.execute(f"""
        SELECT COUNT(*) FROM {table} WHERE insee_code IN ({communes})            
    """)
    return cur.fetchone()[0]

def insert_geography(cur, raw_communes):
    """Insère région, département, commune (dans l'ordre des clés étrangères).

    geo.api donne pour chaque commune son département et sa région (code + nom).
    On en déduit les trois niveaux. Renvoie l'ensemble des codes INSEE connus.
    """
    regions, departements, communes = {}, {}, []
    for c in raw_communes:
        dep = c.get("departement") or {}
        reg = c.get("region") or {}
        if reg.get("code"):
            regions[reg["code"]] = (reg["code"], reg["nom"])
        if dep.get("code"):
            departements[dep["code"]] = (dep["code"], dep["nom"], reg.get("code"))
        communes.append((c["code"], c["nom"], c.get("population"), dep.get("code")))

    cur.executemany(
        "INSERT INTO region (code_region, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        list(regions.values()),
    )
    cur.executemany(
        "INSERT INTO departement (code_departement, name, code_region) "
        "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        list(departements.values()),
    )
    cur.executemany(
        "INSERT INTO commune (insee_code, name, population, code_departement) "
        "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        communes,
    )
    return {c[0] for c in communes}


def insert_mairies(cur, raw_communes):
    """Une mairie par commune, dérivée du référentiel (aucun appel API en plus)."""
    rows = [(c["code"], f"Mairie de {c['nom']}") for c in raw_communes]
    cur.executemany(
        "INSERT INTO mairie (insee_code, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        rows,
    )


def insert_chunk(cur, table, chunk):
    """Insère un chunk de dicts. Les colonnes sont les clés des dicts."""
    if not chunk:
        return
    columns = list(chunk[0].keys())
    placeholders = ", ".join(f"%({c})s" for c in columns)
    print(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING")
    cur.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
        chunk,
    )
