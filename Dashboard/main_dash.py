import streamlit as st

from st_pages import add_page_title, get_nav_from_toml

st.set_page_config(
    page_title="Trading Dashboard Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

nav = get_nav_from_toml(
    "Dashboard_integration/pages.toml"
)

st.logo(image="assets/logo.png", size="large", icon_image="assets/logo.png")

pg = st.navigation(nav)

add_page_title(pg)

pg.run()