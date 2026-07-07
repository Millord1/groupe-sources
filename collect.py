"""Collect: fetch données brutes depuis les APIs OpenData."""

import requests

session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

GEO = "https://geo.api.gouv.fr/communes"


def fetch_communes(dept):
    """Communes d'un département en 1 call (avec leur département et région)."""
    resp = session.get(
        GEO,
        params={
            "codeDepartement": dept,
            "fields": "nom,code,population,departement,region",
            "format": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_page(url, where, select, order_by, offset):
    """Une page (jusque 100 lignes) d'un dataset Opendatasoft."""
    resp = session.get(
        url,
        params={
            "where": where,
            "select": select,
            "order_by": order_by,
            "limit": 100,
            "offset": offset,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])