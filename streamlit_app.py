from pathlib import Path
import json
import math
import urllib.error
import urllib.parse
import urllib.request

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from data_structure.team import Team
from main import load_application


ROOT = Path(__file__).resolve().parent
PLAYERS_FILE = ROOT / 'import' / 'Football_Player_Data-Analysis.csv'
MATCHES_FILE = ROOT / 'import' / 'Matches.csv'

st.set_page_config(
    page_title='GoalMind',
    page_icon='⚽',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.markdown(
    '''
    <style>
    :root { --forest:#153b2b; --leaf:#477b4d; --lime:#d9f77e; --paper:#f5f6f2; }
    .stApp { background:var(--paper); color:#18221b; }
    [data-testid="stHeader"] { background:rgba(245,246,242,.88); }
    [data-testid="stSidebar"] { background:#fff; border-right:1px solid #e7ebe4; }
    .block-container { max-width:1240px; padding-top:2rem; padding-bottom:4rem; }
    .brand { font-size:1.12rem; font-weight:700; letter-spacing:-.04em; color:var(--forest); }
    .brand span { color:var(--leaf); }
    .eyebrow { color:#6b855d; font-size:.72rem; text-transform:uppercase; letter-spacing:.16em; font-weight:650; }
    .hero-card { padding:2.2rem 2.4rem; border-radius:24px; color:#f7f8f2; background:radial-gradient(ellipse at 82% 10%,#436b48 0%,transparent 38%),linear-gradient(120deg,#153b2b,#214d37); min-height:245px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 18px 48px #18342318; }
    .hero-card h1 { color:#fff; font-size:clamp(2.1rem,5vw,3.6rem); line-height:1.02; letter-spacing:-.065em; margin:.45rem 0 .75rem; }
    .hero-card p { max-width:610px; color:#d5dfd2; font-size:1rem; line-height:1.7; margin:0; }
    .hero-kicker { color:var(--lime); font-size:.7rem; letter-spacing:.17em; text-transform:uppercase; }
    [data-testid="stMetric"] { background:white; border:1px solid #e6eae3; padding:1rem 1.1rem; border-radius:16px; box-shadow:0 8px 24px #17341b08; }
    [data-testid="stMetricLabel"] { color:#788076; }
    [data-testid="stMetricValue"] { color:var(--forest); letter-spacing:-.04em; }
    .photo-fallback { min-height:245px; border-radius:18px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#dce8d6,#b6cbb0); color:#31563a; font-size:5rem; font-weight:700; letter-spacing:-.08em; }
    .stTabs [data-baseweb="tab-list"] { gap:1.25rem; }
    .stTabs [data-baseweb="tab"] { height:3rem; }
    div[data-testid="stVerticalBlock"] > div:has(> .stAlert) { border-radius:12px; }
    </style>
    ''',
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner='Sto caricando giocatori e risultati…')
def get_application():
    return load_application(PLAYERS_FILE, MATCHES_FILE)


@st.cache_data(show_spinner=False, ttl=86400)
def get_portrait(player_name):
    title = urllib.parse.quote(player_name.strip().replace(' ', '_'), safe='')
    url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{title}'
    request = urllib.request.Request(url, headers={'User-Agent': 'GoalMind/1.0 (football statistics project)'})
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    text = f"{data.get('description', '')} {data.get('extract', '')}".lower()
    if data.get('type') != 'standard' or not data.get('thumbnail'):
        return None
    if not any(word in text for word in ('football', 'soccer', 'striker', 'midfielder', 'goalkeeper', 'winger')):
        return None
    return {
        'image': data['thumbnail']['source'],
        'page': data.get('content_urls', {}).get('desktop', {}).get('page'),
    }


def initials(name):
    parts = name.split()
    return ''.join(part[0] for part in parts[:2]).upper()


def player_options(app):
    return sorted(
        ((key, player) for key, player in app._players.items()),
        key=lambda item: (item[1].name.casefold(), item[1].team.casefold()),
    )


def player_label(option):
    player = option[1]
    return f'{player.name} · {player.team}'


def choose_player(app, key, label='Calciatore'):
    options = player_options(app)
    return st.selectbox(label, options, format_func=player_label, key=key)[1]


def show_photo(player):
    portrait = get_portrait(player.name)
    if portrait:
        st.image(portrait['image'], use_container_width=True)
        if portrait['page']:
            st.caption(f"Foto e dettagli: [pagina fonte]({portrait['page']})")
    else:
        st.markdown(f'<div class="photo-fallback">{initials(player.name)}</div>', unsafe_allow_html=True)
        st.caption('Ritratto non disponibile per questo profilo.')


def show_player_metrics(player):
    cols = st.columns(4)
    values = [
        ('Gol', player.goal, 0),
        ('Assist', player.assisttotal, 0),
        ('Rating', player.rating, 2),
        ('Minuti', player.mins_played, 0),
    ]
    for col, (label, value, digits) in zip(cols, values):
        display = '—' if not math.isfinite(value) else f'{value:,.{digits}f}'
        col.metric(label, display)


def show_player_chart(player, app):
    table = app.player_table()
    measures = [
        ('Gol', player.goal, table['Goals'].median()),
        ('Assist', player.assisttotal, math.nan),
        ('xG totali', player.xg_total, table['xG_Total'].median()),
    ]
    assists = [p.assisttotal for p in app._players.values() if math.isfinite(p.assisttotal)]
    measures[1] = ('Assist', player.assisttotal, float(pd.Series(assists).median()) if assists else math.nan)
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2))
    for ax, (label, value, median) in zip(axes, measures):
        values = [0 if not math.isfinite(value) else value, 0 if not math.isfinite(median) else median]
        ax.bar(['Giocatore', 'Mediana'], values, color=['#285b3c', '#d8e3ce'], width=.58)
        ax.set_title(label, loc='left', fontsize=11, color='#23352a', pad=12)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.spines['bottom'].set_color('#e5e9e2')
        ax.tick_params(axis='y', left=False, labelleft=False)
        ax.tick_params(axis='x', length=0, labelsize=8, colors='#687266')
        ax.grid(axis='y', color='#edf0eb', linewidth=.8)
        ax.set_axisbelow(True)
        ax.bar_label(ax.containers[0], fmt='%.1f', padding=3, fontsize=8, color='#50604e')
    fig.patch.set_facecolor('white')
    fig.tight_layout(w_pad=2)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_home(app):
    st.markdown(
        '<div class="hero-card"><span class="hero-kicker">GoalMind · calcio, letto meglio</span>'
        '<h1>Dentro il gioco,<br>oltre il risultato.</h1>'
        '<p>Esplora i profili dei calciatori, segui la forma delle squadre e costruisci scenari con i dati storici.</p></div>',
        unsafe_allow_html=True,
    )
    st.write('')
    players = app.player_table()
    teams = app.team_table(active_only=False)
    cols = st.columns(4)
    cols[0].metric('Profili giocatore', f'{len(players):,}'.replace(',', '.'))
    cols[1].metric('Partite analizzate', f"{app.load_report.get('matches', 0):,}".replace(',', '.'))
    cols[2].metric('Squadre', f'{len(app._teams):,}'.replace(',', '.'))
    snapshot = app.snapshot_date.strftime('%d %b %Y') if app.snapshot_date is not None else '—'
    cols[3].metric('Ultimo risultato', snapshot)
    st.write('')
    left, right = st.columns([1.15, .85], gap='large')
    with left:
        st.subheader('Un profilo alla volta')
        featured = choose_player(app, 'home_player', 'Scegli un calciatore')
        a, b = st.columns([.8, 1.2], gap='large')
        with a:
            show_photo(featured)
        with b:
            st.markdown(f'### {featured.name}')
            st.caption(f'{featured.team} · {featured.position}')
            show_player_metrics(featured)
            if math.isfinite(featured.xgperninety):
                st.metric('Expected goals per 90′', f'{featured.xgperninety:.2f}')
    with right:
        st.subheader('Squadre in evidenza')
        divisions = sorted(teams['Division'].dropna().unique())
        if divisions:
            division = st.selectbox('Campionato', divisions, key='home_division')
            top = teams[teams['Division'].eq(division)].sort_values('Elo', ascending=False).head(5)
            st.dataframe(top[['Team', 'Elo', 'RecentMatches']], hide_index=True, use_container_width=True)
        st.caption('Rating Elo calcolati in ordine cronologico dai risultati caricati.')


