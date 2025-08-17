import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# -----------------------------
# Data Ingestion
# -----------------------------

@st.cache_data
def load_data():
    """
    Loads matches and deliveries data from a remote URL.
    """
    try:
        matches_url = 'https://raw.githubusercontent.com/Shivaae/IPL-DATA-/main/matches.csv'
        deliveries_url = 'https://raw.githubusercontent.com/Shivaae/IPL-DATA-/main/deliveries.csv'
        matches = pd.read_csv(matches_url)
        deliveries = pd.read_csv(deliveries_url)
    except Exception as e:
        st.error(f"Error loading data: {e}. Check your internet connection or data source.")
        st.stop()
    return matches, deliveries

# -----------------------------
# Data Preprocessing
# -----------------------------

def preprocess_data(matches, deliveries):
    """
    Cleans and preprocesses the matches and deliveries DataFrames.
    """
    # Preprocess matches
    matches.columns = matches.columns.str.strip()
    if 'id' in matches.columns:
        matches = matches.rename(columns={'id': 'match_id'})

    matches['date'] = pd.to_datetime(matches['date'], errors='coerce')
    matches['season'] = matches['date'].dt.year.fillna(0).astype(int)
    matches = matches.fillna({
        'city': 'Unknown', 'winner': 'No Result', 'player_of_match': 'None',
        'umpire1': 'Unknown', 'umpire2': 'Unknown', 'umpire3': 'Unknown',
        'result_margin': 0
    })
    if 'method' in matches.columns:
        matches['method'] = matches['method'].fillna('Normal')
    matches = matches.drop_duplicates()

    # Preprocess deliveries
    deliveries.columns = deliveries.columns.str.strip()
    if 'id' in deliveries.columns and 'match_id' not in deliveries.columns:
        deliveries = deliveries.rename(columns={'id': 'match_id'})

    deliveries = deliveries.fillna({
        'player_dismissed': 'None', 'dismissal_kind': 'None', 'fielder': 'None'
    })
    deliveries['total_runs'] = deliveries['batsman_runs'] + deliveries['extra_runs']
    deliveries['is_wicket_delivery'] = (deliveries['player_dismissed'] != 'None').astype(int)
    
    deliveries['ball_number_in_innings'] = deliveries.groupby(['match_id', 'inning'])['ball'].cumcount() + 1

    return matches, deliveries

# -----------------------------
# Feature Engineering
# -----------------------------

def get_batting_stats(deliveries):
    batting = deliveries.groupby('batsman').agg(
        batsman_runs=('batsman_runs', 'sum'),
        ball=('ball', 'count'),
        matches_played=('match_id', 'nunique')
    ).reset_index()
    dismissals = deliveries[deliveries['player_dismissed'] != 'None'].groupby('batsman').size().reset_index(name='dismissals')
    batting = batting.merge(dismissals, on='batsman', how='left').fillna({'dismissals': 0})
    batting['average'] = batting['batsman_runs'] / batting['dismissals'].clip(lower=1)
    batting['strike_rate'] = (batting['batsman_runs'] / batting['ball']) * 100
    fours = deliveries[deliveries['batsman_runs'] == 4].groupby('batsman').size().reset_index(name='fours')
    sixes = deliveries[deliveries['batsman_runs'] == 6].groupby('batsman').size().reset_index(name='sixes')
    batting = batting.merge(fours, on='batsman', how='left').merge(sixes, on='batsman', how='left').fillna(0)
    return batting.sort_values('batsman_runs', ascending=False)

