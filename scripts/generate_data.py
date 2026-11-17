#!/usr/bin/env python3
"""Generate Baseline data.json from MCP CSVs using only the Python standard library.

Run from any directory: python3 /path/to/repository/scripts/generate_data.py
Use --help for custom input/output paths. Source CSVs are never modified.
"""
import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RALLY_BUCKETS = {'1-3', '4-6', '7-9', '10'}
OVERVIEW_FIELDS = (
    'serve_pts aces dfs first_in first_won second_in second_won bk_pts bp_saved '
    'return_pts return_pts_won winners winners_fh winners_bh unforced unforced_fh unforced_bh'
).split()


def read_rows(path, required):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path}: missing columns: {", ".join(sorted(missing))}')
        for row in reader:
            if None in row or any(row[key] is None for key in required):
                raise ValueError(f'{path}:{reader.line_num}: unexpected extra fields or missing required field')
            yield row


def count(value, path, match_id, column):
    try:
        number = int(value or 0)
        if number < 0:
            raise ValueError
        return number
    except ValueError:
        raise ValueError(f'{path}: {match_id}: invalid {column} count {value!r}') from None


def build_dataset(source):
    result = []
    skipped = 0
    for gender in ('w', 'm'):
        metadata = source / f'charting-{gender}-matches.csv'
        matches = {}
        for row in read_rows(metadata, ['match_id', 'Date', 'Tournament', 'Surface', 'Round', 'Player 1', 'Player 2']):
            match_id = row['match_id']
            if not match_id:
                raise ValueError(f'{metadata}: empty match_id')
            if match_id in matches:
                print(f'Warning: {metadata.name}: duplicate {match_id}; using the last metadata row', file=sys.stderr)
            matches[match_id] = dict(
                id=match_id, gender=gender, date=row['Date'], tournament=row['Tournament'],
                surface=row['Surface'], round=row['Round'],
                players=[row['Player 1'], row['Player 2']], stats=[], rally=[])
        overview = source / f'charting-{gender}-stats-Overview.csv'
        for row in read_rows(overview, ['match_id', 'player', 'set', *OVERVIEW_FIELDS]):
            if row['set'] != 'Total' or row['match_id'] not in matches:
                continue
            stats = {key: count(value, overview, row['match_id'], key)
                     for key, value in row.items() if key not in ('match_id', 'player', 'set')}
            matches[row['match_id']]['stats'].append(dict(player=row['player'], **stats))
        rally = source / f'charting-{gender}-stats-Rally.csv'
        for row in read_rows(rally, ['match_id', 'row', 'pts']):
            if row['row'] in RALLY_BUCKETS and row['match_id'] in matches:
                matches[row['match_id']]['rally'].append([
                    row['row'], count(row['pts'], rally, row['match_id'], 'pts')])
        for match in matches.values():
            stats = match['stats']
            if len(stats) != 2 or sorted(s['player'] for s in stats) != sorted(match['players']):
                skipped += 1
                continue
            result.append(match)
    return result, skipped


def write_outputs(matches, outputs):
    # Finish parsing and serializing before writing any files.
    payload = json.dumps(matches, separators=(',', ':'), ensure_ascii=True)
    names = sorted({name for match in matches for name in match['players']})
    options = '<option value="">Choose an athlete…</option>' + ''.join(
        f'<option value="{html.escape(name, quote=True)}">{html.escape(name)}</option>'
        for name in names)
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + '.tmp')
        temporary.write_text(payload, encoding='utf-8')
        temporary.replace(output)
        page = output.parent / 'index.html'
        if page.exists():
            original = page.read_text(encoding='utf-8')
            updated = re.sub(
                r'(<select id="athlete">).*?(</select>)',
                lambda match: match[1] + options + match[2], original, flags=re.DOTALL)
            if updated != original:
                page.write_text(updated, encoding='utf-8')
        print(f'Wrote {output}: {len(matches):,} matches, {len(names):,} athletes, {len(payload.encode("utf-8")) / 1e6:.1f} MB')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source-dir', type=Path, default=ROOT, help='Directory containing repository CSVs')
    parser.add_argument('--output', type=Path, action='append', help='Output JSON path; repeat for multiple destinations. Defaults to docs/tennis/data.json and the local dashboard if present.')
    args = parser.parse_args(argv)
    outputs = args.output
    if outputs is None:
        outputs = [ROOT / 'docs/tennis/data.json']
        local = ROOT / 'tennis-dashboard/dist'
        if local.is_dir():
            outputs.append(local / 'data.json')
    try:
        matches, skipped = build_dataset(args.source_dir.resolve())
        if not matches:
            raise ValueError('No matches with two valid player overview totals; outputs were not changed')
        write_outputs(matches, list(dict.fromkeys(path.resolve() for path in outputs)))
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Skipped {skipped:,} matches without exactly one overview Total row per player.')


if __name__ == '__main__':
    main()
