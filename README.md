# Weather-Dependent Bus-Level Load Reconstruction — Texas

Reconstructs hourly, bus-level electricity load for the **Texas 7k synthetic grid** (6,717 buses)
from weather, NREL building-stock simulations and Census data, and validates it against ERCOT's
published 2018 load for all eight ERCOT weather zones.

Extends the framework of Kang, Baembitov, Safdarian, Snodgrass & Overbye from the single ERCOT
Coast case study (200 buses) to the whole state.

**Headline result:** statewide Pearson *r* = 0.922 against ERCOT actual load, calibrated peak
within 1% of the true system peak, load factor 0.592 vs. 0.586 actual.

---

## Read this first

| You want | Open |
|---|---|
| The results, condensed for writing the paper (9 pp.) | [`latex_report/statewide_results_summary.pdf`](latex_report/statewide_results_summary.pdf) |
| The full record: every bug, every pipeline version, every audit (33 pp.) | [`latex_report/report.pdf`](latex_report/report.pdf) |
| Project context, pitfalls, target values | [`CLAUDE.md`](CLAUDE.md) |

---

## Repository layout

### Code — run in this order

```
statewide/notebooks/
  00_zone_mapping.ipynb            # FIRST. Builds every mapping table the rest depends on.
  residential_{2A,2B,3A,3B,4B}.ipynb   # 5 ResStock archetypes per zone  -> bus profiles
  commercial_{2A,2B,3A,3B,4B}.ipynb    # 15 ComStock archetypes per zone -> bus profiles
  zone_calibration.ipynb           # per-ERCOT-zone RES/COM scales + fitted industrial constant
  ercot_zone_validation.ipynb      # validation against all 8 ERCOT weather zones
  validation_metrics_statewide.ipynb   # LDC, diurnal, monthly bias, coincidence factor, …
  statewide_summary.ipynb          # cross-zone comparison + cross-check vs the Coast pipeline
```

The residential and commercial notebooks are independent of each other; either order works.
Everything after them needs both.

The original **Coast-only** study lives at the repository root (`residential.ipynb`,
`commercial.ipynb`, `plot_all.ipynb`) together with the methodology notebooks it produced:
`temporal_train_test`, `weather_correction`, `model_comparison`, `feature_engineering`,
`validation_metrics_full_comparison`. These are kept because `report.pdf` documents them; the
statewide pipeline supersedes them.

### Inputs that are **not** reproducible from code

These are manual ArcGIS/portal exports. Without them nothing runs.

```
texas7k_bus_with_climate_zone.csv          # 6,717 buses: lat/lon, kV, case Load_MW/Gen_MW,
                                           #   county FIPS, IECC zone, ERCOT Area_Name
loadcurves/exports/
  Native_Load_2018.xlsx                    # ERCOT actual load by weather zone, 2018
  tract_to_bus_mapping.csv                 # Coast-only tract -> bus (original 200-bus study)
  zcta_bus_mapping_tx_final.csv            # statewide ZCTA -> nearest bus
  tl_2018_48_puma10_COAST.csv              # Coast PUMA attribute table
  tl_2018_us_zcta510_COAST_centwithin.csv  # Coast ZCTA attribute table
```

Two further ArcGIS exports are **too large for GitHub** and are therefore *not* in the repo:

| File | Size | What it is |
|---|---|---|
| `tract_to_bus_mapping_statewide1.csv` | 118 MB | each 2020 tract cut into 50 equal-area parts, each part joined to its nearest bus |
| `zcta_to_bus_mapping_statewide_tracts_subdivided100.csv` | 53 MB | the same for 2010 ZCTAs, 100 parts each |

Their information is committed in aggregated form as `statewide/tract_bus_weights.csv` and
`statewide/zcta_bus_weights.csv` (`weight = parts won / total parts`), which is what every
downstream notebook actually reads. **Only `00_zone_mapping.ipynb` needs the raw files** — keep
them backed up outside git and drop them at the repository root to re-run that notebook from
scratch.

### Mapping tables (committed, produced by `00_zone_mapping.ipynb`)

