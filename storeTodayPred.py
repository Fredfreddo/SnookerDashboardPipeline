import pandas as pd
import numpy as np
import math
import os

def apply_decay_recovery(player, current_score, today, df_b, historical_stats_b):
    # Safety check if player doesn't exist in historical stats
    if player not in historical_stats_b.index:
        return current_score
        
    stats = historical_stats_b.loc[player]
    average_score = stats['average_score']
    highest_score = stats['highest_score']

    player_matches = df_b[df_b['name'] == player]
    if player_matches.empty:
        return current_score

    last_match_date = player_matches['date'].max()
    today_date = pd.to_datetime(today)
    days_inactive = (today_date - last_match_date).days

    if days_inactive > 7:
        if current_score < 1500 and current_score < highest_score:
            recovery_amount = (highest_score - current_score) * min(0.95, (days_inactive - 7) / 358.0)
            return current_score + recovery_amount
        elif current_score > average_score:
            decay_amount = (current_score - average_score) * min(1.0, (days_inactive - 7) / 49.0)
            return current_score - decay_amount

    return current_score

def getFrameWinProbability(score1, score2):
    return 1 / (1 + np.exp((score2 - score1) / 400))

def getMostPossibleOutcomes(prob1, match_length):
    outcomes = {}
    k = match_length // 2 + 1
    for r in range(k):
        outcomes[f"{k} - {r}"] = (math.comb(k + r - 1, r) * (prob1 ** k) * ((1 - prob1) ** r))
    r = match_length // 2 + 1
    for k in range(r):
        outcomes[f"{k} - {r}"] = (math.comb(k + r - 1, k) * (prob1 ** k) * ((1 - prob1) ** r))

    most_likely_outcome = max(outcomes, key=outcomes.get)
    return most_likely_outcome, outcomes[most_likely_outcome]

def main():
    # 1. Load Data
    try:
        df_a = pd.read_csv("players_score_history.csv")
        df_b = pd.read_csv("O3players_score_history.csv")
        df_a['date'] = pd.to_datetime(df_a['date'])
        df_b['date'] = pd.to_datetime(df_b['date'])
    except FileNotFoundError:
        print("Historical score CSVs not found. Exiting.")
        return

    try:
        upcoming_df = pd.read_csv("upcoming_matches.csv")
    except FileNotFoundError:
        print("No upcoming_matches.csv found. Run scraper first. Exiting.")
        return

    if upcoming_df.empty:
        print("upcoming_matches.csv is empty. No matches to predict.")
        return

    try:
        with open("tourName.txt", "r", encoding='utf-8') as f:
            currentTournamentName = f.read().strip()
    except FileNotFoundError:
        currentTournamentName = "Upcoming_Tournament"

    # Pre-calculate stats for Method B
    historical_stats_b = df_b.groupby('name').agg({'score': ['mean', 'max']})
    historical_stats_b.columns = ['average_score', 'highest_score']

    predictions_data = []

    # Get the date of the first match to use in the file name
    target_date = upcoming_df.iloc[0]['Date']
    
    # Sanitize inputs for safe file naming
    safe_date = str(target_date).replace("/", "-").replace(" ", "_")
    safe_tour_name = currentTournamentName.replace(" ", "_").replace("/", "-")

    print(f"Generating predictions for {currentTournamentName} on {target_date}...")

    # 2. Loop through matches and predict
    for index, row in upcoming_df.iterrows():
        p1 = row['Player 1']
        p2 = row['Player 2']
        best_of = int(row['Best Of'])
        match_date = row['Date']

        # Method A Calculations
        score1_a = df_a[df_a['name'] == p1].tail(1)['score'].values[0] if not df_a[df_a['name'] == p1].empty else 1500
        score2_a = df_a[df_a['name'] == p2].tail(1)['score'].values[0] if not df_a[df_a['name'] == p2].empty else 1500

        # Method B Calculations
        score1_b = df_b[df_b['name'] == p1].tail(1)['score'].values[0] if not df_b[df_b['name'] == p1].empty else 1500
        score2_b = df_b[df_b['name'] == p2].tail(1)['score'].values[0] if not df_b[df_b['name'] == p2].empty else 1500

        score1_b_adjusted = apply_decay_recovery(p1, score1_b, match_date, df_b, historical_stats_b)
        score2_b_adjusted = apply_decay_recovery(p2, score2_b, match_date, df_b, historical_stats_b)

        # Probabilities
        prob_a = getFrameWinProbability(score1_a, score2_a)
        prob_b = getFrameWinProbability(score1_b_adjusted, score2_b_adjusted)

        # Outcomes (stripping trailing parenthesis)
        most_likely_outcomeA = getMostPossibleOutcomes(prob_a, best_of)[0].split("(")[0].strip()
        most_likely_outcomeB = getMostPossibleOutcomes(prob_b, best_of)[0].split("(")[0].strip()

        predictions_data.append({
            "Player 1": p1,
            "Method A Prediction": most_likely_outcomeA,
            "Method B Prediction": most_likely_outcomeB,
            "Player 2": p2,
            "Date": match_date
        })

    # 3. Save to CSV
    output_dir = "predictions"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_filename = os.path.join(output_dir, f"{safe_tour_name}_{safe_date}_predictions.csv")

    if not os.path.exists(output_filename):
        output_df = pd.DataFrame(predictions_data)
        output_df.to_csv(output_filename, index=False)
        print(f"Successfully saved predictions to: {output_filename}")
    else:
        print(f"File {output_filename} already exists. Skipping save.")

if __name__ == "__main__":
    main()