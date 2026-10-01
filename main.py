"""Launch GoalMind from any working directory."""
import argparse
from pathlib import Path

from app.cli import GoalMindCli
from app.elo_application import EloApplication

ROOT = Path(__file__).resolve().parent
PLAYERS_FILE_PATH = ROOT / 'import' / 'Football_Player_Data-Analysis.csv'
MATCHES_FILE_PATH = ROOT / 'import' / 'Matches.csv'


def load_application(players=PLAYERS_FILE_PATH, matches=MATCHES_FILE_PATH,
                     start_date='2020-08-01', end_date=None):
    """Load both CSVs and compute ratings once; reusable by the notebook."""
    application = EloApplication()
    application.deserialize_players(players)
    application.deserialize_matches(matches, start_date, end_date)
    application.update_all_elo()
    return application


def main():
    """Parse file/date options and report loading failures without a traceback."""
    parser = argparse.ArgumentParser(description='GoalMind: historical football exploration')
    parser.add_argument('--players', type=Path, default=PLAYERS_FILE_PATH)
    parser.add_argument('--matches', type=Path, default=MATCHES_FILE_PATH)
    parser.add_argument('--start-date', default='2020-08-01')
    parser.add_argument('--end-date')
    args = parser.parse_args()
    try:
        application = load_application(args.players, args.matches, args.start_date, args.end_date)
    except ValueError as error:
        parser.error(str(error))
    print(f'Data quality: {application.load_report}')
    print(f'Historical match snapshot: {application.snapshot_date}')
    unmatched = application.unmatched_player_teams()
    if unmatched:
        print(f'Player teams without match history: {", ".join(unmatched)}')
    GoalMindCli(application).cmdloop()


if __name__ == '__main__':
    main()
