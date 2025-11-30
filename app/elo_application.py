from data_structure.match import Match
from data_structure.player import Player
from data_structure.team import Team

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns


class EloApplication:
    DEFAULT_K = 25
    DEFAULT_HOME_ADVANTAGE = 40

    def __init__(self):
        self._players = {}
        self._teams = {}
        self._matches = []

    def analyze_statistics(self):
        print("--- Statistical Analysis ---")
        data = []
        for player in self._players.values():
            matches_played = player.mins_played / 90
            estimated_total_xg = player.xgperninety * matches_played

            data.append({
                "Name": player.name,
                "Goals": player.goal,
                "xG_Total": estimated_total_xg,
                "Rating": player.rating
            })

        df = pd.DataFrame(data)
        # Filter to avoid empty or null data
        df = df[df['xG_Total'] > 0]

        if df.empty:
            print("Insufficient data for analysis.")
            return

        # Calculate Pearson correlation
        correlation, p_value = stats.pearsonr(df['xG_Total'], df['Goals'])

        print(f"Correlation between total xG and Goals scored: {correlation:.3f}")
        print(f"Statistical significance (p-value): {p_value:.5f}")

        mean_rating = np.mean(df['Rating'])
        std_rating = np.std(df['Rating'])
        print(f"Mean Rating: {mean_rating:.2f} (Std Dev: {std_rating:.2f})")

    def visualize_data(self):
        print("Generating plots...")
        player_data = []
        for p in self._players.values():
            if p.mins_played > 500:  # Filter players with few minutes
                player_data.append({
                    "Goals": p.goal,
                    "xG": p.xgperninety * (p.mins_played / 90),
                    "Team": p.team
                })
        df_players = pd.DataFrame(player_data)

        if not df_players.empty:
            # Plot 1: Goals vs Expected Goals
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=df_players, x='xG', y='Goals', hue='Team', legend=False, alpha=0.7)

            # Reference line (perfect prediction)
            max_val = max(df_players['xG'].max(), df_players['Goals'].max())
            plt.plot([0, max_val], [0, max_val], 'r--', label='Expected Performance')

            plt.title('Player Performance: Real Goals vs Expected Goals (xG)')
            plt.xlabel('Expected Goals (xG)')
            plt.ylabel('Scored Goals')
            plt.legend()
            plt.show()

        team_data = [{"Team": t.name, "ELO": t.elo} for t in self._teams.values()]
        df_teams = pd.DataFrame(team_data)

        if not df_teams.empty:
            # Plot 2: Top Teams by ELO
            df_teams = df_teams.sort_values(by="ELO", ascending=False).head(15)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df_teams, x="ELO", y="Team", palette="viridis")
            plt.title('Top 15 Teams by ELO Rating')
            plt.xlabel('ELO Score')
            plt.xlim(1400, df_teams['ELO'].max() + 50)
            plt.show()

    def _register_player(self, player :Player):
        self._players[player.name] = player

    def _register_match(self, match :Match):
        self._matches.append(match)

        if match.home_team_name not in self._teams:
            self._teams[match.home_team_name] = Team(match.home_team_name)

        if match.away_team_name not in self._teams:
            self._teams[match.away_team_name] = Team(match.away_team_name)

    def deserialize_matches(self, file_path: str, start_date: str = "2020-08-01"):
        print(f"Deserializing matches from {file_path}")
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
        print(f"Deserializing players from {file_path}")
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

    def _prob_goal_versus(self, player: Player, team: Team):
        elo_def = team.elo

        base_prob = player.prob_goal()
        
        def_factor = 1 / (1 + Team.ELO_BASE ** ((elo_def - 1500) / Team.ELO_SCALE))

        adj_def_factor = def_factor * 2
        final_prob = base_prob * adj_def_factor

        return max(0, min(final_prob, 1))

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



