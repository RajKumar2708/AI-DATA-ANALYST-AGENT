from pathlib import Path
from datetime import datetime
import math
import os
import re

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from visualization_tool import create_chart

PAGE_W, PAGE_H = A4
MARGIN = 30
BG = HexColor("#0B1420")
PANEL = HexColor("#142235")
PANEL_2 = HexColor("#172A41")
TEXT = HexColor("#F4F7FB")
MUTED = HexColor("#91A4BC")
GRID = HexColor("#263A52")
BLUE = HexColor("#3B82F6")
CYAN = HexColor("#11C5C6")
GREEN = HexColor("#34D399")
ORANGE = HexColor("#F59E0B")
RED = HexColor("#FB7185")
PURPLE = HexColor("#A855F7")
TEAL = HexColor("#26A6B8")
ACCENTS = ["#3B82F6", "#11C5C6", "#34D399", "#F59E0B", "#FB7185", "#A855F7"]


def _slug(value):
    value = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_").lower()
    return value or "report"


def _fmt_num(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    try:
        value = float(value)
    except Exception:
        return str(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1000:
        return f"{value / 1000:.1f}K"
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _money(value):
    return "Rs " + _fmt_num(value)


def _pct(value):
    return f"{value:.1f}%" if value is not None and pd.notna(value) else "-"


def _clean_columns(df):
    if df is None:
        return []
    return [str(c) for c in df.columns]


def _select_df(df, selected_columns):
    if not selected_columns:
        return df.copy()
    cols = [c for c in selected_columns if c in df.columns]
    return df[cols].copy() if cols else df.copy()


def _detect_type(df):
    cols = set(map(str, df.columns))
    if {"Revenue", "Product"}.issubset(cols) or {"Revenue", "Category"}.issubset(cols):
        return "sales"
    if {"Stock_Quantity", "Reorder_Level"}.issubset(cols) or "Stock_Status" in cols:
        return "inventory"
    return "generic"


def _sales_metrics(df):
    revenue = pd.to_numeric(df.get("Revenue"), errors="coerce") if "Revenue" in df.columns else pd.Series(dtype=float)
    profit = pd.to_numeric(df.get("Profit"), errors="coerce") if "Profit" in df.columns else pd.Series(dtype=float)
    units = pd.to_numeric(df.get("Units_Sold"), errors="coerce") if "Units_Sold" in df.columns else pd.Series(dtype=float)
    discount = pd.to_numeric(df.get("Discount_Percentage"), errors="coerce") if "Discount_Percentage" in df.columns else pd.Series(dtype=float)
    rating = pd.to_numeric(df.get("Customer_Rating"), errors="coerce") if "Customer_Rating" in df.columns else pd.Series(dtype=float)
    return_status = df["Return_Status"].astype(str).str.lower() if "Return_Status" in df.columns else pd.Series(dtype=str)
    total_revenue = float(revenue.sum()) if len(revenue) else 0
    total_profit = float(profit.sum()) if len(profit) else 0
    return {
        "revenue": total_revenue,
        "profit": total_profit,
        "margin": (total_profit / total_revenue * 100) if total_revenue else 0,
        "units": float(units.sum()) if len(units) else 0,
        "avg_discount": float(discount.mean()) if len(discount) else None,
        "avg_rating": float(rating.mean()) if len(rating) else None,
        "return_rate": float((return_status.str.contains("returned", na=False) & ~return_status.str.contains("not returned", na=False)).mean() * 100) if len(return_status) else None,
    }


def _inventory_metrics(df):
    stock = pd.to_numeric(df.get("Stock_Quantity"), errors="coerce") if "Stock_Quantity" in df.columns else pd.Series(dtype=float)
    reorder = pd.to_numeric(df.get("Reorder_Level"), errors="coerce") if "Reorder_Level" in df.columns else pd.Series(dtype=float)
    sold30 = pd.to_numeric(df.get("Units_Sold_Last_30_Days"), errors="coerce") if "Units_Sold_Last_30_Days" in df.columns else pd.Series(dtype=float)
    lead = pd.to_numeric(df.get("Lead_Time_Days"), errors="coerce") if "Lead_Time_Days" in df.columns else pd.Series(dtype=float)
    supplier_rating = pd.to_numeric(df.get("Supplier_Rating"), errors="coerce") if "Supplier_Rating" in df.columns else pd.Series(dtype=float)
    damaged = pd.to_numeric(df.get("Damaged_Units"), errors="coerce") if "Damaged_Units" in df.columns else pd.Series(dtype=float)
    returned = pd.to_numeric(df.get("Returned_Units"), errors="coerce") if "Returned_Units" in df.columns else pd.Series(dtype=float)
    below = int((stock < reorder).sum()) if len(stock) and len(reorder) else 0
    return {
        "stock": float(stock.sum()) if len(stock) else 0,
        "below_reorder": below,
        "sold30": float(sold30.sum()) if len(sold30) else 0,
        "lead": float(lead.mean()) if len(lead) else None,
        "supplier_rating": float(supplier_rating.mean()) if len(supplier_rating) else None,
        "damaged": float(damaged.sum()) if len(damaged) else 0,
        "returned": float(returned.sum()) if len(returned) else 0,
    }


def _chart_specs(df, dataset_name, max_charts=8):
    kind = _detect_type(df)
    specs = []

    if kind == "sales":
        if {"Product", "Revenue"}.issubset(df.columns):
            specs.append(("bar", {"x": "Product", "y": "Revenue", "title": "Top Products by Revenue", "horizontal": True, "top_n": 8}))
        if {"Category", "Revenue"}.issubset(df.columns):
            specs.append(("bar", {"x": "Category", "y": "Revenue", "title": "Revenue by Category", "top_n": 8}))
        if {"Region", "Profit"}.issubset(df.columns):
            specs.append(("bar", {"x": "Region", "y": "Profit", "title": "Profit by Region", "top_n": 8}))
        date_col = next((c for c in df.columns if "date" in str(c).lower()), None)
        if date_col and "Revenue" in df.columns:
            specs.append(("line", {"x": date_col, "y": "Revenue", "title": "Monthly Revenue Trend"}))
        if {"Sales_Channel", "Revenue"}.issubset(df.columns):
            specs.append(("donut", {"x": "Sales_Channel", "y": "Revenue", "title": "Revenue by Sales Channel"}))
        if {"Category", "Profit"}.issubset(df.columns):
            specs.append(("bar", {"x": "Category", "y": "Profit", "title": "Profit by Category", "top_n": 8}))
        if {"Unit_Price", "Revenue"}.issubset(df.columns):
            specs.append(("scatter", {"x": "Unit_Price", "y": "Revenue", "title": "Unit Price vs Revenue"}))
        if {"Customer_Type", "Revenue"}.issubset(df.columns):
            specs.append(("bar", {"x": "Customer_Type", "y": "Revenue", "title": "Revenue by Customer Type", "top_n": 6}))
        if {"Region", "Revenue"}.issubset(df.columns):
            specs.append(("bar", {"x": "Region", "y": "Revenue", "title": "Revenue by Region", "top_n": 8}))
        if {"Return_Status", "Revenue"}.issubset(df.columns):
            specs.append(("donut", {"x": "Return_Status", "y": "Revenue", "title": "Revenue by Return Status"}))

    elif kind == "inventory":
        if {"Product", "Units_Sold_Last_30_Days"}.issubset(df.columns):
            specs.append(("bar", {"x": "Product", "y": "Units_Sold_Last_30_Days", "title": "Fast-Moving Products (30 Days)", "horizontal": True, "top_n": 8}))
        if {"Stock_Status", "Stock_Quantity"}.issubset(df.columns):
            specs.append(("donut", {"x": "Stock_Status", "y": "Stock_Quantity", "title": "Stock Status Mix"}))
        if {"Stock_Quantity", "Reorder_Level"}.issubset(df.columns):
            specs.append(("scatter", {"x": "Reorder_Level", "y": "Stock_Quantity", "title": "Stock vs Reorder Level"}))
        if {"Region", "Stock_Quantity"}.issubset(df.columns):
            specs.append(("bar", {"x": "Region", "y": "Stock_Quantity", "title": "Stock by Region", "top_n": 8}))
        if {"Supplier", "Lead_Time_Days"}.issubset(df.columns):
            specs.append(("bar", {"x": "Supplier", "y": "Lead_Time_Days", "title": "Supplier Lead Time", "top_n": 8}))
        if {"Supplier", "Supplier_Rating"}.issubset(df.columns):
            specs.append(("bar", {"x": "Supplier", "y": "Supplier_Rating", "title": "Supplier Rating", "top_n": 8}))
        if {"Stock_Quantity", "Units_Sold_Last_30_Days"}.issubset(df.columns):
            temp = df.copy()
            temp["Coverage_Days"] = temp["Stock_Quantity"] / temp["Units_Sold_Last_30_Days"].replace(0, pd.NA) * 30
            temp = temp.dropna(subset=["Coverage_Days"])
            if not temp.empty:
                specs.append(("bar", {"x": "Product", "y": "Coverage_Days", "title": "Estimated Stock Coverage (Days)", "horizontal": True, "top_n": 8, "dataframe": temp}))

    else:
        numeric = df.select_dtypes(include="number").columns.tolist()
        categorical = [c for c in df.columns if df[c].nunique(dropna=True) <= 8 and c not in numeric]
        if categorical and numeric:
            specs.append(("bar", {"x": categorical[0], "y": numeric[0], "title": f"{numeric[0]} by {categorical[0]}"}))
        if len(numeric) >= 2:
            specs.append(("scatter", {"x": numeric[0], "y": numeric[1], "title": f"{numeric[0]} vs {numeric[1]}"}))
        if numeric:
            specs.append(("histogram", {"x": numeric[0], "title": f"Distribution of {numeric[0]}"}))

    return specs[:max_charts]


def _make_charts(df, dataset_name, chart_dir, max_charts=8):
    chart_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    specs = _chart_specs(df, dataset_name, max_charts)
    for idx, (chart_type, options) in enumerate(specs, 1):
        options = dict(options)
        temp_df = options.pop("dataframe", df)
        title = options.get("title", f"Chart {idx}")
        top_n = options.pop("top_n", None)
        horizontal = options.pop("horizontal", False)
        if top_n and options.get("x") and options.get("y") and options["x"] in temp_df.columns and options["y"] in temp_df.columns:
            grouped = temp_df.groupby(options["x"], dropna=False)[options["y"]].sum().sort_values(ascending=False).head(top_n)
            temp_df = grouped.reset_index()
        output = chart_dir / f"{_slug(dataset_name)}_{idx}_{_slug(title)}.png"
        create_chart(
            temp_df,
            chart_type="horizontal_bar" if horizontal and chart_type == "bar" else chart_type,
            x=options.get("x"),
            y=options.get("y"),
            title=title,
            output_path=str(output),
        )
        if output.exists():
            paths.append(str(output))
    return paths


def _draw_text(c, text, x, y, size=10, color=TEXT, font="Helvetica", align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "right":
        c.drawRightString(x, y, str(text))
    elif align == "center":
        c.drawCentredString(x, y, str(text))
    else:
        c.drawString(x, y, str(text))


def _wrap(text, max_chars):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        test = word if not current else current + " " + word
        if len(test) <= max_chars:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_wrapped(c, text, x, y, width, size=9, leading=12, color=TEXT, max_lines=4):
    # Approximate character width from font size.
    max_chars = max(22, int(width / (size * 0.53)))
    lines = _wrap(text, max_chars)[:max_lines]
    for line in lines:
        _draw_text(c, line, x, y, size, color)
        y -= leading
    return y


def _header(c, title, kicker=None, page_no=None, total=None):
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(MARGIN, PAGE_H - 42, PAGE_W - 2 * MARGIN, 6, fill=1, stroke=0)
    if kicker:
        _draw_text(c, kicker.upper(), MARGIN, PAGE_H - 66, 8, CYAN, "Helvetica-Bold")
    _draw_text(c, title, MARGIN, PAGE_H - 91, 22, TEXT, "Helvetica-Bold")
    if page_no and total:
        _draw_text(c, f"Page {page_no} of {total}", PAGE_W - MARGIN, PAGE_H - 68, 8, MUTED, align="right")
    _draw_text(c, "AI DATA ANALYST", MARGIN, 18, 7, MUTED)
    if page_no:
        _draw_text(c, str(page_no), PAGE_W - MARGIN, 18, 7, MUTED, align="right")


def _card(c, x, y, w, h, label, value, sub=None, accent=BLUE):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 7, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(x, y + h - 7, w, 7, fill=1, stroke=0)
    _draw_text(c, label.upper(), x + 9, y + h - 24, 7, TEXT, "Helvetica-Bold")
    _draw_text(c, value, x + 9, y + 17, 16, TEXT, "Helvetica-Bold")
    if sub:
        _draw_text(c, sub, x + 9, y + 7, 6.5, MUTED)


def _panel(c, x, y, w, h, title=None, accent=None):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    if accent:
        c.setFillColor(accent)
        c.roundRect(x, y + h - 5, w, 5, 2, fill=1, stroke=0)
    if title:
        _draw_text(c, title, x + 10, y + h - 22, 10, TEXT, "Helvetica-Bold")


def _draw_chart(c, path, x, y, w, h):
    if not path or not os.path.exists(path):
        return
    _panel(c, x, y, w, h)
    pad = 8
    c.drawImage(ImageReader(path), x + pad, y + pad, width=w - 2 * pad, height=h - 2 * pad, preserveAspectRatio=True, anchor="c", mask="auto")


def _top_summary(df, kind):
    if kind == "sales":
        m = _sales_metrics(df)
        top_product = None
        top_category = None
        top_region = None
        if {"Product", "Revenue"}.issubset(df.columns):
            s = df.groupby("Product")["Revenue"].sum().sort_values(ascending=False)
            if not s.empty:
                top_product = (s.index[0], float(s.iloc[0]))
        if {"Category", "Revenue"}.issubset(df.columns):
            s = df.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
            if not s.empty:
                top_category = (s.index[0], float(s.iloc[0]))
        if {"Region", "Revenue"}.issubset(df.columns):
            s = df.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
            if not s.empty:
                top_region = (s.index[0], float(s.iloc[0]))
        return {
            "kind": kind,
            "metrics": m,
            "top_product": top_product,
            "top_category": top_category,
            "top_region": top_region,
        }
    if kind == "inventory":
        m = _inventory_metrics(df)
        top_product = None
        if {"Product", "Units_Sold_Last_30_Days"}.issubset(df.columns):
            s = df.groupby("Product")["Units_Sold_Last_30_Days"].sum().sort_values(ascending=False)
            if not s.empty:
                top_product = (s.index[0], float(s.iloc[0]))
        return {"kind": kind, "metrics": m, "top_product": top_product}
    return {"kind": kind, "metrics": {}, "top_product": None}


def _findings_for_dataset(name, df):
    kind = _detect_type(df)
    s = _top_summary(df, kind)
    findings = []
    if kind == "sales":
        m = s["metrics"]
        findings.append(f"{name}: total revenue is {_money(m['revenue'])} across {len(df):,} records.")
        if s.get("top_product"):
            findings.append(f"{s['top_product'][0]} leads product revenue at {_money(s['top_product'][1])}.")
        if s.get("top_category"):
            findings.append(f"{s['top_category'][0]} leads category revenue at {_money(s['top_category'][1])}.")
        if s.get("top_region"):
            findings.append(f"{s['top_region'][0]} leads the region revenue mix at {_money(s['top_region'][1])}.")
        findings.append(f"Total profit is {_money(m['profit'])}, with an overall margin of {_pct(m['margin'])}.")
    elif kind == "inventory":
        m = s["metrics"]
        findings.append(f"{name}: total stock is {_fmt_num(m['stock'])} units across {len(df):,} records.")
        findings.append(f"{m['below_reorder']:,} records are below their reorder level.")
        findings.append(f"30-day units sold total {_fmt_num(m['sold30'])}.")
        if s.get("top_product"):
            findings.append(f"{s['top_product'][0]} has the highest 30-day movement at {_fmt_num(s['top_product'][1])} units.")
        if m.get("lead") is not None:
            findings.append(f"Average supplier lead time is {m['lead']:.1f} days.")
    else:
        findings.append(f"{name}: {len(df):,} records and {len(df.columns):,} columns are available for analysis.")
        numeric = df.select_dtypes(include="number").columns.tolist()
        if numeric:
            findings.append(f"The dataset contains {len(numeric)} numeric fields suitable for quantitative analysis.")
        findings.append(f"Missing cells: {int(df.isna().sum().sum()):,}; duplicate rows: {int(df.duplicated().sum()):,}.")
    return findings


def _metric_cards(datasets):
    non_empty = {n: d for n, d in datasets.items() if len(d) > 0}
    if len(non_empty) == 1:
        name, df = next(iter(non_empty.items()))
        kind = _detect_type(df)
        if kind == "sales":
            m = _sales_metrics(df)
            return [
                ("TOTAL REVENUE", _money(m["revenue"]), "full dataset", BLUE),
                ("TOTAL PROFIT", _money(m["profit"]), f"margin {_pct(m['margin'])}", GREEN),
                ("UNITS SOLD", _fmt_num(m["units"]), "all records", CYAN),
                ("AVG RATING", f"{m['avg_rating']:.2f}" if m['avg_rating'] is not None else "-", "customer rating", PURPLE),
                ("RETURN RATE", _pct(m["return_rate"]), "returned orders", RED),
                ("AVG DISCOUNT", _pct(m["avg_discount"]), "discount percentage", ORANGE),
                ("RECORDS", f"{len(df):,}", name, TEAL),
                ("COLUMNS", f"{len(df.columns):,}", name, BLUE),
            ]
        if kind == "inventory":
            m = _inventory_metrics(df)
            return [
                ("STOCK UNITS", _fmt_num(m["stock"]), "current stock", BLUE),
                ("BELOW REORDER", _fmt_num(m["below_reorder"]), "records below threshold", RED),
                ("30D UNITS SOLD", _fmt_num(m["sold30"]), "recent movement", CYAN),
                ("AVG LEAD TIME", f"{m['lead']:.1f} d" if m["lead"] is not None else "-", "supplier lead time", ORANGE),
                ("SUPPLIER RATING", f"{m['supplier_rating']:.2f}" if m["supplier_rating"] is not None else "-", "average rating", PURPLE),
                ("DAMAGED UNITS", _fmt_num(m["damaged"]), "recorded damage", RED),
                ("RECORDS", f"{len(df):,}", name, TEAL),
                ("COLUMNS", f"{len(df.columns):,}", name, BLUE),
            ]
    rows = sum(len(d) for d in non_empty.values())
    cols = sum(len(d.columns) for d in non_empty.values())
    missing = sum(int(d.isna().sum().sum()) for d in non_empty.values())
    return [
        ("DATASETS", f"{len(non_empty):,}", "non-empty datasets", BLUE),
        ("RECORDS", f"{rows:,}", "usable records", CYAN),
        ("COLUMNS", f"{cols:,}", "combined columns", GREEN),
        ("MISSING CELLS", f"{missing:,}", "combined quality check", RED),
        ("SALES FILES", f"{sum(_detect_type(d)=='sales' for d in non_empty.values()):,}", "detected sales datasets", ORANGE),
        ("INVENTORY FILES", f"{sum(_detect_type(d)=='inventory' for d in non_empty.values()):,}", "detected inventory datasets", PURPLE),
        ("EMPTY FILES", f"{len(datasets)-len(non_empty):,}", "excluded from analysis", RED),
        ("REPORT PAGES", "4", "dashboard style", TEAL),
    ]


def _draw_stats_strip(c, stats, x, y, w, h, accent=BLUE):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(x, y + h - 6, w, 6, fill=1, stroke=0)
    _draw_text(c, "KEY STATISTICS AT A GLANCE", x + 10, y + h - 22, 9, TEXT, "Helvetica-Bold")
    n = len(stats)
    cell_w = (w - 20) / n
    for i, (label, value) in enumerate(stats):
        xx = x + 10 + i * cell_w
        if i:
            c.setStrokeColor(GRID)
            c.setLineWidth(0.5)
            c.line(xx, y + 10, xx, y + h - 32)
        _draw_text(c, label, xx + 5, y + 25, 6.5, MUTED)
        _draw_text(c, value, xx + 5, y + 11, 8.5, TEXT, "Helvetica-Bold")


def _draw_findings_strip(c, findings, x, y, w, h, accent=CYAN):
    c.setFillColor(PANEL_2)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
    _draw_text(c, "KEY INSIGHTS", x + 10, y + h - 22, 9, TEXT, "Helvetica-Bold")
    line_y = y + h - 38
    for finding in findings[:5]:
        c.setFillColor(accent)
        c.circle(x + 15, line_y + 2, 2.2, fill=1, stroke=0)
        line_y = _draw_wrapped(c, finding, x + 24, line_y, w - 35, size=7.5, leading=10, color=TEXT, max_lines=2)
        line_y -= 3
        if line_y < y + 8:
            break


def _recommendations_for_dataset(df, kind):
    if kind == "sales":
        recs = []
        if {"Product", "Revenue"}.issubset(df.columns):
            g = df.groupby("Product")["Revenue"].sum().sort_values(ascending=False)
            if len(g) >= 2:
                share = float(g.iloc[0] / g.sum() * 100) if g.sum() else 0
                recs.append(("HIGH", f"Protect availability of the leading product, which contributes {share:.1f}% of recorded revenue."))
        if {"Region", "Revenue"}.issubset(df.columns):
            g = df.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
            if not g.empty:
                recs.append(("MEDIUM", f"Review the regional mix around {g.index[0]}, the highest-revenue region."))
        if {"Category", "Profit", "Revenue"}.issubset(df.columns):
            g = df.groupby("Category")[["Revenue", "Profit"]].sum()
            g["Margin"] = g["Profit"] / g["Revenue"].replace(0, pd.NA) * 100
            g = g.dropna(subset=["Margin"]).sort_values("Margin", ascending=True)
            if not g.empty:
                recs.append(("MEDIUM", f"Investigate {g.index[0]} margins before increasing spend or discounting."))
        if "Return_Status" in df.columns:
            r = df["Return_Status"].astype(str).str.lower()
            returned = int((r.str.contains("returned", na=False) & ~r.str.contains("not returned", na=False)).sum())
            recs.append(("LOW", f"Track return activity across products; {returned:,} recorded orders are marked returned."))
        return recs[:4]
    if kind == "inventory":
        recs = []
        m = _inventory_metrics(df)
        recs.append(("HIGH", f"Review {m['below_reorder']:,} records below reorder level and prioritise replenishment."))
        if {"Product", "Units_Sold_Last_30_Days"}.issubset(df.columns):
            g = df.groupby("Product")["Units_Sold_Last_30_Days"].sum().sort_values(ascending=False)
            if not g.empty:
                recs.append(("MEDIUM", f"Protect availability for {g.index[0]}, the fastest-moving product in the recent 30-day view."))
        if "Lead_Time_Days" in df.columns:
            lead = pd.to_numeric(df["Lead_Time_Days"], errors="coerce").dropna()
            if len(lead):
                recs.append(("MEDIUM", f"Review supplier lead times around the {lead.mean():.1f}-day average to reduce replenishment delays."))
        if {"Damaged_Units", "Returned_Units"}.issubset(df.columns):
            recs.append(("LOW", f"Monitor recorded damage and returns: {_fmt_num(pd.to_numeric(df['Damaged_Units'], errors='coerce').sum())} damaged and {_fmt_num(pd.to_numeric(df['Returned_Units'], errors='coerce').sum())} returned units."))
        return recs[:4]
    return [
        ("MEDIUM", "Use the highest-value segments as the starting point for the next review."),
        ("LOW", "Review missing and duplicate records before operational decisions."),
    ]


def _draw_recommendation_grid(c, recs, x, y, w, h):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(ORANGE)
    c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
    _draw_text(c, "ACTION PRIORITIES", x + 10, y + h - 22, 10, TEXT, "Helvetica-Bold")
    if not recs:
        recs = [("LOW", "No additional action cues were generated from the available fields.")]
    card_gap = 8
    inner_x = x + 10
    inner_y = y + 9
    card_w = (w - 20 - card_gap) / 2
    card_h = (h - 44 - card_gap) / 2
    for i, (priority, rec) in enumerate(recs[:4]):
        col = i % 2
        row = i // 2
        xx = inner_x + col * (card_w + card_gap)
        yy = inner_y + (1 - row) * (card_h + card_gap)
        c.setFillColor(PANEL_2)
        c.roundRect(xx, yy, card_w, card_h, 6, fill=1, stroke=0)
        accent = ORANGE if priority == "HIGH" else BLUE if priority == "MEDIUM" else MUTED
        c.setFillColor(accent)
        c.rect(xx, yy + card_h - 18, card_w, 18, fill=1, stroke=0)
        _draw_text(c, priority, xx + 8, yy + card_h - 13, 6.5, BG, "Helvetica-Bold")
        _draw_wrapped(c, rec, xx + 8, yy + card_h - 31, card_w - 16, size=6.6, leading=8, color=TEXT, max_lines=2)


def _draw_recommendations(c, findings, x, y, w, h):
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColor(ORANGE)
    c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
    _draw_text(c, "ACTION PRIORITIES", x + 10, y + h - 22, 10, TEXT, "Helvetica-Bold")
    recs = []
    for f in findings[:4]:
        lower = f.lower()
        if "below" in lower or "reorder" in lower:
            recs.append("Review stock below reorder thresholds and prioritise replenishment.")
        elif "revenue" in lower and "leads" in lower:
            recs.append("Protect availability of the leading revenue-driving segments.")
        elif "margin" in lower:
            recs.append("Review margin by product/category before scaling volume further.")
        elif "lead time" in lower:
            recs.append("Review supplier lead-time concentration for operational resilience.")
        else:
            recs.append("Use the segment mix as the starting point for the next business review.")
    recs = list(dict.fromkeys(recs))[:4]
    yy = y + h - 42
    for i, rec in enumerate(recs, 1):
        box_y = yy - 52
        c.setFillColor(PANEL_2)
        c.roundRect(x + 10, box_y, w - 20, 44, 6, fill=1, stroke=0)
        _draw_text(c, f"R{i}", x + 18, box_y + 29, 8, ORANGE, "Helvetica-Bold")
        _draw_wrapped(c, rec, x + 43, box_y + 31, w - 65, size=8, leading=10, color=TEXT, max_lines=2)
        yy = box_y - 8
        if box_y < y + 6:
            break


def _draw_table(c, x, y, w, row_h, headers, rows, widths=None, accent=BLUE):
    if widths is None:
        widths = [w / len(headers)] * len(headers)
    total_rows = 1 + len(rows)
    c.setFillColor(PANEL)
    c.roundRect(x, y, w, row_h * total_rows, 7, fill=1, stroke=0)
    cursor_x = x
    c.setFillColor(accent)
    c.rect(x, y + row_h * (total_rows - 1), w, row_h, fill=1, stroke=0)
    for i, header in enumerate(headers):
        _draw_text(c, header, cursor_x + 7, y + row_h * (total_rows - 1) + 8, 7, TEXT, "Helvetica-Bold")
        cursor_x += widths[i]
    for r, row in enumerate(rows):
        yy = y + row_h * (total_rows - 2 - r)
        if r % 2 == 1:
            c.setFillColor(Color(1, 1, 1, alpha=0.03))
            c.rect(x, yy, w, row_h, fill=1, stroke=0)
        cursor_x = x
        for i, cell in enumerate(row):
            _draw_text(c, cell, cursor_x + 7, yy + 8, 7.2, MUTED if r % 2 == 0 else TEXT)
            cursor_x += widths[i]
    # vertical lines
    cursor_x = x
    c.setStrokeColor(GRID)
    c.setLineWidth(0.5)
    for width in widths[:-1]:
        cursor_x += width
        c.line(cursor_x, y, cursor_x, y + row_h * total_rows)
    for r in range(1, total_rows):
        yy = y + r * row_h
        c.line(x, yy, x + w, yy)


def _summary_table_data(df, kind):
    rows = []
    if kind == "sales":
        if {"Category", "Revenue", "Profit"}.issubset(df.columns):
            g = df.groupby("Category")[ ["Revenue", "Profit"] ].sum().sort_values("Revenue", ascending=False).head(8)
            for idx, row in g.iterrows():
                margin = (row["Profit"] / row["Revenue"] * 100) if row["Revenue"] else 0
                rows.append([str(idx), _money(row["Revenue"]), _money(row["Profit"]), _pct(margin)])
        return rows
    if kind == "inventory":
        if {"Region", "Stock_Quantity", "Units_Sold_Last_30_Days"}.issubset(df.columns):
            g = df.groupby("Region")[["Stock_Quantity", "Units_Sold_Last_30_Days"]].sum().sort_values("Stock_Quantity", ascending=False).head(8)
            for idx, row in g.iterrows():
                rows.append([str(idx), _fmt_num(row["Stock_Quantity"]), _fmt_num(row["Units_Sold_Last_30_Days"]), _fmt_num(row["Stock_Quantity"] / row["Units_Sold_Last_30_Days"] * 30 if row["Units_Sold_Last_30_Days"] else 0)])
        return rows
    return rows


def build_report(
    datasets,
    title="AI Data Analyst Report",
    summary="",
    findings=None,
    focus="Overall analysis",
    selected_columns=None,
    chart_paths=None,
    web_sources=None,
):
    if not isinstance(datasets, dict) or not datasets:
        raise ValueError("No datasets were provided.")

    non_empty = {name: _select_df(df, (selected_columns or {}).get(name)) for name, df in datasets.items() if len(df) > 0}
    empty = [name for name, df in datasets.items() if len(df) == 0]
    if not non_empty:
        raise ValueError("All uploaded datasets are empty.")

    report_dir = Path("artifacts/reports")
    chart_dir = Path("artifacts/charts/report")
    report_dir.mkdir(parents=True, exist_ok=True)
    chart_dir.mkdir(parents=True, exist_ok=True)

    generated_charts = {}
    for name, df in non_empty.items():
        generated_charts[name] = _make_charts(df, name, chart_dir, max_charts=10 if len(non_empty) == 1 else 8)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = report_dir / f"AI_Data_Analyst_{stamp}_{_slug(title)}.pdf"
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(title)
    c.setAuthor("AI Data Analyst")

    multi = len(non_empty) > 1
    total_pages = 4 if multi else 3

    # Page 1 - executive dashboard
    _header(c, title, "Analytics dashboard", 1, total_pages)
    _draw_text(c, f"{', '.join(non_empty.keys())}  |  {focus}", MARGIN, PAGE_H - 114, 8.5, MUTED)
    _draw_text(c, "GENERATED", PAGE_W - MARGIN - 90, PAGE_H - 66, 7, ORANGE, "Helvetica-Bold")
    _draw_text(c, datetime.now().strftime("%d %b %Y · %H:%M"), PAGE_W - MARGIN, PAGE_H - 79, 7.5, MUTED, align="right")

    cards = _metric_cards(datasets)
    card_w = (PAGE_W - 2 * MARGIN - 3 * 10) / 4
    card_h = 56
    y1 = PAGE_H - 190
    y2 = y1 - 67
    for i, card in enumerate(cards):
        col = i % 4
        row = i // 4
        x = MARGIN + col * (card_w + 10)
        y = y1 - row * 67
        _card(c, x, y, card_w, card_h, *card)

    if not multi:
        name, df = next(iter(non_empty.items()))
        charts = generated_charts[name]
        chart_w = 250
        chart_h = 132
        top_y = 438
        _draw_chart(c, charts[0] if charts else None, MARGIN, top_y, chart_w, chart_h)
        _draw_chart(c, charts[1] if len(charts) > 1 else None, MARGIN + 10 + chart_w, top_y, PAGE_W - 2 * MARGIN - 10 - chart_w, chart_h)
        _draw_chart(c, charts[3] if len(charts) > 3 else (charts[2] if len(charts) > 2 else None), MARGIN, top_y - 145, chart_w, chart_h)
        _draw_chart(c, charts[4] if len(charts) > 4 else (charts[2] if len(charts) > 2 else None), MARGIN + 10 + chart_w, top_y - 145, PAGE_W - 2 * MARGIN - 10 - chart_w, chart_h)
        fs = _findings_for_dataset(name, df)
        stats = []
        if "Revenue" in df.columns:
            rev = pd.to_numeric(df["Revenue"], errors="coerce").dropna()
            if len(rev):
                stats.extend([("REVENUE MIN", _money(rev.min())), ("REVENUE MEDIAN", _money(rev.median())), ("REVENUE MAX", _money(rev.max()))])
        if "Profit" in df.columns:
            prof = pd.to_numeric(df["Profit"], errors="coerce").dropna()
            if len(prof):
                stats.append(("PROFIT MEDIAN", _money(prof.median())))
        if "Units_Sold" in df.columns:
            units = pd.to_numeric(df["Units_Sold"], errors="coerce").dropna()
            if len(units):
                stats.append(("AVG UNITS", f"{units.mean():.2f}"))
        if not stats:
            stats = [("ROWS", f"{len(df):,}"), ("COLUMNS", f"{len(df.columns):,}"), ("MISSING", f"{int(df.isna().sum().sum()):,}"), ("DUPLICATES", f"{int(df.duplicated().sum()):,}")]
        _draw_stats_strip(c, stats[:5], MARGIN, 118, PAGE_W - 2 * MARGIN, 52, BLUE)
        _draw_findings_strip(c, fs, MARGIN, 55, PAGE_W - 2 * MARGIN, 55, CYAN)
    else:
        # Overall: one chart from each major dataset, plus a compact portfolio panel.
        chart_y = 422
        x1 = MARGIN
        x2 = MARGIN + 275
        for name, x in zip(list(non_empty.keys())[:2], [x1, x2]):
            charts = generated_charts.get(name, [])
            _draw_chart(c, charts[0] if charts else None, x, chart_y, 255, 118)
        # second row: the next meaningful visual from each dataset
        row_y = 286
        for name, x in zip(list(non_empty.keys())[:2], [x1, x2]):
            charts = generated_charts.get(name, [])
            _draw_chart(c, charts[1] if len(charts) > 1 else None, x, row_y, 255, 118)
        all_findings = []
        for name, df in non_empty.items():
            all_findings.extend(_findings_for_dataset(name, df)[:3])
        _draw_findings_strip(c, all_findings, MARGIN, 70, PAGE_W - 2 * MARGIN, 92, CYAN)

    c.showPage()

    # Page 2 - performance and distribution
    if multi:
        first_name, first_df = list(non_empty.items())[0]
        _header(c, f"{first_name.replace('.csv', '').replace('_', ' ').title()} Performance", "Visual analysis", 2, total_pages)
        charts = generated_charts.get(first_name, [])
        x_positions = [MARGIN, MARGIN + 280]
        chart_w = 265
        chart_h = 155
        ys = [PAGE_H - 275, PAGE_H - 450, PAGE_H - 625]
        for idx in range(min(6, len(charts))):
            col = idx % 2
            row = idx // 2
            _draw_chart(c, charts[idx], x_positions[col], ys[row], chart_w, chart_h)
        _draw_findings_strip(c, _findings_for_dataset(first_name, first_df), MARGIN, 62, PAGE_W - 2 * MARGIN, 65, BLUE)
        c.showPage()

        # Page 3 - second dataset, if present
        second_name, second_df = list(non_empty.items())[1]
        second_kind = _detect_type(second_df)
        page_title = "Inventory & Operations" if second_kind == "inventory" else f"{second_name.replace('.csv', '').replace('_', ' ').title()} Analysis"
        _header(c, page_title, "Visual analysis", 3, total_pages)
        charts = generated_charts.get(second_name, [])
        for idx in range(min(6, len(charts))):
            col = idx % 2
            row = idx // 2
            _draw_chart(c, charts[idx], x_positions[col], ys[row], chart_w, chart_h)
        _draw_findings_strip(c, _findings_for_dataset(second_name, second_df), MARGIN, 62, PAGE_W - 2 * MARGIN, 65, CYAN)
        c.showPage()
    else:
        _header(c, "Performance & Distribution", "Visual analysis", 2, total_pages)
        name, df = next(iter(non_empty.items()))
        charts = generated_charts.get(name, [])
        x_positions = [MARGIN, MARGIN + 280]
        chart_w = 265
        chart_h = 155
        ys = [PAGE_H - 275, PAGE_H - 450, PAGE_H - 625]
        for idx in range(min(6, len(charts))):
            col = idx % 2
            row = idx // 2
            _draw_chart(c, charts[idx], x_positions[col], ys[row], chart_w, chart_h)
        _draw_findings_strip(c, _findings_for_dataset(name, df), MARGIN, 62, PAGE_W - 2 * MARGIN, 65, BLUE)
        c.showPage()

    # Page 3 - segment detail + action priorities (single dataset)
    if not multi:
        _header(c, "Segments, Quality & Actions", "Decision support", 3, total_pages)
        first_name, first_df = next(iter(non_empty.items()))
        first_kind = _detect_type(first_df)
        extra_charts = generated_charts.get(first_name, [])[6:]
        if extra_charts:
            _draw_chart(c, extra_charts[0], MARGIN, 470, 265, 170)
        if len(extra_charts) > 1:
            _draw_chart(c, extra_charts[1], MARGIN + 280, 470, 265, 170)
        if len(extra_charts) > 2:
            _draw_chart(c, extra_charts[2], MARGIN, 285, 265, 170)
        if len(extra_charts) > 3:
            _draw_chart(c, extra_charts[3], MARGIN + 280, 285, 265, 170)
        table_rows = _summary_table_data(first_df, first_kind)
        if table_rows:
            _draw_text(c, f"{first_kind.title()} Summary - {first_name}", MARGIN, 255, 10, TEXT, "Helvetica-Bold")
            headers = ["Segment", "Metric A", "Metric B", "Rate / Coverage"]
            _draw_table(c, MARGIN, 155, PAGE_W - 2 * MARGIN, 22, headers, table_rows[:4], widths=[140, 120, 120, 125], accent=BLUE)
        _draw_recommendation_grid(c, _recommendations_for_dataset(first_df, first_kind), MARGIN, 18, PAGE_W - 2 * MARGIN, 140)
        c.showPage()

    if multi:
        _header(c, "Overall Business View", "Portfolio summary", 4, total_pages)
        y = 700
        for name, df in non_empty.items():
            kind = _detect_type(df)
            _draw_text(c, name, MARGIN, y, 11, TEXT, "Helvetica-Bold")
            _draw_text(c, f"{kind.title()} dataset · {len(df):,} records · {len(df.columns):,} columns", MARGIN, y - 15, 8, MUTED)
            y -= 38
            fs = _findings_for_dataset(name, df)
            for finding in fs[:3]:
                c.setFillColor(CYAN)
                c.circle(MARGIN + 5, y + 2, 2, fill=1, stroke=0)
                y = _draw_wrapped(c, finding, MARGIN + 15, y, PAGE_W - 2 * MARGIN - 20, size=8.5, leading=11, color=TEXT, max_lines=2) - 10
            # small summary table
            rows = _summary_table_data(df, kind)
            if rows:
                _draw_table(c, MARGIN, y - 120, PAGE_W - 2 * MARGIN, 23, ["Segment", "Metric A", "Metric B", "Rate / Coverage"], rows[:4], widths=[160, 120, 120, 95], accent=TEAL)
                y -= 150
            else:
                y -= 20
            if y < 260:
                break
        _draw_recommendation_grid(c, _recommendations_for_dataset(first_df, _detect_type(first_df)) + (_recommendations_for_dataset(second_df, _detect_type(second_df)) if len(non_empty) > 1 else []), MARGIN, 55, PAGE_W - 2 * MARGIN, 165)
        c.showPage()

    c.save()
    return str(output_path)
