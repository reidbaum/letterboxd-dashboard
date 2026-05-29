import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats

# ── Output helpers ────────────────────────────────────────────────────────────

_sections = []
_section_title = ""

def _section(title):
    global _section_title
    _section_title = title

LBX_GREEN  = "#00E054"
LBX_ORANGE = "#FF8000"
LBX_CARD   = "#2c3440"
LBX_BODY   = "#14181c"
LBX_TEXT   = "#99aabb"

GREEN_SCALE  = [[0, "#0a1f12"], [0.5, "#007a2e"], [1.0, "#00E054"]]
ORANGE_SCALE = [[0, "#3d1f00"], [0.5, "#804000"], [1.0, "#FF8000"]]

def _show(fig, wide=False):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=LBX_CARD,
        plot_bgcolor=LBX_CARD,
        font_color=LBX_TEXT,
        margin=dict(l=48, r=24, t=40, b=48),
        title_text="",
    )
    _sections.append({
        "title": _section_title,
        "html":  fig.to_html(full_html=False, include_plotlyjs=False),
        "wide":  wide,
    })

# ── Load & clean data ─────────────────────────────────────────────────────────

ratings   = pd.read_csv("data/ratings.csv")
diary     = pd.read_csv("data/diary.csv")
watched   = pd.read_csv("data/watched.csv")
watchlist = pd.read_csv("data/watchlist.csv")

for df in [ratings, diary, watched, watchlist]:
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    if 'year' in df.columns:
        df['year'] = df['year'].astype('Int64')
    if 'watched_date' in df.columns:
        df['watched_date'] = pd.to_datetime(df['watched_date'], errors='coerce')

diary_dated = diary.dropna(subset=['watched_date'])
diary_year  = diary_dated.groupby(diary_dated['watched_date'].dt.year)['name'].count()

