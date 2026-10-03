# Bus-Level Load Reconstruction — Bilan (au 12 août 2026)

Préparé pour la présentation du 13 août avec Farnaz.

## 1. Contexte

Reproduction puis correction du pipeline du papier "A Framework for Weather-Dependent
Bus-Level Load Reconstruction in Synthetic Power Grids" (Kang, Baembitov, Safdarian,
Snodgrass, Overbye), sur la zone ERCOT Coast (200 bus, climat IECC 2A). Objectif : répondre
aux points 5 et 6 des commentaires de relecture de Farnaz avant soumission à IEEE OAJPE
(fin août 2026).

## 2. Chronologie de ce qui a été fait

### Étape 0 — Reproduction du pipeline existant (déjà fait avant cette série de travaux)
Les notebooks `residential.ipynb`, `commercial.ipynb`, `plot_all.ipynb` reproduisent les
résultats du papier à l'identique (R² ResStock/ComStock, pic ERCOT, corrélation Pearson
0,8733/0,8806, grid search RES_SCALE=1,9/COM_SCALE=1,3). Environnement Python réparé
(3.11, dépendances manquantes ajoutées), chemins unifiés en relatif.

### Étape 1 — Fuite temporelle (`temporal_train_test.ipynb`)
- **Problème** : les R² originaux (résidentiel ~0,90, commercial ~0,97) venaient d'un split
  train/test aléatoire sur des données horaires autocorrélées → fuite de données.
