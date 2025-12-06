#!/usr/bin/env bash
# Usage: ./run.sh <name> [--title 'Title text']

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <name> [--title 'Title text'] [--interactive] [--value-col NAME] [--iso-col NAME] [--country-col NAME]"
  exit 2
fi

# Parse arguments: allow `--title` (or -t), `--interactive`, and other passthrough args.
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
NAME=""
TITLE=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title|-t)
      TITLE="$2"
      shift 2
      ;;
    --interactive|-i)
      EXTRA_ARGS+=("--interactive")
      shift
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do EXTRA_ARGS+=("$1"); shift; done
      ;;
    --*=*)
      # allow passing long options as-is
      EXTRA_ARGS+=("$1")
      shift
      ;;
    -* )
      # unknown flag; forward it
      EXTRA_ARGS+=("$1")
      shift
      ;;
    *)
      if [ -z "$NAME" ]; then
        NAME="$1"
      else
        EXTRA_ARGS+=("$1")
      fi
      shift
      ;;
  esac
done

if [ -z "$NAME" ]; then
  echo "Error: name is required. Usage: $0 <name> [--title 'Title text'] ..."
  exit 2
fi

CSV_PATH="$ROOT_DIR/inputs/${NAME}.csv"
OUT_PREFIX="$ROOT_DIR/outputs/${NAME}"

if [ ! -f "$CSV_PATH" ]; then
  echo "Error: input CSV not found: $CSV_PATH"
  exit 1
fi

mkdir -p "$(dirname "$OUT_PREFIX")"

# Default columns: prefer `country_ISO` for ISO3 codes and `value` for numeric value.
# If TITLE was provided, pass it through to the Python script; otherwise omit the flag.
CMD=(python3 "$ROOT_DIR/generate_choropleth.py" "$CSV_PATH" --iso-col country_ISO --value-col value --output-prefix "$OUT_PREFIX")
if [ -n "$TITLE" ]; then
  CMD+=(--title "$TITLE")
fi
# append any extra args collected
for a in "${EXTRA_ARGS[@]}"; do CMD+=("$a"); done

"${CMD[@]}"

echo "Done. Output files are ${OUT_PREFIX}.png (and ${OUT_PREFIX}.html if --interactive was used)."
