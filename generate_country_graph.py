#!/usr/bin/env python3
"""
Generate a directed country graph from a CSV and render nodes masked with flags.

Usage: python generate_country_graph.py

Constants at top of file:
- INPUT_CSV: path to CSV (three columns: country,country_ISO,other_country_ISO)
- SHOW_LABELS: True/False to show country name text below nodes
"""
import os
import io
import math
import argparse
from collections import defaultdict

import pandas as pd
import numpy as np

try:
    import networkx as nx
except Exception:
    raise SystemExit("networkx is required. Install with: pip install networkx")

try:
    import matplotlib.pyplot as plt
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
except Exception:
    raise SystemExit("matplotlib is required. Install with: pip install matplotlib")

try:
    import pycountry
except Exception:
    raise SystemExit("pycountry is required. Install with: pip install pycountry")

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image, ImageOps
except Exception:
    raise SystemExit("Pillow is required. Install with: pip install pillow")

# ========== User-configurable constants ==========
# Default input CSV (used when CLI not provided)
INPUT_CSV = os.path.join("inputs", "sample_graph_input.csv")
# Default output PNG directory/filename (if CLI not provided, we infer from input)
OUTPUT_PNG = os.path.join("outputs", "country_graph.png")
# Show country name text under nodes (not inside the flag circle)
SHOW_LABELS = True
# Size multiplier for node images
SIZE_SCALE = 500
# Flag CDN URL template (expects alpha-2 lower-case code)
FLAG_URL = "https://flagcdn.com/w320/{code}.png"
# Local cache directory for downloaded flags (improves reliability)
FLAGS_CACHE_DIR = os.path.join("outputs", "flags")
# ==================================================


def iso3_to_iso2(iso3):
    if not isinstance(iso3, str):
        return None
    iso3 = iso3.strip().upper()
    try:
        c = pycountry.countries.get(alpha_3=iso3)
        if c:
            return c.alpha_2.lower()
    except Exception:
        pass
    return None


def iso3_to_name(iso3):
    """Return a human-readable country name for a given ISO3 code, or None."""
    if not isinstance(iso3, str):
        return None
    iso3 = iso3.strip().upper()
    try:
        c = pycountry.countries.get(alpha_3=iso3)
        if c:
            # prefer common_name if available, otherwise name
            return getattr(c, "common_name", None) or getattr(c, "name", None)
    except Exception:
        pass
    return None


def fetch_flag_image(alpha2):
    """Return a PIL Image for alpha2 code or None if failed."""
    if not alpha2:
        return None
    os.makedirs(FLAGS_CACHE_DIR, exist_ok=True)
    filename = f"{alpha2.lower()}.png"
    cache_path = os.path.join(FLAGS_CACHE_DIR, filename)
    # Return cached file if present
    if os.path.exists(cache_path):
        try:
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            # corrupted cache -> remove and retry download
            try:
                os.remove(cache_path)
            except Exception:
                pass

    url = FLAG_URL.format(code=alpha2.lower())
    # Try downloading with retries to mitigate transient network issues
    attempts = 3
    for attempt in range(attempts):
        try:
            if requests:
                r = requests.get(url, timeout=12)
                r.raise_for_status()
                with open(cache_path, "wb") as fh:
                    fh.write(r.content)
                return Image.open(cache_path).convert("RGBA")
            else:
                from urllib.request import urlopen

                data = urlopen(url, timeout=12).read()
                with open(cache_path, "wb") as fh:
                    fh.write(data)
                return Image.open(cache_path).convert("RGBA")
        except Exception:
            # on final attempt, give up and return None
            if attempt == attempts - 1:
                return None
            # otherwise, wait a bit and retry
            import time

            time.sleep(1 + attempt * 0.5)


def make_circular_mask(image, size_px):
    """Resize image to (size_px,size_px) and mask to a circle (RGBA)."""
    img = image.resize((size_px, size_px), Image.LANCZOS)
    mask = Image.new("L", (size_px, size_px), 0)
    draw = Image.new("L", (size_px, size_px), 0)
    # create circular mask using ImageOps.fit trick
    mask = Image.new("L", (size_px, size_px), 0)
    ImageOps.expand(mask)
    # draw circle by using a high-contrast alpha composite
    circle = Image.new("L", (size_px, size_px), 0)
    from PIL import ImageDraw

    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, size_px - 1, size_px - 1), fill=255)
    result = Image.new("RGBA", (size_px, size_px))
    result.paste(img, (0, 0), circle)
    return result


