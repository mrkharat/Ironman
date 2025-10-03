# app.py — Full 3-year Ironman Training Coach (Oct 1, 2025 -> Jul 31, 2028)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
import requests
import os

# ---------------- Page config ----------------
st.set_page_config(page_title="Ironman 3-Year Coach", layout="wide", initial_sidebar_state="expanded")

# ---------------- Constants ----------------
ATHLETES = ["Mayur", "Sudeep", "Vaishali"]
START_DATE = pd.Timestamp("2025-10-01")
END_DATE = pd.Timestamp("2028-07-31")
IRONMAN_TARGET = pd.Timestamp("2028-07-14")  # Hamburg example; change if needed

DATA_DIR = "/mnt/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# CSV paths (persistent storage)
DIST_LOG_CSV = os.path.join(DATA_DIR, "ironman_distance_log.csv")
NUTRITION_LOG_CSV = os.path.join(DATA_DIR, "ironman_nutrition_log.csv")
SLEEP_LOG_CSV = os.path.join(DATA_DIR, "ironman_sleep_log.csv")
PROGRESS_LOG_CSV = os.path.join(DATA_DIR, "ironman_progress_log.csv")

# ---------------- Helper: safe CSV load/save ----------------
def safe_load_csv(path, cols=None):
    try:
        df = pd.read_csv(path)
        return df
    except:
        if cols:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame()

def safe_save_csv(path, df):
    df.to_csv(path, index=False)

# ---------------- Generate Weeks list ----------------
weeks = pd.date_range(start=START_DATE, end=END_DATE, freq="W-MON")  # Mondays
weeks = weeks.to_series().reset_index(drop=True)  # Series of timestamps

