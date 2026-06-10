from flask import Flask, render_template, request, jsonify, Response
import io, csv
from utils import (
    get_home_stats, get_top_batters, get_top_bowlers, get_top_fielders,
    get_points_table, get_team_stats, get_head_to_head, get_all_matches,
    get_match_filters, get_all_charts, chart_top_batters, chart_top_bowlers,
    chart_team_wins, chart_strike_rates, chart_economy_rates,
    chart_toss_impact, chart_venue_wins, chart_nrr, chart_batting_vs_bowling,
    search_player, TEAM_FULL, TEAM_COLORS, query_all
)

app = Flask(__name__)


@app.context_processor
def inject_globals():
    return dict(team_full=TEAM_FULL, team_colors=TEAM_COLORS)


# ─── PAGES ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    stats = get_home_stats()
    top_bat = get_top_batters(5)
    top_bowl = get_top_bowlers(5)
    pts = get_points_table()
    return render_template(
        "index.html",
        **stats,
        top_bat=top_bat,
        top_bowl=top_bowl,
        pts=pts,
        active="home",
    )


@app.route("/players")
def players():
    return render_template(
        "players.html",
        batters=get_top_batters(20),
        bowlers=get_top_bowlers(20),
        fielders=get_top_fielders(15),
        chart_bat=chart_top_batters(),
        chart_bowl=chart_top_bowlers(),
        chart_sr=chart_strike_rates(),
        chart_eco=chart_economy_rates(),
        active="players",
    )


@app.route("/teams")
def teams():
    pts = get_points_table()
    return render_template(
        "teams.html",
        pts=pts,
        chart_wins=chart_team_wins(),
        chart_nrr=chart_nrr(),
        team_list=list(TEAM_FULL.keys()),
        active="teams",
    )


@app.route("/teams/<abbr>")
def team_detail(abbr):
    abbr = abbr.upper()
    stats = get_team_stats(abbr)
    return render_template(
        "team_detail.html",
        abbr=abbr,
        name=TEAM_FULL.get(abbr, abbr),
        color=TEAM_COLORS.get(abbr, "#ff6b2b"),
        stats=stats,
        active="teams",
    )


@app.route("/matches")
def matches():
    all_matches = get_all_matches()
    venues_raw, teams_raw = get_match_filters()
    return render_template(
        "matches.html",
        matches=all_matches,
        venues=[v["venue"] for v in venues_raw],
        teams=[t["team1"] for t in teams_raw],
        chart_toss=chart_toss_impact(),
        chart_venue=chart_venue_wins(),
        active="matches",
    )


@app.route("/stats")
def stats():
    return render_template("stats.html", charts=get_all_charts(), active="stats")


# ─── API (search/filter, h2h, CSV export) ─────────────────────────────────────

@app.route("/api/players/search")
def api_search_players():
    q = request.args.get("q", "")
    bat, bowl = search_player(q)
    return jsonify({"batters": bat, "bowlers": bowl})


@app.route("/api/matches/filter")
def api_filter_matches():
    venue = request.args.get("venue", "")
    team = request.args.get("team", "")
    sql = "SELECT * FROM matches WHERE match_result='completed'"
    params = []
    if venue:
        sql += " AND venue LIKE ?"
        params.append(f"%{venue}%")
    if team:
        sql += " AND (team1=? OR team2=? OR match_winner=?)"
        params.extend([team, team, team])
    sql += " ORDER BY match_id"
    return jsonify(query_all(sql, params))


@app.route("/api/h2h")
def api_h2h():
    return jsonify(get_head_to_head(request.args.get("t1", ""), request.args.get("t2", "")))


@app.route("/api/compare/teams")
def api_compare_teams():
    t1 = request.args.get("t1", "")
    t2 = request.args.get("t2", "")
    rows = query_all(
        "SELECT * FROM points_table WHERE team LIKE ? OR team LIKE ?",
        (f"%{TEAM_FULL.get(t1, t1)}%", f"%{TEAM_FULL.get(t2, t2)}%"),
    )
    return jsonify(rows)


@app.route("/export/<table>.csv")
def export_csv(table):
    allowed = {"batting", "bowling", "fielding", "matches", "points_table"}
    if table not in allowed:
        return ("Not allowed", 400)
    rows = query_all(f"SELECT * FROM {table}")
    if not rows:
        return ("Empty", 404)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ipl_{table}.csv"},
    )


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
