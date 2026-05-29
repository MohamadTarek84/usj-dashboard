import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from scipy import stats

# =====================================================
# Configuration
# =====================================================

st.set_page_config(
    page_title="USJ Exit Survey 2022-2025",
    page_icon="📊",
    layout="wide"
)

USJ_BLUE = "#001B75"
USJ_RED = "#C0003B"
USJ_GREEN = "#2E7D32"
USJ_ORANGE = "#F57C00"
USJ_GOLD = "#C9A227"
USJ_PURPLE = "#5B2E91"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_SOFT_GRAY = "#F7F9FC"

# =====================================================
# Useful functions
# =====================================================

@st.cache_data(show_spinner=False)
def load_data():
    possible_files = [
        "Exit_Survey_all-data.xlsx",
        "Exit_Survey_all_data.xlsx",
        "Exit_Survey_all-data.xls",
        "Exit_Survey_all_data.xls",
        "Exit_Survey_Historical_Common_Questions.xlsx",
        "Exit Survey Historical Common Questions.xlsx"
    ]

    for file in possible_files:
        if os.path.exists(file):
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str).str.strip()
            return df

    st.error("Historical Excel file not found.")
    st.write("Available files in the app folder:")
    st.write(os.listdir("."))
    st.stop()


def recode_series(series, mapping):
    return (
        series.astype(str)
        .str.strip()
        .replace(mapping)
        .replace({"nan": np.nan, "None": np.nan, "NaT": np.nan, "<NA>": np.nan})
    )


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


