import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# Configuration
# =====================================================

st.set_page_config(
    page_title="USJ Exit Survey 2024-2025",
    page_icon="📊",
    layout="wide"
)

USJ_BLUE = "#001B75"
USJ_RED = "#C0003B"
USJ_GREEN = "#2E7D32"
USJ_ORANGE = "#F57C00"

# =====================================================
# Functions
# =====================================================

@st.cache_data
def load_data():
    return pd.read_excel("Exit survey 24-25.xlsx")

def recode_series(series, mapping):
    return (
        series.astype(str)
        .str.strip()
        .replace(mapping)
        .replace({"nan": np.nan})
    )

def score_to_percent(value):
    if pd.isna(value):
        return np.nan
    return value / 4 * 100

def kpi_status_percent(value):
    if pd.isna(value):
        return "Non disponible", "#777777"
    elif value >= 81.25:
        return "Forte satisfaction", USJ_GREEN
    elif value >= 62.5:
        return "Satisfaction modérée", USJ_ORANGE
    else:
        return "Faible satisfaction", USJ_RED

def recommendation_status(value):
    if pd.isna(value):
        return "Non disponible", "#777777"
    elif value >= 80:
        return "Très bon niveau", USJ_GREEN
    elif value >= 60:
        return "Niveau acceptable", USJ_ORANGE
    else:
        return "Niveau faible", USJ_RED

def kpi_card(title, mean_value, subtitle="Score de satisfaction"):
    percent_value = score_to_percent(mean_value)
    status, color = kpi_status_percent(percent_value)
    display_value = "NA" if pd.isna(percent_value) else f"{percent_value:.1f}%"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, white 0%, #f8f9fc 100%);
            border-radius:22px;
            padding:24px;
            box-shadow:0 8px 22px rgba(0,0,0,0.10);
            border-left:9px solid {color};
            min-height:170px;
        ">
            <div style="font-size:15px; color:#333; font-weight:700;">
                {title}
            </div>

            <div style="font-size:42px; color:{color}; font-weight:900; margin-top:10px;">
                {display_value}
            </div>

            <div style="font-size:13px; color:#777; margin-top:2px;">
                {subtitle}
            </div>

            <div style="
                display:inline-block;
                margin-top:14px;
                padding:6px 12px;
                border-radius:20px;
                background-color:{color}20;
                color:{color};
                font-size:13px;
                font-weight:700;
            ">
                {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def percent_card(title, value, subtitle="Pourcentage"):
    status, color = recommendation_status(value)
    display_value = "NA" if pd.isna(value) else f"{value:.1f}%"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, white 0%, #f8f9fc 100%);
            border-radius:22px;
            padding:24px;
            box-shadow:0 8px 22px rgba(0,0,0,0.10);
            border-left:9px solid {color};
            min-height:170px;
        ">
            <div style="font-size:15px; color:#333; font-weight:700;">
                {title}
            </div>

            <div style="font-size:42px; color:{color}; font-weight:900; margin-top:10px;">
                {display_value}
            </div>

            <div style="font-size:13px; color:#777; margin-top:2px;">
                {subtitle}
            </div>

            <div style="
                display:inline-block;
                margin-top:14px;
                padding:6px 12px;
                border-radius:20px;
                background-color:{color}20;
                color:{color};
                font-size:13px;
                font-weight:700;
            ">
                {status}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def get_options(data, column):
    values = sorted(data[column].dropna().astype(str).unique())
    return ["Tous"] + values

def apply_filter(data, column, value):
    if value == "Tous":
        return data
    return data[data[column].astype(str) == value]

# =====================================================
# Load data
# =====================================================

df_original = load_data()
df_coded = df_original.copy()

# =====================================================
# Mappings
# =====================================================

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
    "Pas au courant": 0,
    "Très insatisfaisante": 1,
    "Insatisfaisante": 2,
    "Satisfaisante": 3,
    "Très satisfaisante": 4
}

# =====================================================
# Variables
# =====================================================

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

# =====================================================
# Scores
# =====================================================

def create_score(items, mapping, score_name):
    existing_items = [col for col in items if col in df_coded.columns]
    for col in existing_items:
        df_coded[col] = pd.to_numeric(
            recode_series(df_original[col], mapping),
            errors="coerce"
        )
    df_coded[score_name] = df_coded[existing_items].mean(axis=1, skipna=True)

create_score(enseignement_items, satisfaction_mapping_f, "Score enseignement et apprentissage")
create_score(accompagnement_items, satisfaction_mapping_f, "Score accompagnement et encadrement")
create_score(competences_items, accord_mapping, "Score développement des compétences")
create_score(experience_items, satisfaction_mapping_f, "Score expérience globale USJ")
create_score(services_items, satisfaction_mapping_f, "Score services USJ")
create_score(infrastructures_items, satisfaction_mapping_f, "Score infrastructures et équipements")
create_score(vie_items, vie_mapping, "Score vie étudiante et activités")

