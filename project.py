import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Load data ──────────────────────────────────────────────────────────────────

ratings = pd.read_csv("data/ratings.csv")
diary   = pd.read_csv("data/diary.csv")

for df in [ratings, diary]:
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

ratings["year"]       = ratings["year"].astype("Int64")
ratings["decade"]     = (ratings["year"] // 10 * 10).astype(str) + "s"
diary["watched_date"] = pd.to_datetime(diary["watched_date"], errors="coerce")
diary["rating"]       = pd.to_numeric(diary["rating"], errors="coerce")
diary_dated           = diary.dropna(subset=["watched_date"])

# ── Header stats ───────────────────────────────────────────────────────────────

films_watched   = diary["name"].nunique()
avg_rating      = round(ratings["rating"].mean(), 2)
top_year        = int(ratings["year"].value_counts().idxmax())

films_per_day   = diary_dated.groupby(diary_dated["watched_date"].dt.date)["name"].count()
multi_film_days = int((films_per_day >= 2).sum())

watch_dates     = diary_dated["watched_date"].dt.date.drop_duplicates().sort_values().reset_index(drop=True)
longest, current = 1, 1
for i in range(1, len(watch_dates)):
    if (watch_dates[i] - watch_dates[i - 1]).days == 1:
        current += 1
        longest = max(longest, current)
    else:
        current = 1

# ── Charts ─────────────────────────────────────────────────────────────────────

# 1. Rating distribution
rc = ratings["rating"].value_counts().sort_index().reset_index()
rc.columns = ["rating", "count"]
fig_ratings = px.bar(rc, x="rating", y="count",
                     color="count", color_continuous_scale="Oranges",
                     title="Rating distribution",
                     labels={"rating": "Rating (★)", "count": "Films"})
fig_ratings.update_layout(coloraxis_showscale=False)

# 2. Films by decade
dc = ratings["decade"].value_counts().sort_index().reset_index()
dc.columns = ["decade", "count"]
fig_decade = px.bar(dc, x="decade", y="count",
                    color="count", color_continuous_scale="Blues",
                    title="Films by decade",
                    labels={"decade": "Decade", "count": "Films"})
fig_decade.update_layout(coloraxis_showscale=False)

# 3. Films watched per year
fy = diary_dated.groupby(diary_dated["watched_date"].dt.year).size().reset_index()
fy.columns = ["year", "films"]
fig_peryear = px.bar(fy, x="year", y="films",
                     color="films", color_continuous_scale="Greens",
                     title="Films watched per year",
                     labels={"year": "Year", "films": "Films watched"})
fig_peryear.update_layout(coloraxis_showscale=False)

# 4. Avg rating by decade
da = ratings.groupby("decade")["rating"].mean().round(2).reset_index()
da.columns = ["decade", "avg_rating"]
fig_avg = px.bar(da, x="decade", y="avg_rating",
                 color="avg_rating", color_continuous_scale="Purples",
                 title="Avg rating by decade",
                 labels={"decade": "Decade", "avg_rating": "Avg rating"})
fig_avg.update_layout(coloraxis_showscale=False)

# ── Build HTML ─────────────────────────────────────────────────────────────────

html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Letterboxd Stats</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body       {{ font-family: sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 24px; }}
    h1         {{ color: #e63946; margin-bottom: 4px; }}
    .subtitle  {{ color: #aaa; margin-bottom: 32px; }}
    .stats     {{ display: flex; gap: 16px; margin-bottom: 40px; flex-wrap: wrap; }}
    .stat      {{ background: #16213e; border-radius: 10px; padding: 20px 28px; min-width: 140px; }}
    .stat-val  {{ font-size: 2rem; font-weight: bold; color: #e63946; }}
    .stat-lbl  {{ font-size: 0.85rem; color: #aaa; margin-top: 4px; }}
    .charts    {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    .chart     {{ background: #16213e; border-radius: 10px; padding: 16px; }}
    @media (max-width: 700px) {{ .charts {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>

<h1>🎬 My Letterboxd Stats</h1>
<p class="subtitle">A deep dive into my film watching history.</p>

<div class="stats">
  <div class="stat"><div class="stat-val">{films_watched:,}</div><div class="stat-lbl">Films watched</div></div>
  <div class="stat"><div class="stat-val">{avg_rating} ★</div><div class="stat-lbl">Avg rating</div></div>
  <div class="stat"><div class="stat-val">{top_year}</div><div class="stat-lbl">Most watched era</div></div>
  <div class="stat"><div class="stat-val">{longest}</div><div class="stat-lbl">Longest streak (days)</div></div>
  <div class="stat"><div class="stat-val">{multi_film_days}</div><div class="stat-lbl">2+ film days</div></div>
</div>

<div class="charts">
  <div class="chart" id="chart-ratings"></div>
  <div class="chart" id="chart-decade"></div>
  <div class="chart" id="chart-peryear"></div>
  <div class="chart" id="chart-avg"></div>
</div>

<script>
  Plotly.newPlot('chart-ratings', {fig_ratings.to_json()});
  Plotly.newPlot('chart-decade',  {fig_decade.to_json()});
  Plotly.newPlot('chart-peryear', {fig_peryear.to_json()});
  Plotly.newPlot('chart-avg',     {fig_avg.to_json()});
</script>

</body>
</html>
"""

# ── Save ───────────────────────────────────────────────────────────────────────

output_path = "dashboard.html"
with open(output_path, "w") as f:
    f.write(html)

print(f"Dashboard saved to {output_path} — open it in your browser!")