import streamlit as st
import sqlite3
import json
from datetime import datetime
from collections import Counter

import pandas as pd


DB_NAME = "tna_demo.db"


PSG_THEMES = [
    "Communication constructive",
    "Résolution de conflits",
    "Intelligence interpersonnelle",
    "Diversité culturelle",
    "Collaboration",
    "Communication écrite",
    "Communication orale",
    "Public speaking and Body language",
    "Santé mentale",
    "Bien-être au travail",
    "Intelligence émotionnelle",
    "Gestion du stress",
    "Gestion du temps",
    "Mindfulness",
    "Team building",
    "Inclusion",
    "Harcèlement",
    "Branding",
    "Création de contenu-Réseaux sociaux",
    "Outils intelligence artificielle",
    "Bureautique-Word",
    "Bureautique-Excel",
    "Bureautique-PowerPoint",
    "Gestion financière",
    "Esprit critique et résolution de problèmes",
    "Gestion du changement en milieu universitaire",
    "Gestion de projets",
    "Équilibre vie professionnelle vie personnelle",
    "Ergonomie",
    "Customer service"
]


DD_LEADER_THEMES = [
    "Outils intelligence artificielle-IA",
    "Agile management",
    "Strategic decision making",
    "Gestion budgétaire",
    "Gestion financière",
    "Digital marketing",
    "Change management in academic institutions",
    "Crisis management and institutional resilience",
    "Data-driven decision making"
]


DEMO_USERS = {
    "PSG001": {
        "role": "psg",
        "name": "Mohamad Khalil",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Service des Études",
        "director_code": "DD001"
    },
    "PSG002": {
        "role": "psg",
        "name": "Rana Nader",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Service des Études",
        "director_code": "DD001"
    },
    "PSG003": {
        "role": "psg",
        "name": "Karim Haddad",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Service Informatique",
        "director_code": "DD001"
    },
    "PSG004": {
        "role": "psg",
        "name": "Maya Saad",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Service Informatique",
        "director_code": "DD001"
    },
    "PSG005": {
        "role": "psg",
        "name": "Georges Khoury",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Service Administratif",
        "director_code": "DD001"
    },
    "PSG006": {
        "role": "psg",
        "name": "Nadine Abi Rached",
        "faculty": "Faculté de Médecine",
        "institution": "USJ",
        "department": "Secrétariat académique",
        "director_code": "DD002"
    },
    "PSG007": {
        "role": "psg",
        "name": "Paul Tannous",
        "faculty": "Faculté de Médecine",
        "institution": "USJ",
        "department": "Laboratoire",
        "director_code": "DD002"
    },
    "DD001": {
        "role": "director",
        "name": "Dr. Rami Haddad",
        "faculty": "Faculté des Sciences",
        "institution": "USJ",
        "department": "Direction"
    },
    "DD002": {
        "role": "director",
        "name": "Dr. Carla Mansour",
        "faculty": "Faculté de Médecine",
        "institution": "USJ",
        "department": "Direction"
    },
    "ADMIN2032": {
        "role": "admin",
        "name": "Administrateur TNA",
        "faculty": "USJ",
        "institution": "USJ",
        "department": "Administration Centrale"
    }
}


USJ_BLUE = "#001F5B"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_LIGHT_BLUE = "#EAF2F8"
USJ_TEXT = "#1B2A41"


