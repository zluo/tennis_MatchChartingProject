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
