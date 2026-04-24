#!/usr/bin/env python
# coding: utf-8

# In[9]:


import os
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import chi2_contingency
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

st.set_page_config(
    page_title="USJ Advanced Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# LANGUAGE
# =========================================================
LANG = st.sidebar.selectbox("Language / Langue", ["English", "Français"], index=0)

TXT = {
    "English": {
        "title": "USJ Advanced Analytics Dashboard",
        "subtitle": "Professional interactive dashboard for institutional student analytics",
        "password": "Enter dashboard password",
        "incorrect_password": "Incorrect password",
        "db_failed": "Database connection failed.",
        "no_data": "No data found in the students table.",
        "usj_analytics": "USJ Analytics",
        "sidebar_caption": "Interactive institutional dashboard",
        "filters": "Filters",
        "faculty": "Faculty",
        "program": "Program",
        "gender": "Gender",
        "nationality": "Nationality",
        "enrollment_year": "Enrollment Year",
        "rows_after_filtering": "Rows after filtering",
        "download_filtered_data": "Download filtered data",
        "executive_overview": "Executive Overview",
        "student_profile_analysis": "Student Profile Analysis",
        "statistical_analysis": "Statistical Analysis",
        "advanced_relationships": "Advanced Relationships",
        "faculty_comparison": "Faculty Comparison",
        "ranking_style_visuals": "Ranking-Style Visuals",
        "predictive_model": "Predictive Model",
        "data_explorer": "Data Explorer",
        "dashboard_navigation": "Dashboard Navigation",
        "select_section": "Select the dashboard section you want to open.",
        "back": "Back",
        "section_protected": "This section is protected",
        "enter_password_for": "Enter password for",
        "access_granted": "Access granted.",
        "total_students": "Total Students",
        "faculties": "Faculties",
        "average_credits": "Average Credits",
        "enrollment_years": "Enrollment Years",
        "count": "Count",
        "students_by_faculty": "Students by Faculty",
        "gender_distribution": "Gender Distribution",
        "enrollment_trend_by_year": "Enrollment Trend by Year",
        "students_by_nationality": "Students by Nationality",
        "students_by_program": "Students by Program",
        "average_credits_by_faculty": "Average Credits by Faculty",
        "faculty_by_gender": "Faculty by Gender",
        "program_by_nationality": "Program by Nationality",
        "chi_square_caption": "Chi-square tests for categorical associations",
        "variable_1": "Variable 1",
        "variable_2": "Variable 2",
        "select_two_different": "Please select two different variables.",
        "chi_square_need": "Chi-square test requires at least two categories in each selected variable.",
        "chi_square": "Chi-square",
        "p_value": "p-value",
        "degrees_freedom": "Degrees of freedom",
        "observed_frequencies": "Observed Frequencies",
        "expected_frequencies": "Expected Frequencies",
        "significant": "There is a statistically significant association at the 5% level.",
        "not_significant": "There is no statistically significant association at the 5% level.",
        "heatmap_row": "Heatmap row variable",
        "heatmap_column": "Heatmap column variable",
        "choose_heatmap": "Please choose two different variables for the heatmap.",
        "heatmap_of": "Heatmap of",
        "row_normalized_heatmap": "Row-normalized heatmap",
        "correlation_matrix": "Correlation Matrix",
        "numeric_correlation_matrix": "Numeric Correlation Matrix",
        "faculty_comparison_dashboard": "Faculty Comparison Dashboard",
        "faculty_ranking_student_count": "Faculty Ranking by Student Count",
        "faculty_ranking_avg_credits": "Faculty Ranking by Average Credits",
        "faculty_comparison_bubble": "Faculty Comparison Bubble Chart",
        "top_faculties_student_count": "Top Faculties by Student Count",
        "top_faculties_avg_credits": "Top Faculties by Average Credits",
        "dual_ranking": "Dual Ranking View by Faculty",
        "predictive_caption": "Illustrative machine-learning panel using available student attributes to predict credits",
        "model_too_small": "The current filtered dataset is too small for a meaningful predictive model. Add more rows or widen the filters.",
        "model_r2": "Model R²",
        "model_mae": "Model MAE",
        "top_feature_importances": "Top Feature Importances",
        "prediction_preview": "Prediction Preview",
        "filtered_preview_export": "Filtered table preview and export",
        "no_records": "No records match the current filters.",
    },
    "Français": {
        "title": "Tableau de bord analytique avancé de l’USJ",
        "subtitle": "Tableau de bord interactif professionnel pour l’analyse institutionnelle des données étudiantes",
        "password": "Entrer le mot de passe du tableau de bord",
        "incorrect_password": "Mot de passe incorrect",
        "db_failed": "Échec de connexion à la base de données.",
        "no_data": "Aucune donnée trouvée dans la table des étudiants.",
        "usj_analytics": "Analytique USJ",
        "sidebar_caption": "Tableau de bord institutionnel interactif",
        "filters": "Filtres",
        "faculty": "Faculté",
        "program": "Programme",
        "gender": "Genre",
        "nationality": "Nationalité",
        "enrollment_year": "Année d’inscription",
        "rows_after_filtering": "Lignes après filtrage",
        "download_filtered_data": "Télécharger les données filtrées",
        "executive_overview": "Vue d’ensemble exécutive",
        "student_profile_analysis": "Analyse du profil étudiant",
        "statistical_analysis": "Analyse statistique",
        "advanced_relationships": "Relations avancées",
        "faculty_comparison": "Comparaison des facultés",
        "ranking_style_visuals": "Visualisations de classement",
        "predictive_model": "Modèle prédictif",
        "data_explorer": "Explorateur de données",
        "dashboard_navigation": "Navigation du tableau de bord",
        "select_section": "Sélectionnez la section du tableau de bord à ouvrir.",
        "back": "Retour",
        "section_protected": "Cette section est protégée",
        "enter_password_for": "Entrer le mot de passe pour",
        "access_granted": "Accès autorisé.",
        "total_students": "Nombre total d’étudiants",
        "faculties": "Facultés",
        "average_credits": "Moyenne des crédits",
        "enrollment_years": "Années d’inscription",
        "count": "Effectif",
        "students_by_faculty": "Étudiants par faculté",
        "gender_distribution": "Répartition par genre",
        "enrollment_trend_by_year": "Évolution des inscriptions par année",
        "students_by_nationality": "Étudiants par nationalité",
        "students_by_program": "Étudiants par programme",
        "average_credits_by_faculty": "Moyenne des crédits par faculté",
        "faculty_by_gender": "Faculté par genre",
        "program_by_nationality": "Programme par nationalité",
        "chi_square_caption": "Tests du khi-deux pour les associations entre variables catégorielles",
        "variable_1": "Variable 1",
        "variable_2": "Variable 2",
        "select_two_different": "Veuillez sélectionner deux variables différentes.",
        "chi_square_need": "Le test du khi-deux nécessite au moins deux catégories dans chaque variable sélectionnée.",
        "chi_square": "Khi-deux",
        "p_value": "p-valeur",
        "degrees_freedom": "Degrés de liberté",
        "observed_frequencies": "Fréquences observées",
        "expected_frequencies": "Fréquences attendues",
        "significant": "Il existe une association statistiquement significative au seuil de 5%.",
        "not_significant": "Il n’existe pas d’association statistiquement significative au seuil de 5%.",
        "heatmap_row": "Variable en ligne",
        "heatmap_column": "Variable en colonne",
        "choose_heatmap": "Veuillez choisir deux variables différentes pour la carte thermique.",
        "heatmap_of": "Carte thermique de",
        "row_normalized_heatmap": "Carte thermique normalisée par ligne",
        "correlation_matrix": "Matrice de corrélation",
        "numeric_correlation_matrix": "Matrice de corrélation numérique",
        "faculty_comparison_dashboard": "Tableau comparatif des facultés",
        "faculty_ranking_student_count": "Classement des facultés par effectif étudiant",
        "faculty_ranking_avg_credits": "Classement des facultés par moyenne des crédits",
        "faculty_comparison_bubble": "Graphique comparatif des facultés",
        "top_faculties_student_count": "Premières facultés par effectif étudiant",
        "top_faculties_avg_credits": "Premières facultés par moyenne des crédits",
        "dual_ranking": "Vue de classement double par faculté",
        "predictive_caption": "Panneau illustratif de machine learning utilisant les attributs disponibles pour prédire les crédits",
        "model_too_small": "L’échantillon filtré est trop petit pour estimer un modèle prédictif fiable. Ajoutez des lignes ou élargissez les filtres.",
        "model_r2": "R² du modèle",
        "model_mae": "MAE du modèle",
        "top_feature_importances": "Variables les plus importantes",
        "prediction_preview": "Aperçu des prédictions",
        "filtered_preview_export": "Aperçu du tableau filtré et export",
        "no_records": "Aucun enregistrement ne correspond aux filtres actuels.",
    },
}

T = TXT[LANG]

# =========================================================
# PASSWORD PROTECTION
# =========================================================
APP_PASSWORD = "HadiSawaya"

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    def password_entered():
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.text_input(
            "Enter dashboard password",
            type="password",
            on_change=password_entered,
            key="password",
        )

        if "password" in st.session_state and st.session_state["password"] != "":
            st.error(T["incorrect_password"])

        st.stop()

check_password()

# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
    <style>
        .main { padding-top: 1rem; }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        div[data-testid='stMetric'] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 14px;
            border-radius: 16px;
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 700;
            margin-top: 0.4rem;
            margin-bottom: 0.8rem;
        }
        .small-note {
            color: #64748b;
            font-size: 0.95rem;
        }
        .narrative-box {
            background-color: #f8fafc;
            border-left: 5px solid #1d4ed8;
            padding: 14px;
            border-radius: 10px;
            margin-top: 8px;
            margin-bottom: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATABASE
# =========================================================
@st.cache_resource
def get_engine():
    db_user = "postgres.zaauwyrpcshrhangorxw"
    db_password = "UsjDashboard2026"
    db_host = "aws-1-ap-northeast-2.pooler.supabase.com"
    db_port = "5432"
    db_name = "postgres"

    return create_engine(
        f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}"
    )

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM students;", get_engine())
    df["credits"] = pd.to_numeric(df["credits"], errors="coerce")
    df["enrollment_year"] = pd.to_numeric(df["enrollment_year"], errors="coerce")

    for col in ["student_id", "faculty", "program", "level", "gender", "nationality"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    return df

# =========================================================
# HELPERS
# =========================================================
def get_ymax(series: pd.Series) -> float:
    max_val = float(series.max()) if len(series) else 0.0
    return max_val + max(1.0, max_val * 0.2)


def compute_kpis(df: pd.DataFrame):
    total_students = int(df.shape[0])
    number_of_faculties = int(df["faculty"].nunique()) if not df.empty else 0
    average_credits = float(df["credits"].mean()) if not df.empty else 0.0
    number_of_years = int(df["enrollment_year"].nunique()) if not df.empty else 0
    return total_students, number_of_faculties, average_credits, number_of_years


def add_count_percentage(df: pd.DataFrame, group_var: str) -> pd.DataFrame:
    summary = (
        df.groupby(group_var)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    total = summary["count"].sum()
    summary["percentage"] = (summary["count"] / total * 100).round(1) if total > 0 else 0
    summary["label"] = summary["count"].astype(str) + " (" + summary["percentage"].astype(str) + "%)"
    return summary


def chi_square_test(df: pd.DataFrame, var1: str, var2: str):
    table = pd.crosstab(df[var1], df[var2])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return None, None

    chi2, p, dof, expected = chi2_contingency(table)
    expected_df = pd.DataFrame(expected, index=table.index, columns=table.columns)
    result = {
        "chi2": round(chi2, 4),
        "p_value": round(p, 4),
        "dof": int(dof),
        "interpretation": T["significant"] if p < 0.05 else T["not_significant"],
    }
    return table, (result, expected_df.round(2))


def build_heatmap_table(df: pd.DataFrame, row_var: str, col_var: str, normalize: bool = False) -> pd.DataFrame:
    if normalize:
        return (pd.crosstab(df[row_var], df[col_var], normalize="index") * 100).round(1)
    return pd.crosstab(df[row_var], df[col_var])


def build_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = df[["enrollment_year", "credits"]].copy()
    return numeric_df.corr().round(3)


def prepare_faculty_comparison(df: pd.DataFrame) -> pd.DataFrame:
    comparison = (
        df.groupby("faculty")
        .agg(
            total_students=("student_id", "count"),
            avg_credits=("credits", "mean"),
            n_programs=("program", "nunique"),
            n_nationalities=("nationality", "nunique"),
        )
        .reset_index()
    )
    comparison["avg_credits"] = comparison["avg_credits"].round(2)
    comparison["student_rank"] = comparison["total_students"].rank(method="dense", ascending=False).astype(int)
    comparison["credit_rank"] = comparison["avg_credits"].rank(method="dense", ascending=False).astype(int)
    return comparison.sort_values("total_students", ascending=False)


def train_predictive_model(df: pd.DataFrame):
    model_df = df[["faculty", "program", "gender", "nationality", "enrollment_year", "credits"]].dropna().copy()

    if model_df.shape[0] < 8 or model_df["credits"].nunique() < 2:
        return None

    X = pd.get_dummies(model_df.drop(columns=["credits"]), drop_first=False)
    y = model_df["credits"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    metrics = {
        "r2": round(r2_score(y_test, preds), 3) if len(y_test) > 1 else None,
        "mae": round(mean_absolute_error(y_test, preds), 3),
    }

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    preview = pd.DataFrame({
        "actual_credits": y_test.values,
        "predicted_credits": preds.round(2),
    })

    return metrics, importance_df, preview


def add_download_button(df: pd.DataFrame):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=T["download_filtered_data"],
        data=csv,
        file_name="usj_filtered_students.csv",
        mime="text/csv",
        use_container_width=True,
    )


def narrative_box(text: str):
    st.markdown(f'<div class="narrative-box">{text}</div>', unsafe_allow_html=True)

# =========================================================
# NARRATIVES
# =========================================================
def executive_narrative(df: pd.DataFrame) -> str:
    total_students, number_of_faculties, average_credits, number_of_years = compute_kpis(df)
    if total_students == 0:
        return T["no_records"]

    top_faculty = add_count_percentage(df, "faculty").iloc[0]
    top_nat = add_count_percentage(df, "nationality").iloc[0]
    top_gender = add_count_percentage(df, "gender").iloc[0]
    year_counts = df.groupby("enrollment_year").size().reset_index(name="count").sort_values("count", ascending=False)
    top_year = year_counts.iloc[0]

    if LANG == "English":
        return (
            f"The filtered dataset contains <b>{total_students}</b> students across <b>{number_of_faculties}</b> faculties and "
            f"<b>{number_of_years}</b> enrollment years, with an average of <b>{average_credits:.2f}</b> credits. "
            f"The largest faculty in the current selection is <b>{top_faculty['faculty']}</b> with <b>{int(top_faculty['count'])}</b> students "
            f"({top_faculty['percentage']:.1f}%). The dominant gender group is <b>{top_gender['gender']}</b> with <b>{int(top_gender['count'])}</b> students "
            f"({top_gender['percentage']:.1f}%), while the most represented nationality is <b>{top_nat['nationality']}</b> with <b>{int(top_nat['count'])}</b> students "
            f"({top_nat['percentage']:.1f}%). The highest enrollment year in the filtered data is <b>{int(top_year['enrollment_year'])}</b> with <b>{int(top_year['count'])}</b> students."
        )
    return (
        f"L’ensemble filtré contient <b>{total_students}</b> étudiants répartis sur <b>{number_of_faculties}</b> facultés et "
        f"<b>{number_of_years}</b> années d’inscription, avec une moyenne de <b>{average_credits:.2f}</b> crédits. "
        f"La faculté la plus représentée dans la sélection actuelle est <b>{top_faculty['faculty']}</b> avec <b>{int(top_faculty['count'])}</b> étudiants "
        f"({top_faculty['percentage']:.1f}%). Le groupe de genre dominant est <b>{top_gender['gender']}</b> avec <b>{int(top_gender['count'])}</b> étudiants "
        f"({top_gender['percentage']:.1f}%), tandis que la nationalité la plus représentée est <b>{top_nat['nationality']}</b> avec <b>{int(top_nat['count'])}</b> étudiants "
        f"({top_nat['percentage']:.1f}%). L’année d’inscription la plus représentée est <b>{int(top_year['enrollment_year'])}</b> avec <b>{int(top_year['count'])}</b> étudiants."
    )


def profile_narrative(df: pd.DataFrame) -> str:
    if df.empty:
        return T["no_records"]

    top_program = add_count_percentage(df, "program").iloc[0]
    avg_credit_fac = df.groupby("faculty")["credits"].mean().reset_index(name="avg_credits").sort_values("avg_credits", ascending=False)
    best_fac = avg_credit_fac.iloc[0]

    if LANG == "English":
        return (
            f"Within the current filtered selection, the leading program is <b>{top_program['program']}</b> with <b>{int(top_program['count'])}</b> students "
            f"({top_program['percentage']:.1f}%). The faculty with the highest average credits is <b>{best_fac['faculty']}</b>, reaching <b>{best_fac['avg_credits']:.2f}</b> credits on average."
        )
    return (
        f"Dans la sélection filtrée actuelle, le programme le plus représenté est <b>{top_program['program']}</b> avec <b>{int(top_program['count'])}</b> étudiants "
        f"({top_program['percentage']:.1f}%). La faculté ayant la moyenne de crédits la plus élevée est <b>{best_fac['faculty']}</b>, avec <b>{best_fac['avg_credits']:.2f}</b> crédits en moyenne."
    )


def stats_narrative(result_bundle, var1: str, var2: str) -> str:
    if result_bundle is None:
        if LANG == "English":
            return f"The chi-square test for {var1} and {var2} cannot be computed with the current filtered data."
        return f"Le test du khi-deux pour {var1} et {var2} ne peut pas être calculé avec les données filtrées actuelles."

    result, _ = result_bundle
    if LANG == "English":
        return (
            f"The chi-square test examining the relationship between <b>{var1}</b> and <b>{var2}</b> produced a chi-square value of <b>{result['chi2']}</b>, "
            f"with a p-value of <b>{result['p_value']}</b> and <b>{result['dof']}</b> degrees of freedom. {result['interpretation']}"
        )
    return (
        f"Le test du khi-deux examinant la relation entre <b>{var1}</b> et <b>{var2}</b> donne une valeur de khi-deux de <b>{result['chi2']}</b>, "
        f"avec une p-valeur de <b>{result['p_value']}</b> et <b>{result['dof']}</b> degrés de liberté. {result['interpretation']}"
    )


def ranking_narrative(df: pd.DataFrame) -> str:
    if df.empty:
        return T["no_records"]
    comparison = prepare_faculty_comparison(df)
    top_students = comparison.sort_values("total_students", ascending=False).iloc[0]
    top_credits = comparison.sort_values("avg_credits", ascending=False).iloc[0]

    if LANG == "English":
        return (
            f"In the current ranking-style comparison, <b>{top_students['faculty']}</b> holds first position by student count with <b>{int(top_students['total_students'])}</b> students, "
            f"while <b>{top_credits['faculty']}</b> leads by average credits with <b>{top_credits['avg_credits']:.2f}</b>."
        )
    return (
        f"Dans la comparaison sous forme de classement, <b>{top_students['faculty']}</b> occupe la première position selon l’effectif étudiant avec <b>{int(top_students['total_students'])}</b> étudiants, "
        f"tandis que <b>{top_credits['faculty']}</b> arrive en tête selon la moyenne des crédits avec <b>{top_credits['avg_credits']:.2f}</b>."
    )


def predictive_narrative(model_output) -> str:
    if model_output is None:
        return T["model_too_small"]
    metrics, importance_df, _ = model_output
    top_feature = importance_df.iloc[0]
    r2_text = f"{metrics['r2']}" if metrics["r2"] is not None else "N/A"

    if LANG == "English":
        return (
            f"The illustrative predictive model achieved an R² of <b>{r2_text}</b> and a mean absolute error of <b>{metrics['mae']}</b>. "
            f"The most influential predictor in the current model is <b>{top_feature['feature']}</b>."
        )
    return (
        f"Le modèle prédictif illustratif atteint un R² de <b>{r2_text}</b> et une erreur absolue moyenne de <b>{metrics['mae']}</b>. "
        f"La variable la plus influente dans le modèle actuel est <b>{top_feature['feature']}</b>."
    )

# =========================================================
# FILTERS
# =========================================================
def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title(T["usj_analytics"])
    st.sidebar.caption(T["sidebar_caption"])
    st.sidebar.markdown(f"### {T['filters']}")

    faculty_options = sorted(df["faculty"].dropna().unique().tolist())
    program_options = sorted(df["program"].dropna().unique().tolist())
    gender_options = sorted(df["gender"].dropna().unique().tolist())
    nationality_options = sorted(df["nationality"].dropna().unique().tolist())
    year_options = sorted(df["enrollment_year"].dropna().unique().tolist())

    selected_faculty = st.sidebar.multiselect(T["faculty"], faculty_options, default=[])
    selected_program = st.sidebar.multiselect(T["program"], program_options, default=[])
    selected_gender = st.sidebar.multiselect(T["gender"], gender_options, default=[])
    selected_nationality = st.sidebar.multiselect(T["nationality"], nationality_options, default=[])
    selected_year = st.sidebar.multiselect(T["enrollment_year"], year_options, default=[])

    filtered_df = df.copy()

    if selected_faculty:
        filtered_df = filtered_df[filtered_df["faculty"].isin(selected_faculty)]
    if selected_program:
        filtered_df = filtered_df[filtered_df["program"].isin(selected_program)]
    if selected_gender:
        filtered_df = filtered_df[filtered_df["gender"].isin(selected_gender)]
    if selected_nationality:
        filtered_df = filtered_df[filtered_df["nationality"].isin(selected_nationality)]
    if selected_year:
        filtered_df = filtered_df[filtered_df["enrollment_year"].isin(selected_year)]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"{T['rows_after_filtering']}: {filtered_df.shape[0]}")
    return filtered_df

# =========================================================
# PAGES
# =========================================================
def executive_overview(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["executive_overview"]}</div>', unsafe_allow_html=True)
    narrative_box(executive_narrative(df))

    total_students, number_of_faculties, average_credits, number_of_years = compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(T["total_students"], total_students)
    c2.metric(T["faculties"], number_of_faculties)
    c3.metric(T["average_credits"], f"{average_credits:.2f}")
    c4.metric(T["enrollment_years"], number_of_years)

    left, right = st.columns([1.2, 1])
    with left:
        faculty_counts = add_count_percentage(df, "faculty")
        fig = px.bar(faculty_counts, x="faculty", y="count", text="label", title=T["students_by_faculty"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, yaxis_title=T["count"], title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(faculty_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with right:
        gender_counts = add_count_percentage(df, "gender")
        fig = px.pie(gender_counts, names="gender", values="count", hole=0.45, title=T["gender_distribution"])
        fig.update_traces(textinfo="label+percent+value")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns([1.2, 1])
    with left:
        year_counts = df.groupby("enrollment_year").size().reset_index(name="count").sort_values("enrollment_year")
        year_counts["percentage"] = (year_counts["count"] / year_counts["count"].sum() * 100).round(1)
        year_counts["label"] = year_counts["count"].astype(str) + " (" + year_counts["percentage"].astype(str) + "%)"
        fig = px.line(year_counts, x="enrollment_year", y="count", markers=True, text="label", title=T["enrollment_trend_by_year"])
        fig.update_traces(textposition="top center")
        fig.update_layout(height=420, yaxis_title=T["count"], title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(year_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with right:
        nationality_counts = add_count_percentage(df, "nationality")
        fig = px.bar(nationality_counts, x="nationality", y="count", text="label", title=T["students_by_nationality"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, yaxis_title=T["count"], title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(nationality_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)


def profile_analysis(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["student_profile_analysis"]}</div>', unsafe_allow_html=True)
    narrative_box(profile_narrative(df))

    t1, t2 = st.columns(2)
    with t1:
        program_counts = add_count_percentage(df, "program")
        fig = px.bar(program_counts, x="program", y="count", text="label", title=T["students_by_program"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white", yaxis_title=T["count"])
        fig.update_yaxes(range=[0, get_ymax(program_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        avg_credits = df.groupby("faculty")["credits"].mean().reset_index(name="avg_credits").sort_values("avg_credits", ascending=False)
        avg_credits["label"] = avg_credits["avg_credits"].round(2).astype(str)
        fig = px.bar(avg_credits, x="faculty", y="avg_credits", text="label", title=T["average_credits_by_faculty"])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(avg_credits["avg_credits"])])
        st.plotly_chart(fig, use_container_width=True)

    t3, t4 = st.columns(2)
    with t3:
        st.markdown(f"**{T['faculty_by_gender']}**")
        st.dataframe(pd.crosstab(df["faculty"], df["gender"]), use_container_width=True)
    with t4:
        st.markdown(f"**{T['program_by_nationality']}**")
        st.dataframe(pd.crosstab(df["program"], df["nationality"]), use_container_width=True)


def statistical_analysis(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["statistical_analysis"]}</div>', unsafe_allow_html=True)
    st.caption(T["chi_square_caption"])

    variables = ["faculty", "program", "gender", "nationality", "level"]
    c1, c2 = st.columns(2)
    var1 = c1.selectbox(T["variable_1"], variables, index=0)
    var2 = c2.selectbox(T["variable_2"], variables, index=2)

    if var1 == var2:
        st.warning(T["select_two_different"])
        return

    observed, result_bundle = chi_square_test(df, var1, var2)
    if observed is None:
        narrative_box(stats_narrative(None, var1, var2))
        st.info(T["chi_square_need"])
        return

    result, expected = result_bundle
    narrative_box(stats_narrative(result_bundle, var1, var2))

    m1, m2, m3 = st.columns(3)
    m1.metric(T["chi_square"], result["chi2"])
    m2.metric(T["p_value"], result["p_value"])
    m3.metric(T["degrees_freedom"], result["dof"])

    if result["p_value"] < 0.05:
        st.success(result["interpretation"])
    else:
        st.info(result["interpretation"])

    a, b = st.columns(2)
    with a:
        st.markdown(f"**{T['observed_frequencies']}**")
        st.dataframe(observed, use_container_width=True)
    with b:
        st.markdown(f"**{T['expected_frequencies']}**")
        st.dataframe(expected, use_container_width=True)


def advanced_relationships(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["advanced_relationships"]}</div>', unsafe_allow_html=True)

    h1, h2 = st.columns(2)
    row_var = h1.selectbox(T["heatmap_row"], ["faculty", "program", "gender", "nationality", "level"], index=0)
    col_var = h2.selectbox(T["heatmap_column"], ["faculty", "program", "gender", "nationality", "level"], index=1)

    if row_var == col_var:
        st.warning(T["choose_heatmap"])
    else:
        heatmap_table = build_heatmap_table(df, row_var, col_var, normalize=False)
        fig = px.imshow(heatmap_table, text_auto=True, aspect="auto", title=f"{T['heatmap_of']} {row_var} × {col_var}")
        fig.update_layout(height=450, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        heatmap_pct = build_heatmap_table(df, row_var, col_var, normalize=True)
        fig_pct = px.imshow(heatmap_pct, text_auto=True, aspect="auto", title=f"{T['row_normalized_heatmap']} {row_var} × {col_var} (%)")
        fig_pct.update_layout(height=450, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig_pct, use_container_width=True)

    corr = build_correlation_matrix(df)
    st.markdown(f"**{T['correlation_matrix']}**")
    fig_corr = px.imshow(corr, text_auto=True, aspect="auto", title=T["numeric_correlation_matrix"])
    fig_corr.update_layout(height=350, title_x=0.5, template="plotly_white")
    st.plotly_chart(fig_corr, use_container_width=True)
    st.dataframe(corr, use_container_width=True)


def faculty_comparison(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["faculty_comparison_dashboard"]}</div>', unsafe_allow_html=True)
    comparison = prepare_faculty_comparison(df)
    narrative_box(ranking_narrative(df))
    st.dataframe(comparison, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(comparison, x="faculty", y="total_students", text_auto=True, title=T["faculty_ranking_student_count"])
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(comparison["total_students"])])
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(comparison, x="faculty", y="avg_credits", text_auto=".2f", title=T["faculty_ranking_avg_credits"])
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(comparison["avg_credits"])])
        st.plotly_chart(fig, use_container_width=True)

    fig_bubble = px.scatter(
        comparison,
        x="n_programs",
        y="avg_credits",
        size="total_students",
        color="faculty",
        hover_data=["n_nationalities"],
        title=T["faculty_comparison_bubble"],
    )
    fig_bubble.update_layout(height=500, title_x=0.5, template="plotly_white")
    st.plotly_chart(fig_bubble, use_container_width=True)


def ranking_visuals(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["ranking_style_visuals"]}</div>', unsafe_allow_html=True)
    narrative_box(ranking_narrative(df))

    ranking_df = prepare_faculty_comparison(df)

    left, right = st.columns(2)
    with left:
        st.markdown(f"**{T['top_faculties_student_count']}**")
        st.dataframe(ranking_df[["student_rank", "faculty", "total_students"]], use_container_width=True)
    with right:
        st.markdown(f"**{T['top_faculties_avg_credits']}**")
        st.dataframe(ranking_df[["credit_rank", "faculty", "avg_credits"]], use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(name=T["total_students"], x=ranking_df["faculty"], y=ranking_df["total_students"]))
    fig.add_trace(go.Scatter(name=T["average_credits"], x=ranking_df["faculty"], y=ranking_df["avg_credits"], mode="lines+markers", yaxis="y2"))
    fig.update_layout(
        title=T["dual_ranking"],
        yaxis=dict(title=T["total_students"]),
        yaxis2=dict(title=T["average_credits"], overlaying="y", side="right"),
        height=500,
        title_x=0.5,
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def predictive_model(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["predictive_model"]}</div>', unsafe_allow_html=True)
    st.caption(T["predictive_caption"])

    model_output = train_predictive_model(df)
    narrative_box(predictive_narrative(model_output))

    if model_output is None:
        st.info(T["model_too_small"])
        return

    metrics, importance_df, preview = model_output

    c1, c2 = st.columns(2)
    c1.metric(T["model_r2"], metrics["r2"] if metrics["r2"] is not None else "N/A")
    c2.metric(T["model_mae"], metrics["mae"])

    top_features = importance_df.head(12)
    fig = px.bar(top_features, x="importance", y="feature", orientation="h", title=T["top_feature_importances"])
    fig.update_layout(height=500, title_x=0.5, template="plotly_white", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**{T['prediction_preview']}**")
    st.dataframe(preview.head(10), use_container_width=True)


def data_explorer(df: pd.DataFrame):
    st.markdown(f'<div class="section-title">{T["data_explorer"]}</div>', unsafe_allow_html=True)
    st.caption(T["filtered_preview_export"])
    st.dataframe(df, use_container_width=True, height=500)
    add_download_button(df)

# =========================================================
# MAIN APP
# =========================================================
header_left, header_right = st.columns([3, 2])

with header_left:
    st.title(T["title"])
    st.caption(T["subtitle"])

with header_right:
    # For Streamlit Cloud, upload usj_logo.png to GitHub and keep this relative path.
    st.image("usj_logo.png", width=520)

try:
    df = load_data()
except Exception as e:
    st.error(T["db_failed"])
    st.exception(e)
    st.stop()

if df.empty:
    st.warning(T["no_data"])
    st.stop()

filtered_df = sidebar_filters(df)

# =========================================================
# HOME PAGE NAVIGATION WITH PROTECTED SECTIONS
# =========================================================
PAGES = [
    "Executive Overview",
    "Student Profile Analysis",
    "Statistical Analysis",
    "Advanced Relationships",
    "Faculty Comparison",
    "Ranking-Style Visuals",
    "Predictive Model",
    "Data Explorer",
]

PAGE_LABELS = {
    "Executive Overview": T["executive_overview"],
    "Student Profile Analysis": T["student_profile_analysis"],
    "Statistical Analysis": T["statistical_analysis"],
    "Advanced Relationships": T["advanced_relationships"],
    "Faculty Comparison": T["faculty_comparison"],
    "Ranking-Style Visuals": T["ranking_style_visuals"],
    "Predictive Model": T["predictive_model"],
    "Data Explorer": T["data_explorer"],
}

PAGE_PASSWORDS = {
    "Executive Overview": None,
    "Student Profile Analysis": "student123",
    "Statistical Analysis": "stats123",
    "Advanced Relationships": "advanced123",
    "Faculty Comparison": None,
    "Ranking-Style Visuals": None,
    "Predictive Model": "model123",
    "Data Explorer": "data123",
}

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"


def go_to_page(page_name):
    st.session_state.current_page = page_name


def check_page_password(page_name):
    required_password = PAGE_PASSWORDS.get(page_name)

    if required_password is None:
        return True

    auth_key = f"auth_{page_name}"

    if auth_key not in st.session_state:
        st.session_state[auth_key] = False

    if st.session_state[auth_key]:
        return True

    st.warning(f"{T['section_protected']}: {PAGE_LABELS.get(page_name, page_name)}")

    entered_password = st.text_input(
        f"{T['enter_password_for']} {PAGE_LABELS.get(page_name, page_name)}",
        type="password",
        key=f"password_input_{page_name}",
    )

    if entered_password == required_password:
        st.session_state[auth_key] = True
        st.success(T["access_granted"])
        st.rerun()

    if entered_password:
        st.error(T["incorrect_password"])

    return False

# =========================================================
# HOME PAGE ONLY
# =========================================================
if st.session_state.current_page == "Home":
    st.markdown(f"## {T['dashboard_navigation']}")
    st.caption(T["select_section"])

    row1 = st.columns(4)
    for i, page_name in enumerate(PAGES[:4]):
        label = PAGE_LABELS[page_name]
        if PAGE_PASSWORDS[page_name] is not None:
            label = "🔒 " + label

        if row1[i].button(label, use_container_width=True):
            go_to_page(page_name)
            st.rerun()

    row2 = st.columns(4)
    for i, page_name in enumerate(PAGES[4:]):
        label = PAGE_LABELS[page_name]
        if PAGE_PASSWORDS[page_name] is not None:
            label = "🔒 " + label

        if row2[i].button(label, use_container_width=True):
            go_to_page(page_name)
            st.rerun()

    st.stop()

# =========================================================
# INSIDE DASHBOARD PAGES
# =========================================================
page = st.session_state.current_page

back_col, title_col = st.columns([1, 5])
with back_col:
    if st.button(f"⬅ {T['back']}", use_container_width=True):
        st.session_state.current_page = "Home"
        st.rerun()

with title_col:
    st.markdown(f"## {PAGE_LABELS.get(page, page)}")

if check_page_password(page):
    if page == "Executive Overview":
        executive_overview(filtered_df)
    elif page == "Student Profile Analysis":
        profile_analysis(filtered_df)
    elif page == "Statistical Analysis":
        statistical_analysis(filtered_df)
    elif page == "Advanced Relationships":
        advanced_relationships(filtered_df)
    elif page == "Faculty Comparison":
        faculty_comparison(filtered_df)
    elif page == "Ranking-Style Visuals":
        ranking_visuals(filtered_df)
    elif page == "Predictive Model":
        predictive_model(filtered_df)
    elif page == "Data Explorer":
        data_explorer(filtered_df)


# In[ ]:




