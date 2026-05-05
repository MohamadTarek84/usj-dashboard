import streamlit as st
import pandas as pd
import unicodedata
from textwrap import dedent

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


def normalize_text(x):
    x = str(x).strip().lower()
    x = x.replace("’", "'").replace("`", "'")
    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    return x


LIKERT_MAP = {
    "pas du tout d'accord": 1,
    "pas d'accord": 2,
    "d'accord": 3,
    "tout a fait d'accord": 4,
    "pas du tout satisfait": 1,
    "peu satisfait": 2,
    "satisfait": 3,
    "tres satisfait": 4,
    "non": 1,
    "plutot non": 2,
    "plutot oui": 3,
    "oui": 4,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}


def to_numeric_score(series):
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().sum() > 0:
        return numeric

    converted = series.astype(str).map(lambda x: LIKERT_MAP.get(normalize_text(x)))
    return pd.to_numeric(converted, errors="coerce")


def find_column(df, candidates):
    normalized = {normalize_text(c): c for c in df.columns}

    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized:
            return normalized[key]

    for col in df.columns:
        col_clean = normalize_text(col)
        for candidate in candidates:
            if normalize_text(candidate) in col_clean:
                return col

    return None


def score_to_percentage(df, col):
    if col is None or col not in df.columns:
        return None

    scores = to_numeric_score(df[col])
    mean_score = scores.mean()

    if pd.isna(mean_score):
        return None

    return mean_score / MAX_SCORE * 100


def satisfaction_label(pct):
    if pct is None or pd.isna(pct):
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
    if pct is None or pd.isna(pct):
        return "#777777"
    elif pct <= 43.75:
        return "#C62828"
    elif pct <= 81.25:
        return "#F57C00"
    else:
        return "#2E7D32"


def kpi_card(title, value, subtitle, level, color):
    html = f"""
    <div style="background-color:#FFFFFF; padding:26px; border-radius:22px;
                box-shadow:0 8px 25px rgba(0,0,0,0.08);
                border-left:8px solid {color}; min-height:220px;">
        <div style="font-size:16px; font-weight:800; color:#111; margin-bottom:18px;">
            {title}
        </div>
        <div style="font-size:42px; color:{color}; font-weight:900;">
            {value}
        </div>
        <div style="font-size:13px; color:#777; margin-top:2px;">
            {subtitle}
        </div>
        <div style="display:inline-block; margin-top:18px; padding:6px 12px;
                    border-radius:20px; background-color:{color}20; color:{color};
                    font-size:13px; font-weight:700;">
            {level}
        </div>
    </div>
    """
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)


def apply_filters(df):
    st.sidebar.title("USJ Exit Survey Dashboard")
    st.sidebar.header("Filtres")

    filtered_df = df.copy()

    filters = [
        ("Genre", "Genre"),
        ("Faculté", "Faculté_Institut_g"),
        ("Cursus", "Cursus"),
        ("Niveau", "Niveau"),
    ]

    for label, col in filters:
        if col in filtered_df.columns:
            options = sorted(filtered_df[col].dropna().astype(str).unique())

            selected = st.sidebar.selectbox(
                label,
                ["Tous"] + options,
                key=f"filter_{col}"
            )

            if selected != "Tous":
                filtered_df = filtered_df[
                    filtered_df[col].astype(str) == selected
                ]

    return filtered_df


# ============================================================
# DASHBOARD
# ============================================================

st.title("Satisfaction globale et expérience")

df = apply_filters(df_original)

if df.empty:
    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
    st.stop()


# ============================================================
# KPI VARIABLES
# ============================================================

satisfaction_col = find_column(
    df,
    [
        "Satisfaction globale à l’Université",
        "Satisfaction globale a l'Universite",
        "Satisfaction globale",
        "Q1"
    ]
)

recommendation_col = find_column(
    df,
    [
        "Taux de recommandation de l’USJ",
        "Taux de recommandation de l'USJ",
        "Recommandation",
        "Recommander",
        "Q2"
    ]
)

experience_col = find_column(
    df,
    [
        "Expérience globale USJ",
        "Experience globale USJ",
        "Expérience globale",
        "Experience globale",
        "Q3"
    ]
)


with st.sidebar.expander("Choisir les variables KPI si nécessaire"):
    all_columns = list(df_original.columns)

    satisfaction_col = st.selectbox(
        "Variable satisfaction globale",
        all_columns,
        index=all_columns.index(satisfaction_col) if satisfaction_col in all_columns else 0
    )

    recommendation_col = st.selectbox(
        "Variable recommandation",
        all_columns,
        index=all_columns.index(recommendation_col) if recommendation_col in all_columns else 0
    )

    experience_col = st.selectbox(
        "Variable expérience globale",
        all_columns,
        index=all_columns.index(experience_col) if experience_col in all_columns else 0
    )


satisfaction_pct = score_to_percentage(df, satisfaction_col)
recommendation_pct = score_to_percentage(df, recommendation_col)
experience_pct = score_to_percentage(df, experience_col)


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    color = satisfaction_color(satisfaction_pct)
    kpi_card(
        "Satisfaction globale à l’Université",
        f"{satisfaction_pct:.1f}%" if satisfaction_pct is not None else "N/A",
        "Score de satisfaction",
        satisfaction_label(satisfaction_pct),
        color
    )

with col2:
    color = satisfaction_color(recommendation_pct)
    kpi_card(
        "Taux de recommandation de l’USJ",
        f"{recommendation_pct:.1f}%" if recommendation_pct is not None else "N/A",
        "Pourcentage",
        satisfaction_label(recommendation_pct),
        color
    )

with col3:
    color = satisfaction_color(experience_pct)
    kpi_card(
        "Expérience globale USJ",
        f"{experience_pct:.1f}%" if experience_pct is not None else "N/A",
        "Score de satisfaction",
        satisfaction_label(experience_pct),
        color
    )


with st.expander("Variables utilisées"):
    st.write({
        "Satisfaction globale": satisfaction_col,
        "Recommandation": recommendation_col,
        "Expérience globale": experience_col
    })
