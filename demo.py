import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import math

# --- 1. SETUP, CONFIG & TRANSLATIONS ---
st.set_page_config(page_title="Snooker Elo Dashboard", page_icon="🔴", layout="wide")

# The Dictionary-Based Localization
TRANSLATIONS = {
    "English": {
        "nav_title": "Navigation & Filters",
        "home": "Home",
        "daily_rankings": "Daily Rankings",
        "score_traj": "Score Trajectories",
        "h2h_pred": "Head2Head Prediction",
        "next_match": "Next Matches Predictions",
        "select_method": "Select Scoring Method:",
        "method_a_name": "Method A (Standard)",
        "method_b_name": "Method B (Live Form)",
        "method_a_desc": "**Modified Elo**: Incorporates standard match results update plus a factor for 70+ breaks.",
        "method_b_desc": "**Live Form Index**: Uses expected frames won, the 70+ breaks factor, plus temporal decay & recovery.",
        "inactive_days": "It has been **{days}** days since **{player}** last played.",
        "home_title": "Snooker Form Analysis & Rankings",
        "rankings_title": "Player Rankings",
        "select_date": "Select Date for Rankings:",
        "rank": "Rank",
        "no_data": "No data available on or before this date.",
        "traj_title": "Score Trajectories",
        "select_players": "Select Players to Compare:",
        "select_time": "Select Timeframe:",
        "rating_over_time": "Rating Over Time",
        "date_axis": "Date",
        "score_axis": "Elo Score",
        "no_match_data": "No match data found for these players in the selected timeframe.",
        "h2h_title": "Head2Head Prediction",
        "h2h_desc": "Select two players and the match length to see the predicted outcome based on the method chosen.",
        "select_p1": "Select Player 1:",
        "select_p2": "Select Player 2:",
        "select_length": "Select Match Length (Best of):",
        "adjusted_scores": "**Adjusted Scores after Decay/Recovery**: **{p1}**: {s1:.2f} | **{p2}**: {s2:.2f}",
        "win_prob": "**Predicted Frame Win Probability for {p1} against {p2}:** {prob:.2%}",
        "most_likely": "**Most Likely Outcome:** {outcome} with probability {prob:.2%}",
        "next_match_title": "Next Matches of {tournament} Predictions",
        "p1_header": "Player 1",
        "p2_header": "Player 2"
    },
    "中文": {
        "nav_title": "导航与筛选",
        "home": "首页",
        "daily_rankings": "每日排名",
        "score_traj": "分数轨迹",
        "h2h_pred": "交手预测",
        "next_match": "近期比赛预测",
        "select_method": "选择评分方法:",
        "method_a_name": "方法 A (标准版)",
        "method_b_name": "方法 B (即时状态)",
        "method_a_desc": "**修改版 Elo**: 结合标准比赛结果更新以及 70+ 单杆得分因素。",
        "method_b_desc": "**即时状态指数**: 使用预期获胜局数、70+ 单杆因素，以及时间衰减与恢复机制。",
        "inactive_days": "**{player}** 已经有 **{days}** 天没有参加比赛了。",
        "home_title": "斯诺克状态分析与排名",
        "rankings_title": "球员排名",
        "select_date": "选择排名日期:",
        "rank": "排名",
        "no_data": "该日期及之前没有可用数据。",
        "traj_title": "分数轨迹",
        "select_players": "选择要对比的球员:",
        "select_time": "选择时间范围:",
        "rating_over_time": "随时间变化的评分",
        "date_axis": "日期",
        "score_axis": "Elo 分数",
        "no_match_data": "在选定的时间范围内未找到这些球员的比赛数据。",
        "h2h_title": "交手预测",
        "h2h_desc": "选择两名球员和比赛局数，以查看基于所选方法的预测结果。",
        "select_p1": "选择球员 1:",
        "select_p2": "选择球员 2:",
        "select_length": "选择比赛赛制 (局/Best of):",
        "adjusted_scores": "**衰减/恢复后的调整分数**: **{p1}**: {s1:.2f} | **{p2}**: {s2:.2f}",
        "win_prob": "**{p1} 对阵 {p2} 的预期单局胜率:** {prob:.2%}",
        "most_likely": "**最可能的结果:** {outcome}，概率为 {prob:.2%}",
        "next_match_title": "{tournament} 近期比赛预测",
        "p1_header": "球员 1",
        "p2_header": "球员 2"
    }
}