- **Diagnostic raté d'abord** : un simple split chronologique 80/20 s'est révélé lui-même
  peu fiable (R² négatifs, mois absents de l'entraînement). L'encodage cyclique seul n'a
  pas suffi à corriger ça.
- **Fix retenu** : CV bloquée par saison (entraîne sur 3 saisons, teste sur la 4ᵉ, tourne).
- **Résultat** : R² honnête résidentiel 0,41 / commercial 0,79. Corrélation ERCOT quasi
  inchangée (0,8819 → 0,8907) malgré la chute des R² par archétype.

### Étape 2 — Métriques de validation (`validation_metrics.ipynb`, point 5)
Coincidence/diversity factor (~0,998, quasi zéro diversité intra-secteur), load duration
curve, forme diurne par semaine/weekend × été/hiver, biais saisonnier mensuel, proxy de
cohérence spatiale (honnêtement caveaté, pas de vérité terrain par bus). Comparaison
Hanyue (point 9) **toujours bloquée**, faute de référence.

### Étape 3 — Bug de géographie météo (`weather_correction.ipynb`)
- **Découverte majeure** : la station météo utilisée depuis le début (`G4804610`) n'est
  pas dans la zone Coast — c'est **Upton County**, à 800 km à l'ouest (climat semi-aride),
  suite à une collision numérique entre code PUMA et FIPS de comté.
- **Fix** : moyenne pondérée par logements sur les 12 vrais comtés de la zone Coast
  (Harris ~67%).
- **Résultat** : R² résidentiel 0,41 → 0,63, commercial 0,79 → 0,86. Corrélation ERCOT
  0,8907 → 0,8987.
- **Découverte annexe** : la sélection PUMA d'origine couvre en fait 21 comtés, mais
  `tract_to_bus_mapping.csv` (le vrai footprint des 200 bus) n'en couvre que 12 — cohérent
  avec la population déjà validée du papier (2,64M logements), donc pas une erreur, mais
  à documenter dans le papier.

### Étape 4 — Comparaison de modèles (`model_comparison.ipynb`, point 6)
- RandomForest vs XGBoost vs LightGBM, mêmes hyperparamètres par défaut, même protocole
  honnête (CV saisonnière, météo corrigée).
- **Précision** : LightGBM gagne (résidentiel 0,73, commercial 0,90), RF perd (0,63/0,86).
- **Vitesse** : XGBoost le plus rapide (0,09s/fit vs 0,33-0,37s).
- **Mais au niveau système** : aucun des trois ne bouge la corrélation ERCOT (~0,898 pour
  les trois) — le choix du modèle compte pour la précision par bâtiment, pas pour la
  validation agrégée.
- LSTM : justification écrite (pas de code), scope tranché avec Rafaël.

### Étape 5 — Feature engineering (`feature_engineering.ipynb`)
Étude par ablation (LightGBM fixe, on isole l'effet des features) :
- Colonnes météo gratuites inutilisées (direction du vent, DNI, DHI) : **n'aide pas**.
- Degree-hours chauffage/climatisation : négligeable.
- **Température décalée (1h, 3h, moyenne 24h)** : gros gain — résidentiel 0,73 → 0,80,
  commercial 0,90 → 0,92. Confirme l'hypothèse d'inertie thermique évoquée pour le LSTM,
  capturée ici à moindre coût.
- Indicateur jour férié : négligeable en plus.
- **Seul changement, avec la météo, à bouger le niveau système** : 0,8979 → 0,9023.
- **C'est la meilleure version du pipeline à ce jour.**

## 3. Inventaire des dossiers et fichiers

| Dossier | Contenu | Origine |
|---|---|---|
| `models/`, `metrics/` | 5 modèles résidentiels originaux (R² ~0,90, split aléatoire) | pipeline original |
| `models_comstock/`, `metrics_comstock/` | 15 modèles commerciaux originaux | pipeline original |
| `models_temporal/`, `metrics_temporal/` | 20 modèles, CV saisonnière, **mauvaise météo** | Étape 1 |
| `models_weather_fixed/`, `metrics_weather_fixed/` | 20 modèles RF, CV saisonnière, **météo corrigée** | Étape 3 |
| `models_xgboost_final/`, `models_lightgbm_final/` | 20 modèles chacun, météo corrigée | Étape 4 |
| `metrics_model_comparison/` | RF vs XGBoost vs LightGBM, résultats CV | Étape 4 |
| `models_feature_engineered/`, `metrics_feature_engineering/` | 20 modèles LightGBM + features enrichies (**meilleure version**) | Étape 5 |
| `weather_county_fixed/` | Météo brute des 12 comtés Coast (téléchargée une fois, réutilisée partout) | Étape 3 |
| `loadcurves/exports/final_*_8760.csv` | Original | pipeline original |
| `loadcurves/exports/final_*_8760_temporal.csv` | Étape 1 | |
| `loadcurves/exports/final_*_8760_weatherfixed.csv` | Étape 3 | |
| `loadcurves/exports/final_*_8760_{xgboost,lightgbm}.csv` | Étape 4 | |
| `loadcurves/exports/final_*_8760_featureeng.csv` | Étape 5, **meilleure version** | |
| `loadcurves/exports/*.csv` (sans suffixe `final_`) | Fichiers manuels ArcGIS + données brutes NREL/Census/ZBP, inchangés depuis le début | |

Chaque étape est dans un dossier séparé, rien n'écrase les versions précédentes — permet
de montrer la progression complète (ablation) dans la présentation.

## 4. Tableau récapitulatif des résultats (le tableau à montrer demain)

| Version | R² résidentiel | R² commercial | Pearson vs ERCOT | Pic estimé (MW) |
|---|---|---|---|---|
| Original (fuite, mauvaise météo) | 0,90 (biaisé) | 0,97 (biaisé) | 0,8819 | 24 418 |
| + split temporel honnête | 0,41 | 0,79 | 0,8907 | 24 604 |
| + météo corrigée | 0,63 | 0,86 | 0,8987 | 26 115 |
| + LightGBM (vs RF) | 0,73 | 0,90 | 0,8979 | 25 735 |
| **+ feature engineering (température décalée)** | **0,80** | **0,92** | **0,9023** | 25 578 |

(ERCOT réel : pic 20 270 MW — le RES_SCALE/COM_SCALE actuel, 1,9/1,3, n'a jamais été
réajusté depuis la météo corrigée, voir section 5.)

## 5. Ce qui N'A PAS encore été fait (important pour demain)

**Deux points promis à Farnaz dans l'email de suivi ne sont pas encore livrés :**
1. **Recalibration RES_SCALE/COM_SCALE** — les facteurs 1,9/1,3 datent du grid search
   original (mauvaise météo, RF, split aléatoire). Le pic estimé dérive de plus en plus
   loin du réel (24 418 → 25 578 MW) à mesure qu'on améliore le reste — signe qu'un
   nouveau grid search est nécessaire, pas encore fait.
2. **Breakdown semaine/weekend du R² résidentiel** — on a un signal indirect (corrélation
   de forme diurne plus faible le weekend d'hiver, 0,77 vs 0,95-0,98 l'été) mais pas encore
   le breakdown propre de la CV saisonnière par semaine/weekend que Farnaz a demandé.

**Autres points ouverts :**
- Référence de la méthode "Hanyue" (point 9) — toujours bloquée, demandée deux fois.
- Extension Texas entier — bloquée sur l'absence d'une liste de bus au-delà des 200 de
  Coast (demandé à Farnaz dans le dernier email).
- Diversité spatiale entre bus quasi nulle (coincidence factor ~0,998) — actuellement les
  200 bus partagent tous la même météo agrégée par zone ; donner à chaque bus la météo de
  son propre comté serait une amélioration possible, pas commencée.
- **Rien n'est commité dans git** — 12 jours de travail, aucun commit. À faire avant
  d'aller plus loin (risque de perte, pas d'historique partageable).

## 6. Recommandation pour la présentation de demain

Montrer la progression du tableau section 4 comme fil conducteur — chaque ligne = une
question de reviewer répondue avec un chiffre. Être transparent sur les deux items
promis non livrés (section 5) plutôt que de laisser Farnaz les découvrir : proposer soit
de les faire en direct/juste après l'appel, soit de les traiter comme prochaine itération.

---

## 7. Mapping statewide refait (2026-09-21) — les deux nouveaux exports ArcGIS

Deux fichiers déposés à la racine débloquent l'extension Texas entier et remplacent
l'ancien `bus_to_zone_full.csv` (un tract → un seul bus le plus proche).

### `texas7k_bus_with_climate_zone.csv` — table de bus faisant autorité
6 717 bus du Texas 7k avec lat/lon sous-station, `Nom_kV`, le `Load_MW`/`Gen_MW` du cas,
le `COUNTYFP`, la zone IECC, et surtout **`Area_Name` = la zone météo ERCOT du bus**.
- La zone IECC du fichier est d'accord à **100 %** avec le crosswalk comté→zone dérivé de
  NREL (`spatial_tract_lookup_table.csv`) : deux géographies indépendantes se confirment.
- Plus de vote majoritaire pour déduire la zone d'un bus, plus de bus manquants (avant :
  seuls les 3 426 bus ayant « gagné » un tract existaient).