def build_graph(df):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        a_name = row.get("country") if isinstance(row, dict) else row["country"]
        a_iso3 = str(row["country_ISO"]).strip().upper()
        b_iso3 = str(row["other_country_ISO"]).strip().upper()

        if not a_iso3:
            continue
        if not G.has_node(a_iso3):
            G.add_node(a_iso3, name=a_name, iso3=a_iso3)
        # ensure target exists as node (may be missing name)
        if not G.has_node(b_iso3):
            # try to map ISO3 to a readable country name; fall back to ISO3 code
            b_name = iso3_to_name(b_iso3) or b_iso3
            G.add_node(b_iso3, name=b_name, iso3=b_iso3)
        G.add_edge(a_iso3, b_iso3)
    return G


def compute_node_sizes(G, scale=SIZE_SCALE):
    """Return per-node diameter in pixels (int).

    Smaller defaults than before; sizes scale with in-degree but are
    clamped to a reasonable pixel range so nodes are not overwhelming.
    """
    in_deg = dict(G.in_degree())
    sizes = {}
    for n in G.nodes():
        deg = in_deg.get(n, 0)
        # base diameter plus a step per incoming edge
        base = 28
        step = 14
        diameter = int(base + step * deg)
        # clamp
        diameter = max(24, min(diameter, 90))
        sizes[n] = diameter
    return sizes


def initial_positions_by_size(sizes):
    # place larger nodes nearer center: sort nodes by size
    nodes_sorted = sorted(sizes.items(), key=lambda x: x[1], reverse=True)
    positions = {}
    # concentric rings: biggest few near center, others arranged in rings
    ring_index = 0
    ring_counts = [3, 8, 16, 32]
    idx = 0
    placed = 0
    for n, s in nodes_sorted:
        # decide ring
        while idx >= sum(ring_counts[: ring_index + 1]):
            ring_index += 1
            if ring_index >= len(ring_counts):
                ring_counts.append(ring_counts[-1] * 2)
        # angle based on placed count within ring
        count_in_ring = ring_counts[ring_index]
        pos_in_ring = placed - (sum(ring_counts[:ring_index]) if ring_index > 0 else 0)
        angle = 2 * math.pi * (pos_in_ring / max(1, count_in_ring))
        radius = 0.12 * (ring_index + 1)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions[n] = (x, y)
        placed += 1
        idx += 1
    return positions


