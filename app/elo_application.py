"""CSV input, Elo updates and reusable exploratory analysis for GoalMind."""
from pathlib import Path
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from data_structure.match import Match
from data_structure.names import canonical_team, normalize_name
from data_structure.player import Player
from data_structure.team import Team


PLAYER_FIELDS = {
    'Mins Played': 'mins_played', 'tacklePerGame': 'tacklepergame',
    'foulsPerGame': 'foulspergame', 'interceptionPerGame': 'interceptionpergame',
    'xGPerNinety': 'xgperninety', 'shotsPerGame': 'shotspergame',
    'xGPerShot': 'xgpershot', 'keyPassPerGame': 'keypasspergame',
    'dribbleWonPerGame': 'dribblewonpergame', 'rating': 'rating',
    'goal': 'goal', 'assistTotal': 'assisttotal', 'xG': 'xg_total',
}
MATCH_COLUMNS = ['MatchDate', 'HomeTeam', 'AwayTeam', 'FTHome', 'FTAway', 'Division']


def read_csv(path, required_columns):
    """Read a CSV and report missing files or columns with a useful message."""
    try:
        frame = pd.read_csv(path, low_memory=False, na_values=['-'])
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        raise ValueError(f'Cannot read CSV {path}: {error}') from error
    missing = set(required_columns) - set(frame.columns)
    if missing:
        raise ValueError(f'{path}: missing columns: {", ".join(sorted(missing))}')
    return frame


def parse_date(value, label):
    """Parse an ISO calendar date for inclusive input bounds."""
    try:
        parsed = pd.Timestamp(pd.to_datetime(value, format='%Y-%m-%d', errors='raise'))
        if pd.isna(parsed):
            raise ValueError('Missing date.')
        return parsed.normalize()
    except (ValueError, TypeError) as error:
        raise ValueError(f'{label} must be an ISO date (YYYY-MM-DD).') from error


