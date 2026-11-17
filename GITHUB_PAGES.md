# Publish Solutions Nextio with GitHub Pages

The complete website is in `docs/`:

- `docs/index.html`: Solutions Nextio home page.
- `docs/tennis/`: Baseline dashboard, including the generated match dataset.
- Trading links to Yahoo Finance.

Both the company page and dashboard run as static files without an application server or Sites sign-in.

## Enable hosting once

In `zluo/tennis_MatchChartingProject`, open **Settings → Pages**:

1. Under **Build and deployment**, select **Deploy from a branch**.
2. Select branch **master** and folder **/docs**.
3. Click **Save** and wait for the Pages deployment to finish.

Expected home page: https://zluo.github.io/tennis_MatchChartingProject/

Expected dashboard: https://zluo.github.io/tennis_MatchChartingProject/tennis/

These addresses are expected deployment destinations, not confirmation of a successful deployment. GitHub Pages serves a public website; confirm that public visibility is intended when enabling it. Hosting availability depends on repository visibility and the account's GitHub plan.

## Preview and update

```sh
python3 -m http.server 8000 --directory docs
```

Open http://localhost:8000. Edit files in `docs/`, commit, and push to `master` to deploy subsequent changes. Relative asset links support the repository URL prefix.

The original Sites sources remain in `solutions-nextio/` and `tennis-dashboard/` locally; `docs/` is the self-contained GitHub Pages distribution. When updating its dataset, run `python3 scripts/generate_data.py`. This updates `docs/tennis/data.json`, refreshes its athlete dropdown, and updates the local dashboard copy if present. No manual copying is required.

Tennis data attribution and CC BY-NC-SA 4.0 license links appear in the dashboard footer. Keep them when changing or sharing the site.

## Athlete history reports

In Baseline, choose an athlete from the **Athlete** dropdown or the player search. The athlete report shows match-by-match serve, return, first-serve, ace, or break-point rates and charted matches per year. Hover over points to see the opponent, tournament, date, and rate. **Show full history** clears surface and year filters for that athlete. Historical records include only charted matches in this dataset.

Validate athlete calculations with `node --test tests/athlete-history.test.mjs`.

## Regenerate data after CSV changes

From the repository root (Python 3.9+; no packages required):

```sh
python3 scripts/generate_data.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/athlete-history.test.mjs
```

The script reads men's and women's `matches`, `stats-Overview`, and `stats-Rally` CSVs. It joins on `match_id`, uses overview `Total` rows, and keeps rally categories `1-3`, `4-6`, `7-9`, and `10`. It excludes matches without one overview total for each player, reporting the count. Existing duplicate metadata IDs produce warnings and use the last row. Missing required columns and invalid numeric counts stop generation before output files change. CSV files remain unchanged.

The default destinations are `docs/tennis/data.json` and, if the local dashboard folder exists, `tennis-dashboard/dist/data.json`. Adjacent `index.html` athlete dropdowns are refreshed with names from the generated data.

Custom source directory or output paths:

```sh
python3 scripts/generate_data.py --source-dir /path/to/csvs --output /tmp/data.json
python3 scripts/generate_data.py --output /tmp/first/data.json --output /tmp/second/data.json
```

After validation, commit and push the changed CSVs, `docs/tennis/data.json`, and `docs/tennis/index.html` to publish the updated reporting data.
