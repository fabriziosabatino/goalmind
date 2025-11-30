

class Match:
    def __init__(self, home_team_name :str, away_team_name :str, home_goals :int, away_goals :int):
        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_goals = home_goals
        self.away_goals = away_goals

    def get_result(self):
        """Return 1 if home won, 0 if away won, 0.5 otherwise"""
        if self.home_goals > self.away_goals:
            return 1
        elif self.home_goals < self.away_goals:
            return 0
        else:
            return 0.5