def render_players(app):
    st.markdown('<p class="eyebrow">Esplora · 01</p>', unsafe_allow_html=True)
    st.title('I calciatori, da vicino.')
    st.caption('Cerca nel dataset completo e confronta i dati del profilo con la mediana degli altri giocatori.')
    player = choose_player(app, 'players_player')
    left, right = st.columns([.72, 1.28], gap='large')
    with left:
        show_photo(player)
        st.markdown(f'### {player.name}')
        st.caption(f'{player.team} · {player.position}')
        show_player_metrics(player)
        st.metric('xG per 90′', f'{player.xgperninety:.2f}' if math.isfinite(player.xgperninety) else 'Non disponibile')
    with right:
        st.subheader('Statistiche del profilo')
        show_player_chart(player, app)
        st.caption('Le barre confrontano i valori assoluti del profilo con la mediana del dataset. I dati non indicano una stagione specifica.')
    st.subheader('Altri indicatori')
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ('Tackle / partita', 'Falli / partita', 'Tiri / partita', 'Passaggi chiave / partita'),
        (player.tacklepergame, player.foulspergame, player.shotspergame, player.keypasspergame),
    ):
        col.metric(label, f'{value:.2f}' if math.isfinite(value) else '—')


def render_goal_scenario(app):
    st.markdown('<p class="eyebrow">Scenario · 02</p>', unsafe_allow_html=True)
    st.title('Quanto è plausibile un gol?')
    st.caption('Una stima esplorativa basata su xG/90, minuti ipotizzati e gol subiti dall’avversaria.')
    left, right = st.columns([.85, 1.15], gap='large')
    with left:
        player = choose_player(app, 'scenario_player')
        minutes = st.slider('Minuti ipotizzati', 0, 120, 90, step=5)
        candidates = [
            team for team in app._teams.values()
            if team.division == (app.find_team(player.team).division if app.find_team(player.team) else None)
            and team.name.casefold() != player.team.casefold()
            and team.defensive_games >= 5
        ]
        candidates.sort(key=lambda team: team.name.casefold())
        opponent = st.selectbox('Avversaria (facoltativa)', [None, *candidates],
                                format_func=lambda team: 'Nessun aggiustamento' if team is None else team.name,
                                key='scenario_opponent')
    with right:
        if not math.isfinite(player.xgperninety) or player.mins_played <= 0:
            st.warning('Per questo profilo non è disponibile un tasso xG/90 utilizzabile.')
        else:
            try:
                if opponent is None:
                    probability = player.prob_goal(minutes)
                    note = 'Stima base: avversaria media.'
                else:
                    probability = app.score_probability(player.name, opponent.name, minutes, player.team)
                    note = f'Correzione difensiva basata su {opponent.defensive_games} partite recenti.'
                st.markdown('<div class="eyebrow">Probabilità stimata di almeno un gol</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:4rem;font-weight:650;letter-spacing:-.07em;color:#153b2b">{probability:.1%}</div>', unsafe_allow_html=True)
                st.progress(probability)
                st.caption(note)
                st.info('Ipotesi: il giocatore disputa tutti i minuti scelti. Il modello non è calibrato su partite future.')
            except ValueError as error:
                st.warning(str(error))
    with st.expander('Come viene calcolata'):
        st.latex(r'\lambda = xG/90 \times minuti/90 \times fattore\ difensivo')
        st.latex(r'P(G \geq 1) = 1 - e^{-\lambda}')
        st.write('Il fattore difensivo confronta i gol subiti per partita con la media del campionato nell’ultima finestra disponibile. Non rappresenta una previsione certa.')


