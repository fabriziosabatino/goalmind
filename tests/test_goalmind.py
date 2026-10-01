"""Regression checks for the data/model errors found in the original project."""
import math
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from app.elo_application import EloApplication
from data_structure.match import Match
from data_structure.player import Player
from data_structure.team import Team

ROOT = Path(__file__).resolve().parents[1]


def player(xg=0.75, minutes=900):
    return Player('Test', 'Arsenal', 'FW', minutes, 0, 0, xg, 1, .1,
                  1, 1, 7, 0, 5, 2, xg_total=7.5)


class ModelTests(unittest.TestCase):
    def test_poisson_rate_and_exposure(self):
        p = player()
        self.assertAlmostEqual(p.prob_goal(), 1 - math.exp(-.75))
        self.assertAlmostEqual(p.prob_goal(45), 1 - math.exp(-.375))
        self.assertLess(p.prob_goal(45), p.prob_goal(90))
        self.assertEqual(p.prob_goal(0), 0)
        self.assertLess(p.prob_goal(opponent_factor=.5), p.prob_goal())
        self.assertEqual(player(0).prob_goal(), 0)
        self.assertAlmostEqual(player(100).prob_goal(), 1)
        for value in [-1, 121, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                p.prob_goal(value)

    def test_missing_rate_is_not_observed_zero(self):
        with self.assertRaises(ValueError):
            player('-').prob_goal()
        with self.assertRaises(ValueError):
            player(minutes=0).prob_goal()
        with self.assertRaises(ValueError):
            player('broken')

    def test_results_and_invalid_scores(self):
        self.assertEqual(Match('A', 'B', 2, 0).get_result(), 1)
        self.assertEqual(Match('A', 'B', 0, 2).get_result(), 0)
        self.assertEqual(Match('A', 'B', 1, 1).get_result(), .5)
        for goals in [math.nan, -1, 1.5, math.inf]:
            with self.assertRaises(ValueError):
                Match('A', 'B', goals, 0)

    def test_elo_expected_score_and_defense(self):
        team = Team('A')
        self.assertEqual(team.compute_expected_score(1500), .5)
        self.assertGreater(team.compute_expected_score(1500, 40), .5)
        self.assertEqual(team.compute_expected_score(-1e10), 1)
        with self.assertRaises(ValueError):
            team.defensive_factor()
        team.defensive_games = 10
        team.goals_conceded = 5
        team.league_goals_per_team_match = 1.5
        self.assertAlmostEqual(team.defensive_factor(), 1 / 3)


class LoaderTests(unittest.TestCase):
    def write_matches(self, root, rows):
        path = Path(root) / 'matches.csv'
        pd.DataFrame(rows, columns=['MatchDate', 'HomeTeam', 'AwayTeam',
                                   'FTHome', 'FTAway', 'Division']).to_csv(path, index=False)
        return path

    def test_sort_bounds_duplicates_missing_scores_and_elo_replay(self):
        rows = [('2024-08-02', 'Bayern', 'Arsenal', 0, 1, 'X'),
                ('2024-08-01', 'Arsenal', 'Bayern Munich', 2, 0, 'X'),
                ('2024-08-01', 'Arsenal', 'Bayern Munich', 2, 0, 'X'),
                ('2024-08-03', 'Arsenal', 'Bayern', None, 1, 'X'),
                ('broken', 'Arsenal', 'Bayern', 0, 1, 'X')]
        with tempfile.TemporaryDirectory() as root:
            app = EloApplication()
            path = self.write_matches(root, rows)
            app.deserialize_matches(path, start_date='2024-08-01')
            self.assertEqual(app.load_report['invalid_matches'], 2)
            self.assertEqual(app.load_report['duplicate_matches'], 1)
            self.assertEqual(len(app._matches), 2)
            self.assertEqual(app._matches[0].home_team_name, 'Arsenal')
            app.update_all_elo(k=20, home_advantage=0)
            first = app.find_team('Arsenal').elo
            # First win gives 1510; second win as away against 1490 adds <10.
            self.assertGreater(first, 1510)
            self.assertLess(first, 1520)
            self.assertAlmostEqual(sum(t.elo for t in app._teams.values()), 3000)
            app.update_all_elo(k=20, home_advantage=0)
            self.assertEqual(app.find_team('Arsenal').elo, first)
            app.deserialize_matches(path, start_date='2024-08-01', end_date='2024-08-01')
            self.assertEqual(len(app._matches), 1)
            app.deserialize_matches(path, start_date='2030-01-01')
            self.assertEqual(len(app._matches), 0)
            self.assertIsNone(app.snapshot_date)

    def test_conflicting_scores_and_invalid_date_bounds(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.write_matches(root, [('2024-01-01', 'A', 'B', 1, 0, 'X'),
                                             ('2024-01-01', 'A', 'B', 2, 0, 'X')])
            with self.assertRaises(ValueError):
                EloApplication().deserialize_matches(path, start_date=None)
            for start, end in [('', None), ('nonsense', None), ('2025-01-01', '2024-01-01')]:
                with self.assertRaises(ValueError):
                    EloApplication().deserialize_matches(path, start, end)

    def test_empty_and_constant_analysis(self):
        app = EloApplication()
        self.assertEqual(app.statistics()['n_pairs'], 0)
        self.assertTrue(math.isnan(app.statistics()['correlation']))
        app._players[('test', 'arsenal')] = player()
        self.assertTrue(math.isnan(app.statistics()['correlation']))

    def test_missing_file_and_schema(self):
        app = EloApplication()
        with self.assertRaisesRegex(ValueError, 'Cannot read CSV'):
            app.deserialize_players('/does/not/exist.csv')
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'bad.csv'
            path.write_text('unrelated\n1\n')
            with self.assertRaisesRegex(ValueError, 'missing columns'):
                app.deserialize_players(path)


class SuppliedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = EloApplication()
        cls.app.deserialize_players(ROOT / 'import/Football_Player_Data-Analysis.csv')
        cls.app.deserialize_matches(ROOT / 'import/Matches.csv')
        cls.app.update_all_elo()

    def test_all_observations_aliases_and_homonyms(self):
        self.assertEqual(self.app.load_report['players'], 1533)
        self.assertEqual(self.app.load_report['missing_xg_rates'], 28)
        self.assertEqual(self.app.unmatched_player_teams(), [])
        self.assertIs(self.app.find_team('bayern'), self.app.find_team('Bayern Munich'))
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.app.find_player('Juan Cruz')
        self.assertEqual(self.app.find_player('Juan Cruz', 'Leganes').team, 'Leganes')
        self.assertEqual(self.app.find_player('Juan Cruz', 'Osasuna').team, 'Osasuna')

    def test_probabilities_statistics_and_no_cross_league_scenario(self):
        self.assertAlmostEqual(self.app.find_player('Mohamed Salah').prob_goal(), .5276334472589853)
        p = self.app.score_probability('Mohamed Salah', 'Arsenal', 60)
        self.assertTrue(0 < p < 1)
        with self.assertRaisesRegex(ValueError, 'same team'):
            self.app.score_probability('Mohamed Salah', 'Liverpool')
        with self.assertRaisesRegex(ValueError, 'same latest division'):
            self.app.score_probability('Mohamed Salah', 'Bayern')
        report = self.app.statistics()
        self.assertEqual(report['n_pairs'], 1533)
        self.assertTrue(math.isfinite(report['correlation']))
        table = self.app.player_table()
        salah = table.loc[table.Name.eq('Mohamed Salah')].iloc[0]
        self.assertEqual(salah.xG_Total, 20.84)  # Use the observed total column.
        self.assertAlmostEqual(sum(t.elo for t in self.app._teams.values()),
                               len(self.app._teams) * 1500, places=7)


if __name__ == '__main__':
    unittest.main()
