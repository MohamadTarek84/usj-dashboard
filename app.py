import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# =====================================================
# Configuration de la page
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
# Fonctions utiles
# =====================================================

@st.cache_data
def load_data():
    possible_files = [
        "Exit survey 24-25.xlsx",
        "Exit Survey 24-25.xlsx",
        "exit survey 24-25.xlsx",
        "EXIT SURVEY 24-25.xlsx"
    ]

    for file in possible_files:
        if os.path.exists(file):
            return pd.read_excel(file)

    st.error("Excel file not found.")
    st.write(os.listdir("."))
    st.stop()


def recode_series(series, mapping):
    return (
        series.astype(str)
        .str.strip()
        .replace(mapping)
        .replace({"nan": np.nan})
    )


def kpi_color_percentage(value_pct):
    if pd.isna(value_pct):
        return "#777777"
    elif value_pct >= 81.25:
        return USJ_GREEN
    elif value_pct >= 62.50:
        return USJ_ORANGE
    else:
        return USJ_RED


def kpi_card(title, value, subtitle="Satisfaction globale"):
    value_pct = np.nan if pd.isna(value) else value / 4 * 100
    color = kpi_color_percentage(value_pct)
    display_value = "NA" if pd.isna(value_pct) else f"{value_pct:.1f}%"

    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:18px;
            padding:22px;
            box-shadow:0 4px 14px rgba(0,0,0,0.08);
            border-left:7px solid {color};
            min-height:145px;
        ">
            <div style="font-size:15px; color:#444; font-weight:600;">
                {title}
            </div>
            <div style="font-size:38px; color:{color}; font-weight:800; margin-top:8px;">
                {display_value}
            </div>
            <div style="font-size:13px; color:#777; margin-top:4px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def percent_card(title, value, subtitle="Pourcentage"):
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
            min-height:145px;
        ">
            <div style="font-size:15px; color:#444; font-weight:600;">
                {title}
            </div>
            <div style="font-size:38px; color:{color}; font-weight:800; margin-top:8px;">
                {display_value}
            </div>
            <div style="font-size:13px; color:#777; margin-top:4px;">
                {subtitle}
            </div>
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
            <div style="font-size:15px; color:#444; font-weight:700;">
                {title}
            </div>
            <div style="font-size:36px; color:{color}; font-weight:900; margin-top:8px;">
                {display_value}
            </div>
            <div style="font-size:13px; color:#777; margin-top:4px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def filter_options(data, column):
    values = sorted(data[column].dropna().astype(str).unique())
    return ["Tous"] + values


def calculate_recommendation_rate(data, column):
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


# =====================================================
# Chargement des données
# =====================================================

df_original = load_data()
df_coded = df_original.copy()

# =====================================================
# Recodages
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

# =====================================================
# Scores internes
# =====================================================

for col in enseignement_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], satisfaction_mapping_f), errors="coerce")
enseignement_existing = [col for col in enseignement_items if col in df_coded.columns]
df_coded["Score enseignement et apprentissage"] = df_coded[enseignement_existing].mean(axis=1, skipna=True)

for col in accompagnement_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], satisfaction_mapping_f), errors="coerce")
accompagnement_existing = [col for col in accompagnement_items if col in df_coded.columns]
df_coded["Score accompagnement et encadrement"] = df_coded[accompagnement_existing].mean(axis=1, skipna=True)

for col in competences_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], accord_mapping), errors="coerce")
competences_existing = [col for col in competences_items if col in df_coded.columns]
df_coded["Score développement des compétences"] = df_coded[competences_existing].mean(axis=1, skipna=True)

for col in experience_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], satisfaction_mapping_f), errors="coerce")
experience_existing = [col for col in experience_items if col in df_coded.columns]
df_coded["Score expérience globale USJ"] = df_coded[experience_existing].mean(axis=1, skipna=True)

for col in services_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], satisfaction_mapping_f), errors="coerce")
services_existing = [col for col in services_items if col in df_coded.columns]
df_coded["Score services USJ"] = df_coded[services_existing].mean(axis=1, skipna=True)

vie_mapping = {
    "Pas au courant": np.nan,
    "Très insatisfaisante": 1,
    "Insatisfaisante": 2,
    "Satisfaisante": 3,
    "Très satisfaisante": 4
}

for col in vie_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], vie_mapping), errors="coerce")
df_coded["Score vie étudiante et activités"] = df_coded[vie_items].mean(axis=1, skipna=True)

