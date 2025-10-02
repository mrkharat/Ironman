# coach_app_admin.py
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
import plotly.express as px

# ---------------- CONFIG ----------------
DB_PATH = Path("ironman_coach.db")
APP_TITLE = "Ironman 2028 — Coach Planner (Admin + Per-user Adjustments)"
USERS = ["Mayur", "Friend_Boy", "Friend_Girl"]  # change as needed
ADMIN_PASS = "ironadmin2025"  # change this to secure admin access

PLAN_START = pd.Timestamp("2025-10-01")
PLAN_END = pd.Timestamp("2028-07-31")
WEEK_FREQ = "W-MON"

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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_adjustments (
        user TEXT PRIMARY KEY,
        run_multiplier REAL DEFAULT 1.0,
        swim_multiplier REAL DEFAULT 1.0,
        bike_multiplier REAL DEFAULT 1.0,
        strength_multiplier REAL DEFAULT 1.0
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()

def seed_plan(conn):
    cur = conn.cursor()
    df_weeks = pd.date_range(start=PLAN_START, end=PLAN_END, freq=WEEK_FREQ).to_pydatetime().tolist()
    rows = []
    for ws in df_weeks:
        year = ws.year
        # Default phase & targets by year
        if ws < pd.Timestamp("2026-01-01"):
            phase = "Base (Oct-Dec 2025)"
            run_sessions = 3
            long_run_km = 12 if ws < pd.Timestamp("2025-12-01") else 18
            swim_sessions = 2
            swim_total_m = 800
            bike_sessions = 0
            long_ride_km = 0
            strength_sessions = 1
            nutrition = "Establish routine: 3 meals + 2 snacks; protein focus"
        elif year == 2026:
            phase = "Build Endurance (70.3 prep)"
            run_sessions = 4
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
            nutrition = "Refine hydration & race nutrition"
        else:
            phase = "Peak Ironman Prep (2028)"
            run_sessions = 4
            long_run_km = 36 if ws < pd.Timestamp("2028-06-01") else 20
            swim_sessions = 3
            swim_total_m = 3000 if ws < pd.Timestamp("2028-05-01") else 3800
            bike_sessions = 3
            long_ride_km = 140 if ws < pd.Timestamp("2028-06-01") else 60
            strength_sessions = 1
            nutrition = "Race simulations; taper & carb-load before race"
        week_key = ws.strftime("%Y-%m-%d")
        rows.append((week_key, phase, run_sessions, long_run_km, swim_sessions, swim_total_m, bike_sessions, long_ride_km, strength_sessions, nutrition))
    # Insert or ignore
    for r in rows:
        try:
            cur.execute("""
            INSERT INTO weeks (week_start, phase, run_sessions, long_run_km, swim_sessions, swim_total_m, bike_sessions, long_ride_km, strength_sessions, nutrition_focus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, r)
        except sqlite3.IntegrityError:
            continue
    # seed user adjustments if empty
    cur.execute("SELECT COUNT(*) FROM user_adjustments")
    if cur.fetchone()[0] == 0:
        for u in USERS:
            cur.execute("INSERT INTO user_adjustments (user, run_multiplier, swim_multiplier, bike_multiplier, strength_multiplier) VALUES (?,1,1,1,1)", (u,))
    # seed default race date meta if not exists
    cur.execute("SELECT value FROM meta WHERE key='race_date'")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO meta (key, value) VALUES ('race_date', '2028-07-15')")
    conn.commit()

# Data access
def get_week_plan(conn):
    df = pd.read_sql("SELECT * FROM weeks ORDER BY week_start", conn)
    df['week_start_dt'] = pd.to_datetime(df['week_start'])
    return df

def upsert_week(conn, week_key, data: dict):
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO weeks (week_start, phase, run_sessions, long_run_km, swim_sessions, swim_total_m, bike_sessions, long_ride_km, strength_sessions, nutrition_focus)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(week_start) DO UPDATE SET
      phase=excluded.phase,
      run_sessions=excluded.run_sessions,
      long_run_km=excluded.long_run_km,
      swim_sessions=excluded.swim_sessions,
      swim_total_m=excluded.swim_total_m,
      bike_sessions=excluded.bike_sessions,
      long_ride_km=excluded.long_ride_km,
      strength_sessions=excluded.strength_sessions,
      nutrition_focus=excluded.nutrition_focus
    """, (week_key, data['phase'], data['run_sessions'], data['long_run_km'], data['swim_sessions'], data['swim_total_m'], data['bike_sessions'], data['long_ride_km'], data['strength_sessions'], data['nutrition_focus']))
    conn.commit()

def save_task(conn, user, week_start, task_key, done):
    ts = datetime.utcnow().isoformat()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks_done WHERE user=? AND week_start=? AND task_key=?", (user, week_start, task_key))
    cur.execute("INSERT INTO tasks_done (user, week_start, task_key, done, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user, week_start, task_key, int(done), ts))
    conn.commit()

def get_tasks_done(conn):
    return pd.read_sql("SELECT * FROM tasks_done ORDER BY timestamp DESC", conn)

def get_user_adjustments(conn):
    return pd.read_sql("SELECT * FROM user_adjustments", conn)

def update_user_adjustment(conn, user, run_m, swim_m, bike_m, str_m):
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO user_adjustments (user, run_multiplier, swim_multiplier, bike_multiplier, strength_multiplier)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user) DO UPDATE SET
      run_multiplier=excluded.run_multiplier,
      swim_multiplier=excluded.swim_multiplier,
      bike_multiplier=excluded.bike_multiplier,
      strength_multiplier=excluded.strength_multiplier
    """, (user, run_m, swim_m, bike_m, str_m))
    conn.commit()

def get_meta(conn, key):
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key=?", (key,))
    r = cur.fetchone()
    return r[0] if r else None

def set_meta(conn, key, value):
    cur = conn.cursor()
    cur.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
    conn.commit()

# ---------------- UI & logic ----------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Coach-style weekly plan (Oct 2025 → Jul 2028) with Admin editor and per-user adjustments.")

# init DB and seed
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
init_db(conn)
seed_plan(conn)

# Sidebar user selection and admin toggle
st.sidebar.header("User")
user = st.sidebar.selectbox("I am:", USERS)

st.sidebar.markdown("---")
st.sidebar.header("User adjustments")
ua_df = get_user_adjustments(conn)
user_row = ua_df[ua_df['user']==user].iloc[0]
run_m = st.sidebar.number_input("Run multiplier", min_value=0.5, max_value=1.5, value=float(user_row['run_multiplier']), step=0.05, format="%.2f", key="runmul")
swim_m = st.sidebar.number_input("Swim multiplier", min_value=0.5, max_value=1.5, value=float(user_row['swim_multiplier']), step=0.05, format="%.2f", key="swimmul")
bike_m = st.sidebar.number_input("Bike multiplier", min_value=0.5, max_value=1.5, value=float(user_row['bike_multiplier']), step=0.05, format="%.2f", key="bikemul")
str_m = st.sidebar.number_input("Strength multiplier", min_value=0.5, max_value=1.5, value=float(user_row['strength_multiplier']), step=0.05, format="%.2f", key="strmul")
if st.sidebar.button("Save my adjustment"):
    update_user_adjustment(conn, user, run_m, swim_m, bike_m, str_m)
    st.sidebar.success("Saved")

st.sidebar.markdown("---")
if st.sidebar.checkbox("Show admin editor"):
    admin_input = st.sidebar.text_input("Enter admin passcode", type="password")
    if admin_input == ADMIN_PASS:
        st.sidebar.success("Admin unlocked")
        st.sidebar.markdown("**Admin actions**")
        if st.sidebar.button("Reset seeded plan (re-seed weeks)"):
            seed_plan(conn)
            st.sidebar.success("Plan seeded (existing weeks preserved)")
        # change race date
        race_date_val = get_meta(conn, "race_date")
        new_date = st.sidebar.date_input("Race date", value=pd.to_datetime(race_date_val).date())
        if st.sidebar.button("Save race date"):
            set_meta(conn, "race_date", new_date.isoformat())
            st.sidebar.success("Race date updated")
    else:
        if admin_input:
            st.sidebar.error("Invalid passcode")

# Main layout
df_weeks = get_week_plan(conn)
# choose week
today = pd.Timestamp.today().normalize()
# default to current week index logic
week_keys = df_weeks['week_start'].tolist()
closest_idx = 0
for i, wk in enumerate(week_keys):
    if pd.Timestamp(wk) <= today:
        closest_idx = i
selected_week = st.selectbox("Select week (Mon start)", week_keys, index=closest_idx, format_func=lambda x: pd.to_datetime(x).strftime("%d %b %Y"))

# fetch week row and apply user multipliers
row = df_weeks[df_weeks['week_start'] == selected_week].iloc[0]
# apply multipliers
run_sessions_user = max(0, round(row['run_sessions'] * run_m))
long_run_km_user = max(0, round(row['long_run_km'] * run_m))
swim_sessions_user = max(0, round(row['swim_sessions'] * swim_m))
swim_total_m_user = max(0, int(row['swim_total_m'] * swim_m))
bike_sessions_user = max(0, round(row['bike_sessions'] * bike_m))
long_ride_km_user = max(0, round(row['long_ride_km'] * bike_m))
strength_sessions_user = max(0, round(row['strength_sessions'] * str_m))
nutrition_focus = row['nutrition_focus']

st.header(f"Week starting {pd.to_datetime(selected_week).strftime('%d %b %Y')} — {row['phase']}")
st.write(f"**Your personalized targets** (multipliers applied):")
st.write(f"- Run sessions: **{run_sessions_user}** (Long run target: **{long_run_km_user} km**)")
st.write(f"- Swim sessions: **{swim_sessions_user}** (Total target: **{swim_total_m_user} m**)")
st.write(f"- Bike sessions: **{bike_sessions_user}** (Long ride target: **{long_ride_km_user} km**)")
st.write(f"- Strength sessions: **{strength_sessions_user}**")
st.write(f"- Nutrition focus: **{nutrition_focus}**")
st.write("---")

# Build tasks for the user for the selected week
tasks = []
for i in range(1, run_sessions_user+1):
    tasks.append((f"run_{i}", f"Run session {i}"))
if long_run_km_user > 0:
    tasks.append(("long_run", f"Long run — {long_run_km_user} km"))
for i in range(1, swim_sessions_user+1):
    tasks.append((f"swim_{i}", f"Swim session {i} (~{int(swim_total_m_user/swim_sessions_user) if swim_sessions_user else 0} m)"))
for i in range(1, bike_sessions_user+1):
    tasks.append((f"bike_{i}", f"Bike session {i}"))
if long_ride_km_user > 0:
    tasks.append(("long_ride", f"Long ride — {long_ride_km_user} km"))
for i in range(1, strength_sessions_user+1):
    tasks.append((f"strength_{i}", "Strength / core session"))
tasks.append(("nutrition", f"Follow nutrition focus: {nutrition_focus}"))

# Load existing done state and present checkboxes
existing = pd.read_sql("SELECT task_key, done FROM tasks_done WHERE user=? AND week_start=?", conn, params=(user, selected_week))
done_map = {r['task_key']: bool(r['done']) for r in existing.to_dict('records')}
st.subheader("Mark tasks done (tick when completed)")
for tkey, tdesc in tasks:
    checked = done_map.get(tkey, False)
    new_val = st.checkbox(tdesc, value=checked, key=f"{user}_{selected_week}_{tkey}")
    if new_val != checked:
        save_task(conn, user, selected_week, tkey, new_val)
        done_map[tkey] = new_val

# weekly summary
total_tasks = len(tasks)
done_count = sum(1 for v in done_map.values() if v)
pct = int((done_count/total_tasks)*100) if total_tasks>0 else 0
st.metric("Week Completion", f"{done_count}/{total_tasks}", delta=f"{pct}%")

# quick admin editor section (in-page) if admin unlocked
st.write("---")
admin_unlocked = False
if st.checkbox("Open admin week editor (requires passcode)"):
    admin_input = st.text_input("Admin passcode (in-page)", type="password")
    if admin_input == ADMIN_PASS:
        admin_unlocked = True
    else:
        if admin_input:
            st.error("Wrong passcode")
if admin_unlocked:
    st.markdown("### Admin: Edit selected week")
    with st.form("edit_week_form"):
        phase_in = st.text_input("Phase", value=row['phase'])
        run_sessions_in = st.number_input("Run sessions", min_value=0, max_value=10, value=int(row['run_sessions']))
        long_run_km_in = st.number_input("Long run km", min_value=0, max_value=100, value=int(row['long_run_km']))
        swim_sessions_in = st.number_input("Swim sessions", min_value=0, max_value=10, value=int(row['swim_sessions']))
        swim_total_m_in = st.number_input("Swim total m", min_value=0, max_value=10000, value=int(row['swim_total_m']))
        bike_sessions_in = st.number_input("Bike sessions", min_value=0, max_value=10, value=int(row['bike_sessions']))
        long_ride_km_in = st.number_input("Long ride km", min_value=0, max_value=300, value=int(row['long_ride_km']))
        strength_sessions_in = st.number_input("Strength sessions", min_value=0, max_value=7, value=int(row['strength_sessions']))
        nutrition_in = st.text_area("Nutrition focus", value=row['nutrition_focus'])
        submitted = st.form_submit_button("Save week changes")
        if submitted:
            upsert_week(conn, selected_week, {
                'phase': phase_in,
                'run_sessions': run_sessions_in,
                'long_run_km': long_run_km_in,
                'swim_sessions': swim_sessions_in,
                'swim_total_m': swim_total_m_in,
                'bike_sessions': bike_sessions_in,
                'long_ride_km': long_ride_km_in,
                'strength_sessions': strength_sessions_in,
                'nutrition_focus': nutrition_in
            })
            st.success("Week updated. Reload the app to refresh data (or navigate weeks).")

# Team progress summary
st.write("---")
st.header("Team Progress Snapshot")
df_all_weeks = get_week_plan(conn)
# compute expected tasks total across plan per user with their multipliers
ua = pd.read_sql("SELECT * FROM user_adjustments", conn).set_index('user')
summary = []
for u in USERS:
    urow = ua.loc[u]
    total_expected = 0
    for _, w in df_all_weeks.iterrows():
        t_expected = int(round(w['run_sessions'] * urow['run_multiplier'])) + (1 if round(w['long_run_km'] * urow['run_multiplier'])>0 else 0) + int(round(w['swim_sessions'] * urow['swim_multiplier'])) + int(round(w['bike_sessions'] * urow['bike_multiplier'])) + (1 if round(w['long_ride_km'] * urow['bike_multiplier'])>0 else 0) + int(round(w['strength_sessions'] * urow['strength_multiplier'])) + 1
        total_expected += t_expected
    done_count = pd.read_sql("SELECT count(*) as c FROM tasks_done WHERE user=?", conn, params=(u,)).iloc[0]['c']
    pct = int((done_count/total_expected)*100) if total_expected>0 else 0
    summary.append({'user':u, 'done':int(done_count), 'expected':int(total_expected), 'pct':pct})
df_summary = pd.DataFrame(summary)
st.dataframe(df_summary[['user','done','expected','pct']].rename(columns={'pct':'Compliance %'}))

fig = px.bar(df_summary, x='user', y='pct', range_y=[0,100], title="Overall Compliance %")
st.plotly_chart(fig, use_container_width=True)

# recent activity
st.subheader("Recent completions")
df_tasks = get_tasks_done(conn)
if not df_tasks.empty:
    df_tasks['week'] = pd.to_datetime(df_tasks['week_start']).dt.strftime("%d %b %Y")
    st.dataframe(df_tasks[['user','week','task_key','done','timestamp']].head(100))
else:
    st.info("No task completions yet.")

# export buttons
st.write("---")
if st.button("Export week plan CSV"):
    st.download_button("Download week_plan.csv", df_all_weeks.to_csv(index=False).encode('utf-8'), file_name="week_plan.csv")
if st.button("Export tasks CSV"):
    st.download_button("Download tasks.csv", pd.read_sql("SELECT * FROM tasks_done", conn).to_csv(index=False).encode('utf-8'), file_name="tasks.csv")
if st.button("Export adjustments CSV"):
    st.download_button("Download adjustments.csv", pd.read_sql("SELECT * FROM user_adjustments", conn).to_csv(index=False).encode('utf-8'), file_name="adjustments.csv")

# race countdown
race_date_str = get_meta(conn, "race_date")
race_date = pd.to_datetime(race_date_str).date() if race_date_str else date(2028,7,15)
days_left = (race_date - date.today()).days
st.sidebar.markdown(f"**Race date:** {race_date.isoformat()}  \n**Days left:** {days_left}")

# Close DB
conn.close()
