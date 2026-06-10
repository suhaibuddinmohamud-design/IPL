import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = "ipl.db"

def create_database():
    conn = sqlite3.connect(DB_PATH)

    # --- Batting ---
    bat = pd.read_csv("data/batting_stats.csv")
    bat.columns = bat.columns.str.strip().str.lower().str.replace(" ", "_")
    bat.to_sql("batting", conn, if_exists="replace", index=False)

    # --- Bowling ---
    bowl = pd.read_csv("data/bowling_stats.csv")
    bowl.columns = bowl.columns.str.strip().str.lower().str.replace(" ", "_")
    bowl.to_sql("bowling", conn, if_exists="replace", index=False)

    # --- Fielding ---
    field = pd.read_csv("data/fielding_stats.csv")
    field.columns = field.columns.str.strip().str.lower().str.replace(" ", "_")
    field.to_sql("fielding", conn, if_exists="replace", index=False)

    # --- Matches ---
    matches = pd.read_csv("data/matches.csv")
    matches.columns = matches.columns.str.strip().str.lower().str.replace(" ", "_")
    matches["first_ings_score"] = pd.to_numeric(matches["first_ings_score"], errors="coerce")
    matches["second_ings_score"] = pd.to_numeric(matches["second_ings_score"], errors="coerce")
    matches["wb_runs"] = pd.to_numeric(matches.get("wb_runs", pd.Series(dtype=float)), errors="coerce")
    matches["wb_wickets"] = pd.to_numeric(matches.get("wb_wickets", pd.Series(dtype=float)), errors="coerce")
    matches.to_sql("matches", conn, if_exists="replace", index=False)

    # --- Points Table ---
    pts = pd.read_csv("data/points_table.csv")
    pts.columns = pts.columns.str.strip().str.lower().str.replace(" ", "_")
    pts.to_sql("points_table", conn, if_exists="replace", index=False)

    # --- Venues ---
    venues = pd.read_csv("data/venues.csv")
    venues.columns = venues.columns.str.strip().str.lower().str.replace(" ", "_")
    venues.to_sql("venues", conn, if_exists="replace", index=False)

    # --- Squads ---
    squads = pd.read_csv("data/squads.csv")
    squads.columns = squads.columns.str.strip().str.lower().str.replace(" ", "_")
    squads.to_sql("squads", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print("✅ Database created successfully!")

if __name__ == "__main__":
    create_database()