def get_bowling_stats(deliveries):
    bowling = deliveries.groupby('bowler').agg(
        total_runs=('total_runs', 'sum'),
        ball=('ball', 'count'),
        matches_played=('match_id', 'nunique')
    ).reset_index()
    wickets = deliveries[
        (deliveries['player_dismissed'] != 'None') &
        (deliveries['dismissal_kind'] != 'run out') &
        (deliveries['dismissal_kind'] != 'retired hurt') &
        (deliveries['dismissal_kind'] != 'obstructing the field')
    ].groupby('bowler').size().reset_index(name='wickets')
    bowling = bowling.merge(wickets, on='bowler', how='left').fillna({'wickets': 0})
    bowling['economy'] = (bowling['total_runs'] / bowling['ball']) * 6
    bowling['overs'] = (bowling['ball'] // 6) + (bowling['ball'] % 6) / 10.0
    overs_summary = deliveries.groupby(['match_id', 'inning', 'over', 'bowler'])['total_runs'].sum().reset_index()
    maidens = overs_summary[overs_summary['total_runs'] == 0].groupby('bowler').size().reset_index(name='maidens')
    bowling = bowling.merge(maidens, on='bowler', how='left').fillna({'maidens': 0})
    return bowling.sort_values('wickets', ascending=False)

def get_advanced_batting_stats(deliveries, batting_stats):
    match_agg = deliveries.groupby('match_id').agg(
        match_total_runs=('batsman_runs', 'sum'),
        match_total_balls=('ball', 'count'),
        match_wickets=('is_wicket_delivery', 'sum')
    ).reset_index()
    match_agg['match_avg'] = match_agg['match_total_runs'] / match_agg['match_wickets'].clip(lower=1)
    match_agg['match_sr'] = (match_agg['match_total_runs'] / match_agg['match_total_balls']) * 100
    player_matches = deliveries.groupby(['batsman', 'match_id']).agg(
        player_runs=('batsman_runs', 'sum'),
        player_balls=('ball', 'count'),
        player_dismissals=('is_wicket_delivery', 'sum')
    ).reset_index()
    player_matches = player_matches.merge(match_agg, on='match_id', how='left')
    player_agg = player_matches.groupby('batsman').agg(
        total_runs=('player_runs', 'sum'),
        total_balls=('player_balls', 'sum'),
        total_dismissals=('player_dismissals', 'sum'),
        avg_match_avg=('match_avg', 'mean'),
        avg_match_sr=('match_sr', 'mean')
    ).reset_index()
    player_agg['player_avg'] = player_agg['total_runs'] / player_agg['total_dismissals'].clip(lower=1)
    player_agg['player_sr'] = (player_agg['total_runs'] / player_agg['total_balls']) * 100
    player_agg['true_average'] = (player_agg['player_avg'] / player_agg['avg_match_avg']) * 100
    player_agg['true_strike_rate'] = (player_agg['player_sr'] / player_agg['avg_match_sr']) * 100
    return batting_stats.merge(player_agg[['batsman', 'true_average', 'true_strike_rate']], on='batsman', how='left').fillna(0)

def get_advanced_bowling_stats(deliveries, bowling_stats):
    bowling_stats['bowling_avg'] = bowling_stats['total_runs'] / bowling_stats['wickets'].clip(lower=1)
    bowling_stats['bowling_sr'] = bowling_stats['ball'] / bowling_stats['wickets'].clip(lower=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        cbr = 3 / (
            (1 / bowling_stats['bowling_avg'].clip(lower=1)) +
            (1 / bowling_stats['economy'].clip(lower=1)) +
            (1 / bowling_stats['bowling_sr'].clip(lower=1))
        )
    bowling_stats['cbr'] = cbr.fillna(0)
    return bowling_stats

def get_player_form(deliveries, last_n_balls=50):
    deliveries_sorted = deliveries.sort_values(by=['match_id', 'inning', 'over', 'ball'])
    recent_batting = deliveries_sorted.groupby('batsman').tail(last_n_balls)
    batting_form_agg = recent_batting.groupby('batsman').agg(
        form_runs=('batsman_runs', 'sum'),
        form_balls=('ball', 'count'),
        form_dismissals=('is_wicket_delivery', 'sum')
    ).reset_index()
    recent_bowling = deliveries_sorted.groupby('bowler').tail(last_n_balls)
    bowling_form_agg = recent_bowling.groupby('bowler').agg(
        form_runs_conceded=('total_runs', 'sum'),
        form_balls_bowled=('ball', 'count'),
        form_wickets=('is_wicket_delivery', 'sum')
    ).reset_index()
    batting_form_agg['form'] = (
        (batting_form_agg['form_runs'] / batting_form_agg['form_balls'].clip(lower=1) * 100) * 0.6 +
        (batting_form_agg['form_runs'] / batting_form_agg['form_dismissals'].clip(lower=1)) * 0.4
    ).fillna(0)
    bowling_form_agg['form'] = (
        (1 / (bowling_form_agg['form_runs_conceded'] / bowling_form_agg['form_balls_bowled'].clip(lower=1) * 6).clip(lower=1)) * 0.7 +
        (bowling_form_agg['form_wickets'] * 10) * 0.3
    ).fillna(0)
    batting_form = batting_form_agg[['batsman', 'form']].rename(columns={'batsman': 'player'})
    bowling_form = bowling_form_agg[['bowler', 'form']].rename(columns={'bowler': 'player'})
    player_form = pd.concat([batting_form, bowling_form]).groupby('player')['form'].mean().reset_index()
    return player_form

# -----------------------------
# Team Performance Analysis
# -----------------------------

def get_team_stats(matches):
    """
    Calculates team-level statistics like win percentage.
    """
    team_wins = matches[matches['winner'] != 'No Result'].groupby('winner').size().reset_index(name='wins')
    
    # --- FIX FOR KEYERROR ---
    # The previous method was brittle. This is a more robust way to count total matches.
    # We concatenate the team1 and team2 columns and then count the occurrences of each team.
    all_teams_series = pd.concat([matches['team1'], matches['team2']])
    total_matches = all_teams_series.value_counts().reset_index()
    # The resulting columns are named 'index' and 0 by default, so we rename them explicitly.
    total_matches.columns = ['team', 'matches_played']
    # --------------------------
    
    team_stats = total_matches.merge(team_wins, left_on='team', right_on='winner', how='left').fillna({'wins': 0})
    team_stats['win_percentage'] = (team_stats['wins'] / team_stats['matches_played']) * 100
    team_stats = team_stats.drop(columns=['winner'])
    
    return team_stats

# -----------------------------
# Phase-wise Analysis
# -----------------------------

def get_phase_stats(deliveries):
    deliveries['phase'] = pd.cut(
        deliveries['over'],
        bins=[0, 6, 15, 20],
        labels=['Powerplay', 'Middle', 'Death'],
        include_lowest=True,
        right=True
    )
    phase_agg = deliveries.groupby('phase').agg(
        total_runs=('total_runs', 'sum'),
        total_balls=('ball', 'count'),
        total_wickets=('is_wicket_delivery', 'sum')
    ).reset_index()
    phase_agg['run_rate'] = (phase_agg['total_runs'] / phase_agg['total_balls']) * 6
    return phase_agg


# --- Main Application Logic (for running the script) ---
if __name__ == '__main__':
    st.set_page_config(layout="wide")
    st.title("IPL Data Analysis Dashboard")

    matches_df, deliveries_df = load_data()
    matches_df, deliveries_df = preprocess_data(matches_df, deliveries_df)

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Overview & Team Stats", "Player Deep Dive", "Match Phase Analysis"])
    
    # This call to get_team_stats now uses the fixed function
    team_stats_df = get_team_stats(matches_df)
    
    batting_stats_df = get_batting_stats(deliveries_df)
    bowling_stats_df = get_bowling_stats(deliveries_df)
    advanced_batting_df = get_advanced_batting_stats(deliveries_df, batting_stats_df)
    advanced_bowling_df = get_advanced_bowling_stats(deliveries_df, bowling_stats_df)
    player_form_df = get_player_form(deliveries_df)
    phase_stats_df = get_phase_stats(deliveries_df)

    if page == "Overview & Team Stats":
        st.header("Team Performance Overview")
        st.dataframe(team_stats_df.sort_values('win_percentage', ascending=False))
        fig_wins = px.bar(team_stats_df, x='team', y='wins', title='Total Wins by Team')
        st.plotly_chart(fig_wins)
        st.header("Top Performers")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 Run Scorers")
            st.dataframe(batting_stats_df.head(10))
        with col2:
            st.subheader("Top 10 Wicket Takers")
            st.dataframe(bowling_stats_df.head(10))

    elif page == "Player Deep Dive":
        st.header("Player Performance Analysis")
        all_players = sorted(pd.concat([batting_stats_df['batsman'], bowling_stats_df['bowler']]).unique())
        player = st.selectbox("Select a Player", all_players)
        st.subheader(f"Stats for {player}")
        col1, col2 = st.columns(2)
        with col1:
            st.write("#### Batting Stats")
            player_batting = advanced_batting_df[advanced_batting_df['batsman'] == player]
            if not player_batting.empty:
                st.dataframe(player_batting)
            else:
                st.write(f"{player} has no batting stats.")
        with col2:
            st.write("#### Bowling Stats")
            player_bowling = advanced_bowling_df[advanced_bowling_df['bowler'] == player]
            if not player_bowling.empty:
                st.dataframe(player_bowling)
            else:
                st.write(f"{player} has no bowling stats.")
        player_form_val = player_form_df[player_form_df['player'] == player]
        if not player_form_val.empty:
            st.metric("Current Form Score", f"{player_form_val['form'].values[0]:.2f}")

    elif page == "Match Phase Analysis":
        st.header("Match Phase Statistics")
        st.write("This shows the average run rate and total wickets across all matches for each phase of the game.")
        st.dataframe(phase_stats_df)
        fig_phase = px.bar(phase_stats_df, x='phase', y='run_rate', title='Average Run Rate by Phase', color='phase')
        st.plotly_chart(fig_phase)