from data_structure.match import Match
from data_structure.player import Player
from data_structure.team import Team

import pandas as pd

class EloApplication:
    DEFAULT_K = 25
    DEFAULT_HOME_ADVANTAGE = 40

    def __init__(self):
        self._players = {}
        self._teams = {}
        self._matches = []

    def _register_player(self, player :Player):
        self._players[player.name] = player

    def _register_match(self, match :Match):
        self._matches.append(match)

        if match.home_team_name not in self._teams:
            self._teams[match.home_team_name] = Team(match.home_team_name)

        if match.away_team_name not in self._teams:
            self._teams[match.away_team_name] = Team(match.away_team_name)

    def deserialize_matches(self, file_path: str, start_date: str = "2020-08-01"):
        df = pd.read_csv(file_path, dtype={2: str})

        matches = []
        for _, row in df.iterrows():
            if row["MatchDate"] > start_date:
                self._register_match(Match(
                    home_team_name=row["HomeTeam"],
                    away_team_name=row["AwayTeam"],
                    home_goals=row["FTHome"],
                    away_goals=row["FTAway"]
                ))

    def deserialize_players(self, file_path: str):
        df = pd.read_csv(file_path)
        players = {}

        for _, row in df.iterrows():
            player_name = row["Player Name"]
            self._register_player(Player(
                name=player_name,
                team=row["Player Team"], position=row["Position 1"],
                mins_played=row["Mins Played"],
                tacklepergame=row["tacklePerGame"],
                foulspergame=row["foulsPerGame"],
                interceptionpergame=row["interceptionPerGame"],
                xgperninety=row["xGPerNinety"],
                shotspergame=row["shotsPerGame"],
                xgpershot=row["xGPerShot"],
                keypasspergame=row["keyPassPerGame"],
                dribblewonpergame=row["dribbleWonPerGame"],
                rating=row["rating"],
                goal=row["goal"],
                assisttotal=row["assistTotal"]
            ))

        return players

    def _update_elo(self, match: Match, k :int, home_advantage :int):
        result = match.get_result()
        team_home = self._teams[match.home_team_name]
        team_away = self._teams[match.away_team_name]

        # expected probability
        exp_home = team_home.compute_win_probability(team_away.elo, home_advantage)
        exp_away = 1 - exp_home

        # Update ELO of teams
        team_home.elo += k * (result - exp_home)
        team_away.elo += k * ((1 - result) - exp_away)

    def update_all_elo(self, k :int = DEFAULT_K, home_advantage :int = DEFAULT_HOME_ADVANTAGE):
        for match in self._matches:
            self._update_elo(match, k, home_advantage)

    def find_player(self, name :str):
        return self._players.get(name)

    def find_team(self, name :str):
        return self._teams.get(name)

    def _prob_goal_versus(self, player :Player, team :Team):
        #find formula and put in
        return 0

    def print_score_probability(self, player_name :str, team_name :str):
        player = self.find_player(player_name)
        if player is None:
            print("Error: Player not found")
            return

        team = self.find_team(team_name)
        if team is None:
            print("Error: Team not found")
            return

        score_prob = self._prob_goal_versus(player, team)
        print(f"Goal probability: {score_prob}")



