
import os
import textwrap
import warnings
import html as html_lib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as st_components
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

try:
    from scipy import stats
except Exception:
    stats = None

warnings.filterwarnings("ignore")

# =====================================================
# Page configuration
# =====================================================

st.set_page_config(
    page_title="USJ Exit Survey 2022-2025",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# Institutional colors close to USJ / UAQ identity
# =====================================================

USJ_BLUE = "#001B75"
USJ_BLUE_2 = "#003A8C"
USJ_LIGHT_BLUE = "#EAF2FF"
USJ_RED = "#C0003B"
USJ_DARK_RED = "#8B1538"
USJ_GREEN = "#2E7D32"
USJ_ORANGE = "#F57C00"
USJ_GOLD = "#C9A227"
USJ_GRAY = "#F5F7FB"
USJ_TEXT = "#1B2A41"

# Professional institutional palettes
PLOTLY_SEQ = [
    USJ_BLUE,
    USJ_DARK_RED,
    USJ_GREEN,
    USJ_GOLD,
    USJ_BLUE_2,
    "#6D4C41",
    "#5E6C84",
    "#00838F",
    "#7E57C2",
    "#455A64",
]

# Continuous scale used for satisfaction percentages.
# Low results are burgundy, mid results are gold/light blue, high results are institutional blue/green.
PLOTLY_CONT = [
    [0.00, USJ_DARK_RED],
    [0.35, USJ_RED],
    [0.55, USJ_GOLD],
    [0.72, USJ_LIGHT_BLUE],
    [0.86, USJ_BLUE_2],
    [1.00, USJ_GREEN],
]

PLOTLY_DIVERGING = [
    [0.00, USJ_DARK_RED],
    [0.25, USJ_RED],
    [0.50, "#F4F6FA"],
    [0.75, USJ_BLUE_2],
    [1.00, USJ_GREEN],
]

RESPONSE_COLORS = {
    "Très insatisfaisante": USJ_DARK_RED,
    "Très insatisfaisant": USJ_DARK_RED,
    "Insatisfaisante": USJ_RED,
    "Insatisfait": USJ_RED,
    "Pas du tout d’accord": USJ_DARK_RED,
    "Pas d’accord": USJ_RED,
    "Satisfaisante": USJ_BLUE_2,
    "Satisfait": USJ_BLUE_2,
    "D’accord": USJ_BLUE_2,
    "Très satisfaisante": USJ_GREEN,
    "Très satisfait": USJ_GREEN,
    "Tout à fait d’accord": USJ_GREEN,
    "Pas au courant": "#8A94A6",
    "Oui": USJ_GREEN,
    "Non": USJ_DARK_RED,
}

# =====================================================
# Global CSS
# =====================================================

st.markdown(
    f"""
    <style>
    .main {{
        background-color: #FFFFFF;
    }}

    h1, h2, h3 {{
        color: {USJ_BLUE};
        font-family: Candara, Arial, sans-serif;
    }}

    div[data-testid="stMetric"] {{
        background-color: white;
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }}

    .stRadio > div {{
        background: #F7F9FC;
        padding: 8px 12px;
        border-radius: 16px;
    }}

    button[kind="secondary"] {{
        border-radius: 18px !important;
        border: 1px solid #D0D7E2 !important;
    }}

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 1.5rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# General helpers
# =====================================================

@st.cache_data(show_spinner=False)
def load_data():
    possible_files = [
        "Exit_Survey_all-data.xlsx",
        "Exit_Survey_all_data.xlsx",
        "Exit_Survey_Historical_Common_Questions.xlsx",
        "Exit survey all-data.xlsx",
        "Exit survey all data.xlsx",
    ]

    for file in possible_files:
        if os.path.exists(file):
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str).str.strip()
            return df

    st.error("Excel file not found. Please upload the historical file to GitHub.")
    st.write("Available files:")
    st.write(os.listdir("."))
    st.stop()


def recode_series(series, mapping):
    return (
        series.astype(str)
        .str.strip()
        .replace(mapping)
        .replace({"nan": np.nan, "None": np.nan, "NaT": np.nan, "<NA>": np.nan})
    )


def normalize_year_column(df):
    df = df.copy()
    if "Année" in df.columns and "Year" not in df.columns:
        df = df.rename(columns={"Année": "Year"})
    if "Year" not in df.columns:
        st.error("The historical dataset must contain a 'Year' or 'Année' column.")
        st.stop()
    df["Year"] = df["Year"].astype(str).str.strip()
    return df


def kpi_color_percentage(value_pct):
    if pd.isna(value_pct):
        return "#777777"
    elif value_pct < 50:
        return USJ_RED
    elif value_pct <= 75:
        return USJ_BLUE
    else:
        return USJ_GREEN


def pct_from_mean(value):
    if pd.isna(value):
        return np.nan
    return value / 4 * 100


def safe_pct(value):
    return "NA" if pd.isna(value) else f"{value:.1f}%"


def safe_num(value, digits=1):
    return "NA" if pd.isna(value) else f"{value:.{digits}f}"


def calculate_recommendation_rate(data, column):
    if column not in data.columns:
        return np.nan
    valid = data[column].dropna().astype(str).str.strip()
    if len(valid) == 0:
        return np.nan
    return valid.eq("Oui").sum() / len(valid) * 100


def clean_component_name(name):
    return (
        name
        .replace("Score ", "")
        .replace("score ", "")
        .strip()
        .capitalize()
    )


def filter_options(data, column):
    if column not in data.columns:
        return ["Tous"]
    values = sorted(data[column].dropna().astype(str).unique())
    return ["Tous"] + values


def summary_box(text, color=USJ_BLUE, background="#F7F9FC"):
    st.html(
        f"""
        <div style="
            background-color:{background};
            border-left:6px solid {color};
            padding:18px 20px;
            border-radius:16px;
            margin-top:18px;
            margin-bottom:20px;
            font-family:Candara, Arial, sans-serif;
            font-size:16px;
            line-height:1.65;
            color:{USJ_TEXT};
            box-shadow:0 4px 14px rgba(0,0,0,0.04);
        ">
            {text}
        </div>
        """
    )


def section_header(title, subtitle=None):
    subtitle_html = f"<p style='margin-top:4px;color:#5F6B7A;font-size:16px;'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-top:12px;margin-bottom:14px;">
            <h2 style="color:{USJ_BLUE}; margin-bottom:0;">{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def kpi_card(title, value, subtitle="Score de satisfaction", delta=None):
    value_pct = np.nan if pd.isna(value) else value / 4 * 100
    color = kpi_color_percentage(value_pct)
    display_value = "NA" if pd.isna(value_pct) else f"{value_pct:.1f}%"

    delta_html = ""
    if delta is not None and pd.notna(delta):
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "●")
        delta_color = USJ_GREEN if delta > 0 else (USJ_RED if delta < 0 else "#777777")
        delta_html = f"""
        <div style="font-size:13px; color:{delta_color}; font-weight:700; margin-top:6px;">
            {arrow} {delta:+.1f} pts vs année précédente
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:20px;
            padding:22px;
            box-shadow:0 6px 20px rgba(0,0,0,0.08);
            border-left:8px solid {color};
            min-height:155px;
        ">
            <div style="font-size:15px; color:#303742; font-weight:700;">{title}</div>
            <div style="font-size:40px; color:{color}; font-weight:900; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#667085; margin-top:4px;">{subtitle}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def percent_card(title, value, subtitle="Pourcentage", delta=None):
    color = kpi_color_percentage(value)
    display_value = "NA" if pd.isna(value) else f"{value:.1f}%"

    delta_html = ""
    if delta is not None and pd.notna(delta):
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "●")
        delta_color = USJ_GREEN if delta > 0 else (USJ_RED if delta < 0 else "#777777")
        delta_html = f"""
        <div style="font-size:13px; color:{delta_color}; font-weight:700; margin-top:6px;">
            {arrow} {delta:+.1f} pts vs année précédente
        </div>
        """

    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:20px;
            padding:22px;
            box-shadow:0 6px 20px rgba(0,0,0,0.08);
            border-left:8px solid {color};
            min-height:155px;
        ">
            <div style="font-size:15px; color:#303742; font-weight:700;">{title}</div>
            <div style="font-size:40px; color:{color}; font-weight:900; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#667085; margin-top:4px;">{subtitle}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def insight_card(title, value, subtitle, color=USJ_BLUE):
    st.markdown(
        f"""
        <div style="
            background:linear-gradient(135deg, #FFFFFF 0%, #F7F9FC 100%);
            border:1px solid #DDE5F0;
            border-radius:20px;
            padding:20px;
            min-height:135px;
            box-shadow:0 5px 18px rgba(0,0,0,0.06);
        ">
            <div style="font-size:14px; font-weight:800; color:{USJ_TEXT};">{title}</div>
            <div style="font-size:32px; font-weight:900; color:{color}; margin-top:8px;">{value}</div>
            <div style="font-size:13px; color:#667085; margin-top:5px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def importance_card(title, value, subtitle):
    color = kpi_color_percentage(value)
    display_value = "NA" if pd.isna(value) else f"{value:.1f}%"

    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:18px;
            padding:22px;
            box-shadow:0 4px 14px rgba(0,0,0,0.08);
            border-left:7px solid {color};
            min-height:155px;
        ">
            <div style="font-size:15px; color:#444; font-weight:700;">{title}</div>
            <div style="font-size:36px; color:{color}; font-weight:900; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#777; margin-top:4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def cronbach_alpha(data):
    data = data.dropna()
    if data.shape[0] < 5 or data.shape[1] < 2:
        return np.nan

    item_variances = data.var(axis=0, ddof=1)
    total_variance = data.sum(axis=1).var(ddof=1)
    n_items = data.shape[1]

    if total_variance == 0:
        return np.nan

    return (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)


def alpha_interpretation(alpha):
    if pd.isna(alpha):
        return "Non calculable"
    elif alpha >= 0.90:
        return "Excellente cohérence interne"
    elif alpha >= 0.80:
        return "Bonne cohérence interne"
    elif alpha >= 0.70:
        return "Cohérence interne acceptable"
    elif alpha >= 0.60:
        return "Cohérence interne modérée"
    else:
        return "Cohérence interne faible"


def theme_layout(fig, height=480, showlegend=True):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Candara, Arial", size=13, color=USJ_TEXT),
        title=dict(font=dict(size=20, color=USJ_BLUE), x=0.01),
        margin=dict(l=30, r=30, t=70, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if showlegend else dict(),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Candara, Arial"),
        coloraxis_colorbar=dict(tickfont=dict(family="Candara, Arial", color=USJ_TEXT)),
    )
    fig.update_xaxes(showgrid=False, linecolor="#D9E1EC")
    fig.update_yaxes(gridcolor="#E6ECF3", linecolor="#D9E1EC")
    return fig


# =====================================================
# Survey sections and preprocessing
# =====================================================

@st.cache_data(show_spinner=False)
def prepare_data():
    df_original = normalize_year_column(load_data())
    df_coded = df_original.copy()

    if "Faculté_Institut_g" in df_coded.columns:
        df_coded["Faculté_Institut_g"] = df_coded["Faculté_Institut_g"].replace({"ELFS": "ESTS"})
        df_original["Faculté_Institut_g"] = df_original["Faculté_Institut_g"].replace({"ELFS": "ESTS"})

    satisfaction_mapping_f = {
        "Très insatisfaisante": 1,
        "Insatisfaisante": 2,
        "Satisfaisante": 3,
        "Très satisfaisante": 4
    }

    satisfaction_mapping_m = {
        "Très insatisfaisant": 1,
        "Insatisfait": 2,
        "Satisfait": 3,
        "Très satisfait": 4
    }

    accord_mapping = {
        "Pas du tout d’accord": 1,
        "Pas d’accord": 2,
        "D’accord": 3,
        "Tout à fait d’accord": 4
    }

    vie_mapping = {
        "Pas au courant": np.nan,
        "Très insatisfaisante": 1,
        "Insatisfaisante": 2,
        "Satisfaisante": 3,
        "Très satisfaisante": 4
    }

    binary_mapping = {
        "Non": 0,
        "Oui": 1
    }

    enseignement_items = [
        "1_a- La qualité de l'enseignement dans les unités d’enseignement obligatoires",
        "1_b- La qualité de l'enseignement dans les unités d’enseignement optionnelles",
        "1_c- La qualité de l'enseignement dans les cours de langue",
        "1_d- Usage de méthodes pédagogiques actives",
        "1_e- Usage des outils technologiques par les enseignants",
        "1_f- La pertinence du programme",
        "1_g- La charge de travail du programme",
        "1_h- La qualité des expériences labo/labo informatique"
    ]

    accompagnement_items = [
        "2a- Qualité du conseil et de l'orientation académique",
        "2b- Qualité du conseil et de l'orientation administratif",
        "2c- Disponibilité & interaction avec les enseignants",
        "2d- Disponibilité & interaction avec le personnel administratif"
    ]

    competences_items = [
        "5_a- Améliorer les compétences numériques",
        "5_b- Améliorer les capacités de travail en équipe",
        "5_c- Travailler avec des personnes d'origines et de cultures variées",
        "5_d- Développer les capacités d'analyse et de résolution de problèmes",
        "5_e- Développer une réflexion personnelle",
        "5_f- Développer les compétences en matière de communication écrite",
        "5_g- Développer les compétences en matière de communication orale",
        "5_h- Développer les capacités de planification",
        "5_i- Développer la capacité d’apprendre tout au long de la vie",
        "5_j- Acquérir des compétences entrepreneuriales"
    ]

    experience_items = [
        "41_a- Votre expérience académique à l’USJ",
        "41_b- Votre expérience de la vie étudiante à l’USJ",
        "41_c- Vos opportunités de développement personnel",
        "41_d- Votre acquisition des compétences nécessaires"
    ]

    services_items = [
        "28_a-Processus d’admission",
        "28_b-Service d'aide psychologique",
        "28_c-Service de l’insertion professionnelle",
        "28_d-Service étudiant d’information et d’orientation",
        "28_e-Service social",
        "28_f-Service de la vie étudiante",
        "28_g-USJ en mission",
        "28_h-O7",
        "28_i-Service du sport",
        "28_j-Service de soins (Centre de soins dentaires, …)",
        "28_k-Aumônerie et pastorale"
    ]

    vie_items = [
        col for col in [
            "29_a- Activités organisées par la pastorale / l’Aumônerie",
            "29_b- Activités sociales par campus / Événements et clubs étudiants",
            "29_c- Vie sur le campus, environnement et ambiance sociales",
            "29_d- Liberté d'expression et respect des croyances religieuses d’autrui",
            "29_e- Activités sportives",
            "29_f- Clubs étudiants",
            "29_g- Leadership et bénévolat (O7/USJ en mission)",
            "29_h- Activités du Service de la vie étudiante"
        ]
        if col in df_coded.columns
    ]

    infrastructures_items = [
        "40_a- Accès aux ordinateurs",
        "40_b- Accès aux logiciels",
        "40_c- Accès à une connexion Internet/WiFi fiable et rapide sur le campus",
        "40_d- Aménagement des installations pour les personnes handicapées ou ayant des besoins particuliers",
        "40_e- Salles de cours",
        "40_f- Laboratoires et laboratoires informatiques",
        "40_g- Ressources des bibliothèques",
        "40_h- Gym et Installations sportives",
        "40_i- Qualité des aliments et variété du menu de la cafeteria",
        "40_j- Modernité et propreté des installations et équipements",
        "40_k- Espace extérieur",
        "40_l- Dortoirs",
        "40_m- Parking"
    ]

    financial_items = [
        "26- satisfait par les frais de scolarité à l’USJ par rapport à la qualité de l’enseignement ?",
        "27- satisfait par les frais de scolarité à l’USJ par rapport à ceux d’autres universités ?"
    ]

    section_definitions = {
        "Enseignement et apprentissage": {"items": enseignement_items, "mapping": satisfaction_mapping_f, "score": "Score enseignement et apprentissage"},
        "Accompagnement et encadrement": {"items": accompagnement_items, "mapping": satisfaction_mapping_f, "score": "Score accompagnement et encadrement"},
        "Développement des compétences": {"items": competences_items, "mapping": accord_mapping, "score": "Score développement des compétences"},
        "Expérience globale USJ": {"items": experience_items, "mapping": satisfaction_mapping_f, "score": "Score expérience globale USJ"},
        "Services de l’USJ": {"items": services_items, "mapping": satisfaction_mapping_f, "score": "Score services USJ"},
        "Vie étudiante et activités": {"items": vie_items, "mapping": vie_mapping, "score": "Score vie étudiante et activités"},
        "Infrastructures et équipements": {"items": infrastructures_items, "mapping": satisfaction_mapping_f, "score": "Score infrastructures et équipements"},
        "Perception financière": {"items": financial_items, "mapping": satisfaction_mapping_m, "score": None},
    }

    components = {}

    for section, details in section_definitions.items():
        existing = [col for col in details["items"] if col in df_coded.columns]
        for col in existing:
            df_coded[col] = pd.to_numeric(recode_series(df_original[col], details["mapping"]), errors="coerce")

        if details["score"] is not None and existing:
            df_coded[details["score"]] = df_coded[existing].mean(axis=1, skipna=True)

        components[section] = existing

    q42 = "42-Quel est le niveau de votre satisfaction globale à l’Université ?"
    q43 = "43-Recommanderiez-vous l’USJ à un proche ou à un ami ?"
    q26 = "26- satisfait par les frais de scolarité à l’USJ par rapport à la qualité de l’enseignement ?"
    q27 = "27- satisfait par les frais de scolarité à l’USJ par rapport à ceux d’autres universités ?"

    if q42 in df_original.columns:
        df_coded["Score satisfaction globale"] = pd.to_numeric(
            recode_series(df_original[q42], satisfaction_mapping_m),
            errors="coerce"
        )
    else:
        df_coded["Score satisfaction globale"] = np.nan

    if q43 in df_original.columns:
        df_coded[q43] = df_original[q43].astype(str).str.strip().replace({"nan": np.nan})
    else:
        df_coded[q43] = np.nan

    if q26 in df_original.columns:
        df_coded["Score frais / qualité enseignement"] = pd.to_numeric(
            recode_series(df_original[q26], satisfaction_mapping_m),
            errors="coerce"
        )
    else:
        df_coded["Score frais / qualité enseignement"] = np.nan

    if q27 in df_original.columns:
        df_coded["Score frais / autres universités"] = pd.to_numeric(
            recode_series(df_original[q27], satisfaction_mapping_m),
            errors="coerce"
        )
    else:
        df_coded["Score frais / autres universités"] = np.nan

    score_columns = [
        "Score satisfaction globale",
        "Score enseignement et apprentissage",
        "Score accompagnement et encadrement",
        "Score développement des compétences",
        "Score expérience globale USJ",
        "Score services USJ",
        "Score vie étudiante et activités",
        "Score infrastructures et équipements",
        "Score frais / qualité enseignement",
        "Score frais / autres universités"
    ]

    for col in score_columns:
        if col not in df_coded.columns:
            df_coded[col] = np.nan

    return df_original, df_coded, components, q42, q43, q26, q27


@st.cache_data(show_spinner=False)
def train_satisfaction_importance(model_sat, feature_columns):
    X = model_sat[feature_columns]
    y = model_sat["Score satisfaction globale"]

    rf = RandomForestRegressor(
        n_estimators=250,
        random_state=42,
        max_depth=5,
        n_jobs=-1
    )

    rf.fit(X, y)
    return rf.feature_importances_


@st.cache_data(show_spinner=False)
def train_recommendation_importance(model_rec, feature_columns):
    X = model_rec[feature_columns]
    y = model_rec["Recommandation"]

    rf = RandomForestClassifier(
        n_estimators=250,
        random_state=42,
        max_depth=5,
        class_weight="balanced",
        n_jobs=-1
    )

    rf.fit(X, y)
    return rf.feature_importances_


# =====================================================
# Analysis helpers
# =====================================================

SCORE_COLUMNS = [
    "Score satisfaction globale",
    "Score enseignement et apprentissage",
    "Score accompagnement et encadrement",
    "Score développement des compétences",
    "Score expérience globale USJ",
    "Score services USJ",
    "Score vie étudiante et activités",
    "Score infrastructures et équipements",
    "Score frais / qualité enseignement",
    "Score frais / autres universités"
]

SCORE_LABELS = {
    "Score satisfaction globale": "Satisfaction globale",
    "Score enseignement et apprentissage": "Enseignement et apprentissage",
    "Score accompagnement et encadrement": "Accompagnement et encadrement",
    "Score développement des compétences": "Développement des compétences",
    "Score expérience globale USJ": "Expérience globale USJ",
    "Score services USJ": "Services de l’USJ",
    "Score vie étudiante et activités": "Vie étudiante et activités",
    "Score infrastructures et équipements": "Infrastructures et équipements",
    "Score frais / qualité enseignement": "Frais / qualité enseignement",
    "Score frais / autres universités": "Frais / autres universités",
}


def build_year_summary(data, q43):
    rows = []
    for year, g in data.groupby("Year"):
        row = {"Année": year, "N": len(g)}
        for col in SCORE_COLUMNS:
            if col in g.columns:
                row[SCORE_LABELS[col]] = pct_from_mean(g[col].mean())
        row["Taux de recommandation"] = calculate_recommendation_rate(g, q43)
        rows.append(row)
    out = pd.DataFrame(rows).sort_values("Année")
    return out


def build_component_long(data):
    rows = []
    for col in SCORE_COLUMNS:
        if col in data.columns:
            for year, g in data.groupby("Year"):
                rows.append({
                    "Année": year,
                    "Dimension": SCORE_LABELS[col],
                    "Pourcentage": pct_from_mean(g[col].mean()),
                    "N valide": g[col].notna().sum()
                })
    return pd.DataFrame(rows)


def compute_previous_delta(year_summary, selected_year, column):
    if selected_year == "Tous" or column not in year_summary.columns:
        return None
    years = year_summary["Année"].tolist()
    if selected_year not in years:
        return None
    idx = years.index(selected_year)
    if idx == 0:
        return None
    current = year_summary.loc[year_summary["Année"] == selected_year, column].iloc[0]
    previous = year_summary.loc[year_summary["Année"] == years[idx - 1], column].iloc[0]
    if pd.isna(current) or pd.isna(previous):
        return None
    return current - previous


def anova_or_kruskal(data, value_col):
    temp = data[["Year", value_col]].dropna()
    groups = [g[value_col].values for _, g in temp.groupby("Year") if len(g) > 1]
    if len(groups) < 2 or stats is None:
        return np.nan, "Non calculable"
    try:
        f_stat, p_value = stats.f_oneway(*groups)
        return p_value, "ANOVA"
    except Exception:
        try:
            h_stat, p_value = stats.kruskal(*groups)
            return p_value, "Kruskal-Wallis"
        except Exception:
            return np.nan, "Non calculable"


def chi_square_recommendation(data, q43):
    if q43 not in data.columns or stats is None:
        return np.nan
    temp = data[["Year", q43]].copy()
    temp[q43] = temp[q43].astype(str).str.strip()
    temp = temp[temp[q43].isin(["Oui", "Non"])]
    if temp["Year"].nunique() < 2 or temp[q43].nunique() < 2:
        return np.nan
    table = pd.crosstab(temp["Year"], temp[q43])
    try:
        chi2, p, dof, expected = stats.chi2_contingency(table)
        return p
    except Exception:
        return np.nan


def p_interpretation(p):
    if pd.isna(p):
        return "Non calculable"
    if p < 0.001:
        return "Différence hautement significative"
    if p < 0.01:
        return "Différence très significative"
    if p < 0.05:
        return "Différence significative"
    return "Différence non significative"


def question_short_label(question):
    q = str(question)
    if "-" in q:
        return q.split("-", 1)[0].strip()
    return q[:35]


def score_question_label(question):
    q = str(question)
    if "-" in q:
        return q.split("-", 1)[1].strip()
    return q


def wrap_label(label, width=46):
    label = str(label).strip()
    return "<br>".join(textwrap.wrap(label, width=width)) if label else label


def question_display_label(question, width=70):
    # Display the real question wording instead of technical item codes such as 1_a or 1_b.
    return wrap_label(score_question_label(question), width=width)


def plain_question_label(question):
    return score_question_label(question)


def section_question_summary(data, items):
    rows = []
    for item in items:
        if item in data.columns:
            series = data[item]
            rows.append({
                "Question": item,
                "Libellé question": plain_question_label(item),
                "Libellé affiché": question_display_label(item, width=58),
                "Résultat (%)": pct_from_mean(series.mean()),
                "Moyenne /4": series.mean(),
                "N valide": series.notna().sum(),
                "Taux de données manquantes (%)": series.isna().mean() * 100
            })
    return pd.DataFrame(rows).sort_values("Résultat (%)", ascending=False)


def section_trend(data, items):
    rows = []
    for item in items:
        if item in data.columns:
            for year, g in data.groupby("Year"):
                rows.append({
                    "Année": year,
                    "Question": question_display_label(item, width=42),
                    "Question complète": plain_question_label(item),
                    "Résultat (%)": pct_from_mean(g[item].mean())
                })
    return pd.DataFrame(rows)


def response_distribution(original_data, coded_data, items):
    rows = []
    for item in items:
        if item in original_data.columns and item in coded_data.columns:
            temp = pd.DataFrame({
                "Question": question_display_label(item, width=62),
                "Question complète": plain_question_label(item),
                "Réponse": original_data[item].astype(str).str.strip().replace({"nan": np.nan}),
                "Year": coded_data["Year"]
            })
            temp = temp.dropna(subset=["Réponse"])
            for (year, q, q_full, resp), g in temp.groupby(["Year", "Question", "Question complète", "Réponse"]):
                rows.append({
                    "Année": year,
                    "Question": q,
                    "Question complète": q_full,
                    "Réponse": resp,
                    "N": len(g)
                })
    dist = pd.DataFrame(rows)
    if dist.empty:
        return dist
    dist["Pourcentage"] = dist.groupby(["Année", "Question"])["N"].transform(lambda x: x / x.sum() * 100)
    return dist


def correlation_with_section_mean(data, items):
    valid_items = [i for i in items if i in data.columns]
    if len(valid_items) < 2:
        return pd.DataFrame(), pd.DataFrame()

    temp = data[valid_items].copy()
    temp["Moyenne de la section"] = temp[valid_items].mean(axis=1, skipna=True)
    corr = temp.corr(numeric_only=True)

    ranking = (
        corr["Moyenne de la section"]
        .drop(labels=["Moyenne de la section"], errors="ignore")
        .reset_index()
    )
    ranking.columns = ["Question", "Corrélation avec la moyenne"]
    ranking["Question affichée"] = ranking["Question"].apply(lambda x: question_display_label(x, width=58))
    ranking = ranking.sort_values("Corrélation avec la moyenne", ascending=False)

    return corr, ranking


# =====================================================
# Load data
# =====================================================

with st.spinner("Chargement du tableau de bord..."):
    df_original, df_coded, components, q42, q43, q26, q27 = prepare_data()

# =====================================================
# Header
# =====================================================

header_left, header_right = st.columns([4.5, 1.5])

with header_left:
    st.markdown(
        f"""
        <h1 style="color:{USJ_BLUE}; margin-bottom:0;">
            Tableau de bord – Exit Survey USJ 2022-2025
        </h1>
        <p style="font-size:18px; color:#555; margin-top:4px;">
            Analyse historique, indicateurs clés, comparaisons et leviers d’amélioration
        </p>
        """,
        unsafe_allow_html=True
    )

with header_right:
    if os.path.exists("LogoUAQ.png"):
        st.image("LogoUAQ.png", width=260)
    elif os.path.exists("usj_logo.png"):
        st.image("usj_logo.png", width=170)

st.divider()

# =====================================================
# Linked filters
# =====================================================

if st.button("Réinitialiser les filtres"):
    st.session_state["filter_year"] = "Tous"
    st.session_state["filter_genre"] = "Tous"
    st.session_state["filter_faculte"] = "Tous"
    st.session_state["filter_cursus"] = "Tous"
    st.session_state["filter_niveau"] = "Tous"
    st.rerun()

filter_cols = st.columns(5)
df_filter_base = df_coded.copy()

with filter_cols[0]:
    year = st.selectbox("Année", filter_options(df_filter_base, "Year"), key="filter_year")

df_after_year = df_filter_base.copy()
if year != "Tous":
    df_after_year = df_after_year[df_after_year["Year"].astype(str) == year]

with filter_cols[1]:
    genre = st.selectbox("Genre", filter_options(df_after_year, "Genre"), key="filter_genre")

df_after_genre = df_after_year.copy()
if genre != "Tous":
    df_after_genre = df_after_genre[df_after_genre["Genre"].astype(str) == genre]

with filter_cols[2]:
    faculte = st.selectbox("Faculté", filter_options(df_after_genre, "Faculté_Institut_g"), key="filter_faculte")

df_after_faculte = df_after_genre.copy()
if faculte != "Tous":
    df_after_faculte = df_after_faculte[df_after_faculte["Faculté_Institut_g"].astype(str) == faculte]

with filter_cols[3]:
    cursus = st.selectbox("Cursus", filter_options(df_after_faculte, "Cursus"), key="filter_cursus")

df_after_cursus = df_after_faculte.copy()
if cursus != "Tous":
    df_after_cursus = df_after_cursus[df_after_cursus["Cursus"].astype(str) == cursus]

with filter_cols[4]:
    niveau = st.selectbox("Niveau", filter_options(df_after_cursus, "Niveau"), key="filter_niveau")

df_filtered = df_after_cursus.copy()
if niveau != "Tous":
    df_filtered = df_filtered[df_filtered["Niveau"].astype(str) == niveau]

st.markdown(
    f"""
    <div style="font-size:16px; margin-top:10px; margin-bottom:18px;">
        <b>Nombre de répondants affichés :</b> {len(df_filtered)}
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# Navigation
# =====================================================

page = st.radio(
    "Navigation",
    [
        "Vue générale des indicateurs",
        "Comparaison historique",
        "Facteurs clés d’amélioration",
        "Résultats descriptifs par section",
        "Statistiques inférentielles",
        "Méthodologie des composantes",
        "Rapport synthétique imprimable"
    ],
    horizontal=True
)

year_summary_all = build_year_summary(df_coded, q43)
year_summary_filtered = build_year_summary(df_filtered, q43)
component_long_filtered = build_component_long(df_filtered)

# =====================================================
# Page 1 - Overview
# =====================================================

def page_indicators():
    section_header(
        "Vue générale des indicateurs",
        "Synthèse dynamique des principaux indicateurs de satisfaction et de recommandation."
    )

    selected_year = year

    satisfaction_pct = pct_from_mean(df_filtered["Score satisfaction globale"].mean())
    recommandation_pct = calculate_recommendation_rate(df_filtered, q43)

    delta_sat = compute_previous_delta(year_summary_filtered, selected_year, "Satisfaction globale")
    delta_rec = compute_previous_delta(year_summary_filtered, selected_year, "Taux de recommandation")

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card(
            "Satisfaction globale à l’Université",
            df_filtered["Score satisfaction globale"].mean(),
            "Pourcentage de satisfaction",
            delta=delta_sat
        )

    with c2:
        percent_card(
            "Taux de recommandation de l’USJ",
            recommandation_pct,
            "Réponses Oui",
            delta=delta_rec
        )

    with c3:
        kpi_card(
            "Expérience globale USJ",
            df_filtered["Score expérience globale USJ"].mean(),
            "Expérience académique et personnelle"
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        kpi_card("Enseignement et apprentissage", df_filtered["Score enseignement et apprentissage"].mean())

    with c5:
        kpi_card("Accompagnement et encadrement", df_filtered["Score accompagnement et encadrement"].mean())

    with c6:
        kpi_card("Développement des compétences", df_filtered["Score développement des compétences"].mean())

    c7, c8, c9 = st.columns(3)

    with c7:
        kpi_card("Services de l’USJ", df_filtered["Score services USJ"].mean())

    with c8:
        kpi_card(
            "Vie étudiante et activités",
            df_filtered["Score vie étudiante et activités"].mean(),
            "Pas au courant exclu"
        )

    with c9:
        kpi_card("Infrastructures et équipements", df_filtered["Score infrastructures et équipements"].mean())

    c10, c11 = st.columns(2)

    with c10:
        kpi_card("Frais de scolarité / qualité de l’enseignement", df_filtered["Score frais / qualité enseignement"].mean())

    with c11:
        kpi_card("Frais de scolarité / autres universités", df_filtered["Score frais / autres universités"].mean())

    component_summary = pd.DataFrame({
        "Dimension": [
            "Enseignement et apprentissage",
            "Accompagnement et encadrement",
            "Développement des compétences",
            "Expérience globale USJ",
            "Services de l’USJ",
            "Vie étudiante et activités",
            "Infrastructures et équipements",
            "Frais / qualité de l’enseignement",
            "Frais / autres universités"
        ],
        "Pourcentage": [
            pct_from_mean(df_filtered["Score enseignement et apprentissage"].mean()),
            pct_from_mean(df_filtered["Score accompagnement et encadrement"].mean()),
            pct_from_mean(df_filtered["Score développement des compétences"].mean()),
            pct_from_mean(df_filtered["Score expérience globale USJ"].mean()),
            pct_from_mean(df_filtered["Score services USJ"].mean()),
            pct_from_mean(df_filtered["Score vie étudiante et activités"].mean()),
            pct_from_mean(df_filtered["Score infrastructures et équipements"].mean()),
            pct_from_mean(df_filtered["Score frais / qualité enseignement"].mean()),
            pct_from_mean(df_filtered["Score frais / autres universités"].mean())
        ]
    }).dropna()

    if not component_summary.empty and pd.notna(satisfaction_pct):
        best_dimension = component_summary.sort_values("Pourcentage", ascending=False).iloc[0]
        weakest_dimension = component_summary.sort_values("Pourcentage", ascending=True).iloc[0]

        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture synthétique</span><br>
            Pour les filtres sélectionnés, la satisfaction globale atteint
            <b>{safe_pct(satisfaction_pct)}</b>, tandis que le taux de recommandation de l’USJ est de
            <b>{safe_pct(recommandation_pct)}</b>. La dimension la mieux évaluée est
            <b>{best_dimension["Dimension"]}</b> avec <b>{best_dimension["Pourcentage"]:.1f}%</b>.
            La dimension la plus faible est <b>{weakest_dimension["Dimension"]}</b> avec
            <b>{weakest_dimension["Pourcentage"]:.1f}%</b>. Cette lecture permet d’identifier rapidement
            les forces institutionnelles et les dimensions à prioriser.
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )

    if year == "Tous" and len(year_summary_filtered) > 1:
        section_header("Évolution synthétique", "Tendance globale des indicateurs principaux sur les années disponibles.")

        trend = year_summary_filtered[["Année", "Satisfaction globale", "Taux de recommandation"]].melt(
            id_vars="Année",
            var_name="Indicateur",
            value_name="Pourcentage"
        )

        fig = px.line(
            trend,
            x="Année",
            y="Pourcentage",
            color="Indicateur",
            markers=True,
            text="Pourcentage",
            color_discrete_sequence=[USJ_BLUE, "#7BC4FF"]
        )

        fig.update_traces(texttemplate="%{text:.1f}%", textposition="top center", mode="lines+markers+text")
        fig.update_layout(
            title="Évolution de la satisfaction globale et de la recommandation",
            yaxis_title="Pourcentage",
            xaxis_title="Année"
        )
        theme_layout(fig, height=430)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# =====================================================
# Page 2 - Historical comparison
# =====================================================

def page_historical_comparison():
    section_header(
        "Comparaison historique",
        "Analyse de l’évolution des indicateurs par année, avec écarts, tableaux comparatifs et tests statistiques."
    )

    if len(year_summary_filtered) == 0:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    c1, c2, c3, c4 = st.columns(4)
    years_available = year_summary_filtered["Année"].nunique()

    with c1:
        insight_card("Années couvertes", years_available, "Période historique", USJ_BLUE)

    with c2:
        latest_year = year_summary_filtered["Année"].max()
        latest_sat = year_summary_filtered.loc[year_summary_filtered["Année"] == latest_year, "Satisfaction globale"].iloc[0]
        insight_card("Dernière satisfaction", safe_pct(latest_sat), latest_year, kpi_color_percentage(latest_sat))

    with c3:
        if years_available > 1:
            first_sat = year_summary_filtered.sort_values("Année")["Satisfaction globale"].iloc[0]
            last_sat = year_summary_filtered.sort_values("Année")["Satisfaction globale"].iloc[-1]
            evolution = last_sat - first_sat
            insight_card("Évolution globale", f"{evolution:+.1f} pts", "Première vs dernière année", USJ_GREEN if evolution >= 0 else USJ_RED)
        else:
            insight_card("Évolution globale", "NA", "Sélectionnez plusieurs années", "#777777")

    with c4:
        latest_rec = year_summary_filtered.loc[year_summary_filtered["Année"] == latest_year, "Taux de recommandation"].iloc[0]
        insight_card("Dernière recommandation", safe_pct(latest_rec), latest_year, kpi_color_percentage(latest_rec))

    st.markdown("<br>", unsafe_allow_html=True)

    # Main trend chart
    trend_cols = ["Satisfaction globale", "Taux de recommandation"]
    trend = year_summary_filtered[["Année"] + trend_cols].melt(
        id_vars="Année",
        var_name="Indicateur",
        value_name="Pourcentage"
    )

    fig_trend = px.line(
        trend,
        x="Année",
        y="Pourcentage",
        color="Indicateur",
        markers=True,
        text="Pourcentage",
        color_discrete_sequence=[USJ_BLUE, "#7BC4FF"]
    )
    fig_trend.update_traces(texttemplate="%{text:.1f}%", textposition="top center", mode="lines+markers+text")
    fig_trend.update_layout(
        title="Évolution de la satisfaction globale et de la recommandation",
        yaxis_title="Pourcentage",
        xaxis_title="Année"
    )
    theme_layout(fig_trend, height=450)
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

    # Component heatmap
    heatmap_data = component_long_filtered.copy()
    if not heatmap_data.empty:
        heatmap_pivot = heatmap_data.pivot_table(
            index="Dimension",
            columns="Année",
            values="Pourcentage",
            aggfunc="mean"
        )

        fig_heat = px.imshow(
            heatmap_pivot,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale=PLOTLY_CONT,
            zmin=70,
            zmax=85,
            title="Carte thermique des dimensions par année"
        )
        fig_heat.update_traces(textfont=dict(size=13, family="Candara, Arial"), hovertemplate="Dimension=%{y}<br>Année=%{x}<br>Résultat=%{z:.1f}%<extra></extra>")
        fig_heat.update_layout(
            xaxis_title="Année",
            yaxis_title="Dimension",
            coloraxis_colorbar=dict(title="%")
        )
        theme_layout(fig_heat, height=540, showlegend=False)
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

        latest_hm_year = heatmap_pivot.columns[-1]
        latest_hm = heatmap_pivot[latest_hm_year].dropna().sort_values(ascending=False)
        if not latest_hm.empty:
            summary_box(
                f"""
                <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture de la carte thermique</span><br>
                En <b>{latest_hm_year}</b>, la dimension la mieux positionnée est
                <b>{latest_hm.index[0]}</b> avec <b>{latest_hm.iloc[0]:.1f}%</b>, tandis que la dimension
                la plus fragile est <b>{latest_hm.index[-1]}</b> avec <b>{latest_hm.iloc[-1]:.1f}%</b>.
                Les couleurs permettent de repérer rapidement les zones de performance élevée et les zones
                où un suivi institutionnel plus ciblé est recommandé.
                """,
                color=USJ_BLUE,
                background="#F7F9FC"
            )

        # Year-over-year changes
        diff_df = heatmap_pivot.copy()
        if diff_df.shape[1] >= 2:
            first_year = diff_df.columns[0]
            last_year = diff_df.columns[-1]
            diff_df["Évolution"] = diff_df[last_year] - diff_df[first_year]
            diff_plot = diff_df["Évolution"].reset_index().sort_values("Évolution")

            diff_plot["Libellé"] = diff_plot["Évolution"].apply(lambda x: f"{x:+.2f} pts")
            diff_plot["Sens"] = np.where(diff_plot["Évolution"] >= 0, "Progression", "Baisse")

            fig_diff = go.Figure()
            for sens, color in [("Baisse", USJ_RED), ("Progression", USJ_GREEN)]:
                sub = diff_plot[diff_plot["Sens"] == sens]
                if not sub.empty:
                    fig_diff.add_trace(
                        go.Bar(
                            x=sub["Évolution"],
                            y=sub["Dimension"],
                            orientation="h",
                            name=sens,
                            marker=dict(color=color, line=dict(color="white", width=1.2)),
                            text=sub["Libellé"],
                            textposition="outside",
                            cliponaxis=False,
                            hovertemplate="<b>%{y}</b><br>Évolution: %{x:+.2f} pts<extra></extra>",
                        )
                    )

            max_abs = max(1, float(np.nanmax(np.abs(diff_plot["Évolution"]))))
            fig_diff.add_vline(x=0, line_width=1.5, line_color="#8A94A6")
            fig_diff.update_layout(
                title=f"Évolution des dimensions entre {first_year} et {last_year}",
                xaxis_title="Évolution en points de pourcentage",
                yaxis_title="",
                xaxis=dict(range=[-max_abs - 1.2, max_abs + 1.2], zeroline=False),
                bargap=0.28,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            theme_layout(fig_diff, height=540, showlegend=True)
            st.plotly_chart(fig_diff, use_container_width=True, config={"displayModeBar": True})

            best_gain = diff_plot.sort_values("Évolution", ascending=False).iloc[0]
            largest_decline = diff_plot.sort_values("Évolution", ascending=True).iloc[0]
            summary_box(
                f"""
                <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture comparative</span><br>
                Entre <b>{first_year}</b> et <b>{last_year}</b>, la plus forte progression concerne
                <b>{best_gain["Dimension"]}</b> avec <b>{best_gain["Évolution"]:+.1f} points</b>.
                La dimension la plus en recul est <b>{largest_decline["Dimension"]}</b> avec
                <b>{largest_decline["Évolution"]:+.1f} points</b>. Ces écarts permettent d’identifier
                les domaines où les actions semblent produire une amélioration et ceux qui nécessitent
                une attention prioritaire.
                """,
                color=USJ_BLUE,
                background="#F7F9FC"
            )

    # Statistical tests table
    st.markdown(f"<h3 style='color:{USJ_BLUE};'>Tests statistiques de comparaison entre années</h3>", unsafe_allow_html=True)

    stat_rows = []
    for col in SCORE_COLUMNS:
        if col in df_filtered.columns:
            p_value, test_name = anova_or_kruskal(df_filtered, col)
            stat_rows.append({
                "Indicateur": SCORE_LABELS[col],
                "p-value": round(p_value, 3) if pd.notna(p_value) else np.nan,
                "Interprétation": p_interpretation(p_value)
            })

    p_rec = chi_square_recommendation(df_filtered, q43)
    stat_rows.append({
        "Indicateur": "Taux de recommandation",
        "p-value": round(p_rec, 3) if pd.notna(p_rec) else np.nan,
        "Interprétation": p_interpretation(p_rec)
    })

    stat_df = pd.DataFrame(stat_rows)
    stat_df["p-value"] = stat_df["p-value"].apply(lambda x: "" if pd.isna(x) else f"{float(x):.3f}")

    def style_pvalue_table(row):
        interpretation = str(row.get("Interprétation", ""))
        if "hautement" in interpretation:
            color = USJ_GREEN
            bg = "#E8F5E9"
        elif ("très" in interpretation) or ("significative" in interpretation and "non" not in interpretation):
            color = USJ_BLUE
            bg = "#EAF2FF"
        else:
            color = "#5F6B7A"
            bg = "#F2F4F7"
        return ["", "", f"background-color:{bg}; color:{color}; font-weight:700;"]

    st.dataframe(
        stat_df.style.apply(style_pvalue_table, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # Table details
    display_table = year_summary_filtered.copy()
    for col in display_table.columns:
        if col not in ["Année", "N"]:
            display_table[col] = display_table[col].map(lambda x: "" if pd.isna(x) else f"{x:.1f}%")
    st.markdown(f"<h3 style='color:{USJ_BLUE};'>Tableau comparatif par année</h3>", unsafe_allow_html=True)
    st.dataframe(display_table, use_container_width=True, hide_index=True)

    # Faculty heatmap
    if faculte == "Tous" and "Faculté_Institut_g" in df_filtered.columns:
        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Comparaison par faculté et par année</h3>", unsafe_allow_html=True)

        fac_year = (
            df_filtered
            .groupby(["Faculté_Institut_g", "Year"])["Score satisfaction globale"]
            .mean()
            .reset_index()
        )
        fac_year["Satisfaction globale (%)"] = fac_year["Score satisfaction globale"].apply(pct_from_mean)

        fac_pivot = fac_year.pivot_table(
            index="Faculté_Institut_g",
            columns="Year",
            values="Satisfaction globale (%)",
            aggfunc="mean"
        )

        fig_fac = px.imshow(
            fac_pivot,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale=PLOTLY_CONT,
            zmin=65,
            zmax=100,
            title="Satisfaction globale par faculté et par année"
        )
        fig_fac.update_traces(textfont=dict(size=12, family="Candara, Arial"), hovertemplate="Faculté=%{y}<br>Année=%{x}<br>Satisfaction=%{z:.1f}%<extra></extra>")
        fig_fac.update_layout(xaxis_title="Année", yaxis_title="Faculté", coloraxis_colorbar=dict(title="%"))
        theme_layout(fig_fac, height=max(520, 26 * len(fac_pivot)), showlegend=False)
        st.plotly_chart(fig_fac, use_container_width=True, config={"displayModeBar": False})


# =====================================================
# Page 3 - Variable importance
# =====================================================

def page_importance():
    section_header(
        "Facteurs clés d’amélioration",
        "Modèles explicatifs pour identifier les dimensions qui influencent le plus la satisfaction globale et la recommandation."
    )

    summary_box(
        """
        Cette section étudie l’impact des principales dimensions de l’expérience étudiante sur deux variables dépendantes :
        <b>la satisfaction globale à l’Université</b> et <b>la recommandation de l’USJ</b>.
        L’objectif est d’identifier les leviers les plus utiles pour guider les décisions d’amélioration.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    feature_columns = [
        "Score enseignement et apprentissage",
        "Score accompagnement et encadrement",
        "Score développement des compétences",
        "Score services USJ",
        "Score vie étudiante et activités",
        "Score infrastructures et équipements",
        "Score frais / qualité enseignement",
        "Score frais / autres universités"
    ]

    feature_columns = [col for col in feature_columns if col in df_filtered.columns]
    display_names = {col: clean_component_name(col) for col in feature_columns}

    st.markdown(f"<h3 style='color:{USJ_BLUE};'>1. Impact sur la satisfaction globale</h3>", unsafe_allow_html=True)

    model_sat = df_filtered[feature_columns + ["Score satisfaction globale"]].dropna()

    if len(model_sat) < 30:
        st.warning("Pas assez de données valides pour analyser la satisfaction globale.")
    else:
        importances = train_satisfaction_importance(model_sat, feature_columns)

        importance_sat = pd.DataFrame({
            "Dimension": [display_names[col] for col in feature_columns],
            "Importance": importances
        })

        importance_sat["Importance (%)"] = (
            importance_sat["Importance"] / importance_sat["Importance"].sum() * 100
        ).round(1)

        importance_sat = importance_sat.sort_values("Importance (%)", ascending=False)
        top_sat = importance_sat.iloc[0]
        second_sat = importance_sat.iloc[1] if len(importance_sat) > 1 else top_sat

        c1, c2, c3 = st.columns(3)

        with c1:
            importance_card("Principal levier", top_sat["Importance (%)"], top_sat["Dimension"])

        with c2:
            importance_card("Base d’analyse", len(model_sat) / len(df_filtered) * 100, f"{len(model_sat)} répondants valides")

        with c3:
            importance_card("Dimensions analysées", len(feature_columns) / 8 * 100, f"{len(feature_columns)} dimensions")

        fig_sat = px.bar(
            importance_sat,
            x="Importance (%)",
            y="Dimension",
            orientation="h",
            text="Importance (%)",
            color="Importance (%)",
            color_continuous_scale=PLOTLY_CONT,
            title="Importance relative des dimensions dans la satisfaction globale"
        )

        fig_sat.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_sat.update_layout(xaxis_title="Importance relative (%)", yaxis_title="")
        theme_layout(fig_sat, height=500, showlegend=False)
        st.plotly_chart(fig_sat, use_container_width=True, config={"displayModeBar": False})

        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_ORANGE};">Interprétation décisionnelle</span><br>
            La dimension <b>{top_sat["Dimension"]}</b> est le facteur le plus déterminant
            pour expliquer la satisfaction globale, avec une importance relative de
            <b>{top_sat["Importance (%)"]:.1f}%</b>. La deuxième dimension la plus importante est
            <b>{second_sat["Dimension"]}</b>. Ces résultats indiquent que les efforts d’amélioration
            devraient prioritairement cibler ces dimensions.
            """,
            color=USJ_ORANGE,
            background="#FFF8F0"
        )

    st.divider()

    st.markdown(f"<h3 style='color:{USJ_BLUE};'>2. Impact sur la recommandation de l’USJ</h3>", unsafe_allow_html=True)

    model_rec = df_filtered[feature_columns + [q43]].copy()
    model_rec[q43] = model_rec[q43].astype(str).str.strip()
    model_rec = model_rec[model_rec[q43].isin(["Oui", "Non"])]
    model_rec["Recommandation"] = model_rec[q43].map({"Oui": 1, "Non": 0})
    model_rec = model_rec[feature_columns + ["Recommandation"]].dropna()

    if len(model_rec) < 30 or model_rec["Recommandation"].nunique() < 2:
        st.warning("Pas assez de données valides pour analyser la recommandation.")
    else:
        importances = train_recommendation_importance(model_rec, feature_columns)

        importance_rec = pd.DataFrame({
            "Dimension": [display_names[col] for col in feature_columns],
            "Importance": importances
        })

        importance_rec["Importance (%)"] = (
            importance_rec["Importance"] / importance_rec["Importance"].sum() * 100
        ).round(1)

        importance_rec = importance_rec.sort_values("Importance (%)", ascending=False)
        top_rec = importance_rec.iloc[0]
        second_rec = importance_rec.iloc[1] if len(importance_rec) > 1 else top_rec

        c1, c2, c3 = st.columns(3)

        with c1:
            importance_card("Principal levier", top_rec["Importance (%)"], top_rec["Dimension"])

        with c2:
            importance_card("Taux de recommandation", calculate_recommendation_rate(df_filtered, q43), "Réponses Oui")

        with c3:
            importance_card("Base d’analyse", len(model_rec) / len(df_filtered) * 100, f"{len(model_rec)} répondants valides")

        fig_rec = px.bar(
            importance_rec,
            x="Importance (%)",
            y="Dimension",
            orientation="h",
            text="Importance (%)",
            color="Importance (%)",
            color_continuous_scale=PLOTLY_CONT,
            title="Importance relative des dimensions dans la recommandation de l’USJ"
        )

        fig_rec.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_rec.update_layout(xaxis_title="Importance relative (%)", yaxis_title="")
        theme_layout(fig_rec, height=500, showlegend=False)
        st.plotly_chart(fig_rec, use_container_width=True, config={"displayModeBar": False})

        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_GREEN};">Interprétation décisionnelle</span><br>
            La dimension <b>{top_rec["Dimension"]}</b> est le facteur le plus déterminant
            pour expliquer la recommandation de l’USJ, avec une importance relative de
            <b>{top_rec["Importance (%)"]:.1f}%</b>. La deuxième dimension la plus importante est
            <b>{second_rec["Dimension"]}</b>. Cette lecture permet d’identifier les leviers qui
            peuvent renforcer l’image positive de l’Université.
            """,
            color=USJ_GREEN,
            background="#F3FAF5"
        )


# =====================================================
# Page 4 - Descriptive results by section
# =====================================================

def page_descriptive_sections():
    section_header(
        "Résultats descriptifs par section",
        "Analyse détaillée des questions par section, avec évolution, distributions et corrélations internes."
    )

    available_sections = [sec for sec, items in components.items() if len(items) > 0]

    if not available_sections:
        st.warning("Aucune section disponible.")
        return

    selected_section = st.selectbox("Choisir une section", available_sections)
    items = components[selected_section]

    if len(items) == 0:
        st.warning("Aucune question disponible pour cette section.")
        return

    section_score = None
    for col in SCORE_COLUMNS:
        if SCORE_LABELS.get(col, "") == selected_section or selected_section.lower() in SCORE_LABELS.get(col, "").lower():
            section_score = col
            break

    question_summary = section_question_summary(df_filtered, items)

    if question_summary.empty:
        st.warning("Aucun résultat disponible pour cette section.")
        return

    top_q = question_summary.iloc[0]
    weak_q = question_summary.iloc[-1]

    c1, c2, c3 = st.columns(3)

    with c1:
        insight_card("Nombre de questions", len(items), selected_section, USJ_BLUE)

    with c2:
        insight_card("Question la mieux évaluée", safe_pct(top_q["Résultat (%)"]), plain_question_label(top_q["Question"]), USJ_GREEN)

    with c3:
        insight_card("Question la plus faible", safe_pct(weak_q["Résultat (%)"]), plain_question_label(weak_q["Question"]), USJ_RED if weak_q["Résultat (%)"] < 50 else USJ_ORANGE)

    summary_box(
        f"""
        <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture de la section</span><br>
        Dans la section <b>{selected_section}</b>, la question la mieux évaluée est
        <b>{score_question_label(top_q["Question"])}</b> avec <b>{top_q["Résultat (%)"]:.1f}%</b>.
        La question la moins bien évaluée est <b>{score_question_label(weak_q["Question"])}</b>
        avec <b>{weak_q["Résultat (%)"]:.1f}%</b>. Cette lecture permet d’identifier les points forts
        et les aspects à prioriser au sein de la même section.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    # Ranking bar chart
    fig_rank = px.bar(
        question_summary.sort_values("Résultat (%)"),
        x="Résultat (%)",
        y="Libellé affiché",
        orientation="h",
        text="Résultat (%)",
        color="Résultat (%)",
        color_continuous_scale=PLOTLY_CONT,
        hover_data={"Question": True, "Moyenne /4": ":.2f", "N valide": True, "Taux de données manquantes (%)": ":.1f"}
    )
    fig_rank.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_rank.update_layout(
        title=f"Classement des questions – {selected_section}",
        xaxis_title="Résultat (%)",
        yaxis_title="Question"
    )
    theme_layout(fig_rank, height=max(440, 45 * len(question_summary)), showlegend=False)
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})

    # Table
    display_q = question_summary.copy()
    display_q["Résultat (%)"] = display_q["Résultat (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
    display_q["Moyenne /4"] = display_q["Moyenne /4"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    display_q["Taux de données manquantes (%)"] = display_q["Taux de données manquantes (%)"].map(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
    st.dataframe(
        display_q[["Libellé question", "Résultat (%)", "Moyenne /4", "N valide", "Taux de données manquantes (%)"]].rename(columns={"Libellé question": "Question"}),
        use_container_width=True,
        hide_index=True
    )

    # Evolution by year
    trend_q = section_trend(df_filtered, items)
    if not trend_q.empty and trend_q["Année"].nunique() > 1:
        all_questions = list(dict.fromkeys(trend_q["Question complète"].tolist()))
        default_questions = all_questions[: min(4, len(all_questions))]
        selected_questions = st.multiselect(
            "Questions à afficher dans le graphique d’évolution",
            options=all_questions,
            default=default_questions,
            help="Sélectionnez quelques questions pour garder un graphique lisible et interactif."
        )

        trend_selected = trend_q[trend_q["Question complète"].isin(selected_questions)].copy()
        if trend_selected.empty:
            st.info("Sélectionnez au moins une question pour afficher l’évolution.")
        else:
            trend_selected["Libellé valeur"] = trend_selected["Résultat (%)"].apply(lambda x: "" if pd.isna(x) else f"{x:.2f}%")
            fig_q_trend = px.line(
                trend_selected,
                x="Année",
                y="Résultat (%)",
                color="Question complète",
                markers=True,
                text="Libellé valeur",
                color_discrete_sequence=PLOTLY_SEQ,
                hover_data={"Question": False, "Question complète": True, "Résultat (%)": ":.2f"}
            )
            fig_q_trend.update_traces(
                textposition="top center",
                mode="lines+markers+text",
                line=dict(width=3),
                marker=dict(size=9, line=dict(width=1, color="white")),
                hovertemplate="<b>%{fullData.name}</b><br>Année: %{x}<br>Résultat: %{y:.2f}%<extra></extra>"
            )
            y_min = max(0, float(trend_selected["Résultat (%)"].min()) - 5)
            y_max = min(100, float(trend_selected["Résultat (%)"].max()) + 5)
            fig_q_trend.update_layout(
                title=f"Évolution des questions – {selected_section}",
                xaxis_title="Année",
                yaxis_title="Résultat (%)",
                legend_title="Question",
                hovermode="x unified"
            )
            fig_q_trend.update_yaxes(range=[y_min, y_max])
            theme_layout(fig_q_trend, height=650, showlegend=True)
            fig_q_trend.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="left", x=0, font=dict(size=11)),
                margin=dict(l=40, r=30, t=80, b=170),
                hovermode="x unified"
            )
            st.plotly_chart(fig_q_trend, use_container_width=True, config={"displayModeBar": True})

            trend_change = trend_selected.sort_values("Année").groupby("Question complète").agg(
                Début=("Résultat (%)", "first"),
                Fin=("Résultat (%)", "last")
            ).reset_index()
            trend_change["Évolution"] = trend_change["Fin"] - trend_change["Début"]
            best_trend = trend_change.sort_values("Évolution", ascending=False).iloc[0]
            summary_box(
                f"""
                <span style=\"font-size:20px; font-weight:800; color:{USJ_BLUE};\">Lecture de l’évolution des questions</span><br>
                Parmi les questions affichées, la progression la plus favorable concerne
                <b>{best_trend["Question complète"]}</b>, avec une variation de
                <b>{best_trend["Évolution"]:+.2f} points</b> entre la première et la dernière année visibles.
                Le sélecteur permet de comparer uniquement les questions pertinentes et d’éviter une légende trop chargée.
                """,
                color=USJ_BLUE,
                background="#F7F9FC"
            )

    # Distribution
    dist = response_distribution(df_original.loc[df_filtered.index], df_filtered, items)
    if not dist.empty:
        selected_question_short = st.selectbox(
            "Choisir une question pour afficher la distribution des réponses",
            sorted(dist["Question"].unique())
        )

        dist_q = dist[dist["Question"] == selected_question_short]

        fig_dist = px.bar(
            dist_q,
            x="Année",
            y="Pourcentage",
            color="Réponse",
            text="Pourcentage",
            barmode="stack",
            color_discrete_map=RESPONSE_COLORS,
            hover_data={"Question complète": True, "N": True}
        )
        fig_dist.update_traces(texttemplate="%{text:.2f}%", textposition="inside", hovertemplate="Réponse: %{fullData.name}<br>Année: %{x}<br>Pourcentage: %{y:.2f}%<extra></extra>")
        fig_dist.update_layout(
            title=f"Distribution des réponses – {selected_question_short}",
            xaxis_title="Année",
            yaxis_title="Pourcentage des réponses"
        )
        theme_layout(fig_dist, height=500)
        st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})

    # Correlation matrix
    corr, ranking = correlation_with_section_mean(df_filtered, items)

    if not corr.empty:
        labels = [question_display_label(c, width=34) if c != "Moyenne de la section" else c for c in corr.columns]
        corr_display = corr.copy()
        corr_display.index = labels
        corr_display.columns = labels

        fig_corr = px.imshow(
            corr_display,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=PLOTLY_DIVERGING,
            zmin=-1,
            zmax=1,
            title=f"Heatmap de corrélation – {selected_section}"
        )
        fig_corr.update_layout(
            xaxis_title="Questions",
            yaxis_title="Questions",
            coloraxis_colorbar=dict(title="Corrélation")
        )
        theme_layout(fig_corr, height=max(520, 35 * len(corr_display)), showlegend=False)
        st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})

        fig_corr_rank = px.bar(
            ranking.sort_values("Corrélation avec la moyenne"),
            x="Corrélation avec la moyenne",
            y="Question affichée",
            orientation="h",
            text="Corrélation avec la moyenne",
            color="Corrélation avec la moyenne",
            color_continuous_scale=PLOTLY_CONT,
            hover_data={"Question": True}
        )
        fig_corr_rank.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_corr_rank.update_layout(
            title="Questions les plus liées à la moyenne de la section",
            xaxis_title="Corrélation avec la moyenne de section",
            yaxis_title="Question"
        )
        theme_layout(fig_corr_rank, height=max(420, 42 * len(ranking)), showlegend=False)
        st.plotly_chart(fig_corr_rank, use_container_width=True, config={"displayModeBar": False})

        top_corr = ranking.iloc[0]
        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_GREEN};">Lecture corrélationnelle</span><br>
            La question la plus fortement associée à la moyenne de la section est
            <b>{score_question_label(top_corr["Question"])}</b>, avec une corrélation de
            <b>{top_corr["Corrélation avec la moyenne"]:.2f}</b>. Cette question peut être considérée
            comme particulièrement représentative de la dimension analysée.
            """,
            color=USJ_GREEN,
            background="#F3FAF5"
        )



# =====================================================
# Page 5 - Inferential statistics by demographic variables
# =====================================================

def clean_question_name(question):
    """Return the full question wording without the leading code."""
    q = str(question).strip()
    if "-" in q:
        return q.split("-", 1)[1].strip()
    return q


def wrap_plot_label(text, width=46):
    text = str(text)
    return "<br>".join(textwrap.wrap(text, width=width))


def format_p_value(p):
    if pd.isna(p):
        return "NA"
    return f"{p:.3f}"


def effect_size_label(value, test_name):
    if pd.isna(value):
        return "NA"
    if test_name == "Welch t-test":
        return f"d = {value:.2f}"
    return f"η² = {value:.2f}"


def inferential_test(data, group_col, value_col):
    temp = data[[group_col, value_col]].copy()
    temp[group_col] = temp[group_col].astype(str).str.strip()
    temp = temp.replace({"nan": np.nan, "None": np.nan, "": np.nan})
    temp[value_col] = pd.to_numeric(temp[value_col], errors="coerce")
    temp = temp.dropna(subset=[group_col, value_col])

    group_values = [g[value_col].values for _, g in temp.groupby(group_col) if g[value_col].notna().sum() >= 2]
    group_names = [name for name, g in temp.groupby(group_col) if g[value_col].notna().sum() >= 2]

    if len(group_values) < 2 or stats is None:
        return {
            "Test": "Non calculable",
            "p-value": np.nan,
            "Effet": np.nan,
            "Groupes valides": len(group_values),
            "N valide": len(temp),
        }

    try:
        if len(group_values) == 2:
            _, p = stats.ttest_ind(group_values[0], group_values[1], equal_var=False, nan_policy="omit")
            n1, n2 = len(group_values[0]), len(group_values[1])
            s1, s2 = np.nanstd(group_values[0], ddof=1), np.nanstd(group_values[1], ddof=1)
            pooled_sd = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / max(n1 + n2 - 2, 1))
            effect = (np.nanmean(group_values[0]) - np.nanmean(group_values[1])) / pooled_sd if pooled_sd > 0 else np.nan
            test_name = "Welch t-test"
        else:
            _, p = stats.f_oneway(*group_values)
            grand_mean = temp[value_col].mean()
            ss_between = sum(len(vals) * (np.nanmean(vals) - grand_mean) ** 2 for vals in group_values)
            ss_total = sum((temp[value_col] - grand_mean) ** 2)
            effect = ss_between / ss_total if ss_total > 0 else np.nan
            test_name = "ANOVA"
    except Exception:
        p = np.nan
        effect = np.nan
        test_name = "Non calculable"

    return {
        "Test": test_name,
        "p-value": p,
        "Effet": effect,
        "Groupes valides": len(group_values),
        "N valide": len(temp),
    }


def significance_badge(p):
    if pd.isna(p):
        return "Non calculable"
    if p < 0.001:
        return "Différence hautement significative"
    if p < 0.01:
        return "Différence très significative"
    if p < 0.05:
        return "Différence significative"
    return "Différence non significative"


def build_group_mean_table(data, group_col, variables_dict):
    rows = []
    for var_col, label in variables_dict.items():
        if var_col not in data.columns:
            continue
        temp = data[[group_col, var_col]].copy()
        temp[group_col] = temp[group_col].astype(str).str.strip()
        temp = temp.replace({"nan": np.nan, "None": np.nan, "": np.nan})
        temp[var_col] = pd.to_numeric(temp[var_col], errors="coerce")
        temp = temp.dropna(subset=[group_col, var_col])
        for group_name, g in temp.groupby(group_col):
            rows.append({
                "Variable": label,
                "Variable courte": wrap_plot_label(label, 42),
                "Groupe": group_name,
                "Moyenne (%)": pct_from_mean(g[var_col].mean()),
                "Écart-type (%)": g[var_col].std() / 4 * 100 if pd.notna(g[var_col].std()) else np.nan,
                "N": len(g),
            })
    return pd.DataFrame(rows)


def build_inferential_results(data, group_col, variables_dict):
    rows = []
    for var_col, label in variables_dict.items():
        if var_col not in data.columns:
            continue
        res = inferential_test(data, group_col, var_col)
        rows.append({
            "Indicateur": label,
            "Test": res["Test"],
            "p-value": format_p_value(res["p-value"]),
            "Taille d’effet": effect_size_label(res["Effet"], res["Test"]),
            "N valide": res["N valide"],
            "Groupes valides": res["Groupes valides"],
            "Interprétation": significance_badge(res["p-value"]),
            "p_numeric": res["p-value"],
        })
    return pd.DataFrame(rows)


def page_inferential_statistics():
    section_header(
        "Statistiques inférentielles par variables démographiques",
        "Comparaison des moyennes des dimensions et des questions selon le genre, la faculté, le niveau et la langue de démarrage."
    )

    summary_box(
        f"""
        Cette section permet de tester si les résultats moyens diffèrent significativement entre les groupes démographiques.
        Les moyennes sont présentées en pourcentage afin de rester cohérentes avec les autres pages du tableau de bord.
        Pour deux groupes, le tableau utilise un <b>Welch t-test</b>. Pour trois groupes ou plus, il utilise une <b>ANOVA</b>. Les comparaisons couvrent aussi la <b>Langue de démarrage</b> lorsque cette colonne existe dans le fichier.
        Une p-value inférieure à <b>0.050</b> indique une différence statistiquement significative entre les groupes comparés.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    # Variables requested for inferential comparisons.
    # The language variable can have different names depending on the Excel export,
    # so the code detects the available column automatically.
    demographic_candidates = {
        "Genre": "Genre",
        "Faculté_Institut_g": "Faculté / Institut",
        "Niveau_Lib": "Niveau",
        "startlanguage": "Langue de démarrage",
        "StartLanguage": "Langue de démarrage",
        "start_language": "Langue de démarrage",
        "Langue": "Langue de démarrage",
        "Language": "Langue de démarrage",
    }

    available_demo = {}
    for col, label in demographic_candidates.items():
        if col in df_filtered.columns:
            # Avoid displaying duplicated language entries if several aliases exist.
            if label == "Langue de démarrage" and "Langue de démarrage" in available_demo.values():
                continue
            available_demo[col] = label

    if "Niveau_Lib" not in available_demo and "Niveau" in df_filtered.columns:
        available_demo["Niveau"] = "Niveau"

    if not available_demo:
        st.warning("Aucune des variables démographiques demandées n’est disponible dans le fichier filtré.")
        return

    controls = st.columns([1.4, 1.2, 1.8])
    with controls[0]:
        selected_demo = st.selectbox(
            "Variable démographique",
            list(available_demo.keys()),
            format_func=lambda x: available_demo[x]
        )
    with controls[1]:
        analysis_level = st.selectbox(
            "Niveau d’analyse",
            ["Moyennes des sections", "Questions d’une section"]
        )
    with controls[2]:
        selected_section_inf = None
        if analysis_level == "Questions d’une section":
            available_sections = [sec for sec, items in components.items() if len(items) > 0]
            selected_section_inf = st.selectbox("Section à comparer", available_sections)

    if analysis_level == "Moyennes des sections":
        variables_dict = {
            col: SCORE_LABELS[col]
            for col in SCORE_COLUMNS
            if col in df_filtered.columns and df_filtered[col].notna().sum() > 0
        }
        title_suffix = "les dimensions"
    else:
        items = [item for item in components.get(selected_section_inf, []) if item in df_filtered.columns]
        variables_dict = {item: clean_question_name(item) for item in items}
        title_suffix = f"les questions de la section {selected_section_inf}"

    if not variables_dict:
        st.warning("Aucune variable numérique disponible pour cette comparaison.")
        return

    mean_table = build_group_mean_table(df_filtered, selected_demo, variables_dict)
    inferential_df = build_inferential_results(df_filtered, selected_demo, variables_dict)

    if mean_table.empty:
        st.warning("Aucune donnée valide disponible après application des filtres.")
        return

    group_count = mean_table["Groupe"].nunique()
    variable_count = mean_table["Variable"].nunique()
    significant_count = inferential_df["p_numeric"].lt(0.05).sum() if "p_numeric" in inferential_df.columns else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        insight_card("Groupes comparés", group_count, available_demo[selected_demo], USJ_BLUE)
    with c2:
        insight_card("Indicateurs analysés", variable_count, title_suffix, USJ_BLUE_2)
    with c3:
        insight_card("Différences significatives", significant_count, "p-value < 0.050", USJ_GREEN if significant_count > 0 else "#777777")

    tab_heat, tab_detail, tab_tests = st.tabs([
        "Vue comparative interactive",
        "Comparaison détaillée",
        "Tests statistiques"
    ])

    with tab_heat:
        pivot = mean_table.pivot_table(index="Variable", columns="Groupe", values="Moyenne (%)", aggfunc="mean")
        pivot = pivot.loc[[variables_dict[col] for col in variables_dict.keys() if variables_dict[col] in pivot.index]]
        wrapped_index = [wrap_plot_label(x, 44) for x in pivot.index]
        pivot_display = pivot.copy()
        pivot_display.index = wrapped_index

        fig_heat = px.imshow(
            pivot_display,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale=PLOTLY_CONT,
            zmin=max(0, np.nanmin(pivot.values) - 5) if np.isfinite(np.nanmin(pivot.values)) else None,
            zmax=min(100, np.nanmax(pivot.values) + 5) if np.isfinite(np.nanmax(pivot.values)) else None,
            title=f"Carte comparative des moyennes par {available_demo[selected_demo]}"
        )
        fig_heat.update_layout(
            xaxis_title=available_demo[selected_demo],
            yaxis_title="Indicateur",
            coloraxis_colorbar=dict(title="Moyenne (%)"),
            hoverlabel=dict(bgcolor="white", font_size=13, font_family="Candara")
        )
        theme_layout(fig_heat, height=max(520, 46 * len(pivot_display)), showlegend=False)
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

        best_row = mean_table.sort_values("Moyenne (%)", ascending=False).iloc[0]
        weak_row = mean_table.sort_values("Moyenne (%)", ascending=True).iloc[0]
        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture comparative</span><br>
            Le résultat moyen le plus élevé est observé pour <b>{best_row['Variable']}</b> dans le groupe
            <b>{best_row['Groupe']}</b>, avec <b>{best_row['Moyenne (%)']:.2f}%</b>.
            Le résultat moyen le plus faible est observé pour <b>{weak_row['Variable']}</b> dans le groupe
            <b>{weak_row['Groupe']}</b>, avec <b>{weak_row['Moyenne (%)']:.2f}%</b>.
            Cette lecture permet de repérer les écarts les plus visibles avant l’interprétation statistique.
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )

    with tab_detail:
        selected_variable_label = st.selectbox(
            "Indicateur à explorer",
            list(variables_dict.values())
        )
        detail = mean_table[mean_table["Variable"] == selected_variable_label].sort_values("Moyenne (%)", ascending=False)

        fig_bar = px.bar(
            detail,
            x="Groupe",
            y="Moyenne (%)",
            text="Moyenne (%)",
            error_y="Écart-type (%)",
            color="Moyenne (%)",
            color_continuous_scale=PLOTLY_CONT,
            hover_data={"N": True, "Écart-type (%)": ":.2f"},
            title=f"Comparaison de l’indicateur : {selected_variable_label}"
        )
        fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside", marker_line_color="white", marker_line_width=1.2)
        fig_bar.update_layout(
            xaxis_title=available_demo[selected_demo],
            yaxis_title="Moyenne (%)",
            yaxis=dict(range=[0, min(105, max(100, detail["Moyenne (%)"].max() + 10))])
        )
        theme_layout(fig_bar, height=520, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

        # Boxplot on the original 1-4 scale for the same indicator
        reverse_lookup = {v: k for k, v in variables_dict.items()}
        selected_col = reverse_lookup[selected_variable_label]
        box_data = df_filtered[[selected_demo, selected_col]].copy()
        box_data[selected_demo] = box_data[selected_demo].astype(str).str.strip()
        box_data = box_data.replace({"nan": np.nan, "None": np.nan, "": np.nan})
        box_data[selected_col] = pd.to_numeric(box_data[selected_col], errors="coerce")
        box_data = box_data.dropna(subset=[selected_demo, selected_col])
        box_data["Résultat (%)"] = box_data[selected_col].apply(pct_from_mean)

        fig_box = px.box(
            box_data,
            x=selected_demo,
            y="Résultat (%)",
            color=selected_demo,
            points="outliers",
            color_discrete_sequence=PLOTLY_SEQ,
            title="Distribution des réponses par groupe"
        )
        fig_box.update_layout(
            xaxis_title=available_demo[selected_demo],
            yaxis_title="Résultat (%)",
            showlegend=False
        )
        theme_layout(fig_box, height=500, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

        display_detail = detail[["Groupe", "Moyenne (%)", "Écart-type (%)", "N"]].copy()
        display_detail["Moyenne (%)"] = display_detail["Moyenne (%)"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")
        display_detail["Écart-type (%)"] = display_detail["Écart-type (%)"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        st.dataframe(display_detail, use_container_width=True, hide_index=True)

    with tab_tests:
        display_tests = inferential_df.drop(columns=["p_numeric"], errors="ignore").copy()
        st.dataframe(display_tests, use_container_width=True, hide_index=True)

        significant = inferential_df[inferential_df["p_numeric"].lt(0.05)].copy()
        if not significant.empty:
            significant = significant.sort_values("p_numeric").head(5)
            items_html = "".join(
                f"<li><b>{row['Indicateur']}</b> : p-value = <b>{row['p-value']}</b>, {row['Interprétation'].lower()}.</li>"
                for _, row in significant.iterrows()
            )
            summary_box(
                f"""
                <span style="font-size:20px; font-weight:800; color:{USJ_GREEN};">Résultats significatifs à retenir</span><br>
                Les différences statistiquement significatives les plus marquées concernent :
                <ul style="margin-top:8px; margin-bottom:0;">{items_html}</ul>
                """,
                color=USJ_GREEN,
                background="#F3FAF5"
            )
        else:
            summary_box(
                f"""
                <span style="font-size:20px; font-weight:800; color:{USJ_ORANGE};">Lecture statistique</span><br>
                Aucun indicateur ne présente une différence statistiquement significative au seuil de 0.050 pour
                la variable <b>{available_demo[selected_demo]}</b> avec les filtres actuellement appliqués.
                """,
                color=USJ_ORANGE,
                background="#FFF8F0"
            )



# =====================================================
# Page 6 - Printable synthetic faculty report
# =====================================================

def apply_current_filters_without_faculty(data):
    base = data.copy()
    if year != "Tous":
        base = base[base["Year"].astype(str) == str(year)]
    if genre != "Tous" and "Genre" in base.columns:
        base = base[base["Genre"].astype(str) == str(genre)]
    if cursus != "Tous" and "Cursus" in base.columns:
        base = base[base["Cursus"].astype(str) == str(cursus)]
    if niveau != "Tous" and "Niveau" in base.columns:
        base = base[base["Niveau"].astype(str) == str(niveau)]
    return base


def build_report_dimension_table(data):
    rows = []
    for col in SCORE_COLUMNS:
        if col in data.columns and col != "Score satisfaction globale":
            value = pct_from_mean(data[col].mean())
            if pd.notna(value):
                rows.append({"Dimension": SCORE_LABELS.get(col, col), "Résultat": value})
    return pd.DataFrame(rows).sort_values("Résultat", ascending=False)


def report_badge(value):
    if pd.isna(value):
        return "Non disponible", "#777777"
    if value < 50:
        return "Zone d’alerte", USJ_RED
    if value <= 75:
        return "Zone de consolidation", USJ_BLUE
    return "Zone de force", USJ_GREEN


def html_escape(value):
    return html_lib.escape(str(value))


def build_printable_report_html():
    report_data = df_filtered.copy()
    comparison_data = apply_current_filters_without_faculty(df_coded)

    faculty_label = faculte if faculte != "Tous" else "Ensemble de l’Université"
    period_label = year if year != "Tous" else "Toutes les années disponibles"
    report_title = f"Rapport synthétique Exit Survey - {faculty_label}"

    n_resp = len(report_data)
    sat = pct_from_mean(report_data["Score satisfaction globale"].mean()) if "Score satisfaction globale" in report_data.columns else np.nan
    rec = calculate_recommendation_rate(report_data, q43)
    exp = pct_from_mean(report_data["Score expérience globale USJ"].mean()) if "Score expérience globale USJ" in report_data.columns else np.nan

    badge_text, badge_color = report_badge(sat)
    dim_table = build_report_dimension_table(report_data)

    if not dim_table.empty:
        best = dim_table.iloc[0]
        weak = dim_table.iloc[-1]
        dim_rows_html = "".join(
            f"""
            <tr>
                <td>{html_escape(row['Dimension'])}</td>
                <td style='text-align:right; font-weight:700;'>{row['Résultat']:.2f}%</td>
            </tr>
            """
            for _, row in dim_table.iterrows()
        )
    else:
        best = {"Dimension": "Non disponible", "Résultat": np.nan}
        weak = {"Dimension": "Non disponible", "Résultat": np.nan}
        dim_rows_html = "<tr><td colspan='2'>Aucune dimension disponible.</td></tr>"

    benchmark_html = ""
    if faculte != "Tous" and "Faculté_Institut_g" in comparison_data.columns:
        usj_sat = pct_from_mean(comparison_data["Score satisfaction globale"].mean())
        usj_rec = calculate_recommendation_rate(comparison_data, q43)
        sat_gap = sat - usj_sat if pd.notna(sat) and pd.notna(usj_sat) else np.nan
        rec_gap = rec - usj_rec if pd.notna(rec) and pd.notna(usj_rec) else np.nan
        benchmark_html = f"""
        <div class='report-card'>
            <h3>Positionnement par rapport à l’ensemble USJ filtré</h3>
            <p>
                La satisfaction globale de la faculté est de <b>{safe_pct(sat)}</b>, contre <b>{safe_pct(usj_sat)}</b>
                pour l’ensemble USJ avec les mêmes filtres hors faculté, soit un écart de
                <b>{'NA' if pd.isna(sat_gap) else f'{sat_gap:+.2f} points'}</b>.
                Le taux de recommandation est de <b>{safe_pct(rec)}</b>, contre <b>{safe_pct(usj_rec)}</b>,
                soit un écart de <b>{'NA' if pd.isna(rec_gap) else f'{rec_gap:+.2f} points'}</b>.
            </p>
        </div>
        """
    else:
        benchmark_html = """
        <div class='report-card'>
            <h3>Positionnement institutionnel</h3>
            <p>
                Le rapport présente ici une lecture globale de l’Université. Pour générer un rapport propre à une faculté,
                sélectionnez une faculté dans le filtre <b>Faculté</b>, puis revenez à cette page.
            </p>
        </div>
        """

    trend_html = ""
    ys = build_year_summary(report_data, q43)
    if len(ys) >= 2 and "Satisfaction globale" in ys.columns:
        first_year = ys["Année"].iloc[0]
        last_year = ys["Année"].iloc[-1]
        first_sat = ys["Satisfaction globale"].iloc[0]
        last_sat = ys["Satisfaction globale"].iloc[-1]
        delta = last_sat - first_sat if pd.notna(first_sat) and pd.notna(last_sat) else np.nan
        trend_html = f"""
        <div class='report-card'>
            <h3>Évolution historique</h3>
            <p>
                Entre <b>{html_escape(first_year)}</b> et <b>{html_escape(last_year)}</b>, la satisfaction globale évolue de
                <b>{safe_pct(first_sat)}</b> à <b>{safe_pct(last_sat)}</b>, soit
                <b>{'NA' if pd.isna(delta) else f'{delta:+.2f} points'}</b>.
            </p>
        </div>
        """

    action_text = ""
    if not dim_table.empty:
        action_text = f"""
        <p>
            La priorité d’amélioration immédiate concerne <b>{html_escape(weak['Dimension'])}</b>, qui présente le résultat le plus faible
            (<b>{weak['Résultat']:.2f}%</b>). À l’inverse, <b>{html_escape(best['Dimension'])}</b> constitue un point fort à préserver
            et à valoriser (<b>{best['Résultat']:.2f}%</b>).
        </p>
        """

    generated_filters = f"Année : {year} | Genre : {genre} | Faculté : {faculte} | Cursus : {cursus} | Niveau : {niveau}"

    return f"""
    <html>
    <head>
    <meta charset='utf-8'>
    <style>
        body {{
            font-family: Candara, Arial, sans-serif;
            color: {USJ_TEXT};
            background: #ffffff;
            margin: 0;
            padding: 0;
        }}
        .report-container {{
            max-width: 1050px;
            margin: 0 auto;
            padding: 28px 34px;
            border: 1px solid #DDE5F0;
            border-radius: 22px;
            background: linear-gradient(180deg, #FFFFFF 0%, #F7F9FC 100%);
        }}
        .report-header {{
            border-bottom: 4px solid {USJ_BLUE};
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .report-title {{
            font-size: 31px;
            font-weight: 900;
            color: {USJ_BLUE};
            margin: 0;
        }}
        .report-subtitle {{
            font-size: 16px;
            color: #5F6B7A;
            margin-top: 7px;
        }}
        .badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 800;
            margin-top: 10px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin: 20px 0;
        }}
        .kpi-box {{
            background: #ffffff;
            border: 1px solid #DDE5F0;
            border-left: 7px solid {USJ_BLUE};
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 5px 16px rgba(0,0,0,0.06);
        }}
        .kpi-label {{
            font-size: 13px;
            font-weight: 800;
            color: #303742;
        }}
        .kpi-value {{
            font-size: 28px;
            font-weight: 900;
            color: {USJ_BLUE};
            margin-top: 6px;
        }}
        .report-card {{
            background: #ffffff;
            border: 1px solid #DDE5F0;
            border-radius: 18px;
            padding: 18px 20px;
            margin-top: 16px;
            box-shadow: 0 5px 16px rgba(0,0,0,0.05);
        }}
        .report-card h3 {{
            color: {USJ_BLUE};
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 20px;
        }}
        .report-card p {{
            font-size: 15.5px;
            line-height: 1.65;
            text-align: justify;
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14.5px;
        }}
        th {{
            background: {USJ_BLUE};
            color: white;
            text-align: left;
            padding: 10px;
        }}
        td {{
            border-bottom: 1px solid #E6ECF3;
            padding: 9px 10px;
        }}
        .print-note {{
            margin-top: 16px;
            font-size: 13px;
            color: #667085;
        }}
        @media print {{
            body {{ margin: 0; }}
            .no-print {{ display: none !important; }}
            .report-container {{ border: none; box-shadow: none; padding: 10px; }}
        }}
    </style>
    </head>
    <body>
        <div class='report-container'>
            <div class='report-header'>
                <h1 class='report-title'>{html_escape(report_title)}</h1>
                <div class='report-subtitle'>Période : {html_escape(period_label)} | {html_escape(generated_filters)}</div>
                <div class='badge'>{html_escape(badge_text)}</div>
            </div>

            <div class='kpi-grid'>
                <div class='kpi-box'><div class='kpi-label'>Répondants</div><div class='kpi-value'>{n_resp}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Satisfaction globale</div><div class='kpi-value'>{safe_pct(sat)}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Recommandation</div><div class='kpi-value'>{safe_pct(rec)}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Expérience globale</div><div class='kpi-value'>{safe_pct(exp)}</div></div>
            </div>

            <div class='report-card'>
                <h3>Synthèse exécutive</h3>
                <p>
                    Ce rapport présente une lecture synthétique des résultats de l’Exit Survey pour <b>{html_escape(faculty_label)}</b>.
                    La satisfaction globale atteint <b>{safe_pct(sat)}</b> et le taux de recommandation atteint <b>{safe_pct(rec)}</b>.
                    {action_text}
                </p>
            </div>

            {benchmark_html}
            {trend_html}

            <div class='report-card'>
                <h3>Classement des dimensions</h3>
                <table>
                    <thead><tr><th>Dimension</th><th style='text-align:right;'>Résultat</th></tr></thead>
                    <tbody>{dim_rows_html}</tbody>
                </table>
            </div>

            <div class='report-card'>
                <h3>Message de lecture</h3>
                <p>
                    Les résultats doivent être lus comme un outil d’aide à la décision. Les dimensions les plus élevées indiquent
                    des acquis à maintenir, tandis que les dimensions les plus faibles signalent des domaines où des actions ciblées
                    peuvent améliorer l’expérience étudiante. La comparaison avec les filtres sélectionnés permet d’adapter la lecture
                    à chaque faculté ou population analysée.
                </p>
            </div>

            <div class='print-note'>Université Saint-Joseph de Beyrouth - Unité Assurance Qualité / CCAD</div>
        </div>
    </body>
    </html>
    """


def page_printable_report():
    section_header(
        "Rapport synthétique imprimable",
        "Rapport court, personnalisé selon les filtres sélectionnés, destiné à être lu ou imprimé par chaque faculté."
    )

    summary_box(
        """
        Ce rapport est généré automatiquement à partir des filtres actifs en haut du tableau de bord.
        Pour obtenir un rapport propre à une faculté, sélectionnez d’abord la faculté souhaitée dans le filtre <b>Faculté</b>,
        puis revenez à cette page. Le rapport peut être imprimé depuis le navigateur ou téléchargé au format HTML.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    report_html = build_printable_report_html()

    col_print, col_download = st.columns([1, 1])
    with col_print:
        st_components.html(
            """
            <button onclick="window.print()" style="
                width:100%;
                padding:13px 18px;
                border-radius:14px;
                border:0;
                background:#001B75;
                color:white;
                font-family:Candara, Arial, sans-serif;
                font-size:16px;
                font-weight:800;
                cursor:pointer;
            ">Imprimer le rapport</button>
            """,
            height=58,
        )
    with col_download:
        faculty_part = faculte if faculte != "Tous" else "USJ"
        file_name = f"rapport_exit_survey_{str(faculty_part).replace(' ', '_')}.html"
        st.download_button(
            "Télécharger le rapport HTML",
            data=report_html.encode("utf-8"),
            file_name=file_name,
            mime="text/html",
            use_container_width=True,
        )

    st.markdown(report_html, unsafe_allow_html=True)


# =====================================================
# Page 6 - Methodology
# =====================================================

def page_methodology():
    section_header(
        "Méthodologie des composantes",
        "Mode de calcul des dimensions, recodage des réponses et fiabilité interne."
    )

    summary_box(
        """
        <b>Principe général :</b><br>
        Chaque composante est calculée comme la moyenne des items qui la constituent.
        Les réponses sont recodées sur une échelle allant de <b>1 à 4</b>, où 1 représente
        le niveau le plus faible de satisfaction ou d’accord, et 4 le niveau le plus élevé.
        Les réponses non valides ou non applicables sont exclues du calcul.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    alpha_rows = []

    for component_name, items in components.items():
        valid_items = [col for col in items if col in df_coded.columns]

        if len(valid_items) >= 2:
            alpha = cronbach_alpha(df_coded[valid_items])
        else:
            alpha = np.nan

        alpha_rows.append({
            "Composante": component_name,
            "Nombre d’items": len(valid_items),
            "Alpha de Cronbach": round(alpha, 3) if pd.notna(alpha) else np.nan,
            "Interprétation": alpha_interpretation(alpha)
        })

    alpha_df = pd.DataFrame(alpha_rows)

    st.subheader("Fiabilité interne des composantes")
    st.dataframe(alpha_df, use_container_width=True, hide_index=True)

    st.markdown(f"<h3 style='color:{USJ_BLUE};'>Détail des composantes</h3>", unsafe_allow_html=True)

    for component_name, items in components.items():
        valid_items = [col for col in items if col in df_coded.columns]

        with st.expander(component_name):
            st.markdown(
                f"""
                <b>Mode de calcul :</b> moyenne des items disponibles.<br>
                <b>Nombre d’items utilisés :</b> {len(valid_items)}
                """,
                unsafe_allow_html=True
            )

            for item in valid_items:
                st.markdown(f"- {item}")

    summary_box(
        """
        <b>Note méthodologique :</b><br>
        L’alpha de Cronbach permet d’évaluer la cohérence interne des items composant chaque dimension.
        Une valeur élevée indique que les items mesurent de manière relativement cohérente une même
        dimension latente. Toutefois, l’alpha doit être interprété avec prudence et toujours en lien avec
        la cohérence conceptuelle des items.
        """,
        color=USJ_ORANGE,
        background="#FFF8F0"
    )


# =====================================================
# Display selected page
# =====================================================

if page == "Vue générale des indicateurs":
    page_indicators()

elif page == "Comparaison historique":
    page_historical_comparison()

elif page == "Facteurs clés d’amélioration":
    page_importance()

elif page == "Résultats descriptifs par section":
    page_descriptive_sections()

elif page == "Statistiques inférentielles":
    page_inferential_statistics()

elif page == "Méthodologie des composantes":
    page_methodology()

elif page == "Rapport synthétique imprimable":
    page_printable_report()


# =====================================================
# Footer
# =====================================================

st.markdown(
    f"""
    <div style="
        margin-top:35px;
        padding:15px;
        background-color:{USJ_BLUE};
        color:white;
        border-radius:14px;
        text-align:center;
        font-size:14px;
        box-shadow:0 4px 14px rgba(0,0,0,0.08);
    ">
        Université Saint-Joseph de Beyrouth – Exit Survey 2022-2025
    </div>
    """,
    unsafe_allow_html=True
)
