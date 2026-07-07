
# Les arrondissements de Lyon, Paris et Marseille ne sont pas dans la liste des
# communes (geo.api renvoie une seule commune : 69123, 75056, 13055).
# On ramène chaque arrondissement vers sa commune principale.
DISTRICTS = {}
DISTRICTS.update({str(c): "69123" for c in range(69381, 69390)})  # Lyon
DISTRICTS.update({str(c): "75056" for c in range(75101, 75121)})  # Paris
DISTRICTS.update({str(c): "13055" for c in range(13201, 13217)})  # Marseille


def normalize_insee(code):
    code = str(code).strip()
    return DISTRICTS.get(code, code)


def _to_float(v):
    # certains champs (lat/lon) arrivent en texte : on convertit, ou None si on ne peut pas
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v):
    # certains compteurs arrivent en float (397.0) ou en texte : on ramène à un entier
    try:
        return int(float(v))
    except (TypeError, ValueError):
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

        "date_prelevement": row.get("date_prelevement"),
    }

def clean_education(row):
    return {
        "uai": row.get("identifiant_de_l_etablissement"),
        "name": row.get("nom_etablissement"),
        "status": row.get("statut_public_prive"),
        "nature": row.get("libelle_nature"),
        "address": row.get("adresse_1"),
        "postal_code": row.get("code_postal"),
        "commune_name": row.get("nom_commune"),
        "phone": row.get("telephone"),
        "email": row.get("mail"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "insee_code": normalize_insee(row.get("code_commune")),
    }


def clean_finess(row):
    coord = row.get("coord") or {}
    rue = " ".join(str(p) for p in [row.get("numvoie"), row.get("typvoie"), row.get("voie")] if p)
    return {
        "finess": row.get("nofinesset"),
        "name": row.get("rs"),
        "category": row.get("libcategetab"),
        "address": rue,
        "postal_line": row.get("ligneacheminement"),
        "commune_name": row.get("com_name"),
        "phone": row.get("telephone"),
        "siret": row.get("siret"),
        "latitude": coord.get("lat"),
        "longitude": coord.get("lon"),
        "insee_code": normalize_insee(row.get("com_code")),
    }


def clean_gare(row):
    # Pas de code commune ici : on garde le brut (le rattachement viendra plus tard).
    return {
        "code_uic": row.get("code_uic_complet"),
        "name": row.get("nom_gare"),
        "postal_code": row.get("code_postal"),
        "region_sncf": row.get("direction_regionale_gares"),
        "travelers_2024": row.get("total_voyageurs_2024"),
        "travelers_2023": row.get("total_voyageurs_2023"),
    }


def clean_culture(row):
    return {
        "code_bib": row.get("code_bib"),
        "name": row.get("nom_de_l_etablissement"),
        "status": row.get("statut"),
        "address": row.get("adresse"),
        "postal_code": row.get("cp"),
        "commune_name": row.get("ville"),
        "phone": row.get("telephone"),
        "population": _to_int(row.get("population_commune")),
        "borrowers": _to_int(row.get("nombre_d_emprunteurs")),
        "loans": _to_int(row.get("nombre_de_prets")),
        "latitude": _to_float(row.get("latitude")),
        "longitude": _to_float(row.get("longitude")),
        "insee_code": normalize_insee(row.get("code_insee_commune")),
    }

def clean_sports(row):
    return {
        "insee_code": normalize_insee(row.get("cc_2024")),
        "nom_commune": row.get("cc_lib"),
        "code_departement": row.get("dep"),
        "code_fede_ref": _to_int(row.get("code_fede_ref")),
        "nombre_clubs": _to_int(row.get("n_clubs")),
        "nombre_actifs_clubs": _to_int(row.get("n_actifs_clubs")),
        "code_epci": row.get("epci_code"),
        "nom_epci": row.get("epci_name"),
        "annee_data": row.get("annee")
    }
    
def clean_dechets(row):
    return {
        "nom_commune": row.get("ville"),
        "insee_code": normalize_insee(row.get("departement")),
        "nom_du_site": row.get("nom_du_site"),
        "categorie": row.get("categorie"),
        "famille_in": row.get("famille_in"),
        "description_physique": row.get("description_physique"),
        "volume_equivalent_conditionne": _to_float(row.get("volume_equivalent_conditionne")),
        "activite_bq": _to_float(row.get("activite_bq")),
        "principaux_radionuclides": row.get("principaux_radionucleides"),
        "groupe_de_dechets": row.get("groupe_de_dechets"),
        "sous_groupe_de_dechets": row.get("sous_groupe_de_dechets"),
        "majoration": row.get("majoration")
    }

def clean_btp(etab, nom):
    # etab = un établissement de matching_etablissements ; nom = nom de l'entreprise.
    return {
        "siret": etab.get("siret"),
        "name": (nom or "")[:200],
        "commune_name": etab.get("libelle_commune"),
        "tranche_effectif": etab.get("tranche_effectif_salarie"),
        "latitude": _to_float(etab.get("latitude")),
        "longitude": _to_float(etab.get("longitude")),
        "insee_code": normalize_insee(etab.get("commune")),
    }
