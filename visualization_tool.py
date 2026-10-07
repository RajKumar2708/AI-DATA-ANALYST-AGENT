from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

BG = "#0B1420"
PANEL = "#142235"
TEXT = "#F4F7FB"
MUTED = "#91A4BC"
GRID = "#263A52"
PALETTE = ["#3B82F6", "#11C5C6", "#34D399", "#F59E0B", "#FB7185", "#A855F7", "#26A6B8", "#60A5FA"]

SUPPORTED_CHARTS = {
    "bar", "horizontal_bar", "grouped_bar", "stacked_bar", "line", "area", "pie", "donut",
    "scatter", "bubble", "histogram", "box", "violin", "heatmap", "correlation_heatmap",
    "funnel", "radar", "waterfall", "gauge", "treemap", "sunburst", "pareto", "candlestick",
    "geographic_map", "missing_values", "data_quality", "outlier"
}


def _style(ax):
    ax.set_facecolor(PANEL)
    ax.figure.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=7)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, axis="y", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def _clean_label(v):
    return str(v).replace("_", " ")


def _money_tick(v, pos=None):
    if abs(v) >= 1e6:
        return f"Rs {v/1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"Rs {v/1e3:.0f}K"
    return f"Rs {v:,.0f}"


def _currency_axis(ax, axis="y"):
    formatter = FuncFormatter(_money_tick)
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)


