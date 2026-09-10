from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable
import os
import sqlite3

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
          user_id INTEGER NOT NULL, author_name TEXT DEFAULT '', body TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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
        comment_columns = {row[1] for row in con.execute("PRAGMA table_info(comments)").fetchall()}
        if "author_name" not in comment_columns:
            con.execute("ALTER TABLE comments ADD COLUMN author_name TEXT DEFAULT ''")


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
PROJECT_TEMPLATES = {
    "Blank project": {"category": "Other", "days": 30, "tasks": []},
    "Institutional report": {"category": "Reporting", "days": 30, "tasks": [
        "Confirm requirements", "Collect data", "Validate data", "Analyze results",
        "Draft report", "Internal review", "Final submission"]},
    "Survey project": {"category": "Survey", "days": 45, "tasks": [
        "Define objectives", "Design questionnaire", "Pilot test", "Collect responses",
        "Clean and analyze data", "Prepare findings", "Submit report"]},
    "Dashboard development": {"category": "Dashboard", "days": 35, "tasks": [
        "Confirm user requirements", "Prepare data model", "Build prototype",
        "User testing", "Apply revisions", "Publish dashboard"]},
    "Ranking submission": {"category": "Rankings", "days": 60, "tasks": [
        "Review methodology", "Map required indicators", "Collect evidence",
        "Validate figures", "Obtain approval", "Submit and archive"]},
    "Training activity": {"category": "Training", "days": 21, "tasks": [
        "Assess participant needs", "Prepare materials", "Deliver training",
        "Collect evaluation", "Prepare completion report"]},
}