def kpi_card(title, value, subtitle="Score de satisfaction"):
    value_pct = np.nan if pd.isna(value) else value / 4 * 100
    color = kpi_color_percentage(value_pct)
    display_value = "NA" if pd.isna(value_pct) else f"{value_pct:.1f}%"

    st.markdown(
        f"""
        <div style="background-color:white; border-radius:18px; padding:22px;
                    box-shadow:0 4px 14px rgba(0,0,0,0.08);
                    border-left:7px solid {color}; min-height:145px;">
            <div style="font-size:15px; color:#444; font-weight:600;">{title}</div>
            <div style="font-size:38px; color:{color}; font-weight:800; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#777; margin-top:4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def percent_card(title, value, subtitle="Pourcentage"):
    color = kpi_color_percentage(value)
    display_value = "NA" if pd.isna(value) else f"{value:.1f}%"

    st.markdown(
        f"""
        <div style="background-color:white; border-radius:18px; padding:22px;
                    box-shadow:0 4px 14px rgba(0,0,0,0.08);
                    border-left:7px solid {color}; min-height:145px;">
            <div style="font-size:15px; color:#444; font-weight:600;">{title}</div>
            <div style="font-size:38px; color:{color}; font-weight:800; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#777; margin-top:4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def importance_card(title, value, subtitle):
    color = kpi_color_percentage(value)
    display_value = "NA" if pd.isna(value) else f"{value:.1f}%"

    st.markdown(
        f"""
        <div style="background-color:white; border-radius:18px; padding:22px;
                    box-shadow:0 4px 14px rgba(0,0,0,0.08);
                    border-left:7px solid {color}; min-height:155px;">
            <div style="font-size:15px; color:#444; font-weight:700;">{title}</div>
            <div style="font-size:36px; color:{color}; font-weight:900; margin-top:8px;">{display_value}</div>
            <div style="font-size:13px; color:#777; margin-top:4px;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def summary_box(text, color=USJ_BLUE, background="#F7F9FC"):
    st.html(
        f"""
        <div style="
            background-color:{background};
            border-left:6px solid {color};
            padding:18px;
            border-radius:14px;
            margin-top:20px;
            margin-bottom:20px;
            font-size:16px;
            line-height:1.6;
        ">
            {text}
        </div>
        """
    )


def component_columns_available(df):
    cols = [
        "Score satisfaction globale",
        "Score expérience globale USJ",
        "Score enseignement et apprentissage",
        "Score accompagnement et encadrement",
        "Score développement des compétences",
        "Score services USJ",
        "Score vie étudiante et activités",
        "Score infrastructures et équipements",
        "Score frais / qualité enseignement",
        "Score frais / autres universités"
    ]
    return [c for c in cols if c in df.columns]


# =====================================================
# Cached preprocessing
# =====================================================

@st.cache_data(show_spinner=False)
def prepare_data():
    df_original = load_data()
    df_coded = df_original.copy()

    # Make sure the historical year column is standardized.
    if "Year" not in df_coded.columns and "Année" in df_coded.columns:
        df_coded = df_coded.rename(columns={"Année": "Year"})
        df_original = df_original.rename(columns={"Année": "Year"})

    if "Year" in df_coded.columns:
        df_coded["Year"] = df_coded["Year"].astype(str).str.strip()
        df_original["Year"] = df_original["Year"].astype(str).str.strip()

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

    def recode_items(items, mapping):
        existing = [col for col in items if col in df_coded.columns]
        for col in existing:
            df_coded[col] = pd.to_numeric(
                recode_series(df_original[col], mapping),
                errors="coerce"
            )
        return existing

    enseignement_existing = recode_items(enseignement_items, satisfaction_mapping_f)
    accompagnement_existing = recode_items(accompagnement_items, satisfaction_mapping_f)
    competences_existing = recode_items(competences_items, accord_mapping)
    experience_existing = recode_items(experience_items, satisfaction_mapping_f)
    services_existing = recode_items(services_items, satisfaction_mapping_f)
    infrastructures_existing = recode_items(infrastructures_items, satisfaction_mapping_f)

    for col in vie_items:
        df_coded[col] = pd.to_numeric(
            recode_series(df_original[col], vie_mapping),
            errors="coerce"
        )

    def mean_or_nan(existing_items):
        if len(existing_items) == 0:
            return np.nan
        return df_coded[existing_items].mean(axis=1, skipna=True)

    df_coded["Score enseignement et apprentissage"] = mean_or_nan(enseignement_existing)
    df_coded["Score accompagnement et encadrement"] = mean_or_nan(accompagnement_existing)
    df_coded["Score développement des compétences"] = mean_or_nan(competences_existing)
    df_coded["Score expérience globale USJ"] = mean_or_nan(experience_existing)
    df_coded["Score services USJ"] = mean_or_nan(services_existing)
    df_coded["Score vie étudiante et activités"] = mean_or_nan(vie_items)
    df_coded["Score infrastructures et équipements"] = mean_or_nan(infrastructures_existing)

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

    components = {
        "Enseignement et apprentissage": enseignement_existing,
        "Accompagnement et encadrement": accompagnement_existing,
        "Développement des compétences": competences_existing,
        "Expérience globale USJ": experience_existing,
        "Services de l’USJ": services_existing,
        "Vie étudiante et activités": vie_items,
        "Infrastructures et équipements": infrastructures_existing
    }

    return df_original, df_coded, components, q42, q43, q26, q27


# =====================================================
# Cached machine learning functions
# =====================================================

@st.cache_data(show_spinner=False)
def train_satisfaction_importance(model_sat, feature_columns):
    X = model_sat[feature_columns]
    y = model_sat["Score satisfaction globale"]

    rf = RandomForestRegressor(
        n_estimators=150,
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
        n_estimators=150,
        random_state=42,
        max_depth=5,
        class_weight="balanced",
        n_jobs=-1
    )

    rf.fit(X, y)
    return rf.feature_importances_


# =====================================================
# Load prepared data
# =====================================================

with st.spinner("Chargement du tableau de bord..."):
    df_original, df_coded, components, q42, q43, q26, q27 = prepare_data()

# =====================================================
# Header with USJ / UAQ logo
# =====================================================

logo_candidates = [
    "LogoUAQ.png",
    "usj_uaq_logo.png",
    "USJ_UAQ_logo.png",
    "usj_logo.png",
    "image.png"
]

logo_path = next((logo for logo in logo_candidates if os.path.exists(logo)), None)

header_left, header_right = st.columns([4.5, 1.5], vertical_alignment="center")

with header_left:
    st.markdown(
        f"""
        <h1 style="color:{USJ_BLUE}; margin-bottom:0; font-size:36px; font-weight:800;">
            Tableau de bord – Exit Survey USJ 2022-2025
        </h1>
        <p style="font-size:18px; color:#555; margin-top:4px;">
            Indicateurs clés de satisfaction, tendances historiques et facteurs d’amélioration
        </p>
        """,
        unsafe_allow_html=True
    )

with header_right:
    if logo_path is not None:
        st.image(logo_path, width=300)

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
if genre != "Tous" and "Genre" in df_after_genre.columns:
    df_after_genre = df_after_genre[df_after_genre["Genre"].astype(str) == genre]

with filter_cols[2]:
    faculte = st.selectbox("Faculté", filter_options(df_after_genre, "Faculté_Institut_g"), key="filter_faculte")

df_after_faculte = df_after_genre.copy()
if faculte != "Tous" and "Faculté_Institut_g" in df_after_faculte.columns:
    df_after_faculte = df_after_faculte[df_after_faculte["Faculté_Institut_g"].astype(str) == faculte]

with filter_cols[3]:
    cursus = st.selectbox("Cursus", filter_options(df_after_faculte, "Cursus"), key="filter_cursus")

df_after_cursus = df_after_faculte.copy()
if cursus != "Tous" and "Cursus" in df_after_cursus.columns:
    df_after_cursus = df_after_cursus[df_after_cursus["Cursus"].astype(str) == cursus]

with filter_cols[4]:
    niveau = st.selectbox("Niveau", filter_options(df_after_cursus, "Niveau"), key="filter_niveau")

df_filtered = df_after_cursus.copy()
if niveau != "Tous" and "Niveau" in df_filtered.columns:
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
        "Résultats descriptifs par section",
        "Facteurs clés d’amélioration",
        "Méthodologie des composantes"
    ],
    horizontal=True
)

# =====================================================
# Page 1
# =====================================================

def page_indicators():
    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Satisfaction globale et expérience</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    satisfaction_pct = pct_from_mean(df_filtered["Score satisfaction globale"].mean())
    recommandation_pct = calculate_recommendation_rate(df_filtered, q43)

    with c1:
        kpi_card("Satisfaction globale à l’Université", df_filtered["Score satisfaction globale"].mean())

    with c2:
        percent_card("Taux de recommandation de l’USJ", recommandation_pct)

    with c3:
        kpi_card("Expérience globale USJ", df_filtered["Score expérience globale USJ"].mean())

    c4, c5, c6 = st.columns(3)

    with c4:
        kpi_card("Enseignement et apprentissage", df_filtered["Score enseignement et apprentissage"].mean())

    with c5:
        kpi_card("Accompagnement et encadrement", df_filtered["Score accompagnement et encadrement"].mean())

    with c6:
        kpi_card("Développement des compétences", df_filtered["Score développement des compétences"].mean())

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Vie étudiante, services et environnement</h2>", unsafe_allow_html=True)

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

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Perception financière</h2>", unsafe_allow_html=True)

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

    if not component_summary.empty and not pd.isna(satisfaction_pct) and not pd.isna(recommandation_pct):
        best_dimension = component_summary.sort_values("Pourcentage", ascending=False).iloc[0]
        weakest_dimension = component_summary.sort_values("Pourcentage", ascending=True).iloc[0]

        selected_year_text = "toutes les années" if year == "Tous" else year

        summary_box(
            f"""
            <b>Lecture synthétique :</b><br>
            Pour les filtres sélectionnés sur <b>{selected_year_text}</b>, la satisfaction globale atteint
            <b>{satisfaction_pct:.1f}%</b>, tandis que le taux de recommandation de l’USJ est de
            <b>{recommandation_pct:.1f}%</b>. La dimension la mieux évaluée est
            <b>{best_dimension["Dimension"]}</b> avec <b>{best_dimension["Pourcentage"]:.1f}%</b>.
            La dimension la plus faible est <b>{weakest_dimension["Dimension"]}</b> avec
            <b>{weakest_dimension["Pourcentage"]:.1f}%</b>, ce qui en fait un axe prioritaire
            à suivre dans les actions d’amélioration.
            """,
            color=USJ_BLUE,
            background="#F7F9FC"
        )

# =====================================================
# Page 2 - Historical comparison
# =====================================================

def page_historical_comparison():
    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Comparaison historique des résultats</h2>", unsafe_allow_html=True)

    summary_box(
        """
        Cette page présente une analyse comparative des résultats de l’Exit Survey sur les années disponibles.
        Elle permet d’identifier les tendances, les écarts entre années, les dimensions en progression ou en recul,
        ainsi que les différences statistiquement significatives. Les résultats sont calculés selon les filtres actifs.
        """,
        color=USJ_BLUE,
        background="#F7F9FC"
    )

    if "Year" not in df_filtered.columns:
        st.error("La colonne Year est introuvable dans le fichier historique.")
        return

    years_available = sorted(df_filtered["Year"].dropna().astype(str).unique())

    if len(years_available) < 2:
        st.warning("Pour comparer les années, sélectionnez Année = Tous ou gardez au moins deux années dans les données filtrées.")
        return

    component_map = {
        "Satisfaction globale": "Score satisfaction globale",
        "Expérience globale USJ": "Score expérience globale USJ",
        "Enseignement et apprentissage": "Score enseignement et apprentissage",
        "Accompagnement et encadrement": "Score accompagnement et encadrement",
        "Développement des compétences": "Score développement des compétences",
        "Services de l’USJ": "Score services USJ",
        "Vie étudiante et activités": "Score vie étudiante et activités",
        "Infrastructures et équipements": "Score infrastructures et équipements",
        "Frais / qualité de l’enseignement": "Score frais / qualité enseignement",
        "Frais / autres universités": "Score frais / autres universités"
    }

    component_map = {k: v for k, v in component_map.items() if v in df_filtered.columns}

    # -------------------------------------------------
    # Yearly comparison table
    # -------------------------------------------------

    rows = []

    for y in years_available:
        sub = df_filtered[df_filtered["Year"].astype(str) == y]
        row = {"Année": y, "Nombre de répondants": len(sub)}

        for label, col in component_map.items():
            row[label] = pct_from_mean(sub[col].mean())

        row["Taux de recommandation"] = calculate_recommendation_rate(sub, q43)
        rows.append(row)

    trend_df = pd.DataFrame(rows)

    # Ensure chronological order when labels are standard strings.
    trend_df["Année"] = trend_df["Année"].astype(str)
    trend_df = trend_df.sort_values("Année")

    last_year = trend_df["Année"].iloc[-1]
    previous_year = trend_df["Année"].iloc[-2] if len(trend_df) >= 2 else trend_df["Année"].iloc[-1]

    def get_year_value(indicator, year_value):
        vals = trend_df.loc[trend_df["Année"] == year_value, indicator]
        return vals.iloc[0] if len(vals) > 0 else np.nan

    sat_last = get_year_value("Satisfaction globale", last_year) if "Satisfaction globale" in trend_df.columns else np.nan
    sat_prev = get_year_value("Satisfaction globale", previous_year) if "Satisfaction globale" in trend_df.columns else np.nan
    rec_last = get_year_value("Taux de recommandation", last_year) if "Taux de recommandation" in trend_df.columns else np.nan
    rec_prev = get_year_value("Taux de recommandation", previous_year) if "Taux de recommandation" in trend_df.columns else np.nan

    diff_sat = sat_last - sat_prev if pd.notna(sat_last) and pd.notna(sat_prev) else np.nan
    diff_rec = rec_last - rec_prev if pd.notna(rec_last) and pd.notna(rec_prev) else np.nan

    # Identify strongest improvement and strongest decline.
    diff_rows_for_cards = []
    for col in trend_df.columns:
        if col in ["Année", "Nombre de répondants"]:
            continue
        v_last = get_year_value(col, last_year)
        v_prev = get_year_value(col, previous_year)
        if pd.notna(v_last) and pd.notna(v_prev):
            diff_rows_for_cards.append({"Indicateur": col, "Écart": v_last - v_prev})

    diff_card_df = pd.DataFrame(diff_rows_for_cards)
    if not diff_card_df.empty:
        strongest_up = diff_card_df.sort_values("Écart", ascending=False).iloc[0]
        strongest_down = diff_card_df.sort_values("Écart", ascending=True).iloc[0]
    else:
        strongest_up = {"Indicateur": "NA", "Écart": np.nan}
        strongest_down = {"Indicateur": "NA", "Écart": np.nan}

    st.subheader("Résumé exécutif de l’évolution")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        importance_card(
            f"Satisfaction globale {last_year}",
            sat_last,
            f"Écart vs {previous_year}: {diff_sat:+.1f} pts" if pd.notna(diff_sat) else "Écart non disponible"
        )

    with c2:
        importance_card(
            f"Recommandation {last_year}",
            rec_last,
            f"Écart vs {previous_year}: {diff_rec:+.1f} pts" if pd.notna(diff_rec) else "Écart non disponible"
        )

    with c3:
        importance_card(
            "Plus forte progression",
            abs(strongest_up["Écart"]) if pd.notna(strongest_up["Écart"]) else np.nan,
            f"{strongest_up['Indicateur']} ({strongest_up['Écart']:+.1f} pts)" if pd.notna(strongest_up["Écart"]) else "Non disponible"
        )

    with c4:
        importance_card(
            "Plus fort recul",
            abs(strongest_down["Écart"]) if pd.notna(strongest_down["Écart"]) else np.nan,
            f"{strongest_down['Indicateur']} ({strongest_down['Écart']:+.1f} pts)" if pd.notna(strongest_down["Écart"]) else "Non disponible"
        )

    # -------------------------------------------------
    # Detailed comparison table
    # -------------------------------------------------

    st.subheader("Tableau comparatif détaillé par année")

    format_dict = {col: "{:.1f}%" for col in trend_df.columns if col not in ["Année", "Nombre de répondants"]}
    st.dataframe(
        trend_df.style.format(format_dict),
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------
    # Main trend chart with labels
    # -------------------------------------------------

    st.subheader("Évolution de la satisfaction globale et de la recommandation")

    main_cols = [col for col in ["Satisfaction globale", "Taux de recommandation"] if col in trend_df.columns]
    main_trend = trend_df[["Année"] + main_cols].melt(
        id_vars="Année",
        var_name="Indicateur",
        value_name="Pourcentage"
    )

    fig_main = px.line(
        main_trend,
        x="Année",
        y="Pourcentage",
        color="Indicateur",
        markers=True,
        text="Pourcentage",
        title="Évolution de la satisfaction globale et de la recommandation"
    )

    fig_main.update_traces(
        mode="lines+markers+text",
        texttemplate="%{text:.1f}%",
        textposition="top center",
        line=dict(width=4),
        marker=dict(size=10)
    )

    fig_main.update_layout(
        yaxis_title="Pourcentage",
        xaxis_title="Année",
        height=460,
        legend_title="",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=70, b=40)
    )

    st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": False})

    # -------------------------------------------------
    # Heatmap of dimensions by year
    # -------------------------------------------------

    st.subheader("Carte de chaleur des dimensions par année")

    dimensions_for_heatmap = [label for label in component_map.keys() if label != "Satisfaction globale"]
    heatmap_df = trend_df[["Année"] + dimensions_for_heatmap].copy()
    heatmap_long = heatmap_df.melt(
        id_vars="Année",
        var_name="Dimension",
        value_name="Pourcentage"
    )

    fig_heat = px.imshow(
        heatmap_df.set_index("Année")[dimensions_for_heatmap].T,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale=[USJ_RED, USJ_BLUE, USJ_GREEN],
        title="Niveau des dimensions par année (%)"
    )

    fig_heat.update_layout(
        height=540,
        xaxis_title="Année",
        yaxis_title="Dimension",
        coloraxis_colorbar_title="%",
        margin=dict(l=20, r=20, t=70, b=40)
    )

    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    # -------------------------------------------------
    # Grouped bar chart of components
    # -------------------------------------------------

    st.subheader("Comparaison visuelle des dimensions")

    fig_comp = px.bar(
        heatmap_long,
        x="Dimension",
        y="Pourcentage",
        color="Année",
        barmode="group",
        text="Pourcentage",
        title="Comparaison des dimensions par année"
    )

    fig_comp.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_comp.update_layout(
        yaxis_title="Pourcentage",
        xaxis_title="",
        height=620,
        xaxis_tickangle=-35,
        legend_title="Année",
        margin=dict(l=20, r=20, t=70, b=150)
    )

    st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

    # -------------------------------------------------
    # Year-over-year differences with colors
    # -------------------------------------------------

    st.subheader(f"Écarts entre {previous_year} et {last_year}")

    diff_rows = []
    for col in trend_df.columns:
        if col in ["Année", "Nombre de répondants"]:
            continue

        val_last = get_year_value(col, last_year)
        val_prev = get_year_value(col, previous_year)

        if pd.notna(val_last) and pd.notna(val_prev):
            diff_rows.append({
                "Indicateur": col,
                previous_year: round(val_prev, 1),
                last_year: round(val_last, 1),
                "Écart en points": round(val_last - val_prev, 1)
            })

    diff_df = pd.DataFrame(diff_rows).sort_values("Écart en points", ascending=False)

    fig_diff = px.bar(
        diff_df,
        x="Écart en points",
        y="Indicateur",
        orientation="h",
        text="Écart en points",
        color="Écart en points",
        color_continuous_scale=[USJ_RED, "#E8E8E8", USJ_GREEN],
        title=f"Variation en points entre {previous_year} et {last_year}"
    )

    fig_diff.update_traces(texttemplate="%{text:+.1f} pts", textposition="outside")
    fig_diff.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="Écart en points",
        yaxis_title="",
        height=560,
        coloraxis_showscale=False,
        margin=dict(l=20, r=40, t=70, b=40)
    )

    st.plotly_chart(fig_diff, use_container_width=True, config={"displayModeBar": False})

    st.dataframe(
        diff_df.style.format({previous_year: "{:.1f}%", last_year: "{:.1f}%", "Écart en points": "{:+.1f}"}),
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------
    # Statistical tests
    # -------------------------------------------------

    st.subheader("Tests statistiques de comparaison entre les années")

    test_rows = []

    for label, col in component_map.items():
        groups = []
        valid_years = []
        ns_by_year = []
        means_by_year = []

        for y in years_available:
            vals = df_filtered[df_filtered["Year"].astype(str) == y][col].dropna()
            if len(vals) >= 5:
                groups.append(vals)
                valid_years.append(y)
                ns_by_year.append(len(vals))
                means_by_year.append(vals.mean())

        if len(groups) >= 2:
            try:
                f_stat, p_value = stats.f_oneway(*groups)
            except Exception:
                f_stat, p_value = np.nan, np.nan

            try:
                all_vals = pd.concat(groups)
                grand_mean = all_vals.mean()
                ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
                ss_total = ((all_vals - grand_mean) ** 2).sum()
                eta_sq = ss_between / ss_total if ss_total != 0 else np.nan
            except Exception:
                eta_sq = np.nan
        else:
            f_stat, p_value, eta_sq = np.nan, np.nan, np.nan

        test_rows.append({
            "Dimension": label,
            "Test": "ANOVA",
            "Années comparées": ", ".join(valid_years),
            "N valide total": int(sum(ns_by_year)) if ns_by_year else 0,
            "p-value": p_value,
            "Taille d’effet": eta_sq,
            "Résultat": "Différence significative" if pd.notna(p_value) and p_value < 0.05 else "Non significatif"
        })

    # Chi-square for recommendation
    if q43 in df_filtered.columns:
        rec_data = df_filtered[["Year", q43]].copy()
        rec_data[q43] = rec_data[q43].astype(str).str.strip()
        rec_data = rec_data[rec_data[q43].isin(["Oui", "Non"])]

        if rec_data["Year"].nunique() >= 2 and rec_data[q43].nunique() >= 2:
            contingency = pd.crosstab(rec_data["Year"], rec_data[q43])
            try:
                chi2, p_rec, dof, expected = stats.chi2_contingency(contingency)
                n_total = contingency.values.sum()
                min_dim = min(contingency.shape) - 1
                cramers_v = np.sqrt(chi2 / (n_total * min_dim)) if n_total > 0 and min_dim > 0 else np.nan
            except Exception:
                p_rec, cramers_v = np.nan, np.nan

            test_rows.append({
                "Dimension": "Taux de recommandation",
                "Test": "Chi-square",
                "Années comparées": ", ".join(sorted(rec_data["Year"].astype(str).unique())),
                "N valide total": len(rec_data),
                "p-value": p_rec,
                "Taille d’effet": cramers_v,
                "Résultat": "Différence significative" if pd.notna(p_rec) and p_rec < 0.05 else "Non significatif"
            })

    tests_df = pd.DataFrame(test_rows)
    tests_df["p-value"] = tests_df["p-value"].apply(lambda x: np.nan if pd.isna(x) else round(x, 4))
    tests_df["Taille d’effet"] = tests_df["Taille d’effet"].apply(lambda x: np.nan if pd.isna(x) else round(x, 4))

    st.dataframe(tests_df, use_container_width=True, hide_index=True)

    significant = tests_df[tests_df["Résultat"] == "Différence significative"]

    if len(significant) > 0:
        sig_list = ", ".join(significant["Dimension"].tolist())
        summary_box(
            f"""
            <b>Lecture statistique :</b><br>
            Les différences entre les années sont statistiquement significatives pour :
            <b>{sig_list}</b>. Cela signifie que les écarts observés ne sont pas uniquement descriptifs
            et peuvent être considérés comme statistiquement confirmés au seuil de 5%.
            """,
            color=USJ_GREEN,
            background="#F3FAF5"
        )
    else:
        summary_box(
            """
            <b>Lecture statistique :</b><br>
            Aucun écart statistiquement significatif n’a été détecté entre les années pour les dimensions analysées.
            Les variations observées doivent donc être interprétées avec prudence comme des différences descriptives.
            """,
            color=USJ_ORANGE,
            background="#FFF8F0"
        )

    # -------------------------------------------------
    # Optional faculty heatmap when all faculties are shown
    # -------------------------------------------------

    if "Faculté_Institut_g" in df_filtered.columns and faculte == "Tous":
        st.subheader("Comparaison par faculté et par année")

        faculty_metric = st.selectbox(
            "Choisir l’indicateur à comparer par faculté",
            ["Satisfaction globale", "Taux de recommandation"] + dimensions_for_heatmap,
            key="faculty_metric_comparison"
        )

        if faculty_metric == "Taux de recommandation":
            fac_rows = []
            for (fac, y), sub in df_filtered.groupby(["Faculté_Institut_g", "Year"]):
                fac_rows.append({
                    "Faculté": fac,
                    "Année": y,
                    "Pourcentage": calculate_recommendation_rate(sub, q43),
                    "N": len(sub)
                })
            fac_df = pd.DataFrame(fac_rows)
        else:
            metric_col = component_map.get(faculty_metric)
            fac_df = (
                df_filtered.groupby(["Faculté_Institut_g", "Year"])[metric_col]
                .mean()
                .reset_index()
                .rename(columns={"Faculté_Institut_g": "Faculté", metric_col: "Moyenne"})
            )
            fac_df["Pourcentage"] = fac_df["Moyenne"].apply(pct_from_mean)
            fac_df["N"] = df_filtered.groupby(["Faculté_Institut_g", "Year"]).size().values

        fac_pivot = fac_df.pivot(index="Faculté", columns="Année", values="Pourcentage")
        fac_pivot = fac_pivot.dropna(how="all")

        fig_fac = px.imshow(
            fac_pivot,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale=[USJ_RED, USJ_BLUE, USJ_GREEN],
            title=f"{faculty_metric} par faculté et par année (%)"
        )

        fig_fac.update_layout(
            height=max(450, 28 * len(fac_pivot)),
            xaxis_title="Année",
            yaxis_title="Faculté",
            coloraxis_colorbar_title="%"
        )

        st.plotly_chart(fig_fac, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Voir le tableau détaillé par faculté"):
            st.dataframe(fac_df.sort_values(["Faculté", "Année"]), use_container_width=True, hide_index=True)



# =====================================================
# Page 3 - Descriptive results by survey section
# =====================================================

def short_question_label(question, max_len=78):
    question = str(question).strip()
    if len(question) <= max_len:
        return question
    return question[:max_len - 3] + "..."


def section_score_column(section_name):
    mapping = {
        "Enseignement et apprentissage": "Score enseignement et apprentissage",
        "Accompagnement et encadrement": "Score accompagnement et encadrement",
        "Développement des compétences": "Score développement des compétences",
        "Expérience globale USJ": "Score expérience globale USJ",
        "Services de l’USJ": "Score services USJ",
        "Vie étudiante et activités": "Score vie étudiante et activités",
        "Infrastructures et équipements": "Score infrastructures et équipements",
        "Perception financière": None,
        "Satisfaction globale et recommandation": None
    }
    return mapping.get(section_name)


def descriptive_section_items():
    sections = dict(components)
    financial_items = [col for col in [q26, q27] if col in df_coded.columns]
    if financial_items:
        sections["Perception financière"] = financial_items
    global_items = [col for col in [q42, q43] if col in df_original.columns]
    if global_items:
        sections["Satisfaction globale et recommandation"] = global_items
    return sections


def make_item_summary(data, items, section_name):
    rows = []
    for item in items:
        if item == q43:
            rate = calculate_recommendation_rate(data, q43)
            rows.append({
                "Question": item,
                "Libellé court": short_question_label(item),
                "Indicateur (%)": rate,
                "Moyenne /4": np.nan,
                "N valide": data[item].notna().sum() if item in data.columns else 0,
                "Manquants (%)": round(data[item].isna().mean() * 100, 1) if item in data.columns else np.nan,
                "Type": "Recommandation"
            })
        elif item in data.columns:
            numeric = pd.to_numeric(data[item], errors="coerce")
            mean_value = numeric.mean()
            rows.append({
                "Question": item,
                "Libellé court": short_question_label(item),
                "Indicateur (%)": pct_from_mean(mean_value),
                "Moyenne /4": mean_value,
                "N valide": numeric.notna().sum(),
                "Manquants (%)": round(numeric.isna().mean() * 100, 1),
                "Type": "Moyenne"
            })
    return pd.DataFrame(rows)


def make_distribution_table(raw_data, coded_data, item):
    rows = []
    if item not in raw_data.columns and item not in coded_data.columns:
        return pd.DataFrame()

    base = raw_data[item] if item in raw_data.columns else coded_data[item]
    years = sorted(coded_data["Year"].dropna().astype(str).unique()) if "Year" in coded_data.columns else ["Tous"]

    for y in years:
        if "Year" in coded_data.columns:
            idx = coded_data[coded_data["Year"].astype(str) == y].index
            s = base.loc[idx]
        else:
            s = base
        s = s.dropna().astype(str).str.strip()
        total = len(s)
        if total == 0:
            continue
        counts = s.value_counts().reset_index()
        counts.columns = ["Réponse", "Effectif"]
        counts["Pourcentage"] = counts["Effectif"] / total * 100
        counts["Année"] = y
        rows.append(counts)

    if rows:
        return pd.concat(rows, ignore_index=True)
    return pd.DataFrame()


def page_descriptive_sections():
    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Résultats descriptifs par section</h2>", unsafe_allow_html=True)

    summary_box(
        """
        Cette page présente les résultats détaillés des questions regroupées par section du questionnaire.
        Elle permet de visualiser les moyennes, les pourcentages, les distributions de réponses et les corrélations
        entre les items d’une même section et leur moyenne globale. Les résultats restent dynamiques selon les filtres actifs.
        """,
        color=USJ_BLUE,
        background=USJ_LIGHT_BLUE
    )

    sections = descriptive_section_items()
    section_names = list(sections.keys())

    c_left, c_right = st.columns([2.2, 1])
    with c_left:
        selected_section = st.selectbox(
            "Choisir une section du questionnaire",
            section_names,
            key="descriptive_section_selector"
        )
    with c_right:
        show_raw_distribution = st.toggle(
            "Afficher la distribution détaillée d’une question",
            value=True
        )

    items = [col for col in sections[selected_section] if col in df_coded.columns or col in df_original.columns]
    numeric_items = [col for col in items if col in df_coded.columns and pd.to_numeric(df_coded[col], errors="coerce").notna().sum() > 0]
    raw_filtered = df_original.loc[df_filtered.index].copy()

    if not items:
        st.warning("Aucune question disponible pour cette section dans les données filtrées.")
        return

    section_col = section_score_column(selected_section)
    if section_col is not None and section_col in df_filtered.columns:
        section_pct = pct_from_mean(df_filtered[section_col].mean())
    elif selected_section == "Perception financière":
        finance_cols = ["Score frais / qualité enseignement", "Score frais / autres universités"]
        finance_cols = [c for c in finance_cols if c in df_filtered.columns]
        section_pct = pct_from_mean(df_filtered[finance_cols].mean(axis=1).mean()) if finance_cols else np.nan
    elif selected_section == "Satisfaction globale et recommandation":
        section_pct = pct_from_mean(df_filtered["Score satisfaction globale"].mean()) if "Score satisfaction globale" in df_filtered.columns else np.nan
    else:
        section_pct = np.nan

    valid_n_section = int(df_filtered[numeric_items].notna().any(axis=1).sum()) if numeric_items else len(df_filtered)

    k1, k2, k3 = st.columns(3)
    with k1:
        percent_card("Résultat moyen de la section", section_pct, selected_section)
    with k2:
        importance_card("Questions analysées", len(items) / max(len(items), 1) * 100, f"{len(items)} questions")
    with k3:
        importance_card("Répondants valides", valid_n_section / max(len(df_filtered), 1) * 100, f"{valid_n_section} sur {len(df_filtered)}")

    item_summary = make_item_summary(df_filtered, items, selected_section)

    if not item_summary.empty:
        item_summary_display = item_summary.copy()
        item_summary_display["Indicateur (%)"] = item_summary_display["Indicateur (%)"].round(1)
        item_summary_display["Moyenne /4"] = item_summary_display["Moyenne /4"].round(2)

        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Synthèse des questions de la section</h3>", unsafe_allow_html=True)
        st.dataframe(
            item_summary_display[["Libellé court", "Indicateur (%)", "Moyenne /4", "N valide", "Manquants (%)", "Type"]],
            use_container_width=True,
            hide_index=True
        )

        fig_items = px.bar(
            item_summary.sort_values("Indicateur (%)", ascending=True),
            x="Indicateur (%)",
            y="Libellé court",
            orientation="h",
            text="Indicateur (%)",
            color="Indicateur (%)",
            color_continuous_scale=[USJ_RED, USJ_BLUE, USJ_GOLD, USJ_GREEN],
            title=f"Résultats détaillés des questions – {selected_section}"
        )
        fig_items.update_layout(
            height=max(430, 45 * len(item_summary)),
            xaxis_title="Pourcentage /4",
            yaxis_title="",
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig_items.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_items, use_container_width=True, config={"displayModeBar": False})

    # -------------------------------------------------
    # Historical view for section items
    # -------------------------------------------------
    if "Year" in df_filtered.columns and len(df_filtered["Year"].dropna().unique()) > 1 and numeric_items:
        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Évolution par année dans la section</h3>", unsafe_allow_html=True)
        year_rows = []
        for y in sorted(df_filtered["Year"].dropna().astype(str).unique()):
            sub = df_filtered[df_filtered["Year"].astype(str) == y]
            for item in numeric_items:
                year_rows.append({
                    "Année": y,
                    "Question": short_question_label(item),
                    "Résultat (%)": pct_from_mean(pd.to_numeric(sub[item], errors="coerce").mean())
                })
        year_item_df = pd.DataFrame(year_rows).dropna()
        if not year_item_df.empty:
            fig_year = px.line(
                year_item_df,
                x="Année",
                y="Résultat (%)",
                color="Question",
                markers=True,
                text="Résultat (%)",
                title=f"Évolution des questions – {selected_section}",
                color_discrete_sequence=[USJ_BLUE, USJ_RED, USJ_GREEN, USJ_ORANGE, USJ_PURPLE, USJ_GOLD]
            )
            fig_year.update_traces(mode="lines+markers+text", texttemplate="%{text:.1f}%", textposition="top center")
            fig_year.update_layout(height=520, yaxis_title="Résultat (%)", xaxis_title="Année", plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig_year, use_container_width=True, config={"displayModeBar": False})

    # -------------------------------------------------
    # Distribution of one question
    # -------------------------------------------------
    if show_raw_distribution:
        st.markdown(f"<h3 style='color:{USJ_BLUE};'>Distribution interactive des réponses</h3>", unsafe_allow_html=True)
        selected_question = st.selectbox(
            "Choisir une question pour afficher la distribution des réponses",
            items,
            format_func=lambda x: short_question_label(x, 120),
            key="distribution_question_selector"
        )
        dist_df = make_distribution_table(raw_filtered, df_filtered, selected_question)
        if not dist_df.empty:
            fig_dist = px.bar(
                dist_df,
                x="Réponse",
                y="Pourcentage",
                color="Année",
                barmode="group",
                text="Pourcentage",
                title="Distribution des réponses par année",
                color_discrete_sequence=[USJ_BLUE, USJ_RED, USJ_GREEN, USJ_ORANGE, USJ_PURPLE, USJ_GOLD]
            )
            fig_dist.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_dist.update_layout(height=480, xaxis_title="Réponse", yaxis_title="Pourcentage", plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False})
            st.dataframe(dist_df.sort_values(["Année", "Réponse"]), use_container_width=True, hide_index=True)
        else:
            st.info("Aucune distribution disponible pour cette question avec les filtres actuels.")

    # -------------------------------------------------
    # Correlation heatmap
    # -------------------------------------------------
    st.markdown(f"<h3 style='color:{USJ_BLUE};'>Corrélation entre les questions et la moyenne de la section</h3>", unsafe_allow_html=True)

    if len(numeric_items) < 2:
        st.info("La heatmap de corrélation nécessite au moins deux questions numériques dans la section.")
    else:
        corr_data = df_filtered[numeric_items].apply(pd.to_numeric, errors="coerce").copy()
        corr_data["Moyenne de la section"] = corr_data[numeric_items].mean(axis=1, skipna=True)
        corr_matrix = corr_data.corr().round(2)

        labels = [short_question_label(c, 38) if c != "Moyenne de la section" else c for c in corr_matrix.columns]
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale=[USJ_RED, "#FFFFFF", USJ_BLUE],
            zmin=-1,
            zmax=1,
            title=f"Heatmap des corrélations – {selected_section}"
        )
        fig_corr.update_xaxes(ticktext=labels, tickvals=list(range(len(labels))))
        fig_corr.update_yaxes(ticktext=labels, tickvals=list(range(len(labels))))
        fig_corr.update_layout(height=max(520, 55 * len(labels)), plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})

        corr_with_mean = corr_matrix["Moyenne de la section"].drop("Moyenne de la section").sort_values(ascending=False).reset_index()
        corr_with_mean.columns = ["Question", "Corrélation avec la moyenne"]
        corr_with_mean["Question"] = corr_with_mean["Question"].apply(lambda x: short_question_label(x, 110))

        fig_corr_bar = px.bar(
            corr_with_mean.sort_values("Corrélation avec la moyenne", ascending=True),
            x="Corrélation avec la moyenne",
            y="Question",
            orientation="h",
            text="Corrélation avec la moyenne",
            color="Corrélation avec la moyenne",
            color_continuous_scale=[USJ_ORANGE, USJ_BLUE, USJ_GREEN],
            title="Questions les plus liées à la moyenne de la section"
        )
        fig_corr_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_corr_bar.update_layout(height=max(420, 42 * len(corr_with_mean)), xaxis_title="Corrélation", yaxis_title="", coloraxis_showscale=False, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_corr_bar, use_container_width=True, config={"displayModeBar": False})

# =====================================================
# Page 4
# =====================================================

def page_importance():
    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Facteurs clés d’amélioration</h2>", unsafe_allow_html=True)

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
            color_continuous_scale=["#C0003B", "#F57C00", "#2E7D32"],
            title="Importance relative des dimensions dans la satisfaction globale"
        )

        fig_sat.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Importance relative (%)",
            yaxis_title="",
            height=480,
            coloraxis_showscale=False
        )

        fig_sat.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_sat, use_container_width=True, config={"displayModeBar": False})

        summary_box(
            f"""
            <b>Interprétation décisionnelle :</b><br>
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
            color_continuous_scale=["#C0003B", "#F57C00", "#2E7D32"],
            title="Importance relative des dimensions dans la recommandation de l’USJ"
        )

        fig_rec.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Importance relative (%)",
            yaxis_title="",
            height=480,
            coloraxis_showscale=False
        )

        fig_rec.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(fig_rec, use_container_width=True, config={"displayModeBar": False})

        summary_box(
            f"""
            <b>Interprétation décisionnelle :</b><br>
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
# Page 4
# =====================================================

def page_methodology():
    st.markdown(f"<h2 style='color:{USJ_BLUE};'>Méthodologie de calcul des composantes</h2>", unsafe_allow_html=True)

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

elif page == "Résultats descriptifs par section":
    page_descriptive_sections()

elif page == "Facteurs clés d’amélioration":
    page_importance()

elif page == "Méthodologie des composantes":
    page_methodology()

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
        border-radius:12px;
        text-align:center;
        font-size:14px;
    ">
        Université Saint-Joseph de Beyrouth – Exit Survey 2022-2025
    </div>
    """,
    unsafe_allow_html=True
)
