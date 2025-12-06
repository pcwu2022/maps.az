# World Choropleth Generator
# World Choropleth Generator

Small utility to generate choropleth maps for world countries from a CSV file.

**Quick start**

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Prepare a CSV with one row per country. Example files are under `inputs/`.

CSV requirements:
- A column with country names or ISO codes.
- A numeric column containing the value to plot (e.g. GDP per capita, score). By default the script looks for a `value` column.
- You can provide an ISO column (alpha-3 or alpha-2) named e.g. `country_ISO` to avoid name lookup.

Files and helper runner
- `generate_choropleth.py` — main script. Key CLI options:
	- `--iso-col`: column containing ISO codes (preferred)
	- `--country-col`: column containing country names (used if no ISO column)
	- `--value-col`: numeric column to plot (default detected as `value`)
	- `--colormap`: matplotlib colormap name for the static plot (e.g. `OrRd`, `viridis`)
	- `--title`: title template; use `{value_col}` to insert the column name (omit to have no title)
	- `--interactive`: also generate a `folium` HTML map

- `run.sh` — small bash runner. Call it with a base name (looks for `inputs/<name>.csv`) and it will write `outputs/<name>.png` (and `.html` if `--interactive` used):

```bash
bash run.sh punctuality --title "Punctuality"
```

This runs `generate_choropleth.py inputs/punctuality.csv --iso-col country_ISO --value-col value --output-prefix outputs/punctuality`.

Appearance details
- The static PNG uses a compact, full-figure world map and a small overlaid horizontal colorbar placed low over the map (lower-centre) so the map area is maximized.
- The colorbar is semi-transparent and by default shows no label (so it doesn't display the raw column name). You can change appearance with `--colormap` and the top-level config variables in the script.

Outputs
- `outputs/<name>.png` — static image
- `outputs/<name>.html` — interactive map (only if `--interactive` is passed)

Notes and troubleshooting
- The script uses `pycountry` to map country names to ISO3 codes when an ISO column isn't provided. Some unusual names may not map; those rows are skipped with a warning.
- GeoPandas dataset loading: newer GeoPandas versions may not expose the built-in Natural Earth dataset; the script falls back to a remote Natural Earth shapefile if needed (internet access required).
- If you want different colorbar placement or size, ask and I can add CLI flags to control `cbar` width/height/position and opacity.

If you want, I can add example automation, CI, or extra CLI flags for finer layout control.
