import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from PIL import Image
import random

# ------------------- SETTINGS -------------------
st.set_page_config(
    page_title="Ironman Training Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- SIDEBAR -------------------
# Logo
logo_url = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
st.sidebar.image(logo_url, use_column_width=True)

# Athlete selection
athlete = st.sidebar.selectbox("Select Athlete", ["Mayur", "Sudeep", "Vaishali"])

# Countdown to Ironman Hamburg 2028
ironman_date = datetime(2028, 7, 15)  # update exact date if needed
now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
days_left = (ironman_date - now_ist).days
st.sidebar.markdown(f"### 🕒 Days to Ironman Hamburg 2028: {days_left} days")

# Motivational quote
quotes = [
    "Your only limit is you.",
    "One step at a time, one swim, bike, run at a time.",
    "Ironman is a journey, not a race.",
    "Consistency beats intensity.",
    "Pain is temporary, pride is forever."
]
st.sidebar.markdown(f"**Quote of the Day:**\n\n_{random.choice(quotes)}_")

# ------------------- MAIN PAGE -------------------
st.title(f"Hello {athlete}! 👋")

# IST time
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
hour = now.hour
if 5 <= hour < 12:
    greeting = "Good Morning"
elif 12 <= hour < 17:
    greeting = "Good Afternoon"
elif 17 <= hour < 21:
    greeting = "Good Evening"
else:
    greeting = "Good Night"

st.subheader(f"{greeting}! Today is {now.strftime('%A, %d %B %Y')}")

# Week number starting Monday
week_start = now - timedelta(days=now.weekday())
st.markdown(f"**Week Starting:** {week_start.strftime('%d %b %Y')}")

# ------------------- ATHLETE DATA -------------------
athlete_info = {
    "Mayur": {"weight": 62, "target_weight": 60},
    "Sudeep": {"weight": 73, "target_weight": 70},
    "Vaishali": {"weight": 64, "target_weight": 58}
}

# ------------------- TRAINING PHASES -------------------
# Base: Oct 2025 - Mar 2026
# Build: Apr 2026 - Mar 2027
# Peak: Apr 2027 - Mar 2028
# Taper: Apr 2028 - Jul 2028

def get_phase(date):
    if date < datetime(2026, 4, 1):
        return "Base"
    elif date < datetime(2027, 4, 1):
        return "Build"
    elif date < datetime(2028, 4, 1):
        return "Peak"
    else:
        return "Taper"

phase = get_phase(now)

# ------------------- WEEKLY TRAINING TEMPLATE -------------------
def weekly_plan(athlete, phase):
    # Run, Swim, Bike, Strength, Recovery load based on phase and athlete
    plan = []
    weight = athlete_info[athlete]["weight"]
    target_weight = athlete_info[athlete]["target_weight"]

    for day in range(7):
        day_plan = {}
        day_plan['Day'] = (week_start + timedelta(days=day)).strftime('%A')

        # Running (km)
        if phase == "Base":
            run = 5 + day  # progressive
            swim = 0 if now < datetime(2025, 11, 1) else 20  # swim starts Nov 2025
            bike = 0  # bike starts Feb 2026
        elif phase == "Build":
            run = 8 + day
            swim = 25
            bike = 30
        elif phase == "Peak":
            run = 12 + day
            swim = 40
            bike = 60
        else:  # Taper
            run = 6 + day
            swim = 20
            bike = 30

        day_plan['Run (km)'] = run
        day_plan['Swim (min)'] = swim
        day_plan['Bike (km)'] = bike
        day_plan['Strength (min)'] = 30
        day_plan['Recovery (min)'] = 20
        # Nutrition - Indian timings
        day_plan['Breakfast'] = "7:30 AM - Oats / Poha / Upma + milk"
        day_plan['Mid-Morning Snack'] = "10:30 AM - Fruits / Nuts"
        day_plan['Lunch'] = "1:00 PM - Chapati/Rice + Veg + Dal + Salad"
        day_plan['Evening Snack'] = "4:30 PM - Sprouts / Fruit Smoothie"
        day_plan['Dinner'] = "8:00 PM - Chapati + Veg + Protein"
        # Weight tracker
        day_plan['Current Weight'] = weight
        day_plan['Target Weight'] = target_weight

        plan.append(day_plan)
    return pd.DataFrame(plan)

df_today_week = weekly_plan(athlete, phase)

# ------------------- TABS -------------------
tabs = st.tabs(["Today's Plan ✅", "Next Day Plan 🔜", "Weekly Overview 📊", "Team Overview 🌟", "Logs 📁"])

# ------------------- TODAY'S PLAN -------------------
with tabs[0]:
    st.subheader("Today's Training Plan")
    today_day = now.weekday()
    df_today = df_today_week.iloc[[today_day]]
    
    # Activities with checkboxes
    st.markdown("**Activities**")
    for activity in ['Run (km)', 'Swim (min)', 'Bike (km)', 'Strength (min)', 'Recovery (min)']:
        completed = st.checkbox(f"{activity}: {df_today.iloc[0][activity]}", key=f"{athlete}_{activity}")
        if completed:
            df_today.at[0, activity] = f"✅ {df_today.iloc[0][activity]}"
    
    # Nutrition
    st.markdown("**Nutrition Plan**")
    for meal in ['Breakfast', 'Mid-Morning Snack', 'Lunch', 'Evening Snack', 'Dinner']:
        st.checkbox(f"{meal}: {df_today.iloc[0][meal]}", key=f"{athlete}_{meal}")

    # Weight tracker
    st.markdown(f"**Weight Tracker:** Current: {df_today.iloc[0]['Current Weight']} kg | Target: {df_today.iloc[0]['Target Weight']} kg")
    
    # Motivation tip
    tip = random.choice(quotes)
    st.markdown(f"**Tip for Today:** _{tip}_")

# ------------------- NEXT DAY PLAN -------------------
with tabs[1]:
    st.subheader("Next Day Plan")
    df_next = df_today_week.iloc[[(today_day+1)%7]]
    st.table(df_next[['Day','Run (km)','Swim (min)','Bike (km)','Strength (min)','Recovery (min)','Breakfast','Lunch','Dinner']])

# ------------------- WEEKLY OVERVIEW -------------------
with tabs[2]:
    st.subheader("Weekly Overview")
    st.table(df_today_week[['Day','Run (km)','Swim (min)','Bike (km)','Strength (min)','Recovery (min)']])

# ------------------- TEAM OVERVIEW -------------------
with tabs[3]:
    st.subheader("Team Overview")
    df_team = pd.DataFrame({
        'Athlete': ['Mayur','Sudeep','Vaishali'],
        'Run km': [df_today_week['Run (km)'].sum() for _ in range(3)],
        'Swim min': [df_today_week['Swim (min)'].sum() for _ in range(3)],
        'Bike km': [df_today_week['Bike (km)'].sum() for _ in range(3)],
        'Strength min': [df_today_week['Strength (min)'].sum() for _ in range(3)]
    })
    st.bar_chart(df_team.set_index('Athlete'))

# ------------------- LOGS -------------------
with tabs[4]:
    st.subheader("Logs")
    st.table(df_today_week)

st.markdown("---")
st.markdown(f"*Phase:* {phase} | *Week Start:* {week_start.strftime('%d %b %Y')}")
