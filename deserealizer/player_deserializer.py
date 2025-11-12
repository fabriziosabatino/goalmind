import pandas as pd

from data_structure.player import Player


def deserialize_players(file_path : str):
    df = pd.read_csv(file_path)
    players = {}
    for _, row in df.iterrows():
        player_name = row["Player Name"]
        p = Player(
            name = player_name,
            team = row["Player Team"]
        )
        players[player_name] = p
    return players

