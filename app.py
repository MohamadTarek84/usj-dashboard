import streamlit as st
import pandas as pd
import plotly.express as px

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


# ============================================================
# HELPERS
# ============================================================

def clean_text(x):
    return (
        str(x)
        .lower()
        .strip()
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
        "Diplôme",
        "Cursus",
        "Niveau"
    ]

    for col in filter_columns:
        if col in filtered_df.columns:
            options = sorted(filtered_df[col].dropna().astype(str).unique())
            options = ["Tous"] + options

            selected = st.sidebar.selectbox(
                col,
                options,
                index=0
            )

            if selected != "Tous":
                filtered_df = filtered_df[
                    filtered_df[col].astype(str) == selected
                ]

    return filtered_df


def numeric_mean(df, col):
    return pd.to_numeric(df[col], errors="coerce").mean()


# ============================================================
# PAGE 1
# ============================================================

def page_1_kpis(df):

    st.title("Satisfaction globale et expérience")

    filtered_df = apply_linked_filters(df)

    if filtered_df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    satisfaction_global_col = find_column(filtered_df, ["satisfaction", "univers"])
    recommendation_col = find_column(filtered_df, ["recommand"])

    if satisfaction_global_col is None and "Q1" in filtered_df.columns:
        satisfaction_global_col = "Q1"

    if recommendation_col is None and "Q2" in filtered_df.columns:
        recommendation_col = "Q2"

    # Experience globale: instead of searching for missing variable,
    # we calculate it from Q5 items.
    q5_cols = [
        col for col in filtered_df.columns
        if str(col).startswith("Q5")
    ]

    missing_cols = []

    if satisfaction_global_col is None:
        missing_cols.append("Satisfaction globale")

    if recommendation_col is None:
        missing_cols.append("Recommandation")

    if len(q5_cols) == 0:
        missing_cols.append("Items Q5 pour calculer l’expérience globale")

    if missing_cols:
        st.error("Colonnes non trouvées automatiquement :")
        st.write(missing_cols)

        with st.expander("Voir les colonnes disponibles"):
            st.write(df.columns.tolist())

        return

    satisfaction_mean = numeric_mean(filtered_df, satisfaction_global_col)
    satisfaction_pct = satisfaction_mean / MAX_SCORE * 100

    recommendation_mean = numeric_mean(filtered_df, recommendation_col)
    recommendation_pct = recommendation_mean / MAX_SCORE * 100

    q5_numeric = filtered_df[q5_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    experience_mean = q5_numeric.mean(axis=1).mean()
    experience_pct = experience_mean / MAX_SCORE * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_card(
            "Satisfaction globale à l’Université",
            f"{satisfaction_pct:.1f}%",
            "Score de satisfaction",
            satisfaction_label(satisfaction_pct),
            satisfaction_color(satisfaction_pct)
        )

    with col2:
        kpi_card(
            "Taux de recommandation de l’USJ",
            f"{recommendation_pct:.1f}%",
            "Pourcentage",
            satisfaction_label(recommendation_pct),
            satisfaction_color(recommendation_pct)
        )

    with col3:
        kpi_card(
            "Expérience globale USJ",
            f"{experience_pct:.1f}%",
            "Moyenne des items Q5",
            satisfaction_label(experience_pct),
            satisfaction_color(experience_pct)
        )

    with st.expander("Variables utilisées"):
        st.write({
            "Satisfaction globale": satisfaction_global_col,
            "Recommandation": recommendation_col,
            "Expérience globale": "Calculée à partir des items Q5",
            "Nombre d’items Q5": len(q5_cols)
        })


# ============================================================
# PAGE 2
# ============================================================

def page_2_satisfaction(df):

    st.title("Analyse détaillée de la satisfaction")

    filtered_df = apply_linked_filters(df)

    if filtered_df.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    satisfaction_cols = [
        col for col in filtered_df.columns
        if str(col).startswith("Q5")
    ]

    if len(satisfaction_cols) == 0:
        st.error("Aucune colonne Q5 trouvée.")
        with st.expander("Voir les colonnes disponibles"):
            st.write(df.columns.tolist())
        return

    for col in satisfaction_cols:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce")

    st.markdown(
        """
        **Pourcentage de satisfaction = moyenne / 4 × 100**
        """
    )

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

    st.subheader("1. Satisfaction par item")
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

    filtered_df["Score global Q5"] = filtered_df[satisfaction_cols].mean(axis=1)
    filtered_df["Satisfaction globale Q5 (%)"] = (
        filtered_df["Score global Q5"] / MAX_SCORE * 100
    )

    overall_mean = filtered_df["Score global Q5"].mean()
    overall_pct = filtered_df["Satisfaction globale Q5 (%)"].mean()

    st.subheader("2. Score global Q5")

    col1, col2, col3 = st.columns(3)

    with col1:
        kpi_card(
            "Score moyen Q5",
            f"{overall_mean:.2f} / 4",
            "Moyenne des items Q5",
            satisfaction_label(overall_pct),
            satisfaction_color(overall_pct)
        )

    with col2:
        kpi_card(
            "Satisfaction Q5",
            f"{overall_pct:.1f}%",
            "Score transformé en pourcentage",
            satisfaction_label(overall_pct),
            satisfaction_color(overall_pct)
        )

    with col3:
        kpi_card(
            "Niveau global",
            satisfaction_label(overall_pct),
            "Classification automatique",
            "Selon les seuils définis",
            satisfaction_color(overall_pct)
        )

    st.subheader("3. Comparaison par groupe")

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
        .groupby(group_var)["Satisfaction globale Q5 (%)"]
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
        title=f"Satisfaction globale Q5 selon {group_var}",
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
    page_2_satisfaction(df_original)
