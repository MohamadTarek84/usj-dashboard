#!/usr/bin/env python
# coding: utf-8

# In[11]:


import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from io import BytesIO

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# App configuration
# ============================================================

st.set_page_config(
    page_title="Interactive SWOT Classification Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Interactive SWOT Classification and Expert Review Dashboard")
st.caption(
    "This dashboard classifies open-ended answers into SWOT categories, suggests thematic groups, "
    "allows experts to revise the classification, and automatically updates the final SWOT figure."
)


# ============================================================
# 1. Training data for SWOT model
# ============================================================

training_data = [
    # Strengths
    ("Experienced staff", "Strength"),
    ("Qualified employees", "Strength"),
    ("Strong academic expertise", "Strength"),
    ("Committed team members", "Strength"),
    ("Strong institutional knowledge", "Strength"),
    ("Strong university reputation", "Strength"),
    ("Good reporting capacity", "Strength"),
    ("Reliable internal data", "Strength"),
    ("Good leadership support", "Strength"),
    ("Strong quality assurance process", "Strength"),
    ("Good student services", "Strength"),
    ("Strong research capacity", "Strength"),
    ("Existing dashboards and reports", "Strength"),
    ("Good internal collaboration", "Strength"),
    ("Strong institutional memory", "Strength"),

    # Weaknesses
    ("Lack of staff", "Weakness"),
    ("Not enough employees", "Weakness"),
    ("Low salaries", "Weakness"),
    ("Low income", "Weakness"),
    ("High rent", "Weakness"),
    ("Limited budget", "Weakness"),
    ("Manual processes", "Weakness"),
    ("Slow administrative procedures", "Weakness"),
    ("Lack of automation", "Weakness"),
    ("Incomplete data", "Weakness"),
    ("Weak communication", "Weakness"),
    ("No centralized dashboard", "Weakness"),
    ("Poor coordination between departments", "Weakness"),
    ("Lack of documentation", "Weakness"),
    ("Limited training opportunities", "Weakness"),

    # Opportunities
    ("New digital tools can improve reporting", "Opportunity"),
    ("Dashboards can support decision-making", "Opportunity"),
    ("Automation can reduce workload", "Opportunity"),
    ("Machine learning can support prediction", "Opportunity"),
    ("International partnerships can improve benchmarking", "Opportunity"),
    ("External funding opportunities", "Opportunity"),
    ("New grants can support projects", "Opportunity"),
    ("Online platforms can improve data collection", "Opportunity"),
    ("Digital transformation can improve efficiency", "Opportunity"),
    ("New systems can improve monitoring", "Opportunity"),
    ("Training programs can improve staff capacity", "Opportunity"),
    ("Data integration can support advanced analytics", "Opportunity"),
    ("Quality assurance can be strengthened", "Opportunity"),
    ("Strategic planning can strengthen performance", "Opportunity"),

    # Threats
    ("Economic crisis affects planning", "Threat"),
    ("Financial instability may reduce resources", "Threat"),
    ("Inflation increases operational costs", "Threat"),
    ("Competition from other universities", "Threat"),
    ("Cybersecurity risks threaten data", "Threat"),
    ("Data breaches may affect trust", "Threat"),
    ("Political instability can disrupt planning", "Threat"),
    ("Brain drain may reduce qualified staff", "Threat"),
    ("Declining enrollment can affect sustainability", "Threat"),
    ("Budget cuts may affect services", "Threat"),
    ("Rising costs may affect financial sustainability", "Threat"),
    ("External ranking criteria may change", "Threat"),
    ("Regional instability may affect operations", "Threat"),
    ("Technological changes may make systems obsolete", "Threat"),
]

train_df = pd.DataFrame(training_data, columns=["answer", "true_swot"])


# ============================================================
# 2. Train SWOT classifier
# ============================================================

@st.cache_resource
def train_swot_model():
    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 3),
        max_features=8000
    )

    char_vectorizer = TfidfVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=5000
    )

    model = Pipeline([
        ("features", FeatureUnion([
            ("word_tfidf", word_vectorizer),
            ("char_tfidf", char_vectorizer),
        ])),
        ("clf", LogisticRegression(
            max_iter=3000,
            solver="lbfgs",
            class_weight="balanced",
            C=2.0
        ))
    ])

    model.fit(train_df["answer"], train_df["true_swot"])
    return model


swot_model = train_swot_model()


# ============================================================
# 3. Theme / group dictionary
# ============================================================

