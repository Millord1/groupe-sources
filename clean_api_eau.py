"""Clean: une ligne de l'API Hub'Eau ."""

import pandas as pd


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_date(v):
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


def _to_str(v):
    if v is None:
        return None
    return str(v).strip()


def clean_eau_resultats_dis(row):
    return {
        # Identifiants géographiques
        "code_commune": _to_str(row.get("code_commune")),
        "nom_commune": _to_str(row.get("nom_commune")),

        # Paramètre qualité eau
        "code_parametre": _to_str(row.get("code_parametre")),
        "libelle_parametre": _to_str(row.get("libelle_parametre")),

        # Résultat d’analyse
        "resultat": _to_float(row.get("resultat")),
        "unite": _to_str(row.get("unite")),

        # Date prélèvement
        "date_prelevement": _to_date(row.get("date_prelevement")),
    }