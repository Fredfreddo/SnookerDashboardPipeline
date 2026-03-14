import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="Snooker Elo Dashboard", layout="wide")

# Map shorter display names to your actual CSV file names
ELO_FILES = {
    "Method A": "players_score_history.csv",
    "Method B": "O3players_score_history.csv"
}

# Explanations for each method to display in the sidebar
METHOD_DESCRIPTIONS = {
    "Method A": "**Modified Elo**: Incorporates standard match results update plus a factor for 70+ breaks.",
    "Method B": "**Live Form Index**: Uses expected frames won, the 70+ breaks factor, plus temporal decay & recovery."
}

# Cache the data loading so switching toggles is instant
@st.cache_data
def load_data(filename):
    df = pd.read_csv(filename)
    df['date'] = pd.to_datetime(df['date'])
    return df

def apply_decay_recovery(player, current_score):
    stats = historical_stats.loc[player]
    average_score = stats['average_score']
    highest_score = stats['highest_score']

    last_match_date = df[df['name'] == player]['date'].max()
    days_inactive = (pd.Timestamp.now() - last_match_date).days

    # display how many days the player has been inactive
    st.markdown(f"It has been **{days_inactive}** days since **{player}** last played.")

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
    # if player 1 wins
    k = match_length // 2 + 1
    for r in range(k):
        outcomes[f"{k} - {r}"] = (math.comb(k + r - 1, r) * (prob1 ** k) * ((1 - prob1) ** r))
    # if player 2 wins
    r = match_length // 2 + 1
    for k in range(r):
        outcomes[f"{k} - {r}"] = (math.comb(k + r - 1, k) * (prob1 ** k) * ((1 - prob1) ** r))
    
    # print out the most likely outcome with scoreline and probability
    most_likely_outcome = max(outcomes, key=outcomes.get)
    st.markdown(f"**Most Likely Outcome:** {most_likely_outcome} with probability {outcomes[most_likely_outcome]:.2%}")

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("Navigation & Filters")

# Added "Home" as the first (default) option
app_mode = st.sidebar.radio("Choose a view:", ["Home", "Daily Rankings", "Score Trajectories", "Head2Head Prediction", "Next Matches Predictions"])
if app_mode == "Home":
    st.sidebar.markdown("---")

# Toggle for the Elo calculation method
selected_method = st.sidebar.radio("Select Scoring Method:", list(ELO_FILES.keys()))

# Display the brief explanation dynamically based on the selection
st.sidebar.info(METHOD_DESCRIPTIONS[selected_method])

# Load the data for the currently selected method
current_file = ELO_FILES[selected_method]
try:
    df = load_data(current_file)
except FileNotFoundError:
    st.error(f"Could not find {current_file}. Please ensure your CSV files are in the same folder as app.py and named correctly.")
    st.stop()