theme_dictionary = {
    "Human resource shortage": [
        "lack of staff",
        "not enough employees",
        "limited staff",
        "human resources shortage",
        "high workload",
        "insufficient human resources"
    ],
    "Economic and financial pressure": [
        "low salaries",
        "low income",
        "high rent",
        "limited budget",
        "financial pressure",
        "rising costs",
        "operational costs"
    ],
    "Operational inefficiency": [
        "manual processes",
        "slow procedures",
        "manual data entry",
        "lack of automation",
        "time-consuming",
        "inefficient services"
    ],
    "Internal communication and coordination": [
        "weak communication",
        "poor coordination",
        "limited coordination",
        "lack of communication",
        "coordination between departments"
    ],
    "Institutional reputation": [
        "strong reputation",
        "well-known institution",
        "positive image",
        "recognized programs",
        "stakeholder trust"
    ],
    "Data and reporting capacity": [
        "reliable data",
        "reporting capacity",
        "historical data",
        "quality reports",
        "data sources"
    ],
    "Digital transformation": [
        "dashboards",
        "automation",
        "digital tools",
        "machine learning",
        "data visualization",
        "digital transformation"
    ],
    "Partnerships and collaboration": [
        "international partnerships",
        "peer universities",
        "collaboration",
        "external cooperation",
        "professional associations"
    ],
    "Funding opportunities": [
        "external funding",
        "grants",
        "donor funding",
        "funding calls",
        "international projects"
    ],
    "Market competition": [
        "competition",
        "other universities",
        "student recruitment",
        "cheaper alternatives",
        "competitors"
    ],
    "Technology and cybersecurity risks": [
        "cybersecurity",
        "data breach",
        "cyberattack",
        "data security",
        "systems obsolete"
    ],
    "Economic instability": [
        "economic crisis",
        "inflation",
        "financial instability",
        "currency fluctuation",
        "economic pressure"
    ],
    "Strategic and regulatory risks": [
        "political instability",
        "regulations",
        "ranking criteria",
        "external shocks",
        "government regulations"
    ],
    "Other / To be reviewed": [
        "other",
        "unclear",
        "to be reviewed"
    ]
}


@st.cache_resource
def prepare_theme_model():
    theme_examples = []

    for theme, examples in theme_dictionary.items():
        for example in examples:
            theme_examples.append((theme, example))

    theme_df = pd.DataFrame(theme_examples, columns=["theme", "theme_example"])

    theme_vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 3)
    )

    theme_matrix = theme_vectorizer.fit_transform(theme_df["theme_example"])

    return theme_df, theme_vectorizer, theme_matrix


theme_df, theme_vectorizer, theme_matrix = prepare_theme_model()


def assign_theme(answer):
    answer_vec = theme_vectorizer.transform([answer])
    similarities = cosine_similarity(answer_vec, theme_matrix)[0]

    best_index = similarities.argmax()
    best_score = similarities[best_index]
    best_theme = theme_df.iloc[best_index]["theme"]

    if best_score < 0.10:
        return "Other / To be reviewed", round(best_score, 3)

    return best_theme, round(best_score, 3)


# ============================================================
# 4. Default demo answers
# ============================================================

default_answers = [
    "Low salaries",
    "Low income",
    "The rent is high",
    "We do not have enough staff",
    "There is a lack of human resources",
    "Manual data entry takes too much time",
    "The university has a strong reputation",
    "Experienced professors",
    "Reliable data sources",
    "New dashboards can improve decision-making",
    "External funding can help us develop new projects",
    "International partnerships can improve benchmarking",
    "Competition from other universities is increasing",
    "Cybersecurity is a serious risk",
    "Budget cuts may delay strategic projects",
    "Economic crisis may reduce enrollment"
]


# ============================================================
# 5. Data loading
# ============================================================

st.sidebar.header("Data source")

