#!/usr/bin/env python3
"""Generate interactive HTML pages from `interactive.json`.

This script reads `interactive.json`, invokes `generate_choropleth.py` for
each map entry with `--interactive`, and writes the HTML pages into `pages/`.

Usage:
  python3 generate_pages.py --config interactive.json

Requirements: `generate_choropleth.py` in the same folder, and optional
`folium` for interactive maps.
"""
import argparse
import json
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))


def run_map(map_cfg, inputs_dir, pages_dir):
    map_id = map_cfg.get('id') or os.path.splitext(map_cfg.get('csv', ''))[0]
    csv = map_cfg.get('csv')
    if not csv:
        print(f"Skipping map with no csv: {map_cfg}")
        return False
    csv_path = os.path.join(inputs_dir, csv)
    if not os.path.exists(csv_path):
        print(f"Warning: CSV not found, skipping: {csv_path}")
        return False

    os.makedirs(pages_dir, exist_ok=True)
    out_prefix = os.path.join(pages_dir, map_id)

    cmd = [sys.executable, os.path.join(ROOT, 'generate_choropleth.py'), csv_path]
    # value column (required)
    value_col = map_cfg.get('value_col')
    if value_col:
        cmd += ['--value-col', value_col]
    # optional iso column
    iso_col = map_cfg.get('iso_col')
    if iso_col:
        cmd += ['--iso-col', iso_col]
    # interactive output prefix
    cmd += ['--interactive', '--output-prefix', out_prefix]
    # colormap
    if 'colormap' in map_cfg and map_cfg['colormap']:
        cmd += ['--colormap', str(map_cfg['colormap'])]
    # title
    if 'title' in map_cfg and map_cfg['title']:
        cmd += ['--title', str(map_cfg['title'])]

    print('Running:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print('Error generating map', map_id, e)
        return False


def main():
    p = argparse.ArgumentParser(description='Generate interactive pages from interactive.json')
    p.add_argument('--config', default=os.path.join(ROOT, 'interactive.json'), help='Path to interactive.json')
    p.add_argument('--inputs', default=os.path.join(ROOT, 'inputs'), help='Inputs directory')
    p.add_argument('--pages', default=os.path.join(ROOT, 'pages'), help='Output pages directory')
    args = p.parse_args()

    if not os.path.exists(args.config):
        print('Config not found:', args.config)
        sys.exit(2)

    with open(args.config, 'r', encoding='utf8') as f:
        cfg = json.load(f)

    maps = cfg.get('maps') or []
    if not maps:
        print('No maps defined in config (maps array is empty).')
        sys.exit(0)

    total = len(maps)
    ok = 0
    for m in maps:
        print('\n=== Generating', m.get('id') or m.get('csv'), '===')
        if run_map(m, args.inputs, args.pages):
            ok += 1

    print(f'\nFinished: generated {ok}/{total} interactive pages in {args.pages}')


if __name__ == '__main__':
    main()
