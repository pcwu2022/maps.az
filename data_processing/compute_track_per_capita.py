#!/usr/bin/env python3
import csv
import re
import pycountry
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACK_FILE = ROOT / 'data_processing' / 'track_length.csv'
POP_FILE = ROOT / 'data_processing' / 'World Population by country 2024.csv'
OUT_FILE = ROOT / 'inputs' / 'track_length_per_capita_iso3.csv'
SCALE = 1000  # multiply km-per-person by this factor


def numeric_to_alpha3(numeric_code: str) -> str:
    """Convert numeric ISO code (e.g. '380' or '084') to alpha_3 (e.g. 'ITA')."""
    if not numeric_code:
        return ''
    code = re.sub(r"[^0-9]", "", numeric_code).zfill(3)
    try:
        c = pycountry.countries.get(numeric=code)
        if c and getattr(c, 'alpha_3', None):
            return c.alpha_3
    except Exception:
        pass
    return ''


def norm_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\'\"\,\.]", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def load_population(path):
    pop = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            country = r.get('Country') or r.get('country')
            popstr = r.get('Population 2024') or r.get('Population')
            if not country or not popstr:
                continue
            try:
                # remove commas and non-digits
                p = int(re.sub(r"[^0-9]", "", popstr))
            except Exception:
                continue
            pop[norm_name(country)] = p
    return pop


def main():
    pop_map = load_population(POP_FILE)

    # small manual alias mappings for names that differ between files
    alias = {
        'congo': 'republic of the congo',
        'dr congo': 'dr congo',
        'ivory coast': 'ivory coast',
        'south korea': 'south korea',
        'north korea': 'north korea',
        'united states': 'united states',
    }

    rows = []
    unmatched = []
    with open(TRACK_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            if not r:
                continue
            # Expect: country, country_iso, track_length
            if len(r) < 3:
                continue
            country_raw = r[0].strip()
            iso_raw = r[1].strip()
            track_raw = r[2].strip()
            try:
                track = float(re.sub(r"[^0-9.]", "", track_raw))
            except Exception:
                track = 0.0

            cname_norm = norm_name(country_raw)
            pop = None
            if cname_norm in pop_map:
                pop = pop_map[cname_norm]
            else:
                # try aliases
                if cname_norm in alias and alias[cname_norm] in pop_map:
                    pop = pop_map[alias[cname_norm]]
                else:
                    # try fuzzy substring match: find pop key that contains country token
                    for k in pop_map.keys():
                        if cname_norm in k or k in cname_norm:
                            pop = pop_map[k]
                            break

            if pop is None or pop == 0:
                unmatched.append(country_raw)
                continue

            value = (track / pop) * SCALE
            iso3 = numeric_to_alpha3(iso_raw)
            rows.append((country_raw, iso3 or iso_raw, value))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out)
        w.writerow(['country', 'country_ISO', 'value'])
        for country, iso, value in rows:
            w.writerow([country, iso, f"{value:.12f}"])

    if unmatched:
        import sys
        print('Warning: unmatched countries (skipped):', file=sys.stderr)
        for u in unmatched:
            print('-', u, file=sys.stderr)


if __name__ == '__main__':
    import sys
    main()