ratings['decade'] = (ratings['year'] // 10 * 10).astype(str) + 's'
diary['rating']   = pd.to_numeric(diary['rating'], errors='coerce')

# ── Header stats ──────────────────────────────────────────────────────────────

films_watched = len(watched)

watch_dates = diary.watched_date.dt.date.drop_duplicates().sort_values().reset_index(drop=True)
longest_streak = 1
current_streak = 1
for i in range(1, len(watch_dates)):
    if (watch_dates[i] - watch_dates[i - 1]).days == 1:
        current_streak += 1
        longest_streak = max(longest_streak, current_streak)
    else:
        current_streak = 1

watch_weeks = diary['watched_date'].dt.to_period('W').drop_duplicates().sort_values().reset_index(drop=True)
longest_week_streak = 1
current_week_streak = 1
for i in range(1, len(watch_weeks)):
    gap      = watch_weeks[i].week - watch_weeks[i - 1].week
    year_gap = watch_weeks[i].year - watch_weeks[i - 1].year
    if (gap == 1) or (year_gap == 1 and gap < 0):
        current_week_streak += 1
        longest_week_streak = max(longest_week_streak, current_week_streak)
    else:
        current_week_streak = 1

films_per_day_counts = diary.groupby(diary['watched_date'].dt.date)['name'].count()
multi_film_days = int((films_per_day_counts >= 2).sum())
avg_rating = round(ratings['rating'].mean(), 2)

# ── Rating distribution ───────────────────────────────────────────────────────

_section('Rating Distribution')

rc = ratings['rating'].value_counts().sort_index().reset_index()
rc.columns = ['rating', 'count']
fig = px.bar(rc, x='rating', y='count',
             labels={'rating': 'Rating (★)', 'count': 'Films'},
             color='count', color_continuous_scale=GREEN_SCALE)
fig.update_layout(coloraxis_showscale=False)
_show(fig)

# ── Films watched per month ───────────────────────────────────────────────────

_section('Films Watched per Month')

monthly = (
    diary_dated
    .groupby(diary_dated['watched_date'].dt.to_period('M'))
    .size().reset_index(name='films')
)
monthly['month'] = monthly['watched_date'].astype(str)
fig = px.area(monthly, x='month', y='films',
              labels={'month': 'Month', 'films': 'Films watched'},
              color_discrete_sequence=[LBX_GREEN])
fig.update_xaxes(tickangle=45)
_show(fig, wide=True)

# ── Films watched by release year ─────────────────────────────────────────────

_section('Films by Release Year')

year_counts = watched['year'].value_counts().sort_index().reset_index()
year_counts.columns = ['year', 'count']
fig = px.bar(year_counts, x='year', y='count',
             labels={'year': 'Release year', 'count': 'Films'},
             color='count', color_continuous_scale=GREEN_SCALE)
fig.update_layout(coloraxis_showscale=False)
fig.update_xaxes(tickangle=45)
_show(fig, wide=True)

# ── Avg rating by release year ────────────────────────────────────────────────

_section('Avg Rating by Release Year')

ratings_year = (
    ratings.groupby('year')['rating']
    .agg(['mean', 'count']).reset_index()
    .rename(columns={'mean': 'avg_rating', 'count': 'films'})
    .sort_values('year')
)
ratings_year.loc[ratings_year['films'] < 3, 'avg_rating'] = None
fig = px.bar(ratings_year, x='year', y='avg_rating',
             labels={'year': 'Release year', 'avg_rating': 'Avg rating'},
             color='avg_rating', color_continuous_scale=ORANGE_SCALE)
fig.update_layout(coloraxis_showscale=False, yaxis_range=[0, 5.5])
fig.update_xaxes(tickangle=45)
_show(fig, wide=True)

# ── Films logged per year ─────────────────────────────────────────────────────

_section('Films Logged per Year')

fy = diary_dated.groupby(diary_dated['watched_date'].dt.year).size().reset_index()
fy.columns = ['year', 'films']
fig = px.bar(fy, x='year', y='films',
             labels={'year': 'Year', 'films': 'Films watched'},
             color='films', color_continuous_scale=GREEN_SCALE)
fig.update_layout(coloraxis_showscale=False)
_show(fig)

# ── Films watched by decade ───────────────────────────────────────────────────

_section('Films by Decade')

decade_counts = ratings['decade'].value_counts().sort_index().reset_index()
decade_counts.columns = ['decade', 'count']
fig = px.bar(decade_counts, x='decade', y='count',
             labels={'decade': 'Decade', 'count': 'Films'},
             color='count', color_continuous_scale=GREEN_SCALE)
fig.update_layout(coloraxis_showscale=False)
_show(fig)

# ── Avg rating by decade ──────────────────────────────────────────────────────

_section('Avg Rating by Decade')

decade_stats = (
    ratings.groupby('decade')['rating']
    .agg(['mean', 'count']).reset_index()
    .rename(columns={'mean': 'avg_rating', 'count': 'films'})
    .query('films >= 20')
    .sort_values('decade')
)
fig = px.bar(decade_stats, x='decade', y='avg_rating',
             labels={'decade': 'Decade', 'avg_rating': 'Avg rating'},
             color='avg_rating', color_continuous_scale=ORANGE_SCALE)
fig.update_layout(coloraxis_showscale=False, yaxis_range=[0, 5.5])
_show(fig)

# ── Most rewatched films ──────────────────────────────────────────────────────

_section('Most Rewatched Films')

rewatched = (
    diary.groupby(['name', 'year']).size().reset_index(name='watches')
    .query('watches > 1').sort_values('watches').tail(15)
)
rewatched['label'] = rewatched['name'] + ' (' + rewatched['year'].astype(str) + ')'
fig = px.bar(rewatched, x='watches', y='label', orientation='h',
             labels={'watches': 'Times watched', 'label': 'Film'},
             color='watches', color_continuous_scale=ORANGE_SCALE)
fig.update_layout(coloraxis_showscale=False,
                  yaxis={'categoryorder': 'total ascending'})
_show(fig)

# ── Activity heatmap (all time) ───────────────────────────────────────────────

_section('Watching Activity — All Time')

films_per_day = (
    diary_dated.groupby(diary_dated['watched_date'].dt.date)['name']
    .count().reset_index()
)
films_per_day.columns = ['date', 'count']
films_per_day['date'] = pd.to_datetime(films_per_day['date'])
date_range = pd.date_range(films_per_day['date'].min(), films_per_day['date'].max())
all_days = pd.DataFrame({'date': date_range})
all_days = all_days.merge(films_per_day, on='date', how='left').fillna(0)
all_days['count'] = all_days['count'].astype(int)
all_days['dow']   = all_days['date'].dt.dayofweek
all_days['week']  = (all_days['date'] - all_days['date'].min()).dt.days // 7

num_weeks = all_days['week'].max() + 1
grid = np.zeros((7, num_weeks))
for _, row in all_days.iterrows():
    grid[int(row['dow']), int(row['week'])] = row['count']

months = all_days.groupby(all_days['date'].dt.to_period('M'))['week'].min()
fig = go.Figure(go.Heatmap(
    z=grid,
    colorscale=[[0, '#0a1510'], [0.25, '#003d1a'], [0.5, '#007a2e'],
                [0.75, '#00b544'], [1.0, '#00E054']],
    xgap=2, ygap=2,
    showscale=True,
    colorbar=dict(title='Films', thickness=12),
    hovertemplate='Week %{x}<br>%{y}<br>Films: %{z}<extra></extra>',
))
fig.update_layout(
    xaxis=dict(tickvals=months.values.tolist(),
               ticktext=[str(m) for m in months.index], tickangle=45),
    yaxis=dict(tickvals=list(range(7)),
               ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
               autorange='reversed'),
    height=240,
)
_show(fig, wide=True)

# ── Activity heatmap (2025) ───────────────────────────────────────────────────

_section('Watching Activity — 2025')

diary_2025 = diary_dated[diary_dated['watched_date'].dt.year == 2025]
fpd_2025 = (
    diary_2025.groupby(diary_2025['watched_date'].dt.date)['name']
    .count().reset_index()
)
fpd_2025.columns = ['date', 'count']
fpd_2025['date'] = pd.to_datetime(fpd_2025['date'])
dr_2025 = pd.date_range('2025-01-01', '2025-12-31')
ad_2025 = pd.DataFrame({'date': dr_2025})
ad_2025 = ad_2025.merge(fpd_2025, on='date', how='left').fillna(0)
ad_2025['count'] = ad_2025['count'].astype(int)
ad_2025['dow']   = ad_2025['date'].dt.dayofweek
ad_2025['week']  = (ad_2025['date'] - ad_2025['date'].min()).dt.days // 7

nw_2025 = ad_2025['week'].max() + 1
grid_2025 = np.zeros((7, nw_2025))
for _, row in ad_2025.iterrows():
    grid_2025[int(row['dow']), int(row['week'])] = row['count']

months_2025 = ad_2025.groupby(ad_2025['date'].dt.to_period('M'))['week'].min()
fig = go.Figure(go.Heatmap(
    z=grid_2025,
    colorscale=[[0, '#0a1510'], [0.25, '#003d1a'], [0.5, '#007a2e'],
                [0.75, '#00b544'], [1.0, '#00E054']],
    xgap=2, ygap=2,
    showscale=True,
    colorbar=dict(title='Films', thickness=12),
))
fig.update_layout(
    xaxis=dict(tickvals=months_2025.values.tolist(),
               ticktext=[str(m) for m in months_2025.index], tickangle=45),
    yaxis=dict(tickvals=list(range(7)),
               ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
               autorange='reversed'),
    height=240,
)
_show(fig, wide=True)

# ── Avg rating by month ───────────────────────────────────────────────────────

_section('Avg Rating by Month')

month_ratings = (
    diary_dated.dropna(subset=['rating'])
    .groupby(diary_dated['watched_date'].dt.month)['rating']
    .agg(['mean', 'count']).reset_index()
    .rename(columns={'watched_date': 'month', 'mean': 'avg_rating', 'count': 'films'})
    .query('films >= 3')
)
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
month_ratings['month_name'] = month_ratings['month'].apply(lambda x: month_names[x - 1])
fig = px.bar(month_ratings, x='month_name', y='avg_rating',
             labels={'month_name': 'Month', 'avg_rating': 'Avg rating'},
             color='avg_rating', color_continuous_scale=ORANGE_SCALE)
fig.update_layout(coloraxis_showscale=False, yaxis_range=[0, 5.5])
_show(fig)

# ── Films watched by day of week ──────────────────────────────────────────────

_section('Films by Day of Week')

day_counts = (
    diary_dated
    .groupby(diary_dated['watched_date'].dt.day_name())['name'].count()
    .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    .reset_index()
)
day_counts.columns = ['day', 'count']
fig = px.bar(day_counts, x='day', y='count',
             labels={'day': 'Day', 'count': 'Films watched'},
             color='count', color_continuous_scale=GREEN_SCALE)
fig.update_layout(coloraxis_showscale=False)
_show(fig)

# ── Avg rating over time ──────────────────────────────────────────────────────

_section('Avg Rating Over Time')

rating_over_time = (
    diary_dated.dropna(subset=['rating'])
    .groupby(diary_dated['watched_date'].dt.year)['rating']
    .agg(['mean', 'count']).reset_index()
    .rename(columns={'watched_date': 'year', 'mean': 'avg_rating', 'count': 'films'})
    .query('films >= 10')
)
fig = px.line(rating_over_time, x='year', y='avg_rating',
              labels={'year': 'Year', 'avg_rating': 'Avg rating'},
              markers=True, color_discrete_sequence=[LBX_GREEN])
fig.update_layout(yaxis_range=[0, 5.5])
_show(fig)

# ── Half star vs full star ────────────────────────────────────────────────────

_section('Rating Style: Half Star vs Full Star')

ratings['is_half'] = ratings['rating'] % 1 != 0
half_full = ratings['is_half'].value_counts().rename({True: 'Half star', False: 'Full star'})
pct_hf = (half_full / half_full.sum() * 100).round(1).reset_index()
pct_hf.columns = ['type', 'pct']

fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]])
fig.add_trace(go.Bar(x=pct_hf['type'], y=pct_hf['pct'],
                     marker_color=[LBX_ORANGE, LBX_GREEN], showlegend=False), row=1, col=1)
