import pandas as pd
import re

# read csv file "platers_score_history.csv"
df = pd.read_csv("players_score_history.csv", encoding='utf-8')
# get unique player names
player_names = df["name"].unique()
# write player names to file "player_list.txt"
with open("player_list.txt", "w", encoding='utf-8') as f:
    for name in player_names:
        f.write(name.strip() + "\n")
print("Player list generated successfully.")