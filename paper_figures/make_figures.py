"""Paper-ready figures for the ERCOT Coast paper.

Regenerates every figure from the current-best pipeline outputs (LightGBM, feature set E,
population-weighted county weather: the `_featureeng` files) and the metric CSVs.

Usage (from anywhere):
    DATA_ROOT=/path/to/tamu_project uv run python paper_figures/make_figures.py

DATA_ROOT defaults to the repository root (the parent of this folder). The large CSVs it
reads are git-ignored, so point DATA_ROOT at a checkout where the notebooks have been run.

Output: paper_figures/pdf/*.pdf (vector, for LaTeX) and paper_figures/png/*.png (300 dpi).
Sizes follow IEEEtran: single column 3.5 in, double column 7.16 in, 8 pt Times-like text.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("DATA_ROOT", HERE.parent)).resolve()
EXP = ROOT / "loadcurves" / "exports"
OUT_PDF, OUT_PNG = HERE / "pdf", HERE / "png"
OUT_PDF.mkdir(exist_ok=True)
OUT_PNG.mkdir(exist_ok=True)

# ---------------------------------------------------------------- calibration (Eq. 4)
# Matches Table III of the current draft. Pearson only identifies the ratio RES/COM, so
# the levels are a choice: change these three numbers if the paper's calibration changes.
RES_SCALE, COM_SCALE, IND_MW = 1.6, 1.3, 4500.0

# ---------------------------------------------------------------- style
SINGLE, DOUBLE = 3.5, 7.16
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#b8b7b2", "#e8e7e3"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"  # validated categorical slots 1-3
IND_GRAY = "#c9c8c3"  # the industrial term is a flat placeholder, so it stays neutral
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": INK2, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.axisbelow": True, "legend.frameon": False,
    "lines.linewidth": 1.0, "figure.dpi": 150,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42, "ps.fonttype": 42,  # embed TrueType: IEEE PDF eXpress requirement
})

RES_TYPES = ["single-family_detached", "single-family_attached", "mobile_home",
             "multi-family_with_2_-_4_units", "multi-family_with_5plus_units"]
COM_TYPES = ["smalloffice", "mediumoffice", "largeoffice", "retailstandalone",
             "retailstripmall", "grocery", "primaryschool", "secondaryschool", "outpatient",
             "hospital", "smallhotel", "largehotel", "quickservicerestaurant",
             "fullservicerestaurant", "warehouse"]
NICE = {
    "single-family_detached": "SF detached", "single-family_attached": "SF attached",
    "mobile_home": "Mobile home", "multi-family_with_2_-_4_units": "MF 2–4 units",
    "multi-family_with_5plus_units": "MF 5+ units",
    "smalloffice": "Small office", "mediumoffice": "Medium office",
    "largeoffice": "Large office", "retailstandalone": "Retail standalone",
    "retailstripmall": "Retail strip mall", "grocery": "Grocery",
    "primaryschool": "Primary school", "secondaryschool": "Secondary school",
    "outpatient": "Outpatient", "hospital": "Hospital", "smallhotel": "Small hotel",
    "largehotel": "Large hotel", "quickservicerestaurant": "Quick-service rest.",
    "fullservicerestaurant": "Full-service rest.", "warehouse": "Warehouse",
}


def save(fig, name):
    fig.savefig(OUT_PDF / f"{name}.pdf")
    fig.savefig(OUT_PNG / f"{name}.png")
    plt.close(fig)
    print(f"  wrote {name}.pdf / .png")


def panel_tag(ax, tag):
    ax.text(0.0, 1.02, tag, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8, fontweight="bold", color=INK)


def thousands(ax, axis="y"):
    fmt = mpl.ticker.FuncFormatter(lambda v, _: f"{v / 1000:g}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


# ---------------------------------------------------------------- data
def load_ercot():
    df = pd.read_excel(EXP / "Native_Load_2018.xlsx", sheet_name="Native Load Report")
    he = df["HourEnding"].astype(str)
    is_dst = he.str.contains(" DST", regex=False)
    he = he.str.replace(" DST", "", regex=False)
    m24 = he.str.contains("24:00")
    ts = pd.to_datetime(he.str.replace("24:00", "00:00"))
    ts.loc[m24] += pd.Timedelta(days=1)
    df["dt"] = ts.dt.tz_localize("US/Central", ambiguous=is_dst, nonexistent="shift_forward")
    s = df.set_index("dt").tz_convert("Etc/GMT+5")["COAST"]  # NREL clock: EST, no DST
    s.index = s.index.tz_localize(None)
    return s[~s.index.duplicated()]


print(f"Reading data from {ROOT}")
ercot = load_ercot()
res_bus = pd.read_csv(EXP / "final_bus_load_profiles_8760_featureeng.csv",
                      index_col=0, parse_dates=True)
com_bus = pd.read_csv(EXP / "final_comstock_bus_load_profiles_8760_featureeng.csv",
                      index_col=0, parse_dates=True)
res_bus.columns = res_bus.columns.astype(int)
com_bus.columns = com_bus.columns.astype(int)

idx = ercot.index.intersection(res_bus.index)
y = ercot.loc[idx]
R = res_bus.sum(axis=1).loc[idx] / 1000  # kWh per hour -> MW
C = com_bus.sum(axis=1).loc[idx] / 1000
Rs, Cs = RES_SCALE * R, COM_SCALE * C
stack = IND_MW + Rs + Cs
print(f"  {len(idx)} common hours; Pearson (calibrated) = {y.corr(stack):.4f}; "
      f"peak ERCOT {y.max():,.0f} MW vs model {stack.max():,.0f} MW")

# ================================================================ Fig: time series
def fig_timeseries():
    fig = plt.figure(figsize=(DOUBLE, 3.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], hspace=0.55, wspace=0.18)
    ax = fig.add_subplot(gs[0, :])
    yd, sd = y.resample("D").mean(), stack.resample("D").mean()
    ax.plot(yd.index, yd.values, color=INK, lw=1.0, label="ERCOT Coast (reported)")
    ax.plot(sd.index, sd.values, color=BLUE, lw=1.0, label="Reconstruction (calibrated)")
    ax.set_ylabel("Daily mean load (GW)")
    thousands(ax)
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
    ax.xaxis.set_major_formatter(mpl.dates.DateFormatter("%b"))
    ax.set_xlim(yd.index[0], yd.index[-1])
    ax.legend(loc="upper left", ncol=2)
    ax.text(0.995, 0.97, f"hourly $r$ = {y.corr(stack):.3f}", transform=ax.transAxes,
            ha="right", va="top", color=INK2)
    panel_tag(ax, "(a)")

    weeks = [("2018-07-16", "(b) Summer week, 16–22 Jul 2018"),
             ("2018-01-15", "(c) Winter week, 15–21 Jan 2018")]
    for k, (start, title) in enumerate(weeks):
        a = fig.add_subplot(gs[1, k])
        sl = slice(pd.Timestamp(start), pd.Timestamp(start) + pd.Timedelta(days=7))
        a.plot(y.loc[sl].index, y.loc[sl].values, color=INK, lw=1.0)
        a.plot(stack.loc[sl].index, stack.loc[sl].values, color=BLUE, lw=1.0)
        a.set_ylabel("Load (GW)" if k == 0 else "")
        thousands(a)
        a.xaxis.set_major_locator(mpl.dates.DayLocator())
        a.xaxis.set_major_formatter(mpl.dates.DateFormatter("%a"))
        a.text(0.0, 1.02, title, transform=a.transAxes, ha="left", va="bottom",
               fontweight="bold", color=INK)
    save(fig, "fig_timeseries_vs_ercot")


# ================================================================ Fig: diurnal shapes
def hour_beginning(series):
    """NREL and ERCOT stamps are hour-ending (01:00 = 00:00-01:00). Shift by one hour so
    that the hour, weekday and season of each value are those of the interval itself."""
    s = series.copy()
    s.index = s.index - pd.Timedelta(hours=1)
    return s


def diurnal(series, weekday, summer):
    s = hour_beginning(series)
    i = s.index
    season = i.month.isin([6, 7, 8]) if summer else i.month.isin([12, 1, 2])
    day = (i.dayofweek < 5) if weekday else (i.dayofweek >= 5)
    sub = s[season & day]
    return sub.groupby(sub.index.hour).mean()


def fig_diurnal():
    fig, axes = plt.subplots(2, 2, figsize=(SINGLE, 2.9), sharex=True)
    cfg = [(True, True, "Summer weekday"), (False, True, "Summer weekend"),
           (True, False, "Winter weekday"), (False, False, "Winter weekend")]
    rows = []
    for ax, (wd, sm, title) in zip(axes.flat, cfg):
        a, m = diurnal(y, wd, sm), diurnal(stack, wd, sm)
        r = a.corr(m)
        rows.append((title, r))
        ax.plot(a.index, a.values, color=INK, lw=1.0, label="ERCOT")
        ax.plot(m.index, m.values, color=BLUE, lw=1.0, label="Reconstruction")
        ax.set_title(f"{title}   $r$ = {r:.3f}", loc="left", color=INK)
        thousands(ax)
        ax.set_xticks(range(0, 25, 6))
        ax.set_xlim(0, 23)
    for ax in axes[1]:
        ax.set_xlabel("Hour (EST)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Load (GW)")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(pad=0.3, h_pad=0.6, w_pad=0.6, rect=(0, 0, 1, 0.94))
    save(fig, "fig_diurnal_shapes")
    return rows


# ================================================================ Fig: load duration curve
def fig_ldc():
    fig, ax = plt.subplots(figsize=(SINGLE, 2.2))
    pct = np.arange(1, len(y) + 1) / len(y) * 100
    lf = lambda s: s.mean() / s.max()
    ax.plot(pct, np.sort(y.values)[::-1], color=INK, lw=1.1,
            label=f"ERCOT Coast (LF {lf(y):.2f})")
    ax.plot(pct, np.sort(stack.values)[::-1], color=BLUE, lw=1.1,
            label=f"Reconstruction, calibrated (LF {lf(stack):.2f})")
    ax.plot(pct, np.sort((R + C).values)[::-1], color=ORANGE, lw=1.1, ls=(0, (4, 2)),
            label=f"Res. + com., unscaled (LF {lf(R + C):.2f})")
    ax.set_xlabel("Share of hours load is exceeded (%)")
    ax.set_ylabel("Load (GW)")
    thousands(ax)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, None)
    ax.legend(loc="lower left")
    fig.tight_layout(pad=0.3)
    save(fig, "fig_load_duration_curve")


# ================================================================ Fig: monthly sector stack
def fig_monthly():
    m = lambda s: s.groupby(s.index.month).mean()
    ind, res, com, act = np.full(12, IND_MW), m(Rs).values, m(Cs).values, m(y).values
    x = np.arange(1, 13)
    fig, ax = plt.subplots(figsize=(SINGLE, 2.3))
    w = 0.72
    kw = dict(width=w, edgecolor="white", linewidth=0.8)  # white gap between stacked fills
    ax.bar(x, ind, color=IND_GRAY, label=f"Industrial (flat {IND_MW / 1000:g} GW)", **kw)
    ax.bar(x, res, bottom=ind, color=BLUE, label=f"Residential (×{RES_SCALE:g})", **kw)
    ax.bar(x, com, bottom=ind + res, color=ORANGE, label=f"Commercial (×{COM_SCALE:g})", **kw)
    ax.plot(x, act, color=INK, marker="o", ms=3.2, lw=1.0, label="ERCOT Coast",
            markeredgecolor="white", markeredgewidth=0.6, zorder=5)
    ax.set_xticks(x, ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_xlim(0.4, 12.6)
    ax.set_ylabel("Monthly mean load (GW)")
    thousands(ax)
    ax.grid(axis="x", visible=False)
    h, l = ax.get_legend_handles_labels()
    order = [3, 2, 1, 0]  # ERCOT first, then the stack top-down, matching the bars
    ax.legend([h[i] for i in order], [l[i] for i in order], loc="upper left",
              ncol=2, columnspacing=1.0, handlelength=1.2)
    ax.set_ylim(0, max((ind + res + com).max(), act.max()) * 1.32)
    fig.tight_layout(pad=0.3)
    save(fig, "fig_monthly_sector_stack")
    return pd.DataFrame({"ERCOT": act, "Model": ind + res + com}, index=x)


# ================================================================ Fig: model comparison
def archetype_order(values):
    """Residential block then commercial block, each sorted by the given values (desc)."""
    r = sorted(RES_TYPES, key=lambda b: -values[b])
    c = sorted(COM_TYPES, key=lambda b: -values[b])
    return r, c


def zero_area_types():
    sq = pd.read_csv(EXP / "bus_commercial_sqft.csv", index_col=0).sum()
    return set(sq[sq < 0.001 * sq.sum()].index)  # < 0.1 % of zone floor area


def dot_rows(ax, blocks, series, xlabel, empty=()):
    """Horizontal dot plot. blocks = [(label, [archetypes])]; series = [(name, dict, color, marker)]."""
    ylab, ypos, yy = [], [], 0
    seps = []
    for bi, (blabel, types) in enumerate(blocks):
        if bi:
            yy += 0.8
            seps.append(yy - 0.9)
        for b in types:
            ylab.append(NICE[b] + ("$^{\\dagger}$" if b in empty else ""))
            ypos.append(yy)
            yy += 1
    pos = dict(zip([b for _, t in blocks for b in t], ypos))
    for name, vals, color, marker in series:
        ax.scatter([vals[b] for b in pos], [pos[b] for b in pos], s=16, color=color,
                   marker=marker, label=name, zorder=3, edgecolors="white", linewidths=0.5)
    for b, p in pos.items():  # thin range line per row, so the eye reads the spread
        v = [vals[b] for _, vals, _, _ in series]
        ax.plot([min(v), max(v)], [p, p], color=MUTED, lw=0.8, zorder=2)
    ax.set_yticks(ypos, ylab)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    for s in seps:
        ax.axhline(s, color=MUTED, lw=0.5)
    ax.set_xlabel(xlabel)
    # sector labels in the right margin
    start = 0
    for bi, (blabel, types) in enumerate(blocks):
        mid = np.mean(ypos[start:start + len(types)])
        ax.text(1.01, mid, blabel, transform=ax.get_yaxis_transform(), rotation=270,
                ha="left", va="center", color=INK2)
        start += len(types)


def fig_model_comparison():
    mc = pd.read_csv(ROOT / "metrics_model_comparison" / "model_comparison_seasonal_cv.csv")
    mean = mc.groupby(["Model", "Building_Type"]).R2.mean()
    vals = {mdl: mean.loc[mdl].to_dict() for mdl in ["RandomForest", "XGBoost", "LightGBM"]}
    r, c = archetype_order(vals["LightGBM"])
    empty = zero_area_types()
    fig, ax = plt.subplots(figsize=(SINGLE, 3.5))
    dot_rows(ax, [("Residential", r), ("Commercial", c)],
             [("Random forest", vals["RandomForest"], ORANGE, "s"),
              ("XGBoost", vals["XGBoost"], AQUA, "^"),
              ("LightGBM", vals["LightGBM"], BLUE, "o")],
             "Blocked seasonal-CV $R^2$ (mean of 4 folds)", empty)
    ax.set_xlim(0.15, 1.0)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=3, handletextpad=0.1,
              columnspacing=0.9, borderaxespad=0.2)
    fig.tight_layout(pad=0.3)
    save(fig, "fig_model_comparison_r2")
    return empty


def fig_ablation(empty):
    ab = pd.read_csv(ROOT / "metrics_feature_engineering" / "ablation_seasonal_cv.csv")
    a = ab[ab.Feature_Set.str.startswith("A")].set_index("Building_Type").R2.to_dict()
    e = ab[ab.Feature_Set.str.startswith("E")].set_index("Building_Type").R2.to_dict()
    gain = {b: e[b] - a[b] for b in a}
    r, c = archetype_order(gain)
    fig, ax = plt.subplots(figsize=(SINGLE, 3.5))
    dot_rows(ax, [("Residential", r), ("Commercial", c)],
             [("Set A: baseline (10 features)", a, MUTED, "o"),
              ("Set E: + lagged temperature, holiday", e, BLUE, "o")],
             "Blocked seasonal-CV $R^2$ (LightGBM)", empty)
    ax.set_xlim(0.4, 1.0)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, handletextpad=0.1,
              columnspacing=0.9, borderaxespad=0.2)
    fig.tight_layout(pad=0.3)
    save(fig, "fig_feature_ablation_r2")


# ================================================================ Fig: bus map
def bus_coords():
    t = pd.read_csv(EXP / "tract_to_bus_mapping.csv", encoding="utf-8-sig")
    z = pd.read_csv(EXP / "zcta_to_bus_mapping.csv", encoding="utf-8-sig")
    cols = ["Bus_Number", "Substation_Latitude", "Substation_Longitude"]
    xy = pd.concat([t[cols], z[cols]]).drop_duplicates("Bus_Number").set_index("Bus_Number")
    tracts = t[["INTPTLAT", "INTPTLON"]].astype(float)
    return xy, tracts


def fig_bus_map():
    xy, tracts = bus_coords()
    e_res = res_bus.sum() / 1e6  # GWh per year
    e_com = com_bus.sum() / 1e6
    e = pd.concat([e_res, e_com], axis=1, keys=["res", "com"]).fillna(0.0)
    e = e[(e.res + e.com) > 0]
    e["tot"] = e.res + e.com
    e["share"] = e.com / e.tot
    e = e.join(xy, how="inner").sort_values("tot", ascending=False)  # big first, small on top
    missing = len(e) - e.Substation_Latitude.notna().sum()

    fig, ax = plt.subplots(figsize=(SINGLE, 3.1))
    ax.scatter(tracts.INTPTLON, tracts.INTPTLAT, s=0.6, color=MUTED, lw=0, zorder=1)
    cmap = mpl.colors.LinearSegmentedColormap.from_list("blue", BLUE_RAMP[1:])  # skip the
    # near-white step so low-share buses stay visible on the page
    smax = e.tot.max()
    sc = ax.scatter(e.Substation_Longitude, e.Substation_Latitude,
                    s=4 + 120 * e.tot / smax, c=e.share * 100, cmap=cmap, vmin=0, vmax=60,
                    edgecolors="white", linewidths=0.4, zorder=3)
    ax.set_aspect(1 / np.cos(np.deg2rad(29.5)))
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.grid(visible=False)
    cb = fig.colorbar(sc, ax=ax, shrink=0.75, pad=0.02, aspect=25, extend="max")
    cb.set_label("Commercial share of bus energy (%)")
    cb.outline.set_visible(False)
    for v in [100, 500, 1000]:  # size legend, GWh per year
        ax.scatter([], [], s=4 + 120 * v / smax, color=BLUE_RAMP[3],
                   edgecolors="white", linewidths=0.4, label=f"{v:,} GWh/yr")
    ax.scatter([], [], s=4, color=MUTED, label="Census tract")
    ax.legend(loc="lower right", labelspacing=0.9, borderpad=0.4, handletextpad=0.3)
    fig.tight_layout(pad=0.3)
    save(fig, "fig_bus_map")
    return len(e), missing, e.tot.max()


# ================================================================ Fig: bus diversity
def fig_bus_shapes():
    tot = hour_beginning(res_bus.add(com_bus, fill_value=0.0))
    tot = tot[tot.index.month.isin([6, 7, 8]) & (tot.index.dayofweek < 5)]
    prof = tot.groupby(tot.index.hour).mean()
    prof = prof.loc[:, prof.max() > 0]
    norm = prof / prof.max()
    share = (com_bus.sum() / (res_bus.sum().reindex(com_bus.columns).fillna(0) + com_bus.sum()))
    share = share.reindex(norm.columns).fillna(0.0)
    with_res = share[share.index.isin(res_bus.columns)]  # skip the 4 commercial-only buses
    pick = lambda q: (with_res - with_res.quantile(q)).abs().idxmin()
    lo, hi = pick(0.05), pick(0.95)  # typical residential-heavy vs commercial-heavy bus
    fig, ax = plt.subplots(figsize=(SINGLE, 2.2))
    for b in norm.columns:
        ax.plot(norm.index, norm[b], color=MUTED, lw=0.4, alpha=0.6, zorder=1)
    ax.plot(norm.index, norm[lo], color=BLUE, lw=1.4, zorder=3,
            label=f"Bus {lo} ({share[lo] * 100:.0f}% commercial energy)")
    ax.plot(norm.index, norm[hi], color=ORANGE, lw=1.4, zorder=3, ls=(0, (4, 2)),
            label=f"Bus {hi} ({share[hi] * 100:.0f}% commercial energy)")
    ax.plot([], [], color=MUTED, lw=0.8, label=f"All {norm.shape[1]} load buses")
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 25, 6))
    ax.set_xlabel("Hour of day (EST, hour beginning)")
    ax.set_ylabel("Load / daily peak")
    ax.set_ylim(0.2, 1.03)
    ax.legend(loc="lower center", bbox_to_anchor=(0.6, 0.0))
    fig.tight_layout(pad=0.3)
    save(fig, "fig_bus_shape_diversity")
    return lo, share[lo], hi, share[hi], norm.shape[1]


# ================================================================ Fig: calendar heatmap
def calendar_matrix(series):
    """365 x 24 matrix (day of year x hour beginning), hour-ending stamps shifted back."""
    s = hour_beginning(series)
    s = s[s.index.year == 2018]
    df = pd.DataFrame({"v": s.values, "d": s.index.normalize(), "h": s.index.hour})
    return df.pivot_table(index="h", columns="d", values="v", aggfunc="mean")


def fig_calendar():
    act, mod = calendar_matrix(y), calendar_matrix(stack)
    diff = mod - act
    days = act.columns
    x0, x1 = mpl.dates.date2num(days[0]), mpl.dates.date2num(days[-1] + pd.Timedelta(days=1))
    ext = (x0, x1, 0, 24)

    seq = mpl.colors.LinearSegmentedColormap.from_list("seq", BLUE_RAMP)
    # diverging blue <-> red with a neutral gray midpoint (reference palette)
    div = mpl.colors.LinearSegmentedColormap.from_list(
        "div", ["#104281", "#3987e5", "#9ec5f4", "#f0efec", "#f2a3a2", "#e34948", "#9b2020"])
    vmin = min(np.nanmin(act.values), np.nanmin(mod.values))
    vmax = max(np.nanmax(act.values), np.nanmax(mod.values))
    dlim = np.nanpercentile(np.abs(diff.values), 99.5)

    fig, axes = plt.subplots(3, 1, figsize=(DOUBLE, 4.6), sharex=True)
    panels = [(act, seq, (vmin, vmax), "(a) ERCOT Coast, reported", "Load (GW)"),
              (mod, seq, (vmin, vmax), "(b) Reconstruction, calibrated", "Load (GW)"),
              (diff, div, (-dlim, dlim), "(c) Reconstruction − ERCOT", "Difference (GW)")]
    for ax, (mat, cmap, (lo, hi), title, cbl) in zip(axes, panels):
        im = ax.imshow(mat.values, aspect="auto", origin="lower", extent=ext, cmap=cmap,
                       vmin=lo, vmax=hi, interpolation="nearest")
        ax.set_yticks([0, 6, 12, 18, 24])
        ax.set_ylabel("Hour")
        ax.grid(False)
        ax.text(0.0, 1.02, title, transform=ax.transAxes, ha="left", va="bottom",
                fontweight="bold", color=INK)
        cb = fig.colorbar(im, ax=ax, pad=0.01, aspect=12, fraction=0.03,
                          extend="both" if cmap is div else "neither")
        cb.set_label(cbl)
        cb.outline.set_visible(False)
        cb.formatter = mpl.ticker.FuncFormatter(lambda v, _: f"{v / 1000:g}")
        cb.update_ticks()
    axes[-1].xaxis.set_major_locator(mpl.dates.MonthLocator())
    axes[-1].xaxis.set_major_formatter(mpl.dates.DateFormatter("%b"))
    axes[-1].set_xlim(x0, x1)
    fig.tight_layout(pad=0.3, h_pad=0.8)
    save(fig, "fig_calendar_heatmap")
    return dlim


# ================================================================ Fig: spatial load density
def _dbf_column(raw, field):
    """Values of one character field from a dBASE III table (bytes)."""
    import struct
    n_rec, hdr_len, rec_len = struct.unpack("<IHH", raw[4:12])
    fields, pos, off = [], 32, 1  # offset 1 skips the deletion flag
    while raw[pos] != 0x0D:
        name = raw[pos:pos + 11].split(b"\0")[0].decode()
        size = raw[pos + 16]
        fields.append((name, off, size))
        off += size
        pos += 32
    _, foff, fsize = next(f for f in fields if f[0] == field)
    return [raw[hdr_len + i * rec_len + foff: hdr_len + i * rec_len + foff + fsize]
            .decode().strip() for i in range(n_rec)]


def read_polygons(zip_path, stem, field, keep):
    """Minimal zipped-shapefile reader (polygon type 5): {field value: [ring arrays]}.
    Avoids a geopandas dependency; records are read in file order with forward seeks."""
    import struct
    import zipfile
    zf = zipfile.ZipFile(zip_path)
    keys = _dbf_column(zf.read(f"{stem}.dbf"), field)
    shx = zf.read(f"{stem}.shx")
    want = sorted(i for i, k in enumerate(keys) if k in keep)
    out = {}
    with zf.open(f"{stem}.shp") as f:
        for i in want:
            offset = struct.unpack(">i", shx[100 + 8 * i: 104 + 8 * i])[0] * 2
            f.seek(offset)
            _, clen = struct.unpack(">ii", f.read(8))
            rec = f.read(clen * 2)
            stype, = struct.unpack("<i", rec[:4])
            if stype != 5:
                continue
            nparts, npts = struct.unpack("<ii", rec[36:44])
            parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
            pts = np.frombuffer(rec, "<f8", 2 * npts, 44 + 4 * nparts).reshape(-1, 2)
            out[keys[i]] = [pts[parts[j]:parts[j + 1]] for j in range(nparts)]
    return out


def geography_loads():
    """Mean load (kW) of every tract (residential) and ZCTA (commercial) BEFORE the
    nearest-bus assignment, rebuilt from the same inputs as the notebooks and checked to
    sum back exactly to the per-bus count files."""
    import json
    cnt = pd.read_csv(EXP / "final_bus_building_counts.csv", index_col=0)
    sq = pd.read_csv(EXP / "bus_commercial_sqft.csv", index_col=0)
    # per-unit mean load of each archetype: bus mean load is linear in the counts
    u_res = np.linalg.lstsq(cnt.loc[res_bus.columns].values, res_bus.mean().values,
                            rcond=None)[0]
    u_com = np.linalg.lstsq(sq.loc[com_bus.columns].values, com_bus.mean().values,
                            rcond=None)[0]

    # residential: B25024 -> 5 archetypes, same crosswalk as residential.ipynb
    t = pd.read_csv(EXP / "tract_to_bus_mapping.csv", encoding="utf-8-sig", dtype={"GEOID": str})
    c = pd.read_csv(EXP / "census_b25024_state_48_tracts.csv",
                    dtype={"county": str, "tract": str})
    c["GEOID"] = "48" + c.county.str.zfill(3) + c.tract.str.zfill(6)
    c["single-family_detached"] = c.B25024_002E
    c["single-family_attached"] = c.B25024_003E
    c["multi-family_with_2_-_4_units"] = c.B25024_004E + c.B25024_005E
    c["multi-family_with_5plus_units"] = c[[f"B25024_00{k}E" for k in (6, 7, 8, 9)]].sum(axis=1)
    c["mobile_home"] = c.B25024_010E
    tr = t[["GEOID", "Bus_Number"]].merge(c[["GEOID", *cnt.columns]], on="GEOID", how="left")
    check = tr.groupby("Bus_Number")[list(cnt.columns)].sum().reindex(cnt.index).fillna(0)
    assert np.allclose(check.values, cnt.values), "tract counts no longer match bus counts"
    tract_kw = pd.Series(tr[cnt.columns].values @ u_res, index=tr.GEOID)

    # commercial: re-run the notebook's own NAICS mapping and sq ft factors per ZCTA
    nb = json.load(open(ROOT / "commercial.ipynb"))
    ns = {}
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if "def get_comstock_type" in src:
            exec(src.split("# --- APPLY ---")[0], ns)
        if "sqft_per_emp = {" in src:
            exec(src, ns)
    d = pd.read_csv(EXP / "tx_zbp_2018_commercial_raw.csv", dtype={"zip": str, "naics": str})
    d = d[~d.naics.str.contains("[-/]")].copy()
    d["naics"] = d.naics.astype(int)
    zc = pd.read_csv(EXP / "tl_2018_us_zcta510_COAST_centwithin.csv", dtype=str)
    d = d[d.zip.isin(zc.ZCTA5CE10)]
    d["t"] = d.naics.apply(ns["get_comstock_type"])
    d = d[~d.t.isin(["Industrial", "Other"]) & (d.Final_Employees > 0)]
    d["sqft"] = d.Final_Employees * d.t.map(ns["sqft_per_emp"]).fillna(250)
    pv = d.pivot_table(index="zip", columns="t", values="sqft", aggfunc="sum", fill_value=0)
    pv = pv.reindex(columns=sq.columns, fill_value=0)
    zm = pd.read_csv(EXP / "zcta_to_bus_mapping.csv", encoding="utf-8-sig",
                     dtype={"ZCTA5CE10": str})
    zz = zm[["ZCTA5CE10", "Bus_Number"]].merge(pv, left_on="ZCTA5CE10", right_index=True,
                                               how="left").fillna(0)
    check = zz.groupby("Bus_Number")[list(sq.columns)].sum().reindex(sq.index).fillna(0)
    assert np.allclose(check.values, sq.values), "ZCTA sq ft no longer match bus sq ft"
    zcta_kw = pd.Series(zz[sq.columns].values @ u_com, index=zz.ZCTA5CE10)
    return tract_kw, zcta_kw


def rasterize(polys, loads, lon, lat, footprint):
    """Spread each polygon's load uniformly over the grid cells whose centers fall inside
    it (or the cell holding its first vertex if it is smaller than a cell)."""
    from matplotlib.path import Path as MPath
    grid = np.zeros((len(lat), len(lon)))
    d = lon[1] - lon[0]
    for key, rings in polys.items():
        verts = np.vstack(rings)
        codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r) - 1) for r in rings])
        path = MPath(verts, codes)
        (x0, y0), (x1, y1) = verts.min(0), verts.max(0)
        ix = np.where((lon >= x0 - d) & (lon <= x1 + d))[0]
        iy = np.where((lat >= y0 - d) & (lat <= y1 + d))[0]
        if len(ix) and len(iy):
            gx, gy = np.meshgrid(lon[ix], lat[iy])
            inside = path.contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
        else:
            inside = np.zeros((0, 0), bool)
        if inside.any():
            yy, xx = np.nonzero(inside)
            yy, xx = iy[yy], ix[xx]
        else:
            xx = [np.abs(lon - verts[:, 0].mean()).argmin()]
            yy = [np.abs(lat - verts[:, 1].mean()).argmin()]
        footprint[yy, xx] = True
        grid[yy, xx] += loads.get(key, 0.0) / len(xx)
    return grid


def fig_density_map(res_ = 0.01):
    tract_kw, zcta_kw = geography_loads()
    tracts = read_polygons(EXP / "tl_2018_48_tract.zip", "tl_2018_48_tract", "GEOID",
                           set(tract_kw.index))
    zctas = read_polygons(EXP / "tl_2018_us_zcta510.zip", "tl_2018_us_zcta510", "ZCTA5CE10",
                          set(zcta_kw.index))
    allv = np.vstack([np.vstack(r) for r in tracts.values()])
    (x0, y0), (x1, y1) = allv.min(0), allv.max(0)
    lon = np.arange(x0, x1 + res_, res_) + res_ / 2
    lat = np.arange(y0, y1 + res_, res_) + res_ / 2
    foot = np.zeros((len(lat), len(lon)), bool)
    g_res = rasterize(tracts, tract_kw.to_dict(), lon, lat, foot)
    foot_res = foot.copy()
    g_com = rasterize(zctas, zcta_kw.to_dict(), lon, lat, foot)
    kw_tot = tract_kw.sum() + zcta_kw.sum()
    assert np.isclose(g_res.sum() + g_com.sum(), kw_tot), "load lost in rasterization"
    cell_km2 = (res_ * 111.32 * np.cos(np.deg2rad(lat)))[:, None] * (res_ * 110.57)
    dens = (g_res + g_com) / 1000 / cell_km2  # MW per km2
    dens = np.where(foot_res, dens, np.nan)   # draw within the 12-county tract footprint

    fig, ax = plt.subplots(figsize=(SINGLE, 3.2))
    bg = np.where(foot_res, 1.0, np.nan)
    ax.imshow(bg, origin="lower", extent=(lon[0], lon[-1], lat[0], lat[-1]),
              cmap=mpl.colors.ListedColormap(["#f0efec"]), interpolation="nearest")
    cmap = mpl.colors.LinearSegmentedColormap.from_list("seq", BLUE_RAMP)
    pos = dens[np.isfinite(dens) & (dens > 0)]
    lo, hi = np.percentile(pos, 5), np.percentile(pos, 99.5)
    im = ax.imshow(np.where(dens > 0, dens, np.nan), origin="lower",
                   extent=(lon[0], lon[-1], lat[0], lat[-1]), cmap=cmap,
                   norm=mpl.colors.LogNorm(lo, hi), interpolation="nearest")
    xy, _ = bus_coords()
    live = res_bus.columns.union(com_bus.columns[com_bus.sum() > 0])
    b = xy.loc[xy.index.intersection(live)]
    ax.scatter(b.Substation_Longitude, b.Substation_Latitude, s=3, color=ORANGE,
               edgecolors=INK, linewidths=0.2, zorder=4, label="Load bus")
    ax.set_aspect(1 / np.cos(np.deg2rad(29.5)))
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.grid(visible=False)
    ax.legend(loc="lower right", handletextpad=0.2, markerscale=2)
    cb = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02, aspect=25, extend="both")
    cb.set_label("Mean load density (MW/km$^2$)")
    cb.outline.set_visible(False)
    fig.tight_layout(pad=0.3)
    save(fig, "fig_load_density_map")
    peak_cell = np.nanmax(dens)
    return kw_tot / 1000, len(tracts), len(zctas), lo, hi, peak_cell


if __name__ == "__main__":
    fig_timeseries()
    d = fig_diurnal()
    fig_ldc()
    mon = fig_monthly()
    empty = fig_model_comparison()
    fig_ablation(empty)
    nb, miss, emax = fig_bus_map()
    lo, slo, hi, shi, nshape = fig_bus_shapes()
    dlim = fig_calendar()
    mw, nt, nz, dlo, dhi, dpk = fig_density_map()
    print("\nNumbers to quote in captions/text:")
    print(f"  calendar: difference color scale +/-{dlim:,.0f} MW (99.5th pct of |diff|)")
    print(f"  density map: {mw:,.0f} MW mean load from {nt} tracts + {nz} ZCTAs; "
          f"color {dlo:.2f}-{dhi:.1f} MW/km2, max cell {dpk:.1f} MW/km2")
    print(f"  calibration RES x{RES_SCALE}, COM x{COM_SCALE}, industrial {IND_MW:g} MW")
    for t, r in d:
        print(f"  diurnal r, {t}: {r:.3f}")
    print(f"  monthly bias (model/ERCOT - 1): "
          + ", ".join(f"{m}:{(v - 1) * 100:+.0f}%" for m, v in (mon.Model / mon.ERCOT).items()))
    print(f"  zero-floor-area commercial archetypes (dagger): {sorted(empty)}")
    print(f"  bus map: {nb} load-carrying buses drawn ({miss} without coordinates), max {emax:,.0f} GWh/yr")
    print(f"  bus shapes: {nshape} buses; {lo} {slo:.0%} com, {hi} {shi:.0%} com")
