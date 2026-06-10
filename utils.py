import sqlite3
import pandas as pd
import numpy as np
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ipl.db")

TEAM_COLORS = {
    "RCB": "#EC1C24", "MI": "#004BA0", "CSK": "#FFCB05",
    "KKR": "#3A225D", "SRH": "#F7A721", "RR": "#2D4DB3",
    "GT": "#1C1C1C", "PBKS": "#ED1B24", "DC": "#0078BC",
    "LSG": "#A4CFD8",
}

TEAM_FULL = {
    "RCB": "Royal Challengers Bengaluru",
    "MI": "Mumbai Indians",
    "CSK": "Chennai Super Kings",
    "KKR": "Kolkata Knight Riders",
    "SRH": "Sunrisers Hyderabad",
    "RR": "Rajasthan Royals",
    "GT": "Gujarat Titans",
    "PBKS": "Punjab Kings",
    "DC": "Delhi Capitals",
    "LSG": "Lucknow Super Giants",
}

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query_df(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def query_one(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(sql, params).fetchone()
    conn.close()
    return row

def query_all(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── CHART HELPERS ────────────────────────────────────────────────────────────

DARK_BG = "#0d0d14"
CARD_BG = "#13131f"
ORANGE = "#ff6b2b"
TEXT_COLOR = "#e8e8f0"
GRID_COLOR = "#1e1e30"

def _setup_dark_fig(w=10, h=5):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, color=GRID_COLOR, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    return fig, ax

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=130,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ── HOME STATS ───────────────────────────────────────────────────────────────

def get_home_stats():
    total_matches = query_one("SELECT COUNT(*) FROM matches WHERE match_result='completed'")[0]
    total_teams = query_one("SELECT COUNT(*) FROM points_table")[0]
    total_players = query_one("SELECT COUNT(*) FROM batting")[0]
    total_runs = query_one("SELECT SUM(runs) FROM batting")[0]
    total_wickets = query_one("SELECT SUM(wickets) FROM bowling")[0]
    seasons = 1  # 2026 IPL season
    orange_cap = query_one("SELECT batsman, team, runs FROM batting ORDER BY runs DESC LIMIT 1")
    purple_cap = query_one("SELECT bowler, team, wickets FROM bowling ORDER BY wickets DESC LIMIT 1")
    top_team = query_one("SELECT team, wins FROM points_table ORDER BY wins DESC LIMIT 1")
    return dict(
        total_matches=total_matches,
        total_teams=total_teams,
        total_players=total_players,
        total_runs=int(total_runs) if total_runs else 0,
        total_wickets=int(total_wickets) if total_wickets else 0,
        seasons=seasons,
        orange_cap=dict(orange_cap) if orange_cap else {},
        purple_cap=dict(purple_cap) if purple_cap else {},
        top_team=dict(top_team) if top_team else {},
    )

# ── PLAYERS ──────────────────────────────────────────────────────────────────

def get_top_batters(n=15):
    return query_all("SELECT * FROM batting ORDER BY runs DESC LIMIT ?", (n,))

def get_top_bowlers(n=15):
    return query_all("SELECT * FROM bowling ORDER BY wickets DESC LIMIT ?", (n,))

def get_top_fielders(n=10):
    return query_all("SELECT * FROM fielding ORDER BY catches DESC LIMIT ?", (n,))

def search_player(name):
    like = f"%{name}%"
    bat = query_all("SELECT * FROM batting WHERE batsman LIKE ?", (like,))
    bowl = query_all("SELECT * FROM bowling WHERE bowler LIKE ?", (like,))
    return bat, bowl

# ── TEAMS ────────────────────────────────────────────────────────────────────

def get_points_table():
    return query_all("SELECT * FROM points_table ORDER BY position")

def get_team_stats(team_abbr):
    bat = query_all("SELECT * FROM batting WHERE team=? ORDER BY runs DESC", (team_abbr,))
    bowl = query_all("SELECT * FROM bowling WHERE team=? ORDER BY wickets DESC", (team_abbr,))
    pts = query_all("SELECT * FROM points_table WHERE team LIKE ?", (f"%{TEAM_FULL.get(team_abbr, team_abbr)}%",))
    matches_w = query_all(
        "SELECT * FROM matches WHERE match_winner=? AND match_result='completed' ORDER BY match_id",
        (team_abbr,)
    )
    return dict(bat=bat, bowl=bowl, pts=pts[0] if pts else {}, wins=matches_w)

def get_head_to_head(t1, t2):
    rows = query_all(
        """SELECT match_winner, COUNT(*) as cnt FROM matches
           WHERE match_result='completed' AND
                 ((team1=? AND team2=?) OR (team1=? AND team2=?))
           GROUP BY match_winner""",
        (t1, t2, t2, t1)
    )
    return rows

# ── MATCHES ──────────────────────────────────────────────────────────────────

def get_all_matches():
    return query_all("SELECT * FROM matches ORDER BY match_id")

def get_match_filters():
    venues = query_all("SELECT DISTINCT venue FROM matches ORDER BY venue")
    teams = query_all("SELECT DISTINCT team1 FROM matches ORDER BY team1")
    return venues, teams

# ── STATS / CHARTS ───────────────────────────────────────────────────────────

def chart_top_batters():
    df = query_df("SELECT batsman, runs, team FROM batting ORDER BY runs DESC LIMIT 10")
    fig, ax = _setup_dark_fig(11, 5)
    colors = [TEAM_COLORS.get(t, ORANGE) for t in df["team"]]
    bars = ax.bar(df["batsman"], df["runs"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, fmt="%d", color=TEXT_COLOR, fontsize=8, padding=3)
    ax.set_xlabel("Players", fontsize=10)
    ax.set_ylabel("Runs", fontsize=10)
    ax.set_title("Top 10 Run Scorers – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_top_bowlers():
    df = query_df("SELECT bowler, wickets, team FROM bowling ORDER BY wickets DESC LIMIT 10")
    fig, ax = _setup_dark_fig(11, 5)
    colors = [TEAM_COLORS.get(t, ORANGE) for t in df["team"]]
    bars = ax.bar(df["bowler"], df["wickets"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, fmt="%d", color=TEXT_COLOR, fontsize=8, padding=3)
    ax.set_xlabel("Bowlers", fontsize=10)
    ax.set_ylabel("Wickets", fontsize=10)
    ax.set_title("Top 10 Wicket Takers – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_team_wins():
    df = query_df("SELECT team, wins FROM points_table ORDER BY wins DESC")
    # Use abbreviations
    abbr_map = {v: k for k, v in TEAM_FULL.items()}
    df["abbr"] = df["team"].apply(lambda x: abbr_map.get(x, x[:3].upper()))
    fig, ax = _setup_dark_fig(10, 5)
    colors = [TEAM_COLORS.get(a, ORANGE) for a in df["abbr"]]
    bars = ax.barh(df["abbr"], df["wins"], color=colors, height=0.6, zorder=3)
    ax.bar_label(bars, fmt="%d", color=TEXT_COLOR, fontsize=9, padding=3)
    ax.set_xlabel("Wins", fontsize=10)
    ax.set_title("Team Wins – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_strike_rates():
    df = query_df("SELECT batsman, strike_rate, team FROM batting ORDER BY strike_rate DESC LIMIT 10")
    fig, ax = _setup_dark_fig(11, 5)
    colors = [TEAM_COLORS.get(t, ORANGE) for t in df["team"]]
    bars = ax.bar(df["batsman"], df["strike_rate"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, fmt="%.1f", color=TEXT_COLOR, fontsize=8, padding=3)
    ax.set_xlabel("Players", fontsize=10)
    ax.set_ylabel("Strike Rate", fontsize=10)
    ax.set_title("Top Strike Rates – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_economy_rates():
    df = query_df("SELECT bowler, economy, team FROM bowling WHERE overs >= 16 ORDER BY economy LIMIT 10")
    fig, ax = _setup_dark_fig(11, 5)
    colors = [TEAM_COLORS.get(t, ORANGE) for t in df["team"]]
    bars = ax.bar(df["bowler"], df["economy"], color=colors, width=0.6, zorder=3)
    ax.bar_label(bars, fmt="%.2f", color=TEXT_COLOR, fontsize=8, padding=3)
    ax.set_xlabel("Bowlers", fontsize=10)
    ax.set_ylabel("Economy Rate", fontsize=10)
    ax.set_title("Best Economy Rates (min 16 overs) – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_toss_impact():
    df = query_df("""
        SELECT toss_decision,
               SUM(CASE WHEN toss_winner=match_winner THEN 1 ELSE 0 END) as toss_wins,
               COUNT(*) as total
        FROM matches WHERE match_result='completed'
        GROUP BY toss_decision
    """)
    df["toss_loss"] = df["total"] - df["toss_wins"]
    fig, ax = _setup_dark_fig(7, 5)
    x = np.arange(len(df))
    w = 0.35
    ax.bar(x - w/2, df["toss_wins"], w, label="Won match", color=ORANGE, zorder=3)
    ax.bar(x + w/2, df["toss_loss"], w, label="Lost match", color="#3a3a5c", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(df["toss_decision"])
    ax.set_title("Toss Decision Impact", fontsize=13, fontweight="bold", pad=12)
    ax.legend(facecolor=CARD_BG, labelcolor=TEXT_COLOR)
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_venue_wins():
    df = query_df("""
        SELECT venue, COUNT(*) as matches FROM matches
        WHERE match_result='completed'
        GROUP BY venue ORDER BY matches DESC LIMIT 8
    """)
    df["short"] = df["venue"].str.split(",").str[0].str.replace(" Stadium", "").str.replace(" Cricket", "")
    fig, ax = _setup_dark_fig(11, 5)
    bars = ax.bar(df["short"], df["matches"], color=ORANGE, width=0.6, zorder=3)
    ax.bar_label(bars, fmt="%d", color=TEXT_COLOR, fontsize=9, padding=3)
    ax.set_xlabel("Venue", fontsize=10)
    ax.set_ylabel("Matches Played", fontsize=10)
    ax.set_title("Matches per Venue – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_nrr():
    df = query_df("SELECT team, nrr FROM points_table ORDER BY nrr DESC")
    abbr_map = {v: k for k, v in TEAM_FULL.items()}
    df["abbr"] = df["team"].apply(lambda x: abbr_map.get(x, x[:3].upper()))
    colors = [ORANGE if n >= 0 else "#5555aa" for n in df["nrr"]]
    fig, ax = _setup_dark_fig(10, 5)
    bars = ax.barh(df["abbr"], df["nrr"], color=colors, height=0.6, zorder=3)
    ax.axvline(0, color=TEXT_COLOR, linewidth=0.8)
    ax.bar_label(bars, fmt="%.3f", color=TEXT_COLOR, fontsize=8, padding=3)
    ax.set_xlabel("Net Run Rate", fontsize=10)
    ax.set_title("Net Run Rate – IPL 2026", fontsize=13, fontweight="bold", pad=12)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig_to_b64(fig)

def chart_batting_vs_bowling():
    """Scatter: avg vs economy for all-rounders"""
    bat_df = query_df("SELECT batsman as player, team, runs, average, strike_rate FROM batting")
    bowl_df = query_df("SELECT bowler as player, team, wickets, economy, avg as bowl_avg FROM bowling")
    common = pd.merge(bat_df, bowl_df, on=["player", "team"])
    if common.empty:
        return None
    fig, ax = _setup_dark_fig(10, 6)
    colors = [TEAM_COLORS.get(t, ORANGE) for t in common["team"]]
    scatter = ax.scatter(common["runs"], common["wickets"], c=colors,
                         s=80, alpha=0.85, zorder=3, edgecolors="none")
    for _, row in common.iterrows():
        ax.annotate(row["player"].split()[-1], (row["runs"], row["wickets"]),
                    fontsize=7, color=TEXT_COLOR, alpha=0.7,
                    xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel("Runs Scored", fontsize=10)
    ax.set_ylabel("Wickets Taken", fontsize=10)
    ax.set_title("All-Rounders: Runs vs Wickets", fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    return fig_to_b64(fig)

def get_all_charts():
    return dict(
        top_batters=chart_top_batters(),
        top_bowlers=chart_top_bowlers(),
        team_wins=chart_team_wins(),
        strike_rates=chart_strike_rates(),
        economy_rates=chart_economy_rates(),
        toss_impact=chart_toss_impact(),
        venue_wins=chart_venue_wins(),
        nrr=chart_nrr(),
        allrounders=chart_batting_vs_bowling(),
    )
