# Projet : Bus-Level Load Reconstruction (Texas A&M / Overbye lab)

## Contexte
Reproduction des résultats du papier "A Framework for Weather-Dependent Bus-Level Load
Reconstruction in Synthetic Power Grids" (Kang, Baembitov, Safdarian, Snodgrass, Overbye).
Objectif immédiat : faire tourner le pipeline complet sur la zone ERCOT Coast (IECC 2A),
régénérer les résultats et figures (sections Validation/Résultats du papier encore vides).
Objectif suivant : re-validation avec split train/test TEMPOREL (limitation connue du papier),
puis extension à d'autres zones climatiques du Texas.

L'utilisateur (Rafaël) : solide Python/ML/stats, débutant ArcGIS. Préfère avancer une étape
à la fois, intuition avant formalisme, pas de code prématuré avant clarification de la logique.

## Pipeline (3 notebooks, ordre : residential -> commercial -> plot_all)

1. **residential.ipynb** (ResStock, 5 archétypes résidentiels)
   - Météo NREL AMY 2018 (S3, par GID PUMA) -> profils ResStock 2A (S3)
   - Agrégation 15min->horaire, normalisation par `units_represented` (kWh/foyer)
   - 5 RandomForest : [temp, humidité, vent, GHI, hour, month, day_of_week] -> kWh/foyer
   - Census B25024 (API, tracts TX) + crosswalk vers 5 archétypes NREL
   - Jointure `tract_to_bus_mapping.csv` (ArcGIS) -> comptages par bus
   - (8760x5) . (5x200 bus) -> `final_bus_load_profiles_8760.csv`
2. **commercial.ipynb** (ComStock, 15 archétypes) — structure miroir
   - Normalisation par `floor_area_represented` (kWh/sqft)
   - CBP/ZBP 2018 (zip census.gov) : employés par NAICS x ZIP (milieux de classes d'effectifs)
   - `get_comstock_type()` : NAICS -> archétype (l'« Industrial » est mis de côté)
   - Facteurs sqft/employé (CBECS) -> `bus_commercial_sqft.csv`
   - Jointure `zcta_to_bus_mapping.csv` -> `final_comstock_bus_load_profiles_8760.csv`
3. **plot_all.ipynb** — validation zone : stack Industriel plat (4500 MW) + Res + Com
   vs ERCOT Coast réel ; stats ; grid search facteurs d'échelle. Génère les figures du papier.

## Fichiers requis dans exports/ (NON produits par le code)
- `Native_Load_2018.xlsx` — ERCOT (obtenu, validé)
- `tl_2018_48_puma10_COAST.csv` — table attributaire PUMA de la zone Coast (export ArcGIS)
- `tract_to_bus_mapping.csv` — jointure spatiale tract -> bus le plus proche (ArcGIS)
- `tl_2018_us_zcta510_COAST_centwithin.csv` — ZCTA de la zone Coast
- `zcta_to_bus_mapping.csv` — jointure spatiale ZCTA -> bus
Tout le reste est auto-téléchargé par le code (NREL S3, Census API, ZBP 2018 ~60 Mo).

## Pièges connus
- **Chemins** : `exports` codé en dur différemment selon les notebooks (machines de Seri et
  Rashid). Unifier en tête de chaque notebook avant toute exécution.
- **Météo** : le code construit ~25 GIDs depuis les codes PUMA ; presque tous font 404,
  seuls G4804610 et G4804630 existent sur S3. Le code utilise ensuite G4804610 seul
  (voulu : une station représentative par zone, cf. papier), mais la boucle est fragile.
- **Colonne cible** : ResStock = `out.electricity.total.energy_consumption..kwh` (double
  point) ; ComStock = `...energy_consumption.kwh` (simple point). Ne pas confondre.
- **Fuseaux horaires** : ResStock/ComStock en EST fixe SANS DST (documenté seulement dans
  les webinaires NREL). ERCOT en Central AVEC DST + heures « 24:00 » + suffixe « DST » sur
  l'heure dupliquée d'automne. Le parsing (cellule ERCOT) gère ça via un masque `ambiguous`
  et une conversion vers 'Etc/GMT+5'. Vérifié sur le vrai fichier : OK, mais 2 petites
  discontinuités d'index subsistent autour des transitions DST (à inspecter, non bloquant).
- **Fuite temporelle** : split train/test ALÉATOIRE (train_test_split) sur une série
  autocorrélée -> R² optimistes. Assumé dans le papier ; la re-validation temporelle est
  l'étape requise n°1 des travaux futurs.
- **Bus à charge nulle** : règle du bus le plus proche -> 6 bus sans aucune assignation
  (résidentiel). Connu et documenté dans le papier.

## Valeurs cibles de reproduction (sorties des notebooks de Seri)
- ResStock R² : mobile_home 0.8488, SF detached 0.9072, SF attached 0.9054,
  MF 2-4 0.9068, MF 5+ 0.9490
- ComStock R² : 0.931 (smallhotel) à 0.982 (fullservicerestaurant) — cf.
  `comstock_training_metrics.csv`
- 200 bus ; comptages ex. bus 7001 : 3438 SF-detached, 44 SF-attached, 154 MF2-4,
  689 MF5+, 798 mobile
- Population estimée : 6 545 533 (2 641 624 logements)
- Pic ERCOT Coast 2018 : 20 269.85 MW ; pic estimé Res 9 625.24 MW ; Com 2 528.56 MW
- Pearson : 0.8733 (Res seul vs ERCOT), 0.8806 (Industriel 4500 MW + Res + Com)
- Grid search : optimum RES_SCALE 1.9, COM_SCALE 1.3, Pearson 0.88179
- ComStock : 404.86 M sqft commercial total ; 773 029 employés commerciaux,
  24 790 industriels mis de côté
- Feature importance ComStock (moyenne) : GHI 46.6%, hour 19.7%, temp 14.7%,
  day_of_week 10.4%

## Environnement
Python 3.11 (les notebooks mentionnent « env1 3.11.13 »).
pandas, numpy, scikit-learn, joblib, matplotlib, seaborn, requests, openpyxl, tzdata.

## Plan de travail
1. Unifier la variable `exports` et vérifier la présence des 5 fichiers manuels.
2. Dérouler residential.ipynb cellule par cellule ; comparer aux valeurs cibles.
3. Idem commercial.ipynb, puis plot_all.ipynb -> figures.
4. Ensuite seulement : split temporel, indicateur jours fériés, industriel data-driven,
   raffinement de l'assignation spatiale (even split / buffer / Voronoi — cf. papier §IV-F),
   extension autres zones climatiques (le code est déjà paramétré par zone_folder/zone_prefix).
