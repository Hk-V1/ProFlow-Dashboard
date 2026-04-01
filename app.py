import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime, date, timedelta
import pandas as pd

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ProFlow Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Database Setup ──────────────────────────────────────────────────────────
DB_PATH = "proflow.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Tasks table
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        deadline TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending',
        category TEXT DEFAULT 'Personal',
        company_id INTEGER DEFAULT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Students table
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        subject TEXT,
        schedule TEXT,
        fees REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'Unpaid',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Attendance table
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        status TEXT DEFAULT 'Present'
    )""")

    # Companies table
    c.execute("""CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        contact TEXT,
        email TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Events / Calendar table
    c.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        event_date TEXT,
        event_time TEXT,
        event_type TEXT DEFAULT 'Meeting',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Budget table
    c.execute("""CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        description TEXT,
        date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Daily planner table
    c.execute("""CREATE TABLE IF NOT EXISTS daily_planner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        note TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        plan_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

# ─── Auth Helpers ────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(username, password, full_name, email):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, full_name, email) VALUES (?,?,?,?)",
                  (username, hash_password(password), full_name, email))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, full_name FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    row = c.fetchone()
    conn.close()
    if row:
        return True, row[0], row[1]
    return False, None, None

# ─── Custom CSS ──────────────────────────────────────────────────────────────
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    :root {
        --bg: #0f1117;
        --card: #1a1d27;
        --accent: #6c63ff;
        --accent2: #f7c948;
        --text: #e8e8f0;
        --muted: #8888aa;
        --border: #2a2d3e;
        --success: #4ade80;
        --danger: #f87171;
        --warning: #fb923c;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--card) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: #7c74ff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(108,99,255,0.4) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
    }

    /* Tables / DataFrames */
    .stDataFrame { border-radius: 12px !important; overflow: hidden; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--card) !important;
        border-radius: 10px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--muted) !important;
        border-radius: 8px !important;
        font-family: 'Syne', sans-serif !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: white !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }

    /* Dividers */
    hr { border-color: var(--border) !important; }

    /* Success/error messages */
    .stSuccess { background: rgba(74,222,128,0.1) !important; border: 1px solid var(--success) !important; border-radius: 8px !important; }
    .stError { background: rgba(248,113,113,0.1) !important; border: 1px solid var(--danger) !important; border-radius: 8px !important; }
    .stWarning { background: rgba(251,146,60,0.1) !important; border: 1px solid var(--warning) !important; border-radius: 8px !important; }

    /* Stat card */
    .stat-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.5rem;
    }
    .stat-number {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: var(--accent);
    }
    .stat-label {
        font-size: 0.85rem;
        color: var(--muted);
        margin-top: 2px;
    }

    /* Page title */
    .page-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text);
        margin-bottom: 0.25rem;
    }
    .page-subtitle {
        color: var(--muted);
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-high { background: rgba(248,113,113,0.15); color: #f87171; }
    .badge-medium { background: rgba(251,146,60,0.15); color: #fb923c; }
    .badge-low { background: rgba(74,222,128,0.15); color: #4ade80; }

    /* Logo / brand */
    .brand {
        font-family: 'Syne', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--accent);
    }

    /* Deadline alert */
    .deadline-card {
        background: rgba(247,201,72,0.08);
        border: 1px solid rgba(247,201,72,0.3);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }

    /* Hide default streamlit elements */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# ─── Auth Page ───────────────────────────────────────────────────────────────
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem;">
        <div style="font-family:'Syne',sans-serif; font-size:2.5rem; font-weight:800; color:#6c63ff;">⚡ ProFlow</div>
        <div style="color:#8888aa; margin-top:0.5rem;">Your Personal Productivity Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_signup = st.tabs(["🔑 Login", "✨ Sign Up"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Login →", use_container_width=True)
                if submit:
                    ok, uid, name = login_user(username, password)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.user_id = uid
                        st.session_state.user_name = name
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_signup:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="john@example.com")
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
                confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                submit2 = st.form_submit_button("Create Account →", use_container_width=True)
                if submit2:
                    if len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif new_password != confirm:
                        st.error("Passwords do not match.")
                    elif not new_username or not full_name:
                        st.error("Please fill all required fields.")
                    else:
                        ok, msg = signup_user(new_username, new_password, full_name, email)
                        if ok:
                            st.success(msg + " Please login.")
                        else:
                            st.error(msg)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f'<div class="brand">⚡ ProFlow</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='color:#8888aa; font-size:0.8rem; margin-bottom:1rem;'>Hello, {st.session_state.user_name} 👋</div>", unsafe_allow_html=True)
        st.divider()

        pages = {
            "🏠 Dashboard": "dashboard",
            "✅ Tasks": "tasks",
            "👩‍🏫 Students": "students",
            "🏢 Companies": "companies",
            "📅 Calendar": "calendar",
            "💰 Budget": "budget",
            "📌 Daily Planner": "planner",
            "⚙️ Settings": "settings"
        }

        if "page" not in st.session_state:
            st.session_state.page = "dashboard"

        for label, key in pages.items():
            is_active = st.session_state.page == key
            btn_style = "background: #6c63ff !important;" if is_active else ""
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ─── DB Query Helpers ────────────────────────────────────────────────────────
def get_tasks(user_id, status=None, category=None, company_id=None):
    conn = get_connection()
    query = "SELECT * FROM tasks WHERE user_id=?"
    params = [user_id]
    if status: query += " AND status=?"; params.append(status)
    if category: query += " AND category=?"; params.append(category)
    if company_id: query += " AND company_id=?"; params.append(company_id)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_students(user_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM students WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def get_companies(user_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM companies WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def get_events(user_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM events WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def get_budget(user_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM budget WHERE user_id=?", conn, params=[user_id])
    conn.close()
    return df

def get_planner(user_id, plan_date):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM daily_planner WHERE user_id=? AND plan_date=?",
                           conn, params=[user_id, plan_date])
    conn.close()
    return df

# ─── DASHBOARD PAGE ──────────────────────────────────────────────────────────
def page_dashboard():
    uid = st.session_state.user_id
    today = date.today()

    st.markdown('<div class="page-title">🏠 Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">Today is {today.strftime("%A, %B %d, %Y")}</div>', unsafe_allow_html=True)

    # Stats row
    tasks = get_tasks(uid)
    total = len(tasks)
    completed = len(tasks[tasks["status"] == "Completed"]) if total else 0
    pending = len(tasks[tasks["status"] == "Pending"]) if total else 0

    budget = get_budget(uid)
    income = budget[budget["type"] == "Income"]["amount"].sum() if not budget.empty else 0
    expenses = budget[budget["type"] == "Expense"]["amount"].sum() if not budget.empty else 0
    balance = income - expenses

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("📋 Total Tasks", total)
    with c2:
        st.metric("✅ Completed", completed)
    with c3:
        st.metric("⏳ Pending", pending)
    with c4:
        st.metric("💰 Total Income", f"₹{income:,.0f}")
    with c5:
        st.metric("🏦 Balance", f"₹{balance:,.0f}", delta=f"₹{balance - expenses:,.0f}" if expenses else None)

    st.divider()

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("#### 📌 Today's Tasks")
        today_tasks = tasks[tasks["deadline"] == str(today)]
        if today_tasks.empty:
            st.info("No tasks due today. Enjoy your day! 🎉")
        else:
            for _, row in today_tasks.iterrows():
                priority_colors = {"High": "#f87171", "Medium": "#fb923c", "Low": "#4ade80"}
                color = priority_colors.get(row["priority"], "#6c63ff")
                status_icon = "✅" if row["status"] == "Completed" else "⏳"
                st.markdown(f"""
                <div style="background:#1a1d27; border:1px solid #2a2d3e; border-left: 3px solid {color};
                     border-radius:8px; padding:0.7rem 1rem; margin:0.3rem 0;">
                    {status_icon} <strong>{row['title']}</strong>
                    <span style="float:right; color:#8888aa; font-size:0.8rem;">{row['category']}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 🔔 Upcoming Deadlines (Next 7 Days)")
        week_end = today + timedelta(days=7)
        if not tasks.empty:
            upcoming = tasks[
                (tasks["deadline"] > str(today)) &
                (tasks["deadline"] <= str(week_end)) &
                (tasks["status"] == "Pending")
            ].sort_values("deadline")
            if upcoming.empty:
                st.info("No upcoming deadlines this week.")
            else:
                for _, row in upcoming.iterrows():
                    days_left = (datetime.strptime(row["deadline"], "%Y-%m-%d").date() - today).days
                    st.markdown(f"""
                    <div class="deadline-card">
                        ⏰ <strong>{row['title']}</strong> — in {days_left} day(s)
                        <span style="float:right; color:#8888aa;">{row['deadline']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No tasks found.")

    with col_right:
        st.markdown("#### 📅 Today's Events")
        events = get_events(uid)
        today_events = events[events["event_date"] == str(today)] if not events.empty else pd.DataFrame()
        if today_events.empty:
            st.info("No events scheduled today.")
        else:
            for _, row in today_events.iterrows():
                st.markdown(f"""
                <div style="background:#1a1d27; border:1px solid #2a2d3e; border-radius:8px; padding:0.7rem 1rem; margin:0.3rem 0;">
                    📌 <strong>{row['title']}</strong><br>
                    <span style="color:#8888aa; font-size:0.8rem;">{row.get('event_time','')} · {row['event_type']}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 👩‍🏫 Students Overview")
        students = get_students(uid)
        if students.empty:
            st.info("No students added yet.")
        else:
            unpaid = len(students[students["payment_status"] == "Unpaid"])
            total_fees = students["fees"].sum()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(students)}</div>
                <div class="stat-label">Total Students · {unpaid} unpaid · ₹{total_fees:,.0f} total fees</div>
            </div>
            """, unsafe_allow_html=True)

# ─── TASKS PAGE ──────────────────────────────────────────────────────────────
def page_tasks():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">✅ Tasks & Assignments</div>', unsafe_allow_html=True)

    companies = get_companies(uid)
    company_options = {row["name"]: row["id"] for _, row in companies.iterrows()} if not companies.empty else {}

    tab_list, tab_add = st.tabs(["📋 All Tasks", "➕ Add Task"])

    with tab_add:
        with st.form("add_task"):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Task Title *")
                deadline = st.date_input("Deadline", value=date.today())
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            with c2:
                category = st.selectbox("Category", ["Personal", "Assignment", "Coaching", "Company"])
                status = st.selectbox("Status", ["Pending", "Completed"])
                company_sel = st.selectbox("Company (optional)", ["None"] + list(company_options.keys()))
            description = st.text_area("Description", height=100)
            submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

            if submitted:
                if not title:
                    st.error("Task title is required.")
                else:
                    cid = company_options.get(company_sel) if company_sel != "None" else None
                    conn = get_connection()
                    conn.execute("""INSERT INTO tasks (user_id, title, description, deadline, priority, status, category, company_id)
                                   VALUES (?,?,?,?,?,?,?,?)""",
                                 (uid, title, description, str(deadline), priority, status, category, cid))
                    conn.commit(); conn.close()
                    st.success("Task added successfully!")
                    st.rerun()

    with tab_list:
        col1, col2, col3 = st.columns(3)
        with col1:
            f_cat = st.selectbox("Filter by Category", ["All", "Personal", "Assignment", "Coaching", "Company"])
        with col2:
            f_status = st.selectbox("Filter by Status", ["All", "Pending", "Completed"])
        with col3:
            search = st.text_input("🔍 Search", placeholder="Search tasks...")

        tasks = get_tasks(uid,
                          status=None if f_status == "All" else f_status,
                          category=None if f_cat == "All" else f_cat)

        if search:
            tasks = tasks[tasks["title"].str.contains(search, case=False, na=False)]

        if tasks.empty:
            st.info("No tasks found.")
        else:
            # CSV export
            csv = tasks.to_csv(index=False)
            st.download_button("⬇️ Export CSV", csv, "tasks.csv", "text/csv")
            st.markdown(f"**{len(tasks)} tasks found**")

            for _, row in tasks.iterrows():
                priority_colors = {"High": "#f87171", "Medium": "#fb923c", "Low": "#4ade80"}
                color = priority_colors.get(row["priority"], "#6c63ff")
                status_icon = "✅" if row["status"] == "Completed" else "⏳"

                with st.expander(f"{status_icon} {row['title']} — {row['priority']} priority"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**Description:** {row['description'] or 'N/A'}")
                        st.write(f"**Deadline:** {row['deadline']}")
                        st.write(f"**Category:** {row['category']}")
                        st.write(f"**Status:** {row['status']}")
                    with c2:
                        # Edit status
                        new_status = st.selectbox("Change Status", ["Pending", "Completed"],
                                                   index=0 if row["status"] == "Pending" else 1,
                                                   key=f"status_{row['id']}")
                        if st.button("Update", key=f"upd_{row['id']}"):
                            conn = get_connection()
                            conn.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, row["id"]))
                            conn.commit(); conn.close()
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                            conn = get_connection()
                            conn.execute("DELETE FROM tasks WHERE id=?", (row["id"],))
                            conn.commit(); conn.close()
                            st.rerun()

# ─── STUDENTS PAGE ───────────────────────────────────────────────────────────
def page_students():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">👩‍🏫 Coaching & Students</div>', unsafe_allow_html=True)

    tab_list, tab_add, tab_attend = st.tabs(["📋 Students", "➕ Add Student", "📊 Attendance"])

    with tab_add:
        with st.form("add_student"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Student Name *")
                subject = st.text_input("Subject")
                schedule = st.text_input("Class Schedule (e.g., Mon/Wed 5-6PM)")
            with c2:
                fees = st.number_input("Monthly Fees (₹)", min_value=0.0, step=100.0)
                payment_status = st.selectbox("Payment Status", ["Unpaid", "Paid", "Partial"])
            notes = st.text_area("Notes")
            if st.form_submit_button("➕ Add Student", use_container_width=True):
                if not name:
                    st.error("Student name is required.")
                else:
                    conn = get_connection()
                    conn.execute("""INSERT INTO students (user_id, name, subject, schedule, fees, payment_status, notes)
                                   VALUES (?,?,?,?,?,?,?)""",
                                 (uid, name, subject, schedule, fees, payment_status, notes))
                    conn.commit(); conn.close()
                    st.success("Student added!")
                    st.rerun()

    with tab_list:
        students = get_students(uid)
        if students.empty:
            st.info("No students added yet.")
        else:
            # Summary stats
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Students", len(students))
            c2.metric("Total Fees", f"₹{students['fees'].sum():,.0f}")
            c3.metric("Unpaid", len(students[students["payment_status"] == "Unpaid"]))

            csv = students.to_csv(index=False)
            st.download_button("⬇️ Export CSV", csv, "students.csv", "text/csv")

            search = st.text_input("🔍 Search student")
            if search:
                students = students[students["name"].str.contains(search, case=False, na=False)]

            for _, row in students.iterrows():
                pay_color = "#4ade80" if row["payment_status"] == "Paid" else ("#fb923c" if row["payment_status"] == "Partial" else "#f87171")
                with st.expander(f"👤 {row['name']} — {row['subject']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**Schedule:** {row['schedule']}")
                        st.write(f"**Fees:** ₹{row['fees']:,.0f}/month")
                        st.write(f"**Notes:** {row['notes'] or 'N/A'}")
                        st.markdown(f"**Payment:** <span style='color:{pay_color}'>{row['payment_status']}</span>", unsafe_allow_html=True)
                    with c2:
                        new_pay = st.selectbox("Update Payment", ["Unpaid", "Paid", "Partial"],
                                                index=["Unpaid", "Paid", "Partial"].index(row["payment_status"]),
                                                key=f"pay_{row['id']}")
                        if st.button("Update", key=f"upay_{row['id']}"):
                            conn = get_connection()
                            conn.execute("UPDATE students SET payment_status=? WHERE id=?", (new_pay, row["id"]))
                            conn.commit(); conn.close()
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"sdel_{row['id']}"):
                            conn = get_connection()
                            conn.execute("DELETE FROM students WHERE id=?", (row["id"],))
                            conn.commit(); conn.close()
                            st.rerun()

    with tab_attend:
        students = get_students(uid)
        if students.empty:
            st.info("Add students first.")
        else:
            st.markdown("#### Mark Attendance")
            attend_date = st.date_input("Date", value=date.today())
            student_sel = st.selectbox("Student", students["name"].tolist())
            s_row = students[students["name"] == student_sel].iloc[0]
            att_status = st.radio("Status", ["Present", "Absent", "Late"], horizontal=True)

            if st.button("✅ Mark Attendance"):
                conn = get_connection()
                conn.execute("INSERT INTO attendance (student_id, date, status) VALUES (?,?,?)",
                             (int(s_row["id"]), str(attend_date), att_status))
                conn.commit(); conn.close()
                st.success("Attendance marked!")

            # Show attendance history
            st.markdown("#### Attendance History")
            conn = get_connection()
            att_df = pd.read_sql_query("""
                SELECT a.date, s.name, a.status FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE s.user_id = ? ORDER BY a.date DESC LIMIT 30
            """, conn, params=[uid])
            conn.close()
            if not att_df.empty:
                st.dataframe(att_df, use_container_width=True, hide_index=True)
            else:
                st.info("No attendance records yet.")

# ─── COMPANIES PAGE ──────────────────────────────────────────────────────────
def page_companies():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">🏢 Companies & Clients</div>', unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📋 Companies", "➕ Add Company"])

    with tab_add:
        with st.form("add_company"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Company / Client Name *")
                contact = st.text_input("Contact Person")
            with c2:
                email = st.text_input("Email")
            notes = st.text_area("Notes")
            if st.form_submit_button("➕ Add Company", use_container_width=True):
                if not name:
                    st.error("Company name required.")
                else:
                    conn = get_connection()
                    conn.execute("INSERT INTO companies (user_id, name, contact, email, notes) VALUES (?,?,?,?,?)",
                                 (uid, name, contact, email, notes))
                    conn.commit(); conn.close()
                    st.success("Company added!")
                    st.rerun()

    with tab_list:
        companies = get_companies(uid)
        if companies.empty:
            st.info("No companies added yet.")
        else:
            for _, comp in companies.iterrows():
                tasks = get_tasks(uid, company_id=int(comp["id"]))
                completed = len(tasks[tasks["status"] == "Completed"]) if not tasks.empty else 0
                pending = len(tasks[tasks["status"] == "Pending"]) if not tasks.empty else 0

                with st.expander(f"🏢 {comp['name']}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write(f"**Contact:** {comp['contact'] or 'N/A'}")
                        st.write(f"**Email:** {comp['email'] or 'N/A'}")
                        st.write(f"**Notes:** {comp['notes'] or 'N/A'}")
                    with c2:
                        st.metric("Tasks", len(tasks))
                        st.metric("Completed", completed)
                    with c3:
                        st.metric("Pending", pending)
                        if st.button("🗑️ Delete Company", key=f"cdel_{comp['id']}"):
                            conn = get_connection()
                            conn.execute("DELETE FROM companies WHERE id=?", (comp["id"],))
                            conn.commit(); conn.close()
                            st.rerun()

                    if not tasks.empty:
                        st.markdown("**Associated Tasks:**")
                        st.dataframe(tasks[["title", "deadline", "priority", "status"]],
                                     use_container_width=True, hide_index=True)

# ─── CALENDAR PAGE ───────────────────────────────────────────────────────────
def page_calendar():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">📅 Calendar & Events</div>', unsafe_allow_html=True)

    tab_view, tab_add = st.tabs(["📅 Events", "➕ Add Event"])

    with tab_add:
        with st.form("add_event"):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Event Title *")
                event_date = st.date_input("Date", value=date.today())
            with c2:
                event_type = st.selectbox("Type", ["Meeting", "Class", "Deadline", "Personal", "Other"])
                event_time = st.text_input("Time (optional)", placeholder="e.g., 10:00 AM")
            description = st.text_area("Description")
            if st.form_submit_button("➕ Add Event", use_container_width=True):
                if not title:
                    st.error("Event title required.")
                else:
                    conn = get_connection()
                    conn.execute("""INSERT INTO events (user_id, title, description, event_date, event_time, event_type)
                                   VALUES (?,?,?,?,?,?)""",
                                 (uid, title, description, str(event_date), event_time, event_type))
                    conn.commit(); conn.close()
                    st.success("Event added!")
                    st.rerun()

    with tab_view:
        events = get_events(uid)
        tasks = get_tasks(uid)

        # Month filter
        today = date.today()
        selected_month = st.date_input("View month", value=today)
        month_start = date(selected_month.year, selected_month.month, 1)
        next_month = month_start.replace(month=month_start.month % 12 + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)

        st.markdown(f"#### Events for {month_start.strftime('%B %Y')}")

        # Show events
        if not events.empty:
            month_events = events[
                (events["event_date"] >= str(month_start)) &
                (events["event_date"] < str(next_month))
            ].sort_values("event_date")

            if month_events.empty:
                st.info("No events this month.")
            else:
                for _, row in month_events.iterrows():
                    type_icons = {"Meeting": "🤝", "Class": "📚", "Deadline": "⏰", "Personal": "👤", "Other": "📌"}
                    icon = type_icons.get(row["event_type"], "📌")
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"""
                        <div style="background:#1a1d27; border:1px solid #2a2d3e; border-radius:8px;
                             padding:0.7rem 1rem; margin:0.3rem 0;">
                            {icon} <strong>{row['title']}</strong> — {row['event_date']} {row.get('event_time', '')}
                            <span style="float:right; color:#8888aa;">{row['event_type']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        if st.button("🗑️", key=f"edel_{row['id']}"):
                            conn = get_connection()
                            conn.execute("DELETE FROM events WHERE id=?", (row["id"],))
                            conn.commit(); conn.close()
                            st.rerun()
        else:
            st.info("No events added yet.")

        # Task deadlines this month
        st.markdown("#### 📋 Task Deadlines This Month")
        if not tasks.empty:
            month_tasks = tasks[
                (tasks["deadline"] >= str(month_start)) &
                (tasks["deadline"] < str(next_month)) &
                (tasks["status"] == "Pending")
            ].sort_values("deadline")
            if not month_tasks.empty:
                st.dataframe(month_tasks[["title", "deadline", "priority", "category"]],
                             use_container_width=True, hide_index=True)
            else:
                st.info("No pending task deadlines this month.")

# ─── BUDGET PAGE ─────────────────────────────────────────────────────────────
def page_budget():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">💰 Budget Planner</div>', unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📊 Overview", "➕ Add Entry"])

    with tab_add:
        with st.form("add_budget"):
            c1, c2 = st.columns(2)
            with c1:
                btype = st.selectbox("Type", ["Income", "Expense"])
                amount = st.number_input("Amount (₹) *", min_value=0.0, step=100.0)
            with c2:
                category = st.selectbox("Category", ["Salary", "Freelance", "Coaching", "Investment", "Food", "Transport", "Bills", "Personal", "Other"])
                bdate = st.date_input("Date", value=date.today())
            description = st.text_input("Description (optional)")
            if st.form_submit_button("➕ Add Entry", use_container_width=True):
                if amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    conn = get_connection()
                    conn.execute("""INSERT INTO budget (user_id, type, amount, category, description, date)
                                   VALUES (?,?,?,?,?,?)""",
                                 (uid, btype, amount, category, description, str(bdate)))
                    conn.commit(); conn.close()
                    st.success("Entry added!")
                    st.rerun()

    with tab_list:
        budget = get_budget(uid)
        if budget.empty:
            st.info("No budget entries yet. Add your first income or expense!")
            return

        income = budget[budget["type"] == "Income"]["amount"].sum()
        expenses = budget[budget["type"] == "Expense"]["amount"].sum()
        balance = income - expenses

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Total Income", f"₹{income:,.2f}")
        c2.metric("💸 Total Expenses", f"₹{expenses:,.2f}")
        c3.metric("🏦 Balance", f"₹{balance:,.2f}", delta="Positive" if balance >= 0 else "Negative")

        # Month filter
        st.divider()
        months = sorted(budget["date"].str[:7].unique(), reverse=True)
        sel_month = st.selectbox("Filter by Month", ["All"] + list(months))

        display = budget if sel_month == "All" else budget[budget["date"].str[:7] == sel_month]
        display = display.sort_values("date", ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📊 Expense Breakdown")
            exp_data = display[display["type"] == "Expense"].groupby("category")["amount"].sum().reset_index()
            if not exp_data.empty:
                try:
                    import plotly.express as px
                    fig = px.pie(exp_data, names="category", values="amount",
                                 color_discrete_sequence=px.colors.qualitative.Set3,
                                 hole=0.4)
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#e8e8f0",
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.dataframe(exp_data, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Income Trend")
            inc_data = display[display["type"] == "Income"].copy()
            if not inc_data.empty:
                inc_data["date"] = pd.to_datetime(inc_data["date"])
                inc_trend = inc_data.groupby(inc_data["date"].dt.to_period("M"))["amount"].sum().reset_index()
                inc_trend["date"] = inc_trend["date"].astype(str)
                try:
                    import plotly.express as px
                    fig2 = px.line(inc_trend, x="date", y="amount",
                                   markers=True, color_discrete_sequence=["#6c63ff"])
                    fig2.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#e8e8f0",
                        xaxis=dict(gridcolor="#2a2d3e"),
                        yaxis=dict(gridcolor="#2a2d3e"),
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                except ImportError:
                    st.dataframe(inc_trend, use_container_width=True)

        st.markdown("#### 📋 Transactions")
        csv = display.to_csv(index=False)
        st.download_button("⬇️ Export CSV", csv, "budget.csv", "text/csv")
        st.dataframe(display[["date", "type", "category", "amount", "description"]],
                     use_container_width=True, hide_index=True)

# ─── DAILY PLANNER PAGE ──────────────────────────────────────────────────────
def page_planner():
    uid = st.session_state.user_id
    today = str(date.today())

    st.markdown('<div class="page-title">📌 Daily Planner</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">Plan for {date.today().strftime("%A, %B %d")}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.form("add_note"):
            note = st.text_input("Add a quick task/note", placeholder="e.g., Review project proposal...")
            if st.form_submit_button("➕ Add", use_container_width=True):
                if note:
                    conn = get_connection()
                    conn.execute("INSERT INTO daily_planner (user_id, note, plan_date) VALUES (?,?,?)",
                                 (uid, note, today))
                    conn.commit(); conn.close()
                    st.rerun()

        planner_items = get_planner(uid, today)
        if planner_items.empty:
            st.info("Your day is clear! Add your first task above. 🌅")
        else:
            done_count = len(planner_items[planner_items["completed"] == 1])
            st.markdown(f"**Progress: {done_count}/{len(planner_items)} completed**")
            st.progress(done_count / len(planner_items) if len(planner_items) > 0 else 0)

            for _, row in planner_items.iterrows():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    style = "text-decoration: line-through; color: #8888aa;" if row["completed"] else ""
                    st.markdown(f"<div style='{style}; padding: 0.4rem 0;'>{'✅' if row['completed'] else '⬜'} {row['note']}</div>", unsafe_allow_html=True)
                with c2:
                    label = "Undo" if row["completed"] else "Done"
                    if st.button(label, key=f"ptoggle_{row['id']}"):
                        new_val = 0 if row["completed"] else 1
                        conn = get_connection()
                        conn.execute("UPDATE daily_planner SET completed=? WHERE id=?", (new_val, row["id"]))
                        conn.commit(); conn.close()
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"pdel_{row['id']}"):
                        conn = get_connection()
                        conn.execute("DELETE FROM daily_planner WHERE id=?", (row["id"],))
                        conn.commit(); conn.close()
                        st.rerun()

    with col2:
        st.markdown("#### 📋 Pending Tasks Today")
        tasks = get_tasks(uid, status="Pending")
        today_tasks = tasks[tasks["deadline"] == today] if not tasks.empty else pd.DataFrame()
        if today_tasks.empty:
            st.info("No tasks due today.")
        else:
            for _, row in today_tasks.iterrows():
                st.markdown(f"⏳ {row['title']}")

# ─── SETTINGS PAGE ───────────────────────────────────────────────────────────
def page_settings():
    uid = st.session_state.user_id
    st.markdown('<div class="page-title">⚙️ Settings</div>', unsafe_allow_html=True)

    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()

    if user:
        st.markdown("#### 👤 Profile")
        with st.form("update_profile"):
            full_name = st.text_input("Full Name", value=user[3] or "")
            email = st.text_input("Email", value=user[4] or "")
            if st.form_submit_button("💾 Update Profile"):
                conn = get_connection()
                conn.execute("UPDATE users SET full_name=?, email=? WHERE id=?", (full_name, email, uid))
                conn.commit(); conn.close()
                st.session_state.user_name = full_name
                st.success("Profile updated!")

        st.divider()
        st.markdown("#### 🔒 Change Password")
        with st.form("change_pw"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("🔒 Update Password"):
                if hash_password(old_pw) != user[2]:
                    st.error("Current password is incorrect.")
                elif new_pw != confirm_pw:
                    st.error("New passwords don't match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    conn = get_connection()
                    conn.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_pw), uid))
                    conn.commit(); conn.close()
                    st.success("Password updated!")

        st.divider()
        st.markdown("#### 🗂️ Data Management")
        col1, col2 = st.columns(2)
        with col1:
            # Export all data
            conn = get_connection()
            tasks_df = pd.read_sql_query("SELECT * FROM tasks WHERE user_id=?", conn, params=[uid])
            students_df = pd.read_sql_query("SELECT * FROM students WHERE user_id=?", conn, params=[uid])
            budget_df = pd.read_sql_query("SELECT * FROM budget WHERE user_id=?", conn, params=[uid])
            conn.close()

            all_data = f"=== TASKS ===\n{tasks_df.to_csv(index=False)}\n\n=== STUDENTS ===\n{students_df.to_csv(index=False)}\n\n=== BUDGET ===\n{budget_df.to_csv(index=False)}"
            st.download_button("⬇️ Export All Data (CSV)", all_data, "proflow_export.csv", "text/csv")

# ─── MAIN APP ────────────────────────────────────────────────────────────────
def main():
    init_db()
    load_css()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        auth_page()
        return

    render_sidebar()

    page = st.session_state.get("page", "dashboard")
    pages = {
        "dashboard": page_dashboard,
        "tasks": page_tasks,
        "students": page_students,
        "companies": page_companies,
        "calendar": page_calendar,
        "budget": page_budget,
        "planner": page_planner,
        "settings": page_settings
    }

    pages.get(page, page_dashboard)()

if __name__ == "__main__":
    main()
