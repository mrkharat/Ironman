import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ---------------- Config ----------------
st.set_page_config(page_title="Ironman 2028 Coach + Nutrition & Weight", layout="wide")
APP_TITLE = "Ironman 2028 — Coach + Nutrition + Weight"
USERS = ["You", "Friend 1 (M)", "Friend 2 (F)"]

PROGRESS_FILE = "progress.csv"
NUTRITION_FILE = "nutrition.csv"
WEIGHT_FILE = "weight.csv"

# ---------------- Ensure data files ----------------
def ensure_file(path, cols):
    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)

ensure_file(PROGRESS_FILE, ["Date", "Athlete", "Discipline", "Task", "Done"])
ensure_file(NUTRITION_FILE, ["Date", "Athlete", "Meal Time", "Food/Drink", "Quantity", "Remarks"])
ensure_file(WEIGHT_FILE, ["Date", "Athlete", "Weight_kg", "Remarks"])

# ---------------- Utilities ----------------
def get_phase(today):
    if today < datetime(2026, 1, 1):
        return "Base Phase (Oct–Dec 2025)"
    elif today < datetime(2027, 1, 1):
        return "Endurance Build (2026 - includes Goa 70.3)"
    elif today < datetime(2028, 1, 1):
        return "Strength & Long Distance (2027)"
    elif today < datetime(2028, 8, 1):
        return "Peak Ironman Prep (Jan–Jul 2028)"
    else:
        return "Recovery & Maintenance (Aug–Dec 2028)"

def get_weekly_plan(phase):
    if phase == "Base Phase (Oct–Dec 2025)":
        return {
            "Run": "3x 5–7 km + 1 long run (10–15 km)",
            "Swim": "2 technique sessions (200–400m continuous)",
            "Bike": "Start short rides in Dec (20–30 km)",
            "Strength": "1–2 sessions (core, mobility)",
            "Nutrition": "Balanced meals, reduce sugar"
        }
    if phase == "Endurance Build (2026 - includes Goa 70.3)":
        return {
            "Run": "Weekly long run 25–30 km",
            "Swim": "2–3 sessions up to 2 km",
            "Bike": "Long rides 60–80 km",
            "Strength": "1 session per week",
            "Nutrition": "Carb focus, race-day practice"
        }
    if phase == "Strength & Long Distance (2027)":
        return {
            "Run": "Long runs 30–35 km, tempo sessions",
            "Swim": "Build to 2.5 km continuous",
            "Bike": "100–120 km long rides",
            "Strength": "2 sessions (strength + core)",
            "Nutrition": "Hydration + carb timing"
        }
    if phase == "Peak Ironman Prep (Jan–Jul 2028)":
        return {
            "Run": "38–40 km long runs, brick sessions",
            "Swim": "3–3.8 km open water continuous",
            "Bike": "150–180 km long rides",
            "Strength": "Maintain mobility",
            "Nutrition": "Race fuel practice, carb load"
        }
    return {
        "Run": "Easy recovery 5–10 km",
        "Swim": "Light swims, technique",
        "Bike": "Short easy spins",
        "Strength": "Yoga, stretching",
        "Nutrition": "Recovery diet"
    }

# ---------------- Load Data ----------------
def load_progress():
    return pd.read_csv(PROGRESS_FILE)

def load_nutrition():
    return pd.read_csv(NUTRITION_FILE)

def load_weight():
    return pd.read_csv(WEIGHT_FILE)

def save_progress(df):
    df.to_csv(PROGRESS_FILE, index=False)

def save_nutrition(df):
    df.to_csv(NUTRITION_FILE, index=False)

def save_weight(df):
    df.to_csv(WEIGHT_FILE, index=False)

# ---------------- UI ----------------
st.title(APP_TITLE)
today = datetime.today()
phase = get_phase(today)
st.sidebar.header("Profile & Info")
athlete = st.sidebar.selectbox("Select Athlete", USERS)
race_day = date(2028, 7, 9)  # placeholder
days_left = (race_day - today.date()).days
st.sidebar.info(f"Phase: **{phase}**")
st.sidebar.success(f"Days to Ironman Hamburg (approx): {days_left}")

# Tabs
tabs = st.tabs(["Daily Coach", "Nutrition Log", "Weight Tracker", "Team", "Logs & Export"])

# ---------------- Tab: Daily Coach ----------------
with tabs[0]:
    st.header("This Week's Plan")
    weekly_plan = get_weekly_plan(phase)
    st.markdown("**Weekly focus**")
    for d, t in weekly_plan.items():
        st.write(f"- **{d}**: {t}")

    st.markdown("---")
    st.subheader("Today's Checkboxes (tick when done)")
    df_prog = load_progress()
    today_str = str(today.date())

    # For each discipline, show checkbox; pre-fill if today's entry exists for this athlete+discipline
    disciplines = ["Run", "Swim", "Bike", "Strength", "Nutrition"]
    tasks = []
    for disc in disciplines:
        # The Task text is the weekly plan entry condensed
        task_text = weekly_plan[disc]
        # find existing entry
        existing = df_prog[(df_prog["Date"] == today_str) & (df_prog["Athlete"] == athlete) & (df_prog["Discipline"] == disc)]
        initial = False
        if not existing.empty:
            # take last recorded Done
            initial = bool(existing.iloc[-1]["Done"])
        checked = st.checkbox(f"{disc}: {task_text}", value=initial, key=f"{athlete}_{disc}_{today_str}")
        tasks.append({"Date": today_str, "Athlete": athlete, "Discipline": disc, "Task": task_text, "Done": int(checked)})

    if st.button("Save today's progress"):
        # remove existing today's entries for athlete then append
        df = load_progress()
        df = df[~((df["Date"] == today_str) & (df["Athlete"] == athlete))]
        df = pd.concat([df, pd.DataFrame(tasks)], ignore_index=True)
        save_progress(df)
        st.success("Saved today's progress")