def create_chart(df, chart_type, x=None, y=None, title="Chart", output_path="chart.png", **kwargs):
    chart_type = str(chart_type).lower().replace(" ", "_").replace("-", "_")
    if chart_type not in SUPPORTED_CHARTS:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    data = df.copy()

    fig, ax = plt.subplots(figsize=(6.4, 3.25), dpi=220)
    _style(ax)
    fig.subplots_adjust(left=0.14, right=0.97, top=0.82, bottom=0.19)
    fig.suptitle(title, x=0.03, y=0.96, ha="left", fontsize=11, fontweight="bold", color=TEXT)

    if chart_type in {"bar", "horizontal_bar", "grouped_bar", "stacked_bar"}:
        if x is None or y is None:
            raise ValueError("bar chart requires x and y")
        grouped = data.groupby(x, dropna=False)[y].sum().sort_values(ascending=False)
        labels = [_clean_label(v) for v in grouped.index]
        vals = grouped.values
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(vals))]
        if chart_type == "horizontal_bar":
            ax.barh(labels[::-1], vals[::-1], color=colors[::-1], height=0.62)
            for i, v in enumerate(vals[::-1]):
                ax.text(v, i, f" {v/1e6:.1f}M" if abs(v) >= 1e6 else f" {v:,.0f}", va="center", fontsize=7, color=TEXT)
            ax.grid(True, axis="x", color=GRID, linewidth=0.6)
            ax.grid(False, axis="y")
            if "revenue" in str(y).lower() or "profit" in str(y).lower() or "cost" in str(y).lower():
                _currency_axis(ax, "x")
        else:
            bars = ax.bar(labels, vals, color=colors, width=0.62)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, v, f"Rs {v/1e6:.1f}M" if abs(v) >= 1e6 else f"{v:,.0f}", ha="center", va="bottom", fontsize=6.6, color=TEXT)
            ax.tick_params(axis="x", rotation=20)
            if "revenue" in str(y).lower() or "profit" in str(y).lower() or "cost" in str(y).lower():
                _currency_axis(ax, "y")
        ax.set_xlabel(_clean_label(x), color=MUTED, fontsize=7)
        ax.set_ylabel(_clean_label(y), color=MUTED, fontsize=7)

    elif chart_type in {"line", "area"}:
        if x is None or y is None:
            raise ValueError("line chart requires x and y")
        tmp = data[[x, y]].copy()
        dates = pd.to_datetime(tmp[x], errors="coerce")
        if dates.notna().sum() > len(tmp) * 0.6:
            tmp["__date"] = dates
            tmp = tmp.dropna(subset=["__date"]).sort_values("__date")
            tmp["__period"] = tmp["__date"].dt.to_period("M").astype(str)
            series = tmp.groupby("__period")[y].sum()
            labels = series.index.tolist()
        else:
            series = tmp.groupby(x, dropna=False)[y].sum()
            labels = [str(v) for v in series.index]
        xs = np.arange(len(series))
        ax.plot(xs, series.values, color=PALETTE[0], linewidth=2.2, marker="o", markersize=3)
        if chart_type == "area":
            ax.fill_between(xs, series.values, alpha=0.18, color=PALETTE[0])
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=6.5, color=MUTED)
        ax.set_xlabel(_clean_label(x), color=MUTED, fontsize=7)
        ax.set_ylabel(_clean_label(y), color=MUTED, fontsize=7)
        if "revenue" in str(y).lower() or "profit" in str(y).lower():
            _currency_axis(ax, "y")

    elif chart_type in {"pie", "donut"}:
        if x is None or y is None:
            raise ValueError("pie chart requires x and y")
        grouped = data.groupby(x, dropna=False)[y].sum().sort_values(ascending=False)
        labels = [_clean_label(v) for v in grouped.index]
        vals = grouped.values
        wedges, texts, autotexts = ax.pie(
            vals,
            labels=labels if len(vals) <= 6 else None,
            colors=[PALETTE[i % len(PALETTE)] for i in range(len(vals))],
            startangle=90,
            counterclock=False,
            autopct="%1.0f%%" if len(vals) <= 6 else None,
            pctdistance=0.73,
            textprops={"color": TEXT, "fontsize": 7}
        )
        if chart_type == "donut":
            centre = plt.Circle((0, 0), 0.52, fc=PANEL)
            ax.add_artist(centre)
        if len(vals) > 6:
            ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=6.5, labelcolor=TEXT)
        for t in autotexts:
            t.set_color(TEXT)
            t.set_fontsize(7)

    elif chart_type in {"scatter", "bubble"}:
        if x is None or y is None:
            raise ValueError("scatter chart requires x and y")
        xx = pd.to_numeric(data[x], errors="coerce")
        yy = pd.to_numeric(data[y], errors="coerce")
        mask = xx.notna() & yy.notna()
        sizes = np.full(mask.sum(), 22)
        ax.scatter(xx[mask], yy[mask], s=sizes, alpha=0.55, c=PALETTE[0], edgecolors="none")
        ax.set_xlabel(_clean_label(x), color=MUTED, fontsize=7)
        ax.set_ylabel(_clean_label(y), color=MUTED, fontsize=7)

    elif chart_type == "histogram":
        if x is None:
            raise ValueError("histogram requires x")
        vals = pd.to_numeric(data[x], errors="coerce").dropna()
        ax.hist(vals, bins=20, color=PALETTE[0], alpha=0.9, edgecolor=BG)
        ax.set_xlabel(_clean_label(x), color=MUTED, fontsize=7)
        ax.set_ylabel("Count", color=MUTED, fontsize=7)

    elif chart_type in {"box", "violin"}:
        if y is None:
            raise ValueError("box/violin chart requires y")
        vals = pd.to_numeric(data[y], errors="coerce").dropna()
        if chart_type == "box":
            ax.boxplot(vals, vert=True, patch_artist=True, boxprops=dict(facecolor=PALETTE[0], alpha=0.75), medianprops=dict(color=TEXT, linewidth=1.4))
        else:
            parts = ax.violinplot(vals, showmeans=True, showmedians=True)
            for body in parts["bodies"]:
                body.set_facecolor(PALETTE[0]); body.set_alpha(0.75)
        ax.set_xticks([1]); ax.set_xticklabels([_clean_label(y)], color=MUTED, fontsize=7)

    elif chart_type in {"heatmap", "correlation_heatmap"}:
        corr = data.select_dtypes(include="number").corr()
        im = ax.imshow(corr.values, cmap="Blues", vmin=-1, vmax=1, aspect="auto")
        labels = [str(c) for c in corr.columns]
        ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=5.5, color=MUTED)
        ax.set_yticklabels(labels, fontsize=5.5, color=MUTED)
        for i in range(len(labels)):
            for j in range(len(labels)):
                ax.text(j, i, f"{corr.iloc[i, j]:.1f}", ha="center", va="center", fontsize=5.5, color=TEXT)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)

    elif chart_type == "missing_values":
        counts = data.isna().sum().sort_values(ascending=False)
        counts = counts[counts > 0].head(12)
        ax.barh([_clean_label(v) for v in counts.index][::-1], counts.values[::-1], color=PALETTE[4])
        ax.grid(True, axis="x", color=GRID, linewidth=0.6)
        ax.grid(False, axis="y")
        ax.set_xlabel("Missing cells", color=MUTED, fontsize=7)

    elif chart_type == "data_quality":
        vals = [len(data), int(data.isna().sum().sum()), int(data.duplicated().sum())]
        labels = ["Rows", "Missing", "Duplicates"]
        ax.bar(labels, vals, color=PALETTE[:3], width=0.55)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=7, color=TEXT)
        ax.tick_params(axis="x", colors=MUTED)

    else:
        raise ValueError(f"Chart type '{chart_type}' is not implemented in this report renderer.")

    fig.savefig(output_path, facecolor=BG, edgecolor="none", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return output_path
