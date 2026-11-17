from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


ROOT = Path(__file__).resolve().parent
PREVIEW_FILE = ROOT / 'web' / 'index.html'

st.set_page_config(
    page_title='GoalMind',
    page_icon='⚽',
    layout='wide',
    initial_sidebar_state='collapsed',
)

st.markdown(
    '''
    <style>
    [data-testid="stHeader"], [data-testid="stToolbar"], footer { display:none; }
    [data-testid="stMainBlockContainer"] { max-width:none; padding:0; }
    .stApp { background:#f7f7f4; }
    </style>
    ''',
    unsafe_allow_html=True,
)

if not PREVIEW_FILE.is_file():
    st.error('Non trovo la pagina GoalMind.')
    st.stop()

page = PREVIEW_FILE.read_text(encoding='utf-8')
components.html(page, height=980, scrolling=True)