q42 = "42-Quel est le niveau de votre satisfaction globale à l’Université ?"
df_coded["Score satisfaction globale"] = pd.to_numeric(
    recode_series(df_original[q42], satisfaction_mapping_m),
    errors="coerce"
)

q43 = "43-Recommanderiez-vous l’USJ à un proche ou à un ami ?"
df_coded[q43] = df_original[q43].astype(str).str.strip().replace({"nan": np.nan})

q26 = "26- satisfait par les frais de scolarité à l’USJ par rapport à la qualité de l’enseignement ?"
q27 = "27- satisfait par les frais de scolarité à l’USJ par rapport à ceux d’autres universités ?"

df_coded["Score frais / qualité enseignement"] = pd.to_numeric(
    recode_series(df_original[q26], satisfaction_mapping_m),
    errors="coerce"
)

df_coded["Score frais / autres universités"] = pd.to_numeric(
    recode_series(df_original[q27], satisfaction_mapping_m),
    errors="coerce"
)

# =====================================================
# Header
# =====================================================

st.markdown(
    f"""
    <h1 style="color:{USJ_BLUE}; margin-bottom:0;">
        Tableau de bord – Exit Survey USJ 2024-2025
    </h1>
    <p style="font-size:18px; color:#555; margin-top:4px;">
        Indicateurs clés de satisfaction
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# Linked filters
# =====================================================

st.markdown(
    f"<h3 style='color:{USJ_BLUE};'>Filtres</h3>",
    unsafe_allow_html=True
)

f1, f2, f3, f4 = st.columns(4)

with f1:
    genre = st.selectbox("Genre", get_options(df_coded, "Genre"))

df_after_genre = apply_filter(df_coded, "Genre", genre)

with f2:
    faculte = st.selectbox(
        "Faculté",
        get_options(df_after_genre, "Faculté_Institut_g")
    )

df_after_faculte = apply_filter(df_after_genre, "Faculté_Institut_g", faculte)

with f3:
    cursus = st.selectbox(
        "Cursus",
        get_options(df_after_faculte, "Cursus")
    )

df_after_cursus = apply_filter(df_after_faculte, "Cursus", cursus)

with f4:
    niveau = st.selectbox(
        "Niveau",
        get_options(df_after_cursus, "Niveau")
    )

df_filtered = apply_filter(df_after_cursus, "Niveau", niveau)

st.markdown(
    f"""
    <div style="font-size:16px; margin-top:10px; margin-bottom:18px;">
        <b>Nombre de répondants affichés :</b> {len(df_filtered)}
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# Section 1
# =====================================================

st.markdown(
    f"<h2 style='color:{USJ_BLUE};'>Satisfaction globale et expérience</h2>",
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

with c1:
    kpi_card("Satisfaction globale à l’Université", df_filtered["Score satisfaction globale"].mean())

with c2:
    valid_reco = df_filtered[q43].notna().sum()
    taux_recommandation = np.nan if valid_reco == 0 else df_filtered[q43].eq("Oui").sum() / valid_reco * 100
    percent_card("Taux de recommandation de l’USJ", taux_recommandation)

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

# =====================================================
# Section 2
# =====================================================

st.markdown(
    f"<h2 style='color:{USJ_BLUE};'>Vie étudiante, services et environnement</h2>",
    unsafe_allow_html=True
)

c7, c8, c9 = st.columns(3)

with c7:
    kpi_card("Services de l’USJ", df_filtered["Score services USJ"].mean())

with c8:
    kpi_card(
        "Vie étudiante et activités",
        df_filtered["Score vie étudiante et activités"].mean(),
        "Score incluant Pas au courant = 0"
    )

with c9:
    kpi_card("Infrastructures et équipements", df_filtered["Score infrastructures et équipements"].mean())

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================
# Section 3
# =====================================================

st.markdown(
    f"<h2 style='color:{USJ_BLUE};'>Perception financière</h2>",
    unsafe_allow_html=True
)

c10, c11 = st.columns(2)

with c10:
    kpi_card("Frais de scolarité / qualité de l’enseignement", df_filtered["Score frais / qualité enseignement"].mean())

with c11:
    kpi_card("Frais de scolarité / autres universités", df_filtered["Score frais / autres universités"].mean())

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
        Université Saint-Joseph de Beyrouth – Exit Survey 2024-2025
    </div>
    """,
    unsafe_allow_html=True
)
