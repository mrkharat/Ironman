# ironman_coach_app.py

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

ATHLETES = {
    "Mayur": {"weight": 62, "gender": "male", "dob": "1988-12-25"},
    "Sudeep": {"weight": 73, "gender": "male", "dob": "1988-10-31"},
    "Vaishali": {"weight": 64, "gender": "female", "dob": "1988-04-02"},
}

IRONMAN_DATE = datetime(2028, 7, 1, 7, 0)  # Hamburg 2028 start
TIMEZONE = pytz.timezone('Asia/Kolkata')

PHASES = ["Base", "Build", "Peak", "Taper"]
SUNDAY_ACTIVITIES = [
    "Hike", "Long Drive", "Plantation Drive", "Family Cycling", "Yoga in Park"
]

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

def get_phase(today):
    # Define phases over 3 years (approx.)
    start = datetime(2025,10,1)
    delta_weeks = (today - start).days // 7
    cycle = delta_weeks % 52
    if cycle < 20:
        return "Base"
    elif cycle < 36:
        return "Build"
    elif cycle < 48:
        return "Peak"
    else:
        return "Taper"

def get_greeting(now):
    hour = now.hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"

def get_todays_plan(athlete, today):
    df = load_log(athlete)
    phase = get_phase(today)
    
    # Generate sample plan if not exists for today
    if not any(df["Date"] == today):
        run_dist, bike_dist, swim_time = 0,0,0
        # Running plan
        if phase=="Base":
            run_dist = 5
        elif phase=="Build":
            run_dist = 10
        elif phase=="Peak":
            run_dist = 15
        elif phase=="Taper":
            run_dist = 5
        # Bike starts Feb 2026
        if today >= datetime(2026,2,1):
            if phase=="Base":
                bike_dist = 20
            elif phase=="Build":
                bike_dist = 40
            elif phase=="Peak":
                bike_dist = 80
            elif phase=="Taper":
                bike_dist = 20
        # Swim starts Nov 2025
        if today >= datetime(2025,11,1):
            if phase=="Base":
                swim_time = 15
            elif phase=="Build":
                swim_time = 30
            elif phase=="Peak":
                swim_time = 45
            elif phase=="Taper":
                swim_time = 15
        df = df.append({"Date":today,"Phase":phase,"Run":run_dist,"Bike":bike_dist,"Swim":swim_time,
                        "Strength":30,"Recovery":15,"Completed":False}, ignore_index=True)
        save_log(athlete, df)
    today_plan = df[df["Date"]==today].iloc[0]
    return today_plan

def get_next_day_plan(athlete, today):
    return get_todays_plan(athlete, today + timedelta(days=1))

def generate_nutrition_plan(athlete, today):
    # Indian meals and timing
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

def get_special(today, athlete):
    today_str = today.strftime("%Y-%m-%d")
    if today_str in INDIAN_FESTIVALS:
        return INDIAN_FESTIVALS[today_str]
    for name, info in ATHLETES.items():
        dob = datetime.strptime(info["dob"], "%Y-%m-%d")
        if dob.day == today.day and dob.month == today.month:
            return f"Happy Birthday {name}!"
    return ""

# ------------------ APP ------------------
st.set_page_config(page_title="Ironman Coaching App", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background-color: #121212; color: white;}
    .css-1d391kg {color:white;} 
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
st.sidebar.markdown(get_special(today, athlete))

# ------------------ MAIN PAGE ------------------
st.title(f"{get_greeting(now)}, {athlete}!")
st.markdown(f"**Today:** {today.strftime('%A, %d %B %Y')}")
st.markdown(f"**Week starting Monday:** {(today - timedelta(days=today.weekday())).strftime('%d %b %Y')}")
phase = get_phase(today)
st.markdown(f"**Current Phase:** {phase}")

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Today's Plan","Next Day Plan","Nutrition Log","Progress","Teams Overview"])

# ------------------ TODAY'S PLAN ------------------
with tab1:
    plan = get_todays_plan(athlete, today)
    st.markdown("### Activity Plan")
    st.checkbox(f"Run: {plan['Run']} km", key=f"{athlete}_run")
    st.checkbox(f"Bike: {plan['Bike']} km", key=f"{athlete}_bike")
    st.checkbox(f"Swim: {plan['Swim']} min", key=f"{athlete}_swim")
    st.checkbox(f"Strength: {plan['Strength']} min", key=f"{athlete}_strength")
    st.checkbox(f"Recovery: {plan['Recovery']} min", key=f"{athlete}_recovery")
    st.markdown("### Nutrition Plan")
    nutrition = generate_nutrition_plan(athlete, today)
    for time, meal in nutrition.items():
        st.markdown(f"**{time}** - {meal}")

# ------------------ NEXT DAY PLAN ------------------
with tab2:
    next_plan = get_next_day_plan(athlete, today)
    st.markdown(f"### Next Day Plan ({(today + timedelta(days=1)).strftime('%A')})")
    st.markdown(f"Run: {next_plan['Run']} km")
    st.markdown(f"Bike: {next_plan['Bike']} km")
    st.markdown(f"Swim: {next_plan['Swim']} min")
    st.markdown(f"Strength: {next_plan['Strength']} min")
    st.markdown(f"Recovery: {next_plan['Recovery']} min")
    st.markdown("### Nutrition Plan")
    next_nutrition = generate_nutrition_plan(athlete, today+timedelta(days=1))
    for time, meal in next_nutrition.items():
        st.markdown(f"**{time}** - {meal}")

# ------------------ NUTRITION LOG ------------------
with tab3:
    weight_df = load_weight(athlete)
    st.markdown("### Weight Tracking")
    st.dataframe(weight_df, use_container_width=True)

# ------------------ PROGRESS ------------------
with tab4:
    df = load_log(athlete)
    df_progress = df.copy()
    df_progress["Completion"] = np.where(df_progress["Completed"],1,0)
    st.markdown("### Weekly Completion Status")
    if not df_progress.empty:
        st.bar_chart(df_progress[["Run","Bike","Swim","Strength","Recovery"]].fillna(0))
    else:
        st.write("No data yet.")

# ------------------ TEAMS OVERVIEW ------------------
with tab5:
    st.markdown("### Teams Overview")
    all_data = {}
    for a in ATHLETES:
        df_a = load_log(a)
        df_a["Completion"] = np.where(df_a["Completed"],1,0)
        all_data[a] = df_a[["Date","Completion"]].set_index("Date").resample("W").sum()
    combined = pd.concat(all_data, axis=1)
    st.line_chart(combined.fillna(0))
