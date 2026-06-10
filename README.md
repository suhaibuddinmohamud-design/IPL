# 🏏 IPL Analytics Dashboard 2026

Premium full-stack IPL analytics web app — Flask · SQLite · Pandas · NumPy · Matplotlib · Chart.js.

## Quick start

```bash
pip install -r requirements.txt
# (optional, only if you want to rebuild from CSVs in data/)
python database.py
python app.py
```

Open **http://localhost:5000**

> `ipl.db` is included, so step 2 is optional.

## Pages

| Route | Page |
|---|---|
| `/` | Hero, animated counters, season leaders (Orange/Purple Cap, Most Wins), top-5 batters & bowlers, points table |
| `/players` | Tabbed batting/bowling/fielding tables, live search, 4 Matplotlib charts |
| `/teams` | Team cards with KPIs, wins & NRR charts, head-to-head comparator |
| `/teams/<abbr>` | Per-team batting, bowling, match wins (e.g. `/teams/RCB`) |
| `/matches` | All 39 matches with live filters (search/venue/team), toss & venue charts |
| `/stats` | 5-tab analytics dashboard (Batting / Bowling / Teams / Venues / All-rounders) |

## API

- `GET /api/players/search?q=` — live player search
- `GET /api/matches/filter?venue=&team=` — filter matches
- `GET /api/h2h?t1=RCB&t2=MI` — head-to-head
- `GET /api/compare/teams?t1=&t2=` — compare two teams' standings
- `GET /export/<table>.csv` — download batting / bowling / fielding / matches / points_table as CSV

## Architecture

```
ipl_dashboard/
├── app.py              # Flask routes (pages + JSON APIs + CSV export)
├── utils.py            # SQL helpers, Pandas/NumPy analytics, Matplotlib charts
├── database.py         # CSV → SQLite ingestion (rebuild only)
├── ipl.db              # SQLite database (included)
├── requirements.txt
├── templates/          # Jinja2 templates with base.html inheritance
│   ├── base.html  index.html  players.html  teams.html
│   ├── team_detail.html  matches.html  stats.html  404.html
└── static/
    ├── css/style.css   # Premium dark theme + responsive layout
    └── js/main.js      # Counters, tabs, search, filters, h2h
```

## Stack

- **Backend** — Flask 3, SQLite 3, Pandas, NumPy, Matplotlib (dark-themed PNG charts, served as base64)
- **Frontend** — Jinja2, vanilla JS, Chart.js (CDN), Font Awesome, Barlow Condensed + DM Sans
- **Theme** — dark glassmorphism with IPL orange (`#ff6b2b`) accents, fully responsive

## Features

- Animated stat counters, smooth-scroll Explore CTA
- Live player search (debounced fetch)
- Match filters (search + venue + team) — purely client-side over server-rendered table
- Head-to-Head team comparator (AJAX)
- CSV export for every dataset
- Modular routes & utilities, parameterised SQL, reusable chart helpers
- Mobile responsive nav, tables, grids
- 404 handler with branded page

Built for portfolios, hackathons, internships and placement projects.
