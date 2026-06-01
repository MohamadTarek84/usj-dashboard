import streamlit as st
import sqlite3
import json
from datetime import datetime


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


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
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
    """)

    conn.commit()
    conn.close()


def save_response(user, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO responses (
            respondent_code,
            role,
            name,
            faculty,
            institution,
            department,
            data_json,
            submitted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        st.session_state["code"],
        user["role"],
        user["name"],
        user["faculty"],
        user["institution"],
        user["department"],
        json.dumps(data, ensure_ascii=False),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

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


def login_page():
    st.title("Plateforme d’analyse des besoins en formation")
    st.subheader("Training Needs Assessment - TNA 2026")

    code = st.text_input("Code d’accès", type="password")

    if st.button("Accéder au questionnaire"):
        cleaned_code = code.strip().upper()

        if cleaned_code in DEMO_USERS:
            st.session_state["logged_in"] = True
            st.session_state["code"] = cleaned_code
            st.session_state["user"] = DEMO_USERS[cleaned_code]
            st.rerun()
        else:
            st.error("Code non reconnu.")


def render_psg_form(user):
    st.title("Questionnaire d’analyse des besoins en formation - PSG")

    st.info(
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. "
        "Les résultats seront utilisés pour concevoir des programmes de formation qui soutiennent votre travail, "
        "améliorent vos compétences et favorisent votre développement professionnel."
    )

    st.markdown(f"**Nom :** {user['name']}")
    st.markdown(f"**Faculté / Institution :** {user['faculty']}")
    st.markdown(f"**Département :** {user['department']}")

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

    if st.button("Soumettre mes réponses"):
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
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader "
        "ainsi que les besoins de développement de votre département. Les résultats nous aideront "
        "à concevoir des programmes de formation qui soutiennent le leadership, améliorent la performance "
        "des équipes et s’alignent sur les objectifs de l’université."
    )

    st.markdown(f"**Nom :** {user['name']}")
    st.markdown(f"**Faculté / Institution :** {user['faculty']}")
    st.markdown(f"**Département :** {user['department']}")

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

    st.divider()

    st.subheader("B. Besoins de formation de vos employés")

    employees = get_employees_for_director(st.session_state["code"])

    if not employees:
        st.warning("Aucun employé n’est actuellement lié à ce compte directeur.")
    else:
        st.info(
            "Pour chaque employé lié à votre compte, veuillez sélectionner jusqu’à 3 thèmes de formation prioritaires."
        )

    employee_training_needs = []

    for emp in employees:
        with st.expander(f"{emp['name']} - {emp['department']}", expanded=True):
            st.markdown(f"**Code employé :** {emp['code']}")
            st.markdown(f"**Département :** {emp['department']}")

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

            employee_training_needs.append({
                "employee_code": emp["code"],
                "employee_name": emp["name"],
                "employee_department": emp["department"],
                "selected_themes": selected_emp_themes,
                "other_themes": other_emp_themes
            })

    st.divider()

    if st.button("Soumettre mes réponses"):
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
                "Veuillez sélectionner au moins un thème pour chaque employé. "
                "Employés incomplets : " + ", ".join(incomplete_employees)
            )
            return

        data = {
            "leader_selected_themes": leader_themes,
            "leader_other_themes": leader_other,
            "employees_training_needs": employee_training_needs
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def render_admin_dashboard():
    st.title("Tableau de bord administrateur - TNA 2026")

    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        FROM responses
        ORDER BY submitted_at DESC
    """).fetchall()
    conn.close()

    if not rows:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    st.success(f"Nombre total de réponses : {len(rows)}")

    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row
        data = json.loads(data_json)

        with st.expander(f"{name} - {role} - {submitted_at}"):
            st.write("Code :", code)
            st.write("Faculté :", faculty)
            st.write("Institution :", institution)
            st.write("Département :", department)
            st.json(data)


def main():
    st.set_page_config(
        page_title="TNA 2026",
        page_icon="📘",
        layout="wide"
    )

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
        if st.button("Déconnexion"):
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
