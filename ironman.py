# coach_app.py
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
import plotly.express as px

# ---------------- CONFIG ----------------
DB_PATH = Path("ironman_coach.db")
APP_TITLE = "Ironman 2028 — Coach Planner (Oct 2025 → Jul 2028)"
USERS = ["Mayur", "Friend_Boy", "Friend_Girl"]  # change names if you want

PLAN_START = pd.Timestamp("2025-10-01")
PLAN_END = pd.Timestamp("2028-07-31")
WEEK_FREQ = "W-MON"  # weeks start Monday

# ---------------- DB helpers ----------------
def init_db(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weeks (
        week_start TEXT PRIMARY KEY,
        phase TEXT,
        run_sessions INTEGER,
        long_run_km REAL,
        swim_sessions INTEGER,
        swim_total_m REAL,
        bike_sessions INTEGER,
        long_ride_km REAL,
        strength_sessions INTEGER,
        nutrition_focus TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks_done (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        week_start TEXT,
        task_key TEXT,
        done INTEGER,
        timestamp TEXT
    );
    """)
    conn.commit()

def seed_plan(conn):
    cur = conn.cursor()
    df_weeks = pd.date_range(start=PLAN_START, end=PLAN_END, freq=WEEK_FREQ).to_pydatetime().tolist()
    rows = []
    for ws in df_weeks:
        month = ws.month
        year = ws.year
        # Decide phase
        if ws < pd.Timestamp("2026-01-01"):
            phase = "Base (Oct-Dec 2025)"
            run_sessions = 3
            long_run_km = 12 if ws < pd.Timestamp("2025-12-01") else 18
            swim_sessions = 2
            swim_total_m = 800
            bike_sessions = 0  # start cycling in Dec 2025 but light
            long_ride_km = 0
            strength_sessions = 1
            nutrition = "Build routine: 3 meals + 2 snacks; protein focus"
        elif year == 2026:
            phase = "Build Endurance (70.3 prep 2026)"
            run_sessions = 4
            # gradually increase long run during key months
            if ws < pd.Timestamp("2026-04-01"):
                long_run_km = 18
            elif ws < pd.Timestamp("2026-08-01"):
                long_run_km = 24
            else:
                long_run_km = 28
            swim_sessions = 3
            swim_total_m = 1500
            bike_sessions = 2
            long_ride_km = 60 if ws.month < 6 else 80
            strength_sessions = 1
            nutrition = "Practice race fueling; test gels & electrolytes"
        elif year == 2027:
            phase = "Consolidate & Strengthen (2027)"
            run_sessions = 4
            long_run_km = 30
            swim_sessions = 3
            swim_total_m = 2000
            bike_sessions = 2
            long_ride_km = 100
            strength_sessions = 1
            nutrition = "Refine hydration & race nutrition; stable weight"
        else:
            # 2028 Jan - Jul Peak
            phase = "Peak Ironman Prep (2028)"
            run_sessions = 4
            long_run_km = 36 if ws < pd.Timestamp("2028-06-01") else 20  # taper in June-July
            swim_sessions = 3
            swim_total_m = 3000 if ws < pd.Timestamp("2028-05-01") else 3800  # build then simulate
            bike_sessions = 3
            long_ride_km = 140 if ws < pd.Timestamp("2028-06-01") else 60
            strength_sessions = 1
            nutrition = "Race simulations; taper & carb-load before race"
        week_key = ws.strftime("%Y-%m-%d")
        rows.append((week_key, phase, run_sessions, long_run_km, swim_sessions, swim_total_m, bike_sessions, long_ride_km, strength_sessions, nutrition))
    # Insert ignoring existing
    for r in rows:
        try:
            cur.execute("""
            INSERT INTO weeks (week_start, phase, run_sessions, long_run_km, swim_sessions, swim_total_m, bike_sessions, long_ride_km, strength_sessions, nutrition_focus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, r)
        except sqlite3.IntegrityError:
            continue
    conn.commit()

def get_week_plan(conn):
    df = pd.read_sql("SELECT * FROM weeks ORDER BY week_start", conn)
    df['week_start_dt'] = pd.to_datetime(df['week_start'])
    return df

def save_task(conn, user, week_start, task_key, done):
    ts = datetime.utcnow().isoformat()
    cur = conn.cursor()
    # delete any previous entry
    cur.execute("DELETE FROM tasks_done WHERE user=? AND week_start=? AND task_key=?", (user, week_start, task_key))
    cur.execute("INSERT INTO tasks_done (user, week_start, task_key, done, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user, week_start, task_key, int(done), ts))
    conn.commit()

def get_user_tasks(conn, user):
    df = pd.read_sql("SELECT * FROM tasks_done WHERE user=? ORDER BY week_start DESC, id DESC", conn, params=(user,))
    return df

def get_tasks_for_week(conn, week_start):
    df = pd.read_sql("SELECT * FROM tasks_done WHERE week_start=?", conn, params=(week_start,))
    return df

# ---------------- UI & logic ----------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.markdown("Coach-style weekly plan from **Oct 2025 → Jul 2028**. Each user sees the week's tasks and only needs to tap **Done** for each item. Progress auto-calculates.")

# DB init
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
init_db(conn)
seed_plan(conn)

# Sidebar: user select and week navigation
st.sidebar.header("User")
user = st.sidebar.selectbox("I am:", USERS)

st.sidebar.markdown("---")
st.sidebar.header("Navigate Weeks")
df_weeks = get_week_plan(conn)
week_keys = df_weeks['week_start'].tolist()
# default to current week if within plan, else next upcoming
today = pd.Timestamp.today().normalize()
closest_week = None
for wk in week_keys:
    if pd.Timestamp(wk) <= today:
        closest_week = wk
# if none found, use first week
default_idx = week_keys.index(closest_week) if closest_week in week_keys else 0
selected_week = st.sidebar.selectbox("Select week (Mon start)", week_keys, index=default_idx, format_func=lambda x: pd.to_datetime(x).strftime("%d %b %Y"))

st.sidebar.markdown("---")
if st.sidebar.button("Show Team Progress"):
    st.experimental_set_query_params(view="team")

# Main layout: left - week tasks, right - progress & team
col1, col2 = st.columns([2,1])

with col1:
    st.header("This Week's Plan")
    # fetch selected week plan
    row = df_weeks[df_weeks['week_start']==selected_week].iloc[0]
    st.subheader(f"{pd.to_datetime(row['week_start']).strftime('%d %b %Y')} — {row['phase']}")
    st.markdown("**Weekly Targets**")
    st.write(f"- Run sessions: **{row['run_sessions']}**  (Long run target: **{row['long_run_km']} km**)")
    st.write(f"- Swim sessions: **{row['swim_sessions']}**  (Total target: **{int(row['swim_total_m'])} m**)")
    st.write(f"- Bike sessions: **{row['bike_sessions']}**  (Long ride target: **{row['long_ride_km']} km**)")
    st.write(f"- Strength sessions: **{row['strength_sessions']}**")
    st.write(f"- Nutrition focus: **{row['nutrition_focus']}**")
    st.write("---")

    # Build tasks for the week as checklist items (simple granular tasks)
    tasks = []
    # run tasks: run_sessions small runs + 1 long run
    for i in range(1, int(row['run_sessions'])+1):
        tasks.append(("run_{}".format(i), f"Run session {i} (easy / interval / tempo as scheduled)"))
    if row['long_run_km'] > 0:
        tasks.append(("long_run", f"Long run — {int(row['long_run_km'])} km"))
    # swim tasks
    for i in range(1, int(row['swim_sessions'])+1):
        tasks.append((f"swim_{i}", f"Swim session {i} (target ~{int(row['swim_total_m']/row['swim_sessions'])} m)"))
    # bike tasks
    for i in range(1, int(row['bike_sessions'])+1):
        tasks.append((f"bike_{i}", f"Bike session {i}"))
    if row['long_ride_km'] > 0:
        tasks.append(("long_ride", f"Long ride — {int(row['long_ride_km'])} km"))
    # strength
    for i in range(1, int(row['strength_sessions'])+1):
        tasks.append((f"strength_{i}", "Strength / core session"))
    # nutrition
    tasks.append(("nutrition", f"Follow nutrition focus: {row['nutrition_focus']}"))

    # fetch existing done tasks for this user+week
    user_tasks_df = pd.read_sql("SELECT task_key, done FROM tasks_done WHERE user=? AND week_start=?", conn, params=(user, selected_week))
    done_map = {r['task_key']: bool(r['done']) for r in user_tasks_df.to_dict('records')}

    st.markdown("**Mark tasks done for this week**")
    cols = st.columns(1)
    for tkey, tdesc in tasks:
        checked = done_map.get(tkey, False)
        new_val = st.checkbox(tdesc, value=checked, key=f"{user}_{selected_week}_{tkey}")
        # if changed, save
        if new_val != checked:
            save_task(conn, user, selected_week, tkey, new_val)
            done_map[tkey] = new_val

    st.write("---")
    # Quick weekly summary
    total_tasks = len(tasks)
    done_count = sum(1 for v in done_map.values() if v)
    pct = int((done_count/total_tasks)*100) if total_tasks>0 else 0
    st.metric("Week Completion", f"{done_count}/{total_tasks}", delta=f"{pct}%")

    # Option to mark retrospective weeks quickly (useful if catching up)
    st.markdown("**Quick actions**")
    if st.button("Mark all tasks done for this week"):
        for tkey, _ in tasks:
            save_task(conn, user, selected_week, tkey, True)
        st.experimental_rerun()
    if st.button("Clear all tasks for this week"):
        for tkey, _ in tasks:
            save_task(conn, user, selected_week, tkey, False)
        st.experimental_rerun()

with col2:
    st.header("Progress & Team")
    # Show user-specific progress across all weeks
    df_all_tasks = pd.read_sql("SELECT week_start, user, task_key, done FROM tasks_done", conn)
    if df_all_tasks.empty:
        st.info("No task completions logged yet. Mark tasks from the left panel.")
    else:
        # compute per-user completion %
        users_summary = []
        for u in USERS:
            # for weeks in plan, count expected tasks per week
            total_expected = 0
            total_done = 0
            for idx, wrow in df_weeks.iterrows():
                wk = wrow['week_start']
                # compute expected tasks for that week
                tasks_expected = int(wrow['run_sessions']) + (1 if wrow['long_run_km']>0 else 0) + int(wrow['swim_sessions']) + (1 if wrow['bike_sessions']>0 else 0) + (1 if wrow['long_ride_km']>0 else 0) + int(wrow['strength_sessions']) + 1 # nutrition
                total_expected += tasks_expected
                # done count from DB
                done_rows = df_all_tasks[(df_all_tasks['user']==u) & (df_all_tasks['week_start']==wk)]
                total_done += done_rows['done'].sum()
            pct = int((total_done/total_expected)*100) if total_expected>0 else 0
            users_summary.append({"user":u, "done": int(total_done), "expected": int(total_expected), "pct": pct})
        df_users = pd.DataFrame(users_summary)
        st.subheader("Team Consistency")
        st.dataframe(df_users[['user','done','expected','pct']].rename(columns={'pct':'Compliance %'}), height=180)
        # leaderboard
        fig = px.bar(df_users, x='user', y='pct', title="Compliance %", range_y=[0,100])
        st.plotly_chart(fig, use_container_width=True)

    st.write("---")
    # Show upcoming race countdown
    race_date = pd.Timestamp("2028-07-15")  # placeholder; adjust as official date arrives
    days_left = (race_date - pd.Timestamp.today()).days
    st.metric("Days until Ironman Hamburg (approx)", days_left)

    st.write("---")
    st.subheader("Recent activity (team)")
    df_recent = pd.read_sql("SELECT user, week_start, task_key, done, timestamp FROM tasks_done ORDER BY timestamp DESC LIMIT 50", conn)
    if not df_recent.empty:
        df_recent['week'] = pd.to_datetime(df_recent['week_start']).dt.strftime("%d %b %Y")
        st.dataframe(df_recent[['user','week','task_key','done','timestamp']])
    else:
        st.info("No recent activity logged.")

# Footer: export / admin
st.markdown("---")
st.write("Admin & export")
if st.button("Export plan (CSV)"):
    df_export = get_week_plan(conn)
    st.download_button("Download plan.csv", df_export.to_csv(index=False).encode('utf-8'), file_name="week_plan.csv")

if st.button("Export tasks done (CSV)"):
    df_tasks = pd.read_sql("SELECT * FROM tasks_done ORDER BY week_start, user", conn)
    st.download_button("Download tasks.csv", df_tasks.to_csv(index=False).encode('utf-8'), file_name="tasks_done.csv")

# Close DB
conn.close()