# Add the Language Toggle at the very top of the sidebar
lang = st.sidebar.radio("Language / 语言", ["English", "中文"])
t = TRANSLATIONS[lang]

# Map internal keys to your actual CSV file names
ELO_FILES = {
    "Method A": "players_score_history.csv",
    "Method B": "O3players_score_history.csv"
}

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

    st.markdown(t["inactive_days"].format(days=days_inactive, player=player))

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
    st.markdown(t["most_likely"].format(outcome=most_likely_outcome, prob=outcomes[most_likely_outcome]))

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title(t["nav_title"])

app_mode = st.sidebar.radio(
    t["nav_title"],
    [t["home"], t["daily_rankings"], t["score_traj"], t["h2h_pred"], t["next_match"]],
    label_visibility="collapsed"
)

if app_mode == t["home"]:
    st.sidebar.markdown("---")

# Handle UI Method Names vs Internal Method Keys
ui_method_names = [t["method_a_name"], t["method_b_name"]]
selected_ui_method = st.sidebar.radio(t["select_method"], ui_method_names)

# Map the selected UI string back to the internal key ("Method A" or "Method B")
if selected_ui_method == t["method_a_name"]:
    selected_method = "Method A"
    st.sidebar.info(t["method_a_desc"])
else:
    selected_method = "Method B"
    st.sidebar.info(t["method_b_desc"])

current_file = ELO_FILES[selected_method]
try:
    df = load_data(current_file)
except FileNotFoundError:
    st.error(f"Could not find {current_file}.")
    st.stop()

