

class Team:
    ELO_BASE = 10
    ELO_SCALE = 400

    def __init__(self, name):
        self.name = name
        self.elo = 1500

    def compute_win_probability(self, opponent_elo, home_advantage = 0):
        effective_elo = self.elo + home_advantage
        return 1 / (1 + Team.ELO_BASE ** ((opponent_elo - effective_elo) / Team.ELO_SCALE))