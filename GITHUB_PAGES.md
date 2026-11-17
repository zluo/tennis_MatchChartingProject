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

The original Sites sources remain in `solutions-nextio/` and `tennis-dashboard/` locally; `docs/` is the self-contained GitHub Pages distribution. When updating its dataset, run `python3 tennis-dashboard/scripts/prepare_data.py` and `node tennis-dashboard/scripts/check.mjs`, then copy `tennis-dashboard/dist/data.json` to `docs/tennis/data.json`.

Tennis data attribution and CC BY-NC-SA 4.0 license links appear in the dashboard footer. Keep them when changing or sharing the site.
