#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

APP_PASSWORD = "HadiSawaya"   # change this

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
            key="password"
        )

        if "password" in st.session_state and st.session_state["password"] != "":
            st.error("Incorrect password")

        st.stop()

check_password()

st.markdown(
    """
    <style>
        .main {
            padding-top: 1rem;
        }
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
        "interpretation": "There is a statistically significant association at the 5% level." if p < 0.05 else "There is no statistically significant association at the 5% level.",
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
        label="Download filtered data",
        data=csv,
        file_name="usj_filtered_students.csv",
        mime="text/csv",
        use_container_width=True,
    )


def narrative_box(text: str):
    st.markdown(f'<div class="narrative-box">{text}</div>', unsafe_allow_html=True)


def executive_narrative(df: pd.DataFrame) -> str:
    total_students, number_of_faculties, average_credits, number_of_years = compute_kpis(df)
    if total_students == 0:
        return "No records match the current filters."

    top_faculty = add_count_percentage(df, "faculty").iloc[0]
    top_nat = add_count_percentage(df, "nationality").iloc[0]
    gender_tab = add_count_percentage(df, "gender")
    top_gender = gender_tab.iloc[0]

    year_counts = df.groupby("enrollment_year").size().reset_index(name="count").sort_values("count", ascending=False)
    top_year = year_counts.iloc[0]

    return (
        f"The filtered dataset contains <b>{total_students}</b> students across <b>{number_of_faculties}</b> faculties and "
        f"<b>{number_of_years}</b> enrollment years, with an average of <b>{average_credits:.2f}</b> credits. "
        f"The largest faculty in the current selection is <b>{top_faculty['faculty']}</b> with <b>{int(top_faculty['count'])}</b> students "
        f"({top_faculty['percentage']:.1f}%). The dominant gender group is <b>{top_gender['gender']}</b> with <b>{int(top_gender['count'])}</b> students "
        f"({top_gender['percentage']:.1f}%), while the most represented nationality is <b>{top_nat['nationality']}</b> with <b>{int(top_nat['count'])}</b> students "
        f"({top_nat['percentage']:.1f}%). The highest enrollment year in the filtered data is <b>{int(top_year['enrollment_year'])}</b> with <b>{int(top_year['count'])}</b> students."
    )


def profile_narrative(df: pd.DataFrame) -> str:
    if df.empty:
        return "No records match the current filters."

    program_tab = add_count_percentage(df, "program")
    top_program = program_tab.iloc[0]
    avg_credit_fac = df.groupby("faculty")["credits"].mean().reset_index(name="avg_credits").sort_values("avg_credits", ascending=False)
    best_fac = avg_credit_fac.iloc[0]

    return (
        f"Within the current filtered selection, the leading program is <b>{top_program['program']}</b> with <b>{int(top_program['count'])}</b> students "
        f"({top_program['percentage']:.1f}%). The faculty with the highest average credits is <b>{best_fac['faculty']}</b>, reaching <b>{best_fac['avg_credits']:.2f}</b> credits on average."
    )


def stats_narrative(result_bundle, var1: str, var2: str) -> str:
    if result_bundle is None:
        return f"The chi-square test for {var1} and {var2} cannot be computed with the current filtered data."
    result, _ = result_bundle
    return (
        f"The chi-square test examining the relationship between <b>{var1}</b> and <b>{var2}</b> produced a chi-square value of <b>{result['chi2']}</b>, "
        f"with a p-value of <b>{result['p_value']}</b> and <b>{result['dof']}</b> degrees of freedom. {result['interpretation']}"
    )


def ranking_narrative(df: pd.DataFrame) -> str:
    if df.empty:
        return "No records match the current filters."
    comparison = prepare_faculty_comparison(df)
    top_students = comparison.sort_values("total_students", ascending=False).iloc[0]
    top_credits = comparison.sort_values("avg_credits", ascending=False).iloc[0]
    return (
        f"In the current ranking-style comparison, <b>{top_students['faculty']}</b> holds first position by student count with <b>{int(top_students['total_students'])}</b> students, "
        f"while <b>{top_credits['faculty']}</b> leads by average credits with <b>{top_credits['avg_credits']:.2f}</b>."
    )


def predictive_narrative(model_output) -> str:
    if model_output is None:
        return "The predictive model cannot be estimated reliably with the current filtered sample size."
    metrics, importance_df, _ = model_output
    top_feature = importance_df.iloc[0]
    r2_text = f"{metrics['r2']}" if metrics['r2'] is not None else "N/A"
    return (
        f"The illustrative predictive model achieved an R² of <b>{r2_text}</b> and a mean absolute error of <b>{metrics['mae']}</b>. "
        f"The most influential predictor in the current model is <b>{top_feature['feature']}</b>."
    )


# =========================================================
# FILTERS
# =========================================================

def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("USJ Analytics")
    st.sidebar.caption("Interactive institutional dashboard")
    st.sidebar.markdown("### Filters")

    faculty_options = sorted(df["faculty"].dropna().unique().tolist())
    program_options = sorted(df["program"].dropna().unique().tolist())
    gender_options = sorted(df["gender"].dropna().unique().tolist())
    nationality_options = sorted(df["nationality"].dropna().unique().tolist())
    year_options = sorted(df["enrollment_year"].dropna().unique().tolist())

    selected_faculty = st.sidebar.multiselect("Faculty", faculty_options, default=[])
    selected_program = st.sidebar.multiselect("Program", program_options, default=[])
    selected_gender = st.sidebar.multiselect("Gender", gender_options, default=[])
    selected_nationality = st.sidebar.multiselect("Nationality", nationality_options, default=[])
    selected_year = st.sidebar.multiselect("Enrollment Year", year_options, default=[])

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
    st.sidebar.caption(f"Rows after filtering: {filtered_df.shape[0]}")

    return filtered_df


# =========================================================
# PAGES
# =========================================================
def executive_overview(df: pd.DataFrame):
    st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)
    narrative_box(executive_narrative(df))

    total_students, number_of_faculties, average_credits, number_of_years = compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", total_students)
    c2.metric("Faculties", number_of_faculties)
    c3.metric("Average Credits", f"{average_credits:.2f}")
    c4.metric("Enrollment Years", number_of_years)

    left, right = st.columns([1.2, 1])

    with left:
        faculty_counts = add_count_percentage(df, "faculty")
        fig = px.bar(faculty_counts, x="faculty", y="count", text="label", title="Students by Faculty")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, yaxis_title="Count", title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(faculty_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with right:
        gender_counts = add_count_percentage(df, "gender")
        fig = px.pie(gender_counts, names="gender", values="count", hole=0.45, title="Gender Distribution")
        fig.update_traces(textinfo="label+percent+value")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns([1.2, 1])

    with left:
        year_counts = df.groupby("enrollment_year").size().reset_index(name="count").sort_values("enrollment_year")
        year_counts["percentage"] = (year_counts["count"] / year_counts["count"].sum() * 100).round(1)
        year_counts["label"] = year_counts["count"].astype(str) + " (" + year_counts["percentage"].astype(str) + "%)"
        fig = px.line(year_counts, x="enrollment_year", y="count", markers=True, text="label", title="Enrollment Trend by Year")
        fig.update_traces(textposition="top center")
        fig.update_layout(height=420, yaxis_title="Count", title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(year_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with right:
        nationality_counts = add_count_percentage(df, "nationality")
        fig = px.bar(nationality_counts, x="nationality", y="count", text="label", title="Students by Nationality")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, yaxis_title="Count", title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(nationality_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)


def profile_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-title">Student Profile Analysis</div>', unsafe_allow_html=True)
    narrative_box(profile_narrative(df))

    t1, t2 = st.columns(2)

    with t1:
        program_counts = add_count_percentage(df, "program")
        fig = px.bar(program_counts, x="program", y="count", text="label", title="Students by Program")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(program_counts["count"])])
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        avg_credits = (
            df.groupby("faculty")["credits"]
            .mean()
            .reset_index(name="avg_credits")
            .sort_values("avg_credits", ascending=False)
        )
        avg_credits["label"] = avg_credits["avg_credits"].round(2).astype(str)
        fig = px.bar(avg_credits, x="faculty", y="avg_credits", text="label", title="Average Credits by Faculty")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(avg_credits["avg_credits"])])
        st.plotly_chart(fig, use_container_width=True)

    t3, t4 = st.columns(2)

    with t3:
        st.markdown("**Faculty by Gender**")
        st.dataframe(pd.crosstab(df["faculty"], df["gender"]), use_container_width=True)

    with t4:
        st.markdown("**Program by Nationality**")
        st.dataframe(pd.crosstab(df["program"], df["nationality"]), use_container_width=True)


def statistical_analysis(df: pd.DataFrame):
    st.markdown('<div class="section-title">Statistical Analysis</div>', unsafe_allow_html=True)
    st.caption("Chi-square tests for categorical associations")

    variables = ["faculty", "program", "gender", "nationality", "level"]
    c1, c2 = st.columns(2)
    var1 = c1.selectbox("Variable 1", variables, index=0)
    var2 = c2.selectbox("Variable 2", variables, index=2)

    if var1 == var2:
        st.warning("Please select two different variables.")
        return

    observed, result_bundle = chi_square_test(df, var1, var2)
    if observed is None:
        narrative_box(stats_narrative(None, var1, var2))
        st.info("Chi-square test requires at least two categories in each selected variable.")
        return

    result, expected = result_bundle
    narrative_box(stats_narrative(result_bundle, var1, var2))

    m1, m2, m3 = st.columns(3)
    m1.metric("Chi-square", result["chi2"])
    m2.metric("p-value", result["p_value"])
    m3.metric("Degrees of freedom", result["dof"])

    if result["p_value"] < 0.05:
        st.success(result["interpretation"])
    else:
        st.info(result["interpretation"])

    a, b = st.columns(2)
    with a:
        st.markdown("**Observed Frequencies**")
        st.dataframe(observed, use_container_width=True)
    with b:
        st.markdown("**Expected Frequencies**")
        st.dataframe(expected, use_container_width=True)


def advanced_relationships(df: pd.DataFrame):
    st.markdown('<div class="section-title">Advanced Relationships</div>', unsafe_allow_html=True)

    h1, h2 = st.columns(2)
    row_var = h1.selectbox("Heatmap row variable", ["faculty", "program", "gender", "nationality", "level"], index=0)
    col_var = h2.selectbox("Heatmap column variable", ["faculty", "program", "gender", "nationality", "level"], index=1)

    if row_var == col_var:
        st.warning("Please choose two different variables for the heatmap.")
    else:
        heatmap_table = build_heatmap_table(df, row_var, col_var, normalize=False)
        fig = px.imshow(heatmap_table, text_auto=True, aspect="auto", title=f"Heatmap of {row_var} by {col_var}")
        fig.update_layout(height=450, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        heatmap_pct = build_heatmap_table(df, row_var, col_var, normalize=True)
        fig_pct = px.imshow(heatmap_pct, text_auto=True, aspect="auto", title=f"Row-normalized heatmap of {row_var} by {col_var} (%)")
        fig_pct.update_layout(height=450, title_x=0.5, template="plotly_white")
        st.plotly_chart(fig_pct, use_container_width=True)

    corr = build_correlation_matrix(df)
    st.markdown("**Correlation Matrix**")
    fig_corr = px.imshow(corr, text_auto=True, aspect="auto", title="Numeric Correlation Matrix")
    fig_corr.update_layout(height=350, title_x=0.5, template="plotly_white")
    st.plotly_chart(fig_corr, use_container_width=True)
    st.dataframe(corr, use_container_width=True)


def faculty_comparison(df: pd.DataFrame):
    st.markdown('<div class="section-title">Faculty Comparison Dashboard</div>', unsafe_allow_html=True)
    comparison = prepare_faculty_comparison(df)
    narrative_box(ranking_narrative(df))
    st.dataframe(comparison, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(comparison, x="faculty", y="total_students", text_auto=True, title="Faculty Ranking by Student Count")
        fig.update_layout(height=420, title_x=0.5, template="plotly_white")
        fig.update_yaxes(range=[0, get_ymax(comparison["total_students"])])
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(comparison, x="faculty", y="avg_credits", text_auto=".2f", title="Faculty Ranking by Average Credits")
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
        title="Faculty Comparison Bubble Chart",
    )
    fig_bubble.update_layout(height=500, title_x=0.5, template="plotly_white")
    st.plotly_chart(fig_bubble, use_container_width=True)


def ranking_visuals(df: pd.DataFrame):
    st.markdown('<div class="section-title">Ranking-Style Visuals</div>', unsafe_allow_html=True)
    narrative_box(ranking_narrative(df))

    ranking_df = prepare_faculty_comparison(df)

    left, right = st.columns(2)
    with left:
        st.markdown("**Top Faculties by Student Count**")
        st.dataframe(ranking_df[["student_rank", "faculty", "total_students"]], use_container_width=True)
    with right:
        st.markdown("**Top Faculties by Average Credits**")
        st.dataframe(ranking_df[["credit_rank", "faculty", "avg_credits"]], use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Student Count", x=ranking_df["faculty"], y=ranking_df["total_students"]))
    fig.add_trace(go.Scatter(name="Average Credits", x=ranking_df["faculty"], y=ranking_df["avg_credits"], mode="lines+markers", yaxis="y2"))
    fig.update_layout(
        title="Dual Ranking View by Faculty",
        yaxis=dict(title="Student Count"),
        yaxis2=dict(title="Average Credits", overlaying="y", side="right"),
        height=500,
        title_x=0.5,
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def predictive_model(df: pd.DataFrame):
    st.markdown('<div class="section-title">Predictive Model</div>', unsafe_allow_html=True)
    st.caption("Illustrative machine-learning panel using available student attributes to predict credits")

    model_output = train_predictive_model(df)
    narrative_box(predictive_narrative(model_output))

    if model_output is None:
        st.info("The current filtered dataset is too small for a meaningful predictive model. Add more rows or widen the filters.")
        return

    metrics, importance_df, preview = model_output

    c1, c2 = st.columns(2)
    c1.metric("Model R²", metrics["r2"] if metrics["r2"] is not None else "N/A")
    c2.metric("Model MAE", metrics["mae"])

    top_features = importance_df.head(12)
    fig = px.bar(top_features, x="importance", y="feature", orientation="h", title="Top Feature Importances")
    fig.update_layout(height=500, title_x=0.5, template="plotly_white", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Prediction Preview**")
    st.dataframe(preview.head(10), use_container_width=True)


def data_explorer(df: pd.DataFrame):
    st.markdown('<div class="section-title">Data Explorer</div>', unsafe_allow_html=True)
    st.caption("Filtered table preview and export")
    st.dataframe(df, use_container_width=True, height=500)
    add_download_button(df)


# =========================================================
# MAIN APP
# =========================================================
header_left, header_right = st.columns([4, 1.4])
with header_left:
    st.title("USJ Advanced Analytics Dashboard")
    st.markdown('<div class="small-note">Professional interactive dashboard for institutional student analytics</div>', unsafe_allow_html=True)
with header_right:
    pass
    # Example if you want the logo later:
    # st.image(r"C:\Users\710584\Downloads\25-04-28-Logo-UniteAssuranceQualite-150 ans-LK-01.png", width=260)

try:
    df = load_data()
except Exception as e:
    st.error("Database connection failed.")
    st.exception(e)
    st.stop()

if df.empty:
    st.warning("No data found in the students table.")
    st.stop()

filtered_df = sidebar_filters(df)


# =========================================================
# BUTTON NAVIGATION WITH PAGE PASSWORDS
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
    st.session_state.current_page = "Executive Overview"

st.markdown("### Navigation")

row1 = st.columns(4)
for i, page_name in enumerate(PAGES[:4]):
    label = page_name
    if PAGE_PASSWORDS[page_name] is not None:
        label = "🔒 " + label

    if row1[i].button(label, use_container_width=True):
        st.session_state.current_page = page_name

row2 = st.columns(4)
for i, page_name in enumerate(PAGES[4:]):
    label = page_name
    if PAGE_PASSWORDS[page_name] is not None:
        label = "🔒 " + label

    if row2[i].button(label, use_container_width=True):
        st.session_state.current_page = page_name

page = st.session_state.current_page

st.markdown(f"**Current section:** {page}")


def check_page_password(page_name):
    required_password = PAGE_PASSWORDS.get(page_name)

    if required_password is None:
        return True

    auth_key = f"auth_{page_name}"

    if auth_key not in st.session_state:
        st.session_state[auth_key] = False

    if st.session_state[auth_key]:
        return True

    st.warning(f"This section is protected: {page_name}")

    entered_password = st.text_input(
        f"Enter password for {page_name}",
        type="password",
        key=f"password_input_{page_name}"
    )

    if entered_password == required_password:
        st.session_state[auth_key] = True
        st.success("Access granted.")
        st.rerun()

    if entered_password:
        st.error("Incorrect password.")

    return False


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




