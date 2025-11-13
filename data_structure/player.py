class Player:
    def __init__(self, name, team, position,
                 mins_played, tacklepergame, foulspergame,
                 xgperninety, shotspergame, xgpershot, keypasspergame,
                 dribblewonpergame, rating, interceptionpergame,
                 goal, assisttotal):
        self.name = name
        self.team = team
        self.position = position
        self.mins_played = mins_played
        self.tacklepergame = tacklepergame
        self.foulspergame = foulspergame
        self.xgperninety = xgperninety
        self.shotspergame = shotspergame
        self.xgpershot = xgpershot
        self.keypasspergame = keypasspergame
        self.dribblewonpergame = dribblewonpergame
        self.rating = rating
        self.interceptionpergame = interceptionpergame
        self.goal = goal
        self.assisttotal = assisttotal
