import streamlit as st
import psycopg2
import pandas as pd
import os

st.title("CCAD-UAQ PostgreSQL Test")

try:
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10
    )

    st.success("Connection successful")

    df = pd.read_sql(
        "SELECT current_database();",
        conn
    )

    st.dataframe(df)

    conn.close()

except Exception as e:
    st.error(str(e))