for col in infrastructures_items:
    if col in df_coded.columns:
        df_coded[col] = pd.to_numeric(recode_series(df_original[col], satisfaction_mapping_f), errors="coerce")
infrastructures_existing = [col for col in infrastructures_items if col in df_coded.columns]
df_coded["Score infrastructures et équipements"] = df_coded[infrastructures_existing].mean(axis=1, skipna=True)

q42 = "42-Quel est le niveau de votre satisfaction globale à l’Université ?"
q43 = "43-Recommanderiez-vous l’USJ à un proche ou à un ami ?"
q26 = "26- satisfait par les frais de scolarité à l’USJ par rapport à la qualité de l’enseignement ?"
q27 = "27- satisfait par les frais de scolarité à l’USJ par rapport à ceux d’autres universités ?"

df_coded["Score satisfaction globale"] = pd.to_numeric(
    recode_series(df_original[q42], satisfaction_mapping_m),
    errors="coerce"
)

df_coded[q43] = df_original[q43].astype(str).str.strip().replace({"nan": np.nan})

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
# Filtres liés
# =====================================================

filter_cols = st.columns(4)
df_filter_base = df_coded.copy()

with filter_cols[0]:
    genre = st.selectbox("Genre", filter_options(df_filter_base, "Genre"), key="filter_genre")

df_after_genre = df_filter_base.copy()
if genre != "Tous":
    df_after_genre = df_after_genre[df_after_genre["Genre"].astype(str) == genre]

with filter_cols[1]:
    faculte = st.selectbox("Faculté", filter_options(df_after_genre, "Faculté_Institut_g"), key="filter_faculte")

df_after_faculte = df_after_genre.copy()
if faculte != "Tous":
    df_after_faculte = df_after_faculte[df_after_faculte["Faculté_Institut_g"].astype(str) == faculte]

with filter_cols[2]:
    cursus = st.selectbox("Cursus", filter_options(df_after_faculte, "Cursus"), key="filter_cursus")

df_after_cursus = df_after_faculte.copy()
if cursus != "Tous":
    df_after_cursus = df_after_cursus[df_after_cursus["Cursus"].astype(str) == cursus]

with filter_cols[3]:
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
    ["Vue générale des indicateurs", "Facteurs clés d’amélioration"],
    horizontal=True
)

# =====================================================
# Page 1
# =====================================================

if page == "Vue générale des indicateurs":

    st.markdown(
        f"<h2 style='color:{USJ_BLUE};'>Satisfaction globale et expérience</h2>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card("Satisfaction globale à l’Université", df_filtered["Score satisfaction globale"].mean())

    with c2:
        taux_recommandation = calculate_recommendation_rate(df_filtered, q43)
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
            "Pas au courant exclu"
        )

    with c9:
        kpi_card("Infrastructures et équipements", df_filtered["Score infrastructures et équipements"].mean())

    st.markdown("<br>", unsafe_allow_html=True)

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
# Page 2
# =====================================================

