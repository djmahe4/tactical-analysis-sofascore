import streamlit as st
from defs import init,match_pos
import datetime
from animation import match_ani

st.title("Sofascore Tactical Analysis")
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

    # Add a toggle between video and image
    analysis_type = st.radio("Select analysis type:", ("Image", "Video"))

    # Define actions based on toggle choice
    if st.button("Run Analysis"):
        if analysis_type == "Image":
            match_pos(match_id)  # Run match_pos for image analysis
        elif analysis_type == "Video":
            match_ani(match_id)  # Run match_ani for video analysis
