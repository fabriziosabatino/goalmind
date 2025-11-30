import cmd
import shlex

from app.elo_application import EloApplication


class GoalMindCli(cmd.Cmd):

    def __init__(self, elo :EloApplication):
        super().__init__()
        self._elo = elo
    intro = "Welcome to GoalMind! Type help or ? to list commands.\n"
    prompt = ">> "

    def do_searchplayer(self, arg):
        """
        Search a player by name and prints the team he plays for
        Usage: searchplayer <player name>
        """
        player = self._elo.find_player(arg)
        if player is None:
            print("Player not found!")
            return

    def do_searchteam(self, arg):
        """
        Search a team by name and prints its ELO
        Usage: searchplayer <team name>
        """
        team = self._elo.find_team(arg)
        if team is None:
            print("Team not found!")
            return

        print(f"Team found. ELO: {team.elo}")

    def do_scoreprob(self, arg):
        """
        Compute the probability that a player scores versus a team
        Usage: scoreprob "<Player name>" "<Team name>"
        """
        # Try to split the arguments by double quotes
        try:
            args = shlex.split(arg)
        except ValueError:
            print("Error: invalid syntax")
            return

        # Verify we have exactly 2 argument
        if len(args) != 2:
            print("Error: you must provide 2 arguments")
            return

        player, team = shlex.split(arg)
        self._elo.print_score_probability(player, team)

    def do_exit(self, arg):
        "Exit the application"
        print("Goodbye!")
        return True