def render_teams(app):
    st.markdown('<p class="eyebrow">Risultati · 03</p>', unsafe_allow_html=True)
    st.title('La forza delle squadre nel tempo.')
    st.caption('Valori Elo ricostruiti partita dopo partita. La classifica è separata per divisione.')
    teams = app.team_table(active_only=True)
    if teams.empty:
        st.info('Non ci sono squadre con abbastanza partite recenti.')
        return
    divisions = sorted(teams['Division'].dropna().unique())
    division = st.selectbox('Divisione', divisions, key='teams_division')
    ranking = teams[teams['Division'].eq(division)].sort_values('Elo', ascending=False).reset_index(drop=True)
    col1, col2 = st.columns([1.05, .95], gap='large')
    with col1:
        st.subheader('Classifica Elo')
        st.dataframe(ranking.head(20), hide_index=True, use_container_width=True)
    with col2:
        st.subheader('Simula una partita')
        names = ranking['Team'].tolist()
        if len(names) < 2:
            st.info('Servono almeno due squadre per simulare una partita.')
            return
        home_name = st.selectbox('Casa', names, key='elo_home')
        away_options = [name for name in names if name != home_name]
        away_name = st.selectbox('Ospite', away_options, key='elo_away')
        home_goals, away_goals = st.columns(2)
        hg = home_goals.number_input('Gol casa', min_value=0, max_value=20, value=1, step=1)
        ag = away_goals.number_input('Gol ospite', min_value=0, max_value=20, value=0, step=1)
        home_row = ranking.loc[ranking['Team'].eq(home_name)].iloc[0]
        away_row = ranking.loc[ranking['Team'].eq(away_name)].iloc[0]
        home = Team(home_name)
        away = Team(away_name)
        home.elo, away.elo = float(home_row['Elo']), float(away_row['Elo'])
        expected = home.compute_expected_score(away.elo, app.DEFAULT_HOME_ADVANTAGE)
        result = 1.0 if hg > ag else 0.0 if hg < ag else 0.5
        delta = app.DEFAULT_K * (result - expected)
        st.metric('Punteggio atteso Elo casa', f'{expected:.2f}', help='Non è una probabilità di vittoria: include anche i pareggi.')
        st.write(f'**Dopo questo risultato:** {home_name} {home.elo + delta:.0f} · {away_name} {away.elo - delta:.0f}')
        st.caption('Simulazione dimostrativa con K = 25 e vantaggio casa = 40. Non salva né modifica lo storico.')
    st.caption(f"Snapshot: {app.snapshot_date.strftime('%d/%m/%Y') if app.snapshot_date is not None else 'non disponibile'} · {app.load_report.get('matches', 0):,} partite caricate.")


def main():
    app = get_application()
    with st.sidebar:
        st.markdown('<div class="brand">Goal<span>Mind</span></div>', unsafe_allow_html=True)
        st.caption('Statistiche di calcio, in prospettiva.')
        page = st.radio('Vai a', ['Panoramica', 'Calciatori', 'Stima gol', 'Elo & squadre'], label_visibility='collapsed')
        st.divider()
        st.caption('Dati storici caricati dal progetto. Le stime sui gol sono esplorative.')
    if page == 'Panoramica':
        render_home(app)
    elif page == 'Calciatori':
        render_players(app)
    elif page == 'Stima gol':
        render_goal_scenario(app)
    else:
        render_teams(app)
    with st.expander('Dati usati'):
        st.write(f"Giocatori caricati: {app.load_report.get('players', 0):,} · Partite valide: {app.load_report.get('matches', 0):,} · Partite scartate: {app.load_report.get('invalid_matches', 0):,} · Duplicati rimossi: {app.load_report.get('duplicate_matches', 0):,}")
        st.caption('I CSV dei giocatori non indicano la stagione delle statistiche. I risultati non si aggiornano automaticamente.')


main()