```
statewide/
  bus_zone_master.csv                 # 6,717 buses x (IECC zone, county, lat/lon, kV, Load_MW,
                                      #   Gen_MW, ERCOT Area_Name) — the authoritative bus table
  tract_bus_weights.csv               # (GEOID, Bus_Number, weight)  6,896 tracts -> 6,359 buses
  zcta_bus_weights.csv                # (ZCTA5CE10, Bus_Number, weight)  1,933 ZCTAs -> 6,329 buses
  bus_building_counts_statewide.csv   # 5 ResStock archetype counts per bus (fractional)
  county_to_iecc_zone.csv             # 254 TX counties -> IECC zone (derived from NREL's own table)
  zone_county_weather_weights.csv     # housing-weighted county weights per zone
  zcta_to_zone.csv                    # majority-weight zone label per ZCTA
```

### Results (committed)

```
statewide/metrics/     seasonal_cv_{ZONE}.csv, seasonal_cv_comstock_{ZONE}.csv,
                       zone_calibration.csv, ercot_zone_validation_all.csv,
                       statewide_validation_summary.csv, statewide_coincidence_diversity.csv,
                       statewide_monthly_bias.csv, statewide_diurnal_corr.csv,
                       statewide_spatial_proxy.csv
metrics*/              Coast-study metrics (training, temporal CV, weather fix, model
                       comparison, feature ablation)
latex_report/          report.tex, statewide_results_summary.tex, both PDFs, figures/
```

Every table in either PDF is backed by one of these CSVs.

### Not committed — regenerated or auto-downloaded

Trained models (`models*/`, `statewide/models/`), the 8760 × N bus profile CSVs
(`statewide/exports/*_8760_*.csv`, ~1.9 GB), NREL ResStock/ComStock archetype profiles and AMY
weather files, TIGER/Line shapefiles, and the ArcGIS project (`ClimateZones/`, `*.gdb`).
Running the notebooks re-downloads and rebuilds all of it. See `.gitignore`.

---

## Setup

Python 3.11. Dependencies are pinned in `pyproject.toml` / `uv.lock`:

```bash
uv sync
```

`pandas`, `numpy`, `scikit-learn`, `lightgbm`, `xgboost`, `joblib`, `matplotlib`, `seaborn`,
`requests`, `openpyxl`, `scipy`, `tzdata`.

A **Census API key** is needed for the B25024 housing-unit pull. Put it in `census_api_key.txt`
at the repository root (git-ignored) or export `CENSUS_API_KEY`.

Building the PDFs:

```bash
cd latex_report && tectonic report.tex && tectonic statewide_results_summary.tex
```

---

## Things that will bite you

- **Target column names differ between datasets.** ResStock uses
  `out.electricity.total.energy_consumption..kwh` (two dots), ComStock uses
  `...energy_consumption.kwh` (one). They are not interchangeable.
- **Time zones.** ResStock/ComStock are fixed EST with no DST. ERCOT is Central *with* DST, uses
  `24:00` hour endings, and suffixes the duplicated autumn hour with `DST`. The parsing cell
  handles this via an `ambiguous` mask and conversion to `Etc/GMT+5`; don't simplify it.
- **Census tract vintage.** The statewide mapping is on 2020 tract boundaries, so it needs
  `census_b25024_state_48_tracts_2020vintage.csv` (ACS5 2022). The Coast-only files are on 2010
  boundaries. Mixing them silently drops ~40% of buses.
- **ERCOT EAST and NORTH.** The synthetic case's area boundaries do not match ERCOT's for these
  two zones (case peak load is 1.33× and 2.21× the ERCOT zonal peak). Their shape statistics are
  usable; their magnitudes are not.

---

## Open work

Listed with numbers to hit in `latex_report/statewide_results_summary.pdf`, §6. In short: a
time-varying industrial model (the fitted constant is 24.7% of system peak and caps FWEST at
*r* = 0.655); per-bus rather than per-zone weather; the unexplained null commercial coefficient in
ERCOT South Central; and diagnosing the EAST/NORTH boundary mismatch.
