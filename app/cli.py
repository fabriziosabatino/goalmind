"""Command-line interface; all analytical logic lives in EloApplication."""
import cmd
import shlex

from app.elo_application import EloApplication


class GoalMindCli(cmd.Cmd):
    """Explore the same data and calculations exposed by the project notebook."""

    intro = 'Welcome to GoalMind! Type help or ? to list commands.\n'
    prompt = '>> '

    def __init__(self, elo: EloApplication):
        super().__init__()
        self._elo = elo

    def do_searchplayer(self, arg):
        """searchplayer "Player name" ["Player team"]: find a player, resolving homonyms."""
        try:
            args = shlex.split(arg)
            if len(args) not in (1, 2):
                raise ValueError('Use searchplayer "Player name" ["Player team"].')
            player = self._elo.find_player(*args)
            if player is None:
                print('Player not found.')
                return
            print(f'{player}; minutes: {player.mins_played:g}; rating: {player.rating:g}')
        except ValueError as error:
            print(f'Error: {error}')

    def do_searchteam(self, arg):
        """searchteam <team name>: show overall Elo and recent defensive sample size."""
        try:
            args = shlex.split(arg)
        except ValueError as error:
            print(f'Error: {error}')
            return
        team = self._elo.find_team(' '.join(args))
        if team is None:
            print('Team not found.')
            return
        print(f'{team.name}: Elo {team.elo:.0f}; division {team.division}; '
              f'recent defensive matches {team.defensive_games}')

    def do_scoreprob(self, arg):
        """scoreprob "Player name" "Opponent" [minutes] ["Player team"]: scenario estimate."""
        try:
            args = shlex.split(arg)
            if len(args) not in (2, 3, 4):
                raise ValueError('Use scoreprob "Player name" "Opponent" [minutes] ["Player team"].')
            minutes = float(args[2]) if len(args) >= 3 else 90
            player_team = args[3] if len(args) == 4 else None
            self._elo.print_score_probability(args[0], args[1], minutes, player_team)
        except ValueError as error:
            print(f'Error: {error}')

    def do_analysis(self, arg):
        """analysis [output_directory]: print statistics and show/save shared plots."""
        try:
            args = shlex.split(arg)
            if len(args) > 1:
                raise ValueError('Use analysis [output_directory].')
            self._elo.analyze_statistics()
            self._elo.visualize_data(show=not args, output_dir=args[0] if args else None)
        except (ValueError, OSError) as error:
            print(f'Error: {error}')

    def do_export(self, arg):
        """export "directory": save player statistics and active team ratings as CSV."""
        from pathlib import Path
        try:
            args = shlex.split(arg)
            if len(args) != 1:
                raise ValueError('Use export "directory".')
            target = Path(args[0])
            target.mkdir(parents=True, exist_ok=True)
            self._elo.player_table().to_csv(target / 'players.csv', index=False)
            self._elo.team_table().to_csv(target / 'teams.csv', index=False)
            print(f'Exported to {target}.')
        except (ValueError, OSError) as error:
            print(f'Error: {error}')

    def do_exit(self, arg):
        """Exit the application."""
        print('Goodbye!')
        return True

    def do_EOF(self, arg):
        """Exit cleanly when stdin closes (Ctrl-D)."""
        print()
        return self.do_exit(arg)
