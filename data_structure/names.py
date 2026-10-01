"""Explicit aliases connecting team names in the two supplied CSV files."""
import unicodedata

TEAM_ALIASES = {
    'AC Milan': 'Milan', 'Athletic Club': 'Ath Bilbao', 'Atletico': 'Ath Madrid',
    'Bayern': 'Bayern Munich', 'Borussia Dortmund': 'Dortmund',
    'Borussia M.Gladbach': "M'gladbach", 'Celta Vigo': 'Celta',
    'Deportivo Alaves': 'Alaves', 'Eintracht Frankfurt': 'Ein Frankfurt',
    'Espanyol': 'Espanol', 'FC Heidenheim': 'Heidenheim', 'Man Utd': 'Man United',
    'Nottingham Forest': "Nott'm Forest", 'PSG': 'Paris SG',
    'Parma Calcio 1913': 'Parma', 'RBL': 'RB Leipzig', 'Rayo Vallecano': 'Vallecano',
    'Real Betis': 'Betis', 'Real Sociedad': 'Sociedad', 'Real Valladolid': 'Valladolid',
    'Saint-Etienne': 'St Etienne', 'St. Pauli': 'St Pauli',
}


def normalize_name(name):
    """Case/accent/whitespace-insensitive lookup key; no fuzzy guessing."""
    text = unicodedata.normalize('NFKD', str(name))
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).split()).casefold()


_ALIASES = {normalize_name(k): v for k, v in TEAM_ALIASES.items()}


def canonical_team(name):
    """Map known dataset aliases to the match CSV's team names."""
    return _ALIASES.get(normalize_name(name), ' '.join(str(name).split()))
