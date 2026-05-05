import streamlit as st
import pandas as pd
import unicodedata

st.set_page_config(
    page_title="USJ Exit Survey Dashboard",
    page_icon="📊",
    layout="wide"
)

MAX_SCORE = 4

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    df = pd.read_excel("Exit survey 24-25.xlsx")
    df.columns = df.columns.astype(str).str.strip()
    return df

df_original = load_data()

# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_text(x):
    x = str(x).strip().lower()
    x = x.replace("’", "'").replace("`", "'")
    x = unicodedata.normalize("NFKD", x)
    x = "".join([c for c in x if not unicodedata.combining(c)])
    return x


def find_column(df, possible_names):
    normalized_cols = {normalize_text(col): col for col in df.columns}

    for name in possible_names:
        name_clean = normalize_text(name)
        if name_clean in normalized_cols:
            return normalized_cols[name_clean]

    for col in df.columns:
        col_clean = normalize_text(col)
        for name in possible_names:
            if normalize_text(name) in col_clean:
                return col

    return None


# ============================================================
# LIKERT CONVERSION
# ============================================================

LIKERT_MAP = {
    "pas du tout d'accord": 1,
    "pas d'accord": 2,
    "d'accord": 3,
    "tout a fait d'accord": 4,
    "tout à fait d'accord": 4,

    "pas du tout satisfait": 1,
    "peu satisfait": 2,
    "satisfait": 3,
    "tres satisfait": 4,
    "très satisfait": 4,

    "tres mauvaise": 1,
    "mauvaise": 2,
    "bonne": 3,
    "tres bonne": 4,

    "non": 1,
    "plutot non": 2,
    "plutot oui": 3,
    "oui": 4,
}


def to_numeric_score(series):
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().sum() > 0:
        return numeric

    return series.astype(str).apply(
        lambda x: LIKERT_MAP.get(normalize_text(x), pd.NA)
    ).astype("float")


# ============================================================
# SATISFACTION FUNCTIONS
# ============================================================

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
        return "#F57C00"
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


def score_to_percentage(df, col):
    scores = to_numeric_score(df[col])
    mean_score = scores.mean()
    return mean_score / MAX_SCORE * 100


# ============================================================
# FILTERS
# ============================================================

def apply_filters(df):
    st.sidebar.title("USJ Exit Survey Dashboard")
    st.sidebar.header("Filtres")

    filtered_df = df.copy()

    filter_map = {
        "Institution": ["Institution", "Institut", "Faculté / Institution"],
        "Faculté": ["Faculté", "Faculte", "Faculty", "Institution"],
        "Genre": ["Genre", "Gender", "Sexe"],
        "Diplôme": ["Diplôme", "Diplome", "Degree"],
        "Cursus": ["Cursus", "Programme", "Program"],
        "Niveau": ["Niveau", "Level"]
    }

    used_cols = []

    for label, possible_names in filter_map.items():
        col = find_column(filtered_df, possible_names)

        if col is not None and col not in used_cols:
            used_cols.append(col)

            options = sorted(filtered_df[col].dropna().astype(str).unique())

            selected = st.sidebar.selectbox(
                label,
                ["Tous"] + options,
                key=f"filter_{label}"
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
# KPI COLUMN DETECTION
# ============================================================

satisfaction_col = find_column(
    df,
    [
        "Satisfaction globale à l’Université",
        "Satisfaction globale a l'Universite",
        "Satisfaction globale",
        "Satisfaction à l’Université",
        "Satisfaction a l'Universite",
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
        "Recommendation",
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
        "Expérience à l’USJ",
        "Experience a l'USJ",
        "Q3"
    ]
)

# ============================================================
# CALCULATE KPIs
# ============================================================

satisfaction_pct = (
    score_to_percentage(df, satisfaction_col)
    if satisfaction_col is not None
    else pd.NA
)

recommendation_pct = (
    score_to_percentage(df, recommendation_col)
    if recommendation_col is not None
    else pd.NA
)

experience_pct = (
    score_to_percentage(df, experience_col)
    if experience_col is not None
    else pd.NA
)

# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    kpi_card(
        "Satisfaction globale à l’Université",
        f"{satisfaction_pct:.1f}%" if pd.notna(satisfaction_pct) else "N/A",
        "Score de satisfaction",
        satisfaction_label(satisfaction_pct),
        satisfaction_color(satisfaction_pct)
    )

with col2:
    kpi_card(
        "Taux de recommandation de l’USJ",
        f"{recommendation_pct:.1f}%" if pd.notna(recommendation_pct) else "N/A",
        "Pourcentage",
        satisfaction_label(recommendation_pct),
        satisfaction_color(recommendation_pct)
    )

with col3:
    kpi_card(
        "Expérience globale USJ",
        f"{experience_pct:.1f}%" if pd.notna(experience_pct) else "N/A",
        "Score de satisfaction",
        satisfaction_label(experience_pct),
        satisfaction_color(experience_pct)
    )

# ============================================================
# DEBUG
# ============================================================

with st.expander("Variables utilisées"):
    st.write({
        "Satisfaction globale": satisfaction_col,
        "Recommandation": recommendation_col,
        "Expérience globale": experience_col
    })

with st.expander("Voir toutes les colonnes du fichier"):
    st.write(df_original.columns.tolist())