# ---------------- Phases definition ----------------
PHASES = {
    "Base Phase": (pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-31")),
    "Endurance Build": (pd.Timestamp("2026-01-01"), pd.Timestamp("2027-06-30")),
    "Strength & Long Distance": (pd.Timestamp("2027-07-01"), pd.Timestamp("2027-12-31")),
    "Peak Ironman Prep": (pd.Timestamp("2028-01-01"), pd.Timestamp("2028-07-31"))
}

# ---------------- Weekly plan generator (per-week targets) ----------------
def weekly_targets_for_phase(phase_name, week_index_in_phase):
    """
    Returns dict with target weekly volumes (Run_km, Bike_km, Swim_km, Strength_min)
    week_index_in_phase is 0-based week count within that phase.
    We progressively increase load ~3-7% per week depending on phase.
    """
    # base starting volumes per phase (per week)
    base = {
        "Base Phase": {"Run": 20, "Bike": 60, "Swim": 2, "Strength": 60},
        "Endurance Build": {"Run": 30, "Bike": 120, "Swim": 3, "Strength": 90},
        "Strength & Long Distance": {"Run": 40, "Bike": 180, "Swim": 4, "Strength": 100},
        "Peak Ironman Prep": {"Run": 45, "Bike": 200, "Swim": 4.5, "Strength": 80}
    }
    phase_base = base.get(phase_name, base["Base Phase"]).copy()
    # small weekly progression factor
    if phase_name == "Base Phase":
        weekly_inc = 0.03
    elif phase_name == "Endurance Build":
        weekly_inc = 0.05
    elif phase_name == "Strength & Long Distance":
        weekly_inc = 0.04
    else:
        weekly_inc = 0.02  # Peak - maintain with sharpening
    factor = (1 + weekly_inc) ** week_index_in_phase
    # compute rounded targets
    targets = {k: (round(v * factor, 1) if k != "Strength" else int(round(v * factor))) for k, v in phase_base.items()}
    return targets

# ---------------- Build full 3-year schedule dataframe ----------------
rows = []
for w in weeks:
    # determine phase for that week
    phase_name = None
    for pname, (pstart, pend) in PHASES.items():
        if pstart <= w <= pend:
            phase_name = pname
            break
    if phase_name is None:
        # before first phase -> Base Phase
        phase_name = "Base Phase"
    # compute week index within phase
    phase_start = PHASES[phase_name][0]
    week_idx = max(0, int((w - phase_start).days // 7))
    targets = weekly_targets_for_phase(phase_name, week_idx)
    rows.append({
        "week_start": w,
        "week_label": w.strftime("%Y-%m-%d"),
        "phase": phase_name,
        "run_km": targets["Run"],
        "bike_km": targets["Bike"],
        "swim_km": targets["Swim"],
        "strength_min": targets["Strength"]
    })
df_schedule = pd.DataFrame(rows)

# ---------------- UI: Sidebar ----------------
logo_url = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
try:
    resp = requests.get(logo_url, timeout=6)
    img = Image.open(BytesIO(resp.content))
    st.sidebar.image(img, use_column_width=True)
except:
    st.sidebar.write("🏊 Ironman Coach")
st.sidebar.title("Ironman 2028 Coach")

# Athlete selector & today info
athlete = st.sidebar.selectbox("Select athlete", ATHLETES)
TODAY = pd.Timestamp(datetime.now().date())
days_to_race = (IRONMAN_TARGET - TODAY).days
st.sidebar.metric("Days to Ironman (target)", f"{days_to_race} days")

# quick nav
st.sidebar.markdown("---")
st.sidebar.markdown("**Jump to**")
if st.sidebar.button("Today's Tasks"):
    st.experimental_rerun()  # keep simple; UI shows same top area

# ---------------- Greeting + Today's tasks (top of page) ----------------
now = datetime.now()
if now.hour < 12:
    greet = "Good morning"
elif now.hour < 17:
    greet = "Good afternoon"
else:
    greet = "Good evening"

st.markdown(f"## {greet}, {athlete} 👋")
st.markdown(f"**Today:** {TODAY.strftime('%A, %d %B %Y')}")

# get current week plan
current_week_row = df_schedule[df_schedule["week_start"] <= TODAY]
if current_week_row.empty:
    st.warning("Your training schedule starts on " + START_DATE.strftime("%Y-%m-%d"))
    today_targets = None
else:
    today_targets = current_week_row.iloc[-1]  # latest week <= today
    st.markdown(f"**Phase:** {today_targets['phase']}")
    # show today's tasks summary (split roughly across days — we'll show weekly targets and suggested daily focus)
    st.markdown("### Today's snapshot")
    left_col, right_col = st.columns([2, 1])
    with left_col:
        st.write("**Weekly targets (this week):**")
        st.table(pd.DataFrame({
            "Activity": ["Run (km)", "Bike (km)", "Swim (km)", "Strength (min)"],
            "This week target": [today_targets["run_km"], today_targets["bike_km"], today_targets["swim_km"], today_targets["strength_min"]]
        }))
    with right_col:
        st.write("**Nutrition**")
        st.write("- Warm water + lemon on wake")
        st.write("- Breakfast: oats/idli/dosa + fruit + milk or yogurt")
        st.write("- Pre-workout: banana/peanut-butter")
        st.write("- Post-workout: protein (shake/curd/paneer) + fruit")
        st.write("- Dinner: light + protein + salad")
        st.write("")
        st.write("**Sleep**")
        st.write("- Aim 7–8 hours. Wind-down 30–60 min before bed.")

st.markdown("---")

# ---------------- Tabs ----------------
tab_weekly, tab_phase, tab_nutrition, tab_sleep, tab_log, tab_team = st.tabs(
    ["🏁 Weekly Plan", "🔢 Phase Progress", "🥗 Nutrition", "😴 Sleep & Recovery", "📓 Log / Progress", "👥 Team Dashboard"]
)

# ---------------- TAB: Weekly Plan ----------------
with tab_weekly:
    st.header("Weekly Plan (selected week)")
    # allow user to choose week
    week_choice = st.selectbox("Choose week start", df_schedule["week_label"].tolist(), index=max(0, df_schedule[df_schedule["week_start"]<=TODAY].index.max() if not df_schedule[df_schedule["week_start"]<=TODAY].empty else 0))
    chosen_row = df_schedule[df_schedule["week_label"] == week_choice].iloc[0]
    week_table = pd.DataFrame({
        "Activity": ["Run (km)", "Bike (km)", "Swim (km)", "Strength (min)"],
        "Target": [chosen_row["run_km"], chosen_row["bike_km"], chosen_row["swim_km"], chosen_row["strength_min"]]
    })
    # style try-except
    try:
        st.dataframe(week_table.style.background_gradient(cmap="Greens"), use_container_width=True)
    except Exception:
        st.table(week_table)

    st.markdown("**Suggested split (example for day distribution)**")
    st.write("Mon: easy run / Swim technique; Tue: bike endurance; Wed: interval run + strength; Thu: bike tempo; Fri: swim + short run; Sat: long bike; Sun: long run or brick depending on phase.")

# ---------------- TAB: Phase Progress ----------------
with tab_phase:
    st.header("Phase progression & readiness")
    # compute progress percentages for each phase based on calendar date
    phase_rows = []
    for pname, (pstart, pend) in PHASES.items():
        total_days = (pend - pstart).days + 1
        days_done = max(0, (min(TODAY, pend) - pstart).days + 1) if TODAY >= pstart else 0
        progress_pct = round(max(0.0, min(100.0, (days_done / total_days) * 100)), 1)
        phase_rows.append({"Phase": pname, "Start": pstart.date(), "End": pend.date(), "Progress (%)": progress_pct})
    df_phase = pd.DataFrame(phase_rows)
    try:
        st.dataframe(df_phase.style.background_gradient(subset=["Progress (%)"], cmap="Blues").format({"Progress (%)":"{:.1f}%"}), use_container_width=True)
    except Exception:
        st.table(df_phase)

    # readiness score -> weighted sum (weights tuned)
    weights = {"Base Phase": 0.1, "Endurance Build": 0.5, "Strength & Long Distance": 0.2, "Peak Ironman Prep": 0.2}
    readiness = 0.0
    for row in phase_rows:
        readiness += row["Progress (%)"] * weights.get(row["Phase"], 0.0)
    readiness = round(readiness, 1)
    st.metric("Estimated Ironman Readiness", f"{readiness}%")

# ---------------- TAB: Nutrition ----------------
with tab_nutrition:
    st.header("Nutrition plan (Indian-friendly)")
    st.subheader("Daily meal framework (use same beverage throughout the day)")
    st.write("- **Hydration choice** (pick one for day): Water with electrolytes OR black coffee OR herbal tea.")
    st.write("- **Breakfast**: Oats / Idli / Dalia / Poha + fruit + milk/curd")
    st.write("- **Mid-morning**: Nuts + fruit")
    st.write("- **Lunch**: Brown rice / Rotis + Dal / Paneer / Chicken + Salad + Yogurt")
    st.write("- **Pre-workout**: Banana or energy toast")
    st.write("- **Post-workout**: Protein shake or curd + fruit")
    st.write("- **Evening**: Sprouts or roasted chana or nuts")
    st.write("- **Dinner**: Light roti + vegetables + soup + protein")
    st.markdown("**Notes:** prioritize whole foods, consistent meal timing, 3–4 L water/day. If traveling, prefer simple carbs pre-race/training and protein after.")

    st.markdown("### Meal logging (this week)")
    # display checkboxes for current athlete for each day & meal
    week_idx = df_schedule[df_schedule["week_start"] <= TODAY].index.max() if not df_schedule[df_schedule["week_start"]<=TODAY].empty else 0
    week_label = df_schedule.iloc[week_idx]["week_label"]
    st.write(f"This week: {week_label}")
    # Create keys and store in session_state for persistence in UI
    meals_cols = MEALS
    week_days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    meal_table = []
    for d in week_days:
        row = {"Day": d}
        for m in meals_cols:
            key = f"meal_{athlete}_{week_label}_{d}_{m}"
            checked = st.checkbox(f"{d} — {m}", key=key)
            row[m] = int(checked)
        meal_table.append(row)
    df_meal_local = pd.DataFrame(meal_table).set_index("Day")
    # show summary
    try:
        st.dataframe(df_meal_local.style.background_gradient(cmap="Oranges"), use_container_width=True)
    except:
        st.table(df_meal_local)

    # Save meal adherence to CSV if user presses Save
    if st.button("Save this week's meal adherence"):
        # convert to row per day for CSV
        save_rows = []
        for idx, r in df_meal_local.reset_index().iterrows():
            record = {"Athlete": athlete, "Week": week_label, "Day": r["Day"], "DateSaved": str(TODAY.date())}
            for meal_col in meals_cols:
                record[meal_col] = int(r[meal_col])
            save_rows.append(record)
        df_existing = safe_load_csv(NUTRITION_LOG_CSV)
        df_save = pd.concat([df_existing, pd.DataFrame(save_rows)], ignore_index=True) if not df_existing.empty else pd.DataFrame(save_rows)
        safe_save_csv(NUTRITION_LOG_CSV, df_save)
        st.success("Saved meal adherence for this week.")

# ---------------- TAB: Sleep & Recovery ----------------
with tab_sleep:
    st.header("Sleep & Recovery")
    st.write("Aim: 7–8 hours. Mark daily sleep and recovery items for this week.")
    # simple checkboxes for this week
    sleep_rows = []
    for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]:
        key = f"sleep_{athlete}_{week_label}_{d}"
        slept = st.checkbox(f"{d} — slept 7+ hours", key=key)
        nap = st.checkbox(f"{d} — short nap taken", key=f"{key}_nap")
        stretch = st.checkbox(f"{d} — stretch/yoga", key=f"{key}_stretch")
        sleep_rows.append({"Day": d, "Slept7": int(slept), "Nap": int(nap), "Stretch": int(stretch)})
    df_sleep_local = pd.DataFrame(sleep_rows).set_index("Day")
    try:
        st.dataframe(df_sleep_local.style.background_gradient(cmap="Blues"), use_container_width=True)
    except:
        st.table(df_sleep_local)

    if st.button("Save this week's sleep log"):
        records = []
        for idx, r in df_sleep_local.reset_index().iterrows():
            rec = {"Athlete": athlete, "Week": week_label, "Day": r["Day"], "DateSaved": str(TODAY.date()), "Slept7": r["Slept7"], "Nap": r["Nap"], "Stretch": r["Stretch"]}
            records.append(rec)
        df_existing = safe_load_csv(SLEEP_LOG_CSV)
        df_save = pd.concat([df_existing, pd.DataFrame(records)], ignore_index=True) if not df_existing.empty else pd.DataFrame(records)
        safe_save_csv(SLEEP_LOG_CSV, df_save)
        st.success("Saved sleep log for this week.")

# ---------------- TAB: Log / Progress ----------------
with tab_log:
    st.header("Training Log / Progress")
    st.write("Quick log your completed sessions for today (or any day). These will be used to compute adherence & trends.")
    with st.form("log_form", clear_on_submit=False):
        log_date = st.date_input("Date", value=datetime.now().date())
        discipline = st.selectbox("Discipline", ["Run", "Bike", "Swim", "Strength"])
        value = st.text_input("Distance (km) or time (min)", "")
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Save log")
        if submitted:
            rec = {"Athlete": athlete, "Date": str(log_date), "Discipline": discipline, "Value": value, "Notes": notes}
            df_existing = safe_load_csv(DIST_LOG_CSV)
            df_save = pd.concat([df_existing, pd.DataFrame([rec])], ignore_index=True) if not df_existing.empty else pd.DataFrame([rec])
            safe_save_csv(DIST_LOG_CSV, df_save)
            st.success("Saved log entry.")

    st.markdown("### Recent logs (last 20)")
    df_logs = safe_load_csv(DIST_LOG_CSV)
    if not df_logs.empty:
        st.dataframe(df_logs[df_logs["Athlete"]==athlete].sort_values("Date", ascending=False).head(20), use_container_width=True)
    else:
        st.info("No logs yet. Use the form above to add training records.")

# ---------------- TAB: Team Dashboard ----------------
with tab_team:
    st.header("Team Dashboard — Weekly snapshot")
    # compute weekly targets for current week
    if today_targets is None:
        st.info("Schedule not started yet.")
    else:
        # prepare team table
        team_rows = []
        for member in ATHLETES:
            # meal adherence avg for this week from CSV (if present)
            nut_df = safe_load_csv(NUTRITION_LOG_CSV)
            if not nut_df.empty:
                nut_filter = nut_df[(nut_df["Athlete"]==member) & (nut_df["Week"]==week_label)]
                if not nut_filter.empty:
                    # compute avg %
                    meal_cols = [c for c in nut_filter.columns if c not in ["Athlete","Week","Day","DateSaved"]]
                    # compute percent of checked meals (per day average)
                    try:
                        per_day = nut_filter[meal_cols].sum(axis=1) / len(meal_cols) * 100
                        avg_meal = round(per_day.mean(), 1)
                    except Exception:
                        avg_meal = 0.0
                else:
                    avg_meal = 0.0
            else:
                avg_meal = 0.0

            # sleep adherence
            sl_df = safe_load_csv(SLEEP_LOG_CSV)
            if not sl_df.empty:
                sl_filter = sl_df[(sl_df["Athlete"]==member) & (sl_df["Week"]==week_label)]
                if not sl_filter.empty:
                    avg_sleep = round(sl_filter["Slept7"].mean() * 100, 1)
                else:
                    avg_sleep = 0.0
            else:
                avg_sleep = 0.0

            # readiness (same for each if same date)
            readiness_member = readiness  # simple model; could be customized per athlete
            team_rows.append({
                "Athlete": member,
                "Run target (km)": today_targets["run_km"],
                "Bike target (km)": today_targets["bike_km"],
                "Swim target (km)": today_targets["swim_km"],
                "Strength target (min)": today_targets["strength_min"],
                "Meal adherence %": avg_meal,
                "Sleep adherence %": avg_sleep,
                "Readiness %": readiness_member
            })
        df_team = pd.DataFrame(team_rows)
        try:
            st.dataframe(df_team.style.background_gradient(subset=["Run target (km)","Bike target (km)","Swim target (km)","Strength target (min)"], cmap="Greens").background_gradient(subset=["Readiness %"], cmap="Blues"), use_container_width=True)
        except Exception:
            st.table(df_team)

        # Suggested actions per athlete
        st.markdown("---")
        st.subheader("Suggested actions (automated)")
        for r in team_rows:
            st.markdown(f"**{r['Athlete']}**")
            # training load check: compare logged actuals (from DIST_LOG) for this week to targets
            logs = safe_load_csv(DIST_LOG_CSV)
            if not logs.empty:
                logs_member = logs[(logs["Athlete"]==r["Athlete"]) & (pd.to_datetime(logs["Date"]) >= pd.to_datetime(today_targets["week_start"])) & (pd.to_datetime(logs["Date"]) < (pd.to_datetime(today_targets["week_start"]) + pd.Timedelta(days=7)))]
                # compute rough sums for run/bike/swim; strength assumed in minutes
                run_done = logs_member[logs_member["Discipline"]=="Run"]["Value"].replace("", "0").astype(str).str.extract(r'([0-9]+\.?[0-9]*)', expand=False).fillna(0).astype(float).sum() if not logs_member.empty else 0
                bike_done = logs_member[logs_member["Discipline"]=="Bike"]["Value"].replace("", "0").astype(str).str.extract(r'([0-9]+\.?[0-9]*)', expand=False).fillna(0).astype(float).sum() if not logs_member.empty else 0
                swim_done = logs_member[logs_member["Discipline"]=="Swim"]["Value"].replace("", "0").astype(str).str.extract(r'([0-9]+\.?[0-9]*)', expand=False).fillna(0).astype(float).sum() if not logs_member.empty else 0
                strength_done = logs_member[logs_member["Discipline"]=="Strength"]["Value"].replace("", "0").astype(str).str.extract(r'([0-9]+\.?[0-9]*)', expand=False).fillna(0).astype(float).sum() if not logs_member.empty else 0
            else:
                run_done = bike_done = swim_done = strength_done = 0

            # compare
            load_planned = r["Run target (km)"] + r["Bike target (km)"] + r["Swim target (km)"] + r["Strength target (min)"]/10
            load_done = run_done + bike_done + swim_done + strength_done/10
            if load_planned == 0:
                st.write("- No planned load.")
            else:
                if load_done < 0.7 * load_planned:
                    st.write("- ⚠️ Behind on training this week — try to make up 1–2 easy sessions, focus on quality.")
                elif load_done > 1.3 * load_planned:
                    st.write("- ⚠️ High load — ensure recovery (sleep, nutrition), consider reducing intensity.")
                else:
                    st.write("- ✅ Training load OK for this week.")

            # nutrition
            if r["Meal adherence %"] < 70:
                st.write("- ⚠️ Nutrition adherence low — prioritize pre/post-workout meals and hydration.")
            else:
                st.write("- ✅ Nutrition adherence OK.")

            # sleep
            if r["Sleep adherence %"] < 70:
                st.write("- ⚠️ Sleep below target — aim for consistent sleep schedule and naps if needed.")
            else:
                st.write("- ✅ Sleep on track.")
            st.markdown("----")

# ---------------- End of app ----------------
st.caption("App created to help structure training to Ironman 2028. Adjust phase dates/targets as required.")