# --- 3. VIEW 1: HOME PAGE ---
if app_mode == "Home":
    st.image("snooker_logo.png", width=450)
    st.title("Snooker Form Analysis & Rankings")

    # Placeholder markdown for you to fill in
    st.markdown(r"""
    ## About This Dashboard
    This dashboard provides a statistical analysis of professional snooker player's live form. Two different methods are provided (explained below). You may use the sidebar to choose the methods and what to see. This scoring algorithm may serve as a baseline to predict matches outcomes.
    
    ## The Methodologies
    ### Method A

    In this approach, apart from typical ELO, recent abilities to make 70+ breaks are taken into consideration. Average score for all players is 1500.
    
    #### ELO is handled on frame level
    
    For a Match between player1 and player2, we have expected frame win rate for player1 as:
    
    $$P_{1,2} = \frac{1}{1+e^{(S_1 - S_2)/400}}$$
    
    Where $S_1$ and $S_2$ are the scores of player1 and player2 respectively. After a match, the scores are updated as:
    
    $$S_1' = S_1 + K \cdot (F_1 - T_{1,2} \cdot P_{1,2})$$
    
    $$S_2' = S_2 + K \cdot (F_2 - T_{2,1} \cdot P_{2,1})$$
    
    Where:
    - $F_1$ and $F_2$ are the actual frame wins for player1 and player2 respectively
    - $T_{1,2} = T_{2,1} = F_1 + F_2$ is the total frames played in the match
    - $P_{2,1} = 1 - P_{1,2}$ is the expected frame win rate for player2 against player1
    - $K$ is a constant that determines the sensitivity of score updates
    
    This so far is standard frame-wise ELO, satisfying the **_Zero-Sum_** property, meaning the total score of both players remains constant after a match, because:
    
    $$T_{1,2} = T_{2,1} = F_1 + F_2$$
    $$P_{2,1} + P_{1,2} = 1$$
    
    #### Count of 70+ breaks is introduced
    
    $$S_1'' = S_1' + M \cdot (B_1 - G \cdot F_1) $$
    $$S_2'' = S_2' + M \cdot (B_2 - G \cdot F_2) $$
    
    Where:
    - $B_1$ and $B_2$ are the counts of 70+ breaks for player1 and player2 respectively
    - $G$, usually around 0.31-0.33, is the season global average of 70+ breaks per frame, calculated as total 70+ breaks divided by total frames in the season
    - $M$ is a constant that determines the weight of 70+ breaks in the score
    
    Now the **_Zero-Sum_** property is no longer satisfied on the match level, since two players could play both well (many 70+) or bad and therefore have both positive or negative changes in scores.
    
    However, on a season level, the average score of all players remains constant, because we compared player's match performance against the seasonal average 70+ breaks per frame, and the total 70+ breaks and total frames are fixed for the season, and therefore the total score change from 70+ breaks across all players will sum to zero.
    
    ### Method B
    
    The main problem for Method A is that the number of total frames in a match is not fixed.
    
    #### Expected Number of Frames won
    
    Method B calculates the expected number of frames won by players. For a scenario when player 1 wins k frames and player 2 wins r frames, the probability of this scenario is calculated as:
    
    $$P(F_1=k,F_2=r,k \gt r) = \binom{k+r-1}{r} \cdot P_{1,2}^k \cdot P_{2,1}^r$$
    
    $$P(F_1=k,F_2=r,k \lt r) = \binom{k+r-1}{k} \cdot P_{1,2}^k \cdot P_{2,1}^r$$
    
    Where $P_{1,2}$ and $P_{2,1}$ are the expected frame win rates for player1 and player2 respectively, calculated as in Method A.
    
    Considering all scenarios, the expected number of frames won by player1 and player 2 are:
    
    $$E[F_1] = \sum_{k}{} \sum_{r}^{} k \cdot P(F_1=k,F_2=r)$$
    $$E[F_2] = \sum_{k}{} \sum_{r}^{} r \cdot P(F_1=k,F_2=r)$$
    
    Then the score updates are calculated as:
    
    $$S_1' = S_1 + K \cdot (F_1-E[F_1])$$
    $$S_2' = S_2 + K \cdot (F_2-E[F_2])$$
    
    In this case, there is no match level zero-sum property. Take example of a match where Zhao Xintong best an amateur player 4-3:
    
    - Method A would deduct Zhao's score because he has about 90+\% expected frame win rate but only won 4 out of 7
    - Method B would increase Zhao's score slightly because he won more frames than expected (but very close to 4)
    - Both options would increase the amateur player's score significantly because he won much more frames than expected
    
    Therefore, we need a solution to balance out the inflation of scores caused by Method B, introducing:
    
    #### Score Decay and Recovery
    
    For a match on day $t$ for a player. Check their last match's date $t'$, if $\Delta t=t-t'>7$, it triggers decay or recovery before we evaluate the matches expected number of frames won by players.
    
    - if the player's current score is below 1500 and their historical highest score, we "recover" their score by an amount proportional to $\Delta t$ and the difference between current score and historical highest, with a maximum cap.
    - else, if the player's current score is above its historical average score, we "decay" their score by an amount proportional to $\Delta t$ and the difference between the current score and the historical average, with a maximum cap.
    
    By adjusting the hyperparameters of decay and recovery, we can control the overall inflation of scores caused by Method B, keeping the overall average around 1500.
    
    This "decay and recovery" mechanism also helps to reflect players' current forms more accurately, as elite players who have been inactive for a while will have their skills regressed towards their average, and players with lower scores will recover from the break.
    
    70+ breaks are considered in this method as well.
    
    A important note to this method is that an initialization of players' estimated scores are recommended (or a burn-in period), otherwise the historical average would not be accurate.
    """)

# --- 4. VIEW 2: DAILY RANKINGS ---
elif app_mode == "Daily Rankings":
    st.title(f"Player Rankings - {selected_method}")

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    target_date = st.date_input("Select Date for Rankings:", max_date, min_value=min_date, max_value=max_date)
    target_date = pd.to_datetime(target_date)

    historical_data = df[df['date'] <= target_date]

    if not historical_data.empty:
        rankings = (historical_data.sort_values('date')
                    .groupby('name')
                    .tail(1)
                    .sort_values('score', ascending=False)
                    .reset_index(drop=True))

        rankings.index = rankings.index + 1
        rankings.index.name = "Rank"

        st.dataframe(rankings[['name', 'score', 'date']], use_container_width=True)
    else:
        st.warning("No data available on or before this date.")

