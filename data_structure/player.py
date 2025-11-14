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
    def form_index(self):
        """Calcola l'indice di forma basato su xG, gol e assist in 90 minuti"""

        # funzioni interne
        def goals_per_90():
            return 0 if self.mins_played == 0 else self.goal / (self.mins_played / 90)

        def assists_per_90():
            return 0 if self.mins_played == 0 else self.assisttotal / (self.mins_played / 90)

        # formula form index
        return 0.5 * self.xgperninety + 0.3 * goals_per_90() + 0.2 * assists_per_90()

    def position_weight(self):
        pos = str(self.position).upper()
        if any(x in pos for x in ["ST", "CF", "LW", "RW", "SS"]):
            return 0.25
        elif any(x in pos for x in ["CAM", "RM", "LM"]):
            return 0.15
        elif any(x in pos for x in ["CM", "CDM"]):
            return 0.0
        elif any(x in pos for x in ["CB", "LB", "RB", "LWB", "RWB"]):
            return -0.15
        elif "GK" in pos:
            return -0.30
        else:
            return 0.0

    def goal_score_raw(self):
        def defensive_penalty():
            return self.tacklepergame + self.interceptionpergame + self.foulspergame

        return (
                0.30 * self.xgperninety +
                0.25 * self.shotspergame +
                0.15 * self.xgpershot +
                0.10 * self.keypasspergame +
                0.05 * self.dribblewonpergame +
                0.05 * self.rating -
                0.10 * defensive_penalty()
        )

        # ---- Goal score totale ----

    def goal_score(self):
        return self.goal_score_raw() + self.position_weight() + 0.4 * self.form_index()

    def prob_goal(self):
        score = self.goal_score()
        return max(0, min(score, 1))

        # ---- Will score (soglia 0.5) ----

    def will_score(self):
        return 1 if self.prob_goal() > 0.5 else 0

    def __repr__(self):
        return f"{self.name} ({self.team}) - {self.position} | Prob Goal: {self.prob_goal():.2f}"