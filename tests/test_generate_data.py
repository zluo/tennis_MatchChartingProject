"""Run with: python3 -m unittest discover -s tests -p 'test_*.py'."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('generate_data', Path(__file__).resolve().parents[1] / 'scripts/generate_data.py')
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class GeneratorTests(unittest.TestCase):
    def fixture(self, root, bad_count=False):
        def write(name, headers, rows):
            with (root / name).open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
        for gender in ('w', 'm'):
            prefix = f'charting-{gender}-'
            metadata = dict(match_id=gender, Date='20260101', Tournament='Example, Open', Surface='Hard', Round='F', **{'Player 1':'A & B', 'Player 2':'C'})
            write(prefix+'matches.csv', list(metadata), [metadata])
            stats = []
            for player in ('A & B', 'C'):
                row = dict(match_id=gender, player=player, set='Total', **{key:'0' for key in generator.OVERVIEW_FIELDS})
                if bad_count: row['aces'] = 'invalid'
                stats.append(row)
            write(prefix+'stats-Overview.csv', list(stats[0]), stats)
            write(prefix+'stats-Rally.csv', ['match_id','row','pts'], [dict(match_id=gender,row='1-3',pts='2'),dict(match_id=gender,row='Total',pts='2')])

    def test_joins_and_dropdown_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            matches, skipped = generator.build_dataset(root)
            self.assertEqual(skipped, 0)
            self.assertEqual(len(matches), 2)
            self.assertEqual(matches[0]['tournament'], 'Example, Open')
            self.assertEqual(matches[0]['rally'], [['1-3',2]])
            page = root / 'index.html'
            page.write_text('<select id="athlete"><option>Old</option></select>')
            athlete_page = root / 'athlete.html'
            athlete_page.write_text('<select id="athlete"><option>Old</option></select>')
            output = root / 'data.json'
            generator.write_outputs(matches, [output])
            self.assertEqual(json.loads(output.read_text()), matches)
            self.assertIn('A &amp; B', page.read_text())
            self.assertNotIn('Old', page.read_text())
            self.assertIn('A &amp; B', athlete_page.read_text())
            self.assertNotIn('Old', athlete_page.read_text())
            before = output.read_bytes()
            generator.write_outputs(matches, [output])
            self.assertEqual(before, output.read_bytes())

    def test_profiles_match_normalized_names_and_sort_rank(self):
        matches = [dict(gender='m', date='20250101', players=['Felix Auger Aliassime', 'Roger Federer']),
                   dict(gender='m', date='20260101', players=['Felix Auger Aliassime', 'Roger Federer'])]
        rows = [dict(gender='m', name='Auger-Aliassime Felix', rank='17', ranking_date='2026-11-16', source='https://example.com')]
        profiles = generator.build_profiles(matches, rows)
        self.assertEqual(profiles[0]['name'], 'Felix Auger Aliassime')
        self.assertEqual(profiles[0]['rank'], 17)
        self.assertEqual(profiles[0]['first'], '20250101')
        self.assertEqual(profiles[0]['last'], '20260101')
        self.assertEqual(profiles[0]['matches'], 2)
        self.assertIsNone(profiles[1]['rank'])
        self.assertEqual(profiles[1]['rankingDate'], '2026-11-16')

    def test_completed_outcomes_use_server_first_scores(self):
        point = dict(PtWinner='2', Svr='1', Set1='1', Set2='1', Gm1='3', Gm2='5', Pts='30-40')
        self.assertEqual(generator.completed_match_winner(point, '3', '1'), 1)
        point.update(Svr='2', Pts='40-30')
        self.assertEqual(generator.completed_match_winner(point, '3', '1'), 1)
        point.update(Pts='30-30')
        self.assertIsNone(generator.completed_match_winner(point, '3', '1'))
        point.update(Pts='40-30', Set1='0', Set2='0')
        self.assertIsNone(generator.completed_match_winner(point, '3', '1'))

    def test_tiebreak_and_special_formats(self):
        point = dict(PtWinner='1', Svr='2', Set1='1', Set2='1', Gm1='6', Gm2='6', Pts='5-6')
        self.assertEqual(generator.completed_match_winner(point, '3', '1'), 0)
        self.assertIsNone(generator.completed_match_winner(point, '3', 'A'))
        point['Pts'] = '8-9'
        self.assertEqual(generator.completed_match_winner(point, '3', 'A'), 0)
        point.update(Gm1='0', Gm2='0')
        self.assertEqual(generator.completed_match_winner(point, '3', 'S'), 0)
        point.update(Gm1='3', Gm2='2', Pts='40-40')
        self.assertEqual(generator.completed_match_winner(point, '3', 'N'), 0)
        point.update(Set1='2', Set2='1', Gm1='5', Gm2='4', Pts='30-40')
        self.assertEqual(generator.completed_match_winner(point, '5', '1'), 0)
        self.assertIsNone(generator.completed_match_winner(point, '5', 'unsupported'))

    def test_final_point_files_join_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            metadata = root / 'charting-w-matches.csv'
            with metadata.open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            rows[0].update({'Best of':'3', 'Final TB?':'1'})
            with metadata.open('w', newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
                writer.writeheader();writer.writerows(rows)
            point = dict(match_id='w', Pt='99', PtWinner='1', Svr='1', Set1='1', Set2='0', Gm1='5', Gm2='4', Pts='40-30')
            with (root/'charting-w-points-2020s.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=list(point))
                writer.writeheader();writer.writerow(point)
            matches, _ = generator.build_dataset(root)
            self.assertEqual(matches[0]['winner'], 'A & B')
            self.assertIsNone(matches[1]['winner'])

    def test_bad_numeric_count_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, bad_count=True)
            output = root / 'data.json'
            output.write_text('existing')
            with self.assertRaises(SystemExit) as error:
                generator.main(['--source-dir', str(root), '--output', str(output)])
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(output.read_text(), 'existing')

    def test_incomplete_overview_is_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            overview = root / 'charting-w-stats-Overview.csv'
            lines = overview.read_text().splitlines()
            overview.write_text('\n'.join(lines[:2])+'\n')
            matches, skipped = generator.build_dataset(root)
            self.assertEqual(skipped, 1)
            self.assertEqual([m['gender'] for m in matches], ['m'])


if __name__ == '__main__':
    unittest.main()