def apply_style():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #F7F9FC;
            color: {USJ_TEXT};
            font-family: Candara, Arial, sans-serif;
        }}
        h1, h2, h3 {{
            color: {USJ_BLUE};
            font-family: Candara, Arial, sans-serif;
        }}
        div[data-testid="stMetric"] {{
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        div[data-testid="stExpander"] {{
            background: white;
            border-radius: 12px;
        }}
        .block-container {{
            padding-top: 2rem;
        }}
        .info-card {{
            background: white;
            border-left: 6px solid {USJ_BLUE};
            border-radius: 14px;
            padding: 18px 22px;
            margin-bottom: 18px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .theme-pill {{
            background: {USJ_LIGHT_BLUE};
            border: 1px solid #D7E3F2;
            color: {USJ_BLUE};
            border-radius: 999px;
            padding: 7px 12px;
            display: inline-block;
            margin: 4px 5px 4px 0;
            font-weight: 600;
        }}
        .employee-card {{
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respondent_code TEXT,
            role TEXT,
            name TEXT,
            faculty TEXT,
            institution TEXT,
            department TEXT,
            data_json TEXT,
            submitted_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_response(user, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO responses (
            respondent_code, role, name, faculty, institution,
            department, data_json, submitted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            st.session_state["code"],
            user["role"],
            user["name"],
            user["faculty"],
            user["institution"],
            user["department"],
            json.dumps(data, ensure_ascii=False),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()
    conn.close()


def get_employees_for_director(director_code):
    employees = []
    for code, info in DEMO_USERS.items():
        if info.get("role") == "psg" and info.get("director_code") == director_code:
            emp = info.copy()
            emp["code"] = code
            employees.append(emp)
    return employees


def read_all_responses():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        """
        SELECT respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        FROM responses
        ORDER BY submitted_at DESC
        """
    ).fetchall()
    conn.close()
    return rows


def login_page():
    st.markdown(
        f"""
        <div class="info-card">
            <h1 style="margin-bottom:0;">Plateforme d’analyse des besoins en formation</h1>
            <p style="font-size:18px; margin-top:6px; color:{USJ_TEXT};">
                Training Needs Assessment - TNA 2026
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("### Connexion")
        code = st.text_input("Code d’accès", type="password")
        if st.button("Accéder au questionnaire", use_container_width=True):
            cleaned_code = code.strip().upper()
            if cleaned_code in DEMO_USERS:
                st.session_state["logged_in"] = True
                st.session_state["code"] = cleaned_code
                st.session_state["user"] = DEMO_USERS[cleaned_code]
                st.rerun()
            else:
                st.error("Code non reconnu.")

        st.caption("Codes démo : PSG001, DD001, DD002, ADMIN2032")


def render_user_identity(user):
    cols = st.columns(3)
    cols[0].markdown(f"**Nom**  \\n{user['name']}")
    cols[1].markdown(f"**Faculté / Institution**  \\n{user['faculty']}")
    cols[2].markdown(f"**Département**  \\n{user['department']}")


def render_theme_pills(themes):
    if not themes:
        st.caption("Aucun thème sélectionné.")
        return
    html = "".join([f'<span class="theme-pill">{theme}</span>' for theme in themes])
    st.markdown(html, unsafe_allow_html=True)


def render_psg_form(user):
    st.title("Questionnaire d’analyse des besoins en formation - PSG")
    st.info(
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. Les résultats seront utilisés "
        "pour concevoir des programmes de formation qui soutiennent votre travail, améliorent vos compétences "
        "et favorisent votre développement professionnel."
    )
    render_user_identity(user)
    st.divider()

    selected_themes = st.multiselect(
        "1- Veuillez sélectionner jusqu’à 3 thèmes de formation prioritaires :",
        PSG_THEMES,
        max_selections=3,
        key="psg_selected_themes"
    )
    other_themes = st.text_area(
        "2- Quel(s) autre(s) thème(s) ou sujet(s) de formation proposez-vous ?",
        key="psg_other_themes"
    )

    st.markdown("#### Aperçu de votre sélection")
    render_theme_pills(selected_themes)

    if st.button("Soumettre mes réponses", type="primary"):
        if len(selected_themes) == 0:
            st.warning("Veuillez sélectionner au moins un thème.")
            return
        data = {
            "selected_themes": selected_themes,
            "other_themes": other_themes
        }
        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def render_director_form(user):
    st.title("Questionnaire d’analyse des besoins en formation - Doyens et Directeurs")
    st.info(
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader ainsi que les besoins "
        "de développement de votre département. Les résultats nous aideront à concevoir des programmes de "
        "formation qui soutiennent le leadership, améliorent la performance des équipes et s’alignent sur les "
        "objectifs de l’université."
    )
    render_user_identity(user)
    st.divider()

    st.subheader("A. Vos besoins de formation en tant que leader")
    leader_themes = st.multiselect(
        "1- Veuillez sélectionner jusqu’à 3 thématiques auxquelles vous souhaitez participer :",
        DD_LEADER_THEMES,
        max_selections=3,
        key="leader_themes"
    )
    leader_other = st.text_area(
        "2- Quel(s) autre(s) thème(s) ou sujet(s) de formation proposez-vous pour vous-même ?",
        key="leader_other"
    )

    st.markdown("#### Aperçu des thèmes sélectionnés pour vous")
    render_theme_pills(leader_themes)

    st.divider()
    st.subheader("B. Besoins de formation de vos employés")

    employees = get_employees_for_director(st.session_state["code"])
    if not employees:
        st.warning("Aucun employé n’est actuellement lié à ce compte directeur.")
    else:
        st.info(
            f"{len(employees)} employé(s) sont liés à votre compte. "
            "Veuillez sélectionner jusqu’à 3 thèmes prioritaires pour chaque employé."
        )

    employee_training_needs = []
    for emp in employees:
        with st.expander(f"{emp['name']} | {emp['department']}", expanded=True):
            col_info, col_select = st.columns([1, 2])
            with col_info:
                st.markdown(
                    f"""
                    <div class="employee-card">
                        <b>{emp['name']}</b><br>
                        Code : <b>{emp['code']}</b><br>
                        Département : {emp['department']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_select:
                selected_emp_themes = st.multiselect(
                    f"Thèmes prioritaires pour {emp['name']} :",
                    PSG_THEMES,
                    max_selections=3,
                    key=f"themes_{emp['code']}"
                )
                other_emp_themes = st.text_area(
                    f"Autre(s) besoin(s) spécifique(s) pour {emp['name']} :",
                    key=f"other_{emp['code']}"
                )
                render_theme_pills(selected_emp_themes)

            employee_training_needs.append({
                "employee_code": emp["code"],
                "employee_name": emp["name"],
                "employee_department": emp["department"],
                "selected_themes": selected_emp_themes,
                "other_themes": other_emp_themes
            })

    st.divider()
    if st.button("Soumettre mes réponses", type="primary"):
        if len(leader_themes) == 0:
            st.warning("Veuillez sélectionner au moins un thème pour vous-même.")
            return

        incomplete_employees = [
            emp["employee_name"]
            for emp in employee_training_needs
            if len(emp["selected_themes"]) == 0
        ]
        if incomplete_employees:
            st.warning(
                "Veuillez sélectionner au moins un thème pour chaque employé. Employés incomplets : "
                + ", ".join(incomplete_employees)
            )
            return

        data = {
            "leader_selected_themes": leader_themes,
            "leader_other_themes": leader_other,
            "employees_training_needs": employee_training_needs
        }
        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def build_admin_dataframes(rows):
    records = []
    theme_rows = []
    employee_priority_rows = []

    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row
        data = json.loads(data_json)
        records.append({
            "Code": code,
            "Profil": role,
            "Nom": name,
            "Faculté": faculty,
            "Institution": institution,
            "Département": department,
            "Date": submitted_at,
            "Données": data
        })

        if role == "psg":
            for theme in data.get("selected_themes", []):
                theme_rows.append({
                    "Source": "Choix PSG",
                    "Code": code,
                    "Nom": name,
                    "Faculté": faculty,
                    "Département": department,
                    "Thème": theme
                })
                employee_priority_rows.append({
                    "Employee Code": code,
                    "Employee Name": name,
                    "Faculty": faculty,
                    "Department": department,
                    "Theme": theme,
                    "Source": "Employee",
                    "Weight": 1
                })

        if role == "director":
            for theme in data.get("leader_selected_themes", []):
                theme_rows.append({
                    "Source": "Choix leader",
                    "Code": code,
                    "Nom": name,
                    "Faculté": faculty,
                    "Département": department,
                    "Thème": theme
                })
            for emp in data.get("employees_training_needs", []):
                for theme in emp.get("selected_themes", []):
                    theme_rows.append({
                        "Source": "Choix directeur pour employé",
                        "Code": emp.get("employee_code", ""),
                        "Nom": emp.get("employee_name", ""),
                        "Faculté": faculty,
                        "Département": emp.get("employee_department", ""),
                        "Thème": theme
                    })
                    employee_priority_rows.append({
                        "Employee Code": emp.get("employee_code", ""),
                        "Employee Name": emp.get("employee_name", ""),
                        "Faculty": faculty,
                        "Department": emp.get("employee_department", ""),
                        "Theme": theme,
                        "Source": "Director",
                        "Weight": 2
                    })

    responses_df = pd.DataFrame(records)
    themes_df = pd.DataFrame(theme_rows)
    priorities_df = pd.DataFrame(employee_priority_rows)
    return responses_df, themes_df, priorities_df


def calculate_top3_by_employee(priorities_df):
    if priorities_df.empty:
        return pd.DataFrame()
    grouped = (
        priorities_df.groupby(["Employee Code", "Employee Name", "Faculty", "Department", "Theme"], as_index=False)["Weight"]
        .sum()
        .sort_values(["Employee Code", "Weight", "Theme"], ascending=[True, False, True])
    )
    grouped["Rank"] = grouped.groupby("Employee Code")["Weight"].rank(method="first", ascending=False).astype(int)
    return grouped[grouped["Rank"] <= 3]


def render_admin_dashboard():
    st.title("Tableau de bord administrateur - TNA 2026")
    st.caption("Vue dynamique des réponses collectées auprès des PSG, Doyens et Directeurs")

    rows = read_all_responses()
    if not rows:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    responses_df, themes_df, priorities_df = build_admin_dataframes(rows)

    st.markdown("### Synthèse générale")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Réponses totales", len(responses_df))
    col2.metric("Réponses PSG", len(responses_df[responses_df["Profil"] == "psg"]))
    col3.metric("Réponses Doyens / Directeurs", len(responses_df[responses_df["Profil"] == "director"]))
    col4.metric("Facultés / Institutions", responses_df["Faculté"].nunique())

    st.divider()
    st.markdown("### Filtres dynamiques")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        selected_profile = st.multiselect(
            "Filtrer par profil",
            sorted(responses_df["Profil"].unique()),
            default=sorted(responses_df["Profil"].unique())
        )
    with col_f2:
        selected_faculty = st.multiselect(
            "Filtrer par faculté / institution",
            sorted(responses_df["Faculté"].unique()),
            default=sorted(responses_df["Faculté"].unique())
        )
    with col_f3:
        selected_department = st.multiselect(
            "Filtrer par département",
            sorted(responses_df["Département"].unique()),
            default=sorted(responses_df["Département"].unique())
        )

    filtered_df = responses_df[
        responses_df["Profil"].isin(selected_profile)
        & responses_df["Faculté"].isin(selected_faculty)
        & responses_df["Département"].isin(selected_department)
    ]

    st.divider()
    st.markdown("### Tableau des répondants")
    display_df = filtered_df.drop(columns=["Données"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if themes_df.empty:
        st.info("Aucun thème sélectionné dans les réponses filtrées.")
        return

    filtered_themes_df = themes_df[
        themes_df["Faculté"].isin(selected_faculty)
        & themes_df["Département"].isin(selected_department)
    ]

    st.divider()
    st.markdown("### Analyse des thèmes sélectionnés")
    tab1, tab2, tab3, tab4 = st.tabs([
        "Top thèmes",
        "Par source",
        "Priorités par employé",
        "Détails des réponses"
    ])

    with tab1:
        top_themes = filtered_themes_df["Thème"].value_counts().reset_index()
        top_themes.columns = ["Thème", "Nombre de sélections"]
        st.bar_chart(top_themes.set_index("Thème"), use_container_width=True)
        st.dataframe(top_themes, use_container_width=True, hide_index=True)

    with tab2:
        source_count = filtered_themes_df["Source"].value_counts().reset_index()
        source_count.columns = ["Source", "Nombre"]
        st.bar_chart(source_count.set_index("Source"), use_container_width=True)
        st.dataframe(filtered_themes_df, use_container_width=True, hide_index=True)

    with tab3:
        top3_df = calculate_top3_by_employee(priorities_df)
        if top3_df.empty:
            st.info("Aucune priorité par employé disponible.")
        else:
            st.info(
                "Formule démo : sélection employé = 1 point, sélection directeur = 2 points. "
                "Les 3 thèmes ayant le score le plus élevé sont retenus pour chaque employé."
            )
            st.dataframe(top3_df, use_container_width=True, hide_index=True)

    with tab4:
        for _, row in filtered_df.iterrows():
            data = row["Données"]
            with st.expander(f"{row['Nom']} | {row['Profil']} | {row['Faculté']} | {row['Date']}"):
                col_info, col_response = st.columns([1, 2])
                with col_info:
                    st.markdown("#### Informations")
                    st.markdown(f"**Code :** {row['Code']}")
                    st.markdown(f"**Profil :** {row['Profil']}")
                    st.markdown(f"**Faculté :** {row['Faculté']}")
                    st.markdown(f"**Institution :** {row['Institution']}")
                    st.markdown(f"**Département :** {row['Département']}")
                    st.markdown(f"**Date :** {row['Date']}")
                with col_response:
                    if row["Profil"] == "psg":
                        st.markdown("#### Besoins de formation PSG")
                        render_theme_pills(data.get("selected_themes", []))
                        if data.get("other_themes"):
                            st.markdown("**Autres propositions :**")
                            st.info(data.get("other_themes"))
                    elif row["Profil"] == "director":
                        st.markdown("#### Besoins du leader")
                        render_theme_pills(data.get("leader_selected_themes", []))
                        if data.get("leader_other_themes"):
                            st.markdown("**Autres propositions pour le leader :**")
                            st.info(data.get("leader_other_themes"))

                        st.markdown("#### Besoins des employés liés")
                        for emp in data.get("employees_training_needs", []):
                            with st.container(border=True):
                                st.markdown(
                                    f"**{emp.get('employee_name', '')}**  \\n"
                                    f"Code : `{emp.get('employee_code', '')}`  \\n"
                                    f"Département : {emp.get('employee_department', '')}"
                                )
                                render_theme_pills(emp.get("selected_themes", []))
                                if emp.get("other_themes"):
                                    st.caption(f"Autre besoin : {emp.get('other_themes')}")

    st.divider()
    st.markdown("### Export des données")
    csv_respondents = display_df.to_csv(index=False).encode("utf-8-sig")
    csv_themes = filtered_themes_df.to_csv(index=False).encode("utf-8-sig")

    col_export1, col_export2 = st.columns(2)
    with col_export1:
        st.download_button(
            label="Télécharger les répondants CSV",
            data=csv_respondents,
            file_name="tna_repondants.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_export2:
        st.download_button(
            label="Télécharger les thèmes CSV",
            data=csv_themes,
            file_name="tna_themes.csv",
            mime="text/csv",
            use_container_width=True
        )


def main():
    st.set_page_config(
        page_title="TNA 2026",
        page_icon="📘",
        layout="wide"
    )
    apply_style()
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    user = st.session_state["user"]
    col1, col2 = st.columns([4, 1])
    with col1:
        st.caption(f"Connecté : {user['name']}")
    with col2:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if user["role"] == "psg":
        render_psg_form(user)
    elif user["role"] == "director":
        render_director_form(user)
    elif user["role"] == "admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()
