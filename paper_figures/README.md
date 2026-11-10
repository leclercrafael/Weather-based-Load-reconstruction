# Paper figures — ERCOT Coast

Eight figures for the Coast paper, regenerated from the current-best pipeline
(LightGBM, feature set E, population-weighted county weather: the `_featureeng`
outputs) and the metric CSVs. They replace the notebook figures in
`latex_report/figures/`, which carry in-figure titles, raw labels, screen sizing and
superseded pipeline versions.

- `pdf/` — vector, fonts embedded (Type 42), for `\includegraphics` in LaTeX.
- `png/` — 300 dpi, for previews or Word.
- `make_figures.py` — the single script that builds all eight.

```bash
DATA_ROOT=/path/to/tamu_project uv run python paper_figures/make_figures.py
```

`DATA_ROOT` defaults to the repo root. The large CSVs are git-ignored, so it must point
at a checkout where the notebooks have been run.

**Style.** IEEEtran sizes (single column 3.5 in, double 7.16 in), 8 pt Times, no
in-figure titles (the caption carries them), ERCOT always in black. Colors come from a
colorblind-validated set (blue / orange / aqua), and each series also differs by line
style or marker, so the figures survive grayscale printing.

**Calibration.** Figures with a calibrated stack use Eq. (4) with αR = 1.6,
αC = 1.3, P_ind = 4,500 MW (Table III of the current draft). These are three constants
at the top of the script. If the calibration changes (e.g. a least-squares fit), edit
them and re-run.

---

## Suggested use

| # | File | Width | Where in the paper | Priority |
|---|------|-------|--------------------|----------|
| 1 | `fig_timeseries_vs_ercot` | double | §V-C, comparison with ERCOT | **high** |
| 2 | `fig_diurnal_shapes` | single | §V-C, shape metrics | **high** |
| 3 | `fig_monthly_sector_stack` | single | §V-C, sector calibration | **high** |
| 4 | `fig_bus_map` | single | §IV-D or §V, bus-level output | **high** |
| 5 | `fig_model_comparison_r2` | single | §V-A, Table I | medium |
| 6 | `fig_feature_ablation_r2` | single | §V-A, Table II | medium |
| 7 | `fig_load_duration_curve` | single | §V-C, shape metrics | medium |
| 8 | `fig_bus_shape_diversity` | single | §V-C or §VI, limitation | optional |

A 5-page limit will not hold all eight. The four "high" ones are what the draft lacks
most: it currently has no results figure, and nothing shows the bus-level output itself.

---

## Draft captions

**1 — `fig_timeseries_vs_ercot`**
> Reconstructed Coast-zone load (calibrated, Eq. (4)) versus ERCOT reported load, 2018.
> (a) Daily means over the year; hourly Pearson r = 0.902. (b) A summer week and (c) a
> winter week at hourly resolution. The winter week includes the mid-January cold snap,
> where the reconstruction overshoots.

**2 — `fig_diurnal_shapes`**
> Average diurnal profile by season (summer: Jun–Aug, winter: Dec–Feb) and day type,
> ERCOT versus reconstruction. r is the correlation of the 24-hour profiles.

**3 — `fig_monthly_sector_stack`**
> Monthly mean load by sector after calibration (flat industrial term, residential
> ×1.6, commercial ×1.3) against ERCOT's monthly mean.

**4 — `fig_bus_map`**
> Annual energy of the 204 load-carrying buses (marker area) and commercial share of
> that energy (color; scale capped at 60 %). Gray dots are census-tract centroids. Bus
> energies are unscaled model outputs.

**5 — `fig_model_comparison_r2`**
> Blocked seasonal cross-validation R² per archetype for the three model classes
> (baseline features). †: archetype that receives no or negligible floor area from the
> NAICS mapping in this zone.

**6 — `fig_feature_ablation_r2`**
> Per-archetype R² of LightGBM with the baseline features (set A) and the final features
> (set E: lagged and rolling temperature, holiday). † as in Fig. 5.

**7 — `fig_load_duration_curve`**
> Load duration curves of ERCOT, the calibrated reconstruction, and the unscaled
> residential-plus-commercial load. LF: load factor (mean/peak).

**8 — `fig_bus_shape_diversity`**
> Normalized summer-weekday profile of every load bus (gray). Highlighted: a purely
> residential bus and a bus with about half commercial energy. Because every bus shares
> one weather series, shapes differ only through the archetype mix.

---

## Things to fix in the text when inserting these

1. **Diurnal correlations.** The draft's §V-C quotes 0.980 / 0.961 / 0.915 / 0.798,
   computed with the earlier factors (1.9, 1.3). With the (1.6, 1.3) of Table III, which
   Fig. 2 uses, they are **0.979 / 0.959 / 0.922 / 0.797**. Update the text, the
   abstract's "three of four above 0.91" still holds.
2. **Monthly bias** (Fig. 3, model / ERCOT − 1): Jan +17 %, Feb +10 %, Mar +4 %,
   Apr +7 %, May +1 %, Jun–Aug +2 to +3 %, Sep +10 %, Oct +9 %, Nov–Dec +8 %. Summer fits
   well; winter and shoulder months are overestimated. This matches the winter-weekend
   weakness and the January overshoot in Fig. 1(c), and could replace the vaguer
   load-duration sentence.
3. **Bus count.** 204 buses carry load: the 200 with residential load, plus 4 that only
   receive commercial floor area (3 more commercial columns are all-zero). The draft says
   200 throughout.
4. **† archetypes.** Four commercial archetypes get no or negligible floor area: large
   office, retail strip mall, secondary school (0 sq ft) and small hotel (0.01 M sq ft).
   The NAICS rules never map to large office or strip mall at all. The draft only
   mentions the secondary school.
5. **Calibration.** Pearson only identifies αR/αC (see the review notes). If the
   paper switches to a least-squares fit, Figs. 1, 2, 3 and 7 change: re-run the script
   with the new constants.
