# file: french_correction_admin.py

import streamlit as st
import pandas as pd
import language_tool_python
from io import BytesIO

SHEET_NAME = "All Answers"
LANGUAGE = "fr-FR"

st.set_page_config(
    page_title="French Correction Admin",
    layout="wide"
)

st.title("Correction orthographique - Français France")
st.caption("Upload the Excel file manually. Column F contains the original answers. The suggested corrections will be added in Column G.")

@st.cache_resource
def load_tool():
    return language_tool_python.LanguageTool(LANGUAGE)

def correct_french_text(text, tool):
    if pd.isna(text) or str(text).strip() == "":
        return "", []

    text = str(text)
    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)

    notes = []
    for match in matches:
        if match.replacements:
            error_text = text[match.offset:match.offset + match.errorLength]
            suggestions = ", ".join(match.replacements[:5])

            notes.append({
                "error": error_text,
                "suggestions": suggestions,
                "message": match.message
            })

    return corrected, notes

def build_notes(notes):
    if not notes:
        return ""

    return " | ".join(
        f"{note['error']} → {note['suggestions']} ({note['message']})"
        for note in notes
    )

def to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    return output.getvalue()

uploaded_file = st.file_uploader(
    "Upload Excel file",
    type=["xlsx"],
    help="Upload the Excel file: FGs All Answers 25-6-2026.xlsx"
)

if uploaded_file is None:
    st.info("Please upload the Excel file to start the French correction process.")
    st.stop()

df = pd.read_excel(uploaded_file, sheet_name=SHEET_NAME)

if df.shape[1] < 6:
    st.error("Column F was not found. The sheet must contain at least 6 columns.")
    st.stop()

answer_column = df.columns[5]

st.success(f"Loaded sheet: {SHEET_NAME}")
st.info(f"Answers detected in Column F: {answer_column}")

tool = load_tool()

file_signature = f"{uploaded_file.name}_{uploaded_file.size}"

if st.session_state.get("file_signature") != file_signature:
    keys_to_remove = [
        key for key in st.session_state.keys()
        if key.startswith("orig_")
        or key.startswith("sugg_")
        or key.startswith("decision_")
        or key in ["corrected_df", "file_signature"]
    ]

    for key in keys_to_remove:
        del st.session_state[key]

    st.session_state["file_signature"] = file_signature

if "corrected_df" not in st.session_state:
    with st.spinner("Checking French spelling and grammar using Français - France..."):
        corrected_values = []
        notes_values = []

        for text in df[answer_column]:
            corrected, notes = correct_french_text(text, tool)
            corrected_values.append(corrected)
            notes_values.append(build_notes(notes))

        df.insert(6, "Suggested_Correction", corrected_values)
        df.insert(7, "Admin_Decision", "Pending")
        df.insert(8, "Final_Answer", df[answer_column])
        df.insert(9, "Correction_Notes", notes_values)

        st.session_state["corrected_df"] = df

df_edit = st.session_state["corrected_df"]

st.markdown("## Admin validation")

total_rows = len(df_edit)
changed_rows = []

for i in range(total_rows):
    original = str(df_edit.loc[i, answer_column] or "")
    suggested = str(df_edit.loc[i, "Suggested_Correction"] or "")

    if original.strip() != suggested.strip():
        changed_rows.append(i)

st.write(f"Suggested corrections found: **{len(changed_rows)}** out of **{total_rows}** answers.")

if not changed_rows:
    st.success("No spelling or grammar correction was suggested.")

for i in changed_rows:
    original = str(df_edit.loc[i, answer_column] or "")
    suggested = str(df_edit.loc[i, "Suggested_Correction"] or "")

    with st.expander(f"Row {i + 2} - Correction suggested"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original answer**")
            st.text_area(
                "Original",
                value=original,
                height=180,
                disabled=True,
                key=f"orig_{i}",
                label_visibility="collapsed"
            )

        with col2:
            st.markdown("**Suggested correction**")
            edited_suggestion = st.text_area(
                "Suggested",
                value=suggested,
                height=180,
                key=f"sugg_{i}",
                label_visibility="collapsed"
            )

        st.markdown("**Detected issues**")
        st.caption(str(df_edit.loc[i, "Correction_Notes"] or ""))

        decision = st.radio(
            "Admin decision",
            ["Pending", "Accept correction", "Reject correction"],
            horizontal=True,
            key=f"decision_{i}"
        )

        df_edit.loc[i, "Admin_Decision"] = decision

        if decision == "Accept correction":
            df_edit.loc[i, "Suggested_Correction"] = edited_suggestion
            df_edit.loc[i, "Final_Answer"] = edited_suggestion
        elif decision == "Reject correction":
            df_edit.loc[i, "Final_Answer"] = original
        else:
            df_edit.loc[i, "Final_Answer"] = original

st.markdown("## Preview")

preview_columns = [
    answer_column,
    "Suggested_Correction",
    "Admin_Decision",
    "Final_Answer",
    "Correction_Notes"
]

st.dataframe(
    df_edit[preview_columns],
    use_container_width=True,
    height=500
)

excel_bytes = to_excel(df_edit)

st.download_button(
    "Download corrected Excel",
    data=excel_bytes,
    file_name="FGs_All_Answers_25-6-2026_Corrected_Admin.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
