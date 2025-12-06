#!/usr/bin/env python3
"""Generate choropleth maps for world countries from a CSV.

Usage examples:
  python3 generate_choropleth.py sample_data.csv --country-col country --value-col value
  python3 generate_choropleth.py sample_data.csv --country-col country --value-col value --interactive

The script tries to map country names to ISO3 codes using `pycountry` and
merges with the built-in Natural Earth world dataset from `geopandas`.
"""
import argparse
import os
import sys

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.colors import LinearSegmentedColormap

try:
    import pycountry
except Exception:
    pycountry = None

try:
    import folium
except Exception:
    folium = None
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    Image = None
    PIL_AVAILABLE = False

# Watermark path (relative to this script). If the file exists, it will be
# overlaid centered on every generated PNG. Set to None to disable.
DEFAULT_WATERMARK = os.path.join(os.path.dirname(__file__), 'assets', 'watermark.png')

# == Configuration (tweak these at the top of the file) ==
# Colormap for static matplotlib plot (common matplotlib colormap name)
# DEFAULT_COLORMAP = LinearSegmentedColormap.from_list("custom_red_green", ["red", "green"])
DEFAULT_COLORMAP = 'RdYlGn'
# Colormap / fill color for interactive folium map
DEFAULT_INTERACTIVE_COLORMAP = 'YlOrRd'
# Title template for plots; can include `{value_col}` to insert the column name
# Empty string means no title by default
DEFAULT_TITLE_TEMPLATE = ''
# Figure size for static plots (width, height)
DEFAULT_FIGSIZE = (14, 8)
# Color to use for missing / NaN countries
DEFAULT_MISSING_COLOR = 'lightgrey'
# Output DPI for saved PNGs
DEFAULT_DPI = 150
# =====================================================


def map_name_to_iso3(name):
    if not isinstance(name, str):
        return None
    s = name.strip()
    if len(s) == 3 and s.isalpha():
        return s.upper()
    if pycountry is None:
        return None
    try:
        c = pycountry.countries.lookup(s)
        return c.alpha_3
    except Exception:
        return None


def auto_detect_columns(df):
    # common names
    country_candidates = [c for c in df.columns if c.lower() in ("country", "country_name", "name", "nation")]
    value_candidates = [c for c in df.columns if c.lower() in ("value", "val", "metric", "score")]
    # detect ISO-ish columns
    iso_candidates = [c for c in df.columns if c.lower() in ("iso", "iso3", "iso_a3", "country_iso", "country_iso3", "country_iso_a3", "country_iso_code")]
    return (country_candidates[0] if country_candidates else None,
            value_candidates[0] if value_candidates else None,
            iso_candidates[0] if iso_candidates else None)


def _clean_iso_code(code):
    if not isinstance(code, str):
        return None
    s = code.strip()
    if len(s) == 3 and s.isalpha():
        return s.upper()
    if len(s) == 2 and pycountry is not None:
        try:
            c = pycountry.countries.get(alpha_2=s.upper())
            return c.alpha_3
        except Exception:
            return None
    return None


def load_and_prepare(csv_path, country_col, value_col, iso_col=None):
    df = pd.read_csv(csv_path)
    if country_col is None or value_col is None or iso_col is None:
        detected_country, detected_value, detected_iso = auto_detect_columns(df)
        country_col = country_col or detected_country
        value_col = value_col or detected_value
        iso_col = iso_col or detected_iso

    if value_col is None:
        print("Error: couldn't detect value column. Please pass --value-col.")
        print("Available columns:", list(df.columns))
        sys.exit(1)

    # If an ISO column is provided/detected, prefer it (faster, more reliable)
    if iso_col is not None and iso_col in df.columns:
        df[iso_col] = df[iso_col].astype(str)
        df['iso_a3'] = df[iso_col].map(_clean_iso_code)
        missing_iso = df['iso_a3'].isna().sum()
        if missing_iso:
            print(f"Warning: {missing_iso} rows in '{iso_col}' couldn't be interpreted as ISO3. They will be skipped.")
    else:
        if country_col is None:
            print("Error: couldn't detect country column or ISO column. Please pass --country-col or --iso-col.")
            print("Available columns:", list(df.columns))
            sys.exit(1)
        df[country_col] = df[country_col].astype(str)
        df['iso_a3'] = df[country_col].map(map_name_to_iso3)
        missing_iso = df['iso_a3'].isna().sum()
        if missing_iso:
            print(f"Warning: {missing_iso} rows couldn't be mapped to ISO3 codes. They will be skipped.")

    df = df.dropna(subset=['iso_a3'])
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
    return df[['iso_a3', value_col]]