elif page == "Facteurs clés d’amélioration":

    st.markdown(
        f"<h2 style='color:{USJ_BLUE};'>Facteurs clés d’amélioration</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        Cette section identifie les dimensions les plus importantes pour expliquer :
        **la satisfaction globale à l’Université** et **la recommandation de l’USJ**.
        Les résultats sont présentés comme des priorités d’action pour les décideurs.
        """
    )

    feature_columns = [
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

    feature_columns = [col for col in feature_columns if col in df_filtered.columns]

    display_names = {
        col: clean_component_name(col)
        for col in feature_columns
    }

    # -----------------------------
    # Satisfaction globale
    # -----------------------------

    st.markdown(
        f"<h3 style='color:{USJ_BLUE};'>1. Priorités liées à la satisfaction globale</h3>",
        unsafe_allow_html=True
    )

    model_sat = df_filtered[feature_columns + ["Score satisfaction globale"]].dropna()

    if len(model_sat) < 30:
        st.warning("Pas assez de données valides pour analyser la satisfaction globale.")
    else:
        X = model_sat[feature_columns]
        y = model_sat["Score satisfaction globale"]

        rf_sat = RandomForestRegressor(
            n_estimators=500,
            random_state=42,
            max_depth=5
        )

        rf_sat.fit(X, y)

        importance_sat = pd.DataFrame({
            "Dimension": [display_names[col] for col in feature_columns],
            "Importance": rf_sat.feature_importances_
        })

        importance_sat["Importance (%)"] = (
            importance_sat["Importance"] / importance_sat["Importance"].sum() * 100
        ).round(1)

        importance_sat = importance_sat.sort_values("Importance (%)", ascending=False)

        top_sat = importance_sat.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            importance_card(
                "Priorité principale",
                top_sat["Importance (%)"],
                top_sat["Dimension"]
            )

        with c2:
            importance_card(
                "Base d’analyse",
                len(model_sat) / len(df_filtered) * 100,
                f"{len(model_sat)} répondants valides"
            )

        with c3:
            importance_card(
                "Dimensions analysées",
                len(feature_columns) / 10 * 100,
                f"{len(feature_columns)} dimensions"
            )

        fig_sat = px.bar(
            importance_sat,
            x="Importance (%)",
            y="Dimension",
            orientation="h",
            text="Importance (%)",
            color="Importance (%)",
            color_continuous_scale=["#C0003B", "#F57C00", "#2E7D32"],
            title="Poids relatif des dimensions dans la satisfaction globale"
        )

        fig_sat.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Importance relative (%)",
            yaxis_title="",
            height=520,
            coloraxis_showscale=False
        )

        fig_sat.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

        st.plotly_chart(fig_sat, use_container_width=True)

        st.info(
            f"La dimension la plus déterminante pour la satisfaction globale est "
            f"**{top_sat['Dimension']}** avec une importance relative de "
            f"**{top_sat['Importance (%)']:.1f}%**."
        )

    st.divider()

    # -----------------------------
    # Recommandation
    # -----------------------------

    st.markdown(
        f"<h3 style='color:{USJ_BLUE};'>2. Priorités liées à la recommandation de l’USJ</h3>",
        unsafe_allow_html=True
    )

    model_rec = df_filtered[feature_columns + [q43]].copy()
    model_rec[q43] = model_rec[q43].astype(str).str.strip()
    model_rec = model_rec[model_rec[q43].isin(["Oui", "Non"])]
    model_rec["Recommandation"] = model_rec[q43].map({"Oui": 1, "Non": 0})
    model_rec = model_rec[feature_columns + ["Recommandation"]].dropna()

    if len(model_rec) < 30 or model_rec["Recommandation"].nunique() < 2:
        st.warning("Pas assez de données valides pour analyser la recommandation.")
    else:
        X = model_rec[feature_columns]
        y = model_rec["Recommandation"]

        rf_rec = RandomForestClassifier(
            n_estimators=500,
            random_state=42,
            max_depth=5,
            class_weight="balanced"
        )

        rf_rec.fit(X, y)

        importance_rec = pd.DataFrame({
            "Dimension": [display_names[col] for col in feature_columns],
            "Importance": rf_rec.feature_importances_
        })

        importance_rec["Importance (%)"] = (
            importance_rec["Importance"] / importance_rec["Importance"].sum() * 100
        ).round(1)

        importance_rec = importance_rec.sort_values("Importance (%)", ascending=False)

        top_rec = importance_rec.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            importance_card(
                "Priorité principale",
                top_rec["Importance (%)"],
                top_rec["Dimension"]
            )

        with c2:
            importance_card(
                "Taux de recommandation",
                calculate_recommendation_rate(df_filtered, q43),
                "Réponses Oui"
            )

        with c3:
            importance_card(
                "Base d’analyse",
                len(model_rec) / len(df_filtered) * 100,
                f"{len(model_rec)} répondants valides"
            )

        fig_rec = px.bar(
            importance_rec,
            x="Importance (%)",
            y="Dimension",
            orientation="h",
            text="Importance (%)",
            color="Importance (%)",
            color_continuous_scale=["#C0003B", "#F57C00", "#2E7D32"],
            title="Poids relatif des dimensions dans la recommandation de l’USJ"
        )

        fig_rec.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Importance relative (%)",
            yaxis_title="",
            height=520,
            coloraxis_showscale=False
        )

        fig_rec.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

        st.plotly_chart(fig_rec, use_container_width=True)

        st.info(
            f"La dimension la plus déterminante pour la recommandation de l’USJ est "
            f"**{top_rec['Dimension']}** avec une importance relative de "
            f"**{top_rec['Importance (%)']:.1f}%**."
        )

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
