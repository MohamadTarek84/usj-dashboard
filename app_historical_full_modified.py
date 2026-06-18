
import os
import re
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

# Institutional color palette based on the USJ 150 logo
USJ_BLUE = "#232B69"
USJ_BLUE_2 = "#2F3D8E"
USJ_LIGHT_BLUE = "#EEF2FF"
USJ_RED = "#C72243"
USJ_DARK_RED = "#9F1731"
USJ_GREEN = "#2E7D32"
USJ_ORANGE = "#C9852B"
USJ_GOLD = "#A99786"
USJ_GRAY = "#F7F8FC"
USJ_TEXT = "#1B2A41"

# Professional institutional palettes using the USJ logo colors
PLOTLY_SEQ = [
    USJ_BLUE,
    USJ_RED,
    USJ_GOLD,
    USJ_BLUE_2,
    "#6F7FB8",
    "#B7A897",
    "#5A638C",
    "#D35A70",
    "#8894C8",
    "#7A6A5E",
]

# Continuous scale used for satisfaction percentages.
PLOTLY_CONT = [
    [0.00, USJ_DARK_RED],
    [0.35, USJ_RED],
    [0.55, USJ_GOLD],
    [0.75, "#D8DEFF"],
    [0.90, USJ_BLUE_2],
    [1.00, USJ_BLUE],
]

