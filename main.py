from app.cli import GoalMindCli
from app.elo_application import EloApplication

PLAYERS_FILE_PATH = "import/Football_Player_Data-Analysis.csv"
MATCHES_FILE_PATH = "import/Matches.csv"

# Main
if __name__ == "__main__":
    elo_application = EloApplication()
    elo_application.deserialize_players(PLAYERS_FILE_PATH)
    elo_application.deserialize_matches(MATCHES_FILE_PATH)
    elo_application.update_all_elo()

    # 4. Avvia la CLI (interfaccia a riga di comando)
    GoalMindCli(elo_application).cmdloop()
