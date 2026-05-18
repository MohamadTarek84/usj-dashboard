import sqlite3
import json
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st

DB_PATH = Path("etat_actuel_responses.db")
ADMIN_CODE = "USJ-ADMIN-2032"

st.set_page_config(page_title="Download Data", layout="wide")

st.title("Download submitted data")

code = st.text_input("Admin code", type="password")

if code.strip().upper() != ADMIN_CODE:
    st.stop()

st.write("DB path:", DB_PATH.resolve())
st.write("DB exists:", DB_PATH.exists())

if not DB_PATH.exists():
    st.error("Database not found in this Streamlit app environment.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM responses ORDER BY id DESC", conn)
conn.close()

if df.empty:
    st.warning("Database exists, but no responses are saved.")
    st.stop()

st.success(f"{len(df)} response(s) found.")

st.dataframe(df, use_container_width=True)

# Raw CSV
csv_raw = df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="Download raw CSV",
    data=csv_raw,
    file_name="etat_actuel_responses_raw.csv",
    mime="text/csv",
)

# Excel
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="responses_raw")

st.download_button(
    label="Download Excel",
    data=excel_buffer.getvalue(),
    file_name="etat_actuel_responses.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# SQLite DB
with open(DB_PATH, "rb") as f:
    st.download_button(
        label="Download SQLite DB",
        data=f,
        file_name="etat_actuel_responses.db",
        mime="application/octet-stream",
    )
