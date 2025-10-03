# Ironman Training Coach App
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import random

# -------------------- SETTINGS --------------------
st.set_page_config(page_title="Ironman Coach", layout="wide", initial_sidebar_state="expanded")

# -------------------- DATA --------------------
ATHLETES = {
    "Mayur": {"gender":"M", "weight":62, "dob":"25-12"},
    "Sudeep": {"gender":"M", "weight":73, "dob":"31-10"},
    "Vaishali": {"gender":"F", "weight":64, "dob":"02-04"}
}

IRONMAN_DATE = datetime(2028,7,15,0,0)  # Hamburg full Ironman
TIMEZONE = pytz.timezone("Asia/Kolkata")

INDIAN_MEALS = {
    "Breakfast":"7:30 AM - Oats/Poha/Daliya + Milk/Tea/Coffee",
    "Mid-morning Snack":"10:30 AM - Fruits/Seeds",
    "Lunch":"1:00 PM - Rice/Roti + Dal + Veg + Salad",
    "Evening Snack":"5:00 PM - Nuts/Protein Shake",
    "Dinner":"8:00 PM - Roti + Veg + Soup/Salad"
}

SUNDAY_ACTIVITIES = ["Hike", "Long Drive", "Plantation Drive", "Cycling leisurely", "Yoga/Stretching"]

QUOTES = [
    "Pain is temporary, Ironman is forever.",
    "Every swim, bike, run counts.",
    "Consistency beats intensity.",
    "Ironman is 90% mental."
]

FESTIVALS = {
    "15-08":"Independence Day",
    "26-01":"Republic Day",
    "14-04":"Ambedkar Jayanti",
    "12-11":"Diwali 2025"  # example, can extend
}

# -------------------- SIDEBAR --------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg?raw=true", use_container_width=True)
athlete_name = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
today = datetime.now(TIMEZONE)
st.sidebar.write(f"Countdown to Ironman Hamburg: {(IRONMAN_DATE - today).days} days")
st.sidebar.write(f"Quote of the Day: {random.choice(QUOTES)}")

# Birthday or festival
dob_str = ATHLETES[athlete_name]["dob"]
today_str = today.strftime("%d-%m")
if today_str == dob_str:
    st.sidebar.write(f"🎉 Happy Birthday {athlete_name}!")
elif today_str in FESTIVALS:
    st.sidebar.write(f"Today's Special: {FESTIVALS[today_str]}")

# -------------------- MAIN PAGE --------------------
# Greetings
hour = today.hour
greet = "Good Morning" if hour<12 else ("Good Afternoon" if hour<16 else "Good Evening")
st.markdown(f"## {greet}, {athlete_name}!")
st.markdown(f"**Today:** {today.strftime('%A, %d %B %Y')}")
st.markdown(f"**Week of:** {(today - timedelta(days=today.weekday())).strftime('%d %b %Y')}")

# -------------------- TRAINING PLAN PHASE --------------------
phase_weeks = {
    "Base": 12,
    "Build": 24,
    "Peak": 36,
    "Taper": 12
}
# Determine current phase
total_weeks_passed = (today - datetime(2025,10,1,0,0, tzinfo=TIMEZONE)).days // 7
if total_weeks_passed < phase_weeks["Base"]:
    phase = "Base"
elif total_weeks_passed < phase_weeks["Base"]+phase_weeks["Build"]:
    phase = "Build"
elif total_weeks_passed < phase_weeks["Base"]+phase_weeks["Build"]+phase_weeks["Peak"]:
    phase = "Peak"
else:
    phase = "Taper"
st.markdown(f"**Current Phase:** {phase}")

# -------------------- TRAINING PLAN --------------------
# Simplified weekly plan (adjust dynamically)
plan = {
    "Run":"30-60 min easy run" if phase=="Base" else "45-90 min varied pace",
    "Bike":"N/A until Feb 2026" if today<datetime(2026,2,1, tzinfo=TIMEZONE) else "60-120 min cycling",
    "Swim":"Learning from Nov 2025" if today<datetime(2025,11,1, tzinfo=TIMEZONE) else "30-60 min swim drills",
    "Strength":"20-30 min bodyweight/core",
    "Recovery":"Stretching/Yoga 15-20 min"
}

# Today’s Plan with checkboxes
st.subheader("Today's Training Plan")
completed = {}
for key, val in plan.items():
    completed[key] = st.checkbox(f"{key}: {val}")

# -------------------- NUTRITION --------------------
st.subheader("Today's Nutrition Plan")
for meal,time_desc in INDIAN_MEALS.items():
    st.write(f"**{meal}:** {time_desc}")

# -------------------- SLEEP & WEIGHT --------------------
st.subheader("Sleep & Weight Tracker")
sleep_hours = st.number_input("Sleep hours last night", min_value=0, max_value=12, value=7)
weight = st.number_input(f"Current Weight ({athlete_name}) in kg", min_value=40, max_value=120, value=ATHLETES[athlete_name]["weight"])

# -------------------- SUNDAY ACTIVITY --------------------
if today.weekday()==6:
    st.subheader("Sunday Optional Activity")
    sunday_act = random.choice(SUNDAY_ACTIVITIES)
    st.write(f"Suggested activity: **{sunday_act}**")
    # Joint activity once a month
    if today.day <=7: 
        st.write("Suggested joint activity for all athletes this month: Beach Clean-up / Group Hike")

# -------------------- NEXT DAY PLAN --------------------
st.subheader("Next Day Plan")
next_day = today + timedelta(days=1)
st.write(f"**Date:** {next_day.strftime('%A, %d %B %Y')}")
for key, val in plan.items():
    st.write(f"{key}: {val}")
for meal,time_desc in INDIAN_MEALS.items():
    st.write(f"**{meal}:** {time_desc}")

# -------------------- TEAM OVERVIEW --------------------
st.subheader("Team Overview")
team_df = pd.DataFrame({
    "Athlete": list(ATHLETES.keys()),
    "Weight": [ATHLETES[a]["weight"] for a in ATHLETES],
    "Sleep": [7,6,7],  # sample
    "Progress (%)":[random.randint(10,50) for _ in ATHLETES]
})
st.dataframe(team_df.style.format({"Progress (%)":"{:.0f}%"}).highlight_max(axis=0, color="lightgreen"))

# -------------------- MOTIVATIONAL TIP --------------------
st.subheader("Tip of the Day")
tip = "Consistency is key. Log your nutrition, sleep, and training daily. Celebrate small victories!"
st.info(tip)
