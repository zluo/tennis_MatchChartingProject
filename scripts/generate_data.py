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
import unicodedata
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


def completed_match_winner(point, best_of, format_code):
    """Confirm a completed match from its final pre-point score (server-first Pts).

    MatchChart workbook B14 codes: A=10-point deciding TB, T=12-all TB,
    S=deciding match TB, N=NextGen, W=8-all TB, V=all advantage sets.
    Incomplete, retired, unsupported, or malformed records remain unknown.
    """
    try:
        best_of = int(best_of)
        if best_of not in (1, 3, 5):
            return None
        target = best_of // 2 + 1
        winner = int(point['PtWinner']) - 1
        server = int(point['Svr']) - 1
        if winner not in (0, 1) or server not in (0, 1):
            return None
        sets = [int(point['Set1']), int(point['Set2'])]
        games = [int(point['Gm1']), int(point['Gm2'])]
        if any(v < 0 for v in sets + games) or sets[winner] != target - 1 or sets[1-winner] >= target:
            return None
        deciding = sets == [target-1, target-1]
        code = str(format_code or '').strip()
        if code not in ('1', '0', 'A', 'T', 'S', 'N', 'W', 'V'):
            return None
        scores = point['Pts'].upper().split('-')
        if len(scores) != 2:
            return None
        own, other = (scores if winner == server else scores[::-1])
        tb_at = 3 if code == 'N' else 8 if code == 'W' else 12 if deciding and code == 'T' else 6
        tb_enabled = code != 'V' and not (deciding and code == '0')
        match_tb = deciding and code == 'S'
        if (match_tb and games == [0, 0]) or (tb_enabled and games == [tb_at, tb_at]):
            before, against = int(own), int(other)
            needed = 10 if match_tb or (deciding and code == 'A') else 7
            # Reject rows whose score was already terminal before this point.
            if before >= needed and before - against >= 2:
                return None
            return winner if before + 1 >= needed and before + 1 - against >= 2 else None
        game_won = (own == '40' and other in ('0', '15', '30')) or (own in ('AD', 'A') and other == '40')
        if code == 'N' and own == other == '40':
            game_won = True
        games_needed = 4 if code == 'N' else 6
        return winner if game_won and games[winner] + 1 >= games_needed and games[winner] + 1 - games[1-winner] >= 2 else None
    except (ValueError, KeyError, TypeError):
        return None


def attach_outcomes(source, gender, matches, rules):
    final_points = {}
    required = ['match_id','Pt','Set1','Set2','Gm1','Gm2','Pts','Svr','PtWinner']
    for path in sorted(source.glob(f'charting-{gender}-points-*.csv')):
        for row in read_rows(path, required):
            match_id = row['match_id']
            if match_id not in matches:
                continue
            try:
                number = int(row['Pt'])
            except ValueError:
                continue
            previous = final_points.get(match_id)
            if previous is None or number > previous[0]:
                final_points[match_id] = (number, row)
    for match_id, match in matches.items():
        last = final_points.get(match_id)
        winner = completed_match_winner(last[1], *rules[match_id]) if last else None
        match['winner'] = match['players'][winner] if winner is not None else None


def build_dataset(source):
    result = []
    skipped = 0
    for gender in ('w', 'm'):
        metadata = source / f'charting-{gender}-matches.csv'
        matches = {}
        rules = {}
        for row in read_rows(metadata, ['match_id', 'Date', 'Tournament', 'Surface', 'Round', 'Player 1', 'Player 2']):
            match_id = row['match_id']
            if not match_id:
                raise ValueError(f'{metadata}: empty match_id')
            if match_id in matches:
                print(f'Warning: {metadata.name}: duplicate {match_id}; using the last metadata row', file=sys.stderr)
            rules[match_id] = (row.get('Best of'), row.get('Final TB?'))
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
        attach_outcomes(source, gender, matches, rules)
        for match in matches.values():
            stats = match['stats']
            if len(stats) != 2 or sorted(s['player'] for s in stats) != sorted(match['players']):
                skipped += 1
                continue
            result.append(match)
    return result, skipped


def name_key(name):
    plain = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return ' '.join(sorted(re.findall(r'[a-z0-9]+', plain)))


def build_profiles(matches, ranking_rows=()):
    rankings = {}
    dates = {}
    for row in ranking_rows:
        rank = int(row['rank'])
        if row['gender'] not in ('m', 'w') or rank < 1:
            raise ValueError('Invalid gender or rank in athlete_rankings.csv')
        key = (row['gender'], name_key(row['name']))
        if key in rankings:
            raise ValueError(f'Ambiguous ranking name: {row["name"]}')
        rankings[key] = row
        dates[row['gender']] = max(dates.get(row['gender'], ''), row['ranking_date'])
    profiles = {}
    for match in matches:
        for name in match['players']:
            key = (match['gender'], name)
            if key not in profiles:
                ranking = rankings.get((match['gender'], name_key(name)))
                profiles[key] = dict(name=name, gender=match['gender'], first=match['date'], last=match['date'],
                    matches=0, rank=int(ranking['rank']) if ranking else None,
                    rankingDate=ranking['ranking_date'] if ranking else dates.get(match['gender']),
                    rankingSource=ranking['source'] if ranking else None)
            profile = profiles[key]
            profile['first'] = min(profile['first'], match['date'])
            profile['last'] = max(profile['last'], match['date'])
            profile['matches'] += 1
    return sorted(profiles.values(), key=lambda p:(p['gender'], p['rank'] or float('inf'), p['name']))


def athlete_options(profiles):
    options = '<option value="">Choose an athlete…</option>'
    for gender, label in [('w', 'Women'), ('m', 'Men')]:
        options += f'<optgroup label="{label}">'
        for profile in profiles:
            if profile['gender'] != gender:
                continue
            rank = f'#{profile["rank"]}' if profile['rank'] else 'Rank unavailable'
            period = profile['first'][:4] + '–' + profile['last'][:4]
            name = html.escape(profile['name'], quote=True)
            options += f'<option value="{name}">{rank} · {name} · {period}</option>'
        options += '</optgroup>'
    return options


def write_outputs(matches, outputs, ranking_rows=()):
    # Finish parsing and serializing before writing any files.
    payload = json.dumps(matches, separators=(',', ':'), ensure_ascii=True)
    names = {name for match in matches for name in match['players']}
    profiles = build_profiles(matches, ranking_rows)
    options = athlete_options(profiles)
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + '.tmp')
        temporary.write_text(payload, encoding='utf-8')
        temporary.replace(output)
        (output.parent / 'profiles.json').write_text(json.dumps(profiles, ensure_ascii=True, separators=(',', ':')), encoding='utf-8')
        for page in (output.parent / 'index.html', output.parent / 'athlete.html'):
            if not page.exists():
                continue
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
        ranking_path = args.source_dir / 'data/athlete_rankings.csv'
        ranking_rows = list(read_rows(ranking_path, ['gender','name','rank','ranking_date','source'])) if ranking_path.exists() else []
        write_outputs(matches, list(dict.fromkeys(path.resolve() for path in outputs)), ranking_rows)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Confirmed outcomes: {sum(m.get("winner") is not None for m in matches):,}; unknown outcomes: {sum(m.get("winner") is None for m in matches):,}.')
    print(f'Skipped {skipped:,} matches without exactly one overview Total row per player.')


if __name__ == '__main__':
    main()
