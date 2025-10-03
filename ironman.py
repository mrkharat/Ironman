# ironman_coach_app_v3.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random
import pytz

# ------------------ CONFIG ------------------
DATA_DIR = "athlete_data"
LOG_DIR = os.path.join(DATA_DIR, "logs")
WEIGHT_DIR = os.path.join(DATA_DIR, "weight")
SLEEP_DIR = os.path.join(DATA_DIR, "sleep")

ATHLETES = {
    "Mayur": {"weight": 62, "gender": "male", "dob": "1988-12-25", "target_weight": 65},
    "Sudeep": {"weight": 73, "gender": "male", "dob": "1988-10-31", "target_weight": 75},
    "Vaishali": {"weight": 64, "gender": "female", "dob": "1988-04-02", "target_weight": 63},
}

IRONMAN_DATE = datetime(2028, 7, 1, 7, 0)
TIMEZONE = pytz.timezone('Asia/Kolkata')

PHASES = ["Base", "Build", "Peak", "Taper"]
SUNDAY_ACTIVITIES = ["Hike", "Long Drive", "Plantation Drive", "Family Cycling", "Yoga in Park"]
INDIAN_FESTIVALS = {
    "2025-10-24": "Diwali",
    "2026-03-29": "Holi",
    "2026-08-15": "Independence Day",
    "2027-01-14": "Makar Sankranti"
}
QUOTES = [
    "Every swim stroke counts!",
    "Run like the wind, ride like a champion.",
    "Ironman is earned, not given.",
    "Consistency beats intensity.",
    "Small steps today, Ironman tomorrow."
]

# ------------------ FUNCTIONS ------------------
def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(WEIGHT_DIR, exist_ok=True)
    os.makedirs(SLEEP_DIR, exist_ok=True)

def load_log(athlete):
    path = os.path.join(LOG_DIR, f"{athlete}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","Phase","Run","Bike","Swim","Strength","Recovery","Completed"])
    return df

def save_log(athlete, df):
    path = os.path.join(LOG_DIR, f"{athlete}.csv")
    df.to_csv(path, index=False)

def load_weight(athlete):
    path = os.path.join(WEIGHT_DIR, f"{athlete}_weight.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","Weight"])
    return df

def save_weight(athlete, df):
    path = os.path.join(WEIGHT_DIR, f"{athlete}_weight.csv")
    df.to_csv(path, index=False)

def load_sleep(athlete):
    path = os.path.join(SLEEP_DIR, f"{athlete}_sleep.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","SleepHours"])
    return df

def save_sleep(athlete, df):
    path = os.path.join(SLEEP_DIR, f"{athlete}_sleep.csv")
    df.to_csv(path, index=False)

def get_phase(today):
    start = datetime(2025,10,1)
    delta_weeks = (today - start).days // 7
    cycle = delta_weeks % 52
    if cycle < 20: return "Base"
    elif cycle < 36: return "Build"
    elif cycle < 48: return "Peak"
    else: return "Taper"

def get_greeting(now):
    hour = now.hour
    if hour < 12: return "Good Morning"
    elif hour < 17: return "Good Afternoon"
    else: return "Good Evening"

def get_todays_plan(athlete, today):
    df = load_log(athlete)
    phase = get_phase(today)
    if not any(df["Date"] == today):
        run_dist, bike_dist, swim_time = 0,0,0
        if phase=="Base": run_dist=5
        elif phase=="Build": run_dist=10
        elif phase=="Peak": run_dist=15
        elif phase=="Taper": run_dist=5
        if today >= datetime(2026,2,1):
            if phase=="Base": bike_dist=20
            elif phase=="Build": bike_dist=40
            elif phase=="Peak": bike_dist=80
            elif phase=="Taper": bike_dist=20
        if today >= datetime(2025,11,1):
            if phase=="Base": swim_time=15
            elif phase=="Build": swim_time=30
            elif phase=="Peak": swim_time=45
            elif phase=="Taper": swim_time=15
        df = df.append({"Date":today,"Phase":phase,"Run":run_dist,"Bike":bike_dist,"Swim":swim_time,
                        "Strength":30,"Recovery":15,"Completed":False}, ignore_index=True)
        save_log(athlete, df)
    today_plan = df[df["Date"]==today].iloc[0]
    return today_plan

