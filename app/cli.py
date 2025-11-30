import cmd
import shlex
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from app.elo_application import EloApplication


class GoalMindCli(cmd.Cmd):

    def __init__(self, elo: EloApplication):
        super().__init__()
        self._elo = elo

    intro = "Welcome to GoalMind! Type help or ? to list commands.\n"
    prompt = ">> "

    def do_searchplayer(self, arg):
        """
        Search a player by name and print their details.
        Usage: searchplayer <player name>
        """
        player = self._elo.find_player(arg)
        if player is None:
            print("Player not found!")
            return

        print(f"Found: {player.name} ({player.team})")
        print(f"Position: {player.position}")
        print(f"Rating: {player.rating}")

    def do_searchteam(self, arg):
        """
        Search a team by name and print its ELO.
        Usage: searchteam <team name>
        """
        team = self._elo.find_team(arg)
        if team is None:
            print("Team not found!")
            return

        print(f"Team found. ELO: {team.elo:.0f}")

    def do_scoreprob(self, arg):
        """
        Compute the probability that a player scores versus a team.
        Usage: scoreprob "<Player name>" "<Team name>"
        """
        try:
            args = shlex.split(arg)
        except ValueError:
            print("Error: invalid syntax")
            return

        if len(args) != 2:
            print("Error: you must provide exactly 2 arguments")
            return

        player_name, team_name = args
        self._elo.print_score_probability(player_name, team_name)

    def do_analysis(self, arg):
        """
        Performs scientific analysis and visualization of player data.
        Usage: analysis
        """
        print("Running statistical analysis... please wait.")

        # Retrieve player data
        players_list = self._elo._players.values()

        if not players_list:
            print("No player data available.")
            return

        data = []
        for p in players_list:
            try:
                data.append({
                    "Goals": float(p.goal),
                    "xG_per_90": float(p.xgperninety),
                    "Shots": float(p.shotspergame) if p.shotspergame else 0.0,
                    "Assists": float(p.assisttotal),
                    "Rating": float(p.rating)
                })
            except ValueError:
                continue

        if not data:
            print("Error: No valid data found for analysis.")
            return

        df = pd.DataFrame(data)

        # --- Scientific Computing (Numpy) ---
        print("\n--- Statistical Report ---")

        # Correlation: xG vs Goals
        if "xG_per_90" in df.columns and "Goals" in df.columns:
            corr = np.corrcoef(df["xG_per_90"], df["Goals"])[0, 1]
            print(f"Correlation (xG vs Goals): {corr:.3f}")
            if corr > 0.7:
                print("-> Insight: High correlation. xG is a strong predictor.")
            else:
                print("-> Insight: Low correlation. Performance varies significantly.")

        print(f"Average Player Rating: {df['Rating'].mean():.2f}")

        # --- Visualisation (Matplotlib) ---
        print("Opening plots window...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot 1: Scatter xG vs Goals
        ax1.scatter(df["xG_per_90"], df["Goals"], alpha=0.5, c='blue')
        ax1.set_title("Expected Goals (xG) vs Real Goals")
        ax1.set_xlabel("xG per 90")
        ax1.set_ylabel("Total Goals")
        ax1.grid(True, linestyle='--', alpha=0.3)

        # Plot 2: Rating Histogram
        ax2.hist(df["Rating"], bins=20, color='green', edgecolor='black', alpha=0.7)
        ax2.set_title("Player Ratings Distribution")
        ax2.set_xlabel("Rating")

        plt.tight_layout()
        plt.show()

    def do_exit(self, arg):
        "Exit the application"
        print("Goodbye!")
        return True
