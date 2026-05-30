import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from scipy import stats

LBX_GREEN  = "#00E054"
LBX_ORANGE = "#FF8000"
LBX_CARD   = "#2c3440"
LBX_BODY   = "#14181c"
LBX_TEXT   = "#99aabb"

GREEN_SCALE  = [[0, "#0a1f12"], [0.5, "#007a2e"], [1.0, "#00E054"]]
ORANGE_SCALE = [[0, "#3d1f00"], [0.5, "#804000"], [1.0, "#FF8000"]]

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

diary['rating']  = pd.to_numeric(diary['rating'], errors='coerce')
diary_dated      = diary.dropna(subset=['watched_date'])
ratings['decade'] = (ratings['year'] // 10 * 10).astype(str) + 's'

all_years = sorted(
    diary_dated['watched_date'].dt.year.dropna().unique().astype(int).tolist()
)

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']

# ── Chart builder ─────────────────────────────────────────────────────────────

def _style(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=LBX_CARD,
        plot_bgcolor=LBX_CARD,
        font_color=LBX_TEXT,
        margin=dict(l=48, r=24, t=40, b=48),
        title_text="",
    )


def build_content(filter_year=None):
    sections = []

    d = (diary_dated if filter_year is None
         else diary_dated[diary_dated['watched_date'].dt.year == filter_year].copy())
    d_ratings = d.dropna(subset=['rating'])

    if filter_year is None:
        r = ratings.copy()
        r['decade'] = (r['year'] // 10 * 10).astype(str) + 's'
    else:
        diary_films = d[['name', 'year']].drop_duplicates()
        r = ratings.merge(diary_films, on=['name', 'year'], how='inner').copy()
        r['decade'] = (r['year'] // 10 * 10).astype(str) + 's'

    def add(title, fig, wide=False):
        _style(fig)
        sections.append({
            'title': title,
            'html':  fig.to_html(full_html=False, include_plotlyjs=False),
            'wide':  wide,
        })

    # ── Header stats ──────────────────────────────────────────────────────────

    films_stat = len(d)
    avg_stat   = (f'{round(d_ratings["rating"].mean(), 2)} ★'
                  if len(d_ratings) > 0 else '—')

    wdates = d['watched_date'].dt.date.drop_duplicates().sort_values().reset_index(drop=True)
    ls = cs = (1 if len(wdates) > 0 else 0)
    for i in range(1, len(wdates)):
        if (wdates[i] - wdates[i - 1]).days == 1:
            cs += 1; ls = max(ls, cs)
        else:
            cs = 1

    wweeks = d['watched_date'].dt.to_period('W').drop_duplicates().sort_values().reset_index(drop=True)
    lws = cws = (1 if len(wweeks) > 0 else 0)
    for i in range(1, len(wweeks)):
        gap = wweeks[i].week - wweeks[i - 1].week
        ygap = wweeks[i].year - wweeks[i - 1].year
        if gap == 1 or (ygap == 1 and gap < 0):
            cws += 1; lws = max(lws, cws)
        else:
            cws = 1

    mfd = int((d.groupby(d['watched_date'].dt.date)['name'].count() >= 2).sum())

    stats_html = f"""
        <div class="stat"><div class="stat-val">{films_stat:,}</div><div class="stat-lbl">Films watched</div></div>
        <div class="stat"><div class="stat-val">{avg_stat}</div><div class="stat-lbl">Avg rating</div></div>
        <div class="stat"><div class="stat-val">{ls}</div><div class="stat-lbl">Longest streak (days)</div></div>
        <div class="stat"><div class="stat-val">{lws}</div><div class="stat-lbl">Longest streak (weeks)</div></div>
        <div class="stat"><div class="stat-val">{mfd}</div><div class="stat-lbl">Multi-film days</div></div>
    """

    # ── Rating Distribution ───────────────────────────────────────────────────

    if not d_ratings.empty:
        rc = d_ratings['rating'].value_counts().sort_index().reset_index()
        rc.columns = ['rating', 'count']
        rc['rating'] = rc['rating'].astype(str)
        fig = px.bar(rc, x='rating', y='count',
                     labels={'rating': 'Rating (★)', 'count': 'Films'},
                     color_discrete_sequence=[LBX_GREEN])
        add('Rating Distribution', fig, wide=True)

    # ── Films by Release Year ─────────────────────────────────────────────────

    if not r.empty:
        yc = r['year'].value_counts().sort_index().reset_index()
        yc.columns = ['year', 'count']
        fig = px.bar(yc, x='year', y='count',
                     labels={'year': 'Release year', 'count': 'Films'},
                     color='count', color_continuous_scale=GREEN_SCALE)
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(tickangle=45)
        add('Films by Release Year', fig, wide=True)

    # ── Avg Rating by Release Year ────────────────────────────────────────────

    if not r.empty:
        ry = (r.groupby('year')['rating']
              .agg(['mean', 'count']).reset_index()
              .rename(columns={'mean': 'avg_rating', 'count': 'films'})
              .sort_values('year'))
        min_yr = 2 if filter_year is not None else 3
        ry.loc[ry['films'] < min_yr, 'avg_rating'] = None
        if not ry.dropna(subset=['avg_rating']).empty:
            fig = px.bar(ry, x='year', y='avg_rating',
                         labels={'year': 'Release year', 'avg_rating': 'Avg rating'},
                         color='avg_rating', color_continuous_scale=ORANGE_SCALE)
            fig.update_layout(coloraxis_showscale=False, yaxis_range=[0, 5.5])
            fig.update_xaxes(tickangle=45)
            add('Avg Rating by Release Year', fig, wide=True)

    # ── Films Logged (per year or per month when filtered) ────────────────────

    if filter_year is None:
        fy_data = d.groupby(d['watched_date'].dt.year).size().reset_index()
        fy_data.columns = ['year', 'films']
        if not fy_data.empty:
            fig = px.bar(fy_data, x='year', y='films',
                         labels={'year': 'Year', 'films': 'Films watched'},
                         color_discrete_sequence=[LBX_GREEN])
            add('Films Logged per Year', fig, wide=True)
    else:
        fm = d.groupby(d['watched_date'].dt.month).size().reset_index()
        fm.columns = ['month', 'films']
        base = pd.DataFrame({'month': range(1, 13), 'month_name': MONTH_NAMES})
        fm = base.merge(fm, on='month', how='left').fillna(0)
        fm['films'] = fm['films'].astype(int)
        fig = px.bar(fm, x='month_name', y='films',
                     labels={'month_name': 'Month', 'films': 'Films watched'},
                     color_discrete_sequence=[LBX_GREEN])
        add('Films Logged per Month', fig, wide=True)

    # ── Films by Decade ───────────────────────────────────────────────────────

    if not r.empty:
        dc = r['decade'].value_counts().sort_index().reset_index()
        dc.columns = ['decade', 'count']
        fig = px.bar(dc, x='decade', y='count',
                     labels={'decade': 'Decade', 'count': 'Films'},
                     color_discrete_sequence=[LBX_GREEN])
        add('Films by Decade', fig)

    # ── Avg Rating by Decade ──────────────────────────────────────────────────

    if not r.empty:
        min_dec = 3 if filter_year is not None else 20
        ds = (r.groupby('decade')['rating']
              .agg(['mean', 'count']).reset_index()
              .rename(columns={'mean': 'avg_rating', 'count': 'films'})
              .query(f'films >= {min_dec}')
              .sort_values('decade'))
        if not ds.empty:
            fig = px.bar(ds, x='decade', y='avg_rating',
                         labels={'decade': 'Decade', 'avg_rating': 'Avg rating'},
                         color_discrete_sequence=[LBX_ORANGE])
            fig.update_layout(yaxis_range=[0, 5.5])
            add('Avg Rating by Decade', fig)

    # ── Most Rewatched Films ──────────────────────────────────────────────────

    rw = (d.groupby(['name', 'year']).size().reset_index(name='watches')
          .query('watches > 1').sort_values('watches').tail(15))
    if not rw.empty:
        rw['label'] = rw['name'] + ' (' + rw['year'].astype(str) + ')'
        fig = px.bar(rw, x='watches', y='label', orientation='h',
                     labels={'watches': 'Times watched', 'label': 'Film'},
                     color_discrete_sequence=[LBX_ORANGE])
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        add('Most Rewatched Films', fig)

    # ── Watching Activity Heatmap ─────────────────────────────────────────────

    fpd = d.groupby(d['watched_date'].dt.date)['name'].count().reset_index()
    fpd.columns = ['date', 'count']
    fpd['date'] = pd.to_datetime(fpd['date'])
    if not fpd.empty:
        if filter_year is None:
            dr      = pd.date_range(fpd['date'].min(), fpd['date'].max())
            htitle  = 'Watching Activity — All Time'
        else:
            dr      = pd.date_range(f'{filter_year}-01-01', f'{filter_year}-12-31')
            htitle  = f'Watching Activity — {filter_year}'

        ad = pd.DataFrame({'date': dr})
        ad = ad.merge(fpd, on='date', how='left').fillna(0)
        ad['count'] = ad['count'].astype(int)
        ad['dow']   = ad['date'].dt.dayofweek
        ad['week']  = (ad['date'] - ad['date'].min()).dt.days // 7

        nw   = ad['week'].max() + 1
        grid = np.zeros((7, nw))
        for _, row in ad.iterrows():
            grid[int(row['dow']), int(row['week'])] = row['count']

        months = ad.groupby(ad['date'].dt.to_period('M'))['week'].min()
        fig = go.Figure(go.Heatmap(
            z=grid,
            colorscale=[[0, '#0a1510'], [0.25, '#003d1a'], [0.5, '#007a2e'],
                        [0.75, '#00b544'], [1.0, '#00E054']],
            xgap=2, ygap=2, showscale=True,
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
        add(htitle, fig, wide=True)

    # ── Avg Rating by Month ───────────────────────────────────────────────────

    mr = (d_ratings.groupby(d_ratings['watched_date'].dt.month)['rating']
          .agg(['mean', 'count']).reset_index()
          .rename(columns={'watched_date': 'month', 'mean': 'avg_rating', 'count': 'films'})
          .query('films >= 3'))
    if not mr.empty:
        mr['month_name'] = mr['month'].apply(lambda x: MONTH_NAMES[x - 1])
        fig = px.bar(mr, x='month_name', y='avg_rating',
                     labels={'month_name': 'Month', 'avg_rating': 'Avg rating'},
                     color_discrete_sequence=[LBX_ORANGE])
        fig.update_layout(yaxis_range=[0, 5.5])
        add('Avg Rating by Month', fig)

    # ── Films by Day of Week ──────────────────────────────────────────────────

    dow = (d.groupby(d['watched_date'].dt.day_name())['name'].count()
           .reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                     'Friday', 'Saturday', 'Sunday'])
           .reset_index())
    dow.columns = ['day', 'count']
    fig = px.bar(dow, x='day', y='count',
                 labels={'day': 'Day', 'count': 'Films watched'},
                 color='count', color_continuous_scale=GREEN_SCALE)
    fig.update_layout(coloraxis_showscale=False)
    add('Films by Day of Week', fig)

    # ── Avg Rating Over Time (year) / by Month (single year) ─────────────────

    if filter_year is None:
        rot = (d_ratings.groupby(d_ratings['watched_date'].dt.year)['rating']
               .agg(['mean', 'count']).reset_index()
               .rename(columns={'watched_date': 'year', 'mean': 'avg_rating', 'count': 'films'})
               .query('films >= 10'))
        if not rot.empty:
            fig = px.line(rot, x='year', y='avg_rating',
                          labels={'year': 'Year', 'avg_rating': 'Avg rating'},
                          markers=True, color_discrete_sequence=[LBX_GREEN])
            fig.update_layout(yaxis_range=[0, 5.5])
            add('Avg Rating Over Time', fig)

    # ── Half Star vs Full Star ────────────────────────────────────────────────

    if not d_ratings.empty:
        dr2 = d_ratings.copy()
        dr2['is_half'] = dr2['rating'] % 1 != 0
        hf  = dr2['is_half'].value_counts().rename({True: 'Half star', False: 'Full star'})
        pct = (hf / hf.sum() * 100).round(1).reset_index()
        pct.columns = ['type', 'pct']
        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]])
        fig.add_trace(go.Bar(x=pct['type'], y=pct['pct'],
                             marker_color=[LBX_ORANGE, LBX_GREEN], showlegend=False), row=1, col=1)
        fig.add_trace(go.Pie(labels=pct['type'], values=pct['pct'],
                             marker=dict(colors=[LBX_ORANGE, LBX_GREEN]), hole=0.35), row=1, col=2)
        fig.update_layout(yaxis_range=[0, 100], yaxis_title='% of ratings')
        add('Rating Style: Half Star vs Full Star', fig, wide=True)

    # ── Ratings vs Normal Distribution ───────────────────────────────────────

    if len(d_ratings) >= 10:
        rv    = d_ratings['rating'].dropna()
        rc2   = rv.value_counts(normalize=True).sort_index()
        xn    = np.linspace(0.5, 5.0, 300)
        mu, sigma = rv.mean(), rv.std()
        nc    = stats.norm.pdf(xn, mu, sigma) * 0.5
        fig   = go.Figure()
        fig.add_trace(go.Bar(x=rc2.index, y=rc2.values, name='Your ratings',
                             marker_color=LBX_GREEN, opacity=0.8, width=0.4))
        fig.add_trace(go.Scatter(x=xn, y=nc, mode='lines',
                                 name=f'Normal (μ={mu:.2f}, σ={sigma:.2f})',
                                 line=dict(color=LBX_ORANGE, width=2.5, dash='dash')))
        fig.update_layout(xaxis_title='Rating (★)', yaxis_title='Proportion of films')
        add('Ratings vs Normal Distribution', fig)

    # ── Old vs New Films ──────────────────────────────────────────────────────

    if not r.empty:
        r2       = r.copy()
        r2['era'] = r2['year'].apply(
            lambda y: 'Last 5 years' if y >= 2021 else '5+ years ago'
        )
        ec  = r2['era'].value_counts()
        pe  = (ec / ec.sum() * 100).round(1).reset_index()
        pe.columns = ['era', 'pct']
        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]])
        fig.add_trace(go.Bar(x=pe['era'], y=pe['pct'],
                             marker_color=[LBX_GREEN, LBX_ORANGE], showlegend=False), row=1, col=1)
        fig.add_trace(go.Pie(labels=pe['era'], values=pe['pct'],
                             marker=dict(colors=[LBX_GREEN, LBX_ORANGE]), hole=0.35), row=1, col=2)
        fig.update_layout(yaxis_range=[0, 100], yaxis_title='% of films watched')
        add('Old vs New Films', fig, wide=True)

    # ── First Watches vs Rewatches ────────────────────────────────────────────

    wc = diary.groupby(['name', 'year'])['watched_date'].count().reset_index()
    wc.columns = ['name', 'year', 'watch_count']
    dm = d.merge(wc, on=['name', 'year'], how='left')
    dm['is_rewatch'] = dm['watch_count'] > 1

    if filter_year is None:
        rb = (dm.groupby(dm['watched_date'].dt.year)
              .apply(lambda g: pd.Series({
                  'rewatches':     g['is_rewatch'].sum(),
                  'first_watches': (~g['is_rewatch']).sum(),
              })).reset_index().rename(columns={'watched_date': 'year'}))
        if not rb.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=rb['year'].astype(str), y=rb['first_watches'],
                                 name='First watches', marker_color=LBX_GREEN))
            fig.add_trace(go.Bar(x=rb['year'].astype(str), y=rb['rewatches'],
                                 name='Rewatches', marker_color=LBX_ORANGE))
            fig.update_layout(barmode='stack', xaxis_title='Year', yaxis_title='Films')
            add('First Watches vs Rewatches per Year', fig, wide=True)
    else:
        rb = (dm.groupby(dm['watched_date'].dt.month)
              .apply(lambda g: pd.Series({
                  'rewatches':     g['is_rewatch'].sum(),
                  'first_watches': (~g['is_rewatch']).sum(),
              })).reset_index().rename(columns={'watched_date': 'month'}))
        if not rb.empty:
            rb['month_name'] = rb['month'].apply(lambda x: MONTH_NAMES[x - 1])
            fig = go.Figure()
            fig.add_trace(go.Bar(x=rb['month_name'], y=rb['first_watches'],
                                 name='First watches', marker_color=LBX_GREEN))
            fig.add_trace(go.Bar(x=rb['month_name'], y=rb['rewatches'],
                                 name='Rewatches', marker_color=LBX_ORANGE))
            fig.update_layout(barmode='stack', xaxis_title='Month', yaxis_title='Films')
            add('First Watches vs Rewatches', fig, wide=True)

    # ── Watchlist Analysis ────────────────────────────────────────────────────

    wl = watchlist.copy()
    wa = watched.copy()
    wl['date'] = pd.to_datetime(wl['date'], errors='coerce')
    wa['date'] = pd.to_datetime(wa['date'], errors='coerce')

    if filter_year is not None:
        wl = wl[wl['date'].dt.year == filter_year]
        wa = wa[wa['date'].dt.year == filter_year]

    added_wl   = wl.groupby(wl['date'].dt.to_period('M')).size().reset_index(name='added')
    added_wl['date'] = added_wl['date'].astype(str)
    cleared_wl = wa.groupby(wa['date'].dt.to_period('M')).size().reset_index(name='watched_count')
    cleared_wl['date'] = cleared_wl['date'].astype(str)
    growth = (added_wl.merge(cleared_wl, on='date', how='outer')
              .fillna(0).sort_values('date'))

    if not growth.empty:
        if filter_year is None:
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
            add('Watchlist Analysis', fig, wide=True)
        else:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=growth['date'], y=growth['added'],
                                 name='Added', marker_color=LBX_GREEN))
            fig.add_trace(go.Bar(x=growth['date'], y=growth['watched_count'],
                                 name='Watched', marker_color=LBX_ORANGE))
            fig.update_layout(barmode='group', xaxis_title='Month',
                              yaxis_title='Films', xaxis_tickangle=45)
            add('Watchlist Activity', fig, wide=True)

    return stats_html, sections


