# ironman_tracker_fixed.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pytz
import random

# ---------------------- SETTINGS ----------------------
st.set_page_config(page_title="Ironman 2028 Coach", layout="wide", initial_sidebar_state="expanded", page_icon=None)
DATA_DIR = "athlete_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------- DARK THEME ----------------------
st.markdown("""
<style>
body {
    background-color: #0E1117;
    color: #FFFFFF;
}
.stButton>button {
    background-color: #1F2A40;
    color: #FFFFFF;
}
.stCheckbox>div>label {
    color: #FFFFFF;
}
.stDataFrame th {
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- ATHLETES ----------------------
ATHLETES = {
    "Mayur": {"gender":"M", "weight":62, "dob":"25-12"},
    "Sudeep": {"gender":"M", "weight":73, "dob":"31-10"},
    "Vaishali": {"gender":"F", "weight":64, "dob":"02-04"}
}

# ---------------------- IRONMAN DATE ----------------------
tz = pytz.timezone('Asia/Kolkata')
ironman_date = tz.localize(datetime(2028, 7, 14, 6, 0, 0))  # Hamburg
now = datetime.now(tz)

# ---------------------- QUOTES & SUNDAY ACTIVITIES ----------------------
quotes = [
    "Consistency beats intensity.",
    "Every stroke, every pedal, every step counts.",
    "Ironman is 90% mental.",
    "Progress, not perfection.",
    "Strong body, stronger mind."
]

sunday_activities = [
    "Go for a hike",
    "Long drive together",
    "Plantation drive",
    "Group cycling (if available)",
    "Beach run",
    "Yoga session together",
    "Meditation retreat"
]

# ---------------------- FESTIVALS ----------------------
festivals = {
    "01-01":"New Year",
    "15-08":"Independence Day",
    "02-10":"Gandhi Jayanti",
    "25-12":"Christmas"
}

# ---------------------- LOGO ----------------------
logo_url = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"

# ---------------------- SIDEBAR ----------------------
st.sidebar.image(logo_url, use_container_width=True)
athlete_name = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.write("---")

# Countdown
delta = ironman_date - now
days_left = delta.days
st.sidebar.subheader("Ironman Hamburg 2028 Countdown")
st.sidebar.write(f"{days_left} Days Left")

# Quote
st.sidebar.write("---")
st.sidebar.subheader("Quote of the Day")
st.sidebar.write(random.choice(quotes))

# Today's Special
today_str = now.strftime("%d-%m")
special = ""
if today_str in festivals:
    special = f"Festival: {festivals[today_str]}"
elif today_str == ATHLETES[athlete_name]["dob"]:
    special = f"Happy Birthday, {athlete_name}!"
if special:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(special)

# ---------------------- GREETING ----------------------
hour = now.hour
if hour < 12:
    greeting = "Good Morning"
elif hour < 16:
    greeting = "Good Afternoon"
else:
    greeting = "Good Evening"

st.title(f"{greeting}, {athlete_name}!")
st.write(f"Date: {now.strftime('%A, %d %B %Y')}")
week_start = now - timedelta(days=now.weekday())
st.write(f"Week starting: {week_start.strftime('%d %b %Y')}")

# ---------------------- DATA FILE ----------------------
data_file = os.path.join(DATA_DIR, f"{athlete_name}_log.csv")
if os.path.exists(data_file):
    df_log = pd.read_csv(data_file, parse_dates=["Date"])
else:
    # Initialize log
    df_log = pd.DataFrame(columns=["Date","Phase","Activity","Nutrition","Sleep","Weight","Recovery"])
    df_log.to_csv(data_file,index=False)

# ---------------------- PHASE CALCULATION ----------------------
phases = ["Base","Build","Peak","Taper"]
phase_weeks = {"Base":20,"Build":40,"Peak":20,"Taper":10}  # approx

total_weeks = sum(phase_weeks.values())
week_number = ((now - tz.localize(datetime(2025,10,1,0,0,0))).days)//7 +1
phase_cumsum = np.cumsum(list(phase_weeks.values()))
for i,pc in enumerate(phase_cumsum):
    if week_number <= pc:
        current_phase = phases[i]
        break
else:
    current_phase = "Taper"

# ---------------------- ACTIVITY PLAN ----------------------
def generate_daily_plan(athlete, today):
    weight = ATHLETES[athlete]["weight"]
    weekday = today.weekday()
    # Phase based distances
    if current_phase=="Base":
        run_km = 5 + 0.1*week_number
        bike_km = 0
        swim_m = 0
    elif current_phase=="Build":
        run_km = 10 + 0.2*week_number
        bike_km = 20
        swim_m = 200
    elif current_phase=="Peak":
        run_km = 15 + 0.2*week_number
        bike_km = 40
        swim_m = 500
    else:  # Taper
        run_km = 8
        bike_km = 20
        swim_m = 200

    # Nutrition (Indian timings)
    nutrition = {
        "07:30":"Milk + Oats + Banana",
        "10:30":"Fruits / Nuts",
        "13:30":"Rice / Roti + Dal + Veg + Salad",
        "16:30":"Protein Shake / Fruits",
        "20:00":"Roti + Veg + Soup"
    }

    # Sunday Special
    sunday_activity = ""
    if weekday==6:
        sunday_activity = random.choice(sunday_activities)

    return run_km,bike_km,swim_m,nutrition,sunday_activity

run_km,bike_km,swim_m,nutrition,sunday_activity = generate_daily_plan(athlete_name, now)

# ---------------------- TAB LAYOUT ----------------------
tabs = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Progress Tracker","Weight & Sleep Tracker","Team Overview"])

# ---------------------- TODAY'S PLAN ----------------------
with tabs[0]:
    st.subheader("Activity Plan")
    col1,col2,col3 = st.columns(3)
    col1.checkbox(f"Run {run_km:.1f} km", key="run")
    col2.checkbox(f"Bike {bike_km:.1f} km", key="bike")
    col3.checkbox(f"Swim {swim_m:.0f} m", key="swim")

    st.subheader("Nutrition Plan")
    for time, meal in nutrition.items():
        st.checkbox(f"{time} - {meal}", key=f"meal_{time}")

    st.subheader("Sunday Special Activity")
    if sunday_activity:
        st.write(sunday_activity)
    else:
        st.write("Regular training day.")

    st.subheader("Sleep & Recovery")
    sleep_hours = st.slider("Sleep Hours", 0,12,8)
    weight = st.number_input("Current Weight (kg)", ATHLETES[athlete_name]["weight"])
    recovery = st.slider("Recovery level",0,100,50)

    # Save today's data
    df_log_today = pd.DataFrame([{
        "Date":now.strftime("%Y-%m-%d"),
        "Phase":current_phase,
        "Activity":f"Run:{run_km}, Bike:{bike_km}, Swim:{swim_m}",
        "Nutrition":str(nutrition),
        "Sleep":sleep_hours,
        "Weight":weight,
        "Recovery":recovery
    }])
    df_log = df_log[df_log["Date"]!=now.strftime("%Y-%m-%d")]
    df_log = pd.concat([df_log, df_log_today])
    df_log.to_csv(data_file,index=False)

# ---------------------- NEXT DAY PLAN ----------------------
next_day = now + timedelta(days=1)
next_run,next_bike,next_swim,next_nutrition,next_sunday_activity = generate_daily_plan(athlete_name, next_day)
with tabs[1]:
    st.subheader(f"Plan for {next_day.strftime('%A, %d %B %Y')}")
    col1,col2,col3 = st.columns(3)
    col1.write(f"Run: {next_run:.1f} km")
    col2.write(f"Bike: {next_bike:.1f} km")
    col3.write(f"Swim: {next_swim:.0f} m")
    st.subheader("Nutrition")
    for time, meal in next_nutrition.items():
        st.write(f"{time} - {meal}")
    if next_sunday_activity:
        st.subheader("Sunday Special")
        st.write(next_sunday_activity)
    # Birthday/Festival
    next_day_str = next_day.strftime("%d-%m")
    special_next = ""
    if next_day_str in festivals:
        special_next = f"Festival: {festivals[next_day_str]}"
    elif next_day_str == ATHLETES[athlete_name]["dob"]:
        special_next = f"Happy Birthday, {athlete_name}!"
    if special_next:
        st.subheader("Special Message")
        st.write(special_next)

# ---------------------- WEEKLY PLAN ----------------------
with tabs[2]:
    st.subheader("Weekly Overview")
    week_start = now - timedelta(days=now.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    weekly_df = []
    for d in week_dates:
        run,bike,swim,nutrition,sunday_act = generate_daily_plan(athlete_name,d)
        weekly_df.append({
            "Date":d.strftime("%A"),
            "Run_km":run,
            "Bike_km":bike,
            "Swim_m":swim,
            "Sunday_Activity":sunday_act
        })
    st.dataframe(pd.DataFrame(weekly_df).style.format("{:.1f}"))

# ---------------------- PROGRESS TRACKER ----------------------
with tabs[3]:
    st.subheader("Training Progress")
    st.write(f"Current Phase: {current_phase}")
    if not df_log.empty:
        df_log["Progress(%)"] = (week_number/total_weeks)*100
        st.bar_chart(df_log.set_index("Date")[["Progress(%)"]])

# ---------------------- WEIGHT & SLEEP TRACKER ----------------------
with tabs[4]:
    st.subheader("Weight & Sleep Trends")
    if not df_log.empty:
        st.line_chart(df_log.set_index("Date")[["Weight","Sleep"]])

# ---------------------- TEAM OVERVIEW ----------------------
with tabs[5]:
    st.subheader("Team Overview")
    team_data = []
    for ath in ATHLETES.keys():
        f = os.path.join(DATA_DIR, f"{ath}_log.csv")
        if os.path.exists(f):
            df = pd.read_csv(f, parse_dates=["Date"])
            team_data.append(df.tail(7).assign(Athlete=ath))
    if team_data:
        team_df = pd.concat(team_data)
        st.dataframe(team_df)

