Goal Probability Predictor (ELO-Based)
Object-Oriented Programming (OOP)

ELO Rating System Implementation

Statistical Modeling

Modular Architecture

The main question explored is: What is the probability of a specific player scoring a goal against a specific team, considering the team's defensive strength?

While a player has a generic probability of scoring (based on their personal stats), this project calculates a context-aware probability by weighing that base skill against the opponent's dynamic ELO rating.

Project Structure
Plaintext
football-predictor/
├── data/
│   └── players_data.csv        # Raw stats input
│
├── data_structure/             # Core Logic (OOP)
│   ├── match.py                # Calculation engine (Player vs Team logic)
│   ├── player.py               # Player attributes and base form/xG
│   └── team.py                 # Team ELO management
│
├── deserializer/
│   └── player_deserializer.py  # Data loading and object creation
│
├── main.py                     # Execution script
└── README.md
Features
1. Team ELO System (data_structure/team.py)

Implements a dynamic rating system for teams.

Attributes: Tracks team name and current elo (starting standard is 1500).

Constants: Defines ELO_BASE (10) and ELO_SCALE (400) to standardize calculations.

Logic: The ELO represents the team's defensive solidity, used to dampen or amplify an opponent's scoring chance.

2. Player Statistics Modeling (data_structure/player.py)

Encapsulates individual player performance.

Base Probability: Calculates a player's generic threat level using metrics like Expected Goals (xG) per 90, Goals, and Assists.

Form Index: Computes a weighted index (e.g., 50% xG, 30% Goals, 20% Assists) to determine the player's current condition before the match context is applied.

3. Contextual Goal Probability (data_structure/match.py)

This is the core analytical engine. It adjusts the player's base stats based on the specific opponent.

Input: Takes a Player object (attacker) and a Team object (defender).

Algorithm:

Retrieves the Player's base probability (e.g., xgperninety).

Calculates a defensive factor based on the Team's ELO deviation from the average (1500).

Mathematical Adjustment:

DefFactor= 
1+Base 
Scale
Elo−1500
​	
 
 
1
​	
 
Returns a final probability bounded between 0 and 1.

4. Data Deserialization (deserializer/)

Parses raw CSV data to instantiate Player objects, ensuring clean separation between data storage and business logic.

Logic Explanation
The system distinguishes between Generic Ability and Match-Specific Probability:

Generic Ability: Defined in player.py. This is the player's raw statistical likelihood of scoring against an "average" team.

Match-Specific Probability: Defined in match.py.

If the opponent has a High ELO (Strong Defense), the logic calculates a def_factor < 1, reducing the player's chance to score.

If the opponent has a Low ELO (Weak Defense), the factor adjusts upward, increasing the player's probability.

Installation
Bash
git clone <your-repo-url>
cd football-predictor
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
Usage
Python
from data_structure.team import Team
from data_structure.player import Player
from data_structure.match import _prob_goal_versus

# 1. Create entities
inter = Team("Inter") # Starts with ELO 1500
lautaro = Player(name="Lautaro", xgperninety=0.65, ...)

# 2. Simulate defensive strength change
inter.elo = 1600  # Stronger defense

# 3. Calculate specific probability
prob = _prob_goal_versus(lautaro, inter)
print(f"Probability of Lautaro scoring vs Inter: {prob:.2%}")
Skills Demonstrated
Python & OOP: Clean class structures with inheritance and encapsulation.

Algorithm Design: Implementing mathematical formulas to adjust probabilities dynamically.

Data Handling: Separation of concerns between data loading (Deserializers) and data modeling.

Author: Fabrizio Sabatino
