import streamlit as st
from defs import *
import datetime
st.title("Sofascore tactical analysis")

st.write(datetime.datetime.today())
# Define a button to start the analysis after choices are made
if 'match_selected' not in st.session_state:
    st.session_state.match_selected = False

if st.button("Start"):
    contents = init()  # Only calls match_id_init once
    choices = contents

    st.session_state.choices = choices
    st.session_state.match_selected = True

# Show dropdowns only after the "Start Analysis" button is clicked
if st.session_state.match_selected:
    choice = st.selectbox("Match", list(st.session_state.choices.keys()))
    match_id = st.session_state.choices[choice]
    st.write(f"Selected match: {choice}")
    st.write(f"Match ID: {match_id}")
    print(match_id)

    if st.button("Start analysis"):
        match_pos(match_id)