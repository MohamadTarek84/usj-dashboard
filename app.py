import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="USJ Exit Survey Dashboard",
    page_icon="📊",
    layout="wide"
)

MAX_SCORE = 4

@st.cache_data
def load_data():
    df = pd.read_excel("Exit survey 24-25.xlsx")
    df.columns = df.columns.astype(str).str.strip()
    return df

df_original = load_data()


def clean_text(x):
    return (
        str(x).lower().strip()
        .replace("’", "'")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ç", "c")
    )


def find_column(df, keywords):
    for col in df.columns:
        col_clean = clean_text(col)
        if all(clean_text(k) in col_clean for k in keywords):
            return col
    return None


def find_q5_columns(df):
    q5_cols = []
    for col in df.columns:
        c = clean_text(col)
        if c.startswith("q5") or "q5" in c or "experience" in c:
            q5_cols.append(col)
    return q5_cols


def satisfaction_label(pct):
    if pd.isna(pct):
        return "Non disponible"
    elif pct <= 43.75:
        return "Très faible satisfaction"
    elif pct <= 62.50:
        return "Faible satisfaction"
    elif pct <= 81.25:
        return "Satisfaction modérée"
    else:
        return "Forte satisfaction"


def satisfaction_color(pct):
    if pd.isna(pct):
        return "#777777"
    elif pct <= 43.75:
        return "#C62828"
    elif pct <= 81.25:
        return "#F57C00"
    else:
        return "#2E7D32"


def kpi_card(title, value, subtitle, level, color):
    st.markdown(
        f"""
        <div style="
            background-color:#FFFFFF;
            padding:26px;
            border-radius:22px;
            box-shadow:0 8px 25px rgba(0,0,0,0.08);
            border-left:8px solid {color};
            min-height:220px;
        ">
            <div style="font-size:16px; font-weight:800; color:#111; margin-bottom:18px;">
                {title}
            </div>
            <div style="font-size:42px; color:{color}; font-weight:900;">
                {value}
            </div>
            <div style="font-size:13px; color:#777; margin-top:2px;">
                {subtitle}
            </div>
            <div style="
                display:inline-block;
                margin-top:18px;
                padding:6px 12px;
                border-radius:20px;
                background-color:{color}20;
                color:{color};
                font-size:13px;
                font-weight:700;
            ">
                {level}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def apply_linked_filters(df):
    st.sidebar.header("Filtres")

    filtered_df = df.copy()

    filter_columns = [
        "Institution",
        "Faculté",
        "Genre",
        "Diplôme",
        "Cursus",
        "Niveau"
    ]

    for col in filter_columns:
        if col in filtered_df.columns:
            options = sorted(filtered_df[col].dropna().astype(str).unique())
            selected = st.sidebar.selectbox(
                col,
                ["Tous"] + options
            )

            if selected != "Tous":
                filtered_df = filtered_df[
                    filtered_df[col].astype(str) == selected
                ]

    return filtered_df


def score_to_pct(df, col):
    s = pd.to_numeric(df[col], errors="coerce")
    return s.mean() / MAX_SCORE * 100


# ============================================================
# ONE PAGE DASHBOARD
# ============================================================

st.sidebar.title("USJ Exit Survey Dashboard")

st.title("Satisfaction globale et expérience")

df = apply_linked_filters(df_original)

if df.empty:
    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
    st.stop()


# Detect KPI columns
satisfaction_col = find_column(df, ["satisfaction", "univers"])
recommendation_col = find_column(df, ["recommand"])
experience_col = find_column(df, ["experience", "global"])

# Fallbacks
if satisfaction_col is None and "Q1" in df.columns:
    satisfaction_col = "Q1"

if recommendation_col is None and "Q2" in df.columns:
    recommendation_col = "Q2"

if experience_col is None and "Q3" in df.columns:
    experience_col = "Q3"


# Compute satisfaction
if satisfaction_col is not None:
    satisfaction_pct = score_to_pct(df, satisfaction_col)
else:
    satisfaction_pct = None


# Compute recommendation
if recommendation_col is not None:
    recommendation_pct = score_to_pct(df, recommendation_col)
else:
    recommendation_pct = None


# Compute experience
if experience_col is not None:
    experience_pct = score_to_pct(df, experience_col)
else:
    q5_cols = find_q5_columns(df)

    if len(q5_cols) > 0:
        q5_numeric = df[q5_cols].apply(pd.to_numeric, errors="coerce")
        experience_pct = q5_numeric.mean(axis=1).mean() / MAX_SCORE * 100
    else:
        experience_pct = None


# KPI display
col1, col2, col3 = st.columns(3)

with col1:
    kpi_card(
        "Satisfaction globale à l’Université",
        f"{satisfaction_pct:.1f}%" if satisfaction_pct is not None else "N/A",
        "Score de satisfaction",
        satisfaction_label(satisfaction_pct),
        satisfaction_color(satisfaction_pct)
    )

with col2:
    kpi_card(
        "Taux de recommandation de l’USJ",
        f"{recommendation_pct:.1f}%" if recommendation_pct is not None else "N/A",
        "Pourcentage",
        satisfaction_label(recommendation_pct),
        satisfaction_color(recommendation_pct)
    )

with col3:
    kpi_card(
        "Expérience globale USJ",
        f"{experience_pct:.1f}%" if experience_pct is not None else "N/A",
        "Score de satisfaction",
        satisfaction_label(experience_pct),
        satisfaction_color(experience_pct)
    )


with st.expander("Variables utilisées"):
    st.write({
        "Satisfaction globale": satisfaction_col,
        "Recommandation": recommendation_col,
        "Expérience globale": experience_col if experience_col is not None else "Q5 non trouvé / N/A"
    })

with st.expander("Voir toutes les colonnes du fichier"):
    st.write(df_original.columns.tolist())
