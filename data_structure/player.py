"""Player statistics and an explicit Poisson model for at least one goal."""
import math


def to_float(value):
    """Convert numeric CSV values; preserve missing observations as NaN.

    Blanks, '-' and None are missing. Malformed or infinite values raise
    ValueError rather than quietly becoming an observed zero.
    """
    if value is None or str(value).strip().casefold() in {'', '-', 'nan', 'na'}:
        return math.nan
    result = float(value)
    if math.isinf(result):
        raise ValueError('Statistics must be finite.')
    return result


class Player:
    """One player/team observation in the supplied statistics snapshot."""

    def __init__(self, name, team, position,
                 mins_played, tacklepergame, foulspergame,
                 xgperninety, shotspergame, xgpershot, keypasspergame,
                 dribblewonpergame, rating, interceptionpergame,
                 goal, assisttotal, xg_total=None):
        self.name = name
        self.team = team
        self.position = position
        values = locals().copy()
        for field in (
            'mins_played', 'tacklepergame', 'foulspergame', 'xgperninety',
            'shotspergame', 'xgpershot', 'keypasspergame', 'dribblewonpergame',
            'rating', 'interceptionpergame', 'goal', 'assisttotal', 'xg_total',
        ):
            number = to_float(values[field])
            if number < 0:
                raise ValueError(f'{name}: {field} cannot be negative.')
            setattr(self, field, number)

    def goals_per_90(self):
        """Return goals per 90 minutes, or NaN without positive exposure."""
        return self.goal * 90 / self.mins_played if self.mins_played > 0 else math.nan

    def assists_per_90(self):
        """Return assists per 90 minutes, or NaN without positive exposure."""
        return self.assisttotal * 90 / self.mins_played if self.mins_played > 0 else math.nan

    def prob_goal(self, minutes=90, opponent_factor=1.0):
        """Estimate P(at least one goal) = 1 - exp(-lambda).

        lambda = xG per 90 * minutes / 90 * opponent_factor. Assumes a
        constant Poisson rate and that the player actually plays these minutes.
        This is an exploratory estimate, not a calibrated match forecast.
        """
        if not math.isfinite(minutes) or not 0 <= minutes <= 120:
            raise ValueError('Minutes must be between 0 and 120.')
        if not math.isfinite(opponent_factor) or opponent_factor < 0:
            raise ValueError('Opponent factor must be finite and nonnegative.')
        if minutes == 0:
            return 0.0
        if not math.isfinite(self.xgperninety) or not self.mins_played > 0:
            raise ValueError(f'No usable xG rate/exposure for {self.name}.')
        expected_goals = self.xgperninety * minutes / 90 * opponent_factor
        return -math.expm1(-expected_goals)

    def __repr__(self):
        return f'{self.name} ({self.team}) - {self.position}'