class EloApplication:
    """Hold a statistics snapshot and matches; public tables feed CLI/notebook."""

    DEFAULT_K = 25
    DEFAULT_HOME_ADVANTAGE = 40

    def __init__(self):
        self._players = {}
        self._teams = {}
        self._matches = []
        self._match_frame = pd.DataFrame(columns=MATCH_COLUMNS)
        self.load_report = {}
        self.snapshot_date = None
        self.defense_start_date = None

    def deserialize_players(self, file_path):
        """Replace player data; preserve homonyms and missing numeric observations.

        Returns a dictionary keyed by (normalized player name, team name).
        Invalid values and duplicate player/team rows raise ValueError.
        """
        frame = read_csv(file_path, ['Player Name', 'Player Team', 'Position 1', *PLAYER_FIELDS])
        for column in ['Player Name', 'Player Team']:
            if frame[column].isna().any() or frame[column].astype(str).str.strip().eq('').any():
                raise ValueError(f'{file_path}: missing {column}.')
        for column in PLAYER_FIELDS:
            numeric = pd.to_numeric(frame[column], errors='coerce')
            invalid = frame[column].notna() & numeric.isna()
            if invalid.any() or np.isinf(numeric).any() or numeric.lt(0).any():
                raise ValueError(f'{file_path}: invalid/nonnegative numeric values required in {column}.')
            frame[column] = numeric
        players = {}
        for record in frame.to_dict('records'):
            player = Player(
                name=str(record['Player Name']).strip(),
                team=canonical_team(record['Player Team']), position=record['Position 1'],
                **{field: record[column] for column, field in PLAYER_FIELDS.items()},
            )
            key = (normalize_name(player.name), normalize_name(player.team))
            if key in players:
                raise ValueError(f'Duplicate player/team observation: {player.name} ({player.team}).')
            players[key] = player
        self._players = players
        self.load_report['players'] = len(players)
        self.load_report['missing_xg_rates'] = int(frame['xGPerNinety'].isna().sum())
        return players.copy()

    def deserialize_matches(self, file_path, start_date='2020-08-01', end_date=None,
                            divisions=None):
        """Replace completed matches, sort by date/time and rebuild teams.

        Date bounds are inclusive. Invalid dates, names, divisions and scores
        are excluded with counts in load_report. Duplicate fixtures are removed;
        conflicting results for a date/home/away/division raise ValueError.
        """
        frame = read_csv(file_path, MATCH_COLUMNS)
        start = parse_date(start_date, 'start_date') if start_date is not None else None
        end = parse_date(end_date, 'end_date') if end_date is not None else None
        if start is not None and end is not None and start > end:
            raise ValueError('start_date cannot be after end_date.')
        frame['MatchDate'] = pd.to_datetime(frame['MatchDate'], format='%Y-%m-%d', errors='coerce')
        valid = frame['MatchDate'].notna()
        for column in ['HomeTeam', 'AwayTeam', 'Division']:
            valid &= frame[column].notna() & frame[column].astype(str).str.strip().ne('')
        for column in ['FTHome', 'FTAway']:
            frame[column] = pd.to_numeric(frame[column], errors='coerce')
            valid &= np.isfinite(frame[column]) & frame[column].ge(0) & frame[column].mod(1).eq(0)
        for column in ['HomeTeam', 'AwayTeam']:
            frame[column] = frame[column].map(canonical_team)
        valid &= frame['HomeTeam'].map(normalize_name).ne(frame['AwayTeam'].map(normalize_name))
        invalid_count = int((~valid).sum())
        frame = frame.loc[valid].copy()
        if start is not None:
            frame = frame.loc[frame['MatchDate'].ge(start)]
        if end is not None:
            frame = frame.loc[frame['MatchDate'].le(end)]
        if divisions is not None:
            frame = frame.loc[frame['Division'].isin(divisions)]
        fixture = ['MatchDate', 'HomeTeam', 'AwayTeam', 'Division']
        unique = frame.drop_duplicates([*fixture, 'FTHome', 'FTAway'])
        if unique.duplicated(fixture).any():
            raise ValueError('Conflicting scores for the same match fixture.')
        duplicate_count = len(frame) - len(unique)
        frame = unique.copy()
        time = frame['MatchTime'].fillna('00:00:00') if 'MatchTime' in frame else '00:00:00'
        frame['_kickoff'] = pd.to_datetime(
            frame['MatchDate'].dt.strftime('%Y-%m-%d') + ' ' + time,
            format='%Y-%m-%d %H:%M:%S', errors='coerce',
        ).fillna(frame['MatchDate'])
        frame = frame.sort_values('_kickoff', kind='stable').reset_index(drop=True)
        matches, teams = [], {}
        for row in frame[MATCH_COLUMNS].itertuples(index=False, name=None):
            date, home, away, home_goals, away_goals, division = row
            match = Match(home, away, home_goals, away_goals, date, division)
            matches.append(match)
            for name in (home, away):
                key = normalize_name(name)
                team = teams.setdefault(key, Team(name))
                team.division = division  # Latest observed division, including promotion.
        self._matches, self._teams, self._match_frame = matches, teams, frame
        self.snapshot_date = frame['MatchDate'].max() if not frame.empty else None
        self.load_report.update(matches=len(matches), invalid_matches=invalid_count,
                                duplicate_matches=duplicate_count)
        self._compute_defense()
        return list(matches)

    def _compute_defense(self, window_days=365):
        """Summarize the last 365 days within each team's latest division."""
        if self.snapshot_date is None:
            self.defense_start_date = None
            return
        self.defense_start_date = self.snapshot_date - pd.Timedelta(days=window_days)
        recent = self._match_frame.loc[self._match_frame['MatchDate'].gt(self.defense_start_date)]
        home = recent[['HomeTeam', 'Division', 'FTAway']].rename(
            columns={'HomeTeam': 'Team', 'FTAway': 'Conceded'})
        away = recent[['AwayTeam', 'Division', 'FTHome']].rename(
            columns={'AwayTeam': 'Team', 'FTHome': 'Conceded'})
        appearances = pd.concat([home, away], ignore_index=True)
        appearances['Team'] = appearances['Team'].map(normalize_name)
        league_means = appearances.groupby('Division')['Conceded'].mean()
        totals = appearances.groupby(['Team', 'Division'])['Conceded'].agg(['count', 'sum'])
        for key, team in self._teams.items():
            if (key, team.division) in totals.index:
                record = totals.loc[(key, team.division)]
                team.defensive_games = int(record['count'])
                team.goals_conceded = float(record['sum'])
                team.league_goals_per_team_match = float(league_means[team.division])

    def _update_elo(self, match, k, home_advantage):
        home = self.find_team(match.home_team_name)
        away = self.find_team(match.away_team_name)
        delta = k * (match.get_result() - home.compute_expected_score(away.elo, home_advantage))
        home.elo += delta
        away.elo -= delta

    def update_all_elo(self, k=DEFAULT_K, home_advantage=DEFAULT_HOME_ADVANTAGE):
        """Recompute Elo from 1500 in chronological order; safe to call twice."""
        if not math.isfinite(k) or k <= 0 or not math.isfinite(home_advantage):
            raise ValueError('k must be positive and finite; home advantage must be finite.')
        for team in self._teams.values():
            team.elo = Team.INITIAL_ELO
        for match in self._matches:
            self._update_elo(match, k, home_advantage)

    def find_player(self, name, team_name=None):
        """Exact normalized lookup; require a team when a name is ambiguous."""
        name_key = normalize_name(name)
        if team_name is not None:
            return self._players.get((name_key, normalize_name(canonical_team(team_name))))
        matches = [p for (key, _), p in self._players.items() if key == name_key]
        if len(matches) > 1:
            teams = ', '.join(p.team for p in matches)
            raise ValueError(f'Ambiguous player {name}: specify player team ({teams}).')
        return matches[0] if matches else None

    def find_team(self, name):
        """Find a team by normalized name or explicit dataset alias."""
        return self._teams.get(normalize_name(canonical_team(name)))

    def unmatched_player_teams(self):
        """List teams in the player snapshot without any loaded match history."""
        return sorted({p.team for p in self._players.values() if self.find_team(p.team) is None})

    def _prob_goal_versus(self, player, team, minutes=90):
        """Apply observed defensive factor to the player's Poisson goal rate."""
        player_team = self.find_team(player.team)
        if normalize_name(player.team) == normalize_name(team.name):
            raise ValueError('Player and opponent cannot belong to the same team.')
        if player_team is None or player_team.division != team.division:
            raise ValueError('Opponent adjustment requires teams in the same latest division.')
        return player.prob_goal(minutes, team.defensive_factor())

    def score_probability(self, player_name, team_name, minutes=90, player_team=None):
        """Return a scenario estimate; raise on absent/ambiguous/insufficient data."""
        player = self.find_player(player_name, player_team)
        team = self.find_team(team_name)
        if player is None or team is None:
            raise ValueError('Player or opponent team not found.')
        return self._prob_goal_versus(player, team, minutes)

    def print_score_probability(self, player_name, team_name, minutes=90, player_team=None):
        """CLI wrapper around the public numeric API."""
        try:
            probability = self.score_probability(player_name, team_name, minutes, player_team)
            print(f'Exploratory P(at least one goal | {minutes:g} minutes): {probability:.1%}')
            print('Assumes the player participates; this estimate is not calibrated.')
        except ValueError as error:
            print(f'Error: {error}')

    def player_table(self):
        """Export all player/team observations; xG_Total is the CSV total, not a reconstruction."""
        columns = ['Name', 'Team', 'Position', 'Minutes', 'Goals', 'xG_Total', 'xG_per_90', 'Rating']
        return pd.DataFrame([
            [p.name, p.team, p.position, p.mins_played, p.goal, p.xg_total, p.xgperninety, p.rating]
            for p in self._players.values()
        ], columns=columns)

    def team_table(self, division=None, active_only=True):
        """Export Elo/defense; default to teams with at least five recent matches."""
        columns = ['Team', 'Division', 'Elo', 'RecentMatches', 'ConcededPerMatch', 'DefenseFactor']
        records = []
        for team in self._teams.values():
            if division is not None and team.division != division:
                continue
            if active_only and team.defensive_games < 5:
                continue
            games = team.defensive_games
            factor = (team.goals_conceded / games / team.league_goals_per_team_match
                      if games and team.league_goals_per_team_match > 0 else math.nan)
            records.append([team.name, team.division, team.elo, games,
                            team.goals_conceded / games if games else math.nan, factor])
        return pd.DataFrame(records, columns=columns).sort_values('Elo', ascending=False)

    def statistics(self):
        """Descriptive Pearson correlation using total xG and total goals.

        Includes observed zeros, excludes missing pairs, guards constant/small
        samples. Association in this snapshot does not validate future forecasts.
        """
        frame = self.player_table()
        pairs = frame[['xG_Total', 'Goals']].dropna()
        correlation = p_value = math.nan
        if len(pairs) >= 2 and (pairs.nunique() > 1).all():
            correlation, p_value = stats.pearsonr(pairs['xG_Total'], pairs['Goals'])
        ratings = frame['Rating'].dropna()
        return {'n_players': len(frame), 'n_pairs': len(pairs),
                'correlation': float(correlation), 'p_value': float(p_value),
                'mean_rating': float(ratings.mean()), 'std_rating': float(ratings.std(ddof=0))}

    def analyze_statistics(self):
        """Print the shared descriptive analysis used by both interfaces."""
        report = self.statistics()
        print(f"Players: {report['n_players']}; complete xG/goal pairs: {report['n_pairs']}")
        print(f"Pearson r (total xG vs total goals): {report['correlation']:.3f}")
        print(f"Descriptive p-value: {report['p_value']:.5g}")
        print(f"Rating mean: {report['mean_rating']:.2f}; SD: {report['std_rating']:.2f}")
        print('Snapshot association; not a forecast validation or a causal effect.')
        return report

    def visualize_data(self, show=True, output_dir=None, division='I1'):
        """Return figures for notebook/CLI; optionally save PNGs without a GUI."""
        figures = []
        frame = self.player_table()
        players = frame.loc[frame['Minutes'].ge(500)].dropna(subset=['xG_Total', 'Goals'])
        if not players.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.scatter(players['xG_Total'], players['Goals'], alpha=0.5)
            limit = max(players['xG_Total'].max(), players['Goals'].max(), 1)
            ax.plot([0, limit], [0, limit], 'r--', label='Goals = xG')
            ax.set(xlabel='Total expected goals (xG)', ylabel='Total goals',
                   title='Goals vs xG (at least 500 minutes)')
            ax.legend()
            fig.tight_layout()
            figures.append(('goals_vs_xg', fig))
        ratings = frame['Rating'].dropna()
        if not ratings.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(ratings, bins=20, edgecolor='white')
            ax.set(xlabel='Rating', ylabel='Player observations', title='Player rating distribution')
            fig.tight_layout()
            figures.append(('ratings', fig))
        teams = self.team_table(division).head(15).iloc[::-1]
        if not teams.empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.barh(teams['Team'], teams['Elo'])
            ax.set(xlabel='Elo rating', title=f'Top active teams in {division} (latest division)')
            fig.tight_layout()
            figures.append(('team_elo', fig))
        if output_dir is not None:
            target = Path(output_dir)
            target.mkdir(parents=True, exist_ok=True)
            for name, fig in figures:
                fig.savefig(target / f'{name}.png', dpi=150)
        if show:
            plt.show()
        return [fig for _, fig in figures]
