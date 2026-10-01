"""Team Elo rating and observed defensive statistics."""
import math


class Team:
    """Team initialized at 1500 Elo; Elo describes overall strength."""

    ELO_BASE = 10
    ELO_SCALE = 400
    INITIAL_ELO = 1500.0

    def __init__(self, name):
        self.name = name
        self.elo = self.INITIAL_ELO
        self.division = None
        self.defensive_games = 0
        self.goals_conceded = 0.0
        self.league_goals_per_team_match = math.nan

    def compute_expected_score(self, opponent_elo, home_advantage=0):
        """Elo expected score (win=1, draw=0.5), not a football win probability."""
        z = math.log(self.ELO_BASE) * (self.elo + home_advantage - opponent_elo) / self.ELO_SCALE
        if z >= 0:
            return 1 / (1 + math.exp(-z))
        exp_z = math.exp(z)
        return exp_z / (1 + exp_z)

    def compute_win_probability(self, opponent_elo, home_advantage=0):
        """Compatibility alias; the return value is an expected score."""
        return self.compute_expected_score(opponent_elo, home_advantage)

    def defensive_factor(self, min_games=5):
        """Conceded goals/game divided by league goals/team-match.

        Values below one describe fewer conceded goals than the league mean.
        This factor is not adjusted for opponent or venue strength.
        """
        if self.defensive_games < min_games or not self.league_goals_per_team_match > 0:
            raise ValueError(f'Insufficient recent defensive data for {self.name}.')
        return (self.goals_conceded / self.defensive_games) / self.league_goals_per_team_match