fig.add_trace(go.Pie(labels=pct_hf['type'], values=pct_hf['pct'],
                     marker=dict(colors=[LBX_ORANGE, LBX_GREEN]), hole=0.35), row=1, col=2)
fig.update_layout(yaxis_range=[0, 100], yaxis_title='% of ratings')
_show(fig, wide=True)

# ── Ratings vs normal distribution ───────────────────────────────────────────

_section('Ratings vs Normal Distribution')

rating_values = ratings['rating'].dropna()
rc2    = rating_values.value_counts(normalize=True).sort_index()
x_norm = np.linspace(0.5, 5.0, 300)
mean_r, std_r = rating_values.mean(), rating_values.std()
normal_curve  = stats.norm.pdf(x_norm, mean_r, std_r) * 0.5

fig = go.Figure()
fig.add_trace(go.Bar(x=rc2.index, y=rc2.values, name='Your ratings',
                     marker_color=LBX_GREEN, opacity=0.8, width=0.4))
fig.add_trace(go.Scatter(x=x_norm, y=normal_curve, mode='lines',
                         name=f'Normal (μ={mean_r:.2f}, σ={std_r:.2f})',
                         line=dict(color=LBX_ORANGE, width=2.5, dash='dash')))
fig.update_layout(xaxis_title='Rating (★)', yaxis_title='Proportion of films')
_show(fig)