uploaded_file = st.sidebar.file_uploader(
    "Upload Excel or CSV file with an 'answer' column",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    if "answer" not in raw_df.columns:
        st.error("Your file must contain a column named 'answer'.")
        st.stop()

    answers_df = raw_df[["answer"]].dropna().copy()

else:
    st.sidebar.info("No file uploaded. Demo answers are used.")
    answers_df = pd.DataFrame({"answer": default_answers})


# ============================================================
# 6. Automatic classification
# ============================================================

def classify_answers(input_df):
    df = input_df.copy()

    df["suggested_swot"] = swot_model.predict(df["answer"])
    df["confidence"] = swot_model.predict_proba(df["answer"]).max(axis=1).round(3)

    theme_results = df["answer"].apply(assign_theme)
    df["suggested_group"] = theme_results.apply(lambda x: x[0])
    df["group_similarity"] = theme_results.apply(lambda x: x[1])

    df["final_swot"] = df["suggested_swot"]
    df["final_group"] = df["suggested_group"]
    df["expert_comment"] = ""

    return df


if "custom_groups" not in st.session_state:
    st.session_state.custom_groups = []

if "review_df" not in st.session_state:
    st.session_state.review_df = classify_answers(answers_df)

if st.sidebar.button("Re-run classification"):
    st.session_state.review_df = classify_answers(answers_df)


# ============================================================
# 7. Add new group above the table
# ============================================================

st.header("1. Expert Review Table")
st.write(
    "Experts can revise the suggested SWOT category and the thematic group. "
    "They can select an existing group or add a new group to the dropdown list. "
    "The summary tables and SWOT figure update automatically after editing."
)

st.subheader("Add a new group if needed")

col_new_group, col_button = st.columns([3, 1])

with col_new_group:
    new_group_name = st.text_input("New group name", key="new_group_name")

with col_button:
    st.write("")
    st.write("")
    add_group_clicked = st.button("Add group")

if add_group_clicked:
    new_group_name = new_group_name.strip()

    if new_group_name:
        if new_group_name not in st.session_state.custom_groups:
            st.session_state.custom_groups.append(new_group_name)
            st.success(f"New group added: {new_group_name}")
            st.rerun()
        else:
            st.info("This group already exists.")


# ============================================================
# 8. Build dropdown group options
# ============================================================

existing_groups = sorted(set(theme_dictionary.keys()))
custom_groups = sorted(set(st.session_state.custom_groups))

current_groups = (
    st.session_state.review_df["final_group"]
    .dropna()
    .astype(str)
    .str.strip()
    .replace("", pd.NA)
    .dropna()
    .unique()
    .tolist()
)

group_options = sorted(set(existing_groups + custom_groups + current_groups))


# Sort first table by Final SWOT, then Final group, then answer
review_df = st.session_state.review_df.sort_values(
    by=["final_swot", "final_group", "answer"],
    ascending=[True, True, True]
).reset_index(drop=True)


# ============================================================
# 9. Editable expert review table
# ============================================================

swot_options = ["Strength", "Weakness", "Opportunity", "Threat"]

edited_df = st.data_editor(
    review_df,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "answer": st.column_config.TextColumn(
            "Original answer",
            disabled=True,
            width="large"
        ),
        "suggested_swot": st.column_config.TextColumn(
            "Suggested SWOT",
            disabled=True
        ),
        "confidence": st.column_config.NumberColumn(
            "Confidence",
            disabled=True,
            format="%.3f"
        ),
        "suggested_group": st.column_config.TextColumn(
            "Suggested group",
            disabled=True,
            width="medium"
        ),
        "group_similarity": st.column_config.NumberColumn(
            "Group similarity",
            disabled=True,
            format="%.3f"
        ),
        "final_swot": st.column_config.SelectboxColumn(
            "Final SWOT",
            options=swot_options,
            required=True
        ),
        "final_group": st.column_config.SelectboxColumn(
            "Final group",
            options=group_options,
            required=True
        ),
        "expert_comment": st.column_config.TextColumn(
            "Expert comment",
            width="medium"
        ),
    },
    hide_index=True,
    key="swot_editor"
)

# Keep edited results in session state
st.session_state.review_df = edited_df.copy()


# ============================================================
# 10. Summary tables sorted by highest frequency
# ============================================================

st.header("2. Summary Tables")

summary_swot = (
    edited_df.groupby("final_swot")
    .size()
    .reset_index(name="number_of_answers")
)

summary_swot["percentage"] = (
    summary_swot["number_of_answers"] /
    summary_swot["number_of_answers"].sum() * 100
).round(1)

summary_swot = summary_swot.sort_values(
    by="number_of_answers",
    ascending=False
).reset_index(drop=True)


summary_group = (
    edited_df.groupby(["final_swot", "final_group"])
    .size()
    .reset_index(name="number_of_answers")
)

summary_group["percentage"] = (
    summary_group["number_of_answers"] /
    summary_group["number_of_answers"].sum() * 100
).round(1)

summary_group = summary_group.sort_values(
    by="number_of_answers",
    ascending=False
).reset_index(drop=True)


col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Summary by SWOT")
    st.dataframe(summary_swot, use_container_width=True, hide_index=True)

