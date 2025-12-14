#!/usr/bin/env python3
import csv
import re
from pathlib import Path
import pycountry

ROOT = Path(__file__).resolve().parent.parent
TRACK_FILE = ROOT / 'data_processing' / 'track_length.csv'
POP_FILE = ROOT / 'data_processing' / 'World Population by country 2024.csv'
OUT_FILE = ROOT / 'inputs' / 'track_length_per_area_iso3.csv'


def norm_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\'\"\,\.]", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_area(area_raw: str):
    if area_raw is None:
        return None
    s = str(area_raw).strip()
    if s == '' or s.lower() in ('nan',):
        return None
    # convert formats like '3M', '364.5K', '9.4M', '< 1', '130.2K'
    s = s.replace('\u202f', '')  # thin space
    s = s.replace(',', '')
    s = s.replace('\u2009', '')
    # handle '< 1' -> 1
    s = s.replace('<', '').strip()
    m = re.match(r'^([0-9]*\.?[0-9]+)\s*([kKmM]?)$', s)
    if not m:
        # fallback: strip non-digits
        digits = re.sub(r'[^0-9.]', '', s)
        if digits == '':
            return None
        try:
            return float(digits)
        except Exception:
            return None
    num = float(m.group(1))
    suf = m.group(2).upper()
    if suf == 'K':
        num *= 1_000
    elif suf == 'M':
        num *= 1_000_000
    return num


def load_area_map(path):
    area = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            country = r.get('Country') or r.get('country')
            area_raw = r.get('Area (km2)') or r.get('Area') or r.get('Area (km2)')
            if not country:
                continue
            val = parse_area(area_raw)
            if val is None:
                continue
            area[norm_name(country)] = val
    return area


def numeric_to_alpha3(numeric_code: str) -> str:
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


def main():
    area_map = load_area_map(POP_FILE)

    alias = {
        'congo': 'republic of the congo',
        'dr congo': 'dr congo',
        'ivory coast': 'ivory coast',
        'united states': 'united states',
    }

    rows = []
    unmatched = []
    with open(TRACK_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            if not r:
                continue
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
            area_km2 = None
            if cname_norm in area_map:
                area_km2 = area_map[cname_norm]
            else:
                if cname_norm in alias and alias[cname_norm] in area_map:
                    area_km2 = area_map[alias[cname_norm]]
                else:
                    for k in area_map.keys():
                        if cname_norm in k or k in cname_norm:
                            area_km2 = area_map[k]
                            break

            if area_km2 is None or area_km2 == 0:
                unmatched.append(country_raw)
                continue

            # value = km of track / km^2 country area
            value = track / area_km2
            # value = track
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
    main()