PLOTLY_DIVERGING = [
    [0.00, USJ_RED],
    [0.35, "#E8CCD2"],
    [0.50, "#F7F8FC"],
    [0.70, "#D8DEFF"],
    [1.00, USJ_BLUE],
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
        background: linear-gradient(135deg, #F7F9FC 0%, #EEF4FF 100%);
        padding: 12px 14px;
        border-radius: 18px;
        border: 1px solid #D9E4F5;
        box-shadow: 0 6px 18px rgba(0, 27, 117, 0.06);
    }}

    .stRadio label {{
        font-family: Candara, Arial, sans-serif !important;
        font-size: 14px !important;
        color: {USJ_TEXT} !important;
    }}

    .stRadio div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {{
        border-color: #B9C7DE !important;
    }}

    .stSelectbox label, .stRadio > label, .stButton button {{
        font-family: Candara, Arial, sans-serif !important;
        color: {USJ_TEXT} !important;
        font-weight: 700 !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #F3F6FB !important;
        border: 1px solid #D8E2F0 !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
    }}

    div[data-baseweb="select"] span {{
        color: {USJ_TEXT} !important;
        font-family: Candara, Arial, sans-serif !important;
    }}

    div[data-baseweb="select"] input {{
        pointer-events: none !important;
        caret-color: transparent !important;
        color: transparent !important;
    }}

    button[kind="secondary"], .stButton button {{
        border-radius: 18px !important;
        border: 1px solid #C9D6EA !important;
        background: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(0, 27, 117, 0.08) !important;
        min-height: 42px !important;
    }}

    button[kind="secondary"]:hover, .stButton button:hover {{
        border-color: {USJ_BLUE} !important;
        color: {USJ_BLUE} !important;
        background: #F4F8FF !important;
    }}

    .control-panel {{
        background: linear-gradient(135deg, #FFFFFF 0%, #F7FAFF 58%, #EEF5FF 100%);
        border: 1px solid #D8E3F3;
        border-radius: 24px;
        padding: 20px 24px 16px 24px;
        margin: 12px 0 18px 0;
        box-shadow: 0 10px 28px rgba(0, 27, 117, 0.08);
    }}

    .control-title {{
        color: {USJ_BLUE};
        font-size: 22px;
        font-weight: 900;
        margin: 0 0 4px 0;
        font-family: Candara, Arial, sans-serif;
    }}

    .control-subtitle {{
        color: #5F6B7A;
        font-size: 14px;
        margin: 0 0 14px 0;
        line-height: 1.45;
        font-family: Candara, Arial, sans-serif;
    }}

    .data-chip-row {{
        display:flex;
        flex-wrap:wrap;
        gap:10px;
        margin-top:8px;
        margin-bottom:8px;
    }}

    .data-chip {{
        display:inline-flex;
        align-items:center;
        gap:7px;
        background:#FFFFFF;
        border:1px solid #D7E2F2;
        border-radius:999px;
        padding:7px 12px;
        color:{USJ_TEXT};
        font-size:13px;
        font-weight:700;
        box-shadow:0 3px 10px rgba(0,27,117,0.05);
        font-family: Candara, Arial, sans-serif;
    }}

    .data-chip strong {{
        color:{USJ_BLUE};
    }}

    .respondent-card {{
        background: linear-gradient(135deg, {USJ_BLUE} 0%, {USJ_BLUE_2} 100%);
        color:white;
        border-radius:18px;
        padding:16px 18px;
        margin-top:12px;
        margin-bottom:16px;
        box-shadow:0 8px 22px rgba(0,27,117,0.16);
        font-family: Candara, Arial, sans-serif;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .respondent-card .label {{
        font-size:14px;
        opacity:0.92;
        font-weight:700;
    }}

    .respondent-card .value {{
        font-size:28px;
        font-weight:900;
        letter-spacing:0.2px;
    }}

    .nav-title {{
        margin-top: 8px;
        margin-bottom: 6px;
        font-family: Candara, Arial, sans-serif;
        color:{USJ_BLUE};
        font-size:16px;
        font-weight:900;
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

def find_excel_file():
    possible_files = [
        "Exit_Survey_all-data.xlsx",
        "Exit_Survey_all_data.xlsx",
        "Exit_Survey_Historical_Common_Questions.xlsx",
        "Exit survey all-data.xlsx",
        "Exit survey all data.xlsx",
    ]

    for file in possible_files:
        if os.path.exists(file):
            stat = os.stat(file)
            return file, stat.st_mtime, stat.st_size

    st.error("Excel file not found. Please upload the historical file to GitHub.")
    st.write("Available files:")
    st.write(os.listdir("."))
    st.stop()


@st.cache_data(show_spinner=False)
def load_data(file_path, file_mtime, file_size):
    """
    Load the Excel file with automatic cache invalidation.

    Streamlit normally keeps cached data even after a file is modified.
    By passing the file modification time and file size as cache arguments,
    the dashboard reloads the Excel automatically whenever a new version is
    uploaded to GitHub or replaced in the app directory.
    """
    df = pd.read_excel(file_path)
    df.columns = df.columns.astype(str).str.strip()
    return df


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


def year_filter_options(data, column="Year"):
    """Year filter without Tous to avoid combined-year results in the dashboard."""
    if column not in data.columns:
        return []
    return sorted(data[column].dropna().astype(str).unique())


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
def prepare_data(file_path, file_mtime, file_size):
    df_original = normalize_year_column(load_data(file_path, file_mtime, file_size))
    df_coded = df_original.copy()

    # Correct known historical availability issue caused by the merged Excel.
    # Questions 9d_a to 9d_e did not exist in the 2022-2023 questionnaire.
    # They must therefore be blank for 2022-2023 and excluded from denominators.
    stage_impact_9d_items = [
        "9d_a- L'expérience de stage a permis d'améliorer : La capacité à travailler en équipe",
        "9d_b- L'expérience de stage a permis d'améliorer : L'appréciation des valeurs éthiques",
        "9d_c- L'expérience de stage a permis d'améliorer :Le développement professionnel",
        "9d_d- L'expérience de stage a permis d'améliorer :Les compétences en matière de gestion du temps",
        "9d_e- L'expérience de stage a permis d'améliorer :Le lien entre la théorie et la pratique",
    ]
    year_norm = df_original["Year"].astype(str).str.strip().str.replace("–", "-", regex=False).str.replace("/", "-", regex=False).str.replace("_", "-", regex=False)
    mask_2022_2023 = year_norm.eq("2022-2023")
    for col in stage_impact_9d_items:
        if col in df_original.columns:
            df_original.loc[mask_2022_2023, col] = np.nan
        if col in df_coded.columns:
            df_coded.loc[mask_2022_2023, col] = np.nan

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

OTHER_QUESTION_LABELS = {
    "3- ‎Dans votre institution (Faculté, Institut ou École), vous a-t-on assigné un tuteur ?": "3-Dans votre institution, vous a-t-on assigné un tuteur ?",
    "6- Etudié à l'étranger dans le cadre du programme d'échange ou d'une période de mobilité sortante durant votre parcours à l’USJ": "6-Avez-vous étudié à l'étranger dans le cadre d’un programme d’échange ou d’une mobilité sortante durant votre parcours à l’USJ ?",

    "7_a- Présentation du CV": "7_a-Avez-vous été formé à l’USJ à : Présentation du CV",
    "7_b- Recherche en ligne": "7_b-Avez-vous été formé à l’USJ à : Recherche d’emploi en ligne",
    "7_c- Entretien d'embauche": "7_c-Avez-vous été formé à l’USJ à : Entretien d’embauche",


    "8-Membre de la plateforme interactive de L’USJ et la Fédération des Associations des Anciens lancé pour fédérer et animer le réseau des Alumni": "8-Êtes-vous membre de la plateforme interactive de l’USJ et de la Fédération des Associations des Anciens, lancée pour fédérer et animer le réseau Alumni ?",

    "Membre de la plateforme interactive de L’USJ et la Fédération des Associations des Anciens lancé pour fédérer et animer le réseau des Alumni": "8-Êtes-vous membre de la plateforme interactive de l’USJ et de la Fédération des Associations des Anciens, lancée pour fédérer et animer le réseau Alumni ?",
    
    "9- Avez-vous réalisé un stage durant votre parcours à l’USJ ?": "9-Avez-vous réalisé un stage durant votre parcours à l’USJ ?",
    "9a- L’université vous aidé à trouver un stage": "9a-L’Université vous a-t-elle aidé à trouver un stage ?",
    "9b_a- Canaux d’accès à votre stage : Service de l’insertion professionnelle de l’USJ": "9b_a-Par quel canal avez-vous accédé à votre stage ? Service de l’insertion professionnelle de l’USJ",
    "9b_b- Canaux d’accès à votre stage : Institution USJ / enseignants": "9b_b-Par quel canal avez-vous accédé à votre stage ? Institution USJ / enseignants",
    "9b_c- Canaux d’accès à votre stage : Réseau des anciens – Plateforme AlumniUSJ": "9b_c-Par quel canal avez-vous accédé à votre stage ? Réseau des anciens / Plateforme AlumniUSJ",
    "9b_d- Canaux d’accès à votre stage : Participation à des concours USJ": "9b_d-Par quel canal avez-vous accédé à votre stage ? Participation à des concours USJ",
    "9b_e- Canaux d’accès à votre stage : Sites Web de l'entreprise": "9b_e-Par quel canal avez-vous accédé à votre stage ? Sites web de l’entreprise",
    "9b_f- Canaux d’accès à votre stage :Médias sociaux": "9b_f-Par quel canal avez-vous accédé à votre stage ? Médias sociaux",
    "9b_g- Canaux d’accès à votre stage : Services de recrutement / Portails de recrutement": "9b_g-Par quel canal avez-vous accédé à votre stage ? Services ou portails de recrutement",
    "9b_h- Canaux d’accès à votre stage : Relations personnelles et familiales": "9b_h-Par quel canal avez-vous accédé à votre stage ? Relations personnelles et familiales",
    "9c- Êtes-vous satisfait de la qualité de votre stage ?": "9c-Êtes-vous satisfait de la qualité de votre stage ?",

    "9d_a- L'expérience de stage a permis d'améliorer : La capacité à travailler en équipe": "9d_a-L’expérience de stage a-t-elle permis d’améliorer la capacité à travailler en équipe ?",
    "9d_b- L'expérience de stage a permis d'améliorer : L'appréciation des valeurs éthiques": "9d_b-L’expérience de stage a-t-elle permis d’améliorer l’appréciation des valeurs éthiques ?",
    "9d_c- L'expérience de stage a permis d'améliorer :Le développement professionnel": "9d_c-L’expérience de stage a-t-elle permis d’améliorer le développement professionnel ?",
    "9d_d- L'expérience de stage a permis d'améliorer :Les compétences en matière de gestion du temps": "9d_d-L’expérience de stage a-t-elle permis d’améliorer les compétences en gestion du temps ?",
    "9d_e- L'expérience de stage a permis d'améliorer :Le lien entre la théorie et la pratique": "9d_e-L’expérience de stage a-t-elle permis de renforcer le lien entre la théorie et la pratique ?",

    "11-Avez-vous pris des cours d’anglais à l’USJ et comment évaluez-vous votre apprentissage ?": "11-Avez-vous pris des cours d’anglais à l’USJ et comment évaluez-vous votre apprentissage ?",
    "12- Avez-vous contacté le Service de l’insertion professionnelle de l’USJ ?": "12-Avez-vous contacté le Service de l’insertion professionnelle de l’USJ ?",
    "12_a- Vous a-t-il proposé un stage?": "12_a-Le Service de l’insertion professionnelle vous a-t-il proposé un stage ?",
    "12_a- Vous a-t-il proposé un stage ?": "12_a-Le Service de l’insertion professionnelle vous a-t-il proposé un stage ?",
    "12_b- Vous a-t-il proposé un emploi ?": "12_b-Le Service de l’insertion professionnelle vous a-t-il proposé un emploi ?",
    "12_b- Vous a-t-il proposé un emploi?": "12_b-Le Service de l’insertion professionnelle vous a-t-il proposé un emploi ?",
    "13-Avez-vous participé au Job Fair organisé par le Service ?": "13-Avez-vous participé au Job Fair organisé par le Service de l’insertion professionnelle ?",

    "14_a- Recherche d’emploi": "14_a-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Recherche d’emploi",
    "14_b- Compétences en entretien": "14_b-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Compétences en entretien",
    "14_c- Compétences en communication": "14_c-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Compétences en communication",
    "14_d- Compétences en présentation": "14_d-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Compétences en présentation",
    "14_e- Compétences en leadership": "14_e-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Compétences en leadership",
    "14_f- Connaissance de soi / prise de décision de carrière": "14_f-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Connaissance de soi et prise de décision de carrière",
    "14_g- Démarrez votre propre entreprise": "14_g-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Démarrer votre propre entreprise",
    "14_h- Comment créer et gérer une «persona» publique sur les réseaux sociaux": "14_h-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Créer et gérer une persona publique sur les réseaux sociaux",
    "14_i- Créez votre propre blog": "14_i-Avez-vous suivi une formation du Service de l’insertion professionnelle sur : Créer votre propre blog",

    "15-De manière générale, êtes-vous satisfait des formations que vous avez suivies au Service de l’insertion professionnelle de l’USJ ?": "15-De manière générale, êtes-vous satisfait des formations suivies au Service de l’insertion professionnelle de l’USJ ?",

    "10_autre- Autres test d'anglais": "10_autre-Précisez l’autre test d’anglais normalisé passé",
    "10a_a- Raison: Pour s'inscrire à un programme de master/Doctorat": "10a_a-Pour quelle raison avez-vous passé un test d’anglais ? S’inscrire à un programme de master/doctorat",
    "10a_b- Raison: Pour postuler à un emploi": "10a_b-Pour quelle raison avez-vous passé un test d’anglais ? Postuler à un emploi",
    "10a_c- Raison: Pour faire une demande de visa": "10a_c-Pour quelle raison avez-vous passé un test d’anglais ? Faire une demande de visa",
    "10a_d- Raison: Requis par la faculté/institution": "10a_d-Pour quelle raison avez-vous passé un test d’anglais ? Requis par la faculté/institution",
    "10b- Obtenu le score requis dès la première fois que vous avez passé le test ?": "10b-Avez-vous obtenu le score requis dès la première tentative au test d’anglais ?",
    "10c_a-Avez-vous utilisé: Cours d'entraînement pour le test": "10c_a-Avez-vous utilisé des cours d’entraînement pour le test ?",
    "10c_b-Avez-vous utilisé: Cours pour améliorer les compétences en anglais (en dehors de l'USJ)": "10c_b-Avez-vous utilisé des cours pour améliorer vos compétences en anglais hors USJ ?",
    "10c_c-Avez-vous utilisé:Tuteur particulier": "10c_c-Avez-vous utilisé un tuteur particulier pour préparer le test ?",
    "10c_d-Avez-vous utilisé:Etudes individuelles": "10c_d-Avez-vous utilisé des études individuelles pour préparer le test ?",
    "10c_e-Avez-vous utilisé:Cours USJ": "10c_e-Avez-vous utilisé des cours USJ pour préparer le test ?",

    "16_a-À l’USJ, dans la même discipline": "16_a-Envisagez-vous de poursuivre vos études à l’USJ dans la même discipline ?",
    "16_b-À l’USJ, dans une autre discipline": "16_b-Envisagez-vous de poursuivre vos études à l’USJ dans une autre discipline ?",
    "16_c-Dans une autre université au Liban": "16_c-Envisagez-vous de poursuivre vos études dans une autre université au Liban ?",
    "16_d- Dans une autre université à l'étranger": "16_d-Envisagez-vous de poursuivre vos études dans une autre université à l’étranger ?",

    "17- Exercer une activité rémunérée": "17-Avez-vous exercé une activité rémunérée durant votre parcours à l’USJ ?",

    "21_a- Evaluation: La réputation de l’USJ m’a aidé à trouver un travail dont je suis satisfait": "21_a-Dans quelle mesure la réputation de l’USJ vous a-t-elle aidé à trouver un travail dont vous êtes satisfait ?",
    "21_b- Evaluation: Mon diplôme m’a aidé à trouver un travail dont je suis satisfait": "21_b-Dans quelle mesure votre diplôme vous a-t-il aidé à trouver un travail dont vous êtes satisfait ?",
    "21_c- Evaluation: Mon travail actuel est en adéquation avec mon domaine de formation": "21_c-Dans quelle mesure votre travail actuel est-il en adéquation avec votre domaine de formation ?",

    "22-Prévoyez-vous de quitter le Liban ?": "22-Prévoyez-vous de quitter le Liban ?",

    "24- Bénéficier d'une aide financière accordée par le Service social sur base de critères sociaux": "24-Avez-vous bénéficié d’une aide financière accordée par le Service social sur base de critères sociaux ?",
    "24a- Dans quelle mesure en êtes-vous satisfait ?": "24a-Dans quelle mesure êtes-vous satisfait de cette aide financière ?",
    "25- Bénéficier d'une bourse accordée par l’USJ sur base de critères non sociaux": "25-Avez-vous bénéficié d’une bourse accordée par l’USJ sur base de critères non sociaux ?",
    "25a- Dans quelle mesure en êtes-vous satisfait ?": "25a-Dans quelle mesure êtes-vous satisfait de cette bourse ?",

    "30_a- Au niveau de la Faculté / du Département": "30_a- Êtes-vous satisfait du niveau d'implication des étudiants dans le processus de prise de décision à l’USJ ? Au niveau de la Faculté ou du Département",
    "30_b- Au niveau de l’Université": "30_b- Êtes-vous satisfait du niveau d'implication des étudiants dans le processus de prise de décision à l’USJ ? Au niveau de l’Université",

    "31-Êtes-vous étudiant en situation de handicap ?": "31-Êtes-vous étudiant en situation de handicap ?",

    "32_a- De type ; Déficience intellectuelle": "32_a-De quel type de handicap s’agit-il ? Déficience intellectuelle",
    "32_b- De type ; Déficience motrice": "32_b-De quel type de handicap s’agit-il ? Déficience motrice",
    "32_c- De type ; Déficience auditive": "32_c-De quel type de handicap s’agit-il ? Déficience auditive",
    "32_d- De type ; Déficience visuelle": "32_d-De quel type de handicap s’agit-il ? Déficience visuelle",
    "32_e- De type ; Trouble d'apprentissage": "32_e-De quel type de handicap s’agit-il ? Trouble d’apprentissage",
    "32_f- De type ; Trouble de communication": "32_f-De quel type de handicap s’agit-il ? Trouble de communication",
    "32_g- De type ; Trouble de comportement": "32_g-De quel type de handicap s’agit-il ? Trouble de comportement",
    "33-Avez-vous eu besoin d’un service au sein de votre établissement ?": "33-Avez-vous eu besoin d’un service au sein de votre établissement ?",
    "33-Avez-vous eu besoin d’un service au sein de votre établissement ?": "33-Avez-vous eu besoin d’un service au sein de votre établissement ?",
    "33a- De quels types de service ?": "33a-De quels types de service avez-vous eu besoin au sein de votre établissement ?",
    "33a- De quels types de service ?  ": "33a-De quels types de service avez-vous eu besoin au sein de votre établissement ?",
    "33b- À qui vous adressez-vous pour obtenir ces services ?": "33b-À qui vous adressez-vous pour obtenir ces services ?",
    "33c- Ont-ils été mis à votre disposition ?": "33c-Ces services ont-ils été mis à votre disposition ?",
    "34- Êtes-vous globalement satisfait de vos conditions d’études et d’accueil ?": "34-Êtes-vous globalement satisfait de vos conditions d’études et d’accueil ?",
    "34- Êtes-vous globalement satisfait de vos conditions d'etudes et d'accueil ?": "34-Êtes-vous globalement satisfait de vos conditions d’études et d’accueil ?",
    "34-Êtes-vous globalement satisfait de vos conditions d’études et d’accueil ?": "34-Êtes-vous globalement satisfait de vos conditions d’études et d’accueil ?",

    "35-Consultez-vous le site de l'USJ ?": "35-Consultez-vous le site web de l’USJ ?",
    "36-Suivez-vous les pages et comptes USJ sur les réseaux sociaux (Facebook, Linkedln, Twitter, YouTube, Instagram, …) ?": "36-Suivez-vous les pages et comptes de l’USJ sur les réseaux sociaux ?",
    "37-À quelle fréquence visitez-vous les pages et comptes USJ sur les réseaux sociaux": "37-À quelle fréquence visitez-vous les pages et comptes de l’USJ sur les réseaux sociaux ?",
    "38-Suivez-vous les pages et comptes de la Fédération des Associations des Anciens USJ sur les réseaux sociaux": "38-Suivez-vous les pages et comptes de la Fédération des Associations des Anciens USJ sur les réseaux sociaux ?",
    "39-À quelle fréquence visitez-vous les pages et comptes de la Fédération des Associations des Anciens USJ sur les réseaux sociaux": "39-À quelle fréquence visitez-vous les pages et comptes de la Fédération des Associations des Anciens USJ sur les réseaux sociaux ?",

    "22a_a- Raisons de départ: Poursuivre des études": "22a_a-Pour quelles raisons prévoyez-vous de quitter le Liban ? Poursuivre des études",
    "22a_b- Raisons de départ: Travailler": "22a_b-Pour quelles raisons prévoyez-vous de quitter le Liban ? Travailler",
    "22a_c- Raisons de départ: Emigrer": "22a_c-Pour quelles raisons prévoyez-vous de quitter le Liban ? Émigrer",
    "22a_d- Raisons de départ: Rejoindre ou accompagner un membre de la famille": "22a_d-Pour quelles raisons prévoyez-vous de quitter le Liban ? Rejoindre ou accompagner un membre de la famille",
    "22a_e- Raisons de départ: Crise économique de 2019": "22a_e-Pour quelles raisons prévoyez-vous de quitter le Liban ? Crise économique de 2019",
    "22a_f- Raisons de départ: Absence de sécurité": "22a_f-Pour quelles raisons prévoyez-vous de quitter le Liban ? Absence de sécurité",
    "22a_autre- Raisons de départ: Autre": "22a_autre-Pour quelles raisons prévoyez-vous de quitter le Liban ? Autre",
    "23- Vers quel pays prévoyez-vous partir ?": "23-Vers quel pays prévoyez-vous partir ?",
    "23_autre- Autre pays": "23_autre-Vers quel pays prévoyez-vous partir ? Autre pays",

    "44_a- Financé vos études à l’USJ : Parents": "44-Comment avez-vous financé vos études à l’USJ ? (2024-2025)",
  
}



def clean_other_question_label(question):
    """Return a complete, readable label for complementary questions."""
    q = str(question).strip()
    q_norm = normalize_question_key(q)

    if q_norm.startswith("8"):
        return "8-Êtes-vous membre de la plateforme interactive de l’USJ et de la Fédération des Associations des Anciens, lancée pour fédérer et animer le réseau Alumni ?"

    if "realise un stage" in q_norm or "stage durant votre parcours" in q_norm:
        return "9-Avez-vous réalisé un stage durant votre parcours à l’USJ ?"

    if q_norm.startswith("11"):
        return "11-Avez-vous pris des cours d’anglais à l’USJ et comment évaluez-vous votre apprentissage ?"

    if q_norm.startswith(normalize_question_key("12_a-")):
        return "12_a-Le Service de l’insertion professionnelle vous a-t-il proposé un stage ?"

    if q_norm.startswith(normalize_question_key("12_b-")):
        return "12_b-Le Service de l’insertion professionnelle vous a-t-il proposé un emploi ?"

    if q_norm.startswith("12"):
        return "12-Avez-vous contacté le Service de l’insertion professionnelle de l’USJ ?"

    return OTHER_QUESTION_LABELS.get(q, score_question_label(q))


def normalize_question_key(value):
    """Normalize column labels for robust matching despite accents, spaces and NBSP."""
    import unicodedata
    text = str(value).strip().replace("\u00a0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("’", "'")
    return text.strip()


def is_yes_response(value):
    """Detect affirmative answers used for skip-pattern eligibility.

    This includes standard Oui/Yes responses and extended affirmative responses
    such as "Oui, à temps plein", "Oui, à temps partiel" and
    "Oui, occasionnellement". This is required for conditional questions such
    as Q21, which should be answered only by respondents who declared an
    employment activity in Q17.
    """
    if pd.isna(value):
        return False
    text = normalize_question_key(value)
    return text in {"oui", "yes", "y"} or text.startswith("oui") or text.startswith("yes")


def is_english_test_response(value):
    """Eligibility for Q10 follow-up questions.

    Q10 follow-up questions are applicable to respondents who passed a standardized
    English test. Only the explicit negative answer is excluded from the denominator.
    This keeps TOEFL, IELTS, TOEIC and other affirmative test responses in the base.
    """
    if pd.isna(value):
        return False
    text = normalize_question_key(value)
    if text in {"", "nan", "none", "nat", "<na>"}:
        return False
    if text in {"non", "no", "0", "0- non", "0 - non"}:
        return False
    if text.startswith("non") or text.startswith("no"):
        return False
    return True


def is_english_other_test_response(value):
    """Eligibility for 10_autre: only respondents who selected the 'Oui, autre' test option."""
    if pd.isna(value):
        return False
    text = normalize_question_key(value)
    if text in {"", "nan", "none", "nat", "<na>"}:
        return False
    if text.startswith("non") or text.startswith("no") or text in {"0", "0- non", "0 - non"}:
        return False
    return "autre" in text or "other" in text


def get_parent_eligibility_mask(question_col, parent_values):
    """Apply the correct parent-question eligibility rule for conditional questions."""
    q_norm = normalize_question_key(question_col)

    if q_norm.startswith(normalize_question_key("10_autre-")):
        return parent_values.map(is_english_other_test_response).fillna(False)

    if any(q_norm.startswith(normalize_question_key(prefix)) for prefix in [
        "10a_a-", "10a_b-", "10a_c-", "10a_d-",
        "10b-",
        "10c_a-", "10c_b-", "10c_c-", "10c_d-", "10c_e-"
    ]):
        return parent_values.map(is_english_test_response).fillna(False)

    return parent_values.map(is_yes_response).fillna(False)


def should_exclude_question_from_presentation(question_col):
    """Questions intentionally hidden from the descriptive presentation."""
    q_norm = normalize_question_key(question_col)
    hidden_prefixes = [
        "10a_e-",
        "18_autre-",
        "19_o-",
        "19_autre-",
        "20_autre-",
        "22a_autre-",
        "23_autre-",
        "32_autre-",
    ]
    return any(q_norm.startswith(normalize_question_key(prefix)) for prefix in hidden_prefixes)


def find_column_by_prefix(columns, prefixes):
    """Find a column using normalized prefixes."""
    normalized = {col: normalize_question_key(col) for col in columns}
    for prefix in prefixes:
        prefix_norm = normalize_question_key(prefix)
        for col, norm_col in normalized.items():
            if norm_col.startswith(prefix_norm):
                return col
    return None


def get_question_dependency(question_col, original_data=None):
    """Return the parent question for skip-pattern questions."""
    columns = original_data.columns if original_data is not None else df_original.columns
    q_norm = normalize_question_key(question_col)

    dependency_rules = [
        {
            "child_prefixes": ["4a_a-", "4a_b-", "4a_c-", "4a_d-", "4a_e-", "4a_f-", "4a_g-", "4a_h-", "4b_a-", "4b_b-", "4b_c-", "4b_d-", "4b_e-", "4b_f-"],
            "parent_prefixes": ["4- sollicite un soutien", "4- sollicité un soutien", "4- avez-vous sollicite un soutien", "4- avez-vous sollicité un soutien"],
        },
        {
            "child_prefixes": ["6a_a-", "6a_b-", "6a_c-"],
            "parent_prefixes": [
                "6- etudie a l'etranger",
                "6- étudié à l'étranger",
                "6- avez-vous effectue une periode d'etudes a l'etranger",
                "6- avez-vous effectué une période d’études à l'étranger",
                "6- avez-vous effectué une période d'études à l'étranger",
                "6- etudié à l'étranger",
                "6- etudie a l’étranger",
            ],
        },
        {
            "child_prefixes": ["10_autre-"],
            "parent_prefixes": [
                "10- avez-vous passe un test d'anglais normalise",
                "10- avez-vous passé un test d’anglais normalisé",
                "10- avez-vous passé un test d'anglais normalisé",
                "10- passe un test d'anglais",
            ],
        },
        {
            "child_prefixes": ["10a_a-", "10a_b-", "10a_c-", "10a_d-", "10b-", "10c_a-", "10c_b-", "10c_c-", "10c_d-", "10c_e-"],
            "parent_prefixes": [
                "10- avez-vous passe un test d'anglais normalise",
                "10- avez-vous passé un test d’anglais normalisé",
                "10- avez-vous passé un test d'anglais normalisé",
                "10- passe un test d'anglais",
            ],
        },
        {
            "child_prefixes": ["12_a-", "12_b-"],
            "parent_prefixes": [
                "12- avez-vous contacte le service de l’insertion professionnelle",
                "12- avez-vous contacté le Service de l’insertion professionnelle",
                "12- avez-vous contacté le service de l'insertion professionnelle",
                "12- avez-vous contacte le service de l'insertion professionnelle",
            ],
        },
        {
            "child_prefixes": ["9a-", "9b_a-", "9b_b-", "9b_c-", "9b_d-", "9b_e-", "9b_f-", "9b_g-", "9b_h-", "9c-", "9d_a-", "9d_b-", "9d_c-", "9d_d-", "9d_e-"],
            "parent_prefixes": ["9- avez-vous realise un stage", "9- avez-vous réalisé un stage"],
        },
        {
            # Employment follow-up questions are applicable only to respondents
            # who reported a paid activity in Q17. Respondents who answered Non
            # are excluded from the denominator.
            "child_prefixes": [
                "18-", "18_autre-",
                "19_a-", "19_b-", "19_c-", "19_d-", "19_e-", "19_f-", "19_g-", "19_h-", "19_i-", "19_j-", "19_k-", "19_l-", "19_m-", "19_n-", "19_o-", "19_autre-",
                "20_a-", "20_b-", "20_c-", "20_d-", "20_e-", "20_f-", "20_g-", "20_h-", "20_i-", "20_j-", "20_autre-",
                "21_a-", "21_b-", "21_c-"
            ],
            "parent_prefixes": [
                "17- exercer une activite remuneree",
                "17- exercer une activité rémunérée",
                "17- exercez-vous une activite remuneree",
                "17- exercez-vous une activité rémunérée",
                "17- avez-vous exerce une activite remuneree",
                "17- avez-vous exercé une activité rémunérée"
            ],
        },
        {
            # Departure follow-up questions are applicable only to respondents
            # who answered Oui to Q22: Prévoyez-vous de quitter le Liban ?
            "child_prefixes": [
                "22a_a-", "22a_b-", "22a_c-", "22a_d-", "22a_e-", "22a_f-", "22a_autre-",
                "23-", "23_autre-"
            ],
            "parent_prefixes": [
                "22- prevoyez-vous de quitter le liban",
                "22- prévoyez-vous de quitter le liban",
                "22-prevoyez-vous de quitter le liban",
                "22-prévoyez-vous de quitter le liban",
            ],
        },

        {
            # Disability follow-up questions are applicable only to respondents
            # who answered Oui to Q31: Étudiant en situation de handicap.
            # 32_autre is hidden from presentation, but the rule is kept for completeness.
            "child_prefixes": [
                "32_a-", "32_b-", "32_c-", "32_d-", "32_e-", "32_f-", "32_g-", "32_autre-",
                "33-", "33a-", "33b-", "34-"
            ],
            "parent_prefixes": [
                "31-etes-vous etudiant en situation de handicap",
                "31-êtes-vous étudiant en situation de handicap",
                "31- etes-vous etudiant en situation de handicap",
                "31- êtes-vous étudiant en situation de handicap",
            ],
        },
        {
            # Availability follow-up question is applicable only to respondents
            # who answered Oui to Q33: Besoin d’un service au sein de l’établissement.
            # 33a, 33b and Q34 are treated as linked to Q31 according to the requested dashboard logic.
            "child_prefixes": ["33c-"],
            "parent_prefixes": [
                "33- avez-vous eu besoin d’un service au sein de votre établissement",
                "33- avez-vous eu besoin d'un service au sein de votre etablissement",
                "33- avez-vous eu besoin d’un service au sein de votre etablissement",
                "33-avez-vous eu besoin d’un service au sein de votre établissement",
                "33-avez-vous eu besoin d'un service au sein de votre etablissement",
            ],
        },
        {
            "child_prefixes": ["24a-"],
            "parent_prefixes": ["24- beneficier d'une aide", "24- bénéficier d'une aide"],
        },
        {
            "child_prefixes": ["25a-"],
            "parent_prefixes": ["25- beneficier d'une bourse", "25- bénéficier d'une bourse"],
        },
    
    ]

    for rule in dependency_rules:
        if any(q_norm.startswith(normalize_question_key(prefix)) for prefix in rule["child_prefixes"]):
            return find_column_by_prefix(columns, rule["parent_prefixes"])
    return None


def get_question_non_available_years(question_col):
    """Return years where a question did not exist in the original survey.

    This is different from a missing answer. For example, 9d_a to 9d_e did not exist
    in the 2022-2023 Exit Survey, so 2022-2023 respondents must be excluded from
    the denominator even if the merged Excel accidentally contains copied values.
    """
    q_norm = normalize_question_key(question_col)

    if any(q_norm.startswith(normalize_question_key(prefix)) for prefix in [
        "9d_a-", "9d_b-", "9d_c-", "9d_d-", "9d_e-"
    ]):
        return {"2022-2023", "2022/2023", "2022–2023", "2022_2023"}

    if q_norm.startswith(normalize_question_key("31-")):
        return {"2022-2023", "2022/2023", "2022–2023", "2022_2023"}

    if any(q_norm.startswith(normalize_question_key(prefix)) for prefix in [
        "44_a-", "44_b-", "44_c-", "44_d-", "44_e-", "44_f-", "44_g-"
    ]):
        return {"2022-2023", "2022/2023", "2022–2023", "2022_2023",
                "2023-2024", "2023/2024", "2023–2024", "2023_2024"}

    return set()


def is_question_available_for_year(question_col, year_value):
    unavailable_years = get_question_non_available_years(question_col)
    if not unavailable_years:
        return True

    y = str(year_value).strip()
    y_norm = y.replace("–", "-").replace("/", "-").replace("_", "-")
    unavailable_norm = {str(v).replace("–", "-").replace("/", "-").replace("_", "-") for v in unavailable_years}
    return y_norm not in unavailable_norm


def get_question_available_index(original_data, coded_filter_data, question_col):
    """Return rows where the selected question existed in that survey year."""
    if len(coded_filter_data) == 0:
        return pd.Index([])
    if "Year" not in coded_filter_data.columns:
        return coded_filter_data.index

    available_mask = coded_filter_data["Year"].map(lambda y: is_question_available_for_year(question_col, y)).fillna(True)
    return available_mask[available_mask].index


def get_applicable_response_series(original_data, coded_filter_data, question_col):
    """Return responses using the correct denominator for conditional questions.

    The denominator excludes:
    1. respondents for whom the question was not asked because of skip logic, and
    2. respondents from years where the question did not exist in the original survey.
    """
    if question_col not in original_data.columns or len(coded_filter_data) == 0:
        empty = pd.Series(dtype=object)
        return empty, pd.Index([]), 0, None

    base_index = coded_filter_data.index
    available_index = get_question_available_index(original_data, coded_filter_data, question_col)

    parent_col = get_question_dependency(question_col, original_data)

    if parent_col and parent_col in original_data.columns:
        parent_values = original_data.loc[available_index, parent_col].map(clean_response_value)
        eligible_mask = get_parent_eligibility_mask(question_col, parent_values)
        eligible_index = eligible_mask[eligible_mask].index
    else:
        eligible_index = available_index

    non_applicable_n = int(len(base_index) - len(eligible_index))
    responses = original_data.loc[eligible_index, question_col].map(clean_response_value)
    return responses, eligible_index, non_applicable_n, parent_col

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
    excel_file_path, excel_file_mtime, excel_file_size = find_excel_file()
    df_original, df_coded, components, q42, q43, q26, q27 = prepare_data(
        excel_file_path,
        excel_file_mtime,
        excel_file_size
    )

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
        st.image("LogoUAQ.png", width=360)
    elif os.path.exists("usj_logo.png"):
        st.image("usj_logo.png", width=230)

st.divider()

# =====================================================
# Page state used to adapt filters
# =====================================================

PAGE_OPTIONS = [
    "Résultats descriptifs de toutes les questions",
    "Comparaison historique",
    "Vue générale des indicateurs",
    "Facteurs clés d’amélioration",
    "Statistiques inférentielles",
    "Méthodologie des composantes",
    "Rapport synthétique imprimable"
]

CURRENT_PAGE = st.session_state.get("nav_page", "Vue générale des indicateurs")
if CURRENT_PAGE not in PAGE_OPTIONS:
    CURRENT_PAGE = "Vue générale des indicateurs"
IS_HISTORICAL_PAGE = CURRENT_PAGE == "Comparaison historique"

# =====================================================
# Professional control panel and linked filters
# =====================================================

last_update_label = pd.to_datetime(excel_file_mtime, unit="s").strftime("%Y-%m-%d %H:%M:%S")
file_size_mb = excel_file_size / (1024 * 1024)

st.markdown(
    f"""
    <div class="control-panel">
        <div class="control-title">Pilotage du tableau de bord</div>
        <div class="control-subtitle">
            Ajustez les filtres pour actualiser automatiquement l’ensemble des indicateurs, comparaisons, analyses descriptives,
            statistiques inférentielles et rapports synthétiques.
        </div>
        <div class="data-chip-row">
            <span class="data-chip">📁 <strong>Fichier actif</strong> {excel_file_path}</span>
            <span class="data-chip">💾 <strong>Taille</strong> {file_size_mb:.2f} Mo</span>
            <span class="data-chip">🕒 <strong>Dernière modification</strong> {last_update_label}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

filter_action_cols = st.columns([1.15, 1.35, 6.5])

with filter_action_cols[0]:
    if st.button("↺ Réinitialiser les filtres", use_container_width=True):
        available_years_reset = year_filter_options(df_coded, "Year")
        st.session_state["filter_year"] = available_years_reset[-1] if available_years_reset else ""
        st.session_state["filter_genre"] = "Tous"
        st.session_state["filter_faculte"] = "Tous"
        st.session_state["filter_campus"] = "Tous"
        st.session_state["filter_cursus"] = "Tous"
        st.session_state["filter_niveau"] = "Tous"
        st.rerun()

with filter_action_cols[1]:
    if st.button("⟳ Actualiser les données Excel", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown(
    f"""
    <div style="
        margin-top:12px;
        margin-bottom:8px;
        color:{USJ_BLUE};
        font-family:Candara, Arial, sans-serif;
        font-weight:900;
        font-size:17px;
    ">
        Filtres d’analyse
    </div>
    """,
    unsafe_allow_html=True
)

filter_cols = st.columns(5 if IS_HISTORICAL_PAGE else 6)
df_filter_base = df_coded.copy()

# Campus can have slightly different names depending on the Excel file.
CAMPUS_COLUMN = next(
    (col for col in ["Campus", "campus", "Campus_g", "Campus principal", "Campus_principal", "Site", "site"] if col in df_filter_base.columns),
    None
)

available_years = year_filter_options(df_filter_base, "Year")
if not available_years:
    st.error("Aucune année valide n’est disponible dans le fichier Excel.")
    st.stop()

# The global year filter intentionally excludes "Tous".
# This prevents the overview and descriptive pages from combining several survey years.
if st.session_state.get("filter_year") not in available_years:
    st.session_state["filter_year"] = available_years[-1]

if IS_HISTORICAL_PAGE:
    year = "Tous"
    df_after_year = df_filter_base.copy()
    filter_offset = 0
else:
    with filter_cols[0]:
        year = st.selectbox("Année", available_years, key="filter_year")
    df_after_year = df_filter_base[df_filter_base["Year"].astype(str) == year].copy()
    filter_offset = 1

with filter_cols[filter_offset + 0]:
    genre = st.selectbox("Genre", filter_options(df_after_year, "Genre"), key="filter_genre")

df_after_genre = df_after_year.copy()
if genre != "Tous":
    df_after_genre = df_after_genre[df_after_genre["Genre"].astype(str) == genre]

with filter_cols[filter_offset + 1]:
    faculte = st.selectbox("Faculté", filter_options(df_after_genre, "Faculté_Institut_g"), key="filter_faculte")

df_after_faculte = df_after_genre.copy()
if faculte != "Tous":
    df_after_faculte = df_after_faculte[df_after_faculte["Faculté_Institut_g"].astype(str) == faculte]

with filter_cols[filter_offset + 2]:
    if CAMPUS_COLUMN:
        campus = st.selectbox("Campus", filter_options(df_after_faculte, CAMPUS_COLUMN), key="filter_campus")
    else:
        campus = "Tous"
        st.selectbox("Campus", ["Tous"], key="filter_campus", disabled=True)

df_after_campus = df_after_faculte.copy()
if CAMPUS_COLUMN and campus != "Tous":
    df_after_campus = df_after_campus[df_after_campus[CAMPUS_COLUMN].astype(str) == campus]

with filter_cols[filter_offset + 3]:
    cursus = st.selectbox("Cursus", filter_options(df_after_campus, "Cursus"), key="filter_cursus")

df_after_cursus = df_after_campus.copy()
if cursus != "Tous":
    df_after_cursus = df_after_cursus[df_after_cursus["Cursus"].astype(str) == cursus]

with filter_cols[filter_offset + 4]:
    niveau = st.selectbox("Niveau", filter_options(df_after_cursus, "Niveau"), key="filter_niveau")

df_filtered = df_after_cursus.copy()
if niveau != "Tous":
    df_filtered = df_filtered[df_filtered["Niveau"].astype(str) == niveau]

active_filter_labels = []
if year != "Tous" and not IS_HISTORICAL_PAGE:
    active_filter_labels.append(f"Année : {year}")
if genre != "Tous":
    active_filter_labels.append(f"Genre : {genre}")
if faculte != "Tous":
    active_filter_labels.append(f"Faculté : {faculte}")
if CAMPUS_COLUMN and campus != "Tous":
    active_filter_labels.append(f"Campus : {campus}")
if cursus != "Tous":
    active_filter_labels.append(f"Cursus : {cursus}")
if niveau != "Tous":
    active_filter_labels.append(f"Niveau : {niveau}")
active_filter_text = " | ".join(active_filter_labels) if active_filter_labels else "Aucun filtre spécifique appliqué"

st.markdown(
    f"""
    <div class="respondent-card">
        <div>
            <div class="label">Population actuellement analysée</div>
            <div style="font-size:13px; opacity:0.90; margin-top:4px;">{active_filter_text}</div>
        </div>
        <div class="value">{len(df_filtered):,}</div>
    </div>
    """.replace(",", " "),
    unsafe_allow_html=True
)

# =====================================================
# Navigation
# =====================================================

st.markdown('<div class="nav-title">Navigation analytique</div>', unsafe_allow_html=True)

page = st.radio(
    "Navigation analytique",
    PAGE_OPTIONS,
    horizontal=True,
    label_visibility="collapsed",
    key="nav_page"
)

year_summary_all = build_year_summary(df_coded, q43)
year_summary_filtered = build_year_summary(df_filtered, q43)
component_long_filtered = build_component_long(df_filtered)


def get_single_year_context(page_key, label="Année à afficher"):
    """For selected pages, force one year instead of combining all years when global year is Tous."""
    years_available = sorted(df_coded["Year"].dropna().astype(str).unique().tolist()) if "Year" in df_coded.columns else []
    if not years_available:
        return year, df_filtered.copy(), df_original.loc[df_filtered.index].copy()

    if year != "Tous":
        page_year = str(year)
    else:
        default_index = len(years_available) - 1
        st.info("Cette page n’agrège pas les années. Sélectionnez une année spécifique pour afficher les résultats.")
        page_year = st.selectbox(label, years_available, index=default_index, key=f"single_year_{page_key}")

    data_page = df_filtered[df_filtered["Year"].astype(str) == page_year].copy()
    original_page = df_original.loc[data_page.index].copy()
    return page_year, data_page, original_page


# =====================================================
# Page 1 - Overview
# =====================================================

def page_indicators():
    section_header(
        "Vue générale des indicateurs",
        "Synthèse dynamique des principaux indicateurs de satisfaction et de recommandation pour une année sélectionnée."
    )

    selected_year, data_ind, original_ind = get_single_year_context("indicators")

    if data_ind.empty:
        st.warning("Aucune donnée disponible pour l’année et les filtres sélectionnés.")
        return

    local_year_summary = build_year_summary(data_ind, q43)

    satisfaction_pct = pct_from_mean(data_ind["Score satisfaction globale"].mean())
    recommandation_pct = calculate_recommendation_rate(data_ind, q43)

    delta_sat = compute_previous_delta(local_year_summary, selected_year, "Satisfaction globale")
    delta_rec = compute_previous_delta(local_year_summary, selected_year, "Taux de recommandation")

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card(
            "Satisfaction globale à l’Université",
            data_ind["Score satisfaction globale"].mean(),
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
            data_ind["Score expérience globale USJ"].mean(),
            "Expérience académique et personnelle"
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        kpi_card("Enseignement et apprentissage", data_ind["Score enseignement et apprentissage"].mean())

    with c5:
        kpi_card("Accompagnement et encadrement", data_ind["Score accompagnement et encadrement"].mean())

    with c6:
        kpi_card("Développement des compétences", data_ind["Score développement des compétences"].mean())

    c7, c8, c9 = st.columns(3)

    with c7:
        kpi_card("Services de l’USJ", data_ind["Score services USJ"].mean())

    with c8:
        kpi_card(
            "Vie étudiante et activités",
            data_ind["Score vie étudiante et activités"].mean(),
            "Pas au courant exclu"
        )

    with c9:
        kpi_card("Infrastructures et équipements", data_ind["Score infrastructures et équipements"].mean())

    c10, c11 = st.columns(2)

    with c10:
        kpi_card("Frais de scolarité / qualité de l’enseignement", data_ind["Score frais / qualité enseignement"].mean())

    with c11:
        kpi_card("Frais de scolarité / autres universités", data_ind["Score frais / autres universités"].mean())

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
            pct_from_mean(data_ind["Score enseignement et apprentissage"].mean()),
            pct_from_mean(data_ind["Score accompagnement et encadrement"].mean()),
            pct_from_mean(data_ind["Score développement des compétences"].mean()),
            pct_from_mean(data_ind["Score expérience globale USJ"].mean()),
            pct_from_mean(data_ind["Score services USJ"].mean()),
            pct_from_mean(data_ind["Score vie étudiante et activités"].mean()),
            pct_from_mean(data_ind["Score infrastructures et équipements"].mean()),
            pct_from_mean(data_ind["Score frais / qualité enseignement"].mean()),
            pct_from_mean(data_ind["Score frais / autres universités"].mean())
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

    if False and year == "Tous" and len(local_year_summary) > 1:
        section_header("Évolution synthétique", "Tendance globale des indicateurs principaux sur les années disponibles.")

        trend = local_year_summary[["Année", "Satisfaction globale", "Taux de recommandation"]].melt(
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
        "Comparaison des questions de la section sélectionnée sur toutes les années disponibles."
    )

    summary_box(
        """
        Cette page compare automatiquement toutes les années disponibles. Le filtre Année n’est pas utilisé dans cette page afin de garder une vraie lecture historique. Les autres filtres actifs restent appliqués.
        """,
        color=USJ_BLUE,
        background="#F7F8FC"
    )

    data_hist = df_coded.copy()

    if genre != "Tous" and "Genre" in data_hist.columns:
        data_hist = data_hist[data_hist["Genre"].astype(str) == str(genre)]
    if faculte != "Tous" and "Faculté_Institut_g" in data_hist.columns:
        data_hist = data_hist[data_hist["Faculté_Institut_g"].astype(str) == str(faculte)]
    if CAMPUS_COLUMN and campus != "Tous" and CAMPUS_COLUMN in data_hist.columns:
        data_hist = data_hist[data_hist[CAMPUS_COLUMN].astype(str) == str(campus)]
    if cursus != "Tous" and "Cursus" in data_hist.columns:
        data_hist = data_hist[data_hist["Cursus"].astype(str) == str(cursus)]
    if niveau != "Tous" and "Niveau" in data_hist.columns:
        data_hist = data_hist[data_hist["Niveau"].astype(str) == str(niveau)]

    if data_hist.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    years_hist = sorted(data_hist["Year"].dropna().astype(str).unique().tolist()) if "Year" in data_hist.columns else []
    if len(years_hist) < 2:
        st.warning("La comparaison historique nécessite au moins deux années disponibles après application des filtres.")
        return

    def compact_card(title, value, subtitle, color=USJ_BLUE):
        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-radius:14px;padding:12px 14px;min-height:92px;box-shadow:0 3px 10px rgba(0,0,0,0.04);font-family:Candara, Arial, sans-serif;'>
                <div style='font-size:13px;font-weight:900;color:{USJ_TEXT};'>{html_escape(title)}</div>
                <div style='font-size:26px;font-weight:900;color:{color};margin-top:6px;line-height:1;'>{html_escape(value)}</div>
                <div style='font-size:12px;color:#667085;margin-top:8px;'>{html_escape(subtitle)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    available_sections = list(ALL_SURVEY_SECTION_NUMBERS.keys())
    selected_section_comp = st.selectbox(
        "Choisir une section du questionnaire",
        available_sections,
        key="historical_section_selector_clean"
    )

    question_map = get_columns_for_all_questions_section(df_original, selected_section_comp)
    if not question_map:
        st.warning("Aucune colonne trouvée dans le fichier Excel pour cette section.")
        return

    base_by_year = data_hist.groupby("Year").size().reindex(years_hist).fillna(0).astype(int)
    k1, k2, k3 = st.columns([1, 1, 1.8])
    with k1:
        compact_card("Années comparées", str(len(years_hist)), " | ".join(years_hist), USJ_BLUE)
    with k2:
        compact_card("Base totale", f"{len(data_hist):,}".replace(",", " "), "Toutes années", USJ_BLUE_2)
    with k3:
        base_txt = " | ".join([f"{y}: {int(base_by_year.loc[y]):,}".replace(',', ' ') for y in years_hist])
        compact_card("Bases annuelles", base_txt, "Répondants par année", USJ_GOLD)

    summary_box(
        f"""
        La section <b>{html_escape(selected_section_comp)}</b> contient <b>{len(question_map)}</b> question(s). Toutes les questions de cette section sont affichées ci-dessous, sans menu de sélection question par question.
        """,
        color=USJ_BLUE,
        background="#F7F8FC"
    )

    def build_historical_distribution_for_question(question_col):
        rows = []
        meta_rows = []
        for year_value in years_hist:
            year_data = data_hist[data_hist["Year"].astype(str) == str(year_value)].copy()
            if year_data.empty:
                continue
            responses, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(
                df_original,
                year_data,
                question_col
            )
            valid = responses.dropna()
            eligible_n = int(len(eligible_index))
            valid_n = int(valid.shape[0])
            missing_n = int(responses.isna().sum()) if eligible_n > 0 else 0
            missing_pct = missing_n / eligible_n * 100 if eligible_n > 0 else np.nan
            meta_rows.append({
                "Année": str(year_value),
                "Base applicable": eligible_n,
                "N valide": valid_n,
                "Données manquantes (%)": missing_pct,
                "Non applicable": int(non_applicable_n),
                "Question filtre": clean_other_question_label(parent_col) if parent_col else "Aucune condition",
            })
            if valid_n > 0:
                counts = valid.value_counts(dropna=True).reset_index()
                counts.columns = ["Réponse", "N"]
                counts["Pourcentage"] = counts["N"] / counts["N"].sum() * 100
                for _, row in counts.iterrows():
                    rows.append({
                        "Année": str(year_value),
                        "Réponse": row["Réponse"],
                        "N": int(row["N"]),
                        "Pourcentage": float(row["Pourcentage"]),
                    })
        return pd.DataFrame(rows), pd.DataFrame(meta_rows)

    def render_comparison_pivot(dist_hist, years_hist, response_label="Réponse", max_rows=None):
        """USJ-styled comparison table: modalities in rows and years in columns."""
        if dist_hist.empty:
            return

        pivot_pct = dist_hist.pivot_table(index="Réponse", columns="Année", values="Pourcentage", aggfunc="sum").fillna(0)
        pivot_n = dist_hist.pivot_table(index="Réponse", columns="Année", values="N", aggfunc="sum").fillna(0)
        order = pivot_pct.mean(axis=1).sort_values(ascending=False).index
        pivot_pct = pivot_pct.loc[order]
        pivot_n = pivot_n.loc[order]

        if max_rows is not None:
            pivot_pct = pivot_pct.head(max_rows)
            pivot_n = pivot_n.loc[pivot_pct.index]

        year_colors = [USJ_BLUE, USJ_RED, USJ_GOLD, USJ_BLUE_2]

        header_cells = [f"<th class='first-col'>{html_escape(response_label)}</th>"]
        for i, y in enumerate(years_hist):
            header_cells.append(
                f"<th><span class='year-dot' style='background:{year_colors[i % len(year_colors)]};'></span>{html_escape(y)}</th>"
            )

        body_rows = []
        for resp in pivot_pct.index:
            cells = [f"<td class='modalite-cell'>{html_escape(resp)}</td>"]
            for i, y in enumerate(years_hist):
                pct_val = float(pivot_pct.loc[resp, y]) if y in pivot_pct.columns else 0.0
                n_val = int(pivot_n.loc[resp, y]) if y in pivot_n.columns else 0
                color = year_colors[i % len(year_colors)]
                bar_width = min(100, max(0, pct_val))
                cells.append(
                    f"""
                    <td>
                        <div class='cell-wrap'>
                            <div class='mini-bar'>
                                <div class='mini-fill' style='width:{bar_width:.1f}%; background:{color};'></div>
                            </div>
                            <div class='cell-value'>{pct_val:.2f}% <span>({n_val})</span></div>
                        </div>
                    </td>
                    """
                )
            body_rows.append("<tr>" + "".join(cells) + "</tr>")

        height = 72 + min(360, 38 * max(1, len(pivot_pct)))
        table_html = f"""
        <html>
        <head>
        <style>
            body {{
                margin:0;
                font-family:Candara, Arial, sans-serif;
                color:{USJ_TEXT};
                background:white;
            }}
            .table-card {{
                border:1px solid #DDE5F0;
                border-radius:18px;
                overflow:hidden;
                box-shadow:0 8px 22px rgba(0,27,117,0.08);
                background:white;
            }}
            .scroll-area {{
                max-height:{min(360, 38 * max(1, len(pivot_pct)) + 44)}px;
                overflow:auto;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                font-size:14px;
            }}
            thead th {{
                position:sticky;
                top:0;
                z-index:2;
                background:{USJ_BLUE};
                color:white;
                padding:9px 12px;
                text-align:left;
                font-weight:900;
                border-right:1px solid rgba(255,255,255,0.20);
                white-space:nowrap;
            }}
            th.first-col {{ min-width:280px; }}
            tbody td {{
                padding:7px 12px;
                border-bottom:1px solid #E6ECF3;
                border-right:1px solid #EEF2F8;
                vertical-align:middle;
                background:#FFFFFF;
            }}
            tbody tr:nth-child(even) td {{ background:#FBFCFE; }}
            tbody tr:hover td {{ background:#F3F6FF; }}
            .modalite-cell {{
                font-weight:900;
                color:{USJ_BLUE};
                line-height:1.25;
            }}
            .year-dot {{
                display:inline-block;
                width:10px;
                height:10px;
                border-radius:50%;
                margin-right:8px;
                vertical-align:middle;
            }}
            .cell-wrap {{
                display:flex;
                align-items:center;
                gap:12px;
                min-width:170px;
            }}
            .mini-bar {{
                height:8px;
                width:90px;
                background:#EEF2F8;
                border-radius:999px;
                overflow:hidden;
                box-shadow:inset 0 1px 2px rgba(0,0,0,0.08);
            }}
            .mini-fill {{
                height:8px;
                border-radius:999px;
            }}
            .cell-value {{
                font-weight:900;
                color:{USJ_TEXT};
                white-space:nowrap;
            }}
            .cell-value span {{
                font-weight:600;
                color:#667085;
            }}
        </style>
        </head>
        <body>
            <div class='table-card'>
                <div class='scroll-area'>
                    <table>
                        <thead><tr>{''.join(header_cells)}</tr></thead>
                        <tbody>{''.join(body_rows)}</tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        st_components.html(table_html, height=height, scrolling=False)

    def render_clear_comparison_chart(dist_hist, years_hist, title="Comparaison des modalités par année", top_n=12):
        """Clear grouped horizontal chart using the USJ logo palette."""
        if dist_hist.empty:
            return
        order = (
            dist_hist.groupby("Réponse", as_index=False)["Pourcentage"].mean()
            .sort_values("Pourcentage", ascending=False)
            .head(top_n)["Réponse"].tolist()
        )
        chart_df = dist_hist[dist_hist["Réponse"].isin(order)].copy()
        chart_df["Réponse"] = pd.Categorical(chart_df["Réponse"], categories=list(reversed(order)), ordered=True)
        fig = px.bar(
            chart_df,
            x="Pourcentage",
            y="Réponse",
            color="Année",
            text="Pourcentage",
            barmode="group",
            orientation="h",
            color_discrete_sequence=[USJ_BLUE, USJ_RED, USJ_GOLD, USJ_BLUE_2],
            hover_data={"N": True, "Pourcentage": ":.2f"},
            title=title
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            marker_line_color="white",
            marker_line_width=1.1,
            cliponaxis=False
        )
        fig.update_layout(
            xaxis_title="Pourcentage des réponses valides",
            yaxis_title="",
            legend_title="Année",
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="left", x=0, font=dict(size=12)),
            margin=dict(l=40, r=110, t=95, b=45),
        )
        fig.update_xaxes(range=[0, min(105, max(10, chart_df["Pourcentage"].max() + 8))])
        theme_layout(fig, height=max(380, 36 * len(order)), showlegend=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

    def render_historical_positive_kpis(dist_hist, years_hist):
        """Add yearly positive-answer KPIs for recognized scale questions while keeping original modalities."""
        if dist_hist is None or dist_hist.empty:
            return

        positive_rows = []
        for year_value in years_hist:
            year_dist = dist_hist[dist_hist["Année"].astype(str) == str(year_value)][["Réponse", "N", "Pourcentage"]].copy()
            if year_dist.empty:
                continue
            positive_summary = get_positive_scale_summary(year_dist)
            if positive_summary:
                positive_rows.append({
                    "Année": str(year_value),
                    "Label": positive_summary.get("label", "Réponses positives"),
                    "Subtitle": positive_summary.get("subtitle", "Total des réponses positives"),
                    "N positif": int(positive_summary.get("N positif", 0)),
                    "N total": int(positive_summary.get("N total", 0)),
                    "Pourcentage positif": float(positive_summary.get("Pourcentage positif", np.nan)),
                })

        if not positive_rows:
            return

        positive_df = pd.DataFrame(positive_rows)
        kpi_label = positive_df["Label"].iloc[0]
        kpi_subtitle = positive_df["Subtitle"].iloc[0]

        st.markdown(
            f"""
            <div style='margin:8px 0 8px 0;font-family:Candara, Arial, sans-serif;'>
                <div style='font-size:18px;font-weight:900;color:{USJ_BLUE};'>{html_escape(kpi_label)} par année</div>
                <div style='font-size:13px;color:#667085;margin-top:2px;'>{html_escape(kpi_subtitle)}. Les modalités originales restent affichées dans le graphique et le tableau ci-dessous.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        card_cols = st.columns(len(positive_df))
        for col, (_, row) in zip(card_cols, positive_df.iterrows()):
            pct = row["Pourcentage positif"]
            color = kpi_color_percentage(pct)
            with col:
                st.markdown(
                    f"""
                    <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {color};border-radius:16px;padding:13px 15px;min-height:104px;box-shadow:0 5px 14px rgba(0,27,117,0.06);font-family:Candara, Arial, sans-serif;'>
                        <div style='font-size:13px;font-weight:900;color:{USJ_TEXT};'>{html_escape(row['Année'])}</div>
                        <div style='font-size:31px;font-weight:900;color:{color};line-height:1;margin-top:7px;'>{safe_pct(pct)}</div>
                        <div style='font-size:13px;font-weight:800;color:{USJ_BLUE};margin-top:7px;'>{int(row['N positif']):,} / {int(row['N total']):,}</div>
                    </div>
                    """.replace(",", " "),
                    unsafe_allow_html=True
                )


    def render_age_comparison(question_col):
        age_rows = []
        band_rows = []
        labels = ["Moins de 20 ans", "20-21 ans", "22-23 ans", "24-25 ans", "26-29 ans", "30-34 ans", "35 ans et plus"]
        bins = [0, 20, 22, 24, 26, 30, 35, 150]
        for year_value in years_hist:
            year_data = data_hist[data_hist["Year"].astype(str) == str(year_value)].copy()
            responses, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(df_original, year_data, question_col)
            age_numeric = pd.to_numeric(responses, errors="coerce").dropna()
            if age_numeric.empty:
                continue
            age_rows.append({
                "Année": str(year_value),
                "Moyenne": float(age_numeric.mean()),
                "Médiane": float(age_numeric.median()),
                "N valide": int(age_numeric.shape[0]),
            })
            grouped = pd.cut(age_numeric, bins=bins, labels=labels, right=False)
            counts = grouped.value_counts().reindex(labels).fillna(0).astype(int)
            total = int(counts.sum())
            for band, n in counts.items():
                band_rows.append({
                    "Année": str(year_value),
                    "Tranche d’âge": str(band),
                    "N": int(n),
                    "Pourcentage": (int(n) / total * 100) if total > 0 else np.nan,
                })
        age_df = pd.DataFrame(age_rows)
        band_df = pd.DataFrame(band_rows)
        if age_df.empty:
            st.warning("Aucune donnée numérique valide disponible pour l’âge.")
            return

        c1, c2, c3 = st.columns(3)
        with c1:
            compact_card("Âge moyen", f"{age_df.iloc[-1]['Moyenne']:.1f}", f"Dernière année : {age_df.iloc[-1]['Année']}", USJ_BLUE)
        with c2:
            compact_card("Âge médian", f"{age_df.iloc[-1]['Médiane']:.1f}", "Dernière année", USJ_BLUE_2)
        with c3:
            delta = age_df.sort_values("Année").iloc[-1]["Moyenne"] - age_df.sort_values("Année").iloc[0]["Moyenne"] if len(age_df) >= 2 else np.nan
            compact_card("Évolution moyenne", f"{delta:+.1f} an" if pd.notna(delta) else "NA", f"{years_hist[0]} à {years_hist[-1]}", USJ_RED if pd.notna(delta) and delta < 0 else USJ_GOLD)

        fig_mean = go.Figure()
        fig_mean.add_trace(go.Scatter(
            x=age_df["Année"], y=age_df["Moyenne"], mode="lines+markers+text",
            name="Moyenne", text=age_df["Moyenne"].map(lambda x: f"{x:.1f}"), textposition="top center",
            line=dict(color=USJ_BLUE, width=4), marker=dict(size=11, color=USJ_BLUE, line=dict(color="white", width=2)),
            hovertemplate="Année=%{x}<br>Âge moyen=%{y:.2f}<extra></extra>"
        ))
        fig_mean.add_trace(go.Scatter(
            x=age_df["Année"], y=age_df["Médiane"], mode="lines+markers+text",
            name="Médiane", text=age_df["Médiane"].map(lambda x: f"{x:.1f}"), textposition="bottom center",
            line=dict(color=USJ_RED, width=3, dash="dot"), marker=dict(size=10, color=USJ_RED, line=dict(color="white", width=2)),
            hovertemplate="Année=%{x}<br>Âge médian=%{y:.2f}<extra></extra>"
        ))
        fig_mean.update_layout(title="Évolution de l’âge moyen et médian", xaxis_title="Année", yaxis_title="Âge")
        theme_layout(fig_mean, height=360, showlegend=True)
        st.plotly_chart(fig_mean, use_container_width=True, config={"displayModeBar": False})

        if not band_df.empty:
            fig_band = px.bar(
                band_df,
                x="Tranche d’âge",
                y="Pourcentage",
                color="Année",
                text="Pourcentage",
                barmode="group",
                color_discrete_sequence=[USJ_BLUE, USJ_RED, USJ_GOLD, USJ_BLUE_2],
                hover_data={"N": True, "Pourcentage": ":.2f"},
                title="Comparaison par tranches d’âge"
            )
            fig_band.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_color="white", marker_line_width=1.2)
            fig_band.update_layout(xaxis_title="Tranche d’âge", yaxis_title="Pourcentage des âges valides", legend_title="Année")
            fig_band.update_xaxes(tickangle=-20)
            theme_layout(fig_band, height=420, showlegend=True)
            st.plotly_chart(fig_band, use_container_width=True, config={"displayModeBar": False})

        display_age = age_df.copy()
        display_age["Moyenne"] = display_age["Moyenne"].map(lambda x: f"{x:.2f}")
        display_age["Médiane"] = display_age["Médiane"].map(lambda x: f"{x:.2f}")
        st.dataframe(display_age, use_container_width=True, hide_index=True)

    current_main_group = None
    for idx, (question_label, question_col) in enumerate(question_map.items(), start=1):
        group_info = get_main_question_group_header(question_col)
        group_code = group_info["code"] if group_info else None
        if group_code and group_code != current_main_group:
            render_main_question_group_header(group_info)
            current_main_group = group_code
        elif not group_code:
            current_main_group = None

        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {USJ_BLUE};border-radius:16px;padding:10px 14px;margin:6px 0 2px 0;box-shadow:0 3px 10px rgba(0,0,0,0.04);font-family:Candara, Arial, sans-serif;'>
                <div style='font-size:12px;font-weight:900;color:#667085;margin-bottom:4px;'>Question / variable</div>
                <div style='font-size:19px;font-weight:900;color:{USJ_BLUE};line-height:1.35;'>{html_escape(question_label)}</div>
                <div style='font-size:12px;color:#667085;margin-top:6px;'>Variable Excel : {html_escape(question_col)}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if normalize_question_key(question_col) in {"age", "âge"} or normalize_question_key(question_label) in {"age", "âge"}:
            render_age_comparison(question_col)
            continue

        dist_hist, metadata = build_historical_distribution_for_question(question_col)
        if metadata.empty:
            st.warning("Aucune information disponible pour cette question.")
            continue

        parent_label = metadata["Question filtre"].iloc[0] if "Question filtre" in metadata.columns else "Aucune condition"
        if parent_label != "Aucune condition":
            st.markdown(
                f"<div style='font-size:12px;color:#667085;margin-top:-2px;margin-bottom:6px;'>Question conditionnelle liée à : <b>{html_escape(parent_label)}</b></div>",
                unsafe_allow_html=True
            )

        total_valid = int(metadata["N valide"].sum())
        total_base = int(metadata["Base applicable"].sum())
        avg_missing = metadata["Données manquantes (%)"].replace([np.inf, -np.inf], np.nan).mean()
        modalities_n = int(dist_hist["Réponse"].dropna().nunique()) if not dist_hist.empty else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            compact_card("Base applicable", f"{total_base:,}".replace(",", " "), "Somme annuelle", USJ_BLUE_2)
        with c2:
            compact_card("N valide", f"{total_valid:,}".replace(",", " "), "Réponses valides", USJ_BLUE)
        with c3:
            compact_card("Données manquantes moy.", safe_pct(avg_missing), "Moyenne annuelle", USJ_RED if pd.notna(avg_missing) and avg_missing > 10 else USJ_GOLD)

        if dist_hist.empty or total_valid == 0:
            st.warning("Aucune réponse valide disponible pour cette question sur les années comparées.")
            continue

        with st.expander("Voir les bases de calcul par année", expanded=False):
            meta_display = metadata.copy()
            meta_display["Données manquantes (%)"] = meta_display["Données manquantes (%)"].map(lambda x: "" if pd.isna(x) else f"{x:.1f}%")
            st.dataframe(meta_display[["Année", "Base applicable", "N valide", "Données manquantes (%)", "Non applicable"]], use_container_width=True, hide_index=True)

        if modalities_n > 30:
            st.markdown(f"<h3 style='color:{USJ_BLUE}; margin-top:4px;margin-bottom:2px;'>Tableau comparatif des modalités les plus fréquentes</h3>", unsafe_allow_html=True)
            render_comparison_pivot(dist_hist, years_hist, response_label="Modalité", max_rows=60)
            continue

        render_historical_positive_kpis(dist_hist, years_hist)

        st.markdown(f"<h3 style='color:{USJ_BLUE}; margin-top:4px;margin-bottom:2px;'>Distribution comparative</h3>", unsafe_allow_html=True)
        render_clear_comparison_chart(
            dist_hist,
            years_hist,
            title="Comparaison des réponses par année",
            top_n=12
        )
        st.markdown(f"<h3 style='color:{USJ_BLUE}; margin-top:4px;margin-bottom:2px;'>Tableau comparatif par année</h3>", unsafe_allow_html=True)
        render_comparison_pivot(dist_hist, years_hist, response_label="Réponse")


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
        "Statistiques inférentielles par question",
        "Comparaison statistique des réponses aux questions du questionnaire selon le genre, la faculté, le campus et le niveau."
    )

    summary_box(
        """
        Cette section teste directement les réponses brutes des questions du questionnaire, sans utiliser les scores agrégés.
        Dans le profil des répondants, les autres variables démographiques restent comparées à la variable sélectionnée, en excluant seulement l’auto-comparaison directe comme Genre selon Genre.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    data_inf = df_filtered.copy()
    original_inf = df_original.loc[data_inf.index].copy()

    if data_inf.empty:
        st.warning("Aucune donnée disponible avec les filtres sélectionnés.")
        return

    inferential_group_candidates = {
        "Genre": ["Genre"],
        "Faculté": ["Faculté_Institut_g", "Faculté_Institut", "Faculté", "Institut"],
        "Campus": ["Campus", "campus", "Campus_g", "Campus principal", "Campus_principal", "Site", "site"],
        "Niveau": ["Niveau", "Niveau_Lib"],
    }

    available_groups = {}
    for display_name, candidates in inferential_group_candidates.items():
        found_col = resolve_first_existing_column(data_inf, candidates)
        if found_col:
            available_groups[display_name] = found_col

    if not available_groups:
        st.warning("Aucune des variables de comparaison demandées n’est disponible dans le fichier filtré.")
        return

    control_cols = st.columns([1.1, 2.2])
    with control_cols[0]:
        selected_group_label = st.selectbox(
            "Comparer les réponses selon",
            list(available_groups.keys()),
            key="inferential_question_group_selector"
        )
    selected_group_col = available_groups[selected_group_label]

    with control_cols[1]:
        available_sections = list(ALL_SURVEY_SECTION_NUMBERS.keys())
        selected_section_inf = st.selectbox(
            "Choisir une section du questionnaire",
            available_sections,
            key="inferential_question_section_selector"
        )

    question_map = get_columns_for_all_questions_section(df_original, selected_section_inf)
    if not question_map:
        st.warning("Aucune colonne trouvée dans le fichier Excel pour cette section.")
        return

    def is_self_comparison_question(question_label, question_col):
        """Exclude comparisons where the tested question is the same concept as the comparison variable."""
        q_label_norm = normalize_question_key(question_label)
        q_col_norm = normalize_question_key(question_col)
        group_col_norm = normalize_question_key(selected_group_col)
        group_label_norm = normalize_question_key(selected_group_label)

        if q_col_norm == group_col_norm:
            return True

        if selected_group_label == "Genre":
            return q_label_norm == "genre" or q_col_norm == "genre"

        if selected_group_label == "Faculté":
            return (
                "faculte" in q_label_norm
                or "faculte" in q_col_norm
                or "institut" in q_label_norm
                or q_col_norm in {"faculte_institut", "faculte_institut_g", "faculty"}
            )

        if selected_group_label == "Campus":
            return "campus" in q_label_norm or q_col_norm in {"campus", "campus_g", "site"}

        if selected_group_label == "Niveau":
            return q_label_norm == "niveau" or q_col_norm in {"niveau", "niveau_lib"}

        return group_label_norm in q_label_norm or group_col_norm == q_col_norm

    def chi_square_question_test(question_label, question_col):
        if is_self_comparison_question(question_label, question_col):
            return None, None, "Question identique à la variable de comparaison"

        responses, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(
            df_original,
            data_inf,
            question_col
        )

        if len(eligible_index) == 0:
            return None, None, "Base applicable nulle"

        response_values = responses.map(clean_response_value)

        # In the demographic profile section, keep the comparison between demographic variables.
        # Age is treated as age groups instead of raw single-year values, otherwise it becomes unreadable
        # and most ages are excluded because of small frequencies.
        is_profile_section = selected_section_inf == "Profil des répondants"
        q_norm_for_profile = normalize_question_key(question_col)
        q_label_norm_for_profile = normalize_question_key(question_label)
        if is_profile_section and (q_norm_for_profile in {"age", "âge"} or q_label_norm_for_profile in {"age", "âge"}):
            age_numeric = pd.to_numeric(responses, errors="coerce")
            bins = [0, 20, 22, 24, 26, 29, 34, 39, 49, 150]
            labels = ["Moins de 20 ans", "20-21 ans", "22-23 ans", "24-25 ans", "26-29 ans", "30-34 ans", "35-39 ans", "40-49 ans", "50 ans et plus"]
            response_values = pd.cut(age_numeric, bins=bins, labels=labels, right=False).astype(object)

        temp = pd.DataFrame({
            "Groupe": data_inf.loc[eligible_index, selected_group_col].map(clean_response_value),
            "Réponse": response_values,
        }).dropna(subset=["Groupe", "Réponse"])

        n_valid = int(len(temp))

        group_counts = temp["Groupe"].value_counts()
        response_counts = temp["Réponse"].value_counts()

        if group_counts.shape[0] < 2:
            return None, None, "Moins de deux groupes valides"
        if response_counts.shape[0] < 2:
            return None, None, "Moins de deux modalités de réponse"

        contingency = pd.crosstab(temp["Réponse"], temp["Groupe"])
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return None, None, "Tableau croisé insuffisant"

        if stats is None:
            return None, None, "SciPy non disponible"

        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
        except Exception:
            return None, None, "Test non calculable"

        total = contingency.to_numpy().sum()
        min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
        cramers_v = np.sqrt((chi2 / total) / min_dim) if total > 0 and min_dim > 0 else np.nan

        if pd.isna(p_value):
            interpretation = "Non calculable"
        elif p_value < 0.001:
            interpretation = "Différence hautement significative"
        elif p_value < 0.01:
            interpretation = "Différence très significative"
        elif p_value < 0.05:
            interpretation = "Différence significative"
        else:
            interpretation = "Différence non significative"

        if pd.isna(cramers_v):
            effect_label = "NA"
        elif cramers_v < 0.10:
            effect_label = "Très faible"
        elif cramers_v < 0.30:
            effect_label = "Faible"
        elif cramers_v < 0.50:
            effect_label = "Modéré"
        else:
            effect_label = "Fort"

        row = {
            "Section": selected_section_inf,
            "Question": question_label,
            "Variable Excel": question_col,
            "Variable de comparaison": selected_group_label,
            "Base applicable": int(len(eligible_index)),
            "Non applicable": int(non_applicable_n),
            "N valide": n_valid,
            "Groupes": int(group_counts.shape[0]),
            "Modalités": int(response_counts.shape[0]),
            "p-value": float(p_value),
            "V de Cramer": float(cramers_v) if pd.notna(cramers_v) else np.nan,
            "Effet": effect_label,
            "Interprétation": interpretation,
            "Question filtre": clean_other_question_label(parent_col) if parent_col else "Aucune condition",
        }
        return row, temp, None

    results = []
    details = {}
    excluded = []

    for question_label, question_col in question_map.items():
        if should_exclude_question_from_presentation(question_col):
            continue
        row, temp, reason = chi_square_question_test(question_label, question_col)
        if row is not None:
            results.append(row)
            details[question_label] = temp
        else:
            excluded.append({"Question": question_label, "Variable Excel": question_col, "Raison d’exclusion": reason})

    results_df = pd.DataFrame(results)
    excluded_df = pd.DataFrame(excluded)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        insight_card("Variable comparée", selected_group_label, "Groupes de comparaison", USJ_BLUE)
    with c2:
        insight_card("Questions testées", len(results_df), "Tests calculés", USJ_GREEN if len(results_df) > 0 else USJ_RED)
    with c3:
        significant_n = int(results_df["p-value"].lt(0.05).sum()) if not results_df.empty else 0
        insight_card("Différences significatives", significant_n, "p-value < 0.050", USJ_GREEN if significant_n > 0 else USJ_GOLD)
    with c4:
        insight_card("Questions exclues", len(excluded_df), "Base nulle ou auto-comparaison", USJ_ORANGE if len(excluded_df) > 0 else USJ_GREEN)

    if results_df.empty:
        st.warning("Aucune question de cette section ne peut être testée avec les filtres sélectionnés.")
        if not excluded_df.empty:
            with st.expander("Voir les questions exclues"):
                st.dataframe(excluded_df, use_container_width=True, hide_index=True)
        return

    results_df = results_df.sort_values(["p-value", "V de Cramer"], ascending=[True, False]).reset_index(drop=True)

    # The inferential page remains simple by default.
    # Detailed statistical tables and visual comparisons are available only through buttons,
    # so readers are not overloaded unless they choose to go deeper.

    significant = results_df[results_df["p-value"] < 0.05]
    if not significant.empty:
        strongest = significant.iloc[0]
        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_BLUE};">Lecture inférentielle</span><br>
            La différence la plus marquée concerne <b>{html_escape(str(strongest['Question']))}</b> selon
            <b>{html_escape(selected_group_label)}</b>, avec une p-value de <b>{strongest['p-value']:.4f}</b>
            et un V de Cramer de <b>{strongest['V de Cramer']:.3f}</b>. Les tableaux statistiques et les comparaisons visuelles sont masqués par défaut afin de garder la page simple pour les lecteurs.
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )
    else:
        summary_box(
            f"""
            <span style="font-size:20px; font-weight:800; color:{USJ_GOLD};">Lecture inférentielle</span><br>
            Aucune question de la section <b>{html_escape(selected_section_inf)}</b> ne présente une différence statistiquement significative
            selon <b>{html_escape(selected_group_label)}</b> au seuil de 0.050.
            """,
            color=USJ_GOLD,
            background="#FFF8F0"
        )

    summary_button_key = f"inferential_show_summary_{selected_group_label}_{selected_section_inf}"
    if summary_button_key not in st.session_state:
        st.session_state[summary_button_key] = False

    if st.button("Afficher / masquer la synthèse statistique", key=f"btn_{summary_button_key}", use_container_width=True):
        st.session_state[summary_button_key] = not st.session_state[summary_button_key]

    if st.session_state[summary_button_key]:
        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Synthèse des tests par question</h3>", unsafe_allow_html=True)
        display_results = results_df.copy()
        display_results["p-value"] = display_results["p-value"].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
        display_results["V de Cramer"] = display_results["V de Cramer"].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
        st.dataframe(
            display_results[[
                "Question", "Variable de comparaison", "N valide", "Groupes", "Modalités",
                "p-value", "V de Cramer", "Effet", "Interprétation"
            ]],
            use_container_width=True,
            hide_index=True
        )

    # The detailed visual comparisons are shown automatically.
    # Only the statistical synthesis table remains behind a button to keep the page readable.
    detail_source = results_df.sort_values(["p-value", "V de Cramer"], ascending=[True, False]).copy()

    st.markdown(
        f"<h3 style='color:{USJ_BLUE};'>Comparaisons détaillées par question</h3>",
        unsafe_allow_html=True
    )

    for _, selected_row in detail_source.iterrows():
        selected_question_detail = selected_row["Question"]
        detail_temp = details[selected_question_detail].copy()
        dist = detail_temp.groupby(["Groupe", "Réponse"]).size().reset_index(name="N")
        dist["Pourcentage"] = dist.groupby("Groupe")["N"].transform(lambda x: x / x.sum() * 100)

        with st.expander(f"{selected_question_detail} | p-value = {selected_row['p-value']:.4f}", expanded=True):
            positive_group_rows = []
            for grp_name, grp_dist in dist.groupby("Groupe"):
                positive_summary = get_positive_scale_summary(grp_dist[["Réponse", "N", "Pourcentage"]].copy())
                if positive_summary:
                    positive_group_rows.append({
                        "Groupe": grp_name,
                        "Label": positive_summary.get("label", "Réponses positives"),
                        "Subtitle": positive_summary.get("subtitle", "Total des réponses positives"),
                        "N positif": int(positive_summary.get("N positif", 0)),
                        "N total": int(positive_summary.get("N total", 0)),
                        "Pourcentage positif": float(positive_summary.get("Pourcentage positif", np.nan)),
                    })

            if positive_group_rows:
                positive_group_df = pd.DataFrame(positive_group_rows).sort_values("Pourcentage positif", ascending=False)
                positive_label = positive_group_df["Label"].iloc[0]
                positive_subtitle = positive_group_df["Subtitle"].iloc[0]
                st.markdown(
                    f"<h4 style='color:{USJ_BLUE}; margin-top:6px;'>{html_escape(positive_label)} selon {html_escape(selected_group_label)}</h4>"
                    f"<div style='color:#667085; font-size:13px; margin-top:-8px; margin-bottom:10px;'>{html_escape(positive_subtitle)}. Les modalités originales restent affichées dans le graphique et le tableau ci-dessous.</div>",
                    unsafe_allow_html=True
                )
                kpi_cols = st.columns(min(4, len(positive_group_df)))
                for k, (_, pos_row) in enumerate(positive_group_df.iterrows()):
                    with kpi_cols[k % len(kpi_cols)]:
                        color = kpi_color_percentage(pos_row["Pourcentage positif"])
                        st.markdown(
                            f"""
                            <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {color};border-radius:16px;padding:12px 14px;margin:4px 0 12px 0;box-shadow:0 4px 12px rgba(0,0,0,0.04);font-family:Candara, Arial, sans-serif;'>
                                <div style='font-size:13px;font-weight:900;color:{USJ_BLUE};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{html_escape(str(pos_row['Groupe']))}</div>
                                <div style='font-size:25px;font-weight:900;color:{color};margin-top:5px;'>{safe_pct(pos_row['Pourcentage positif'])}</div>
                                <div style='font-size:12px;color:{USJ_BLUE};font-weight:800;margin-top:3px;'>{int(pos_row['N positif']):,} / {int(pos_row['N total']):,}</div>
                            </div>
                            """.replace(",", " "),
                            unsafe_allow_html=True
                        )

            use_table_only = (dist["Réponse"].nunique() > 6) or (dist["Groupe"].nunique() > 4)

            if not use_table_only:
                fig = px.bar(
                    dist,
                    x="Pourcentage",
                    y="Réponse",
                    color="Groupe",
                    orientation="h",
                    barmode="group",
                    text="Pourcentage",
                    color_discrete_sequence=[USJ_BLUE, USJ_RED, USJ_GOLD, USJ_BLUE_2, USJ_DARK_RED, "#B49C88", "#5E6C84"],
                    hover_data={"N": True, "Pourcentage": ":.2f"},
                    title=f"Distribution des réponses selon {selected_group_label}"
                )
                fig.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside",
                    marker_line_color="white",
                    marker_line_width=1.1,
                    cliponaxis=False
                )
                fig.update_layout(
                    xaxis_title="Pourcentage des réponses valides dans chaque groupe",
                    yaxis_title="",
                    legend_title=selected_group_label,
                    margin=dict(l=40, r=90, t=90, b=45),
                )
                theme_layout(fig, height=max(390, 42 * dist["Réponse"].nunique()), showlegend=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False}, key=f"inferential_detail_fig_{selected_group_label}_{selected_section_inf}_{re.sub(r'[^A-Za-z0-9_]+', '_', str(selected_question_detail))}")
            else:
                st.markdown(
                    f"""
                    <div style='background:#F7F9FC;border-left:6px solid {USJ_BLUE};border-radius:14px;padding:12px 16px;margin:8px 0 14px 0;font-family:Candara, Arial, sans-serif;'>
                        <b>Lecture adaptée :</b> cette question comporte plusieurs modalités ou groupes. Le graphique est remplacé par un tableau interactif afin de garder une lecture claire et professionnelle.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            pivot_pct = dist.pivot_table(index="Réponse", columns="Groupe", values="Pourcentage", aggfunc="sum").fillna(0)
            pivot_n = dist.pivot_table(index="Réponse", columns="Groupe", values="N", aggfunc="sum").fillna(0)
            row_order = pivot_pct.mean(axis=1).sort_values(ascending=False).index
            pivot_pct = pivot_pct.loc[row_order]
            pivot_n = pivot_n.loc[row_order]

            display_rows = []
            for resp in pivot_pct.index:
                row = {"Réponse": resp}
                for grp in pivot_pct.columns:
                    row[str(grp)] = f"{pivot_pct.loc[resp, grp]:.2f}% ({int(pivot_n.loc[resp, grp])})"
                display_rows.append(row)

            st.markdown(f"<h4 style='color:{USJ_BLUE};'>Tableau comparatif par {html_escape(selected_group_label.lower())}</h4>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    with st.expander("Questions exclues des tests inférentiels", expanded=False):
        if excluded_df.empty:
            st.info("Aucune question exclue pour cette sélection.")
        else:
            st.dataframe(excluded_df, use_container_width=True, hide_index=True)


# =====================================================
# Page 6 - Printable synthetic faculty report
# =====================================================

def apply_current_filters_without_faculty(data):
    base = data.copy()
    if year != "Tous":
        base = base[base["Year"].astype(str) == str(year)]
    if genre != "Tous" and "Genre" in base.columns:
        base = base[base["Genre"].astype(str) == str(genre)]
    if CAMPUS_COLUMN and campus != "Tous" and CAMPUS_COLUMN in base.columns:
        base = base[base[CAMPUS_COLUMN].astype(str) == str(campus)]
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


# =====================================================
# Additional survey questions helpers
# =====================================================


def get_excluded_non_question_columns():
    """Columns that should not be treated as questionnaire items."""
    base_cols = {
        "Year", "Année", "Genre", "Faculté_Institut_g", "Faculté", "Faculté_Institut", "Faculty", "Institut",
        "Cursus", "Campus", "campus", "Campus_g", "Campus principal", "Campus_principal", "Site", "site", "Niveau", "Niveau_Lib", "startlanguage", "StartLanguage", "Language", "Langue", "Age",
        "Date", "Horodateur", "Timestamp", "Institution", "Responsable", "Email", "Adresse e-mail", "ID", "Id", "id",
        "Code", "Nom", "Prénom", "StartDate", "EndDate", "Status", "IPAddress", "Progress", "Duration",
        "Finished", "RecordedDate", "ResponseId", "RecipientLastName", "RecipientFirstName", "RecipientEmail",
        "ExternalReference", "LocationLatitude", "LocationLongitude", "DistributionChannel", "UserLanguage"
    }
    base_cols.update(SCORE_COLUMNS)
    return base_cols


def get_used_dashboard_question_columns():
    """Original questionnaire columns already used in KPIs/components."""
    used = set()
    for item_list in components.values():
        used.update([str(x).strip() for x in item_list])
    for q in [q42, q43, q26, q27]:
        if q:
            used.add(str(q).strip())
    return used


def is_probable_survey_question(col_name):
    """Detect actual survey-question columns dynamically from the Excel file.

    This intentionally captures numbered questions such as:
    3- Dans votre institution..., 6- Etudié à l'étranger..., 14_a-..., etc.
    """
    import re
    c = str(col_name).strip()
    if not c:
        return False
    c_lower = c.lower()

    # Strong signal: survey item starts with a number, optionally followed by _a, a, -, or spaces.
    if re.match(r"^\s*\d+\s*[_a-zA-Z]?\s*[-–—]", c):
        return True
    if re.match(r"^\s*\d+\s*[_a-zA-Z]\s*[-–—]", c):
        return True
    if re.match(r"^\s*\d+[_a-zA-Z]+\s*[-–—]", c):
        return True

    # Secondary signal: looks like a survey wording even without a numeric prefix.
    question_terms = [
        "satisf", "recommand", "tuteur", "mobilité", "etranger", "étranger", "échange", "stage",
        "emploi", "travail", "programme", "parcours", "université", "institution", "faculté", "institut",
        "école", "enseignement", "service", "activité", "campus", "bibliothèque", "laboratoire", "frais",
        "avez-vous", "vous a-t-on", "dans votre", "durant votre", "après l’obtention", "après l'obtention", "?"
    ]
    return any(term in c_lower for term in question_terms)


def classify_other_question(col_name, series=None):
    c = str(col_name).lower()
    if any(k in c for k in ["tuteur", "orientation", "conseil", "encadrement"]):
        return "Accompagnement / tutorat"
    if any(k in c for k in ["étranger", "etranger", "mobilité", "mobilite", "échange", "echange"]):
        return "Mobilité internationale"
    if any(k in c for k in ["stage", "emploi", "travail", "carrière", "carriere", "insertion"]):
        return "Insertion / parcours professionnel"
    if any(k in c for k in ["admission", "inscription", "administratif", "dossier"]):
        return "Processus administratifs"
    if any(k in c for k in ["langue", "language"]):
        return "Langues / profil"
    if any(k in c for k in ["commentaire", "remarque", "suggestion", "précisez", "precisez", "autre"]):
        return "Questions complémentaires détaillées"
    if series is not None:
        nunique = series.map(clean_response_value).dropna().nunique()
        if nunique > 30:
            return "Questions complémentaires détaillées"
    return "Autres informations complémentaires"


def get_other_question_columns(original_data):
    """Return all survey questions not already used in the main indicators/components."""
    excluded = get_excluded_non_question_columns().union(get_used_dashboard_question_columns())
    candidate_cols = []

    for col in original_data.columns:
        col_str = str(col).strip()
        col_norm = normalize_question_key(col_str)

        if should_exclude_question_from_presentation(col_str):
            continue

        if col_str in excluded:
            continue

        if col_norm in {"faculte_institut", "faculte institut", "faculte_institut_g", "faculty", "faculte", "institut"}:
            continue

        if "faculte_institut" in col_norm or col_norm.startswith("faculte institut"):
            continue

        # Keep only one dropdown item for Q44 financing.
        # 44_a is used as the representative option, while the chart uses all Q44 items.
        if any(col_norm.startswith(normalize_question_key(prefix)) for prefix in [
            "44_b-", "44_c-", "44_d-", "44_e-", "44_f-", "44_g-"
        ]):
            continue

        if col_str.startswith("Score "):
            continue

        if original_data[col].dropna().empty:
            continue

        if not is_probable_survey_question(col_str):
            continue

        candidate_cols.append(col_str)

    import re

    def sort_key(x):
        m = re.match(r"^\s*(\d+)", str(x))
        return (int(m.group(1)) if m else 9999, str(x))

    return sorted(candidate_cols, key=sort_key)

    import re
    def sort_key(x):
        m = re.match(r"^\s*(\d+)", str(x))
        return (int(m.group(1)) if m else 9999, str(x))
    return sorted(candidate_cols, key=sort_key)


def get_other_question_inventory(original_data, coded_filter_data):
    rows = []
    for col in get_other_question_columns(original_data):
        s, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(original_data, coded_filter_data, col)
        valid = s.dropna()
        eligible_n = int(len(eligible_index))
        missing_n = int(s.isna().sum()) if eligible_n > 0 else 0
        missing_pct = (missing_n / eligible_n * 100) if eligible_n > 0 else np.nan
        rows.append({
            "Catégorie": classify_other_question(col, s),
            "Question": col,
            "Question affichée": clean_other_question_label(col),
            "Question filtre": clean_other_question_label(parent_col) if parent_col else "Aucun filtre conditionnel",
            "Base applicable": eligible_n,
            "Non applicable": non_applicable_n,
            "N valide": int(valid.shape[0]),
            "Données manquantes (%)": missing_pct,
            "Modalités": int(valid.nunique()) if not valid.empty else 0,
            "Type": "Fermée / catégorielle" if (not valid.empty and valid.nunique() <= 30) else "Ouverte / texte libre",
        })
    return pd.DataFrame(rows)


def clean_response_value(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if text.lower() in ["nan", "none", "nat", "", "<na>"]:
        return np.nan
    return text


def build_other_question_distribution(original_data, coded_filter_data, question_col):
    if question_col not in original_data.columns:
        return pd.DataFrame()

    responses, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(original_data, coded_filter_data, question_col)
    if len(eligible_index) == 0:
        return pd.DataFrame()

    temp = pd.DataFrame({
        "Année": coded_filter_data.loc[eligible_index, "Year"].astype(str).values,
        "Réponse": responses.values,
    })
    temp = temp.dropna(subset=["Réponse"])
    if temp.empty:
        return pd.DataFrame()
    dist = temp.groupby(["Année", "Réponse"]).size().reset_index(name="N")
    dist["Pourcentage"] = dist.groupby("Année")["N"].transform(lambda x: x / x.sum() * 100)
    return dist




def clean_question_for_narrative(question_label):
    """Return a readable survey statement/question without technical prefixes."""
    text = str(question_label).strip()
    text = re.sub(r"^\s*\d+[a-zA-Z_]*\s*[-–—]\s*", "", text)
    text = re.sub(r"^\s*Evaluation\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_other_question_narrative(question_label, overall_distribution, n_valid, eligible_n, parent_col=None, dependency_label=None, non_applicable_n=0):
    """Build a professional, data-driven narrative for complementary questions."""
    if overall_distribution is None or overall_distribution.empty:
        return "Aucune distribution exploitable n’est disponible pour cette question avec les filtres sélectionnés."

    dist = overall_distribution.sort_values("Pourcentage", ascending=False).copy()
    question_text = clean_question_for_narrative(question_label)
    is_question = question_text.endswith("?")
    respondent_word = "répondants concernés" if parent_col else "répondants"

    first = dist.iloc[0]
    if is_question:
        opening = (
            f"À la question <b>« {html_escape(question_text)} »</b>, "
            f"<b>{first['Pourcentage']:.2f}%</b> des {respondent_word} ont répondu "
            f"<b>« {html_escape(first['Réponse'])} »</b>"
        )
    else:
        opening = (
            f"Pour l’énoncé <b>« {html_escape(question_text)} »</b>, "
            f"<b>{first['Pourcentage']:.2f}%</b> des {respondent_word} ont indiqué "
            f"<b>« {html_escape(first['Réponse'])} »</b>"
        )

    follow_parts = []
    for _, row in dist.iloc[1:4].iterrows():
        follow_parts.append(
            f"<b>{row['Pourcentage']:.2f}%</b> <b>« {html_escape(row['Réponse'])} »</b>"
        )

    if len(follow_parts) == 1:
        continuation = f", suivis de {follow_parts[0]}."
    elif len(follow_parts) == 2:
        continuation = f", suivis de {follow_parts[0]} et de {follow_parts[1]}."
    elif len(follow_parts) >= 3:
        continuation = f", suivis de {follow_parts[0]}, de {follow_parts[1]} et de {follow_parts[2]}."
    else:
        continuation = "."

    residual_text = ""
    if len(dist) > 4:
        residual = dist.iloc[4:]["Pourcentage"].sum()
        residual_text = f" Les autres modalités regroupent <b>{residual:.2f}%</b> des réponses valides."

    base_text = (
        f" La lecture repose sur <b>{n_valid}</b> réponses valides"
        f" sur une base applicable de <b>{eligible_n}</b> répondants."
    )

    conditional_text = ""
    if parent_col:
        conditional_text = (
            f" Cette base est conditionnelle : elle exclut <b>{non_applicable_n}</b> répondants non concernés par la question filtre "
            f"<b>« {html_escape(clean_question_for_narrative(dependency_label or parent_col))} »</b>."
        )

    dominant_share = float(first["Pourcentage"]) if pd.notna(first["Pourcentage"]) else np.nan
    if pd.notna(dominant_share) and dominant_share >= 50:
        decision_sentence = (
            " Cette concentration autour de la modalité dominante indique une tendance relativement claire, "
            "qui peut être mobilisée comme signal prioritaire dans l’analyse du périmètre sélectionné."
        )
    else:
        decision_sentence = (
            " La distribution montre une répartition relativement partagée des réponses, ce qui invite à interpréter le résultat avec nuance "
            "et à examiner les écarts par année, faculté ou niveau lorsque ces filtres sont utilisés."
        )

    return opening + continuation + residual_text + base_text + conditional_text + decision_sentence


def summarize_other_questions_for_report(original_data, coded_filter_data, max_questions=14):
    """Compact executive summary of complementary questions for the printable report.

    For conditional questions, the denominator is the applicable base only.
    Example: Q9a/Q9b/Q9c/Q9d are computed only among respondents who answered Oui to Q9.
    """
    rows = []
    priority_terms = [
        "tuteur", "mobilité", "mobilite", "étranger", "etranger", "échange", "echange",
        "stage", "emploi", "travail", "insertion", "admission", "administratif", "parcours"
    ]
    other_cols = get_other_question_columns(original_data)
    for col in other_cols:
        if col not in original_data.columns:
            continue
        series, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(original_data, coded_filter_data, col)
        series = series.dropna()
        if series.empty:
            continue
        n_valid = int(series.shape[0])
        unique_n = int(series.nunique())
        if unique_n < 2 or unique_n > 30:
            continue
        counts = series.value_counts(dropna=True)
        top_resp = counts.index[0]
        top_pct = counts.iloc[0] / counts.sum() * 100
        q_lower = str(col).lower()
        priority_score = 0
        if any(term in q_lower for term in priority_terms):
            priority_score += 1000
        if str(col).strip().startswith(("3-", "3 -", "6-", "6 -", "9-", "9a-", "9b_", "9c-")):
            priority_score += 1200
        priority_score += min(n_valid, 500)
        rows.append({
            "Catégorie": classify_other_question(col, series),
            "Question": col,
            "Question affichée": clean_other_question_label(col),
            "Question filtre": clean_other_question_label(parent_col) if parent_col else "Aucun filtre conditionnel",
            "Base applicable": int(len(eligible_index)),
            "Non applicable": int(non_applicable_n),
            "N valide": n_valid,
            "Réponse dominante": top_resp,
            "Pourcentage": top_pct,
            "Nombre de modalités": unique_n,
            "Priorité": priority_score,
        })
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out = out.sort_values(["Priorité", "N valide", "Pourcentage"], ascending=[False, False, False]).head(max_questions)
    return out.drop(columns=["Priorité"], errors="ignore")



# =====================================================
# Page - Demographic profile
# =====================================================

def resolve_first_existing_column(data, candidates):
    for col in candidates:
        if col in data.columns:
            return col
    return None


def make_frequency_table(data, col, top_n=None, include_other=True):
    if col is None or col not in data.columns:
        return pd.DataFrame()
    s = data[col].map(clean_response_value).dropna()
    if s.empty:
        return pd.DataFrame()
    out = s.value_counts().reset_index()
    out.columns = ["Modalité", "N"]
    out["Pourcentage"] = out["N"] / out["N"].sum() * 100
    out = out.sort_values(["N", "Modalité"], ascending=[False, True]).reset_index(drop=True)
    if top_n is not None and len(out) > top_n:
        if include_other:
            top = out.head(top_n).copy()
            other = pd.DataFrame({
                "Modalité": ["Autres"],
                "N": [int(out.iloc[top_n:]["N"].sum())],
                "Pourcentage": [float(out.iloc[top_n:]["Pourcentage"].sum())]
            })
            out = pd.concat([top, other], ignore_index=True)
        else:
            out = out.head(top_n).copy()
    return out.reset_index(drop=True)


def render_professional_frequency_table(
    df,
    title,
    note=None,
    max_rows=None,
    show_rank=False,
    sort_by_frequency=True
):
    if df is None or df.empty:
        st.warning(f"Aucune donnée disponible pour {title}.")
        return

    table = df.copy()
    if max_rows is not None:
        table = table.head(max_rows).copy()

    if "Pourcentage" in table.columns:
        table["Pourcentage"] = pd.to_numeric(table["Pourcentage"], errors="coerce")

    if sort_by_frequency and "Pourcentage" in table.columns:
        table = table.sort_values(["Pourcentage", "N"], ascending=[False, False]) if "N" in table.columns else table.sort_values("Pourcentage", ascending=False)

    table = table.reset_index(drop=True)

    if show_rank:
        table.insert(0, "Rang", range(1, len(table) + 1))

    display = table.copy()
    if "Pourcentage" in display.columns:
        display["Pourcentage"] = display["Pourcentage"].map(lambda x: "" if pd.isna(x) else f"{x:.2f}%")
    if "N" in display.columns:
        display["N"] = display["N"].map(lambda x: "" if pd.isna(x) else f"{int(x):,}".replace(",", " "))

    numeric_cols = ["N", "Pourcentage"]

    header_html = "".join(
        f"<th style='text-align:{'right' if col in numeric_cols else 'left'};'>{html_escape(col)}</th>"
        for col in display.columns
    )

    body_html = ""
    for _, row in display.iterrows():
        cells = []
        for col in display.columns:
            align = "right" if col in numeric_cols else "left"
            weight = "800" if col in ["N", "Pourcentage"] else "500"
            cells.append(f"<td style='text-align:{align}; font-weight:{weight};'>{html_escape(row[col])}</td>")
        body_html += "<tr>" + "".join(cells) + "</tr>"

    note_html = f"<div style='font-size:13px;color:#667085;margin-top:6px;'>{note}</div>" if note else ""

    st.markdown(
        f"""
        <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-radius:18px;padding:18px 20px;margin:18px 0;box-shadow:0 6px 18px rgba(0,0,0,0.05);'>
            <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:10px;'>
                <div>
                    <div style='font-size:20px;font-weight:900;color:{USJ_BLUE};font-family:Candara, Arial, sans-serif;'>{html_escape(title)}</div>
                    {note_html}
                </div>
                <div style='background:{USJ_LIGHT_BLUE};color:{USJ_BLUE};border-radius:999px;padding:7px 12px;font-size:13px;font-weight:800;'>
                    {len(table)} modalités
                </div>
            </div>
            <table style='width:100%;border-collapse:collapse;font-family:Candara, Arial, sans-serif;font-size:14px;'>
                <thead>
                    <tr style='background:{USJ_BLUE};color:white;'>{header_html}</tr>
                </thead>
                <tbody>{body_html}</tbody>
            </table>
        </div>
        <style>
            table td, table th {{ padding:10px 12px; border-bottom:1px solid #E6ECF3; vertical-align:top; }}
            table tbody tr:nth-child(even) td {{ background:#FBFCFE; }}
            table tbody tr:hover td {{ background:#F2F6FF; }}
        </style>
        """,
        unsafe_allow_html=True
    )


def make_age_group_table(age_series):
    age_numeric = pd.to_numeric(age_series, errors="coerce").dropna()
    if age_numeric.empty:
        return pd.DataFrame()

    bins = [0, 20, 22, 24, 26, 29, 34, 39, 49, 150]
    labels = ["Moins de 20 ans", "20-21 ans", "22-23 ans", "24-25 ans", "26-29 ans", "30-34 ans", "35-39 ans", "40-49 ans", "50 ans et plus"]
    grouped = pd.cut(age_numeric, bins=bins, labels=labels, right=False)
    out = grouped.value_counts().reindex(labels).dropna().reset_index()
    out.columns = ["Modalité", "N"]
    out = out[out["N"] > 0].copy()
    out["Pourcentage"] = out["N"] / out["N"].sum() * 100
    return out.reset_index(drop=True)


def make_diploma_faculty_table(data, diplome_col, fac_col, top_n=None):
    if diplome_col is None or diplome_col not in data.columns:
        return pd.DataFrame()
    temp = data[[diplome_col] + ([fac_col] if fac_col and fac_col in data.columns else [])].copy()
    temp[diplome_col] = temp[diplome_col].map(clean_response_value)
    if fac_col and fac_col in temp.columns:
        temp[fac_col] = temp[fac_col].map(clean_response_value)
    else:
        temp["Faculté / Institut"] = "Non disponible"
        fac_col = "Faculté / Institut"
    temp = temp.dropna(subset=[diplome_col])
    if temp.empty:
        return pd.DataFrame()

    rows = []
    total = len(temp)
    grouped = temp.groupby([diplome_col, fac_col], dropna=False).size().reset_index(name="N")
    grouped["Pourcentage"] = grouped["N"] / total * 100
    grouped = grouped.sort_values(["N", diplome_col], ascending=[False, True])
    for _, row in grouped.iterrows():
        rows.append({
            "Intitulé diplôme": row[diplome_col],
            "Faculté / Institut": row[fac_col] if pd.notna(row[fac_col]) else "Non renseigné",
            "N": int(row["N"]),
            "Pourcentage": float(row["Pourcentage"]),
        })
    out = pd.DataFrame(rows)
    if top_n is not None:
        out = out.head(top_n).copy()
    return out.reset_index(drop=True)


def demographic_bar_chart(freq, title, orientation="h", height=430):
    if freq.empty:
        st.warning(f"Aucune donnée disponible pour {title}.")
        return
    plot_df = freq.copy()
    if orientation == "h":
        plot_df = plot_df.sort_values("Pourcentage", ascending=True)
        fig = px.bar(
            plot_df,
            x="Pourcentage",
            y="Modalité",
            orientation="h",
            text="Pourcentage",
            color="Pourcentage",
            color_continuous_scale=[[0, "#EAF2FF"], [0.5, "#7FA6D9"], [1, USJ_BLUE]],
            hover_data={"N": True, "Pourcentage": ":.2f"},
            title=title
        )
        fig.update_layout(xaxis_title="Pourcentage", yaxis_title="")
    else:
        fig = px.bar(
            plot_df,
            x="Modalité",
            y="Pourcentage",
            text="Pourcentage",
            color="Pourcentage",
            color_continuous_scale=[[0, "#EAF2FF"], [0.5, "#7FA6D9"], [1, USJ_BLUE]],
            hover_data={"N": True, "Pourcentage": ":.2f"},
            title=title
        )
        fig.update_layout(xaxis_title="", yaxis_title="Pourcentage")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", marker_line_color="white", marker_line_width=1)
    fig.update_layout(coloraxis_showscale=False, margin=dict(l=30, r=70, t=70, b=50))
    theme_layout(fig, height=height, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def page_demographics():
    section_header(
        "Profil des répondants selon le genre, l’âge, le campus, la faculté ou institut, le niveau et l’intitulé du diplôme."
    )

    selected_year, data_demo, original_demo = get_single_year_context("demographics")

    if data_demo.empty:
        st.warning("Aucune donnée disponible pour l’année et les filtres sélectionnés.")
        return

    genre_col = resolve_first_existing_column(data_demo, ["Genre"])
    age_col = resolve_first_existing_column(data_demo, ["Age", "Âge"])
    fac_col = resolve_first_existing_column(data_demo, ["Faculté_Institut", "Faculté_Institut_g", "Faculté", "Institut"])
    campus_col = resolve_first_existing_column(data_demo, ["Campus", "campus", "Campus_g", "Campus principal", "Campus_principal", "Site", "site"])
    niveau_col = resolve_first_existing_column(data_demo, ["Niveau", "Niveau_Lib"])
    diplome_col = resolve_first_existing_column(data_demo, ["Intitulé Diplôme", "Intitulé_Diplôme", "Intitulé Diplome", "Diplôme", "Intitule Diplome"])

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        insight_card("Année affichée", selected_year, "Analyse non agrégée", USJ_BLUE)
    with k2:
        insight_card("Répondants", len(data_demo), "Base filtrée", USJ_GREEN)
    with k3:
        fac_n = data_demo[fac_col].map(clean_response_value).dropna().nunique() if fac_col else 0
        insight_card("Facultés / Instituts", fac_n, "Modalités observées", USJ_BLUE_2)
    with k4:
        campus_n = data_demo[campus_col].map(clean_response_value).dropna().nunique() if campus_col else 0
        insight_card("Campus", campus_n, "Modalités observées", USJ_ORANGE)
    with k5:
        diplome_n = data_demo[diplome_col].map(clean_response_value).dropna().nunique() if diplome_col else 0
        insight_card("Diplômes", diplome_n, "Intitulés distincts", USJ_GOLD)

    st.markdown("<br>", unsafe_allow_html=True)

    genre_freq = make_frequency_table(data_demo, genre_col)
    age_numeric = pd.to_numeric(data_demo[age_col], errors="coerce") if age_col else pd.Series(dtype=float)
    age_group_freq = make_age_group_table(age_numeric) if age_col else pd.DataFrame()
    fac_freq = make_frequency_table(data_demo, fac_col, top_n=18, include_other=False)
    campus_freq = make_frequency_table(data_demo, campus_col)
    niveau_freq = make_frequency_table(data_demo, niveau_col)
    diplome_fac_table = make_diploma_faculty_table(data_demo, diplome_col, fac_col)

    c_left, c_right = st.columns([1, 1])

    with c_left:
        if not genre_freq.empty:
            fig_genre = px.pie(
                genre_freq,
                names="Modalité",
                values="N",
                hole=0.55,
                color_discrete_sequence=PLOTLY_SEQ,
                title="Répartition des répondants par genre"
            )
            fig_genre.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="%{label}<br>N=%{value}<br>%{percent}<extra></extra>"
            )
            theme_layout(fig_genre, height=430, showlegend=True)
            st.plotly_chart(fig_genre, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("Aucune donnée disponible pour le genre.")

    with c_right:
        if not age_group_freq.empty:
            plot_age = age_group_freq.copy()
            fig_age = px.bar(
                plot_age,
                x="Modalité",
                y="Pourcentage",
                text="Pourcentage",
                color="Pourcentage",
                color_continuous_scale=[[0, "#EAF2FF"], [0.5, "#7FA6D9"], [1, USJ_BLUE]],
                hover_data={"N": True, "Pourcentage": ":.2f"},
                title="Distribution de l’âge des répondants"
            )
            fig_age.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                marker_line_color="white",
                marker_line_width=1.2,
                cliponaxis=False
            )
            fig_age.update_layout(
                xaxis_title="Tranche d’âge",
                yaxis_title="Pourcentage des répondants",
                coloraxis_showscale=False,
                margin=dict(l=40, r=60, t=75, b=95)
            )
            fig_age.update_xaxes(tickangle=-25)
            theme_layout(fig_age, height=430, showlegend=False)
            st.plotly_chart(fig_age, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f"""
                <div style='background:#F7F9FC;border-left:6px solid {USJ_BLUE};border-radius:14px;padding:12px 16px;margin-top:-6px;'>
                    <b>Âge moyen :</b> {safe_num(age_numeric.mean(), 1)} ans &nbsp; | &nbsp; <b>Âge médian :</b> {safe_num(age_numeric.median(), 1)} ans
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("Aucune donnée numérique disponible pour l’âge.")

    st.divider()

    if campus_col:
        demographic_bar_chart(campus_freq, "Répartition par campus", orientation="h", height=max(360, 38 * len(campus_freq)))
        st.divider()

    c_fac, c_niveau = st.columns([1.35, 1])
    with c_fac:
        demographic_bar_chart(fac_freq, "Répartition par faculté / institut", orientation="h", height=max(470, 30 * len(fac_freq)))

    with c_niveau:
        demographic_bar_chart(niveau_freq, "Répartition par niveau", orientation="v", height=470)

    st.divider()

    st.markdown(f"<h3 style='color:{USJ_BLUE};'>Tableaux démographiques détaillés</h3>", unsafe_allow_html=True)
    summary_box(
        """
        Les tableaux ci-dessous remplacent le graphique des intitulés de diplôme afin de permettre une lecture plus précise.
        Les tableaux de fréquences sont triés automatiquement du pourcentage le plus élevé au plus faible, sauf l’âge qui est présenté selon l’ordre naturel des tranches. Pour les diplômes, la faculté ou l’institut associé est affiché à côté de chaque intitulé.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    t1, t2 = st.columns([1, 1])
    with t1:
        render_professional_frequency_table(
            genre_freq,
            "Genre des répondants",
            "Effectifs et pourcentages calculés sur les réponses valides."
        )
    with t2:
        render_professional_frequency_table(
            age_group_freq,
            "Âge des répondants par tranche",
            "Les pourcentages sont calculés sur les âges valides. Le tableau est trié selon l’ordre naturel des tranches d’âge.",
            show_rank=False,
            sort_by_frequency=False
        )

    if campus_col:
        render_professional_frequency_table(
            campus_freq,
            "Campus",
            "Répartition par campus dans l’année sélectionnée."
        )

    t3, t4 = st.columns([1.2, 1])
    with t3:
        render_professional_frequency_table(
            fac_freq,
            "Faculté / Institut",
            "Tableau trié du poids le plus élevé au plus faible."
        )
    with t4:
        render_professional_frequency_table(
            niveau_freq,
            "Niveau d’études",
            "Répartition par niveau dans l’année sélectionnée."
        )

    render_professional_frequency_table(
        diplome_fac_table,
        "Intitulés de diplôme avec faculté / institut associé",
        "Chaque ligne correspond à un couple diplôme + faculté/institut, trié du plus fréquent au moins fréquent."
    )


# =====================================================
# Page 5 - Results of all questions before KPI calculation
# =====================================================

DEMOGRAPHIC_FIELDS = {
    "Genre": ["Genre"],
    "Age": ["Age", "Âge"],
    "Faculté / Institut": ["Faculté_Institut", "Faculté_Institut_g", "Faculté", "Institut"],
    "Campus": ["Campus", "campus", "Campus_g", "Campus principal", "Campus_principal", "Site", "site"],
    "Niveau": ["Niveau", "Niveau_Lib"],
    "Intitulé Diplôme": ["Intitulé Diplôme", "Intitulé_Diplôme", "Intitulé Diplome", "Intitule Diplome", "Diplôme", "Diplome"],
}

ALL_SURVEY_SECTION_NUMBERS = {
    "Profil des répondants": "DEMOGRAPHICS",
    "Satisfaction dans l’expérience académique": [1, 2],
    "Politique d’accompagnement": [3, 4],
    "Développement des compétences et mobilité internationale": [5, 6, 7],
    "Plateforme Alumni et expérience de stage": [8, 9],
    "Apprentissage de l’anglais": [10, 11],
    "Service de l’insertion professionnelle de l’USJ": [12, 13, 14, 15],
    "Perspectives d’avenir": [16, 17, 18, 19, 20, 21, 22, 23],
    "Évaluation des services, des infrastructures et de la satisfaction globale à l’USJ": list(range(24, 44)),
    "Financement des études à l’USJ": [44, 45, 46],
    "Propositions et commentaires": [47],
}


def extract_question_number(col_name):
    text = str(col_name).strip()
    match = re.match(r"^\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def find_existing_demographic_columns(data):
    found = {}
    normalized_cols = {normalize_question_key(col): col for col in data.columns}

    for display_name, possible_cols in DEMOGRAPHIC_FIELDS.items():
        selected_col = None
        for col in possible_cols:
            if col in data.columns:
                selected_col = col
                break
            norm_col = normalize_question_key(col)
            if norm_col in normalized_cols:
                selected_col = normalized_cols[norm_col]
                break
        if selected_col is not None:
            found[display_name] = selected_col

    return found


def get_columns_for_all_questions_section(original_data, section_name):
    section_spec = ALL_SURVEY_SECTION_NUMBERS.get(section_name)

    if section_spec == "DEMOGRAPHICS":
        return find_existing_demographic_columns(original_data)

    selected_numbers = set(section_spec)
    cols = []

    for col in original_data.columns:
        col_str = str(col).strip()

        if should_exclude_question_from_presentation(col_str):
            continue

        if col_str in get_excluded_non_question_columns():
            continue

        if col_str.startswith("Score "):
            continue

        q_number = extract_question_number(col_str)
        if q_number in selected_numbers:
            cols.append(col_str)

    def sort_key(col):
        qn = extract_question_number(col)
        return (qn if qn is not None else 9999, str(col))

    cols = sorted(cols, key=sort_key)
    return {clean_other_question_label(col): col for col in cols}


def build_simple_distribution(data, col):
    if col not in data.columns:
        return pd.DataFrame()

    s = data[col].map(clean_response_value).dropna()

    if s.empty:
        return pd.DataFrame()

    dist = s.value_counts().reset_index()
    dist.columns = ["Réponse", "N"]
    dist["Pourcentage"] = dist["N"] / dist["N"].sum() * 100
    return dist


def build_simple_year_distribution(original_data, coded_data, col):
    if col not in original_data.columns or "Year" not in coded_data.columns:
        return pd.DataFrame()

    temp = pd.DataFrame({
        "Année": coded_data["Year"].astype(str),
        "Réponse": original_data.loc[coded_data.index, col].map(clean_response_value)
    }).dropna(subset=["Réponse"])

    if temp.empty:
        return pd.DataFrame()

    dist = temp.groupby(["Année", "Réponse"]).size().reset_index(name="N")
    dist["Pourcentage"] = dist.groupby("Année")["N"].transform(lambda x: x / x.sum() * 100)
    return dist




def normalize_response_label_for_kpi(value):
    """Normalize response labels to detect positive answers across satisfaction and agreement scales."""
    if pd.isna(value):
        return ""
    import unicodedata
    text = str(value).strip().replace("\u00a0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text).strip()
    return text


POSITIVE_SCALE_RESPONSES = {
    # Satisfaction scale, feminine and masculine
    "satisfaisante",
    "tres satisfaisante",
    "satisfaisant",
    "tres satisfaisant",
    "satisfait",
    "tres satisfait",
    "satisfaite",
    "tres satisfaite",

    # Agreement scale
    "d'accord",
    "tout a fait d'accord",

    # Utility / usefulness scale used in some questions
    "plutot oui",
    "tout a fait",
    "oui, suffisamment",
    "oui et j'ai beaucoup appris",
    "oui et j'ai bien appris",
}

NEGATIVE_SCALE_RESPONSES = {
    # Satisfaction scale
    "insatisfaisante",
    "tres insatisfaisante",
    "insatisfaisant",
    "tres insatisfaisant",
    "insatisfait",
    "tres insatisfait",
    "insatisfaite",
    "tres insatisfaite",

    # Agreement scale
    "pas d'accord",
    "pas du tout d'accord",

    # Utility / usefulness scale used in some questions
    "plutot non",
    "pas du tout",
    "oui, mais pas suffisamment",
    "non",
    "oui mais j'ai peu appris",
}


SCALE_SIGNATURE_GROUPS = [
    {
        "positive": {"satisfaisante", "tres satisfaisante", "satisfaisant", "tres satisfaisant", "satisfait", "tres satisfait", "satisfaite", "tres satisfaite"},
        "negative": {"insatisfaisante", "tres insatisfaisante", "insatisfaisant", "tres insatisfaisant", "insatisfait", "tres insatisfait", "insatisfaite", "tres insatisfaite"},
        "label": "Satisfaction positive",
        "subtitle": "Satisfait(e) + très satisfait(e)"
    },
    {
        "positive": {"d'accord", "tout a fait d'accord"},
        "negative": {"pas d'accord", "pas du tout d'accord"},
        "label": "Accord positif",
        "subtitle": "D’accord + tout à fait d’accord"
    },
    {
        "positive": {"plutot oui", "tout a fait"},
        "negative": {"plutot non", "pas du tout"},
        "label": "Réponses positives",
        "subtitle": "Plutôt oui + tout à fait"
    },
    {
        "positive": {"oui, suffisamment"},
        "negative": {"oui, mais pas suffisamment", "non"},
        "label": "Formation suffisante",
        "subtitle": "Oui, suffisamment"
    },
]


def get_positive_scale_summary(dist):
    """Return positive percentage/frequency only for recognized scale questions.

    The original response distribution remains unchanged. This helper only adds an
    additional KPI when the response modalities clearly correspond to a satisfaction,
    agreement, usefulness, or sufficiency scale.
    """
    if dist is None or dist.empty or "Réponse" not in dist.columns or "N" not in dist.columns:
        return None

    temp = dist.copy()
    temp["_norm"] = temp["Réponse"].map(normalize_response_label_for_kpi)
    present = set(temp["_norm"].dropna().tolist())

    for signature in SCALE_SIGNATURE_GROUPS:
        has_positive = len(present.intersection(signature["positive"])) > 0
        has_negative = len(present.intersection(signature["negative"])) > 0
        if has_positive and has_negative:
            pos_n = int(temp.loc[temp["_norm"].isin(signature["positive"]), "N"].sum())
            total_n = int(temp["N"].sum())
            pos_pct = pos_n / total_n * 100 if total_n > 0 else np.nan
            return {
                "label": signature["label"],
                "subtitle": signature["subtitle"],
                "N positif": pos_n,
                "N total": total_n,
                "Pourcentage positif": pos_pct,
            }

    return None


def render_positive_scale_kpi(positive_summary):
    """Render an attractive KPI card for total positive answers."""
    if not positive_summary:
        return

    pct = positive_summary.get("Pourcentage positif", np.nan)
    pos_n = positive_summary.get("N positif", 0)
    total_n = positive_summary.get("N total", 0)
    label = positive_summary.get("label", "Réponses positives")
    subtitle = positive_summary.get("subtitle", "Total des réponses positives")
    color = kpi_color_percentage(pct)

    st.markdown(
        f"""
        <div style='
            background:linear-gradient(135deg, #FFFFFF 0%, #F7F9FC 100%);
            border:1px solid #DDE5F0;
            border-left:8px solid {color};
            border-radius:20px;
            padding:18px 20px;
            margin:0 0 14px 0;
            box-shadow:0 6px 18px rgba(0,0,0,0.06);
            font-family:Candara, Arial, sans-serif;
        '>
            <div style='font-size:14px;font-weight:900;color:{USJ_TEXT};margin-bottom:6px;'>{html_escape(label)}</div>
            <div style='display:flex;align-items:flex-end;gap:14px;flex-wrap:wrap;'>
                <div style='font-size:38px;font-weight:900;color:{color};line-height:1;'>{safe_pct(pct)}</div>
                <div style='font-size:18px;font-weight:900;color:{USJ_BLUE};line-height:1.25;'>{int(pos_n):,} / {int(total_n):,}</div>
            </div>
            <div style='font-size:13px;color:#667085;margin-top:8px;'>{html_escape(subtitle)}</div>
        </div>
        """.replace(",", " "),
        unsafe_allow_html=True
    )


def get_main_question_group_header(question_col):
    """Return the main questionnaire wording that should appear before grouped sub-items."""
    q_norm = normalize_question_key(question_col)

    if q_norm.startswith("28_") or q_norm.startswith("28-"):
        return {
            "code": "28",
            "title": "28- Comment évaluez-vous la qualité des services suivants offerts par l’USJ ?",
            "subtitle": "Les résultats ci-dessous détaillent l’évaluation de chaque service proposé par l’USJ."
        }

    if q_norm.startswith("29_") or q_norm.startswith("29-"):
        return {
            "code": "29",
            "title": "29- Évaluez chacun des aspects suivants de votre expérience de vie étudiante à l’USJ :",
            "subtitle": "Les résultats ci-dessous détaillent les différents aspects de l’expérience de vie étudiante."
        }

    return None


def render_main_question_group_header(group_info):
    """Display the main question before its detailed sub-questions."""
    if not group_info:
        return

    st.markdown(
        f"""
        <div style='
            background:linear-gradient(135deg, #F7F9FC 0%, #EEF4FF 100%);
            border:1px solid #DDE5F0;
            border-left:8px solid {USJ_BLUE};
            border-radius:20px;
            padding:20px 22px;
            margin:28px 0 14px 0;
            box-shadow:0 6px 18px rgba(0,27,117,0.07);
            font-family:Candara, Arial, sans-serif;
        '>
            <div style='font-size:13px;font-weight:900;color:#667085;margin-bottom:6px;'>Question principale</div>
            <div style='font-size:23px;font-weight:900;color:{USJ_BLUE};line-height:1.35;'>{html_escape(group_info['title'])}</div>
            <div style='font-size:14px;color:#5F6B7A;margin-top:8px;'>{html_escape(group_info['subtitle'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_all_questions_single_result(question_label, question_col, original_filtered, total_n, coded_filter_data=None):
    """Render one complete descriptive result block for a question within the selected section.

    Conditional questions use the applicable denominator only. Example: 4a and 4b
    questions are calculated only among respondents who answered Oui to Q4.
    """
    if question_col not in df_original.columns and question_col not in original_filtered.columns:
        return

    if coded_filter_data is not None:
        selected_series, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(
            df_original,
            coded_filter_data,
            question_col
        )
        valid_series = selected_series.dropna()
        eligible_n = int(len(eligible_index))
        valid_n = int(valid_series.shape[0])
        missing_n = int(selected_series.isna().sum()) if eligible_n > 0 else 0
        missing_pct = missing_n / eligible_n * 100 if eligible_n > 0 else np.nan
        modalities_n = int(valid_series.nunique()) if valid_n > 0 else 0
        base_label = "Base applicable" if parent_col else "Base filtrée"
        base_subtitle = "Répondants concernés" if parent_col else "Répondants sélectionnés"
        base_n = eligible_n
        dependency_label = clean_other_question_label(parent_col) if parent_col else None

        if valid_series.empty:
            dist = pd.DataFrame()
        else:
            dist = valid_series.value_counts().reset_index()
            dist.columns = ["Réponse", "N"]
            dist["Pourcentage"] = dist["N"] / dist["N"].sum() * 100
    else:
        if question_col not in original_filtered.columns:
            return
        dist = build_simple_distribution(original_filtered, question_col)
        valid_n = int(original_filtered[question_col].map(clean_response_value).dropna().shape[0])
        missing_n = int(total_n - valid_n)
        missing_pct = missing_n / total_n * 100 if total_n > 0 else np.nan
        modalities_n = int(original_filtered[question_col].map(clean_response_value).dropna().nunique())
        base_label = "Base filtrée"
        base_subtitle = "Répondants sélectionnés"
        base_n = int(total_n)
        parent_col = None
        non_applicable_n = 0
        dependency_label = None

    condition_html = ""
    if parent_col:
        condition_html = (
            f"<div style='font-size:13px;color:#667085;margin-top:8px;'>"
            f"Question conditionnelle liée à : <b>{html_escape(dependency_label)}</b>"
            f"</div>"
            f"<div style='font-size:13px;color:#667085;margin-top:4px;'>"
            f"Non applicables exclus du dénominateur : <b>{int(non_applicable_n):,}</b>"
            f"</div>"
        ).replace(',', ' ')

    st.markdown(
        f"""
        <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {USJ_BLUE};border-radius:18px;padding:18px 20px;margin:24px 0 12px 0;box-shadow:0 5px 16px rgba(0,0,0,0.05);'>
            <div style='font-size:13px;font-weight:800;color:#667085;margin-bottom:6px;'>Question / variable</div>
            <div style='font-size:20px;font-weight:900;color:{USJ_BLUE};line-height:1.35;'>{html_escape(question_label)}</div>
            <div style='font-size:13px;color:#667085;margin-top:8px;'>Variable Excel : {html_escape(question_col)}</div>
            {condition_html}
        </div>
        """,
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        insight_card(base_label, base_n, base_subtitle, USJ_BLUE_2)
    with m2:
        insight_card("N valide", valid_n, "Réponses non manquantes", USJ_GREEN if valid_n > 0 else USJ_RED)
    with m3:
        insight_card("Données manquantes", safe_pct(missing_pct), "Dans la base applicable" if parent_col else "Dans la base filtrée", USJ_ORANGE if pd.notna(missing_pct) and missing_pct > 10 else USJ_GREEN)
    with m4:
        insight_card("Modalités", modalities_n, "Réponses distinctes", USJ_GOLD)

    if dist.empty:
        st.warning("Aucune réponse valide disponible pour cette question avec les filtres sélectionnés.")
        return

    if modalities_n > 30:
        display_dist = dist.sort_values("N", ascending=False).head(30).copy()
        display_dist["Pourcentage"] = display_dist["Pourcentage"].map(lambda x: f"{x:.2f}%")
        st.markdown(f"<h4 style='color:{USJ_BLUE};'>Réponses les plus fréquentes</h4>", unsafe_allow_html=True)
        st.dataframe(display_dist, use_container_width=True, hide_index=True)
        return

    dist_chart = dist.sort_values("Pourcentage", ascending=True).copy()
    fig = px.bar(
        dist_chart,
        x="Pourcentage",
        y="Réponse",
        orientation="h",
        text="Pourcentage",
        color="Pourcentage",
        color_continuous_scale=[[0, "#EAF2FF"], [0.5, "#7FA6D9"], [1, USJ_BLUE]],
        hover_data={"N": True, "Pourcentage": ":.2f"},
        title="Distribution des réponses"
    )
    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        marker_line_color="white",
        marker_line_width=1,
        cliponaxis=False
    )
    fig.update_layout(
        xaxis_title="Pourcentage des réponses valides",
        yaxis_title="",
        coloraxis_showscale=False,
        margin=dict(l=40, r=80, t=75, b=45)
    )
    theme_layout(fig, height=max(390, 38 * len(dist_chart)), showlegend=False)

    positive_summary = get_positive_scale_summary(dist)

    chart_col, table_col = st.columns([1.55, 1])
    with chart_col:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"all_questions_chart_{re.sub(r'[^A-Za-z0-9_]+', '_', str(question_col))}"
        )

    with table_col:
        if positive_summary:
            render_positive_scale_kpi(positive_summary)
        display_dist = dist.sort_values("Pourcentage", ascending=False).copy()
        display_dist["Pourcentage"] = display_dist["Pourcentage"].map(lambda x: f"{x:.2f}%")
        st.markdown(f"<h4 style='color:{USJ_BLUE}; margin-top:0;'>Tableau des fréquences</h4>", unsafe_allow_html=True)
        st.dataframe(display_dist, use_container_width=True, hide_index=True)

    top_dist = dist.sort_values("Pourcentage", ascending=False).iloc[0]
    conditional_note = " Cette lecture est calculée uniquement sur la base applicable à la question conditionnelle." if parent_col else ""
    st.markdown(
        f"""
        <div style='background:#F7F9FC;border-left:6px solid {USJ_BLUE};border-radius:14px;padding:12px 16px;margin-top:4px;margin-bottom:8px;'>
            <b>Lecture descriptive :</b> la modalité la plus fréquente est <b>{html_escape(top_dist['Réponse'])}</b>,
            avec <b>{top_dist['Pourcentage']:.2f}%</b> des réponses valides.{conditional_note}
        </div>
        """,
        unsafe_allow_html=True
    )

def page_all_questions_results():
    section_header(
        "Résultats descriptifs de toutes les questions",
        "Présentation descriptive question par question, avant le calcul des scores et des indicateurs."
    )

    summary_box(
        """
        Cette page présente les résultats bruts de chaque question du questionnaire avant toute agrégation en scores ou KPI.
        Les résultats sont affichés pour une seule année à la fois. Les comparaisons historiques seront traitées séparément dans la page dédiée.
        Les bases applicables des questions conditionnelles sont corrigées automatiquement lorsque la question filtre est identifiée.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    selected_year, data_questions, original_questions = get_single_year_context("all_questions")

    if data_questions.empty:
        st.warning("Aucune donnée disponible pour l’année et les filtres sélectionnés.")
        return

    available_sections = list(ALL_SURVEY_SECTION_NUMBERS.keys())

    selected_section_all = st.selectbox(
        "Choisir une section du questionnaire",
        available_sections,
        key="all_questions_section_selector"
    )

    question_map = get_columns_for_all_questions_section(df_original, selected_section_all)

    if not question_map:
        st.warning("Aucune colonne trouvée dans le fichier Excel pour cette section.")
        return

    original_filtered = original_questions.copy()
    total_n = int(len(original_filtered))
    question_count = len(question_map)

    valid_counts = []
    for _, col in question_map.items():
        if col in original_filtered.columns:
            valid_counts.append(int(original_filtered[col].map(clean_response_value).dropna().shape[0]))
    average_valid_n = np.mean(valid_counts) if valid_counts else np.nan

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        insight_card("Section", selected_section_all, "Titre du questionnaire", USJ_BLUE)
    with c2:
        insight_card("Année", selected_year, "Année affichée", USJ_BLUE_2)
    with c3:
        insight_card("Questions", question_count, "Variables affichées", USJ_GOLD)
    with c4:
        insight_card("Base filtrée", total_n, "Répondants sélectionnés", USJ_GREEN if total_n > 0 else USJ_RED)

    summary_box(
        f"""
        La section <b>{html_escape(selected_section_all)}</b> contient <b>{question_count}</b> question(s) ou variable(s) affichées directement sur cette page.
        Il n’y a plus de sélection question par question. Chaque bloc présente la distribution, le tableau des fréquences, le nombre de réponses valides et les données manquantes.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    if question_count > 12:
        st.info("Cette section contient plusieurs questions. Les blocs ci-dessous peuvent être longs à afficher, mais toutes les questions de la section sont présentées sans menu de sélection supplémentaire.")

    current_main_group = None
    for question_label, question_col in question_map.items():
        group_info = get_main_question_group_header(question_col)
        group_code = group_info["code"] if group_info else None
        if group_code and group_code != current_main_group:
            render_main_question_group_header(group_info)
            current_main_group = group_code
        elif not group_code:
            current_main_group = None

        render_all_questions_single_result(question_label, question_col, original_filtered, total_n, data_questions)


Q44_FINANCING_ITEMS = {
    "44_a- Financé vos études à l’USJ : Parents": "Parents",
    "44_b- Financé vos études à l’USJ : Moi-même (emploi)": "Moi-même par un emploi",
    "44_c- Financé vos études à l’USJ : Bourse accordée par l'USJ sur bases de critères sociaux (Service social)": "Bourse USJ sur critères sociaux",
    "44_d- Financé vos études à l’USJ : Bourse accordée par l'USJ sur bases de critères non sociaux": "Bourse USJ sur critères non sociaux",
    "44_e- Financé vos études à l’USJ : Autre bourse": "Autre bourse",
    "44_f- Financé vos études à l’USJ : Prêt USJ": "Prêt USJ",
    "44_g- Financé vos études à l’USJ : Autre prêt": "Autre prêt",
}


def page_other_questions():
    section_header(
        "Autres questions du questionnaire",
        "Résultats complémentaires issus des questions non intégrées dans les indicateurs principaux."
    )

    summary_box(
        """
        Cette page détecte automatiquement, à partir du fichier Excel, les questions qui ne sont pas utilisées dans les scores principaux.
        Pour les questions conditionnelles, la base de calcul est corrigée : les répondants non concernés sont classés comme <b>non applicables</b> et ne sont pas comptés comme données manquantes.
        Par exemple, les questions liées au stage sont calculées uniquement parmi les répondants ayant déclaré avoir réalisé un stage.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    inventory = get_other_question_inventory(df_original, df_filtered)
    if inventory.empty:
        st.warning("Aucune question complémentaire n’a été détectée en dehors des composantes déjà analysées.")
        return

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        insight_card("Questions complémentaires", len(inventory), "Détectées dans Excel", USJ_BLUE)
    with col_b:
        insight_card("Répondants filtrés", len(df_filtered), "Base active", USJ_GREEN if len(df_filtered) > 0 else USJ_RED)
    with col_c:
        insight_card("Questions fermées", int((inventory["Type"] == "Fermée / catégorielle").sum()), "Analysables en graphique", USJ_GOLD)
    with col_d:
        conditional_n = int((inventory["Question filtre"] != "Aucun filtre conditionnel").sum())
        insight_card("Questions conditionnelles", conditional_n, "Base applicable corrigée", USJ_BLUE_2)

    st.markdown(f"<h3 style='color:{USJ_BLUE}; margin-top:22px;'>Inventaire des autres questions détectées</h3>", unsafe_allow_html=True)
    inv_display = inventory.copy()
    inv_display["Données manquantes (%)"] = inv_display["Données manquantes (%)"].map(lambda x: "" if pd.isna(x) else f"{x:.1f}%")
    st.dataframe(
        inv_display[["Catégorie", "Question affichée", "Question filtre", "Base applicable", "Non applicable", "N valide", "Données manquantes (%)", "Modalités", "Type"]],
        use_container_width=True,
        hide_index=True
    )

    categories = ["Toutes les catégories"] + sorted(inventory["Catégorie"].dropna().unique().tolist())
    cfilter, qfilter = st.columns([1, 2])
    with cfilter:
        selected_category = st.selectbox("Filtrer par catégorie", categories)
    filtered_inventory = inventory.copy()
    if selected_category != "Toutes les catégories":
        filtered_inventory = filtered_inventory[filtered_inventory["Catégorie"] == selected_category]

    with qfilter:
        question_options = {
            row["Question affichée"]: row["Question"]
            for _, row in filtered_inventory.iterrows()
        }
        selected_other_question_label = st.selectbox(
            "Choisir une question complémentaire",
            options=list(question_options.keys()),
            key="other_question_dropdown"
        )
        selected_other_question = question_options[selected_other_question_label]

    selected_series, eligible_index, non_applicable_n, parent_col = get_applicable_response_series(
        df_original,
        df_filtered,
        selected_other_question
    )
    valid_series = selected_series.dropna()
    eligible_n = int(len(eligible_index))
    n_valid = int(valid_series.shape[0])
    missing_n = int(selected_series.isna().sum()) if eligible_n > 0 else 0
    missing_pct = missing_n / eligible_n * 100 if eligible_n > 0 else np.nan
    unique_n = int(valid_series.nunique()) if n_valid > 0 else 0
    selected_category_label = classify_other_question(selected_other_question, selected_series)
    dependency_label = clean_other_question_label(parent_col) if parent_col else "Aucune condition"

    if selected_other_question.startswith("44_"):
        rows = []

        for col, label in Q44_FINANCING_ITEMS.items():
            if col in df_original.columns:
                responses, q44_eligible_index, q44_non_applicable_n, q44_parent_col = get_applicable_response_series(
                    df_original,
                    df_filtered,
                    col
                )

                valid = responses.dropna()
                total = len(valid)

                yes_n = valid.astype(str).str.strip().str.lower().eq("oui").sum()
                no_n = valid.astype(str).str.strip().str.lower().eq("non").sum()

                if total > 0:
                    rows.append({
                        "Modalité": label,
                        "Oui (%)": yes_n / total * 100,
                        "Non (%)": no_n / total * 100,
                        "N valide": total
                    })

        q44_df = pd.DataFrame(rows)

        if q44_df.empty:
            st.warning("Aucune donnée valide disponible pour les modes de financement.")
            return

        q44_base = int(q44_df["N valide"].max()) if "N valide" in q44_df.columns and not q44_df.empty else 0
        q44_missing_pct = missing_pct
        q44_modalities = int(len(Q44_FINANCING_ITEMS))

        q1, q2, q3, q4 = st.columns(4)
        with q1:
            insight_card("Catégorie", selected_category_label, "Lecture thématique", USJ_BLUE)
        with q2:
            insight_card("Base applicable", q44_base, "Répondants concernés", USJ_GREEN if q44_base > 0 else USJ_RED)
        with q3:
            insight_card("Données manquantes", safe_pct(q44_missing_pct), "Parmi les répondants concernés", USJ_ORANGE if pd.notna(q44_missing_pct) and q44_missing_pct > 10 else USJ_GREEN)
        with q4:
            insight_card("Nombre de modalités", q44_modalities, "Modes de financement", USJ_GOLD)

        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {USJ_BLUE};border-radius:18px;padding:18px 20px;margin:18px 0;box-shadow:0 5px 16px rgba(0,0,0,0.05);'>
                <div style='font-size:14px;font-weight:800;color:#667085;margin-bottom:6px;'>Question analysée</div>
                <div style='font-size:20px;font-weight:900;color:{USJ_BLUE};line-height:1.35;'>{html_escape(selected_other_question_label)}</div>
                <div style='font-size:13px;color:#667085;margin-top:8px;'>Analyse groupée des modalités de financement déclarées dans le questionnaire.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        q44_long = q44_df.melt(
            id_vars=["Modalité", "N valide"],
            value_vars=["Oui (%)", "Non (%)"],
            var_name="Réponse",
            value_name="Pourcentage"
        )

        fig_q44 = px.bar(
            q44_long,
            x="Modalité",
            y="Pourcentage",
            color="Réponse",
            text="Pourcentage",
            barmode="group",
            color_discrete_map={
                "Oui (%)": USJ_GREEN,
                "Non (%)": USJ_DARK_RED
            },
            hover_data={"N valide": True},
            title="Modes de financement des études à l’USJ"
        )

        fig_q44.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_q44.update_layout(
            xaxis_title="Mode de financement",
            yaxis_title="Pourcentage des réponses valides",
            legend_title="Réponse",
            yaxis=dict(range=[0, 100])
        )

        theme_layout(fig_q44, height=560)
        st.plotly_chart(fig_q44, use_container_width=True, config={"displayModeBar": False})

        q44_yes = q44_df.sort_values("Oui (%)", ascending=False)
        top_q44 = q44_yes.iloc[0]
        second_q44 = q44_yes.iloc[1] if len(q44_yes) > 1 else None

        second_q44_text = ""
        if second_q44 is not None:
            second_q44_text = (
                f" La deuxième modalité la plus déclarée est <b>{html_escape(second_q44['Modalité'])}</b> "
                f"avec <b>{second_q44['Oui (%)']:.2f}%</b> de réponses « Oui »."
            )

        summary_box(
            f"""
            <span style='font-size:20px; font-weight:800; color:{USJ_BLUE};'>Lecture décisionnelle</span><br>
            Concernant les modes de financement des études à l’USJ, <b>{top_q44['Oui (%)']:.2f}%</b> des répondants concernés
            déclarent avoir mobilisé la modalité <b>{html_escape(top_q44['Modalité'])}</b>.{second_q44_text}
            Cette lecture permet d’identifier les principales sources de financement utilisées par les étudiants et d’éclairer
            les décisions relatives aux aides financières, aux bourses et aux dispositifs de soutien économique.
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )

        q44_display = q44_df.copy()
        q44_display["Oui (%)"] = q44_display["Oui (%)"].map(lambda x: f"{x:.2f}%")
        q44_display["Non (%)"] = q44_display["Non (%)"].map(lambda x: f"{x:.2f}%")

        st.dataframe(
            q44_display[["Modalité", "N valide", "Oui (%)", "Non (%)"]],
            use_container_width=True,
            hide_index=True
        )

        return


    k1, k2, k3, k4 = st.columns(4)
    with k1:
        insight_card("Catégorie", selected_category_label, "Lecture thématique", USJ_BLUE)
    with k2:
        insight_card("Base applicable", eligible_n, "Répondants concernés", USJ_GREEN if eligible_n > 0 else USJ_RED)
    with k3:
        insight_card("Données manquantes", safe_pct(missing_pct), "Parmi les répondants concernés", USJ_ORANGE if pd.notna(missing_pct) and missing_pct > 10 else USJ_GREEN)
    with k4:
         insight_card("Nombre de modalités", unique_n, "Réponses distinctes", USJ_GOLD)

    if eligible_n == 0:
        st.warning("Aucun répondant n’est applicable pour cette question avec les filtres sélectionnés.")
        return

    if n_valid == 0:
        st.warning("Aucune réponse valide pour cette question parmi les répondants concernés.")
        return

    st.markdown(
        f"""
        <div style='background:#FFFFFF;border:1px solid #DDE5F0;border-left:7px solid {USJ_BLUE};border-radius:18px;padding:18px 20px;margin:18px 0;box-shadow:0 5px 16px rgba(0,0,0,0.05);'>
            <div style='font-size:14px;font-weight:800;color:#667085;margin-bottom:6px;'>Question analysée</div>
            <div style='font-size:20px;font-weight:900;color:{USJ_BLUE};line-height:1.35;'>{html_escape(selected_other_question_label)}</div>
            <div style='font-size:13px;color:#667085;margin-top:8px;'>Variable Excel : {html_escape(selected_other_question)}</div>
            <div style='font-size:13px;color:#667085;margin-top:4px;'>Condition d’applicabilité : {html_escape(dependency_label)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if unique_n <= 30:
        dist_year = build_other_question_distribution(df_original, df_filtered, selected_other_question)
        overall = valid_series.value_counts(dropna=True).reset_index()
        overall.columns = ["Réponse", "N"]
        overall["Pourcentage"] = overall["N"] / overall["N"].sum() * 100
        overall = overall.sort_values("Pourcentage", ascending=True)

        fig_overall = px.bar(
            overall,
            x="Pourcentage",
            y="Réponse",
            orientation="h",
            text="Pourcentage",
            color="Pourcentage",
            color_continuous_scale=[[0, "#EAF2FF"], [0.5, "#7FA6D9"], [1, USJ_BLUE]],
            hover_data={"N": True, "Pourcentage": ":.2f"},
            title="Distribution globale des réponses parmi les répondants concernés"
        )
        fig_overall.update_traces(texttemplate="%{text:.2f}%", textposition="outside", marker_line_color="white", marker_line_width=1, cliponaxis=False)
        fig_overall.update_layout(xaxis_title="Pourcentage des réponses valides", yaxis_title="", coloraxis_showscale=False, margin=dict(l=40, r=80, t=90, b=50))
        theme_layout(fig_overall, height=max(460, 42 * len(overall)), showlegend=False)
        st.plotly_chart(fig_overall, use_container_width=True, config={"displayModeBar": False})

        if not dist_year.empty and dist_year["Année"].nunique() > 1:
            response_count = dist_year["Réponse"].nunique()
            fig_stack = px.bar(
                dist_year,
                x="Année",
                y="Pourcentage",
                color="Réponse",
                text="Pourcentage",
                barmode="stack",
                color_discrete_sequence=PLOTLY_SEQ,
                hover_data={"N": True, "Pourcentage": ":.2f"},
                title="Évolution de la distribution par année"
            )
            fig_stack.update_traces(texttemplate="%{text:.1f}%", textposition="inside", cliponaxis=False)
            fig_stack.update_layout(
                yaxis_title="Pourcentage des réponses valides",
                xaxis_title="Année",
                legend_title="Réponse",
                legend=dict(orientation="h", yanchor="bottom", y=1.14, xanchor="left", x=0, font=dict(size=10)),
                margin=dict(l=40, r=30, t=150 if response_count > 6 else 100, b=50),
            )
            theme_layout(fig_stack, height=620 if response_count > 6 else 540)
            st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})

        top_resp = overall.sort_values("Pourcentage", ascending=False).iloc[0]
        second_resp = overall.sort_values("Pourcentage", ascending=False).iloc[1] if len(overall) > 1 else None
        second_text = ""
        if second_resp is not None:
            second_text = f" La deuxième réponse la plus fréquente est <b>{html_escape(second_resp['Réponse'])}</b> ({second_resp['Pourcentage']:.2f}%)."

        conditional_text = ""
        if parent_col:
            conditional_text = (
                f" Cette question est conditionnelle : le calcul est basé uniquement sur les <b>{eligible_n}</b> répondants concernés, "
                f"tandis que <b>{non_applicable_n}</b> répondants sont considérés comme non applicables et exclus du taux de non-réponse."
            )

        narrative_text = build_other_question_narrative(
            selected_other_question_label,
            overall.sort_values("Pourcentage", ascending=False),
            n_valid=n_valid,
            eligible_n=eligible_n,
            parent_col=parent_col,
            dependency_label=dependency_label,
            non_applicable_n=non_applicable_n
        )

        summary_box(
            f"""
            <span style='font-size:20px; font-weight:800; color:{USJ_BLUE};'>Lecture décisionnelle</span><br>
            {narrative_text}
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )

        display_overall = overall.sort_values("Pourcentage", ascending=False).copy()
        display_overall["Pourcentage"] = display_overall["Pourcentage"].map(lambda x: f"{x:.2f}%")
        st.dataframe(display_overall, use_container_width=True, hide_index=True)

    else:
        freq = valid_series.value_counts().head(25).reset_index()
        freq.columns = ["Réponse", "N"]
        freq["Pourcentage"] = freq["N"] / n_valid * 100
        freq["Pourcentage"] = freq["Pourcentage"].map(lambda x: f"{x:.2f}%")
        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Réponses les plus fréquentes</h3>", unsafe_allow_html=True)
        st.dataframe(freq, use_container_width=True, hide_index=True)
        summary_box(
            """
            Cette question comporte un nombre élevé de réponses distinctes. Elle est donc traitée comme une question ouverte ou quasi ouverte.
            Le tableau présente les réponses les plus fréquentes parmi les répondants concernés afin d’identifier les signaux récurrents sans surcharger la lecture.
            """,
            color=USJ_ORANGE,
            background="#FFF8F0"
        )





def build_printable_report_html():
    """Build a detailed, decision-oriented printable HTML report.

    The report uses the active dashboard filters and combines:
    - KPI results
    - dimensional ranking
    - historical evolution
    - faculty benchmarking when a faculty is selected
    - key improvement drivers from the Random Forest models
    - statistical significance tests across years
    - question-level strengths and priorities
    - automatic operational recommendations
    """

    def fmt_pct2(value):
        return "NA" if pd.isna(value) else f"{value:.2f}%"

    def fmt_pts(value):
        return "NA" if pd.isna(value) else f"{value:+.2f} pts"

    def fmt_num(value, digits=2):
        return "NA" if pd.isna(value) else f"{value:.{digits}f}"

    def clean_text(value):
        return html_escape(value)

    def performance_class(value):
        if pd.isna(value):
            return "Non disponible", "#777777"
        if value < 50:
            return "Zone d’alerte", USJ_RED
        if value <= 75:
            return "Zone de consolidation", USJ_ORANGE
        return "Zone de force", USJ_GREEN

    def row_color(value):
        if pd.isna(value):
            return "#F3F4F6"
        if value < 50:
            return "#FDE2E1"
        if value <= 75:
            return "#FFF3D6"
        return "#E5F4E7"

    def gap_color(value):
        if pd.isna(value):
            return "#667085"
        if value > 0:
            return USJ_GREEN
        if value < 0:
            return USJ_RED
        return "#667085"

    def html_table(rows, headers, empty_message="Aucune donnée disponible."):
        """Render report tables with consistent column alignment.

        Numeric columns are right-aligned in both header and body, so values sit exactly
        under their titles. Text columns remain left-aligned. The function also keeps
        older pre-built <td> cells working while normalizing header alignment.
        """
        numeric_headers = {
            "Résultat", "Faculté", "USJ", "USJ filtré", "Écart", "p-value",
            "Importance", "Poids", "Base applicable", "N valide", "N", "Moyenne", "Moyenne (%)",
            "Évolution", "Rang"
        }
        if not rows:
            colspan = max(1, len(headers))
            return f"<table class='report-table'><tbody><tr><td colspan='{colspan}'>{empty_message}</td></tr></tbody></table>"

        head_cells = []
        for h in headers:
            align = "right" if h in numeric_headers else "left"
            head_cells.append(f"<th style='text-align:{align};'>{clean_text(h)}</th>")
        head = "".join(head_cells)

        body = ""
        for row in rows:
            cells = []
            for h in headers:
                cell = str(row.get(h, ""))
                # Most report rows already provide a complete <td>...</td> cell.
                # If not, wrap safely and align it according to the header type.
                if not cell.lstrip().lower().startswith("<td"):
                    align = "right" if h in numeric_headers else "left"
                    cell = f"<td style='text-align:{align};'>{cell}</td>"
                elif h in numeric_headers and "text-align" not in cell.lower():
                    cell = cell.replace("<td", "<td style='text-align:right;'", 1)
                cells.append(cell)
            body += "<tr>" + "".join(cells) + "</tr>"

        return f"<table class='report-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    report_data = df_filtered.copy()
    comparison_data = apply_current_filters_without_faculty(df_coded)

    faculty_label = faculte if faculte != "Tous" else "Ensemble de l’Université"
    period_label = year if year != "Tous" else "Toutes les années disponibles"
    report_title = f"Rapport analytique Exit Survey - {faculty_label}"

    n_resp = len(report_data)
    sat = pct_from_mean(report_data["Score satisfaction globale"].mean()) if "Score satisfaction globale" in report_data.columns else np.nan
    rec = calculate_recommendation_rate(report_data, q43)
    exp = pct_from_mean(report_data["Score expérience globale USJ"].mean()) if "Score expérience globale USJ" in report_data.columns else np.nan

    # Benchmark variables used later in the customized conclusion.
    usj_sat = np.nan
    usj_rec = np.nan
    usj_exp = np.nan
    sat_gap = np.nan
    rec_gap = np.nan
    exp_gap = np.nan
    best_benchmark_dim = None
    weakest_benchmark_dim = None

    badge_text, badge_color = performance_class(sat)
    dim_table = build_report_dimension_table(report_data)

    if not dim_table.empty:
        dim_table = dim_table.copy().sort_values("Résultat", ascending=False)
        top_dims = dim_table.head(3)
        weak_dims = dim_table.tail(3).sort_values("Résultat", ascending=True)
        best = dim_table.iloc[0]
        weak = dim_table.iloc[-1]
    else:
        top_dims = pd.DataFrame()
        weak_dims = pd.DataFrame()
        best = {"Dimension": "Non disponible", "Résultat": np.nan}
        weak = {"Dimension": "Non disponible", "Résultat": np.nan}

    generated_filters = f"Année : {year} | Genre : {genre} | Faculté : {faculte} | Campus : {campus if CAMPUS_COLUMN else 'Non disponible'} | Niveau : {niveau}"

    # -------------------------------------------------
    # Dimensional ranking table
    # -------------------------------------------------
    dim_rows = []
    for i, row in dim_table.iterrows():
        status_text, status_color = performance_class(row["Résultat"])
        dim_rows.append({
            "Dimension": f"<td>{clean_text(row['Dimension'])}</td>",
            "Résultat": f"<td style='text-align:right; background:{row_color(row['Résultat'])}; font-weight:800;'>{fmt_pct2(row['Résultat'])}</td>",
            "Lecture": f"<td><span class='mini-badge' style='background:{status_color};'>{clean_text(status_text)}</span></td>",
        })
    dim_table_html = html_table(dim_rows, ["Dimension", "Résultat", "Lecture"])

    # -------------------------------------------------
    # Strengths and priorities tables
    # -------------------------------------------------
    strength_rows = []
    for rank, (_, row) in enumerate(top_dims.iterrows(), start=1):
        strength_rows.append({
            "Rang": f"<td>{rank}</td>",
            "Dimension": f"<td>{clean_text(row['Dimension'])}</td>",
            "Résultat": f"<td style='text-align:right; font-weight:800; color:{USJ_GREEN};'>{fmt_pct2(row['Résultat'])}</td>",
        })
    strengths_html = html_table(strength_rows, ["Rang", "Dimension", "Résultat"])

    priority_rows = []
    for rank, (_, row) in enumerate(weak_dims.iterrows(), start=1):
        priority_rows.append({
            "Rang": f"<td>{rank}</td>",
            "Dimension": f"<td>{clean_text(row['Dimension'])}</td>",
            "Résultat": f"<td style='text-align:right; font-weight:800; color:{USJ_RED if row['Résultat'] < 75 else USJ_ORANGE};'>{fmt_pct2(row['Résultat'])}</td>",
        })
    priorities_html = html_table(priority_rows, ["Rang", "Dimension", "Résultat"])

    # -------------------------------------------------
    # Historical trend, using all available years in the filtered scope
    # -------------------------------------------------
    trend_html = ""
    trend_dimension_html = ""
    ys = build_year_summary(report_data, q43)
    if len(ys) >= 2 and "Satisfaction globale" in ys.columns:
        ys = ys.sort_values("Année")
        first_year = ys["Année"].iloc[0]
        last_year = ys["Année"].iloc[-1]
        first_sat = ys["Satisfaction globale"].iloc[0]
        last_sat = ys["Satisfaction globale"].iloc[-1]
        delta_sat = last_sat - first_sat if pd.notna(first_sat) and pd.notna(last_sat) else np.nan
        first_rec = ys["Taux de recommandation"].iloc[0] if "Taux de recommandation" in ys.columns else np.nan
        last_rec = ys["Taux de recommandation"].iloc[-1] if "Taux de recommandation" in ys.columns else np.nan
        delta_rec = last_rec - first_rec if pd.notna(first_rec) and pd.notna(last_rec) else np.nan

        trend_html = f"""
        <div class='report-card'>
            <h3>Évolution historique globale</h3>
            <p>
                Entre <b>{clean_text(first_year)}</b> et <b>{clean_text(last_year)}</b>, la satisfaction globale évolue de
                <b>{fmt_pct2(first_sat)}</b> à <b>{fmt_pct2(last_sat)}</b>, soit <b style='color:{gap_color(delta_sat)};'>{fmt_pts(delta_sat)}</b>.
                Le taux de recommandation évolue de <b>{fmt_pct2(first_rec)}</b> à <b>{fmt_pct2(last_rec)}</b>, soit
                <b style='color:{gap_color(delta_rec)};'>{fmt_pts(delta_rec)}</b>. Cette évolution permet de distinguer les progrès réels
                des dimensions nécessitant une attention continue.
            </p>
        </div>
        """

        comp_long = build_component_long(report_data)
        if not comp_long.empty:
            hp = comp_long.pivot_table(index="Dimension", columns="Année", values="Pourcentage", aggfunc="mean")
            hp = hp.sort_index(axis=1)
            if hp.shape[1] >= 2:
                first_col = hp.columns[0]
                last_col = hp.columns[-1]
                diff = (hp[last_col] - hp[first_col]).dropna().sort_values(ascending=False)
                dim_evo_rows = []
                for dim, val in diff.items():
                    dim_evo_rows.append({
                        "Dimension": f"<td>{clean_text(dim)}</td>",
                        f"{first_col}": f"<td style='text-align:right;'>{fmt_pct2(hp.loc[dim, first_col])}</td>",
                        f"{last_col}": f"<td style='text-align:right;'>{fmt_pct2(hp.loc[dim, last_col])}</td>",
                        "Évolution": f"<td style='text-align:right; font-weight:800; color:{gap_color(val)};'>{fmt_pts(val)}</td>",
                    })
                trend_dimension_html = f"""
                <div class='report-card'>
                    <h3>Évolution par dimension</h3>
                    {html_table(dim_evo_rows, ["Dimension", str(first_col), str(last_col), "Évolution"])}
                </div>
                """

    # -------------------------------------------------
    # Benchmark against filtered USJ when a faculty is selected
    # -------------------------------------------------
    benchmark_html = ""
    if faculte != "Tous" and "Faculté_Institut_g" in comparison_data.columns and len(comparison_data) > 0:
        usj_sat = pct_from_mean(comparison_data["Score satisfaction globale"].mean()) if "Score satisfaction globale" in comparison_data.columns else np.nan
        usj_rec = calculate_recommendation_rate(comparison_data, q43)
        usj_exp = pct_from_mean(comparison_data["Score expérience globale USJ"].mean()) if "Score expérience globale USJ" in comparison_data.columns else np.nan
        sat_gap = sat - usj_sat if pd.notna(sat) and pd.notna(usj_sat) else np.nan
        rec_gap = rec - usj_rec if pd.notna(rec) and pd.notna(usj_rec) else np.nan
        exp_gap = exp - usj_exp if pd.notna(exp) and pd.notna(usj_exp) else np.nan

        bench_rows = []
        benchmark_scores = {
            "Satisfaction globale": (sat, usj_sat, sat_gap),
            "Recommandation": (rec, usj_rec, rec_gap),
            "Expérience globale": (exp, usj_exp, exp_gap),
        }
        for label, values in benchmark_scores.items():
            fac_val, usj_val, gap = values
            bench_rows.append({
                "Indicateur": f"<td>{clean_text(label)}</td>",
                "Faculté": f"<td style='text-align:right; font-weight:800;'>{fmt_pct2(fac_val)}</td>",
                "USJ filtré": f"<td style='text-align:right;'>{fmt_pct2(usj_val)}</td>",
                "Écart": f"<td style='text-align:right; font-weight:800; color:{gap_color(gap)};'>{fmt_pts(gap)}</td>",
            })

        # Dimension-level benchmark
        fac_dims = build_report_dimension_table(report_data).rename(columns={"Résultat": "Faculté"})
        usj_dims = build_report_dimension_table(comparison_data).rename(columns={"Résultat": "USJ"})
        merged_bench = fac_dims.merge(usj_dims, on="Dimension", how="inner")
        merged_bench["Écart"] = merged_bench["Faculté"] - merged_bench["USJ"]
        merged_bench = merged_bench.sort_values("Écart", ascending=False)
        if not merged_bench.empty:
            best_benchmark_dim = merged_bench.iloc[0]
            weakest_benchmark_dim = merged_bench.iloc[-1]

        bench_dim_rows = []
        for _, row in merged_bench.iterrows():
            bench_dim_rows.append({
                "Dimension": f"<td>{clean_text(row['Dimension'])}</td>",
                "Faculté": f"<td style='text-align:right; font-weight:800;'>{fmt_pct2(row['Faculté'])}</td>",
                "USJ filtré": f"<td style='text-align:right;'>{fmt_pct2(row['USJ'])}</td>",
                "Écart": f"<td style='text-align:right; font-weight:800; color:{gap_color(row['Écart'])};'>{fmt_pts(row['Écart'])}</td>",
            })

        best_gap_text = ""
        weak_gap_text = ""
        if not merged_bench.empty:
            best_gap = merged_bench.iloc[0]
            weak_gap = merged_bench.iloc[-1]
            best_gap_text = f"Le positionnement le plus favorable concerne <b>{clean_text(best_gap['Dimension'])}</b> ({fmt_pts(best_gap['Écart'])})."
            weak_gap_text = f"Le principal retrait relatif concerne <b>{clean_text(weak_gap['Dimension'])}</b> ({fmt_pts(weak_gap['Écart'])})."

        benchmark_html = f"""
        <div class='report-card'>
            <h3>Positionnement par rapport à l’ensemble USJ filtré</h3>
            <p>
                La comparaison ci-dessous situe <b>{clean_text(faculty_label)}</b> par rapport à l’ensemble USJ, en conservant les mêmes filtres
                d’année, de genre et de niveau. {best_gap_text} {weak_gap_text}
            </p>
            {html_table(bench_rows, ["Indicateur", "Faculté", "USJ filtré", "Écart"])}
            <div style='height:14px;'></div>
            <h4>Écarts par dimension</h4>
            {html_table(bench_dim_rows, ["Dimension", "Faculté", "USJ filtré", "Écart"])}
        </div>
        """
    else:
        key_points = []
        if pd.notna(sat):
            key_points.append(f"La satisfaction globale du périmètre analysé atteint <b>{fmt_pct2(sat)}</b>, ce qui le situe en <b>{clean_text(badge_text)}</b>.")
        if pd.notna(rec):
            key_points.append(f"Le taux de recommandation atteint <b>{fmt_pct2(rec)}</b>, indicateur central de l’attachement des répondants à l’USJ.")
        if not dim_table.empty:
            key_points.append(f"Le principal point fort est <b>{clean_text(best['Dimension'])}</b> avec <b>{fmt_pct2(best['Résultat'])}</b>.")
            key_points.append(f"La principale priorité d’amélioration concerne <b>{clean_text(weak['Dimension'])}</b> avec <b>{fmt_pct2(weak['Résultat'])}</b>.")
        key_points_html = "".join(f"<li>{item}</li>" for item in key_points)
        benchmark_html = f"""
        <div class='report-card decision-card'>
            <h3>Points clés à retenir</h3>
            <p>
                Cette lecture synthétise les résultats institutionnels selon les filtres sélectionnés. Elle met en évidence les forces,
                les zones à consolider et les priorités d’action à discuter dans une logique d’amélioration continue.
            </p>
            <ul>{key_points_html}</ul>
        </div>
        """

    # -------------------------------------------------
    # Key improvement drivers, using the same RF models as the dashboard
    # -------------------------------------------------
    feature_columns = [
        "Score enseignement et apprentissage",
        "Score accompagnement et encadrement",
        "Score développement des compétences",
        "Score services USJ",
        "Score vie étudiante et activités",
        "Score infrastructures et équipements",
        "Score frais / qualité enseignement",
        "Score frais / autres universités",
    ]
    feature_columns = [c for c in feature_columns if c in report_data.columns]
    display_names = {col: clean_component_name(col) for col in feature_columns}

    importance_html = ""
    model_base = report_data
    sat_model = model_base[feature_columns + ["Score satisfaction globale"]].dropna() if feature_columns else pd.DataFrame()
    if len(sat_model) < 30:
        # Use the broader filtered comparison sample as fallback so the report still gives decision support.
        sat_model = comparison_data[feature_columns + ["Score satisfaction globale"]].dropna() if feature_columns and "Score satisfaction globale" in comparison_data.columns else pd.DataFrame()

    if len(sat_model) >= 30 and feature_columns:
        try:
            importances = train_satisfaction_importance(sat_model, feature_columns)
            imp_df = pd.DataFrame({
                "Dimension": [display_names[c] for c in feature_columns],
                "Importance": importances,
            })
            total_imp = imp_df["Importance"].sum()
            imp_df["Importance (%)"] = imp_df["Importance"] / total_imp * 100 if total_imp > 0 else np.nan
            imp_df = imp_df.sort_values("Importance (%)", ascending=False).head(5)
            imp_rows = []
            for rank, (_, row) in enumerate(imp_df.iterrows(), start=1):
                imp_rows.append({
                    "Rang": f"<td>{rank}</td>",
                    "Levier": f"<td>{clean_text(row['Dimension'])}</td>",
                    "Importance": f"<td style='text-align:right; font-weight:800; color:{USJ_BLUE};'>{fmt_pct2(row['Importance (%)'])}</td>",
                })
            top_driver = imp_df.iloc[0]
            importance_html = f"""
            <div class='report-card driver-card'>
                <h3>Facteurs clés d’amélioration de la satisfaction globale</h3>
                <p>
                    Le modèle explicatif met en évidence les dimensions qui contribuent le plus à la satisfaction globale. Le levier principal est
                    <b>{clean_text(top_driver['Dimension'])}</b> avec une importance relative de <b>{fmt_pct2(top_driver['Importance (%)'])}</b>.
                    Ces résultats orientent les priorités d’action vers les dimensions les plus influentes, et non uniquement vers les scores les plus faibles.
                </p>
                {html_table(imp_rows, ["Rang", "Levier", "Importance"])}
            </div>
            """
        except Exception:
            importance_html = """
            <div class='report-card'>
                <h3>Facteurs clés d’amélioration</h3>
                <p>Les facteurs clés n’ont pas pu être recalculés pour les filtres actuels. Les données filtrées sont probablement insuffisantes.</p>
            </div>
            """
    else:
        importance_html = """
        <div class='report-card'>
            <h3>Facteurs clés d’amélioration</h3>
            <p>
                L’échantillon filtré ne contient pas assez de réponses complètes pour recalculer un modèle explicatif fiable. Pour interpréter les leviers,
                il est recommandé de consulter la page <b>Facteurs clés d’amélioration</b> avec un périmètre plus large.
            </p>
        </div>
        """

    # -------------------------------------------------
    # Statistical tests across years
    # -------------------------------------------------
    stats_rows = []
    if report_data["Year"].nunique() >= 2 and stats is not None:
        for col in SCORE_COLUMNS:
            if col in report_data.columns:
                p_value, test_name = anova_or_kruskal(report_data, col)
                stats_rows.append({
                    "Indicateur": f"<td>{clean_text(SCORE_LABELS.get(col, col))}</td>",
                    "p-value": f"<td style='text-align:right; font-weight:800;'>{format_p_value(p_value)}</td>",
                    "Interprétation": f"<td>{clean_text(p_interpretation(p_value))}</td>",
                })
        p_rec = chi_square_recommendation(report_data, q43)
        stats_rows.append({
            "Indicateur": "<td>Taux de recommandation</td>",
            "p-value": f"<td style='text-align:right; font-weight:800;'>{format_p_value(p_rec)}</td>",
            "Interprétation": f"<td>{clean_text(p_interpretation(p_rec))}</td>",
        })
    stats_html = ""
    if stats_rows:
        significant_count = sum(1 for row in stats_rows if "non significative" not in str(row["Interprétation"]).lower() and "Non calculable" not in str(row["Interprétation"]))
        stats_html = f"""
        <div class='report-card'>
            <h3>Résultats statistiques historiques</h3>
            <p>
                Les tests ci-dessous indiquent si les écarts observés entre années sont statistiquement significatifs. Ils permettent de distinguer
                les fluctuations descriptives des différences plus solides. Nombre d’indicateurs significatifs : <b>{significant_count}</b>.
            </p>
            {html_table(stats_rows, ["Indicateur", "p-value", "Interprétation"])}
        </div>
        """

    # -------------------------------------------------
    # Question-level diagnostics
    # -------------------------------------------------
    question_rows = []
    for section_name, item_list in components.items():
        valid_items = [item for item in item_list if item in report_data.columns]
        if not valid_items:
            continue
        qsum = section_question_summary(report_data, valid_items)
        if qsum.empty:
            continue
        q_best = qsum.iloc[0]
        q_weak = qsum.iloc[-1]
        question_rows.append({
            "Section": f"<td>{clean_text(section_name)}</td>",
            "Point fort question": f"<td>{clean_text(score_question_label(q_best['Question']))}<br><b style='color:{USJ_GREEN};'>{fmt_pct2(q_best['Résultat (%)'])}</b></td>",
            "Point à améliorer": f"<td>{clean_text(score_question_label(q_weak['Question']))}<br><b style='color:{USJ_RED if q_weak['Résultat (%)'] < 75 else USJ_ORANGE};'>{fmt_pct2(q_weak['Résultat (%)'])}</b></td>",
        })
    question_html = f"""
    <div class='report-card'>
        <h3>Diagnostic détaillé par section et par question</h3>
        <p>
            Ce tableau descend au niveau des questions afin d’identifier les aspects concrets qui soutiennent les résultats ou qui expliquent les faiblesses.
            Il est particulièrement utile pour transformer les constats statistiques en actions opérationnelles.
        </p>
        {html_table(question_rows, ["Section", "Point fort question", "Point à améliorer"])}
    </div>
    """

    # -------------------------------------------------
    # Complementary questions not included in components
    # -------------------------------------------------
    other_report_df = summarize_other_questions_for_report(df_original, report_data, max_questions=14)
    other_questions_html = ""
    if not other_report_df.empty:
        other_rows = []
        for _, row in other_report_df.iterrows():
            other_rows.append({
                "Catégorie": f"<td>{clean_text(row.get('Catégorie', ''))}</td>",
                "Question": f"<td>{clean_text(row.get('Question affichée', clean_other_question_label(row['Question'])))}</td>",
                "Base applicable": f"<td style='text-align:right;'>{int(row.get('Base applicable', row['N valide']))}</td>",
                "N valide": f"<td style='text-align:right;'>{int(row['N valide'])}</td>",
                "Réponse dominante": f"<td>{clean_text(row['Réponse dominante'])}</td>",
                "Poids": f"<td style='text-align:right; font-weight:800; color:{USJ_BLUE};'>{fmt_pct2(row['Pourcentage'])}</td>",
            })

        # Specific operational signals, when available in the Excel file.
        signal_lines = []
        for _, row in other_report_df.iterrows():
            q_lower = str(row["Question"]).lower()
            if any(term in q_lower for term in ["tuteur", "mobilité", "mobilite", "étranger", "etranger", "échange", "echange"]):
                signal_lines.append(
                    f"<li><b>{clean_text(row.get('Question affichée', clean_other_question_label(row['Question'])))}</b> : réponse dominante <b>{clean_text(row['Réponse dominante'])}</b> ({fmt_pct2(row['Pourcentage'])}, base applicable={int(row.get('Base applicable', row['N valide']))}, N valide={int(row['N valide'])}).</li>"
                )
        signals_html = ""
        if signal_lines:
            signals_html = f"""
            <div class='zone-explain' style='border-left-color:{USJ_GOLD};'>
                <b>Signaux opérationnels à lire avec attention</b>
                <ul>{''.join(signal_lines[:6])}</ul>
            </div>
            """

        other_questions_html = f"""
        <div class='report-card'>
            <h3>Questions complémentaires non intégrées aux composantes</h3>
            <p>
                Cette section exploite les questions du questionnaire qui ne sont pas incluses dans les scores principaux. Elles donnent un contexte essentiel
                pour comprendre les résultats et orienter les décisions. Les questions de tutorat, de mobilité internationale, de parcours et d’administration
                sont automatiquement détectées lorsqu’elles existent dans le fichier Excel.
            </p>
            {signals_html}
            {html_table(other_rows, ["Catégorie", "Question", "Base applicable", "N valide", "Réponse dominante", "Poids"])}
        </div>
        """
    else:
        other_questions_html = """
        <div class='report-card'>
            <h3>Questions complémentaires non intégrées aux composantes</h3>
            <p>Aucune question complémentaire fermée suffisamment exploitable n’a été détectée pour les filtres sélectionnés.</p>
        </div>
        """

    # -------------------------------------------------
    # Recommendations
    # -------------------------------------------------
    rec_items = []
    if not weak_dims.empty:
        for _, row in weak_dims.iterrows():
            rec_items.append(f"Prioriser un plan d’action ciblé sur <b>{clean_text(row['Dimension'])}</b>, dont le résultat est de <b>{fmt_pct2(row['Résultat'])}</b>.")
    if not top_dims.empty:
        for _, row in top_dims.head(2).iterrows():
            rec_items.append(f"Préserver et valoriser <b>{clean_text(row['Dimension'])}</b>, qui constitue un acquis solide à <b>{fmt_pct2(row['Résultat'])}</b>.")
    if importance_html and len(sat_model) >= 30 and feature_columns:
        try:
            main_driver = top_driver["Dimension"]
            rec_items.append(f"Aligner les actions d’amélioration avec le levier explicatif principal : <b>{clean_text(main_driver)}</b>.")
        except Exception:
            pass
    if faculte != "Tous":
        rec_items.append("Comparer les résultats avec la moyenne USJ filtrée afin de distinguer les enjeux propres à la faculté des enjeux institutionnels transversaux.")

    recommendations_html = "".join(f"<li>{item}</li>" for item in rec_items[:7])
    decision_html = f"""
    <div class='report-card decision-card'>
        <h3>Recommandations décisionnelles</h3>
        <ul>{recommendations_html}</ul>
    </div>
    """

    # -------------------------------------------------
    # Executive narrative
    # -------------------------------------------------
    if not dim_table.empty:
        action_text = (
            f"La priorité d’amélioration immédiate concerne <b>{clean_text(weak['Dimension'])}</b>, qui présente le résultat le plus faible "
            f"(<b>{fmt_pct2(weak['Résultat'])}</b>). À l’inverse, <b>{clean_text(best['Dimension'])}</b> constitue le principal point fort "
            f"à préserver et à valoriser (<b>{fmt_pct2(best['Résultat'])}</b>)."
        )
    else:
        action_text = "Les dimensions ne sont pas disponibles pour les filtres sélectionnés."

    executive_text = f"""
    Ce rapport présente une lecture décisionnelle des résultats de l’Exit Survey pour <b>{clean_text(faculty_label)}</b>.
    La satisfaction globale atteint <b>{fmt_pct2(sat)}</b>, le taux de recommandation atteint <b>{fmt_pct2(rec)}</b> et l’expérience globale est évaluée à
    <b>{fmt_pct2(exp)}</b>. {action_text} Les résultats doivent être interprétés conjointement avec les tendances historiques, les écarts par rapport à l’ensemble USJ
    et les facteurs clés d’amélioration, afin de prioriser les actions les plus susceptibles d’améliorer l’expérience étudiante.
    """

    # -------------------------------------------------
    # Customized operational conclusion
    # -------------------------------------------------
    try:
        driver_text = clean_text(top_driver["Dimension"]) if len(sat_model) >= 30 and feature_columns else None
    except Exception:
        driver_text = None

    if faculte != "Tous":
        benchmark_sentence = ""
        if pd.notna(sat_gap):
            if sat_gap >= 1:
                benchmark_sentence = f"Son niveau de satisfaction globale est supérieur à la moyenne USJ filtrée de <b style='color:{USJ_GREEN};'>{fmt_pts(sat_gap)}</b>, ce qui traduit un positionnement favorable à consolider."
            elif sat_gap <= -1:
                benchmark_sentence = f"Son niveau de satisfaction globale est inférieur à la moyenne USJ filtrée de <b style='color:{USJ_RED};'>{fmt_pts(sat_gap)}</b>, ce qui justifie un suivi spécifique au niveau facultaire."
            else:
                benchmark_sentence = f"Son niveau de satisfaction globale est proche de la moyenne USJ filtrée (<b>{fmt_pts(sat_gap)}</b>), ce qui indique un positionnement globalement aligné sur la tendance institutionnelle."

        dim_gap_sentence = ""
        if best_benchmark_dim is not None and weakest_benchmark_dim is not None:
            dim_gap_sentence = (
                f"Par rapport à l’ensemble USJ filtré, le meilleur avantage relatif concerne <b>{clean_text(best_benchmark_dim['Dimension'])}</b> "
                f"(<b style='color:{gap_color(best_benchmark_dim['Écart'])};'>{fmt_pts(best_benchmark_dim['Écart'])}</b>), tandis que le principal retrait concerne "
                f"<b>{clean_text(weakest_benchmark_dim['Dimension'])}</b> (<b style='color:{gap_color(weakest_benchmark_dim['Écart'])};'>{fmt_pts(weakest_benchmark_dim['Écart'])}</b>)."
            )

        driver_sentence = f"Le facteur clé d’amélioration prioritaire à considérer est <b>{driver_text}</b>, car il présente le poids explicatif le plus élevé dans la satisfaction globale." if driver_text else "Les facteurs clés d’amélioration doivent être interprétés avec prudence pour ce périmètre, car l’échantillon disponible peut limiter la robustesse du modèle explicatif."

        conclusion_text = f"""
        Pour <b>{clean_text(faculty_label)}</b>, les résultats doivent être lus comme un outil d’aide à la décision propre au périmètre facultaire sélectionné, et non comme une conclusion générale sur l’ensemble de l’Université.
        La situation actuelle se caractérise par une satisfaction globale de <b>{fmt_pct2(sat)}</b>, un taux de recommandation de <b>{fmt_pct2(rec)}</b> et une expérience globale de <b>{fmt_pct2(exp)}</b>.
        {benchmark_sentence} {dim_gap_sentence}
        Sur le plan opérationnel, la priorité consiste à agir d’abord sur <b>{clean_text(weak['Dimension'])}</b>, qui représente le point le plus fragile du profil facultaire, tout en maintenant les acquis observés sur <b>{clean_text(best['Dimension'])}</b>.
        {driver_sentence} La combinaison du diagnostic par dimension, du positionnement par rapport à l’USJ, des questions complémentaires et des facteurs explicatifs permet de transformer ce rapport en plan d’action facultaire ciblé, mesurable et directement exploitable par l’équipe de direction.
        """
    else:
        driver_sentence = f"Le levier explicatif le plus important pour améliorer la satisfaction globale est <b>{driver_text}</b>." if driver_text else "Les facteurs explicatifs doivent être analysés sur un périmètre suffisamment large pour garantir une interprétation robuste."
        conclusion_text = f"""
        Pour <b>l’ensemble de l’Université</b>, ce rapport fournit une lecture institutionnelle consolidée destinée à orienter les priorités transversales d’amélioration.
        La satisfaction globale atteint <b>{fmt_pct2(sat)}</b>, le taux de recommandation atteint <b>{fmt_pct2(rec)}</b> et l’expérience globale est évaluée à <b>{fmt_pct2(exp)}</b>.
        La priorité institutionnelle concerne <b>{clean_text(weak['Dimension'])}</b>, tandis que <b>{clean_text(best['Dimension'])}</b> constitue un point fort à préserver.
        {driver_sentence} Les résultats doivent être utilisés pour arbitrer les actions communes, identifier les dimensions nécessitant un accompagnement institutionnel et soutenir une amélioration continue fondée sur des données comparables entre années et entre facultés.
        """

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
            max-width: 1120px;
            margin: 0 auto;
            padding: 30px 36px;
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
            font-size: 32px;
            font-weight: 900;
            color: {USJ_BLUE};
            margin: 0;
            line-height: 1.15;
        }}
        .report-subtitle {{
            font-size: 16px;
            color: #5F6B7A;
            margin-top: 8px;
        }}
        .badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 800;
            margin-top: 12px;
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
        .two-col {{
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap:16px;
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
        .report-card h4 {{
            color: {USJ_BLUE};
            margin: 10px 0 8px 0;
            font-size: 17px;
        }}
        .report-card p {{
            font-size: 15.5px;
            line-height: 1.65;
            text-align: justify;
            margin: 0 0 12px 0;
        }}
        .driver-card {{ border-left: 7px solid {USJ_GOLD}; }}
        .decision-card {{ border-left: 7px solid {USJ_GREEN}; background: #F8FCF8; }}
        .decision-card li {{ margin-bottom: 8px; line-height: 1.5; }}
        table.report-table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: auto;
            font-size: 14.2px;
            margin-top: 10px;
        }}
        table.report-table th {{
            background: {USJ_BLUE};
            color: white;
            padding: 10px 12px;
            vertical-align: middle;
            white-space: nowrap;
        }}
        table.report-table td {{
            border-bottom: 1px solid #E6ECF3;
            padding: 9px 12px;
            vertical-align: top;
            overflow-wrap: break-word;
        }}
        table.report-table tr:nth-child(even) td {{
            background-color: #FBFCFE;
        }}
        table.report-table td:last-child,
        table.report-table th:last-child {{
            padding-right: 18px;
        }}
        .zone-explain {{
            margin-top: 12px;
            background: #F7F9FC;
            border: 1px solid #DDE5F0;
            border-left: 6px solid {badge_color};
            border-radius: 14px;
            padding: 12px 14px;
            font-size: 14px;
            line-height: 1.55;
        }}
        .mini-badge {{
            display:inline-block;
            color:#fff;
            padding:4px 9px;
            border-radius:999px;
            font-size:12px;
            font-weight:800;
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
            .report-card {{ page-break-inside: avoid; }}
        }}
    </style>
    </head>
    <body>
        <div class='report-container'>
            <div class='no-print' style='display:flex; justify-content:flex-end; margin-bottom:12px;'>
                <button onclick='window.print()' style='background:#001B75;color:white;border:0;border-radius:12px;padding:10px 16px;font-family:Candara, Arial, sans-serif;font-size:14px;font-weight:800;cursor:pointer;'>Imprimer ce rapport</button>
            </div>
            <div class='report-header'>
                <h1 class='report-title'>{clean_text(report_title)}</h1>
                <div class='report-subtitle'>Période : {clean_text(period_label)} | {clean_text(generated_filters)}</div>
                <div class='badge'>{clean_text(badge_text)}</div>
                <div class='zone-explain'>
                    <b>Comment lire cette classification ?</b> La mention <b>{clean_text(badge_text)}</b> est calculée à partir de la satisfaction globale du périmètre sélectionné.
                    <b>Zone de force</b> signifie que le résultat est supérieur à 75% et peut être considéré comme un acquis solide à préserver.
                    <b>Zone de consolidation</b> indique un résultat entre 50% et 75%, nécessitant un suivi régulier. <b>Zone d’alerte</b> signale un résultat inférieur à 50%, nécessitant une action prioritaire.
                </div>
            </div>

            <div class='kpi-grid'>
                <div class='kpi-box'><div class='kpi-label'>Répondants</div><div class='kpi-value'>{n_resp}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Satisfaction globale</div><div class='kpi-value'>{fmt_pct2(sat)}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Recommandation</div><div class='kpi-value'>{fmt_pct2(rec)}</div></div>
                <div class='kpi-box'><div class='kpi-label'>Expérience globale</div><div class='kpi-value'>{fmt_pct2(exp)}</div></div>
            </div>

            <div class='report-card'>
                <h3>Synthèse exécutive</h3>
                <p>{executive_text}</p>
            </div>

            <div class='two-col'>
                <div class='report-card'>
                    <h3>Forces principales</h3>
                    <p>Ces dimensions constituent les acquis les plus solides du périmètre analysé.</p>
                    {strengths_html}
                </div>
                <div class='report-card'>
                    <h3>Priorités d’amélioration</h3>
                    <p>Ces dimensions doivent être examinées en priorité pour orienter les actions d’amélioration.</p>
                    {priorities_html}
                </div>
            </div>

            {benchmark_html}
            {trend_html}
            {trend_dimension_html}
            {importance_html}
            {stats_html}
            {question_html}
            {other_questions_html}

            <div class='report-card'>
                <h3>Classement complet des dimensions</h3>
                {dim_table_html}
            </div>

            {decision_html}

            <div class='report-card'>
                <h3>Conclusion opérationnelle personnalisée</h3>
                <p>{conclusion_text}</p>
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
        Ce rapport analytique synthétise les indicateurs clés, les forces, les priorités d’amélioration, les évolutions historiques,
        les facteurs explicatifs et les questions complémentaires selon les filtres actuellement sélectionnés.
        Il est conçu pour servir de support direct à la lecture, à l’impression et à la prise de décision.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    try:
        report_html = build_printable_report_html()
    except Exception as exc:
        st.error("Le rapport synthétique n’a pas pu être généré. Vérifiez les filtres ou les colonnes disponibles.")
        st.exception(exc)
        return

    faculty_part = faculte if faculte != "Tous" else "USJ"
    safe_faculty_part = str(faculty_part).replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_name = f"rapport_exit_survey_{safe_faculty_part}.html"

    st.download_button(
        "Télécharger le rapport HTML",
        data=report_html.encode("utf-8"),
        file_name=file_name,
        mime="text/html",
        use_container_width=True,
    )

    st_components.html(
        report_html,
        height=1450,
        scrolling=True,
    )


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


elif page == "Résultats descriptifs de toutes les questions":
    page_all_questions_results()

elif page == "Comparaison historique":
    page_historical_comparison()

elif page == "Facteurs clés d’amélioration":
    page_importance()

elif page == "Résultats descriptifs par section":
    page_descriptive_sections()

elif page == "Autres questions du questionnaire":
    page_other_questions()

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
