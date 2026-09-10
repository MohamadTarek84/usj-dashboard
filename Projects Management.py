from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
import os
import sqlite3

import bcrypt
import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------------------------------------------------------
# Database, authentication, calculations, exports, and business logic
# Everything is kept in this one script so it can be uploaded directly.
# -----------------------------------------------------------------------------

DB_PATH = Path(os.getenv("PROJECTFLOW_DB_PATH", Path(__file__).resolve().parent / "data" / "project_manager.db"))


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with connection() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE COLLATE NOCASE NOT NULL,
          full_name TEXT NOT NULL, email TEXT, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('owner','coordinator')), active INTEGER DEFAULT 1,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS projects(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '',
          category TEXT DEFAULT 'Other', priority TEXT DEFAULT 'Medium', status TEXT DEFAULT 'Not started',
          start_date TEXT, due_date TEXT, owner_id INTEGER NOT NULL, coordinator_id INTEGER,
          manual_progress REAL, alert_days INTEGER DEFAULT 7, color TEXT DEFAULT '#1F4E78',
          archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(owner_id) REFERENCES users(id),
          FOREIGN KEY(coordinator_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, title TEXT NOT NULL,
          description TEXT DEFAULT '', assignee_id INTEGER, status TEXT DEFAULT 'Not started',
          priority TEXT DEFAULT 'Medium', start_date TEXT, due_date TEXT, completed_at TEXT,
          weight REAL DEFAULT 1 CHECK(weight>0), estimated_hours REAL DEFAULT 0,
          actual_hours REAL DEFAULT 0, dependency_task_id INTEGER,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(assignee_id) REFERENCES users(id),
          FOREIGN KEY(dependency_task_id) REFERENCES tasks(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS milestones(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, title TEXT NOT NULL,
          due_date TEXT NOT NULL, completed INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS comments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL, task_id INTEGER,
          user_id INTEGER NOT NULL, body TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
          FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS activity_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, user_id INTEGER,
          action TEXT NOT NULL, details TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(user_id) REFERENCES users(id));
        CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date,status);
        CREATE INDEX IF NOT EXISTS idx_projects_due ON projects(due_date,status);
        """)


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    with connection() as con:
        cur = con.execute(sql, tuple(params))
        return int(cur.lastrowid or 0)


def query(sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with connection() as con:
        return [dict(row) for row in con.execute(sql, tuple(params)).fetchall()]


def scalar(sql: str, params: Iterable[Any] = ()) -> Any:
    with connection() as con:
        row = con.execute(sql, tuple(params)).fetchone()
        return row[0] if row else None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except (ValueError, TypeError):
        return False


def create_user(username: str, full_name: str, email: str, password: str, role: str) -> int:
    if len(username.strip()) < 3:
        raise ValueError("Username must contain at least 3 characters.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    if role not in {"owner", "coordinator"}:
        raise ValueError("Invalid role.")
    return execute("INSERT INTO users(username,full_name,email,password_hash,role) VALUES(?,?,?,?,?)",
                   (username.strip(), full_name.strip(), email.strip(), hash_password(password), role))


def authenticate(username: str, password: str):
    rows = query("SELECT * FROM users WHERE username=? AND active=1", (username.strip(),))
    if rows and verify_password(password, rows[0]["password_hash"]):
        user = rows[0]
        user.pop("password_hash", None)
        return user
    return None


def change_password(user_id: int, current: str, new: str) -> None:
    rows = query("SELECT password_hash FROM users WHERE id=?", (user_id,))
    if not rows or not verify_password(current, rows[0]["password_hash"]):
        raise ValueError("The current password is incorrect.")
    if len(new) < 8:
        raise ValueError("The new password must contain at least 8 characters.")
    execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(new), user_id))


def log_activity(user_id: int | None, action: str, details: str = "", project_id: int | None = None) -> None:
    execute("INSERT INTO activity_log(project_id,user_id,action,details) VALUES(?,?,?,?)",
            (project_id, user_id, action, details))


def project_progress(project_id: int) -> float:
    project = query("SELECT manual_progress FROM projects WHERE id=?", (project_id,))
    if not project:
        return 0.0
    if project[0]["manual_progress"] is not None:
        return float(project[0]["manual_progress"])
    rows = query("SELECT status,weight FROM tasks WHERE project_id=? AND status<>'Cancelled'", (project_id,))
    total = sum(float(r["weight"]) for r in rows)
    completed = sum(float(r["weight"]) for r in rows if r["status"] == "Completed")
    return round(completed / total * 100, 1) if total else 0.0


def visible_projects(user: dict[str, Any], include_archived: bool = False) -> list[dict[str, Any]]:
    archive = "" if include_archived else "AND p.archived=0"
    visibility = "p.owner_id=?" if user["role"] == "owner" else "p.coordinator_id=?"
    rows = query(f"""SELECT p.*,o.full_name owner_name,c.full_name coordinator_name
      FROM projects p JOIN users o ON o.id=p.owner_id LEFT JOIN users c ON c.id=p.coordinator_id
      WHERE {visibility} {archive}
      ORDER BY CASE p.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
      COALESCE(p.due_date,'9999-12-31')""", (user["id"],))
    for row in rows:
        row["progress"] = project_progress(row["id"])
    return rows


def due_alerts(user: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    today = date.today()
    for project in visible_projects(user):
        if project["status"] in {"Completed", "Cancelled"}:
            continue
        sources = []
        if project["due_date"]:
            sources.append(("Project", project["id"], project["name"], project["due_date"], project["priority"]))
        for task in query("SELECT * FROM tasks WHERE project_id=? AND due_date IS NOT NULL AND status NOT IN ('Completed','Cancelled')", (project["id"],)):
            sources.append(("Task", task["id"], task["title"], task["due_date"], task["priority"]))
        for milestone in query("SELECT * FROM milestones WHERE project_id=? AND completed=0", (project["id"],)):
            sources.append(("Milestone", milestone["id"], milestone["title"], milestone["due_date"], project["priority"]))
        for kind, item_id, item, due_text, priority in sources:
            due = date.fromisoformat(due_text)
            days = (due - today).days
            if days <= int(project["alert_days"]):
                alerts.append(dict(type=kind,id=item_id,project=project["name"],item=item,
                                   due_date=due,days=days,priority=priority))
    return sorted(alerts, key=lambda x: (x["days"], x["type"]))


def save_project(data: dict[str, Any], user_id: int, project_id: int | None = None) -> int:
    fields = ("name","description","category","priority","status","start_date","due_date",
              "coordinator_id","manual_progress","alert_days","color")
    values = [data.get(k) for k in fields]
    if project_id:
        execute(f"UPDATE projects SET {','.join(f'{f}=?' for f in fields)},updated_at=CURRENT_TIMESTAMP WHERE id=? AND owner_id=?",
                (*values, project_id, user_id))
        log_activity(user_id,"Updated project",data["name"],project_id)
        return project_id
    project_id = execute(f"INSERT INTO projects({','.join(fields)},owner_id) VALUES({','.join('?' for _ in fields)},?)",
                         (*values,user_id))
    log_activity(user_id,"Created project",data["name"],project_id)
    return project_id


def save_task(data: dict[str, Any], user_id: int, task_id: int | None = None) -> int:
    fields = ("project_id","title","description","assignee_id","status","priority","start_date",
              "due_date","weight","estimated_hours","actual_hours","dependency_task_id")
    values = [data.get(k) for k in fields]
    completed = datetime.now().isoformat(timespec="seconds") if data["status"] == "Completed" else None
    if task_id:
        execute(f"UPDATE tasks SET {','.join(f'{f}=?' for f in fields)},completed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (*values,completed,task_id))
        log_activity(user_id,"Updated task",data["title"],data["project_id"])
        return task_id
    task_id = execute(f"INSERT INTO tasks({','.join(fields)},completed_at) VALUES({','.join('?' for _ in fields)},?)",
                      (*values,completed))
    log_activity(user_id,"Created task",data["title"],data["project_id"])
    return task_id


def add_comment(project_id: int, task_id: int | None, user_id: int, body: str) -> None:
    execute("INSERT INTO comments(project_id,task_id,user_id,body) VALUES(?,?,?,?)",
            (project_id,task_id,user_id,body.strip()))
    log_activity(user_id,"Added comment",body.strip()[:120],project_id)


def project_export(project_ids: list[int]) -> bytes:
    placeholders = ",".join("?" for _ in project_ids)
    datasets = {
      "Projects": query(f"SELECT * FROM projects WHERE id IN ({placeholders})",project_ids),
      "Tasks": query(f"SELECT t.*,p.name project_name FROM tasks t JOIN projects p ON p.id=t.project_id WHERE t.project_id IN ({placeholders})",project_ids),
      "Milestones": query(f"SELECT m.*,p.name project_name FROM milestones m JOIN projects p ON p.id=m.project_id WHERE m.project_id IN ({placeholders})",project_ids),
      "Comments": query(f"SELECT c.*,p.name project_name,u.full_name author FROM comments c JOIN projects p ON p.id=c.project_id JOIN users u ON u.id=c.user_id WHERE c.project_id IN ({placeholders})",project_ids),
    }
    output = BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        for name,rows in datasets.items():
            pd.DataFrame(rows).to_excel(writer,sheet_name=name,index=False)
            ws=writer.book[name]; ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
            for column in ws.columns:
                ws.column_dimensions[column[0].column_letter].width=min(max(len(str(c.value or "")) for c in column)+2,45)
    return output.getvalue()


def status_label(days: int) -> str:
    return f"Overdue by {abs(days)} day(s)" if days < 0 else "Due today" if days == 0 else f"Due in {days} day(s)"


def gantt_data(project_ids: list[int]) -> pd.DataFrame:
    if not project_ids:
        return pd.DataFrame()
    placeholders=",".join("?" for _ in project_ids)
    return pd.DataFrame(query(f"""SELECT t.title Task,p.name Project,t.start_date Start,t.due_date Finish,t.status Status
      FROM tasks t JOIN projects p ON p.id=t.project_id WHERE t.project_id IN ({placeholders})
      AND t.start_date IS NOT NULL AND t.due_date IS NOT NULL""",project_ids))


def parse_date(value: str | None, fallback: date | None = None) -> date:
    return date.fromisoformat(value) if value else fallback or date.today()


def seed_demo_data(owner_id: int) -> None:
    if scalar("SELECT COUNT(*) FROM projects WHERE owner_id=?",(owner_id,)):
        return
    today=date.today()
    pid=execute("""INSERT INTO projects(name,description,category,priority,status,start_date,due_date,owner_id,alert_days,color)
      VALUES(?,?,?,?,?,?,?,?,?,?)""",("Annual Institutional Report","Prepare, validate, and submit the annual report.",
      "Reporting","High","In progress",str(today-timedelta(days=10)),str(today+timedelta(days=30)),owner_id,10,"#1F4E78"))
    previous=None
    for title,status,due,weight in [
      ("Collect faculty data","Completed",today-timedelta(days=5),2),
      ("Validate indicators","In progress",today+timedelta(days=7),3),
      ("Draft analytical narrative","Not started",today+timedelta(days=18),2),
      ("Final review and submission","Not started",today+timedelta(days=30),3)]:
        previous=execute("""INSERT INTO tasks(project_id,title,status,priority,start_date,due_date,completed_at,
          weight,estimated_hours,dependency_task_id) VALUES(?,?,?,?,?,?,?,?,?,?)""",
          (pid,title,status,"High",str(today),str(due),datetime.now().isoformat(timespec="seconds") if status=="Completed" else None,weight,8,previous))
    execute("INSERT INTO milestones(project_id,title,due_date) VALUES(?,?,?)",(pid,"Report approved",str(today+timedelta(days=27))))
    log_activity(owner_id,"Created demo project","Sample data generated",pid)


st.set_page_config(page_title="ProjectFlow Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
init_db()

PROJECT_STATUSES = ["Not started", "In progress", "On hold", "Completed", "Cancelled"]
TASK_STATUSES = ["Not started", "In progress", "Blocked", "Completed", "Cancelled"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

st.markdown(
    """
    <style>
      .stApp {background: #f5f7fb;}
      [data-testid="stSidebar"] {background: linear-gradient(180deg,#102a43,#163f63);}
      [data-testid="stSidebar"] * {color: white;}
      .hero {padding:1.25rem 1.5rem;border-radius:16px;background:linear-gradient(110deg,#123b5d,#1f6b8c);color:white;margin-bottom:1rem;box-shadow:0 8px 24px #102a4324;}
      .hero h1 {margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;opacity:.88}
      .card {background:white;border:1px solid #e5eaf0;border-radius:14px;padding:1rem;box-shadow:0 3px 12px #102a430d;margin:.3rem 0;}
      .badge {display:inline-block;padding:.2rem .55rem;border-radius:999px;background:#e8f1f8;color:#174a6e;font-size:.8rem;font-weight:600}
      .danger {color:#b42318;font-weight:700}.warning {color:#b54708;font-weight:700}.good{color:#027a48;font-weight:700}
      div[data-testid="stMetric"] {background:white;border:1px solid #e5eaf0;padding:.9rem;border-radius:12px;}
      .small-muted {font-size:.85rem;color:#667085}
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def logout() -> None:
    st.session_state.pop("user", None)
    st.rerun()


def setup_or_login() -> None:
    user_count = int(scalar("SELECT COUNT(*) FROM users") or 0)
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.markdown("<br><br>", unsafe_allow_html=True)
        hero("ProjectFlow Pro", "Professional project, task, deadline, and collaboration management")
        if user_count == 0:
            st.info("Create the first owner account. You can add your coordinator later.")
            with st.form("initial_setup"):
                full_name = st.text_input("Full name")
                email = st.text_input("Email")
                username = st.text_input("Username")
                password = st.text_input("Password (minimum 8 characters)", type="password")
                confirm = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create account", width="stretch", type="primary")
            if submitted:
                if not full_name.strip():
                    st.error("Full name is required.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        create_user(username, full_name, email, password, "owner")
                        st.success("Account created. Please sign in.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        else:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", width="stretch", type="primary")
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                st.error("Incorrect username or password.")


if "user" not in st.session_state:
    setup_or_login()
    st.stop()

user = st.session_state.user
projects = visible_projects(user)
project_ids = [p["id"] for p in projects]

with st.sidebar:
    st.markdown(f"### ProjectFlow Pro\n**{user['full_name']}**  \n{user['role'].title()}")
    page_options = ["Dashboard", "Projects", "Tasks", "Timeline", "Alerts", "Reports"]
    if user["role"] == "owner":
        page_options.append("Administration")
    page = st.radio("Navigation", page_options, label_visibility="collapsed")
    st.divider()
    if st.button("Sign out", width="stretch"):
        logout()


def project_selector(label: str = "Project", key: str | None = None) -> int | None:
    if not projects:
        st.info("No project is available.")
        return None
    labels = {p["id"]: p["name"] for p in projects}
    return st.selectbox(label, list(labels), format_func=lambda x: labels[x], key=key)


def render_dashboard() -> None:
    hero("Dashboard", "A live overview of priorities, progress, risks, and upcoming deadlines")
    active = [p for p in projects if p["status"] not in {"Completed", "Cancelled"}]
    completed = [p for p in projects if p["status"] == "Completed"]
    overdue = [a for a in due_alerts(user) if a["days"] < 0]
    avg_progress = sum(p["progress"] for p in active) / len(active) if active else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active projects", len(active))
    c2.metric("Average progress", f"{avg_progress:.0f}%")
    c3.metric("Completed", len(completed))
    c4.metric("Overdue items", len(overdue), delta=f"{len(overdue)} need attention" if overdue else "On track", delta_color="inverse")

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Project portfolio")
        if not projects:
            st.info("Create your first project from the Projects page.")
        for p in projects[:8]:
            due = p["due_date"] or "No deadline"
            st.markdown(
                f'<div class="card"><span class="badge">{p["category"]}</span> '
                f'<b>{p["name"]}</b><br><span class="small-muted">{p["status"]} · {p["priority"]} priority · Due {due}</span></div>',
                unsafe_allow_html=True,
            )
            st.progress(float(p["progress"]) / 100, text=f"{p['progress']:.0f}% complete")
    with right:
        st.subheader("Upcoming attention")
        alerts = due_alerts(user)[:8]
        if not alerts:
            st.success("No approaching or overdue deadlines.")
        for alert in alerts:
            css = "danger" if alert["days"] < 0 else "warning" if alert["days"] <= 3 else ""
            st.markdown(
                f'<div class="card"><b>{alert["item"]}</b><br><span class="small-muted">{alert["project"]} · {alert["type"]}</span><br>'
                f'<span class="{css}">{status_label(alert["days"])}</span></div>', unsafe_allow_html=True,
            )

    if projects:
        st.subheader("Portfolio analysis")
        chart1, chart2 = st.columns(2)
        df = pd.DataFrame(projects)
        with chart1:
            counts = df.groupby("status", as_index=False).size()
            fig = px.bar(counts, x="status", y="size", color="status", title="Projects by status", text="size")
            fig.update_layout(showlegend=False, height=330, margin=dict(l=10,r=10,t=50,b=10))
            st.plotly_chart(fig, width="stretch")
        with chart2:
            fig = px.bar(df, x="progress", y="name", orientation="h", color="priority", title="Progress by project",
                         color_discrete_map={"Critical":"#b42318","High":"#f79009","Medium":"#2e90fa","Low":"#12b76a"})
            fig.update_layout(height=330, margin=dict(l=10,r=10,t=50,b=10), xaxis_range=[0,100])
            st.plotly_chart(fig, width="stretch")


def project_form(existing: dict | None = None) -> None:
    coordinators = query("SELECT id,full_name FROM users WHERE role='coordinator' AND active=1 ORDER BY full_name")
    coord_map = {None: "Not shared"} | {x["id"]: x["full_name"] for x in coordinators}
    default_status = existing["status"] if existing else "Not started"
    default_priority = existing["priority"] if existing else "Medium"
    with st.form("project_form"):
        name = st.text_input("Project name *", value=existing["name"] if existing else "")
        description = st.text_area("Purpose and expected outputs", value=existing["description"] if existing else "", height=100)
        c1, c2, c3 = st.columns(3)
        category = c1.text_input("Category", value=existing["category"] if existing else "Reporting")
        priority = c2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(default_priority))
        status = c3.selectbox("Status", PROJECT_STATUSES, index=PROJECT_STATUSES.index(default_status))
        d1, d2, d3 = st.columns(3)
        start_date = d1.date_input("Start date", value=parse_date(existing.get("start_date") if existing else None))
        due_date = d2.date_input("Submission date", value=parse_date(existing.get("due_date") if existing else None, date.today()+timedelta(days=30)))
        alert_days = d3.number_input("Alert before deadline (days)", 0, 365, int(existing["alert_days"] if existing else 7))
        s1, s2, s3 = st.columns(3)
        current_coord = existing.get("coordinator_id") if existing else None
        coord_keys = list(coord_map)
        coordinator_id = s1.selectbox("Share with coordinator", coord_keys, index=coord_keys.index(current_coord) if current_coord in coord_keys else 0, format_func=lambda x: coord_map[x])
        mode = s2.selectbox("Progress calculation", ["Automatic from tasks", "Manual"], index=1 if existing and existing["manual_progress"] is not None else 0)
        manual = s3.slider("Manual progress (%)", 0, 100, int(existing["manual_progress"] or 0) if existing else 0, disabled=mode.startswith("Automatic"))
        color = st.color_picker("Project colour", value=existing["color"] if existing else "#1F4E78")
        submitted = st.form_submit_button("Save project", type="primary", width="stretch")
    if submitted:
        if not name.strip():
            st.error("Project name is required.")
        elif due_date < start_date:
            st.error("The submission date cannot be before the start date.")
        else:
            data = dict(name=name.strip(), description=description.strip(), category=category.strip() or "Other",
                        priority=priority, status=status, start_date=str(start_date), due_date=str(due_date),
                        coordinator_id=coordinator_id, manual_progress=None if mode.startswith("Automatic") else manual,
                        alert_days=alert_days, color=color)
            save_project(data, user["id"], existing["id"] if existing else None)
            st.success("Project saved.")
            st.rerun()


def render_projects() -> None:
    hero("Projects", "Create, prioritize, share, and review every project in one place")
    if user["role"] == "owner":
        tab1, tab2 = st.tabs(["Project list", "Create project"])
    else:
        tab1, = st.tabs(["Shared projects"])
        tab2 = None
    with tab1:
        if not projects:
            st.info("No projects found.")
        filters = st.columns([1,1,1.5])
        status_filter = filters[0].multiselect("Status", PROJECT_STATUSES)
        priority_filter = filters[1].multiselect("Priority", PRIORITIES)
        search = filters[2].text_input("Search")
        shown = [p for p in projects if (not status_filter or p["status"] in status_filter)
                 and (not priority_filter or p["priority"] in priority_filter)
                 and (not search or search.lower() in (p["name"]+p["description"]+p["category"]).lower())]
        for p in shown:
            with st.expander(f"{p['name']}  ·  {p['progress']:.0f}%  ·  {p['status']}"):
                a, b, c, d = st.columns(4)
                a.metric("Progress", f"{p['progress']:.0f}%")
                b.metric("Priority", p["priority"])
                c.metric("Submission", p["due_date"] or "—")
                d.metric("Coordinator", p["coordinator_name"] or "Not shared")
                st.write(p["description"] or "No description.")
                if user["role"] == "owner":
                    if st.button("Edit project", key=f"editp{p['id']}"):
                        st.session_state.edit_project = p["id"]
                    if st.session_state.get("edit_project") == p["id"]:
                        project_form(p)
    if tab2:
        with tab2:
            project_form()


def task_form(project_id: int, existing: dict | None = None) -> None:
    members = query(
        """SELECT u.id,u.full_name FROM users u JOIN projects p ON (u.id=p.owner_id OR u.id=p.coordinator_id)
           WHERE p.id=? AND u.active=1""", (project_id,)
    )
    member_map = {None: "Unassigned"} | {m["id"]:m["full_name"] for m in members}
    dependencies = query("SELECT id,title FROM tasks WHERE project_id=? AND id<>? ORDER BY title", (project_id, existing["id"] if existing else -1))
    dep_map = {None:"No dependency"} | {d["id"]:d["title"] for d in dependencies}
    default_status = existing["status"] if existing else "Not started"
    default_priority = existing["priority"] if existing else "Medium"
    with st.form(f"task_form_{project_id}_{existing['id'] if existing else 'new'}"):
        title = st.text_input("Task title *", value=existing["title"] if existing else "")
        description = st.text_area("Description / definition of done", value=existing["description"] if existing else "")
        c1,c2,c3 = st.columns(3)
        status = c1.selectbox("Status", TASK_STATUSES, index=TASK_STATUSES.index(default_status))
        priority = c2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(default_priority))
        assignee_keys = list(member_map)
        old_assignee = existing.get("assignee_id") if existing else None
        assignee = c3.selectbox("Assignee", assignee_keys, index=assignee_keys.index(old_assignee) if old_assignee in assignee_keys else 0, format_func=lambda x:member_map[x])
        d1,d2,d3 = st.columns(3)
        start = d1.date_input("Start", value=parse_date(existing.get("start_date") if existing else None), key=f"ts{project_id}{existing['id'] if existing else 0}")
        due = d2.date_input("Due", value=parse_date(existing.get("due_date") if existing else None, date.today()+timedelta(days=7)), key=f"td{project_id}{existing['id'] if existing else 0}")
        weight = d3.number_input("Progress weight", .1, 100.0, float(existing["weight"] if existing else 1), .5)
        h1,h2,h3 = st.columns(3)
        estimated = h1.number_input("Estimated hours", 0.0, 10000.0, float(existing["estimated_hours"] if existing else 0), .5)
        actual = h2.number_input("Actual hours", 0.0, 10000.0, float(existing["actual_hours"] if existing else 0), .5)
        dep_keys = list(dep_map)
        old_dep = existing.get("dependency_task_id") if existing else None
        dependency = h3.selectbox("Depends on", dep_keys, index=dep_keys.index(old_dep) if old_dep in dep_keys else 0, format_func=lambda x:dep_map[x])
        submitted = st.form_submit_button("Save task", type="primary")
    if submitted:
        if not title.strip():
            st.error("Task title is required.")
        elif due < start:
            st.error("Due date cannot be before start date.")
        else:
            save_task(dict(project_id=project_id,title=title.strip(),description=description.strip(),assignee_id=assignee,
                           status=status,priority=priority,start_date=str(start),due_date=str(due),weight=weight,
                           estimated_hours=estimated,actual_hours=actual,dependency_task_id=dependency),
                      user["id"], existing["id"] if existing else None)
            st.success("Task saved.")
            st.rerun()


def render_tasks() -> None:
    hero("Tasks", "Plan deliverables, assign responsibility, record effort, and manage dependencies")
    project_id = project_selector(key="task_project")
    if not project_id:
        return
    p = next(x for x in projects if x["id"] == project_id)
    tasks = query("""SELECT t.*,u.full_name assignee,d.title dependency FROM tasks t
                     LEFT JOIN users u ON u.id=t.assignee_id LEFT JOIN tasks d ON d.id=t.dependency_task_id
                     WHERE t.project_id=? ORDER BY COALESCE(t.due_date,'9999-12-31')""", (project_id,))
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    c1,c2,c3 = st.columns(3)
    c1.metric("Project progress", f"{project_progress(project_id):.0f}%")
    c2.metric("Tasks", len(tasks))
    c3.metric("Completed tasks", completed)
    if user["role"] == "owner":
        tabs = st.tabs(["Task board", "Add task", "Milestones", "Discussion"])
    else:
        tabs = st.tabs(["Task board", "Milestones", "Discussion"])
    with tabs[0]:
        status_filter = st.multiselect("Filter task status", TASK_STATUSES)
        shown = [t for t in tasks if not status_filter or t["status"] in status_filter]
        if not shown:
            st.info("No tasks match the selection.")
        for t in shown:
            overdue = t["due_date"] and date.fromisoformat(t["due_date"]) < date.today() and t["status"] not in {"Completed","Cancelled"}
            with st.expander(f"{'🔴 ' if overdue else ''}{t['title']}  ·  {t['status']}  ·  Due {t['due_date'] or '—'}"):
                st.write(t["description"] or "No description.")
                st.caption(f"Assignee: {t['assignee'] or 'Unassigned'} · Priority: {t['priority']} · Weight: {t['weight']} · Dependency: {t['dependency'] or 'None'}")
                st.caption(f"Estimated: {t['estimated_hours']} h · Actual: {t['actual_hours']} h")
                can_edit = user["role"] == "owner" or t["assignee_id"] == user["id"]
                if can_edit and st.button("Edit", key=f"editt{t['id']}"):
                    st.session_state.edit_task = t["id"]
                if can_edit and st.session_state.get("edit_task") == t["id"]:
                    task_form(project_id, t)
    if user["role"] == "owner":
        with tabs[1]:
            task_form(project_id)
        milestone_tab = tabs[2]
        discussion_tab = tabs[3]
    else:
        milestone_tab = tabs[1]
        discussion_tab = tabs[2]
    with milestone_tab:
        milestones = query("SELECT * FROM milestones WHERE project_id=? ORDER BY due_date", (project_id,))
        if user["role"] == "owner":
            with st.form("milestone_form"):
                mc1, mc2 = st.columns([2, 1])
                milestone_title = mc1.text_input("Milestone title")
                milestone_due = mc2.date_input("Milestone date", value=date.today()+timedelta(days=14))
                add_milestone = st.form_submit_button("Add milestone")
            if add_milestone and milestone_title.strip():
                execute("INSERT INTO milestones(project_id,title,due_date) VALUES(?,?,?)",
                        (project_id, milestone_title.strip(), str(milestone_due)))
                log_activity(user["id"], "Created milestone", milestone_title.strip(), project_id)
                st.rerun()
        if not milestones:
            st.info("No milestones have been added.")
        for milestone in milestones:
            m1, m2, m3 = st.columns([3, 1.2, 1])
            m1.write(f"**{'✅' if milestone['completed'] else '◇'} {milestone['title']}**")
            m2.write(milestone["due_date"])
            if user["role"] == "owner":
                label = "Reopen" if milestone["completed"] else "Complete"
                if m3.button(label, key=f"milestone{milestone['id']}"):
                    execute("UPDATE milestones SET completed=? WHERE id=?",
                            (0 if milestone["completed"] else 1, milestone["id"]))
                    log_activity(user["id"], f"{label}d milestone", milestone["title"], project_id)
                    st.rerun()
    with discussion_tab:
        comments = query("""SELECT c.*,u.full_name author,t.title task_title FROM comments c
                            JOIN users u ON u.id=c.user_id LEFT JOIN tasks t ON t.id=c.task_id
                            WHERE c.project_id=? ORDER BY c.created_at DESC""", (project_id,))
        task_map = {None:"Project-level comment"} | {t["id"]:t["title"] for t in tasks}
        with st.form("comment"):
            target = st.selectbox("Related to", list(task_map), format_func=lambda x:task_map[x])
            body = st.text_area("Comment")
            post = st.form_submit_button("Post comment")
        if post and body.strip():
            add_comment(project_id, target, user["id"], body)
            st.rerun()
        for comment in comments:
            st.markdown(f"**{comment['author']}** · {comment['created_at']}  ")
            st.write(comment["body"])
            st.caption(comment["task_title"] or p["name"])
            st.divider()


def render_timeline() -> None:
    hero("Timeline", "See project schedules and task overlaps in an interactive Gantt chart")
    if not projects:
        st.info("No project data to display.")
        return
    selected = st.multiselect("Projects", project_ids, default=project_ids, format_func=lambda x:next(p["name"] for p in projects if p["id"]==x))
    df = gantt_data(selected)
    if df.empty:
        st.info("Add task start and due dates to build the timeline.")
        return
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Status", hover_data=["Project"])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(420, 36*len(df)), margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, width="stretch")


def render_alerts() -> None:
    hero("Deadline alerts", "Prioritized reminders based on each project's alert window")
    alerts = due_alerts(user)
    if not alerts:
        st.success("Everything is on schedule. There are no active alerts.")
        return
    overdue = [a for a in alerts if a["days"] < 0]
    today_items = [a for a in alerts if a["days"] == 0]
    upcoming = [a for a in alerts if a["days"] > 0]
    c1,c2,c3 = st.columns(3)
    c1.metric("Overdue",len(overdue)); c2.metric("Due today",len(today_items)); c3.metric("Upcoming",len(upcoming))
    for title, group in (("Overdue",overdue),("Due today",today_items),("Upcoming",upcoming)):
        st.subheader(title)
        if not group:
            st.caption("None")
        for a in group:
            st.markdown(f'<div class="card"><b>{a["item"]}</b> · {a["type"]}<br><span class="small-muted">{a["project"]} · {a["due_date"]} · {a["priority"]}</span><br><span class="{"danger" if a["days"]<0 else "warning"}">{status_label(a["days"])}</span></div>', unsafe_allow_html=True)
    st.info("In-app alerts appear whenever you open the dashboard. Optional scheduled email alerts are configured with notification_worker.py.")


def render_reports() -> None:
    hero("Reports & export", "Create a portable management workbook for meetings, follow-up, or archiving")
    if not projects:
        st.info("No projects to export.")
        return
    selected = st.multiselect("Projects to include", project_ids, default=project_ids, format_func=lambda x:next(p["name"] for p in projects if p["id"]==x))
    if selected:
        output = project_export(selected)
        st.download_button("Download complete Excel report", output, file_name=f"project_portfolio_{date.today()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    st.subheader("Activity history")
    placeholders = ",".join("?" for _ in project_ids)
    activity = query(f"""SELECT a.created_at,a.action,a.details,p.name project,u.full_name user
                         FROM activity_log a LEFT JOIN projects p ON p.id=a.project_id LEFT JOIN users u ON u.id=a.user_id
                         WHERE a.project_id IN ({placeholders}) OR (a.project_id IS NULL AND a.user_id=?)
                         ORDER BY a.created_at DESC LIMIT 250""", (*project_ids,user["id"]))
    st.dataframe(pd.DataFrame(activity), width="stretch", hide_index=True)


def render_admin() -> None:
    hero("Administration", "Manage coordinator access, sample data, security, and project records")
    t1,t2,t3,t4 = st.tabs(["Coordinator access","Account security","Data tools","Archive"])
    with t1:
        st.subheader("Create a coordinator account")
        st.caption("A coordinator sees only projects explicitly shared with their account.")
        with st.form("new_coordinator"):
            full_name=st.text_input("Coordinator name")
            email=st.text_input("Coordinator email")
            username=st.text_input("Coordinator username")
            password=st.text_input("Temporary password",type="password")
            submitted=st.form_submit_button("Create coordinator")
        if submitted:
            try:
                create_user(username,full_name,email,password,"coordinator")
                log_activity(user["id"],"Created coordinator",full_name)
                st.success("Coordinator account created. Share the username and temporary password securely.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        users=query("SELECT id,username,full_name,email,active FROM users WHERE role='coordinator' ORDER BY full_name")
        st.dataframe(pd.DataFrame(users), hide_index=True, width="stretch")
    with t2:
        with st.form("password_change"):
            current=st.text_input("Current password",type="password")
            new=st.text_input("New password",type="password")
            confirm=st.text_input("Confirm new password",type="password")
            submitted=st.form_submit_button("Change password")
        if submitted:
            if new!=confirm:
                st.error("New passwords do not match.")
            else:
                try:
                    change_password(user["id"],current,new); st.success("Password changed.")
                except Exception as exc: st.error(str(exc))
    with t3:
        st.write("Generate one realistic sample project to explore the dashboard immediately.")
        if st.button("Create sample project"):
            before=int(scalar("SELECT COUNT(*) FROM projects WHERE owner_id=?",(user["id"],)) or 0)
            seed_demo_data(user["id"])
            after=int(scalar("SELECT COUNT(*) FROM projects WHERE owner_id=?",(user["id"],)) or 0)
            st.success("Sample project created." if after>before else "Sample data was not added because projects already exist.")
            st.rerun()
    with t4:
        archived=visible_projects(user,include_archived=True)
        archived=[p for p in archived if p["archived"]]
        st.write("Archived projects remain in the database and can be restored.")
        for p in projects:
            if st.button(f"Archive · {p['name']}",key=f"archive{p['id']}"):
                execute("UPDATE projects SET archived=1 WHERE id=? AND owner_id=?",(p["id"],user["id"])); st.rerun()
        for p in archived:
            if st.button(f"Restore · {p['name']}",key=f"restore{p['id']}"):
                execute("UPDATE projects SET archived=0 WHERE id=? AND owner_id=?",(p["id"],user["id"])); st.rerun()


ROUTES = {
    "Dashboard": render_dashboard, "Projects": render_projects, "Tasks": render_tasks,
    "Timeline": render_timeline, "Alerts": render_alerts, "Reports": render_reports,
    "Administration": render_admin,
}
ROUTES[page]()