# ── Old vs new films ──────────────────────────────────────────────────────────

_section('Old vs New Films')

current_year = 2026
ratings['era'] = ratings['year'].apply(
    lambda y: 'Last 5 years' if y >= current_year - 5 else '5+ years ago'
)
era_counts = ratings['era'].value_counts()
pct_era = (era_counts / era_counts.sum() * 100).round(1).reset_index()
pct_era.columns = ['era', 'pct']

fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]])
fig.add_trace(go.Bar(x=pct_era['era'], y=pct_era['pct'],
                     marker_color=[LBX_GREEN, LBX_ORANGE], showlegend=False), row=1, col=1)
fig.add_trace(go.Pie(labels=pct_era['era'], values=pct_era['pct'],
                     marker=dict(colors=[LBX_GREEN, LBX_ORANGE]), hole=0.35), row=1, col=2)
fig.update_layout(yaxis_range=[0, 100], yaxis_title='% of films watched')
_show(fig, wide=True)

# ── First watches vs rewatches ────────────────────────────────────────────────

_section('First Watches vs Rewatches per Year')

watch_counts  = diary.groupby(['name', 'year'])['watched_date'].count().reset_index()
watch_counts.columns = ['name', 'year', 'watch_count']
diary_merged  = diary_dated.merge(watch_counts, on=['name', 'year'], how='left')
diary_merged['is_rewatch'] = diary_merged['watch_count'] > 1

rewatch_by_year = (
    diary_merged.groupby(diary_merged['watched_date'].dt.year)
    .apply(lambda g: pd.Series({
        'rewatches':     g['is_rewatch'].sum(),
        'first_watches': (~g['is_rewatch']).sum(),
        'total':         len(g),
    }))
    .reset_index().rename(columns={'watched_date': 'year'})
)
rewatch_by_year['rewatch_pct'] = (
    rewatch_by_year['rewatches'] / rewatch_by_year['total'] * 100
).round(1)

fig = go.Figure()
fig.add_trace(go.Bar(x=rewatch_by_year['year'].astype(str),
                     y=rewatch_by_year['first_watches'],
                     name='First watches', marker_color=LBX_GREEN))
