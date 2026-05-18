import os
import streamlit as st

DB_PATH = "etat_actuel_responses.db"

st.set_page_config(page_title="Download DB", layout="centered")

st.title("Download submitted data database")

st.write("Current working directory:")
st.code(os.getcwd())

st.write("Expected database path:")
st.code(os.path.abspath(DB_PATH))

if os.path.exists(DB_PATH):
    st.success("Database found.")

    with open(DB_PATH, "rb") as f:
        st.download_button(
            label="Download etat_actuel_responses.db",
            data=f,
            file_name="etat_actuel_responses.db",
            mime="application/octet-stream"
        )
else:
    st.error("Database file not found in this app environment.")
