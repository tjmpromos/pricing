# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo is a flat collection of JSON pricing files consumed by a backend API, plus a single Python utility (`update_prices.py`) for bulk-adjusting prices by a percentage. There is no build system, no tests, and no package layout — every `*.json` at the repo root is a live data file.

Branches like `pricing-update-2026-05` indicate periodic (typically monthly/seasonal) repricing runs.

## Common commands

`update_prices.py` must be run from the repo root (it uses `glob.glob('*.json')`):

```bash
# Interactive: pick files matching a keyword, then select from a numbered list
python update_prices.py -p 6 --keywords dog-tag

# Non-interactive: apply to all files matching keywords without prompting
python update_prices.py -p 6 --keywords dog-tag --all

# Negative percentages — use `=` to prevent argparse from treating it as a flag
python update_prices.py -p=-1.5% --keywords lapel-pin --all

# Process explicit files (bypasses keyword matching)
python update_prices.py -p 6 --files dog-tag-engraved.json dog-tag-military.json

# Preview matches without writing
python update_prices.py -p 6 --keywords dog-tag --list

# DANGEROUS: omitting --keywords targets every JSON file in the directory
python update_prices.py -p 6 --all
```

The `-p`/`--percent` value accepts `6`, `6%`, `-1.5`, `-1.5%`. Each updated price is multiplied and then **ceiling-rounded to the nearest cent** (`math.ceil(price * 100) / 100`) — repeated runs therefore drift upward slightly even at 0%, so avoid running the script just to "format" files.

## JSON file shapes

Two distinct shapes share the same keys (`caption`, `footnotes`, `priceMultiplier`, `pricable`, `rows`). The shape determines how the script touches them:

**1. Quantity-tier pricing** (e.g., `dog-tag-engraved.json`, `challenge-coins-*.json`)
- `pricable` is a list of quantity strings: `["25", "50", "100", ...]`
- Each row is flat: `{ "Type": "...", "25": 3.74, "50": 2.87, ... }`
- The script updates every numeric value under a key listed in `pricable`.

**2. Options / arbitrary pricing** (files with `"arbitrary": true`, e.g., `lapel-pin-options.json`, `patches-options.json`)
- `pricable` lists option names (e.g., `"screwBack"`, `"magneticAcrylicCase"`).
- Each row wraps a nested object: `{ "screwBack": { "price": 0.43, "postfix": "per pin" } }`.
- **`update_prices.py` does NOT update these rows** — it only mutates values where `row[tier]` is itself an `int`/`float`. The nested `{price, postfix}` shape is skipped silently. Adjust option pricing by hand or extend the script.
- `"FREE"` string prices are also skipped (not numeric).

The `priceMultiplier` top-level field is data for downstream consumers; the script ignores it.

## Editing conventions

- Files are written back with `json.dump(..., indent=2)` — match that style for hand edits to keep diffs minimal.
- When adding a new option to an options file, add the key to **both** the `pricable` array and a corresponding entry in `rows` (see commit `821e166` adding `magneticAcrylicCase` for the pattern).
- Keep filenames kebab-case and grouped by product family prefix (`dog-tag-`, `lapel-pin-`, `wristbands-`, etc.) — keyword matching in the script depends on these prefixes.