fig.add_trace(go.Bar(x=rewatch_by_year['year'].astype(str),
                     y=rewatch_by_year['rewatches'],
                     name='Rewatches', marker_color=LBX_ORANGE))
fig.update_layout(barmode='stack', xaxis_title='Year', yaxis_title='Films')
_show(fig, wide=True)

# ── Watchlist analysis ────────────────────────────────────────────────────────

_section('Watchlist Analysis')

watchlist['date'] = pd.to_datetime(watchlist['date'], errors='coerce')
watched['date']   = pd.to_datetime(watched['date'],   errors='coerce')

added   = watchlist.groupby(watchlist['date'].dt.to_period('M')).size().reset_index(name='added')
added['date'] = added['date'].astype(str)
cleared = watched.groupby(watched['date'].dt.to_period('M')).size().reset_index(name='watched_count')
cleared['date'] = cleared['date'].astype(str)

growth = added.merge(cleared, on='date', how='outer').fillna(0).sort_values('date')
growth['net']        = growth['added'] - growth['watched_count']
growth['cumulative'] = growth['net'].cumsum()

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    subplot_titles=['Added vs Watched per Month',
                                    'Cumulative Watchlist Growth'],
                    vertical_spacing=0.12)
fig.add_trace(go.Bar(x=growth['date'], y=growth['added'],
                     name='Added', marker_color=LBX_GREEN), row=1, col=1)
fig.add_trace(go.Bar(x=growth['date'], y=growth['watched_count'],
                     name='Watched', marker_color=LBX_ORANGE), row=1, col=1)
fig.add_trace(go.Scatter(x=growth['date'], y=growth['cumulative'],
                         mode='lines+markers', fill='tozeroy',
                         name='Net growth',
                         line=dict(color=LBX_GREEN, width=2)), row=2, col=1)
fig.update_layout(height=560, xaxis2_tickangle=45)
_show(fig, wide=True)

# ── Generate HTML ─────────────────────────────────────────────────────────────

card_html = ''
for s in _sections:
    width_class = 'wide' if s['wide'] else 'half'
    card_html += f"""
    <div class="card {width_class}">
      <h2>{s["title"]}</h2>
      {s["html"]}
    </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Letterboxd Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #14181c;
      color: #99aabb;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 2rem;
    }}
    h1 {{
      text-align: center;
      font-size: 2rem;
      color: #00E054;
      margin-bottom: 0.25rem;
    }}
    .subtitle {{
      text-align: center;
      color: #678;
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }}
    .stats {{
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      max-width: 1400px;
      margin: 0 auto 2.5rem;
    }}
    .stat {{
      background: #2c3440;
      border-radius: 10px;
      padding: 1.1rem 1.6rem;
      min-width: 130px;
      text-align: center;
    }}
    .stat-val {{
      font-size: 1.8rem;
      font-weight: bold;
      color: #00E054;
      line-height: 1.1;
    }}
    .stat-lbl {{
      font-size: 0.8rem;
      color: #678;
      margin-top: 0.3rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
      max-width: 1400px;
      margin: 0 auto;
    }}
    .card {{
      background: #2c3440;
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      overflow: hidden;
    }}
    .card.wide {{ grid-column: 1 / -1; }}
    .card h2 {{
      font-size: 0.8rem;
      color: #678;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 0.75rem;
    }}
    @media (max-width: 800px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .card.wide {{ grid-column: 1; }}
    }}
  </style>
</head>
<body>
  <h1>Letterboxd Dashboard</h1>
  <p class="subtitle">Reid B.</p>

  <div class="stats">
    <div class="stat">
      <div class="stat-val">{films_watched:,}</div>
      <div class="stat-lbl">Films watched</div>
    </div>
    <div class="stat">
      <div class="stat-val">{avg_rating} ★</div>
      <div class="stat-lbl">Avg rating</div>
    </div>
    <div class="stat">
      <div class="stat-val">{longest_streak}</div>
      <div class="stat-lbl">Longest streak (days)</div>
    </div>
    <div class="stat">
      <div class="stat-val">{longest_week_streak}</div>
      <div class="stat-lbl">Longest streak (weeks)</div>
    </div>
    <div class="stat">
      <div class="stat-val">{multi_film_days}</div>
      <div class="stat-lbl">Multi-film days</div>
    </div>
  </div>

  <div class="grid">
    {card_html}
  </div>
</body>
</html>"""

output_path = 'dashboard.html'
with open(output_path, 'w') as f:
    f.write(html)

print(f'Generated {output_path} with {len(_sections)} charts.')
