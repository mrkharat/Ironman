import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ---------------- Config ----------------
st.set_page_config(page_title="Ironman Team Coach", layout="wide")
TEAM = ["Mayur (M)", "Sudeep (M)", "Vaishali (F)"]
TODAY = datetime.today()
PHASES = {
    "Base Phase": (datetime(2025,10,1), datetime(2025,12,31)),
    "Endurance Build (Goa 70.3 2026)": (datetime(2026,1,1), datetime(2026,12,31)),
    "Strength & Long Distance 2027": (datetime(2027,1,1), datetime(2027,12,31)),
    "Peak Ironman Prep 2028": (datetime(2028,1,1), datetime(2028,7,31))
}

# ---------------- Data files ----------------
DATA_DIR = "team_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

PROGRESS_FILE = os.path.join(DATA_DIR, "progress.csv")
NUTRITION_FILE = os.path.join(DATA_DIR, "nutrition.csv")
SLEEP_FILE = os.path.join(DATA_DIR, "sleep.csv")

def ensure_file(path, cols):
    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False)

ensure_file(PROGRESS_FILE, ["Date","Athlete","Discipline","Task","Done"])
ensure_file(NUTRITION_FILE, ["Date","Athlete","Meal Time","Food/Drink","Quantity","Remarks"])
ensure_file(SLEEP_FILE, ["Date","Athlete","Sleep_Hours","Bedtime","Wakeup","Remarks"])

# ---------------- Phase Logic ----------------
def get_phase(today):
    for k,v in PHASES.items():
        if v[0] <= today <= v[1]:
            return k
    return "Recovery / Maintenance"

def get_weekly_plan(phase):
    """Return weekly training, nutrition, sleep guidance"""
    if phase=="Base Phase":
        return {
            "Run":"3x 5–7km + 1 long run 10–15km",
            "Swim":"2 sessions 200–400m (technique)",
            "Bike":"Short rides starting Dec 20–30km",
            "Strength":"1–2 sessions (core, mobility)",
            "Nutrition":"Balanced meals, reduce sugar",
            "Sleep":"7–8 hrs, consistent bedtime"
        }
    if phase=="Endurance Build (Goa 70.3 2026)":
        return {
            "Run":"Weekly long run 25–30 km",
            "Swim":"2–3 sessions up to 2 km",
            "Bike":"Long rides 60–80 km, practice nutrition",
            "Strength":"1 session/week",
            "Nutrition":"Carb focus before long workouts",
            "Sleep":"7–8 hrs, early night before long training"
        }
    if phase=="Strength & Long Distance 2027":
        return {
            "Run":"Long runs 30–35 km, tempo sessions",
            "Swim":"Build to 2.5 km continuous",
            "Bike":"100–120 km long rides",
            "Strength":"2 sessions/week",
            "Nutrition":"Hydration + carb timing",
            "Sleep":"7–9 hrs, recovery-focused"
        }
    if phase=="Peak Ironman Prep 2028":
        return {
            "Run":"38–40 km long runs, brick workouts",
            "Swim":"3–3.8 km open water",
            "Bike":"150–180 km rides",
            "Strength":"Maintain mobility",
            "Nutrition":"Race fuel practice, carb load",
            "Sleep":"8–9 hrs, early bedtime before race simulations"
        }
    return {
        "Run":"Easy recovery runs 5–10 km",
        "Swim":"Light technique swims",
        "Bike":"Short spins",
        "Strength":"Yoga / mobility",
        "Nutrition":"Balanced diet",
        "Sleep":"7–8 hrs"
    }

# ---------------- Load & Save Helpers ----------------
def load_csv(path):
    return pd.read_csv(path)

def save_csv(df,path):
    df.to_csv(path,index=False)

# ---------------- Sidebar ----------------
st.sidebar.title("Team Ironman Coach")
athlete = st.sidebar.selectbox("Select Athlete", TEAM)
phase = get_phase(TODAY)
st.sidebar.info(f"Current Phase: **{phase}**")
race_day = date(2028,7,9)
days_left = (race_day - TODAY.date()).days
st.sidebar.success(f"Days to Ironman Hamburg 2028: **{days_left}**")

# ---------------- Tabs ----------------
tabs = st.tabs(["Weekly Plan & Check", "Nutrition Log", "Sleep Log", "Team Leaderboard"])

weekly_plan = get_weekly_plan(phase)

