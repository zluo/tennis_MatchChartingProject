# Baseline — Tennis Analytics

A dependency-free static dashboard for the repository's men's and women's match data. Filter by tour, surface, year range, and exact player name. Explore serve and return rates, rally-length distributions, annual serving trends, individual match statistics, and CSV exports of selected match metadata.

## Run locally

From the repository root:

```sh
python3 scripts/generate_data.py
node tennis-dashboard/scripts/check.mjs
python3 -m http.server 8000 --directory tennis-dashboard/dist
```

Open http://localhost:8000. No Node packages or build step are required. Node is used only for validation. The app runs in the browser; the Google Fonts stylesheet is optional and has system font fallbacks.

## Athlete reporting

Open **Athlete reporting** from the overview navigation, or visit `athlete.html` directly. The dedicated page separates Men and Women, sorts athletes by dated singles ranking, and shows charted career periods alongside history charts, filters, and a match notebook. Rankings cover saved top-500 snapshots; missing ranks are labeled unavailable. Run `python3 scripts/update_rankings.py` from the repository root to refresh the snapshot and regenerate profiles. An overview player selection carries over in the report link.

## Data and analysis

`scripts/generate_data.py` at the repository root joins match metadata with `Total` rows from `Overview` and the non-overlapping `1-3`, `4-6`, `7-9`, and `10` rows from `Rally`. Matches without exactly two overview total rows are excluded. Re-run after CSV updates. Source CSVs are never modified.

Percentages use summed numerators divided by summed denominators, rather than averages of percentages. Serve points won uses `(first_won + second_won) / serve_pts`; return points won uses `return_pts_won / return_pts`; break points saved uses `bp_saved / bk_pts`. Zero denominators display a dash. Player filters select that player's overview statistics; rally charts and recorded point counts always describe both players in the selected matches. Ten or more shots corresponds to source rally category `10`.

Charted matches are a selected sample, not all professional matches. Comparisons and temporal patterns may reflect sample composition. Point totals do not determine the match winner. The generator confirms completed match outcomes from final point scores and workbook match rules. The yearly athlete chart stacks wins, losses, and unknown outcomes; incomplete or unconfirmed outcomes remain unknown. Export downloads selected match metadata, not derived statistics.

## Files

- `dist/`: complete static site, including generated `data.json`.
- `../scripts/generate_data.py`: canonical CSV generator; updates both dashboard distributions and athlete lists.
- `scripts/prepare_data.py`: compatibility entry point for the canonical generator.
- `scripts/check.mjs`: dataset integrity, weighted calculations, and filtering checks.
- `.openai/hosting.json`: private Sites identity and static hosting configuration.

Data attribution: Tennis Abstract Match Charting Project, CC BY-NC-SA 4.0. Preserve attribution and license terms when sharing adaptations.