def render_graph(G, sizes, flags, out_png=OUTPUT_PNG, show_labels=SHOW_LABELS):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_facecolor("white")
    ax.axis("off")

    # initial pos biased by size
    init_pos = initial_positions_by_size(sizes)
    # spring layout refinement
    # choose k to spread nodes more and avoid overlaps; scale with graph size
    avg_size = float(sum(sizes.values()) / max(1, len(sizes)))
    # larger avg_size -> slightly larger desired spacing; also use node count
    k = 0.9 * math.sqrt(avg_size) / max(1.0, math.sqrt(len(G)))
    pos = nx.spring_layout(G, pos=init_pos, iterations=500, k=k, seed=42)

    # Compute axis limits from positions and apply a margin so the whole
    # layout is visible (prevents Matplotlib from showing only a corner).
    try:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        xpad = max((xmax - xmin) * 0.35, 0.15)
        ypad = max((ymax - ymin) * 0.35, 0.15)
        ax.set_xlim(xmin - xpad, xmax + xpad)
        ax.set_ylim(ymin - ypad, ymax + ypad)
        ax.set_aspect('equal', adjustable='datalim')
    except Exception:
        pass

    # Draw edges as FancyArrowPatch objects so they stop at the node
    # circumferences (using shrinkA/shrinkB). This ensures edges remain
    # visible even when nodes overlap slightly.
    from matplotlib.patches import FancyArrowPatch

    EDGE_COLOR = "#555555"
    EDGE_ALPHA = 0.95
    EDGE_WIDTH = 2.2
    # Fraction of the edge vector to trim from each end (in addition to shrinkA/B)
    EDGE_SHORTEN_FRAC = 0.10
    for u, v in G.edges():
        src = pos[u]
        dst = pos[v]
        # shorten the edge slightly so it doesn't span full center-to-center
        dx = dst[0] - src[0]
        dy = dst[1] - src[1]
        dist = math.hypot(dx, dy)
        if dist > 1e-12:
            ux = dx / dist
            uy = dy / dist
            trim = EDGE_SHORTEN_FRAC * dist
            new_src = (src[0] + ux * trim, src[1] + uy * trim)
            new_dst = (dst[0] - ux * trim, dst[1] - uy * trim)
        else:
            new_src = src
            new_dst = dst
        # compute shrink in points so arrow doesn't draw under the circle
        fig_dpi = fig.dpi if hasattr(fig, 'dpi') else 150.0
        src_radius_px = sizes.get(u, 32) / 2.0
        dst_radius_px = sizes.get(v, 32) / 2.0
        # convert pixels -> points (1 point = 1/72 inch); points = px * 72 / dpi
        shrinkA = src_radius_px * 72.0 / float(fig_dpi)
        shrinkB = dst_radius_px * 72.0 / float(fig_dpi)
        arrow = FancyArrowPatch(
            new_src,
            new_dst,
            arrowstyle='-|>',
            linewidth=EDGE_WIDTH,
            color=EDGE_COLOR,
            alpha=EDGE_ALPHA,
            shrinkA=shrinkA,
            shrinkB=shrinkB,
            mutation_scale=12,
            connectionstyle='arc3,rad=0.06',
        )
        arrow.set_zorder(1.5)
        ax.add_patch(arrow)

    # Diagnostic: print node/size/position summaries to help debug layout
    try:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        print(f"Nodes: {len(G.nodes())}, Edges: {len(G.edges())}")
        print(f"Size px: min={min(sizes.values()):.1f}, max={max(sizes.values()):.1f}")
        print(f"Position x: min={min(xs):.4f}, max={max(xs):.4f}")
        print(f"Position y: min={min(ys):.4f}, max={max(ys):.4f}")
    except Exception:
        pass

    # Ensure renderer/transforms are initialized before transforming
    try:
        fig.canvas.draw()
    except Exception:
        pass

    # Draw nodes as images using ax.imshow with extents computed in data
    # coordinates for robust placement (avoids AnnotationBbox quirks).
    text_margin_px = 6  # pixels between circumference and text baseline
    missing_flags = []
    for node, (x, y) in pos.items():
        pixel_size = int(sizes.get(node, 32))
        img = flags.get(node)
        radius_px = pixel_size / 2.0
        if img is not None:
            try:
                circ = make_circular_mask(img, pixel_size)
                arr = np.asarray(circ)
                # Use OffsetImage + AnnotationBbox to place image with consistent
                # pixel size. Since `circ` is already sized to pixel_size, use
                # zoom=1 so it renders at that size in display coords.
                im = OffsetImage(arr, zoom=1)
                ab = AnnotationBbox(im, (x, y), frameon=False, pad=0)
                ab.set_zorder(3)
                ax.add_artist(ab)
            except Exception:
                missing_flags.append(node)
                r = 0.02 + pixel_size / 400.0
                circ = plt.Circle((x, y), r, color="#cccccc", ec="#333333")
                circ.set_zorder(3)
                ax.add_artist(circ)
        

        if show_labels:
            lab = G.nodes[node].get("display_name", G.nodes[node].get("name", node))
            # Convert node center from data -> display (pixels)
            disp_xy = ax.transData.transform((x, y))
            # compute text baseline Y in display coords: move down by radius + margin
            text_y_disp = disp_xy[1] - (radius_px + text_margin_px)
            # convert back to data coords
            text_data = ax.transData.inverted().transform((disp_xy[0], text_y_disp))
            ax.text(text_data[0], text_data[1], lab, ha="center", va="top", fontsize=12, zorder=4)

    if missing_flags:
        print(f"Warning: flags missing for {len(missing_flags)} nodes: {missing_flags}")

    # Avoid `tight` bbox to prevent renderer issues when artists have
    # large or unusual extents; save full-figure image with minimal padding.
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png, dpi=150, bbox_inches=None, pad_inches=0)
    print(f"Saved graph image to: {out_png}")


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate directed country graph from CSV')
    parser.add_argument('csv', help='Path to CSV file (three columns: country,country_ISO,other_country_ISO)')
    parser.add_argument('--output', help='Output PNG file path (defaults to outputs/<csv_basename>.png)')
    parser.add_argument('--labels', action='store_true', help='Show country name labels below nodes')
    args = parser.parse_args(argv)

    input_path = args.csv
    # If user provided a relative path and it looks like a bare filename, prefer inputs/ folder
    if not os.path.isabs(input_path) and not input_path.startswith('inputs' + os.sep):
        candidate = os.path.join('inputs', input_path)
        if os.path.exists(candidate):
            input_path = candidate
    # If still relative, keep as-is (user may pass a path)

    # Infer output filename if not provided
    if args.output:
        output_path = args.output
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join('outputs', f"{base_name}.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = pd.read_csv(input_path)
    G = build_graph(df)
    sizes = compute_node_sizes(G)

    # Fetch flags (cache on disk) and compute display names
    flags = {}
    for n in G.nodes():
        iso3 = G.nodes[n].get('iso3')
        alpha2 = iso3_to_iso2(iso3)
        img = None
        if alpha2:
            img = fetch_flag_image(alpha2)
        flags[n] = img
        # compute display name: prefer provided name if it's not the ISO code,
        # otherwise try to map ISO3 -> proper country name
        name = G.nodes[n].get('name')
        if not name or (isinstance(name, str) and name.strip().upper() == (iso3 or "")):
            display = iso3_to_name(iso3) or iso3
        else:
            display = name
        G.nodes[n]['display_name'] = display

    render_graph(G, sizes, flags, out_png=output_path, show_labels=args.labels or SHOW_LABELS)


if __name__ == "__main__":
    main()