def generate_static_map(merged_gdf, value_col, out_png,
                        colormap=DEFAULT_COLORMAP,
                        title_template=DEFAULT_TITLE_TEMPLATE,
                        figsize=DEFAULT_FIGSIZE,
                        missing_color=DEFAULT_MISSING_COLOR,
                        dpi=DEFAULT_DPI):
    # Create a figure and place main map axes to fill the figure with a small
    # reserved space at the bottom for the horizontal colorbar.
    fig = plt.figure(figsize=figsize)
    # Axes for the map: [left, bottom, width, height] in figure coordinates.
    map_ax = fig.add_axes([0.0, 0.06, 1.0, 0.94])

    # Determine vmin/vmax from merged data (ignore NaNs)
    try:
        vmin = merged_gdf[value_col].min()
        vmax = merged_gdf[value_col].max()
    except Exception:
        vmin = None
        vmax = None

    plot_kwargs = dict(column=value_col, cmap=colormap, linewidth=0.2, ax=map_ax,
                       edgecolor='0.6', legend=False,
                       missing_kwds={'color': missing_color})
    if vmin is not None and vmax is not None:
        plot_kwargs.update(dict(vmin=vmin, vmax=vmax))

    merged_gdf.plot(**plot_kwargs)
    map_ax.set_axis_off()

    # Only add title if user provided one
    if title_template:
        title = title_template.format(value_col=value_col)
        map_ax.set_title(title, fontdict={'fontsize': 16}, pad=6)

    # Add a narrow horizontal colorbar overlaid inside the map axes (lower-center)
    if vmin is not None and vmax is not None:
        cmap_obj = plt.cm.get_cmap(colormap)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
        sm._A = []  # required for matplotlib < 3.5 compatibility

        # Create an inset axes inside the main map axes. width/height can be
        # specified as percent strings to keep it responsive to figure size.
        # We'll place it near the lower center; this typically overlays over
        # the bottom of Africa on the world map projection.
        try:
            cax = inset_axes(map_ax, width="25%", height="2.5%", loc='lower center', borderpad=0.2)
        except Exception:
            # Fallback to a small axes in figure coords
            cax = fig.add_axes([0.37, 0.04, 0.26, 0.03])

        # Make the colorbar semi-transparent so underlying map features remain visible
        cbar = fig.colorbar(sm, cax=cax, orientation='horizontal')
        cbar.ax.patch.set_alpha(0.7)

    # Ensure the figure renderer is initialized (required when using inset_axes)
    try:
        fig.canvas.draw()
    except Exception:
        pass

    # Save with minimal padding to maximize map area. Avoid `bbox_inches='tight'`
    # because inset_axes can cause issues with tight bbox calculations on
    # some backends; using `bbox_inches=None` and `pad_inches=0` produces a
    # full-figure image with minimal margins.
    fig.savefig(out_png, dpi=dpi, bbox_inches=None, pad_inches=0)
    print(f"Saved static map to {out_png}")

    # If a watermark image exists, try to overlay it centered on the PNG.
    try:
        wm_path = DEFAULT_WATERMARK
        if wm_path and os.path.exists(wm_path) and PIL_AVAILABLE:
            try:
                bg = Image.open(out_png).convert('RGBA')
                wm = Image.open(wm_path).convert('RGBA')
                bw, bh = bg.size
                ww, wh = wm.size
                # scale watermark if it's wider than 30% of background width
                max_w = int(bw * 0.30)
                if ww > max_w:
                    scale = max_w / ww
                    new_w = max(1, int(ww * scale))
                    new_h = max(1, int(wh * scale))
                    wm = wm.resize((new_w, new_h), resample=Image.LANCZOS)
                    ww, wh = wm.size

                # position centered
                pos = ((bw - ww) // 2, (bh - wh) // 2)
                bg.paste(wm, pos, wm)
                bg.save(out_png)
                print(f"Applied watermark from {wm_path} to {out_png}")
            except Exception as e:
                print(f"Warning: failed to apply watermark: {e}")
        elif wm_path and os.path.exists(wm_path) and not PIL_AVAILABLE:
            print("Notice: watermark present but Pillow is not installed; install pillow to enable watermarking.")
    except Exception:
        pass


def generate_interactive_map(merged_gdf, value_col, out_html, fill_color=DEFAULT_INTERACTIVE_COLORMAP, missing_color=DEFAULT_MISSING_COLOR):
    if folium is None:
        print("Folium not installed; cannot create interactive map. Install folium and try again.")
        return
    geojson = merged_gdf.to_json()
    m = folium.Map(location=[10, 0], zoom_start=2, tiles='CartoDB positron')
    folium.Choropleth(
        geo_data=geojson,
        name='choropleth',
        data=merged_gdf,
        columns=['iso_a3', value_col],
        key_on='feature.properties.iso_a3',
        fill_color=fill_color,
        nan_fill_color=missing_color,
        legend_name=value_col,
    ).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(out_html)
    print(f"Saved interactive map to {out_html}")


def main():
    p = argparse.ArgumentParser(description='Generate world choropleth from CSV')
    p.add_argument('csv', help='Path to CSV file (country-level)')
    p.add_argument('--country-col', help='Country column name in CSV')
    p.add_argument('--iso-col', help='ISO (alpha-3 or alpha-2) column name in CSV (preferred)')
    p.add_argument('--value-col', help='Numeric value column to plot')
    p.add_argument('--output-prefix', default='outputs/choropleth', help='Output path prefix (no extension)')
    p.add_argument('--interactive', action='store_true', help='Also generate interactive HTML map using folium')
    p.add_argument('--colormap', help=f"Matplotlib colormap for static plot (default: {DEFAULT_COLORMAP})")
    p.add_argument('--title', help=f"Title template for static plot; use '{{value_col}}' to insert column name (default: '{DEFAULT_TITLE_TEMPLATE}')")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.output_prefix), exist_ok=True)

    df = load_and_prepare(args.csv, args.country_col, args.value_col, args.iso_col)

    try:
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    except Exception:
        # Newer geopandas versions removed the built-in datasets helper.
        # Fall back to downloading Natural Earth countries (110m) from the S3 mirror.
        try:
            world = gpd.read_file("https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")
        except Exception as e:
            print("Error: couldn't load Natural Earth dataset via geopandas.\n", e)
            print("If you're offline or behind a firewall, download the Natural Earth countries shapefile and pass its path." )
            sys.exit(1)

    # Normalize common ISO column names to `iso_a3` so merging is consistent.
    # Natural Earth has several ISO-like columns; some (like `ISO_A3`) may
    # contain sentinel values such as '-99'. Prefer the candidate column that
    # contains the most valid 3-letter alpha codes (e.g. 'FRA', 'NOR').
    def choose_iso_column(gdf):
        candidates = [c for c in gdf.columns if c.lower() in (
            'iso_a3', 'iso3', 'iso', 'adm0_a3')]
        # also include uppercase variants if present
        if not candidates:
            candidates = [c for c in gdf.columns if c.upper() in ('ISO_A3', 'ADM0_A3', 'ISO3')]
        if not candidates:
            return None

        def score_col(col):
            vals = gdf[col].dropna().astype(str).str.strip()
            # count entries that look like valid alpha-3 codes (3 letters, not '-99'/'0')
            good = vals[vals.str.len() == 3]
            good = good[good.str.isalpha()]
            good = good[~good.isin(['-99', '0'])]
            return len(good)

        scored = [(score_col(c), c) for c in candidates]
        # pick candidate with highest score
        scored.sort(reverse=True)
        best_score, best_col = scored[0]
        if best_score == 0:
            return None
        return best_col

    chosen = choose_iso_column(world)
    if chosen is None:
        print("Error: couldn't find an ISO3-like column in the Natural Earth dataset. Columns:", list(world.columns))
        sys.exit(1)
    if chosen != 'iso_a3':
        world = world.rename(columns={chosen: 'iso_a3'})

    # Normalize values in the Natural Earth ISO column to uppercase 3-letter codes and set invalids to None
    def _normalize_world_iso(code):
        try:
            if code is None:
                return None
            s = str(code).strip()
            if not s or s in ('-99', '0'):
                return None
            if len(s) == 3:
                return s.upper()
            return s.upper()
        except Exception:
            return None

    world['iso_a3'] = world['iso_a3'].map(_normalize_world_iso)

    # Merge data onto world geometries using `iso_a3` keys
    merged = world.merge(df, how='left', left_on='iso_a3', right_on='iso_a3')

    # Debugging output to help explain map results
    try:
        valname = args.value_col
    except Exception:
        valname = None
    print(f"Input rows: {len(df)}; unique ISO codes in input: {df['iso_a3'].nunique()}")
    if valname and valname in df.columns:
        try:
            vmin = df[valname].min()
            vmax = df[valname].max()
            print(f"Value column '{valname}': min={vmin}, max={vmax}")
        except Exception:
            pass
    matched = merged[valname].notna().sum() if valname and valname in merged.columns else merged['iso_a3'].notna().sum()
    print(f"World rows: {len(world)}; matched rows after merge (non-null '{valname}'): {matched}")

    out_png = args.output_prefix + '.png'
    colormap = args.colormap or DEFAULT_COLORMAP
    title_template = args.title or DEFAULT_TITLE_TEMPLATE
    generate_static_map(merged, args.value_col, out_png, colormap=colormap, title_template=title_template)

    if args.interactive:
        out_html = args.output_prefix + '.html'
        generate_interactive_map(merged, args.value_col, out_html, fill_color=colormap)


if __name__ == '__main__':
    main()
