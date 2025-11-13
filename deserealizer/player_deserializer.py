import pandas as pd

from data_structure.player import Player


def deserialize_players(file_path : str):
    df = pd.read_csv(file_path)
    players = {}
    for _, row in df.iterrows():
        player_name = row["Player Name"]
        p = Player(
            name = player_name,
            team = row["Player Team"],position = row["Position 1"],
            mins_played = row["Mins Played"],
            tacklepergame = row["tacklePerGame"],
            foulspergame = row["foulsPerGame"],
            interceptionpergame = row["interceptionPerGame"],
            xgperninety = row["xGPerNinety"],
            shotspergame = row["shotsPerGame"],
            xgpershot = row["xGPerShot"],
            keypasspergame = row["keyPassPerGame"],
            dribblewonpergame = row["dribbleWonPerGame"],
            rating = row["rating"],
            goal = row["goal"],
            assisttotal = row["assistTotal"]
        )
        players[player_name] = p

    return players