# --- 3. VIEW 1: HOME PAGE ---
if app_mode == t["home"]:

    # Optional: Center the logo using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("snooker_logo.png", use_container_width=True)

    st.markdown(f"<h1 style='text-align: center;'>{t['home_title']}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    markdown_en = r"""
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
    
    In this case, there is no match level zero-sum property. Take example of a match where Zhao Xintong beat an amateur player 4-3:
    
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
    """

    markdown_zh = r"""
    ## 关于此仪表板
    该仪表板提供了对职业斯诺克球员即时状态的统计分析。提供了两种不同的方法（如下所述）。您可以使用侧边栏选择方法和查看内容。此评分算法可作为预测比赛结果的基准。
    
    ## 方法论
    ### 方法 A (标准版)

    在这种方法中，除了典型的 ELO 之外，还考虑了最近打出 70+ 单杆的能力。所有球员的平均分设定为 1500 分。
    
    #### 在局数层面处理 ELO
    
    对于 player1 和 player2 之间的比赛，我们得出 player1 的预期单局胜率为：
    
    $$P_{1,2} = \frac{1}{1+e^{(S_1 - S_2)/400}}$$
    
    其中 $S_1$ 和 $S_2$ 分别是 player1 和 player2 的分数。比赛结束后，分数更新如下：
    
    $$S_1' = S_1 + K \cdot (F_1 - T_{1,2} \cdot P_{1,2})$$
    
    $$S_2' = S_2 + K \cdot (F_2 - T_{2,1} \cdot P_{2,1})$$
    
    其中：
    - $F_1$ 和 $F_2$ 分别是 player1 和 player2 的实际胜局数
    - $T_{1,2} = T_{2,1} = F_1 + F_2$ 是比赛的总局数
    - $P_{2,1} = 1 - P_{1,2}$ 是 player2 对阵 player1 的预期单局胜率
    - $K$ 是决定分数更新敏感度的常数
    
    到目前为止，这是标准的局数级 ELO，满足**零和 (Zero-Sum)** 属性，这意味着一场比赛后两名球员的总分保持不变，因为：
    
    $$T_{1,2} = T_{2,1} = F_1 + F_2$$
    $$P_{2,1} + P_{1,2} = 1$$
    
    #### 引入 70+ 单杆的数量
    
    $$S_1'' = S_1' + M \cdot (B_1 - G \cdot F_1) $$
    $$S_2'' = S_2' + M \cdot (B_2 - G \cdot F_2) $$
    
    其中：
    - $B_1$ 和 $B_2$ 分别是 player1 和 player2 打出 70+ 单杆的次数
    - $G$，通常在 0.31-0.33 左右，是每局 70+ 单杆的赛季全球平均值，计算方式为赛季总 70+ 单杆数除以赛季总局数
    - $M$ 是决定 70+ 单杆在分数中权重的常数
    
    现在，在比赛层面上不再满足**零和**属性，因为两名球员可能都表现得很好（很多 70+）或很差，因此他们的分数可能同时出现正向或负向的变化。
    
    然而，在赛季层面上，所有球员的平均分保持不变，因为我们将球员的比赛表现与每局 70+ 单杆的赛季平均值进行了比较，并且整个赛季的总 70+ 单杆数和总局数是固定的，因此所有球员由 70+ 单杆引起的分数变化总和将为零。
    
    ### 方法 B (即时状态)
    
    方法 A 的主要问题是一场比赛的总局数不是固定的。
    
    #### 预期获胜局数
    
    方法 B 计算球员预期的获胜局数。对于 player1 赢得 k 局且 player2 赢得 r 局的情况，该情况的概率计算为：
    
    $$P(F_1=k,F_2=r,k \gt r) = \binom{k+r-1}{r} \cdot P_{1,2}^k \cdot P_{2,1}^r$$
    
    $$P(F_1=k,F_2=r,k \lt r) = \binom{k+r-1}{k} \cdot P_{1,2}^k \cdot P_{2,1}^r$$
    
    其中 $P_{1,2}$ 和 $P_{2,1}$ 分别是 player1 和 player2 的预期单局胜率，计算方法与方法 A 相同。
    
    考虑到所有情况，player1 和 player2 预期赢得的局数为：
    
    $$E[F_1] = \sum_{k}{} \sum_{r}^{} k \cdot P(F_1=k,F_2=r)$$
    $$E[F_2] = \sum_{k}{} \sum_{r}^{} r \cdot P(F_1=k,F_2=r)$$
    
    然后分数更新计算如下：
    
    $$S_1' = S_1 + K \cdot (F_1-E[F_1])$$
    $$S_2' = S_2 + K \cdot (F_2-E[F_2])$$
    
    在这种情况下，不存在比赛级别的零和属性。以赵心童 4-3 击败一名业余球员的比赛为例：
    
    - 方法 A 会扣除赵的分数，因为他有大约 90+\% 的预期单局胜率，但 7 局中只赢了 4 局
    - 方法 B 会稍微增加赵的分数，因为他赢得的局数略多于预期（但非常接近 4 局）
    - 两种方法都会显著增加业余球员的分数，因为他赢得了比预期多得多的局数
    
    因此，我们需要一个解决方案来平衡由方法 B 引起的分数膨胀，引入：
    
    #### 分数衰减与恢复
    
    对于球员在第 $t$ 天的比赛。检查他们上一场比赛的日期 $t'$，如果 $\Delta t=t-t'>7$，它会在我们评估球员预期获胜局数之前触发衰减或恢复。
    
    - 如果该球员当前的分数低于 1500 分且低于其历史最高分，我们将按比例（与 $\Delta t$ 以及当前分数和历史最高分之间的差值成比例）“恢复”其分数，并设有最大上限。
    - 反之，如果该球员当前的分数高于其历史平均分，我们将按比例（与 $\Delta t$ 以及当前分数和历史平均分之间的差值成比例）“衰减”其分数，并设有最大上限。
    
    通过调整衰减和恢复的超参数，我们可以控制由方法 B 引起的整体分数膨胀，将整体平均值保持在 1500 左右。
    
    这种“衰减与恢复”机制也有助于更准确地反映球员当前的竞技状态，因为长期未参赛的精英球员其技能将向其平均水平回归，而分数较低的球员将从休息中恢复。
    
    该方法中也考虑了 70+ 单杆因素。
    
    此方法的一个重要注意事项是，建议对球员的估计分数进行初始化（或预热期），否则历史平均值将不准确。
    """

    # Render the correct Markdown language
    if lang == "English":
        st.markdown(markdown_en)
    else:
        st.markdown("本网页中文为Gemini翻译")
        st.markdown(markdown_zh)

# --- 4. VIEW 2: DAILY RANKINGS ---
elif app_mode == t["daily_rankings"]:
    st.title(f"{t['rankings_title']} - {selected_ui_method}")

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    target_date = st.date_input(t["select_date"], max_date, min_value=min_date, max_value=max_date)
    target_date = pd.to_datetime(target_date)

    historical_data = df[df['date'] <= target_date]

    if not historical_data.empty:
        rankings = (historical_data.sort_values('date')
                    .groupby('name')
                    .tail(1)
                    .sort_values('score', ascending=False)
                    .reset_index(drop=True))

        rankings.index = rankings.index + 1
        rankings.index.name = t["rank"]

        st.dataframe(rankings[['name', 'score', 'date']], use_container_width=True)
    else:
        st.warning(t["no_data"])

# --- 5. VIEW 3: SCORE TRAJECTORIES ---
elif app_mode == t["score_traj"]:
    st.title(f"{t['traj_title']} - {selected_ui_method}")

    all_players = sorted(df['name'].unique())
    default_players = ["Zhao Xintong", "Mark Selby", "Judd Trump"]

    selected_players = st.multiselect(t["select_players"], all_players, default=default_players)

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()

    date_range = st.date_input(t["select_time"], [min_date, max_date], min_value=min_date, max_value=max_date)

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
                          title=f"{t['rating_over_time']} ({selected_ui_method})")

            fig.update_layout(xaxis_title=t["date_axis"], yaxis_title=t["score_axis"], hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(t["no_match_data"])

# --- 6. VIEW 4: HEAD2HEAD PREDICTION ---
elif app_mode == t["h2h_pred"]:
    st.title(f"{t['h2h_title']} - {selected_ui_method}")
    st.markdown(t["h2h_desc"])

    all_players = sorted(df['name'].unique())

    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox(t["select_p1"], all_players, index=all_players.index("Zhao Xintong") if "Zhao Xintong" in all_players else 0)
        match_length = st.selectbox(t["select_length"], [1, 3, 5, 7, 9, 11, 17, 19, 21, 25, 33, 35], index=0)
    with col2:
        player2 = st.selectbox(t["select_p2"], all_players, index=all_players.index("Mark Selby") if "Mark Selby" in all_players else 1)

    latest_scores = df.groupby('name').tail(1).set_index('name')['score']
    score1 = latest_scores.get(player1, 1500)
    score2 = latest_scores.get(player2, 1500)

    st.markdown(f"**{player1}**: {score1:.2f} | **{player2}**: {score2:.2f}")

    if selected_method == "Method B":
        historical_stats = df.groupby('name').agg({'score': ['mean', 'max']})
        historical_stats.columns = ['average_score', 'highest_score']

        score1 = apply_decay_recovery(player1, score1)
        score2 = apply_decay_recovery(player2, score2)

        st.markdown(t["adjusted_scores"].format(p1=player1, p2=player2, s1=score1, s2=score2))

    frame_win_prob = getFrameWinProbability(score1, score2)
    st.markdown(t["win_prob"].format(p1=player1, p2=player2, prob=frame_win_prob))

    getMostPossibleOutcomes(frame_win_prob, match_length)

# --- 7. VIEW 5: NEXT MATCHES PREDICTION ---
elif app_mode == t["next_match"]:
    currentTournamentName = "2026 World Open"
    st.title(t["next_match_title"].format(tournament=currentTournamentName))

    # We dynamically inject the translated headers into the markdown table string
    table_header = f"| {t['p1_header']} | {t['method_a_name']} | {t['method_b_name']} | {t['p2_header']} |"

    st.markdown(
        f"""
        {table_header}
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
        """
    )