# --- 5. VIEW 3: SCORE TRAJECTORIES ---
elif app_mode == "Score Trajectories":
    st.title(f"Score Trajectories - {selected_method}")

    all_players = sorted(df['name'].unique())
    default_players = ["Zhao Xintong", "Mark Selby", "Judd Trump"]

    selected_players = st.multiselect("Select Players to Compare:", all_players, default=default_players)

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    date_range = st.date_input("Select Timeframe:", [min_date, max_date], min_value=min_date, max_value=max_date)

    if selected_players and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

        mask = (df['name'].isin(selected_players)) & (df['date'] >= start_date) & (df['date'] <= end_date)
        df_filtered = df[mask]

        if not df_filtered.empty:
            fig = px.line(df_filtered,
                          x='date',
                          y='score',
                          color='name',
                          markers=True,
                          title=f"Rating Over Time ({selected_method})")

            fig.update_layout(xaxis_title="Date", yaxis_title="Elo Score", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No match data found for these players in the selected timeframe.")

elif app_mode == "Head2Head Prediction":
    st.title(f"Head2Head Prediction - {selected_method}")
    st.markdown("Select two players and the match length to see the predicted outcome based on the method chosen.")
    # scrolldown selectors for player 1, player 2, and match length
    all_players = sorted(df['name'].unique())
    player1 = st.selectbox("Select Player 1:", all_players, index=all_players.index("Zhao Xintong"))
    player2 = st.selectbox("Select Player 2:", all_players, index=all_players.index("Mark Selby"))
    match_length = st.selectbox("Select Match Length (Best of):", [1, 3, 5, 7, 9, 11, 17, 19, 21, 25, 33, 35], index=0)

    # Get the latest scores for both players and display them
    latest_scores = df.groupby('name').tail(1).set_index('name')['score']
    score1 = latest_scores.get(player1, 1500)
    score2 = latest_scores.get(player2, 1500)
    st.markdown(f"**{player1}**: {score1:.2f} | **{player2}**: {score2:.2f}")

    # consider decay and recovery if Method B
    if selected_method == "Method B":
        # Get the historical average and highest scores for both players
        historical_stats = df.groupby('name').agg({'score': ['mean', 'max']})
        historical_stats.columns = ['average_score', 'highest_score']

        score1 = apply_decay_recovery(player1, score1)
        score2 = apply_decay_recovery(player2, score2)
        # display the adjusted scores after decay and recovery
        st.markdown(f"**Adjusted Scores after Decay/Recovery**: **{player1}**: {score1:.2f} | **{player2}**: {score2:.2f}")

    # get the frame win probability for player1 against player2
    frame_win_prob = getFrameWinProbability(score1, score2)
    st.markdown(f"**Predicted Frame Win Probability for {player1} against {player2}:** {frame_win_prob:.2%}")

    # get the most likely outcome for the match
    getMostPossibleOutcomes(frame_win_prob, match_length)

elif app_mode == "Next Matches Predictions":
    currentTournamentName = "2026 World Open"
    st.title(f"Next Matches of {currentTournamentName} Predictions")
    st.markdown(
        """
        | Player 1 | Method A | Method B | Player 2 |
        |---------------|----|----|---------------|
        |John Higgins|5-1|5-0|Liam Highfield|
        |Lei Peifan|5-2|5-3|Ryan Day|
        |David Lilley|1-5|0-5|Shaun Murphy|
        |Umut Dikme|2-5|2-5|Xu Yichen|
        |Zhou Yuelong|5-1|5-1|He Guoqiang|
        |Mark Allen|5-0|5-0|Antoni Kowalski|
        |Jack Lisowski|5-1|5-1|Cheung Ka Wai|
        |Antony McGill|3-5|3-5|Stuart Bingham|
        |Chang Bingyu|3-5|1-5|Wu Yize|
        |Zak Surety|5-1|5-2|Allan Taylor|
        |Lyu Haotian|0-5|1-5|Kyren Wilson|
        |Zhao Hanyang|2-5|2-5|Robbie Williams|
        |Elliot Slessor|5-1|5-1|Daniel Wells|
        |Matthew Stevens|2-5|3-5|Hossein Vafaei|
        |David Grace|2-5|3-5|Thepchaiya Un-Nooh|
        |Marco Fu|5-2|5-3|Iulian Boiko|
        |Ali Carter|5-1|5-1|Martin O'Donnell|
        |Aaron Hill|2-5|1-5|Gary Wilson|
        |Yao Pengcheng|1-5|1-5|Sam Cragie|
        
        """)