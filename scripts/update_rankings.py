#!/usr/bin/env python3
"""Download dated top-500 ATP/WTA singles rankings, then regenerate dashboard data.
Run: python3 scripts/update_rankings.py
Source: TennisExplorer public rankings. Requires network; no third-party packages.
"""
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import html
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {'m':'https://www.tennisexplorer.com/ranking/atp-men/', 'w':'https://www.tennisexplorer.com/ranking/wta-women/'}


def parse_page(content):
    date = re.search(r'WTA and ATP rankings on\s*-\s*(\d{2}\.\d{2}\.\d{4})', content)
    if not date:
        raise ValueError('Ranking date missing from source')
    date = datetime.strptime(date[1], '%d.%m.%Y').strftime('%Y-%m-%d')
    rows = []
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', content, re.S):
        rank = re.search(r'<td class="rank first">(\d+)\.</td>', row)
        name = re.search(r'<td class="t-name"><a[^>]*>(.*?)</a>', row, re.S)
        if rank and name:
            rows.append((int(rank[1]), html.unescape(re.sub('<[^>]+>', '', name[1])).strip()))
    if not rows:
        raise ValueError('Ranking rows missing from source')
    return date, rows


def fetch(job):
    gender, page = job
    url = SOURCES[gender] + (f'?page={page}' if page > 1 else '')
    request = Request(url, headers={'User-Agent':'Mozilla/5.0 (Solutions Nextio ranking refresh)'})
    with urlopen(request, timeout=30) as response:
        date, rows = parse_page(response.read().decode('utf-8'))
    if min(rank for rank, _ in rows) != (page-1)*50+1:
        raise ValueError(f'{url}: unexpected page range')
    return gender, date, [(gender,name,rank,date,url) for rank,name in rows if rank <= 500]


def main():
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            pages = list(pool.map(fetch, [(gender,page) for gender in SOURCES for page in range(1,11)]))
        for gender in SOURCES:
            dates = {date for g,date,_ in pages if g == gender}
            if len(dates) != 1:
                raise ValueError(f'{gender}: ranking dates changed during download; try again')
        rows = [row for _,_,page_rows in pages for row in page_rows]
        if len({(r[0],r[2]) for r in rows}) != 1000:
            raise ValueError('Expected complete top-500 snapshots for both tours')
        destination = ROOT / 'data/athlete_rankings.csv'
        destination.parent.mkdir(exist_ok=True)
        temporary = destination.with_suffix('.tmp')
        with temporary.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['gender','name','rank','ranking_date','source'])
            writer.writerows(rows)
        temporary.replace(destination)
        print(f'Updated {len(rows)} ranking entries: '+', '.join(sorted({r[3] for r in rows})))
        subprocess.run([sys.executable,str(ROOT/'scripts/generate_data.py')],check=True)
    except Exception as error:
        print(f'Ranking refresh failed: {error}',file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