st.markdown(
    """
    <style>
      .stApp {background: #f5f7fb;}
      section[data-testid="stSidebar"] {display:none;}
      .block-container {max-width:1280px;padding-top:2rem;padding-bottom:3rem;}
      .hero {padding:1.25rem 1.5rem;border-radius:16px;background:linear-gradient(110deg,#123b5d,#1f6b8c);color:white;margin-bottom:1rem;box-shadow:0 8px 24px #102a4324;}
      .hero h1 {margin:0;font-size:2rem}.hero p{margin:.35rem 0 0;opacity:.88}
      .card {background:white;border:1px solid #e5eaf0;border-radius:14px;padding:1rem;box-shadow:0 3px 12px #102a430d;margin:.3rem 0;}
      .badge {display:inline-block;padding:.2rem .55rem;border-radius:999px;background:#e8f1f8;color:#174a6e;font-size:.8rem;font-weight:600}
      .danger {color:#b42318;font-weight:700}.warning {color:#b54708;font-weight:700}.good{color:#027a48;font-weight:700}
      div[data-testid="stMetric"] {background:white;border:1px solid #e5eaf0;padding:.9rem;border-radius:12px;}
      .small-muted {font-size:.85rem;color:#667085}
      .task-row {background:white;border:1px solid #e5eaf0;border-left:5px solid #2e90fa;border-radius:12px;padding:.8rem 1rem;margin:.3rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def get_workspace_user() -> dict[str, Any]:
    """Open the shared workspace directly—no sign-in screen."""
    rows = query("SELECT * FROM users WHERE role='owner' ORDER BY id LIMIT 1")
    if not rows:
        execute("""INSERT INTO users(username,full_name,email,password_hash,role)
                   VALUES('shared_workspace','Project workspace','','','owner')""")
        rows = query("SELECT * FROM users WHERE role='owner' ORDER BY id LIMIT 1")
    workspace_user = rows[0]
    workspace_user.pop("password_hash", None)
    return workspace_user


user = get_workspace_user()
projects = visible_projects(user)
project_ids = [p["id"] for p in projects]

with st.sidebar:
    st.markdown("### ProjectFlow Pro\n**Shared project workspace**")
    page_options = ["Dashboard", "Projects", "Tasks", "Timeline", "Alerts", "Reports", "Tools"]
    if "nav_page" not in st.session_state or st.session_state.nav_page not in page_options:
        st.session_state.nav_page = "Dashboard"
    q1, q2 = st.columns(2)
    q1.button("＋ Project", width="stretch", on_click=lambda: st.session_state.update(nav_page="Projects"))
    q2.button("＋ Task", width="stretch", on_click=lambda: st.session_state.update(nav_page="Tasks"))
    page = st.radio("Navigation", page_options, label_visibility="collapsed", key="nav_page")
    st.divider()
    st.caption("Open the app and start working—no account or password required.")


def project_selector(label: str = "Project", key: str | None = None) -> int | None:
    if not projects:
        st.info("No project is available.")
        return None
    labels = {p["id"]: p["name"] for p in projects}
    return st.selectbox(label, list(labels), format_func=lambda x: labels[x], key=key)


def render_dashboard() -> None:
    hero("Dashboard", "A live overview of priorities, progress, risks, and upcoming deadlines")
    if user["role"] == "owner" and projects:
        with st.expander("＋ Quick add a task"):
            project_map = {p["id"]:p["name"] for p in projects}
            with st.form("quick_task"):
                q1,q2,q3 = st.columns([2,1.3,1])
                quick_title = q1.text_input("Task")
                quick_project = q2.selectbox("Project",list(project_map),format_func=lambda x:project_map[x])
                quick_due = q3.date_input("Due",value=date.today()+timedelta(days=7))
                quick_save = st.form_submit_button("Add task",type="primary")
            if quick_save and quick_title.strip():
                save_task(dict(project_id=quick_project,title=quick_title.strip(),description="",assignee_id=user["id"],
                    status="Not started",priority="Medium",start_date=str(date.today()),due_date=str(quick_due),
                    weight=1,estimated_hours=0,actual_hours=0,dependency_task_id=None),user["id"])
                st.success("Task added."); st.rerun()
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


def project_form(existing: dict | None = None, template_name: str = "Blank project") -> None:
    template = PROJECT_TEMPLATES.get(template_name, PROJECT_TEMPLATES["Blank project"])
    default_status = existing["status"] if existing else "Not started"
    default_priority = existing["priority"] if existing else "Medium"
    with st.form("project_form"):
        name = st.text_input("Project name *", value=existing["name"] if existing else "")
        d1, d2 = st.columns(2)
        start_date = d1.date_input("Start date", value=parse_date(existing.get("start_date") if existing else None))
        due_date = d2.date_input("Submission date *", value=parse_date(
            existing.get("due_date") if existing else None,
            date.today()+timedelta(days=int(template["days"]))))
        description = st.text_area("Short description (optional)", value=existing["description"] if existing else "", height=80)
        with st.expander("Advanced options", expanded=bool(existing)):
            c1, c2, c3 = st.columns(3)
            category = c1.text_input("Category", value=existing["category"] if existing else template["category"])
            priority = c2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(default_priority))
            status = c3.selectbox("Status", PROJECT_STATUSES, index=PROJECT_STATUSES.index(default_status))
            alert_days = st.number_input("Alert before deadline (days)", 0, 365, int(existing["alert_days"] if existing else 7))
            coordinator_id = None
            s1, s2 = st.columns(2)
            mode = s1.selectbox("Progress", ["Automatic from tasks", "Manual"],
                                index=1 if existing and existing["manual_progress"] is not None else 0)
            manual = s2.slider("Manual progress (%)", 0, 100,
                               int(existing["manual_progress"] or 0) if existing else 0,
                               disabled=mode.startswith("Automatic"))
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
            saved_id = save_project(data, user["id"], existing["id"] if existing else None)
            if not existing and template["tasks"]:
                span = max((due_date-start_date).days, len(template["tasks"]))
                for index, task_title in enumerate(template["tasks"], start=1):
                    task_due = start_date + timedelta(days=round(span*index/len(template["tasks"])))
                    save_task(dict(project_id=saved_id,title=task_title,description="",assignee_id=user["id"],
                        status="Not started",priority=priority,start_date=str(start_date),due_date=str(task_due),
                        weight=1,estimated_hours=0,actual_hours=0,dependency_task_id=None), user["id"])
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
        filters = st.columns([1,1,1.5,1])
        status_filter = filters[0].multiselect("Status", PROJECT_STATUSES)
        priority_filter = filters[1].multiselect("Priority", PRIORITIES)
        search = filters[2].text_input("Search")
        sort_by = filters[3].selectbox("Sort", ["Priority", "Deadline", "Progress", "Name"])
        shown = [p for p in projects if (not status_filter or p["status"] in status_filter)
                 and (not priority_filter or p["priority"] in priority_filter)
                 and (not search or search.lower() in (p["name"]+p["description"]+p["category"]).lower())]
        priority_rank = {"Critical":0,"High":1,"Medium":2,"Low":3}
        if sort_by == "Deadline": shown.sort(key=lambda p:p["due_date"] or "9999-12-31")
        elif sort_by == "Progress": shown.sort(key=lambda p:p["progress"], reverse=True)
        elif sort_by == "Name": shown.sort(key=lambda p:p["name"].lower())
        else: shown.sort(key=lambda p:priority_rank.get(p["priority"],9))
        for p in shown:
            with st.expander(f"{p['name']}  ·  {p['progress']:.0f}%  ·  {p['status']}"):
                a, b, c, d = st.columns(4)
                a.metric("Progress", f"{p['progress']:.0f}%")
                b.metric("Priority", p["priority"])
                c.metric("Submission", p["due_date"] or "—")
                remaining = (date.fromisoformat(p["due_date"])-date.today()).days if p["due_date"] else None
                d.metric("Time remaining", status_label(remaining) if remaining is not None else "No deadline")
                st.write(p["description"] or "No description.")
                if user["role"] == "owner":
                    if st.button("Edit project", key=f"editp{p['id']}"):
                        st.session_state.edit_project = p["id"]
                    if st.session_state.get("edit_project") == p["id"]:
                        project_form(p)
    if tab2:
        with tab2:
            st.info("Choose a template to create a useful task structure automatically, or start blank.")
            template_name = st.selectbox("Project template", list(PROJECT_TEMPLATES))
            project_form(template_name=template_name)


def task_form(project_id: int, existing: dict | None = None) -> None:
    dependencies = query("SELECT id,title FROM tasks WHERE project_id=? AND id<>? ORDER BY title", (project_id, existing["id"] if existing else -1))
    dep_map = {None:"No dependency"} | {d["id"]:d["title"] for d in dependencies}
    default_status = existing["status"] if existing else "Not started"
    default_priority = existing["priority"] if existing else "Medium"
    with st.form(f"task_form_{project_id}_{existing['id'] if existing else 'new'}"):
        title = st.text_input("Task title *", value=existing["title"] if existing else "")
        c1,c2 = st.columns(2)
        due = c1.date_input("Due date *", value=parse_date(existing.get("due_date") if existing else None, date.today()+timedelta(days=7)), key=f"td{project_id}{existing['id'] if existing else 0}")
        status = c2.selectbox("Status", TASK_STATUSES, index=TASK_STATUSES.index(default_status))
        assignee = user["id"]
        with st.expander("More details", expanded=bool(existing)):
            description = st.text_area("Description / definition of done", value=existing["description"] if existing else "")
            d1,d2,d3 = st.columns(3)
            start = d1.date_input("Start date", value=parse_date(existing.get("start_date") if existing else None), key=f"ts{project_id}{existing['id'] if existing else 0}")
            priority = d2.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(default_priority))
            weight = d3.number_input("Progress weight", .1, 100.0, float(existing["weight"] if existing else 1), .5)
            h1,h2,h3 = st.columns(3)
            estimated = h1.number_input("Estimated hours", 0.0, 10000.0, float(existing["estimated_hours"] if existing else 0), .5)
            actual = h2.number_input("Actual hours", 0.0, 10000.0, float(existing["actual_hours"] if existing else 0), .5)
            dep_keys = list(dep_map)
            old_dep = existing.get("dependency_task_id") if existing else None
            dependency = h3.selectbox("Depends on", dep_keys, index=dep_keys.index(old_dep) if old_dep in dep_keys else 0, format_func=lambda x:dep_map[x])
        submitted = st.form_submit_button("Save task", type="primary", width="stretch")
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
        f1, f2 = st.columns([2,1])
        status_filter = f1.multiselect("Filter task status", TASK_STATUSES)
        view_mode = f2.radio("View", ["Action cards", "Compact table"], horizontal=True)
        shown = [t for t in tasks if not status_filter or t["status"] in status_filter]
        if not shown:
            st.info("No tasks match the selection.")
        if shown and view_mode == "Compact table":
            table = pd.DataFrame([{
                "Task":t["title"], "Status":t["status"], "Priority":t["priority"],
                "Due":t["due_date"], "Hours":f"{t['actual_hours']}/{t['estimated_hours']}"
            } for t in shown])
            st.dataframe(table, hide_index=True, width="stretch")
        for t in shown if view_mode == "Action cards" else []:
            overdue = t["due_date"] and date.fromisoformat(t["due_date"]) < date.today() and t["status"] not in {"Completed","Cancelled"}
            with st.expander(f"{'🔴 ' if overdue else ''}{t['title']}  ·  {t['status']}  ·  Due {t['due_date'] or '—'}"):
                st.write(t["description"] or "No description.")
                st.caption(f"Priority: {t['priority']} · Weight: {t['weight']} · Dependency: {t['dependency'] or 'None'}")
                st.caption(f"Estimated: {t['estimated_hours']} h · Actual: {t['actual_hours']} h")
                can_edit = True
                if can_edit:
                    a1,a2,a3,a4 = st.columns(4)
                    if t["status"] != "In progress" and a1.button("▶ Start", key=f"start{t['id']}", width="stretch"):
                        execute("UPDATE tasks SET status='In progress',updated_at=CURRENT_TIMESTAMP WHERE id=?",(t["id"],))
                        log_activity(user["id"],"Started task",t["title"],project_id); st.rerun()
                    if t["status"] != "Completed" and a2.button("✓ Complete", key=f"done{t['id']}", width="stretch"):
                        execute("UPDATE tasks SET status='Completed',completed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=?",(t["id"],))
                        log_activity(user["id"],"Completed task",t["title"],project_id); st.rerun()
                    if t["status"] != "Blocked" and a3.button("! Block", key=f"block{t['id']}", width="stretch"):
                        execute("UPDATE tasks SET status='Blocked',updated_at=CURRENT_TIMESTAMP WHERE id=?",(t["id"],))
                        log_activity(user["id"],"Blocked task",t["title"],project_id); st.rerun()
                    if a4.button("Edit", key=f"editt{t['id']}", width="stretch"):
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


def render_tools() -> None:
    hero("Tools", "Sample data and project archiving")
    t1,t2 = st.tabs(["Sample project","Archive"])
    with t1:
        st.write("Generate one realistic sample project to explore the dashboard immediately.")
        if st.button("Create sample project"):
            before=int(scalar("SELECT COUNT(*) FROM projects WHERE owner_id=?",(user["id"],)) or 0)
            seed_demo_data(user["id"])
            after=int(scalar("SELECT COUNT(*) FROM projects WHERE owner_id=?",(user["id"],)) or 0)
            st.success("Sample project created." if after>before else "Sample data was not added because projects already exist.")
            st.rerun()
    with t2:
        archived=visible_projects(user,include_archived=True)
        archived=[p for p in archived if p["archived"]]
        st.write("Archived projects remain in the database and can be restored.")
        for p in projects:
            if st.button(f"Archive · {p['name']}",key=f"archive{p['id']}"):
                execute("UPDATE projects SET archived=1 WHERE id=? AND owner_id=?",(p["id"],user["id"])); st.rerun()
        for p in archived:
            if st.button(f"Restore · {p['name']}",key=f"restore{p['id']}"):
                execute("UPDATE projects SET archived=0 WHERE id=? AND owner_id=?",(p["id"],user["id"])); st.rerun()


def all_workspace_tasks() -> list[dict[str, Any]]:
    return query("""SELECT t.*,p.name project_name,p.color project_color
        FROM tasks t JOIN projects p ON p.id=t.project_id
        WHERE p.archived=0 AND p.status<>'Cancelled'
        ORDER BY CASE t.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                 COALESCE(t.due_date,'9999-12-31')""")


def change_task_status(task: dict[str, Any], new_status: str) -> None:
    completed_at = datetime.now().isoformat(timespec="seconds") if new_status == "Completed" else None
    execute("UPDATE tasks SET status=?,completed_at=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_status,completed_at,task["id"]))
    log_activity(user["id"],f"Task: {new_status}",task["title"],task["project_id"])
    st.rerun()


def daily_task_card(task: dict[str, Any], key_prefix: str) -> None:
    due = date.fromisoformat(task["due_date"]) if task["due_date"] else None
    days = (due-date.today()).days if due else None
    due_text = "No due date" if days is None else status_label(days)
    icon = "🔴" if days is not None and days < 0 else "🟠" if days is not None and days <= 2 else "🔵"
    c1,c2,c3,c4 = st.columns([.35,4.4,1.15,1.15],vertical_alignment="center")
    c1.markdown(f"### {icon}")
    c2.markdown(f"**{task['title']}**  \n<span class='small-muted'>{task['project_name']} · {due_text} · {task['priority']}</span>",unsafe_allow_html=True)
    if task["status"] != "In progress":
        if c3.button("Start",key=f"{key_prefix}_start_{task['id']}",width="stretch"):
            change_task_status(task,"In progress")
    else:
        c3.caption("In progress")
    if c4.button("✓ Done",key=f"{key_prefix}_done_{task['id']}",type="primary",width="stretch"):
        change_task_status(task,"Completed")
    st.divider()


def quick_add_task_form(current_projects: list[dict[str, Any]], form_key: str = "daily_quick_add") -> None:
    if not current_projects:
        st.info("Create your first project below, then add tasks here.")
        return
    project_map = {p["id"]:p["name"] for p in current_projects}
    with st.form(form_key,clear_on_submit=True):
        c1,c2,c3,c4 = st.columns([3,2,1.35,.8],vertical_alignment="bottom")
        title = c1.text_input("What needs to be done?",placeholder="Example: Validate the final figures")
        project_id = c2.selectbox("Project",list(project_map),format_func=lambda x:project_map[x])
        due = c3.date_input("Due date",value=date.today())
        submitted = c4.form_submit_button("Add",type="primary",width="stretch")
    if submitted:
        if not title.strip():
            st.warning("Write a task before clicking Add.")
        else:
            save_task(dict(project_id=project_id,title=title.strip(),description="",assignee_id=user["id"],
                status="Not started",priority="Medium",start_date=str(date.today()),due_date=str(due),
                weight=1,estimated_hours=0,actual_hours=0,dependency_task_id=None),user["id"])
            st.rerun()


def render_my_day(current_projects: list[dict[str, Any]]) -> None:
    st.subheader("Quick add")
    quick_add_task_form(current_projects)
    tasks = all_workspace_tasks()
    open_tasks = [t for t in tasks if t["status"] not in {"Completed","Cancelled"}]
    overdue = [t for t in open_tasks if t["due_date"] and date.fromisoformat(t["due_date"]) < date.today()]
    due_today = [t for t in open_tasks if t["due_date"] == str(date.today())]
    next_week = [t for t in open_tasks if t["due_date"] and date.today() < date.fromisoformat(t["due_date"]) <= date.today()+timedelta(days=7)]

    st.subheader("What needs attention")
    view = st.radio("Show",["Today","Next 7 days","All open"],horizontal=True,label_visibility="collapsed")
    if view == "Today":
        selected = overdue + due_today
    elif view == "Next 7 days":
        selected = overdue + due_today + next_week
    else:
        selected = open_tasks
    seen=set(); selected=[t for t in selected if not (t["id"] in seen or seen.add(t["id"]))]
    if not selected:
        st.success("Nothing urgent here. Your day is clear.")
    for task in selected:
        daily_task_card(task,"day")

    completed_today = [t for t in tasks if t["status"]=="Completed" and (t["completed_at"] or "")[:10]==str(date.today())]
    with st.expander(f"Completed today ({len(completed_today)})"):
        for task in completed_today:
            c1,c2=st.columns([5,1])
            c1.write(f"✅ **{task['title']}** · {task['project_name']}")
            if c2.button("Reopen",key=f"reopen_{task['id']}"):
                change_task_status(task,"In progress")


def create_simple_project() -> None:
    with st.form("simple_project",clear_on_submit=True):
        c1,c2,c3,c4=st.columns([3,1.4,1.2,.8],vertical_alignment="bottom")
        name=c1.text_input("Project name",placeholder="Example: QS Sustainability submission")
        due=c2.date_input("Submission date",value=date.today()+timedelta(days=30))
        priority=c3.selectbox("Priority",["Medium","High","Critical","Low"])
        submitted=c4.form_submit_button("Create",type="primary",width="stretch")
    if submitted:
        if not name.strip():
            st.warning("Enter a project name.")
        else:
            save_project(dict(name=name.strip(),description="",category="General",priority=priority,
                status="In progress",start_date=str(date.today()),due_date=str(due),coordinator_id=None,
                manual_progress=None,alert_days=7,color="#1F6B8C"),user["id"])
            st.rerun()


def project_health(project: dict[str, Any]) -> dict[str, Any]:
    tasks=query("SELECT status,due_date FROM tasks WHERE project_id=?",(project["id"],))
    open_tasks=[t for t in tasks if t["status"] not in {"Completed","Cancelled"}]
    overdue=sum(bool(t["due_date"] and date.fromisoformat(t["due_date"])<date.today()) for t in open_tasks)
    blocked=sum(t["status"]=="Blocked" for t in open_tasks)
    project_days=(date.fromisoformat(project["due_date"])-date.today()).days if project["due_date"] else None
    if overdue or (project_days is not None and project_days<0):
        label,icon="Overdue","🔴"
    elif blocked or (project_days is not None and project_days<=7 and project["progress"]<90):
        label,icon="Attention","🟠"
    elif project["status"]=="Completed":
        label,icon="Completed","✅"
    else:
        label,icon="On track","🟢"
    return dict(label=label,icon=icon,open=len(open_tasks),overdue=overdue,blocked=blocked,days=project_days)


def add_followup_comment(project_id: int, body: str) -> None:
    author=st.session_state.get("comment_author","").strip()
    if not author:
        st.warning("Set your name at the top of the page before adding a comment.")
        return
    execute("INSERT INTO comments(project_id,task_id,user_id,author_name,body) VALUES(?,?,?,?,?)",
            (project_id,None,user["id"],author,body.strip()))
    log_activity(user["id"],"Added follow-up comment",f"{author}: {body.strip()[:100]}",project_id)
    st.rerun()


def render_project_workspace(current_projects: list[dict[str, Any]]) -> None:
    st.subheader("Create a project")
    create_simple_project()
    if not current_projects:
        st.info("Your projects will appear here.")
        return
    st.subheader("Your projects")
    search=st.text_input("Search projects",placeholder="Type a project name...")
    shown=[p for p in current_projects if not search or search.lower() in p["name"].lower()]
    for project in shown:
        tasks=query("SELECT * FROM tasks WHERE project_id=? ORDER BY COALESCE(due_date,'9999-12-31')",(project["id"],))
        open_count=sum(t["status"] not in {"Completed","Cancelled"} for t in tasks)
        health=project_health(project)
        comments=query("SELECT * FROM comments WHERE project_id=? ORDER BY created_at DESC",(project["id"],))
        with st.expander(f"{health['icon']} {project['name']}   ·   {project['progress']:.0f}%   ·   {open_count} open   ·   {len(comments)} comment(s)"):
            st.progress(project["progress"]/100,text=f"{project['progress']:.0f}% complete · Submission {project['due_date'] or 'not set'}")
            with st.form(f"project_quick_{project['id']}",clear_on_submit=True):
                q1,q2,q3=st.columns([4,1.5,.8],vertical_alignment="bottom")
                task_title=q1.text_input("Add a task",key=f"ptitle_{project['id']}",placeholder="New task")
                task_due=q2.date_input("Due",value=date.today()+timedelta(days=7),key=f"pdue_{project['id']}")
                add=q3.form_submit_button("Add",type="primary",width="stretch")
            if add and task_title.strip():
                save_task(dict(project_id=project["id"],title=task_title.strip(),description="",assignee_id=user["id"],
                    status="Not started",priority="Medium",start_date=str(date.today()),due_date=str(task_due),
                    weight=1,estimated_hours=0,actual_hours=0,dependency_task_id=None),user["id"])
                st.rerun()
            for task in tasks:
                if task["status"] in {"Completed","Cancelled"}: continue
                task["project_name"]=project["name"]
                daily_task_card(task,f"project_{project['id']}")
            with st.expander(f"💬 Follow-up comments ({len(comments)})"):
                with st.form(f"comment_{project['id']}",clear_on_submit=True):
                    cc1,cc2=st.columns([5,1],vertical_alignment="bottom")
                    comment=cc1.text_input("Add a comment",placeholder="Question, decision, feedback, or requested action")
                    post=cc2.form_submit_button("Post",type="primary",width="stretch")
                if post and comment.strip():
                    add_followup_comment(project["id"],comment)
                if not comments:
                    st.caption("No comments yet.")
                for item in comments[:10]:
                    author=item.get("author_name") or "Team member"
                    st.markdown(f"**{author}** · {item['created_at'][:16]}  \n{item['body']}")
                    st.divider()
            with st.expander("Edit project details"):
                with st.form(f"edit_simple_project_{project['id']}"):
                    e1,e2,e3=st.columns(3)
                    project_due=e1.date_input("Submission",value=parse_date(project["due_date"],date.today()+timedelta(days=30)),key=f"epd{project['id']}")
                    project_priority=e2.selectbox("Priority",PRIORITIES,index=PRIORITIES.index(project["priority"]),key=f"epp{project['id']}")
                    project_status=e3.selectbox("Status",PROJECT_STATUSES,index=PROJECT_STATUSES.index(project["status"]),key=f"eps{project['id']}")
                    description=st.text_area("Notes",value=project["description"] or "",key=f"epn{project['id']}")
                    saved=st.form_submit_button("Save changes")
                if saved:
                    data=dict(name=project["name"],description=description,category=project["category"],priority=project_priority,
                        status=project_status,start_date=project["start_date"],due_date=str(project_due),coordinator_id=None,
                        manual_progress=project["manual_progress"],alert_days=project["alert_days"],color=project["color"])
                    save_project(data,user["id"],project["id"]); st.rerun()


def render_simple_overview(current_projects: list[dict[str, Any]]) -> None:
    if not current_projects:
        st.info("Create a project to see the overview.")
        return
    tasks=all_workspace_tasks()
    active=[p for p in current_projects if p["status"] not in {"Completed","Cancelled"}]
    overdue=[t for t in tasks if t["status"] not in {"Completed","Cancelled"} and t["due_date"] and date.fromisoformat(t["due_date"])<date.today()]
    completed=sum(t["status"]=="Completed" for t in tasks)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Active projects",len(active)); c2.metric("Open tasks",sum(t["status"] not in {"Completed","Cancelled"} for t in tasks))
    c3.metric("Overdue",len(overdue)); c4.metric("Completed tasks",completed)
    st.subheader("Coordinator follow-up")
    followup=[]
    for project in current_projects:
        health=project_health(project)
        next_tasks=query("""SELECT title,due_date FROM tasks WHERE project_id=?
            AND status NOT IN ('Completed','Cancelled') ORDER BY COALESCE(due_date,'9999-12-31') LIMIT 1""",(project["id"],))
        last_comment=query("SELECT author_name,body,created_at FROM comments WHERE project_id=? ORDER BY created_at DESC LIMIT 1",(project["id"],))
        followup.append({
            "Health":f"{health['icon']} {health['label']}","Project":project["name"],
            "Progress":f"{project['progress']:.0f}%","Open tasks":health["open"],"Overdue":health["overdue"],
            "Next action":next_tasks[0]["title"] if next_tasks else "—",
            "Submission":project["due_date"] or "—",
            "Latest comment":(last_comment[0]["body"][:70] if last_comment else "—")
        })
    st.dataframe(pd.DataFrame(followup),hide_index=True,width="stretch")
    df=pd.DataFrame(current_projects)
    fig=px.bar(df,x="progress",y="name",orientation="h",color="priority",text="progress",
               labels={"name":"Project","progress":"Progress (%)"},color_discrete_map={"Critical":"#b42318","High":"#f79009","Medium":"#2e90fa","Low":"#12b76a"})
    fig.update_layout(height=max(320,55*len(df)),xaxis_range=[0,100],margin=dict(l=10,r=10,t=20,b=10),showlegend=True)
    st.plotly_chart(fig,width="stretch")
    with st.expander("Timeline"):
        timeline=gantt_data([p["id"] for p in current_projects])
        if timeline.empty: st.info("Add task dates to display the timeline.")
        else:
            chart=px.timeline(timeline,x_start="Start",x_end="Finish",y="Task",color="Status",hover_data=["Project"])
            chart.update_yaxes(autorange="reversed"); st.plotly_chart(chart,width="stretch")
    recent_comments=query("""SELECT c.author_name,c.body,c.created_at,p.name project_name
        FROM comments c JOIN projects p ON p.id=c.project_id
        WHERE p.archived=0 ORDER BY c.created_at DESC LIMIT 12""")
    with st.expander(f"Recent comments ({len(recent_comments)})",expanded=bool(recent_comments)):
        if not recent_comments:
            st.caption("No comments have been added.")
        for item in recent_comments:
            st.markdown(f"**{item['author_name'] or 'Team member'}** on **{item['project_name']}** · {item['created_at'][:16]}  \n{item['body']}")
            st.divider()
    st.download_button("Download complete Excel backup",project_export([p["id"] for p in current_projects]),
        file_name=f"projectflow_backup_{date.today()}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def render_daily_app() -> None:
    current_projects=visible_projects(user)
    tasks=all_workspace_tasks()
    open_tasks=[t for t in tasks if t["status"] not in {"Completed","Cancelled"}]
    overdue=sum(bool(t["due_date"] and date.fromisoformat(t["due_date"])<date.today()) for t in open_tasks)
    due_today=sum(t["due_date"]==str(date.today()) for t in open_tasks)
    h1,h2=st.columns([5,1.4],vertical_alignment="center")
    h1.markdown("# ProjectFlow Daily")
    h1.caption(f"{date.today().strftime('%A, %d %B %Y')} · {due_today} due today · {overdue} overdue")
    with h2.popover("💬 Commenting identity",width="stretch"):
        st.text_input("Your name",key="comment_author",placeholder="Example: Tarek or Coordinator",
                      help="Used only to identify your comments. No account or password is created.")
        st.caption("Set this once per browser session.")
    tab_day,tab_projects,tab_overview=st.tabs(["☀️ My Day","📁 Projects","📊 Overview"])
    with tab_day: render_my_day(current_projects)
    with tab_projects: render_project_workspace(current_projects)
    with tab_overview: render_simple_overview(current_projects)


def render_ultra_simple_app() -> None:
    current_projects=visible_projects(user)
    tasks=all_workspace_tasks()
    open_tasks=[t for t in tasks if t["status"] not in {"Completed","Cancelled"}]
    overdue=sum(bool(t["due_date"] and date.fromisoformat(t["due_date"])<date.today()) for t in open_tasks)
    due_soon=sum(bool(t["due_date"] and date.today()<=date.fromisoformat(t["due_date"])<=date.today()+timedelta(days=7)) for t in open_tasks)

    st.markdown("# Project Tracker")
    st.caption("One page for projects, tasks, deadlines, and comments")
    m1,m2,m3=st.columns(3)
    m1.metric("Active projects",len(current_projects))
    m2.metric("Due within 7 days",due_soon)
    m3.metric("Overdue tasks",overdue)

    with st.expander("＋ Add a new project",expanded=not current_projects):
        create_simple_project()

    if not current_projects:
        st.info("Add your first project above. It takes only a name and a deadline.")
        return

    st.caption("🟢 On track   ·   🟠 Needs attention   ·   🔴 Overdue")
    for project in current_projects:
        health=project_health(project)
        project_tasks=query("SELECT * FROM tasks WHERE project_id=? ORDER BY COALESCE(due_date,'9999-12-31')",(project["id"],))
        open_project_tasks=[t for t in project_tasks if t["status"] not in {"Completed","Cancelled"}]
        completed_tasks=[t for t in project_tasks if t["status"]=="Completed"]
        comments=query("SELECT * FROM comments WHERE project_id=? ORDER BY created_at DESC",(project["id"],))
        due_text=f"Due {project['due_date']}" if project["due_date"] else "No deadline"

        with st.expander(f"{health['icon']}  {project['name']}   |   {project['progress']:.0f}%   |   {due_text}"):
            st.progress(project["progress"]/100,text=f"{project['progress']:.0f}% complete · {len(open_project_tasks)} task(s) remaining")
            if comments:
                latest=comments[0]
                st.info(f"Latest comment — {latest.get('author_name') or 'Team member'}: {latest['body']}")

            st.markdown("#### Tasks")
            if not open_project_tasks:
                st.success("No open tasks.")
            for task in open_project_tasks:
                task["project_name"]=project["name"]
                daily_task_card(task,f"simple_{project['id']}")

            with st.form(f"simple_task_{project['id']}",clear_on_submit=True):
                t1,t2,t3=st.columns([4,1.5,.8],vertical_alignment="bottom")
                task_title=t1.text_input("New task",placeholder="What needs to be done?",key=f"simple_title_{project['id']}")
                task_due=t2.date_input("Due date",value=date.today()+timedelta(days=7),key=f"simple_due_{project['id']}")
                add_task=t3.form_submit_button("Add",type="primary",width="stretch")
            if add_task and task_title.strip():
                save_task(dict(project_id=project["id"],title=task_title.strip(),description="",assignee_id=user["id"],
                    status="Not started",priority="Medium",start_date=str(date.today()),due_date=str(task_due),
                    weight=1,estimated_hours=0,actual_hours=0,dependency_task_id=None),user["id"])
                st.rerun()

            st.markdown("#### Comments")
            with st.form(f"simple_comment_{project['id']}",clear_on_submit=True):
                c1,c2,c3=st.columns([1.4,4,.8],vertical_alignment="bottom")
                author=c1.text_input("Name",placeholder="Your name",key=f"simple_author_{project['id']}")
                comment=c2.text_input("Comment",placeholder="Feedback, question, or decision",key=f"simple_comment_text_{project['id']}")
                post=c3.form_submit_button("Post",type="primary",width="stretch")
            if post:
                if not author.strip() or not comment.strip():
                    st.warning("Enter your name and comment.")
                else:
                    execute("INSERT INTO comments(project_id,task_id,user_id,author_name,body) VALUES(?,?,?,?,?)",
                            (project["id"],None,user["id"],author.strip(),comment.strip()))
                    log_activity(user["id"],"Added comment",f"{author.strip()}: {comment.strip()[:100]}",project["id"])
                    st.rerun()
            for item in comments[:5]:
                st.markdown(f"**{item.get('author_name') or 'Team member'}** · {item['created_at'][:16]}  \n{item['body']}")

            if completed_tasks:
                with st.expander(f"Completed tasks ({len(completed_tasks)})"):
                    for task in completed_tasks:
                        r1,r2=st.columns([5,1],vertical_alignment="center")
                        r1.write(f"✅ {task['title']}")
                        task["project_name"]=project["name"]
                        if r2.button("Reopen",key=f"simple_reopen_{task['id']}"):
                            change_task_status(task,"In progress")

            with st.expander("Project settings"):
                with st.form(f"simple_settings_{project['id']}"):
                    s1,s2=st.columns(2)
                    new_due=s1.date_input("Project deadline",value=parse_date(project["due_date"],date.today()+timedelta(days=30)),key=f"simple_project_due_{project['id']}")
                    new_status=s2.selectbox("Project status",PROJECT_STATUSES,index=PROJECT_STATUSES.index(project["status"]),key=f"simple_project_status_{project['id']}")
                    save_settings=st.form_submit_button("Save")
                if save_settings:
                    data=dict(name=project["name"],description=project["description"],category=project["category"],priority=project["priority"],
                        status=new_status,start_date=project["start_date"],due_date=str(new_due),coordinator_id=None,
                        manual_progress=project["manual_progress"],alert_days=project["alert_days"],color=project["color"])
                    save_project(data,user["id"],project["id"]); st.rerun()

    st.divider()
    st.download_button("Download Excel backup",project_export([p["id"] for p in current_projects]),
        file_name=f"project_backup_{date.today()}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


render_ultra_simple_app()