# ---------------- Tab 1: Weekly Plan ----------------
with tabs[0]:
    st.header(f"Weekly Coach Plan — {phase}")
    st.markdown("### This Week's Activities & Tasks")
    df_prog = load_csv(PROGRESS_FILE)
    today_str = str(TODAY.date())
    tasks=[]
    for disc, task_text in weekly_plan.items():
        if disc in ["Nutrition","Sleep"]:
            continue
        existing = df_prog[(df_prog["Date"]==today_str)&(df_prog["Athlete"]==athlete)&(df_prog["Discipline"]==disc)]
        init=False
        if not existing.empty:
            init=bool(existing.iloc[-1]["Done"])
        done = st.checkbox(f"{disc}: {task_text}", value=init, key=f"{athlete}_{disc}_{today_str}")
        tasks.append({"Date":today_str,"Athlete":athlete,"Discipline":disc,"Task":task_text,"Done":int(done)})
    if st.button("Save Today's Activity"):
        df_prog = df_prog[~((df_prog["Date"]==today_str)&(df_prog["Athlete"]==athlete))]
        df_prog = pd.concat([df_prog,pd.DataFrame(tasks)],ignore_index=True)
        save_csv(df_prog,PROGRESS_FILE)
        st.success("Saved activity progress")

    st.markdown("### Weekly Nutrition & Sleep Guidance")
    st.write(f"- **Nutrition**: {weekly_plan['Nutrition']}")
    st.write(f"- **Sleep**: {weekly_plan['Sleep']}")

# ---------------- Tab 2: Nutrition ----------------
with tabs[1]:
    st.header("Nutrition Log")
    df_nut = load_csv(NUTRITION_FILE)
    col1,col2,col3 = st.columns(3)
    with col1:
        nut_date = st.date_input("Date", value=TODAY.date())
        meal_time = st.selectbox("Meal time", ["Breakfast","Mid-morning","Lunch","Snack","Pre-workout","Post-workout","Dinner","Other"])
    with col2:
        food = st.text_input("Food / Drink")
        qty = st.text_input("Quantity","e.g., 1 bowl, 2 slices")
    with col3:
        remarks = st.text_input("Remarks / Calories / Feel")
        if st.button("Add Nutrition Entry"):
            df_nut = load_csv(NUTRITION_FILE)
            df_nut = pd.concat([df_nut,pd.DataFrame([{
                "Date":str(nut_date),
                "Athlete":athlete,
                "Meal Time":meal_time,
                "Food/Drink":food,
                "Quantity":qty,
                "Remarks":remarks
            }])],ignore_index=True)
            save_csv(df_nut,NUTRITION_FILE)
            st.success("Nutrition entry added")
    st.dataframe(df_nut[df_nut["Athlete"]==athlete].sort_values("Date",ascending=False).head(20))

# ---------------- Tab 3: Sleep ----------------
with tabs[2]:
    st.header("Sleep Log")
    df_sleep = load_csv(SLEEP_FILE)
    col1,col2,col3 = st.columns([1,1,1])
    with col1:
        sleep_date = st.date_input("Date", value=TODAY.date(), key="sleep_date")
        sleep_hours = st.number_input("Hours slept", 0.0,12.0,7.5,0.5)
    with col2:
        bedtime = st.time_input("Bedtime", key="bedtime")
    with col3:
        wakeup = st.time_input("Wakeup", key="wakeup")
        remarks = st.text_input("Remarks")
        if st.button("Save Sleep Entry"):
            df_sleep = load_csv(SLEEP_FILE)
            df_sleep = pd.concat([df_sleep,pd.DataFrame([{
                "Date":str(sleep_date),
                "Athlete":athlete,
                "Sleep_Hours":sleep_hours,
                "Bedtime":bedtime.strftime("%H:%M"),
                "Wakeup":wakeup.strftime("%H:%M"),
                "Remarks":remarks
            }])],ignore_index=True)
            save_csv(df_sleep,SLEEP_FILE)
            st.success("Sleep entry saved")
    st.dataframe(df_sleep[df_sleep["Athlete"]==athlete].sort_values("Date",ascending=False).head(10))

# ---------------- Tab 4: Team Leaderboard ----------------
with tabs[3]:
    st.header("Team Leaderboard & Consistency")
    df_prog = load_csv(PROGRESS_FILE)
    if df_prog.empty:
        st.info("No progress yet for team")
    else:
        leaderboard = df_prog.groupby("Athlete")["Done"].mean().reset_index()
        leaderboard["Consistency %"] = (leaderboard["Done"]*100).round(1)
        st.bar_chart(leaderboard.set_index("Athlete")["Consistency %"])
        st.subheader("Recent Activity Log")
        st.dataframe(df_prog.sort_values(["Date","Athlete"],ascending=[False,True]).head(50))
