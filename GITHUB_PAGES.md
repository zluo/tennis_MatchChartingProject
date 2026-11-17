# Publish Solutions Nextio with GitHub Pages

The complete website is in `docs/`:

- `docs/index.html`: Solutions Nextio home page.
- `docs/tennis/`: Baseline overview and generated match dataset.
- `docs/tennis/athlete.html`: dedicated athlete history reports.
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

In Baseline, open **Athlete reporting** (`tennis/athlete.html`), then choose an athlete from the **Athlete** dropdown or the player search. The athlete report shows match-by-match serve, return, first-serve, ace, or break-point rates and charted matches per year. Performance uses chronological match bars; scroll horizontally for long histories. Hover over bars to see the opponent, tournament, date, and rate. **Show full history** clears surface and year filters for that athlete. Historical records include only charted matches in this dataset.

Validate athlete calculations with `node --test tests/athlete-history.test.mjs`.

## Regenerate data after CSV changes

From the repository root (Python 3.9+; no packages required):

```sh
python3 scripts/generate_data.py
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/athlete-history.test.mjs
```

The script reads men's and women's `matches`, `stats-Overview`, and `stats-Rally` CSVs. It joins on `match_id`, uses overview `Total` rows, and keeps rally categories `1-3`, `4-6`, `7-9`, and `10`. It excludes matches without one overview total for each player, reporting the count. Existing duplicate metadata IDs produce warnings and use the last row. Missing required columns and invalid numeric counts stop generation before output files change. CSV files remain unchanged.

The default destinations are `docs/tennis/data.json` and, if the local dashboard folder exists, `tennis-dashboard/dist/data.json`. Adjacent `index.html` and `athlete.html` athlete dropdowns are refreshed with names from the generated data.

Custom source directory or output paths:

```sh
python3 scripts/generate_data.py --source-dir /path/to/csvs --output /tmp/data.json
python3 scripts/generate_data.py --output /tmp/first/data.json --output /tmp/second/data.json
```

After validation, commit and push the changed CSVs, `docs/tennis/data.json`, and `docs/tennis/athlete.html` to publish the updated reporting data.

## Athlete tours, rankings, and career coverage

On **Athlete reporting**, choose **Women** or **Men** in **Athlete tour**. The dropdown shows only that tour, sorted by singles ranking (lowest number first), with missing ranks after ranked athletes. Names with no available rank remain selectable. Each option shows its charted period; the profile shows its dated rank, source link, total charted matches, and first/last charted years before report filters.

**Charted career period is dataset coverage**, not verified professional debut or retirement. The match CSVs do not contain official career dates. A missing rank means no match in the saved top-500 snapshot, not proof that an athlete is unranked or retired. Name matching ignores accents, punctuation, and name-token order, but does not guess nicknames or changed surnames.

`data/athlete_rankings.csv` stores the dated top-500 ATP and WTA singles snapshots from [TennisExplorer](https://www.tennisexplorer.com/ranking/). To refresh rankings with network access and regenerate reports:

```sh
python3 scripts/update_rankings.py
```

The downloader validates dates and page coverage before replacing the saved ranking CSV. `python3 scripts/generate_data.py` remains usable offline and joins the saved snapshot to produce `profiles.json` beside each `data.json`. If no ranking CSV exists, profiles still include tour and charted period, with unavailable ranks. The website also falls back to charted periods if `profiles.json` cannot load.

After a ranking refresh, commit `data/athlete_rankings.csv`, `docs/tennis/profiles.json`, and `docs/tennis/athlete.html`, along with any changed match data. Rankings are snapshots and do not refresh automatically for visitors.