# ---------------- Tab: Nutrition Log ----------------
with tabs[1]:
    st.header("Nutrition — Log your meals (simple)")
    df_nut = load_nutrition()
    col1, col2, col3 = st.columns(3)
    with col1:
        nut_date = st.date_input("Date", value=today.date(), key="nut_date")
        meal_time = st.selectbox("Meal time", ["Breakfast", "Mid-morning", "Lunch", "Snack", "Pre-workout", "Post-workout", "Dinner", "Other"], key="meal_time")
    with col2:
        food = st.text_input("Food / Drink", key="food")
        qty = st.text_input("Quantity", key="qty", help="e.g., 1 bowl, 2 slices, 1 scoop")
    with col3:
        remarks = st.text_input("Remarks (calories / feel / hydration)", key="nut_remarks")
        if st.button("Add Nutrition Entry"):
            df_nut = load_nutrition()
            df_nut = pd.concat([df_nut, pd.DataFrame([{
                "Date": str(nut_date),
                "Athlete": athlete,
                "Meal Time": meal_time,
                "Food/Drink": food,
                "Quantity": qty,
                "Remarks": remarks
            }])], ignore_index=True)
            save_nutrition(df_nut)
            st.success("Nutrition entry added")
    st.markdown("Recent nutrition entries (you)")
    df_nut = load_nutrition()
    df_nut_user = df_nut[df_nut["Athlete"] == athlete].sort_values("Date", ascending=False).head(20)
    if not df_nut_user.empty:
        st.dataframe(df_nut_user)
    else:
        st.info("No nutrition entries yet for you.")

# ---------------- Tab: Weight Tracker ----------------
with tabs[2]:
    st.header("Weight Tracker")
    df_w = load_weight()
    col1, col2 = st.columns([2,1])
    with col1:
        wt_date = st.date_input("Date", value=today.date(), key="wt_date")
        weight_val = st.number_input("Weight (kg)", value=62.0, step=0.1, format="%.1f", key="weight")
        wt_rem = st.text_input("Remarks", key="wt_rem")
        if st.button("Save weight"):
            df_w = load_weight()
            df_w = pd.concat([df_w, pd.DataFrame([{
                "Date": str(wt_date),
                "Athlete": athlete,
                "Weight_kg": float(weight_val),
                "Remarks": wt_rem
            }])], ignore_index=True)
            save_weight(df_w)
            st.success("Weight entry saved")
    with col2:
        st.markdown("Your recent weights")
        df_w_user = df_w[df_w["Athlete"]==athlete].sort_values("Date")
        if not df_w_user.empty:
            st.line_chart(df_w_user.set_index(pd.to_datetime(df_w_user["Date"]))["Weight_kg"])
            st.dataframe(df_w_user.tail(10))
        else:
            st.info("No weight entries yet for you.")

# ---------------- Tab: Team ----------------
with tabs[3]:
    st.header("Team Dashboard")
    df_prog = load_progress()
    if df_prog.empty:
        st.info("No progress data yet. Each athlete should save daily progress.")
    else:
        # compute consistency per athlete = mean Done across last 60 days
        recent_cutoff = (today.date()).isoformat()
        # aggregate by athlete
        agg = df_prog.groupby("Athlete")["Done"].mean().reset_index()
        agg["Consistency %"] = (agg["Done"] * 100).round(1)
        agg = agg.sort_values("Consistency %", ascending=False)
        st.subheader("Consistency (all-time)")
        st.bar_chart(agg.set_index("Athlete")["Consistency %"])

        # show recent activity
        st.subheader("Recent activity (all athletes)")
        st.dataframe(df_prog.sort_values(["Date","Athlete"], ascending=[False, True]).head(100))

        # nutrition summary (counts)
        df_nut = load_nutrition()
        if not df_nut.empty:
            st.subheader("Nutrition entries (last 30)")
            st.dataframe(df_nut.sort_values("Date", ascending=False).head(30))
        else:
            st.info("No nutrition entries yet for team.")

# ---------------- Tab: Logs & Export ----------------
with tabs[4]:
    st.header("Logs & Export")
    st.subheader("Progress log")
    df_prog = load_progress()
    st.dataframe(df_prog.sort_values(["Date","Athlete"], ascending=[False, True]).head(200))
    st.download_button("Download progress.csv", df_prog.to_csv(index=False).encode('utf-8'), file_name="progress.csv")
    st.markdown("---")
    st.subheader("Nutrition log")
    df_nut = load_nutrition()
    st.dataframe(df_nut.sort_values("Date", ascending=False).head(200))
    st.download_button("Download nutrition.csv", df_nut.to_csv(index=False).encode('utf-8'), file_name="nutrition.csv")
    st.markdown("---")
    st.subheader("Weight log")
    df_w = load_weight()
    st.dataframe(df_w.sort_values("Date", ascending=False).head(200))
    st.download_button("Download weight.csv", df_w.to_csv(index=False).encode('utf-8'), file_name="weight.csv")

st.markdown("---")
st.caption("App stores CSV files in the app folder. If you deploy to Streamlit Cloud, use a backing store (Google Sheets or a small DB) for permanent storage across deploys.")

