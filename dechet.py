import sys
import requests
import load
import collect
import clean
import unicodedata

URL = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/inventaire-matieres-dechets-radioactifs/records"

DEPT = (sys.argv[1] if len(sys.argv) > 1 else "69").upper().zfill(2)

session = requests.Session()
session.headers["User-Agent"] = "megabase-corrige0 (formation)"

conn = load.connect()
cur = conn.cursor()
load.create_schema(cur)

cur.execute(f"SELECT count(*) FROM dechets_radioactifs WHERE code_dept = {DEPT}")
offset = cur.fetchone()[0]
# seen = set()

def _get_commune_mapping() -> dict:
    try:
        conn = load.connect()
        cur = conn.cursor()
        cur.execute(f"SELECT name, insee_code FROM commune WHERE insee_code LIKE '{DEPT}%'")
        commune_data = cur.fetchall()
        cur.close()
        conn.close()

        commune_mapping = {
            str(row[0]).strip().upper(): clean.normalize_insee(row[1])
            for row in commune_data
        }
    except Exception as e:
        print(e)
        commune_mapping = {}

    return commune_mapping

    
def clean_name(text: str) -> str:
    if not text:
        return ""
    text = str(text).strip().upper()
    clean_text = "".join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return clean_text.replace("-", " ")

mapping = _get_commune_mapping()

while True:
    try:
        rows = collect.fetch_page(
            url=URL, 
            where=f'departement="{DEPT}"', 
            select="ville,nom_du_site,categorie,famille_in,description_physique,volume_equivalent_conditionne,activite_bq,principaux_radionucleides,groupe_de_dechets,sous_groupe_de_dechets,majoration",
            order_by="ville",
            offset=offset
        )
    except Exception as e:
        print(e)
        break
    
    if not rows or not isinstance(rows, list):
        print("not rows")
        break
    
    chunk = []
    for row in rows:
        clean_data = clean.clean_dechets(row)
        
        nom_ville_brut = clean_data.get("nom_commune", "")
        nom_ville_clean = clean_name(str(nom_ville_brut).strip().upper())
        
        # unique_key = f"{clean_data['nom_du_site']}_{clean_data['famille_in']}_{clean_data['description_physique']}_{str(clean_data['volume_equivalent_conditionne'])}_{str(clean_data['activite_bq'])}_{clean_data['categorie']}"
        insee = mapping.get(nom_ville_clean)
        
        if not insee:
            for nom_mapping, code_insee in mapping.items():
                nom_mapping_clean = clean_name(nom_mapping)
                if nom_ville_clean in nom_mapping_clean or nom_mapping_clean in nom_ville_clean:
                    insee = code_insee
                    break  
        
        clean_data["insee_code"] = insee
        clean_data['code_dept'] = int(DEPT)

        # if clean_data['insee_code']:
            # seen.add(unique_key)
        chunk.append(clean_data)
            
    load.insert_chunk(cur, "dechets_radioactifs", chunk)
    conn.commit()
    
    offset += len(rows)
    print(f"length: {len(rows)}")
    print(offset)


cur.execute(f"SELECT count(*) FROM dechets_radioactifs WHERE code_dept = {DEPT}")
print(f"dechets radioactifs: {cur.fetchone()[0]}")
conn.close()