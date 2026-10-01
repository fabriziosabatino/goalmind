"""A completed match used to update Elo chronologically."""
import math


class Match:
    """Match with nonnegative integer goals and optional date/division metadata."""

    def __init__(self, home_team_name, away_team_name, home_goals, away_goals,
                 date=None, division=None):
        for goals in (home_goals, away_goals):
            if not math.isfinite(goals) or goals < 0 or int(goals) != goals:
                raise ValueError('A completed match requires nonnegative integer goals.')
        if home_team_name == away_team_name:
            raise ValueError('A team cannot play against itself.')
        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_goals = int(home_goals)
        self.away_goals = int(away_goals)
        self.date = date
        self.division = division

    def get_result(self):
        """Return 1 for a home win, 0 for an away win and 0.5 for a draw."""
        if self.home_goals > self.away_goals:
            return 1.0
        if self.home_goals < self.away_goals:
            return 0.0
        return 0.5
