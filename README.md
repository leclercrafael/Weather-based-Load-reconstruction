# Bus-Level Load Reconstruction — Statewide Texas

Reconstructs hourly electricity load at every bus of the **Texas 7k synthetic grid** from
weather, NREL building-stock simulations and Census data — then validates it against ERCOT's
published 2018 load.

Extends the framework of Kang, Baembitov, Safdarian, Snodgrass & Overbye from the ERCOT Coast
case study (200 buses) to the whole state (6,717 buses, 5 climate zones, all 8 ERCOT weather
zones).

![Reconstruction vs ERCOT actual, all eight weather zones](latex_report/figures/ercot_8zone_fig1.png)

| | Reconstruction | ERCOT actual |
|---|---|---|
| Statewide peak | 72,617 MW | 73,308 MW |
| Load factor | 0.592 | 0.586 |
| Pearson *r* | **0.922** | — |
| Fitted industrial load | 18,079 MW (24.7% of peak) | — |

---

## Start here

| | |
|---|---|
| **[`statewide_results_summary.pdf`](latex_report/statewide_results_summary.pdf)** | 9 pp. — results and figures, written to be written from |
| [`report.pdf`](latex_report/report.pdf) | 33 pp. — full record: every bug, every pipeline version, every audit |
| [`CLAUDE.md`](CLAUDE.md) | project context and reproduction targets |

## Run it

```bash
uv sync                                  # Python 3.11, deps pinned in uv.lock
echo "YOUR_CENSUS_API_KEY" > census_api_key.txt     # git-ignored
jupyter lab statewide/notebooks/
```

Execute in this order. Everything not listed as an input is downloaded or rebuilt automatically
(~5 GB of NREL archetypes and AMY weather on first run).

| Step | Notebook | Produces |
|---|---|---|
| 1 | `00_zone_mapping` | every mapping table the rest depends on |
| 2 | `residential_{2A,2B,3A,3B,4B}` | 5 ResStock archetypes → bus profiles |
| 3 | `commercial_{2A,2B,3A,3B,4B}` | 15 ComStock archetypes → bus profiles |
| 4 | `zone_calibration` | per-zone RES/COM scales + fitted industrial constant |
| 5 | `ercot_zone_validation` | validation against all 8 ERCOT weather zones |
| 6 | `validation_metrics_statewide` | LDC, diurnal shape, monthly bias, coincidence factor |
| 7 | `statewide_summary` | cross-zone comparison, cross-check vs. the Coast pipeline |

Steps 2 and 3 are independent; either order. Step 1 is the only one needing the large inputs
below.

Rebuild the PDFs with `cd latex_report && tectonic report.tex && tectonic
statewide_results_summary.tex`.

## Repository map

| Path | What |
|---|---|
| `statewide/notebooks/` | the pipeline above |
| `statewide/*.csv` | mapping tables from step 1 — bus→zone, tract→bus weights, ZCTA→bus weights, archetype counts per bus |
| `statewide/metrics/` | every number in both PDFs, as CSV |
| `latex_report/` | both reports, their sources, and `figures/` |
| `*.ipynb` (root) | the original Coast-only study and the methodology notebooks behind `report.pdf` — superseded, kept for provenance |
| `metrics*/` (root) | Coast-study metrics |

Not committed, because running the notebooks rebuilds it: trained models, the 8760 × N bus
profile CSVs (~1.9 GB), NREL downloads, TIGER shapefiles, the ArcGIS project. See `.gitignore`.

## Data you must supply

Manual exports; nothing regenerates them.

```
texas7k_bus_with_climate_zone.csv        # 6,717 buses: lat/lon, kV, case Load_MW/Gen_MW,
                                         #   county, IECC zone, ERCOT Area_Name
loadcurves/exports/
  Native_Load_2018.xlsx                  # ERCOT actual load by weather zone
  tract_to_bus_mapping.csv               # Coast-only tract → bus
  zcta_bus_mapping_tx_final.csv          # statewide ZCTA → nearest bus
  tl_2018_48_puma10_COAST.csv            # Coast PUMA attribute table
  tl_2018_us_zcta510_COAST_centwithin.csv
```

**Two more exceed GitHub's 100 MB file limit and are not in this repo:**

| File | Size | Contents |
|---|---|---|
| `tract_to_bus_mapping_statewide1.csv` | 118 MB | each 2020 tract cut into 50 equal-area parts, each part joined to its nearest bus |
| `zcta_to_bus_mapping_statewide_tracts_subdivided100.csv` | 53 MB | same for 2010 ZCTAs, 100 parts each |

Their content *is* committed, aggregated, as `statewide/tract_bus_weights.csv` and
`statewide/zcta_bus_weights.csv` (`weight = parts won / total parts`) — which is what every
notebook after step 1 actually reads. Keep the raw files backed up elsewhere and drop them at the
repository root only to re-run step 1.

## Gotchas

- **Target columns differ.** ResStock: `out.electricity.total.energy_consumption..kwh` (two
  dots). ComStock: `...energy_consumption.kwh` (one). Not interchangeable.
- **Time zones.** ResStock/ComStock are fixed EST, no DST. ERCOT is Central *with* DST, uses
  `24:00` hour endings, and suffixes the duplicated autumn hour `DST`. The parsing cell handles
  this with an `ambiguous` mask and conversion to `Etc/GMT+5` — don't simplify it.
- **Census tract vintage.** The statewide mapping is on 2020 boundaries and needs the
  2020-vintage B25024 file; the Coast files are on 2010 boundaries. Mixing them silently drops
  ~40% of buses.
- **ERCOT EAST and NORTH.** The synthetic case's area boundaries don't match ERCOT's there (case
  peak is 1.33× and 2.21× the zonal peak). Shape statistics are usable; magnitudes are not.

## Known limits

Industrial load is a *fitted constant*, not a model — it can't reproduce industrial load's own
temporal variation, which caps FAR WEST at *r* = 0.655 where that constant is 61% of zonal peak.
ERCOT South Central fits a null commercial coefficient that is still unexplained after coverage
and collinearity were tested and ruled out. All buses within a zone share one weather series,
which is why within-zone coincidence factors stay near 1.

Full list with numbers to hit: `statewide_results_summary.pdf` §6.
