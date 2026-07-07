# Données DVF (Demande de Valeur Foncière)

ATTENTION, les conditions d'utilisation de ces données sont particulières !

Veuillez lire les limites figurant dans 'conditions-generales-dutilisation.pdf'


## Fichier DVF au format CSV

Le fichier a été agrégé, reformatté et amélioré:
- code_commune reconstitué (5 caractères)
- identifiant de parcelle reconstitué (dep + commune + prefix + section + numero)
- dates remise au format ISO (AAAA-MM-JJ)

Les virgules décimales ont été remplacées par des points, le séparateur du fichier est donc la virgule, avec quote si nécessaire pour certain libellés.


## Tables de référence des natures de terrains non bâtis

Pour faciliter la réutilisation, le PDF d'origine a été transformé en 2 fichiers CSV à l'aide de Tabula.


## API : http://api.cquest.org/dvf

Il s'agit d'une micro API de démonstration qui permet d'interroger la contenu de la base DVF.

Les critères de recherche:
- code_commune = code INSEE de la commune (ex: 94068)
- section = section cadastrale (ex: 94068000CQ)
- numero_plan = identifiant de la parcelle, (ex: 94068000CQ0110)
- lat + lon + dist (optionnel): pour une recherche géographique, dist est par défaut un rayon de 500m
- code_postal

Les filtres de sélection complémentaires:
- nature_mutation (Vente, etc)
- type_local (Maison, Appartement, Local, Dépendance)

Exemples:

- http://api.cquest.org/dvf?code_commune=94068
- http://api.cquest.org/dvf?section=94068000CQ
- http://api.cquest.org/dvf?numero_plan=94068000CQ0110
- http://api.cquest.org/dvf?lat=48.85&lon=2.35&dist=200
- http://api.cquest.org/dvf?code_postal=89110&type_local=Maison

Le résultat est retourné au format JSON et GeoJSON pour la recherche géographique.

L'API est aussi accessible en HTTPS.


## Exemple d'utilisation de l'API: carte uMap

Carte dynamique disponible sur:

https://umap.openstreetmap.fr/fr/map/exploration-donnees-dvf_318471

Elle est alimentée en interrogeant l'API pour récupérer les maisons, appartements et locaux dans un rayon de 500m autour du centre de la carte.

 
2019-04-25