- `Load_MW` donne une référence par bus pour la calibration.
- `Area_Name` remplace le crosswalk comté→zone ERCOT lu à l'œil sur le PNG d'ERCOT.

### `tract_to_bus_mapping_statewide1.csv` — répartition surfacique tract → bus
Chaque tract 2020 est **découpé en 50 morceaux d'aire égale** (vérifié : les 50 `Shape_Area`
d'un tract sont égales à 1e-6 près et somment à `ALAND`), chaque morceau joint à son bus le
plus proche. D'où `poids(tract, bus) = morceaux gagnés / 50`, par pas de 2 %.
C'est exactement le raffinement d'assignation spatiale listé en travaux futurs du papier
(§IV-F) : fin de la règle « le gagnant prend tout ».
- 6 896 tracts → 6 359 bus, 24 499 paires, 3,55 bus/tract en moyenne (max 29).
- **84 % des tracts** sont désormais répartis sur plusieurs bus.
- 4 518 / 4 541 bus porteurs de charge dans le cas sont atteints (contre 3 426 bus au total avant).
- **100 % des logements du Texas conservés** (11 628 419), 6 352 / 6 717 bus reçoivent du
  résidentiel ; il ne reste que **25 bus porteurs de charge à zéro logement** (contre 6/200
  dans le papier Coast, proportionnellement bien meilleur).
- Réserve à écrire dans le papier : le découpage est **équi-surface**, donc il suppose les
  logements uniformément répartis dans le tract. Hypothèse faible sur un grand tract rural
  avec une seule ville, quasi inoffensive en zone urbaine dense — où est la charge.

### Ce qui a changé dans le code
- `00_zone_mapping.ipynb` — réécrit : produit `bus_zone_master.csv`, `tract_bus_weights.csv`,
  `bus_building_counts_statewide.csv`, `zone_county_weather_weights.csv` (maintenant pondérés
  par les logements réellement alloués à la zone), `zcta_to_zone.csv` (zone lue directement
  sur le bus, plus de repli KD-tree).
- Les 5 `residential_{ZONE}.ipynb` — l'allocation des logements est une somme pondérée par
  les poids surfaciques. Ré-exécutés : les 5 exports 8760 sont régénérés.
- `ercot_zone_validation.ipynb` — **réécrit** : la validation passait de la seule zone 3B
  (crosswalk comté lu sur une image) aux **8 zones météo ERCOT**, agrégées par `Area_Name`.
- Les 5 `commercial_{ZONE}.ipynb` et `statewide_summary.ipynb` lisent `bus_zone_master.csv`.
  Le commercial reste en « bus le plus proche » : il n'existe pas encore de découpage en 50
  morceaux pour les ZCTA — **c'est le prochain export ArcGIS à demander**.

### Nouveau résultat de validation (non calibré, sans modèle industriel hors Coast)
| Zone ERCOT | Pearson | couverture du pic |
|---|---|---|
| ERCOT (total) | **0,922** | 67 % |
| COAST | 0,900 | 65 % |
| NCENT | 0,900 | 64 % |
| SOUTH | 0,908 | 65 % |
| SCENT | 0,886 | 64 % |
| WEST | 0,813 | 43 % |
| FWEST | 0,629 | 63 % |
| EAST / NORTH | 0,911 / 0,905 | *frontières non concordantes, magnitude non comparable* |

Le creux WEST/FWEST confirme, plus précisément que l'ancienne approximation par comté
(r = 0,71 sur 3B), l'hypothèse « charge industrielle pétrolière non pilotée par la météo ».
Sur les 12 comtés Coast d'origine, la nouvelle chaîne corrèle à **r = 0,9965** avec le
pipeline Coast 200 bus déjà validé — les deux méthodes indépendantes donnent la même forme.