with col_b:
    st.subheader("Summary by SWOT and group")
    st.dataframe(summary_group, use_container_width=True, hide_index=True)


# ============================================================
# 11. SWOT visual figure
# ============================================================

def prepare_swot_items(data, swot_label, max_items=8):
    temp = data[data["final_swot"] == swot_label]

    if temp.empty:
        return ["No items"]

    grouped = (
        temp.groupby("final_group")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    items = grouped["final_group"].head(max_items).tolist()

    return items


def plot_swot_picture(data):
    strengths = prepare_swot_items(data, "Strength")
    weaknesses = prepare_swot_items(data, "Weakness")
    opportunities = prepare_swot_items(data, "Opportunity")
    threats = prepare_swot_items(data, "Threat")

    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    boxes = [
        (0.3, 3.6, 4.5, 2.8, "Strengths", "S", strengths, "#cfeaf2"),
        (5.2, 3.6, 4.5, 2.8, "Weaknesses", "W", weaknesses, "#ffd8b5"),
        (0.3, 0.5, 4.5, 2.8, "Opportunities", "O", opportunities, "#d9edc2"),
        (5.2, 0.5, 4.5, 2.8, "Threats", "T", threats, "#f6b9b1"),
    ]

    for x, y, w, h, title, letter, items, color in boxes:
        box = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.35",
            linewidth=0,
            facecolor=color,
            alpha=0.95
        )
        ax.add_patch(box)

        ax.text(
            x + 0.35,
            y + h - 0.45,
            title,
            fontsize=21,
            fontweight="bold",
            ha="left",
            va="center"
        )

        ax.text(
            x + w - 0.7,
            y + h / 2,
            letter,
            fontsize=36,
            fontweight="bold",
            ha="center",
            va="center",
            alpha=0.7
        )

        text_y = y + h - 0.9

        for item in items:
            ax.text(
                x + 0.35,
                text_y,
                f"• {item}",
                fontsize=12,
                ha="left",
                va="top",
                wrap=True
            )
            text_y -= 0.34

    ax.add_patch(Circle((5.0, 3.5), 0.95, color="#90aeb8", alpha=0.35))
    ax.add_patch(Circle((5.0, 3.5), 0.45, color="#6f8f96", alpha=0.40))

    ax.set_title(
        "Final SWOT Results after Expert Review",
        fontsize=24,
        fontweight="bold",
        pad=20
    )

    plt.tight_layout()
    return fig


st.header("3. Automatically Updated SWOT Figure")

fig = plot_swot_picture(edited_df)
st.pyplot(fig, use_container_width=True)


# ============================================================
# 12. Downloads
# ============================================================

st.header("4. Downloads")

excel_buffer = BytesIO()

with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    edited_df.to_excel(writer, sheet_name="Reviewed answers", index=False)
    summary_swot.to_excel(writer, sheet_name="Summary SWOT", index=False)
    summary_group.to_excel(writer, sheet_name="Summary Groups", index=False)

excel_buffer.seek(0)

st.download_button(
    label="Download reviewed Excel file",
    data=excel_buffer,
    file_name="swot_reviewed_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

png_buffer = BytesIO()
fig.savefig(png_buffer, format="png", dpi=300, bbox_inches="tight")
png_buffer.seek(0)

st.download_button(
    label="Download final SWOT figure as PNG",
    data=png_buffer,
    file_name="final_swot_figure.png",
    mime="image/png"
)

pdf_buffer = BytesIO()
fig.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
pdf_buffer.seek(0)

st.download_button(
    label="Download final SWOT figure as PDF",
    data=pdf_buffer,
    file_name="final_swot_figure.pdf",
    mime="application/pdf"
)


# ============================================================
# 13. Help section
# ============================================================

with st.expander("How to use this dashboard"):
    st.markdown(
        """
        1. Upload an Excel or CSV file with one column named **answer**.
        2. The app suggests:
           - SWOT category
           - thematic group
           - confidence score
        3. Experts can modify:
           - **Final SWOT**
           - **Final group**
           - **Expert comment**
        4. To add a new group:
           - write the new group in the box above the table
           - click **Add group**
           - the group will appear in the **Final group** dropdown
        5. The expert table is sorted by **Final SWOT**, then **Final group**.
        6. The summary tables are sorted by highest frequency.
        7. The SWOT figure updates automatically and displays only group names.
        8. Download the reviewed Excel file and the final SWOT figure.
        """
    )


# In[ ]:




