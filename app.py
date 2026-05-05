import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="USJ Exit Survey Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# CONSTANTS
# ============================================================

MAX_SCORE = 4

# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():
    file_path = "Exit survey 24-25.xlsx"
    df = pd.read_excel(file_path)
    return df

df_original = load_data()

# ============================================================
# HELPER FUNCTIONS
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
        return "#777777"
    elif pct <= 43.75:
        return "#C62828"
    elif pct <= 62.50:
        return "#F57C00"
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
            min-height:230px;
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
        "Diplôme",
        "Cursus",
        "Niveau"
    ]

    for col in filter_columns:
        if col in filtered_df.columns:
            available_options = sorted(filtered_df[col].dropna().unique())

            selected_options = st.sidebar.multiselect(
                col,
                available_options,
                default=available_options
            )

            filtered_df = filtered_df[filtered_df[col].isin(selected_options)]

    return filtered_df


# ============================================================
# PAGE 1: GLOBAL KPIs
# ============================================================

def page_1_kpis(df):

    st.title("Satisfaction globale et expérience")

    filtered_df = apply_linked_filters(df)

    if filtered_df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    # ------------------------------------------------------------
    # Adjust these variable names if needed
    # ------------------------------------------------------------

    satisfaction_global_col = "Satisfaction globale à l’Université"
    recommendation_col = "Taux de recommandation de l’USJ"
    experience_col = "Expérience globale USJ"

    required_cols = [
        satisfaction_global_col,
        recommendation_col,
        experience_col
    ]

    missing_cols = [col for col in required_cols if col not in filtered_df.columns]

    if missing_cols:
        st.error("Colonnes manquantes dans le fichier :")
        st.write(missing_cols)
        return

    # ------------------------------------------------------------
    # Compute KPIs as percentages
    # ------------------------------------------------------------

    satisfaction_global_mean = filtered_df[satisfaction_global_col].mean()
    satisfaction_global_pct = satisfaction_global_mean / MAX_SCORE * 100
    satisfaction_global_level = satisfaction_label(satisfaction_global_pct)
    satisfaction_global_color = satisfaction_color(satisfaction_global_pct)

    recommendation_mean = filtered_df[recommendation_col].mean()
    recommendation_pct = recommendation_mean / MAX_SCORE * 100
    recommendation_level = satisfaction_label(recommendation_pct)
    recommendation_color = satisfaction_color(recommendation_pct)

    experience_mean = filtered_df[experience_col].mean()
    experience_pct = experience_mean / MAX_SCORE * 100
    experience_level = satisfaction_label(experience_pct)
    experience_color = satisfaction_color(experience_pct)

    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_card(
            "Satisfaction globale à l’Université",
            f"{satisfaction_global_pct:.1f}%",
            "Score de satisfaction",
            satisfaction_global_level,
            satisfaction_global_color
        )

    with col2:
        kpi_card(
            "Taux de recommandation de l’USJ",
            f"{recommendation_pct:.1f}%",
            "Pourcentage",
            recommendation_level,
            recommendation_color
        )

    with col3:
        kpi_card(
            "Expérience globale USJ",
            f"{experience_pct:.1f}%",
            "Score de satisfaction",
            experience_level,
            experience_color
        )


# ============================================================
# PAGE 2: DETAILED SATISFACTION ANALYSIS
# ============================================================

def page_2_satisfaction_analysis(df):

    st.title("Analyse détaillée de la satisfaction")

    filtered_df = apply_linked_filters(df)

    if filtered_df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    satisfaction_cols = [
        col for col in filtered_df.columns
        if col.startswith("Q5")
    ]

    if len(satisfaction_cols) == 0:
        st.error("Aucune colonne Q5 trouvée. Vérifiez les noms des variables.")
        return

    st.markdown(
        """
        Les scores de satisfaction sont présentés en pourcentage selon la formule suivante :

        **Pourcentage de satisfaction = moyenne / 4 × 100**
        """
    )

    # ------------------------------------------------------------
    # Satisfaction by item
    # ------------------------------------------------------------

    st.subheader("1. Satisfaction par item")

    summary = []

    for col in satisfaction_cols:
        mean_score = filtered_df[col].mean()
        pct_score = mean_score / MAX_SCORE * 100

        summary.append({
            "Item": col,
            "Moyenne": round(mean_score, 2),
            "Satisfaction (%)": round(pct_score, 1),
            "Niveau": satisfaction_label(pct_score),
            "N valide": filtered_df[col].notna().sum()
        })

    summary_df = pd.DataFrame(summary).sort_values(
        by="Satisfaction (%)",
        ascending=False
    )

    st.dataframe(summary_df, use_container_width=True)

    fig_items = px.bar(
        summary_df,
        x="Satisfaction (%)",
        y="Item",
        orientation="h",
        text="Satisfaction (%)",
        color="Niveau",
        title="Pourcentage de satisfaction par item",
        color_discrete_map={
            "Très faible satisfaction": "#C62828",
            "Faible satisfaction": "#F57C00",
            "Satisfaction modérée": "#F57C00",
            "Forte satisfaction": "#2E7D32"
        }
    )

    fig_items.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="Satisfaction (%)",
        yaxis_title="Item",
        height=600
    )

    fig_items.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    st.plotly_chart(fig_items, use_container_width=True)

    # ------------------------------------------------------------
    # Overall satisfaction
    # ------------------------------------------------------------

    st.subheader("2. Score global de satisfaction")

    filtered_df["Score global moyen"] = filtered_df[satisfaction_cols].mean(axis=1)
    filtered_df["Satisfaction globale (%)"] = (
        filtered_df["Score global moyen"] / MAX_SCORE * 100
    )

    overall_mean = filtered_df["Score global moyen"].mean()
    overall_pct = filtered_df["Satisfaction globale (%)"].mean()
    overall_level = satisfaction_label(overall_pct)
    overall_color = satisfaction_color(overall_pct)

    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_card(
            "Score moyen global",
            f"{overall_mean:.2f} / 4",
            "Moyenne des items Q5",
            overall_level,
            overall_color
        )

    with col2:
        kpi_card(
            "Satisfaction globale",
            f"{overall_pct:.1f}%",
            "Score transformé en pourcentage",
            overall_level,
            overall_color
        )

    with col3:
        kpi_card(
            "Niveau de satisfaction",
            overall_level,
            "Classification automatique",
            "Basé sur les seuils définis",
            overall_color
        )

    # ------------------------------------------------------------
    # Distribution
    # ------------------------------------------------------------

    st.subheader("3. Distribution des niveaux de satisfaction")

    filtered_df["Catégorie de satisfaction"] = filtered_df[
        "Satisfaction globale (%)"
    ].apply(satisfaction_label)

    dist_df = (
        filtered_df["Catégorie de satisfaction"]
        .value_counts()
        .reset_index()
    )

    dist_df.columns = ["Catégorie", "Fréquence"]
    dist_df["Pourcentage"] = (
        dist_df["Fréquence"] / dist_df["Fréquence"].sum() * 100
    ).round(1)

    st.dataframe(dist_df, use_container_width=True)

    fig_dist = px.bar(
        dist_df,
        x="Catégorie",
        y="Pourcentage",
        text="Pourcentage",
        color="Catégorie",
        title="Distribution des niveaux de satisfaction",
        color_discrete_map={
            "Très faible satisfaction": "#C62828",
            "Faible satisfaction": "#F57C00",
            "Satisfaction modérée": "#F57C00",
            "Forte satisfaction": "#2E7D32"
        }
    )

    fig_dist.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_dist.update_layout(
        xaxis_title="Catégorie",
        yaxis_title="Pourcentage",
        showlegend=False
    )

    st.plotly_chart(fig_dist, use_container_width=True)

    # ------------------------------------------------------------
    # Group comparison
    # ------------------------------------------------------------

    st.subheader("4. Comparaison par groupe")

    group_options = [
        col for col in ["Institution", "Faculté", "Diplôme", "Cursus", "Niveau"]
        if col in filtered_df.columns
    ]

    group_var = st.selectbox(
        "Choisir la variable de comparaison",
        group_options
    )

    group_summary = (
        filtered_df
        .groupby(group_var)["Satisfaction globale (%)"]
        .agg(["count", "mean", "std"])
        .reset_index()
    )

    group_summary.columns = [
        group_var,
        "N valide",
        "Satisfaction moyenne (%)",
        "Écart-type"
    ]

    group_summary["Satisfaction moyenne (%)"] = group_summary[
        "Satisfaction moyenne (%)"
    ].round(1)

    group_summary["Écart-type"] = group_summary["Écart-type"].round(2)

    group_summary["Niveau"] = group_summary[
        "Satisfaction moyenne (%)"
    ].apply(satisfaction_label)

    group_summary = group_summary.sort_values(
        by="Satisfaction moyenne (%)",
        ascending=False
    )

    st.dataframe(group_summary, use_container_width=True)

    fig_group = px.bar(
        group_summary,
        x=group_var,
        y="Satisfaction moyenne (%)",
        text="Satisfaction moyenne (%)",
        color="Niveau",
        title=f"Satisfaction globale selon {group_var}",
        color_discrete_map={
            "Très faible satisfaction": "#C62828",
            "Faible satisfaction": "#F57C00",
            "Satisfaction modérée": "#F57C00",
            "Forte satisfaction": "#2E7D32"
        }
    )

    fig_group.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig_group.update_layout(
        xaxis_title=group_var,
        yaxis_title="Satisfaction moyenne (%)",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig_group, use_container_width=True)

    # ------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------

    st.subheader("5. Interprétation automatique")

    best_item = summary_df.iloc[0]
    weakest_item = summary_df.iloc[-1]

    best_group = group_summary.iloc[0]
    weakest_group = group_summary.iloc[-1]

    st.markdown(f"""
    Le score global de satisfaction est de **{overall_pct:.1f}%**, ce qui correspond à un niveau de **{overall_level}**.

    L’item le mieux évalué est **{best_item["Item"]}**, avec un score de satisfaction de **{best_item["Satisfaction (%)"]:.1f}%**.

    L’item le moins bien évalué est **{weakest_item["Item"]}**, avec un score de satisfaction de **{weakest_item["Satisfaction (%)"]:.1f}%**.

    Selon la variable **{group_var}**, le niveau de satisfaction le plus élevé est observé pour **{best_group[group_var]}** avec **{best_group["Satisfaction moyenne (%)"]:.1f}%**, tandis que le niveau le plus faible est observé pour **{weakest_group[group_var]}** avec **{weakest_group["Satisfaction moyenne (%)"]:.1f}%**.
    """)

    # ------------------------------------------------------------
    # Export
    # ------------------------------------------------------------

    st.subheader("6. Export des résultats")

    st.download_button(
        label="Télécharger le tableau de satisfaction par item",
        data=summary_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="page2_satisfaction_par_item.csv",
        mime="text/csv"
    )

    st.download_button(
        label="Télécharger le tableau de satisfaction par groupe",
        data=group_summary.to_csv(index=False).encode("utf-8-sig"),
        file_name="page2_satisfaction_par_groupe.csv",
        mime="text/csv"
    )


# ============================================================
# NAVIGATION
# ============================================================

st.sidebar.title("USJ Exit Survey Dashboard")

page = st.sidebar.radio(
    "Navigation",
    [
        "Page 1 - KPIs globaux",
        "Page 2 - Satisfaction détaillée"
    ]
)

if page == "Page 1 - KPIs globaux":
    page_1_kpis(df_original)

elif page == "Page 2 - Satisfaction détaillée":
    page_2_satisfaction_analysis(df_original)