# ── Build all year views ──────────────────────────────────────────────────────

filter_options = [None] + all_years
all_content    = {}

for fy in filter_options:
    key = 'all-time' if fy is None else str(fy)
    label = 'All Time' if fy is None else str(fy)
    print(f'Building {label}...')
    stats_html, sections = build_content(fy)
    all_content[key] = {'stats': stats_html, 'sections': sections}

# ── Assemble HTML ─────────────────────────────────────────────────────────────

options_html = '    <option value="all-time">All Time</option>\n'
for y in reversed(all_years):
    options_html += f'    <option value="{y}">{y}</option>\n'

year_blocks = ''
for key, content in all_content.items():
    display   = 'block' if key == 'all-time' else 'none'
    card_html = ''
    for s in content['sections']:
        wc = 'wide' if s['wide'] else 'half'
        card_html += f'\n    <div class="card {wc}"><h2>{s["title"]}</h2>{s["html"]}</div>'

    year_blocks += f"""
  <div class="year-content" data-year="{key}" style="display:{display}">
    <div class="stats">{content['stats']}</div>
    <div class="grid">{card_html}
    </div>
  </div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Letterboxd Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-3.5.0.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: {LBX_BODY};
      color: {LBX_TEXT};
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 2rem;
    }}
    h1 {{
      text-align: center;
      font-size: 2rem;
      color: {LBX_GREEN};
      margin-bottom: 0.25rem;
    }}
    .subtitle {{
      text-align: center;
      color: #678;
      margin-bottom: 1.25rem;
      font-size: 0.95rem;
    }}
    .filter-bar {{
      text-align: center;
      margin-bottom: 2rem;
    }}
    .filter-bar label {{
      color: {LBX_TEXT};
      font-size: 0.95rem;
      margin-right: 0.5rem;
    }}
    .filter-bar select {{
      background: #2c3440;
      color: {LBX_GREEN};
      border: 1px solid #445566;
      border-radius: 6px;
      padding: 0.4rem 0.9rem;
      font-size: 1rem;
      cursor: pointer;
      outline: none;
      appearance: none;
      -webkit-appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath fill='%2300E054' d='M6 8L0 0h12z'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 0.7rem center;
      padding-right: 2rem;
    }}
    .filter-bar select:focus {{ border-color: {LBX_GREEN}; }}
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
      color: {LBX_GREEN};
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

  <div class="filter-bar">
    <label for="year-select">Filter by year:</label>
    <select id="year-select" onchange="filterYear(this.value)">
      {options_html}
    </select>
  </div>

  {year_blocks}

  <script>
    function filterYear(val) {{
      document.querySelectorAll('.year-content').forEach(function(el) {{
        el.style.display = el.dataset.year === val ? 'block' : 'none';
      }});
    }}
  </script>
</body>
</html>"""

output_path = 'dashboard_v2.html'
with open(output_path, 'w') as f:
    f.write(html)

total_charts = sum(len(v['sections']) for v in all_content.values())
print(f'Generated {output_path} — {len(all_content)} views, {total_charts} charts total.')
