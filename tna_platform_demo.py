import streamlit as st
import sqlite3
import json
from datetime import datetime
import pandas as pd

DB_NAME = "tna_demo.db"

USJ_BLUE = "#001F5B"
USJ_RED = "#8B1538"
USJ_GOLD = "#C9A227"
USJ_TEXT = "#1B2A41"

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
    "PSG001": {"role": "psg", "name": "Mohamad Khalil", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service des Études", "director_code": "DD001"},
    "PSG002": {"role": "psg", "name": "Rana Nader", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service des Études", "director_code": "DD001"},
    "PSG003": {"role": "psg", "name": "Karim Haddad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Informatique", "director_code": "DD001"},
    "PSG004": {"role": "psg", "name": "Maya Saad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Informatique", "director_code": "DD001"},
    "PSG005": {"role": "psg", "name": "Georges Khoury", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Service Administratif", "director_code": "DD001"},
    "PSG006": {"role": "psg", "name": "Nadine Abi Rached", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Secrétariat académique", "director_code": "DD002"},
    "PSG007": {"role": "psg", "name": "Paul Tannous", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Laboratoire", "director_code": "DD002"},
    "DD001": {"role": "director", "name": "Dr. Rami Haddad", "faculty": "Faculté des Sciences", "institution": "USJ", "department": "Direction"},
    "DD002": {"role": "director", "name": "Dr. Carla Mansour", "faculty": "Faculté de Médecine", "institution": "USJ", "department": "Direction"},
    "ADMIN2032": {"role": "admin", "name": "Administrateur TNA", "faculty": "USJ", "institution": "USJ", "department": "Administration Centrale"}
}


def apply_style():
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #F7FAFE 0%, #EEF3F9 100%);
        color: {USJ_TEXT};
    }}

    .block-container {{
        padding-top: 1.2rem;
        max-width: 1280px;
    }}

    h1, h2, h3 {{
        color: {USJ_BLUE};
        font-weight: 800;
    }}

    .main-hero {{
        background: linear-gradient(135deg, {USJ_BLUE} 0%, #123E7C 60%, {USJ_RED} 100%);
        border-radius: 24px;
        padding: 30px 34px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 18px 45px rgba(0,31,91,0.18);
    }}

    .hero-kicker {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.85;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .hero-title {{
        font-size: 2.25rem;
        line-height: 1.1;
        font-weight: 850;
        margin-bottom: 10px;
    }}

    .hero-subtitle {{
        font-size: 1.02rem;
        line-height: 1.55;
        opacity: 0.95;
    }}

    div[data-baseweb="input"] {{
        background-color: #ffffff !important;
        border: 2px solid {USJ_BLUE} !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 14px rgba(0,31,91,0.10) !important;
    }}

    div[data-baseweb="input"]:focus-within {{
        border: 3px solid {USJ_RED} !important;
        box-shadow: 0 0 0 4px rgba(139,21,56,0.12) !important;
    }}

    div[data-baseweb="input"] input {{
        background-color: #ffffff !important;
        color: {USJ_BLUE} !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        padding: 14px !important;
    }}

    label {{
        color: {USJ_BLUE} !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }}

    .identity-card {{
        background:#ffffff;
        border: 1px solid #DDE5F0;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 28px rgba(27,42,65,0.06);
        min-height: 112px;
    }}

    .identity-label {{
        color:#6B7688;
        font-size: 0.84rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .identity-value {{
        color:{USJ_TEXT};
        font-size: 1.35rem;
        font-weight: 750;
        line-height: 1.2;
    }}

    .section-card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:20px;
        padding:22px 24px;
        margin: 18px 0;
        box-shadow: 0 12px 32px rgba(27,42,65,0.07);
    }}

    .blue {{ border-top: 5px solid {USJ_BLUE}; }}
    .red {{ border-top: 5px solid {USJ_RED}; }}
    .gold {{ border-top: 5px solid {USJ_GOLD}; }}

    .step-title {{
        color:{USJ_BLUE};
        font-weight: 820;
        font-size: 1.18rem;
        margin-bottom: 8px;
    }}

    .step-help {{
        color:#5D697A;
        font-size:0.94rem;
    }}

    .card {{
        background:#ffffff;
        border:1px solid #DDE5F0;
        border-radius:16px;
        padding:18px 20px;
        margin-bottom:16px;
        box-shadow:0 8px 22px rgba(27,42,65,0.06);
    }}

    .blue-card {{ border-left:6px solid {USJ_BLUE}; }}
    .red-card {{ border-left:6px solid {USJ_RED}; }}
    .gold-card {{ border-left:6px solid {USJ_GOLD}; }}

    .pill {{
        display:inline-block;
        padding:8px 12px;
        margin:4px 5px 4px 0;
        border-radius:999px;
        background:#EAF2F8;
        color:{USJ_BLUE};
        font-weight:700;
        font-size:14px;
    }}

    .pill-red {{ background:#F8EDEF; color:{USJ_RED}; }}
    .pill-gold {{ background:#FFF8DF; color:#735C00; }}
    .matched {{ background:#E9F7EF; color:#146C43; }}
    .missing {{ background:#FFF3CD; color:#7A5A00; }}
    .final {{ background:#EAF2F8; color:{USJ_BLUE}; border:1px solid #C9DDF2; }}

    div.stButton > button {{
        border-radius:12px;
        background:{USJ_BLUE};
        color:white;
        border:0;
        font-weight:800;
        min-height: 46px;
    }}

    div.stButton > button:hover {{
        background:#123E7C;
        color:white;
        border:0;
    }}
    </style>
    """, unsafe_allow_html=True)


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
            respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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


def load_responses():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT respondent_code, role, name, faculty, institution, department, data_json, submitted_at
        FROM responses
        ORDER BY submitted_at DESC
    """).fetchall()
    conn.close()

    records = []
    for row in rows:
        code, role, name, faculty, institution, department, data_json, submitted_at = row
        try:
            data = json.loads(data_json)
        except Exception:
            data = {}

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

    return pd.DataFrame(records)


def get_employees_for_director(director_code):
    employees = []

    for code, info in DEMO_USERS.items():
        if info.get("role") == "psg" and info.get("director_code") == director_code:
            emp = info.copy()
            emp["code"] = code
            employees.append(emp)

    return employees


def unique_ranked_select(label, options, key_prefix):
    st.markdown(f"**{label}**")

    c1, c2, c3 = st.columns(3)

    with c1:
        p1 = st.selectbox("Priorité 1", [""] + options, key=f"{key_prefix}_p1")

    with c2:
        remaining2 = [x for x in options if x != p1]
        p2 = st.selectbox("Priorité 2", [""] + remaining2, key=f"{key_prefix}_p2")

    with c3:
        remaining3 = [x for x in options if x not in [p1, p2]]
        p3 = st.selectbox("Priorité 3", [""] + remaining3, key=f"{key_prefix}_p3")

    return [x for x in [p1, p2, p3] if x]


def weighted_score(theme, employee_ranked, director_ranked):
    score = 0
    weights = {0: 3, 1: 2, 2: 1}

    for i, theme_selected in enumerate(employee_ranked):
        if theme_selected == theme:
            score += weights.get(i, 0)

    for i, theme_selected in enumerate(director_ranked):
        if theme_selected == theme:
            score += weights.get(i, 0)

    return score


def calculate_final_themes(employee_ranked, director_ranked):
    employee_ranked = employee_ranked or []
    director_ranked = director_ranked or []

    matched = [theme for theme in employee_ranked if theme in director_ranked]
    candidates = list(dict.fromkeys(employee_ranked + director_ranked))

    ranked_candidates = sorted(
        candidates,
        key=lambda theme: (
            theme not in matched,
            -weighted_score(theme, employee_ranked, director_ranked),
            candidates.index(theme)
        )
    )

    final = ranked_candidates[:3]

    if len(matched) >= 3:
        scenario = "Accord complet : les 3 thèmes sont communs entre l’employé et le directeur."
    elif len(matched) == 2:
        scenario = "Accord fort : 2 thèmes sont communs. Le 3e thème est proposé selon le score de priorité."
    elif len(matched) == 1:
        scenario = "Accord partiel : 1 thème est commun. Les 2 autres thèmes sont proposés selon le score de priorité."
    else:
        scenario = "Aucun thème commun : la sélection finale est proposée selon les priorités croisées."

    return matched, final, scenario


def login_page():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026</div>
        <div class="hero-title">Plateforme d’analyse des besoins en formation</div>
        <div class="hero-subtitle">Accès sécurisé au questionnaire PSG, au questionnaire Doyens / Directeurs et au tableau de bord administrateur.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
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

        st.caption("Codes demo : PSG001, DD001, DD002, ADMIN2032")


def render_form_hero(profile_label, title, objective):
    st.markdown(f"""
    <div class="main-hero">
        <div class="hero-kicker">TNA 2026 | {profile_label}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{objective}</div>
    </div>
    """, unsafe_allow_html=True)


def render_identity_cards(user):
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Nom</div>
            <div class="identity-value">{user['name']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Faculté / Institution</div>
            <div class="identity-value">{user['faculty']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="identity-card">
            <div class="identity-label">Département</div>
            <div class="identity-value">{user['department']}</div>
        </div>
        """, unsafe_allow_html=True)


def render_ranked_section_header(title, help_text, color_class="blue"):
    st.markdown(f"""
    <div class="section-card {color_class}">
        <div class="step-title">{title}</div>
        <div class="step-help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_theme_pills(themes, css_class="pill"):
    if not themes:
        st.caption("Aucun thème sélectionné.")
        return

    html = "".join([
        f"<span class='{css_class}'>{i}. {theme}</span>"
        for i, theme in enumerate(themes, start=1)
    ])

    st.markdown(html, unsafe_allow_html=True)


def render_psg_form(user):
    render_form_hero(
        "Personnel de soutien et de gestion",
        "Questionnaire d’analyse des besoins en formation - PSG",
        "Ce court questionnaire nous aide à comprendre vos besoins en formation. Les résultats seront utilisés pour concevoir des programmes de formation qui soutiennent votre travail, améliorent vos compétences et favorisent votre développement professionnel."
    )

    render_identity_cards(user)

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "Classement des thèmes prioritaires",
        "Veuillez choisir exactement 3 thèmes, dans l’ordre d’importance. La priorité 1 correspond au besoin le plus important.",
        "blue"
    )

    ranked_themes = unique_ranked_select(
        "Vos 3 thèmes de formation prioritaires :",
        PSG_THEMES,
        "psg_ranked"
    )

    other_themes = st.text_area(
        "Autre(s) thème(s) ou sujet(s) de formation proposés",
        key="psg_other",
        placeholder="Indiquez ici un thème non présent dans la liste, si nécessaire."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(ranked_themes) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes classés par ordre de priorité.")
            return

        data = {
            "ranked_themes": ranked_themes,
            "selected_themes": ranked_themes,
            "other_themes": other_themes,
            "director_code": user.get("director_code", "")
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def render_director_form(user):
    render_form_hero(
        "Doyens et Directeurs",
        "Questionnaire d’analyse des besoins en formation - Doyens et Directeurs",
        "Ce questionnaire vise à identifier vos besoins en formation en tant que leader ainsi que les besoins de développement de votre département. Les résultats nous aideront à concevoir des programmes de formation qui soutiennent le leadership, améliorent la performance des équipes et s’alignent sur les objectifs de l’université."
    )

    render_identity_cards(user)

    st.markdown("<br>", unsafe_allow_html=True)

    render_ranked_section_header(
        "A. Vos besoins de formation en tant que leader",
        "Veuillez choisir exactement 3 thématiques, dans l’ordre d’importance pour votre rôle de direction.",
        "red"
    )

    leader_ranked = unique_ranked_select(
        "Vos 3 thématiques prioritaires :",
        DD_LEADER_THEMES,
        "leader_ranked"
    )

    leader_other = st.text_area(
        "Autre(s) thème(s) proposés pour vous-même",
        key="leader_other",
        placeholder="Indiquez ici un thème de leadership non présent dans la liste, si nécessaire."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    employees = get_employees_for_director(st.session_state["code"])

    render_ranked_section_header(
        "B. Besoins de formation de vos employés",
        f"{len(employees)} employé(s) lié(s) à votre compte. Pour chaque employé, veuillez classer exactement 3 thèmes prioritaires.",
        "gold"
    )

    employee_training_needs = []

    for emp in employees:
        with st.expander(f"{emp['name']} | {emp['department']}", expanded=True):
            st.markdown(
                f"<span class='pill'>Code : {emp['code']}</span><span class='pill pill-gold'>{emp['department']}</span>",
                unsafe_allow_html=True
            )

            emp_ranked = unique_ranked_select(
                f"Classement des 3 thèmes prioritaires pour {emp['name']} :",
                PSG_THEMES,
                f"director_emp_{emp['code']}"
            )

            emp_other = st.text_area(
                f"Autre(s) besoin(s) spécifique(s) pour {emp['name']}",
                key=f"other_{emp['code']}",
                placeholder="Indiquez ici un besoin particulier, si nécessaire."
            )

            employee_training_needs.append({
                "employee_code": emp["code"],
                "employee_name": emp["name"],
                "employee_department": emp["department"],
                "ranked_themes_by_director": emp_ranked,
                "selected_themes": emp_ranked,
                "other_themes": emp_other
            })

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Soumettre mes réponses", use_container_width=True):
        if len(leader_ranked) != 3:
            st.warning("Veuillez sélectionner exactement 3 thèmes pour vous-même.")
            return

        incomplete = [
            emp["employee_name"]
            for emp in employee_training_needs
            if len(emp["ranked_themes_by_director"]) != 3
        ]

        if incomplete:
            st.warning("Veuillez sélectionner exactement 3 thèmes pour chaque employé : " + ", ".join(incomplete))
            return

        data = {
            "leader_ranked_themes": leader_ranked,
            "leader_selected_themes": leader_ranked,
            "leader_other_themes": leader_other,
            "employees_training_needs": employee_training_needs
        }

        save_response(user, data)
        st.success("Vos réponses ont été enregistrées avec succès.")


def latest_by_code(df, code):
    if df.empty:
        return None

    subset = df[df["Code"] == code].sort_values("Date", ascending=False)

    if subset.empty:
        return None

    return subset.iloc[0].to_dict()


def render_admin_dashboard():
    st.markdown("""
    <div class="main-hero">
        <div class="hero-kicker">Administration | TNA 2026</div>
        <div class="hero-title">Tableau de bord administrateur</div>
        <div class="hero-subtitle">Analyse des besoins de formation des PSG et des Doyens / Directeurs, avec comparaison employé-directeur et proposition des 3 thèmes finaux.</div>
    </div>
    """, unsafe_allow_html=True)

    df = load_responses()

    if df.empty:
        st.info("Aucune réponse enregistrée pour le moment.")
        return

    with st.sidebar:
        st.header("Filtres administrateur")

        view = st.selectbox(
            "Vue à afficher",
            [
                "Synthèse directeur-employés",
                "Réponses PSG",
                "Réponses Doyens / Directeurs",
                "Départements",
                "Base de données"
            ]
        )

        profiles = ["Tous"] + sorted(df["Profil"].unique().tolist())
        selected_profile = st.selectbox("Profil", profiles)

        faculties = ["Toutes"] + sorted(df["Faculté"].unique().tolist())
        selected_faculty = st.selectbox("Faculté / institution", faculties)

        departments = ["Tous"] + sorted(df["Département"].unique().tolist())
        selected_department = st.selectbox("Département", departments)

    filtered = df.copy()

    if selected_profile != "Tous":
        filtered = filtered[filtered["Profil"] == selected_profile]

    if selected_faculty != "Toutes":
        filtered = filtered[filtered["Faculté"] == selected_faculty]

    if selected_department != "Tous":
        filtered = filtered[filtered["Département"] == selected_department]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Réponses", len(filtered))
    k2.metric("PSG", len(filtered[filtered["Profil"] == "psg"]))
    k3.metric("Doyens / Directeurs", len(filtered[filtered["Profil"] == "director"]))
    k4.metric("Départements", filtered["Département"].nunique())

    st.divider()

    if view == "Synthèse directeur-employés":
        directors = [
            code for code, user in DEMO_USERS.items()
            if user.get("role") == "director"
        ]

        director_labels = {
            code: f"{DEMO_USERS[code]['name']} | {DEMO_USERS[code]['faculty']}"
            for code in directors
        }

        selected_director = st.selectbox(
            "Sélectionner un Doyen / Directeur",
            directors,
            format_func=lambda x: director_labels[x]
        )

        director_user = DEMO_USERS[selected_director]
        director_response = latest_by_code(df, selected_director)

        st.markdown("### 1. Besoins sélectionnés par le Doyen / Directeur pour lui-même")

        st.markdown(f"""
        <div class='card red-card'>
            <b>{director_user['name']}</b><br>
            {director_user['faculty']} | {director_user['department']}
        </div>
        """, unsafe_allow_html=True)

        if director_response:
            leader_themes = director_response["Données"].get(
                "leader_ranked_themes",
                director_response["Données"].get("leader_selected_themes", [])
            )
            render_theme_pills(leader_themes, "pill pill-red")
        else:
            st.warning("Ce directeur n’a pas encore soumis ses réponses.")

        st.divider()

        st.markdown("### 2. Analyse visuelle par employé")

        employees = get_employees_for_director(selected_director)

        director_emp_map = {}

        if director_response:
            for item in director_response["Données"].get("employees_training_needs", []):
                director_emp_map[item.get("employee_code")] = item

        for emp in employees:
            emp_response = latest_by_code(df, emp["code"])

            employee_ranked = []
            if emp_response:
                employee_ranked = emp_response["Données"].get(
                    "ranked_themes",
                    emp_response["Données"].get("selected_themes", [])
                )

            director_ranked = []
            if emp["code"] in director_emp_map:
                director_ranked = director_emp_map[emp["code"]].get(
                    "ranked_themes_by_director",
                    director_emp_map[emp["code"]].get("selected_themes", [])
                )

            matched, final, scenario = calculate_final_themes(employee_ranked, director_ranked)

            st.markdown(f"""
            <div class='card blue-card'>
                <h3 style='margin-top:0;'>{emp['name']}</h3>
                <span class='pill'>Code : {emp['code']}</span>
                <span class='pill pill-gold'>{emp['department']}</span>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("#### Choix de l’employé")
                render_theme_pills(employee_ranked, "pill")

            with c2:
                st.markdown("#### Choix du directeur")
                render_theme_pills(director_ranked, "pill pill-red")

            with c3:
                st.markdown("#### Thèmes proposés")
                render_theme_pills(final, "pill final")

            if matched:
                st.markdown("**Thèmes en commun :**")
                render_theme_pills(matched, "pill matched")
            else:
                st.markdown("<span class='pill missing'>Aucun thème commun</span>", unsafe_allow_html=True)

            st.info(scenario)
            st.divider()

    elif view == "Réponses PSG":
        st.markdown("### Réponses PSG")

        psg_df = filtered[filtered["Profil"] == "psg"].copy()

        if psg_df.empty:
            st.info("Aucune réponse PSG dans les filtres sélectionnés.")
        else:
            for _, row in psg_df.iterrows():
                themes = row["Données"].get(
                    "ranked_themes",
                    row["Données"].get("selected_themes", [])
                )

                st.markdown(f"""
                <div class='card blue-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Département']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                render_theme_pills(themes, "pill")

    elif view == "Réponses Doyens / Directeurs":
        st.markdown("### Réponses Doyens / Directeurs")

        dd_df = filtered[filtered["Profil"] == "director"].copy()

        if dd_df.empty:
            st.info("Aucune réponse Doyen / Directeur dans les filtres sélectionnés.")
        else:
            for _, row in dd_df.iterrows():
                data = row["Données"]

                st.markdown(f"""
                <div class='card red-card'>
                    <b>{row['Nom']}</b><br>
                    {row['Faculté']} | {row['Département']} | {row['Date']}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Thèmes sélectionnés pour lui-même :**")
                render_theme_pills(
                    data.get("leader_ranked_themes", data.get("leader_selected_themes", [])),
                    "pill pill-red"
                )

                st.markdown("**Thèmes sélectionnés pour les employés :**")

                for emp in data.get("employees_training_needs", []):
                    st.markdown(f"""
                    <div class='card'>
                        <b>{emp.get('employee_name')}</b> | {emp.get('employee_department')}
                    </div>
                    """, unsafe_allow_html=True)

                    render_theme_pills(
                        emp.get("ranked_themes_by_director", emp.get("selected_themes", [])),
                        "pill"
                    )

    elif view == "Départements":
        st.markdown("### Analyse par département")

        theme_rows = []

        for _, row in filtered.iterrows():
            data = row["Données"]

            if row["Profil"] == "psg":
                for theme in data.get("ranked_themes", data.get("selected_themes", [])):
                    theme_rows.append({
                        "Département": row["Département"],
                        "Source": "PSG",
                        "Thème": theme
                    })

            elif row["Profil"] == "director":
                for emp in data.get("employees_training_needs", []):
                    for theme in emp.get("ranked_themes_by_director", emp.get("selected_themes", [])):
                        theme_rows.append({
                            "Département": emp.get("employee_department"),
                            "Source": "Directeur pour employé",
                            "Thème": theme
                        })

        if not theme_rows:
            st.info("Aucune donnée disponible.")
        else:
            theme_df = pd.DataFrame(theme_rows)

            dept = st.selectbox(
                "Choisir un département",
                sorted(theme_df["Département"].dropna().unique())
            )

            sub = theme_df[theme_df["Département"] == dept]

            counts = sub["Thème"].value_counts().reset_index()
            counts.columns = ["Thème", "Nombre"]

            st.bar_chart(counts.set_index("Thème"), use_container_width=True)
            st.dataframe(sub, use_container_width=True, hide_index=True)

    elif view == "Base de données":
        st.markdown("### Base de données filtrée")

        st.dataframe(
            filtered.drop(columns=["Données"]),
            use_container_width=True,
            hide_index=True
        )

        export_df = filtered.drop(columns=["Données"])

        st.download_button(
            "Télécharger CSV",
            export_df.to_csv(index=False).encode("utf-8-sig"),
            "tna_reponses.csv",
            "text/csv"
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

    if user["role"] == "psg":
        render_psg_form(user)

    elif user["role"] == "director":
        render_director_form(user)

    elif user["role"] == "admin":
        render_admin_dashboard()


if __name__ == "__main__":
    main()