def get_next_day_plan(athlete, today):
    plan = get_todays_plan(athlete, today + timedelta(days=1))
    # Adjust based on today's completion
    df = load_log(athlete)
    today_row = df[df["Date"]==today].iloc[0]
    if today_row["Completed"]:
        plan["Run"] += 1
        plan["Bike"] += 2
        plan["Swim"] += 5
        plan["Strength"] += 5
    return plan

def generate_nutrition_plan(athlete):
    return {
        "07:30": "Breakfast: Oats/Poha/Idli + Milk or Tea",
        "10:30": "Snack: Banana or Nuts",
        "13:00": "Lunch: Roti, Dal, Veg, Salad, Yogurt",
        "16:00": "Snack: Fruit or Protein Shake",
        "19:00": "Dinner: Roti/Rice, Dal, Veg, Light Soup"
    }

def get_countdown():
    now = datetime.now(TIMEZONE)
    diff = IRONMAN_DATE - now
    days = diff.days
    hours, rem = divmod(diff.seconds,3600)
    minutes, seconds = divmod(rem,60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_special(today):
    today_str = today.strftime("%Y-%m-%d")
    if today_str in INDIAN_FESTIVALS: return INDIAN_FESTIVALS[today_str]
    for name, info in ATHLETES.items():
        dob = datetime.strptime(info["dob"], "%Y-%m-%d")
        if dob.day==today.day and dob.month==today.month:
            return f"Happy Birthday {name}!"
    return ""

def sunday_activity(today):
    if today.weekday()==6:  # Sunday
        month_first_sunday = today.replace(day=1)
        first_sunday = month_first_sunday + timedelta(days=(6-month_first_sunday.weekday())%7)
        if today==first_sunday:
            return "Joint Activity: " + random.choice(SUNDAY_ACTIVITIES)
        else:
            return "Personal Activity: " + random.choice(SUNDAY_ACTIVITIES)
    return ""

# ------------------ APP ------------------
st.set_page_config(page_title="Ironman Coaching App", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background-color: #121212; color: white;}
    .stDataFrame table {color:white;}
    </style>
    """, unsafe_allow_html=True
)

ensure_dirs()
now = datetime.now(TIMEZONE)
today = datetime(now.year, now.month, now.day)

# ------------------ SIDEBAR ------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg?raw=true", use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown(f"### Countdown to Ironman Hamburg 2028")
st.sidebar.markdown(get_countdown())
st.sidebar.markdown(f"### Quote of the Day")
st.sidebar.markdown(f"_{random.choice(QUOTES)}_")
st.sidebar.markdown(f"### Today's Special")
st.sidebar.markdown(get_special(today))

# ------------------ MAIN PAGE ------------------
st.title(f"{get_greeting(now)}, {athlete}!")
st.markdown(f"**Today:** {today.strftime('%A, %d %B %Y')}")
st.markdown(f"**Week starting Monday:** {(today - timedelta(days=today.weekday())).strftime('%d %b %Y')}")
phase = get_phase(today)
st.markdown(f"**Current Phase:** {phase}")

# ---------- TABS ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Today's Plan","Next Day Plan","Nutrition & Weight","Progress","Teams Overview"])

# ------------------ TODAY'S PLAN ------------------
with tab1:
    today_plan = get_todays_plan(athlete, today)
    st.markdown("### Training Plan")
    completed = []
    for activity in ["Run","Bike","Swim","Strength","Recovery"]:
        checked = st.checkbox(f"{activity}: {today_plan[activity]} {'km' if activity in ['Run','Bike'] else 'min'}", value=False, key=f"{athlete}_{activity}_{today}")
        completed.append(checked)
    if all(completed):
        df = load_log(athlete)
        df.loc[df["Date"]==today,"Completed"]=True
        save_log(athlete, df)
        st.success("Great! Today's plan marked as completed.")
    st.markdown("### Nutrition Plan")
    nutrition = generate_nutrition_plan(athlete)
    for time, meal in nutrition.items():
        st.markdown(f"**{time}** - {meal}")
    # Sunday suggestion
    activity_sun = sunday_activity(today)
    if activity_sun:
        st.markdown(f"### Sunday Suggestion: {activity_sun}")
    # Motivational tip
    st.markdown(f"### Tip for today:")
    st.markdown(f"Stay consistent and hydrate well. Small wins today lead to Ironman success!")

# ------------------ NEXT DAY PLAN ------------------
with tab2:
    next_plan = get_next_day_plan(athlete, today)
    st.markdown(f"### { (today+timedelta(days=1)).strftime('%A, %d %B %Y') } Plan")
    for activity in ["Run","Bike","Swim","Strength","Recovery"]:
        st.markdown(f"{activity}: {next_plan[activity]} {'km' if activity in ['Run','Bike'] else 'min'}")
    st.markdown("### Nutrition Plan")
    next_nutrition = generate_nutrition_plan(athlete)
    for time, meal in next_nutrition.items():
        st.markdown(f"**{time}** - {meal}")
    st.markdown(f"### Tip for tomorrow:")
    st.markdown(f"Prepare well, plan meals and rest accordingly.")

# ------------------ NUTRITION & WEIGHT & SLEEP ------------------
with tab3:
    st.markdown("### Weight Tracking")
    weight_df = load_weight(athlete)
    new_weight = st.number_input("Log today's weight (kg)", min_value=30.0, max_value=150.0, value=ATHLETES[athlete]["weight"], step=0.1)
    if st.button("Save Weight"):
        weight_df = weight_df.append({"Date":today,"Weight":new_weight}, ignore_index=True)
        save_weight(athlete, weight_df)
        st.success("Weight saved.")
    st.dataframe(weight_df, use_container_width=True)
    st.markdown(f"Target Weight for Ironman 2028: {ATHLETES[athlete]['target_weight']} kg")

    st.markdown("### Sleep Tracking")
    sleep_df = load_sleep(athlete)
    sleep_hours = st.number_input("Log sleep hours last night", min_value=0.0, max_value=12.0, value=8.0, step=0.5)
    if st.button("Save Sleep"):
        sleep_df = sleep_df.append({"Date":today,"SleepHours":sleep_hours}, ignore_index=True)
        save_sleep(athlete, sleep_df)
        st.success("Sleep saved.")
    st.dataframe(sleep_df, use_container_width=True)
    if sleep_hours<7:
        st.warning("Try to sleep more for better recovery!")

# ------------------ PROGRESS ------------------
with tab4:
    df = load_log(athlete)
    if not df.empty:
        df_progress = df.copy()
        df_progress["Completion"] = np.where(df_progress["Completed"],1,0)
        st.markdown("### Weekly Completion Status")
        st.bar_chart(df_progress[["Run","Bike","Swim","Strength","Recovery"]].fillna(0))
    else:
        st.write("No data yet.")

# ------------------ TEAMS OVERVIEW ------------------
with tab5:
    st.markdown("### Teams Overview")
    all_data = {}
    for a in ATHLETES.keys():
        df_a = load_log(a)
        if not df_a.empty:
            df_a["Completion"] = np.where(df_a["Completed"],1,0)
            all_data[a] = df_a[["Date","Completion"]].set_index("Date").resample("W").sum()
    if all_data:
        combined = pd.concat(all_data, axis=1)
        st.line_chart(combined.fillna(0))
