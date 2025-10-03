import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import os
import random

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide")

DATA_DIR = "ironman_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "target_weight": 62},
    "Sudeep": {"gender": "M", "weight": 73, "target_weight": 70},
    "Vaishali": {"gender": "F", "weight": 64, "target_weight": 60}
}

PHASES = [
    ("Base", 24),   # weeks
    ("Build", 40),  # weeks
    ("Peak", 36),   # weeks
    ("Taper", 12)   # weeks
]

IRONMAN_DATE = datetime(2028, 7, 14)
QUOTE_LIST = [
    "Consistency beats intensity.",
    "Progress, not perfection.",
    "Train smart, race hard.",
    "One day at a time.",
    "Ironman starts in your mind."
]

# -------------------- UTILS --------------------
def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def get_greeting():
    hour = ist_now().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 16:
        return "Good Afternoon"
    elif 16 <= hour < 20:
        return "Good Evening"
    else:
        return "Good Night"

def get_week_num(today):
    return ((today - date(2025,10,1)).days // 7) + 1

def get_phase(week_num):
    total_weeks = 0
    for name, length in PHASES:
        if week_num <= total_weeks + length:
            return name
        total_weeks += length
    return "Taper"

def load_log(athlete):
    path = f"{DATA_DIR}/{athlete}_log.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Date", "Activity", "Completed", "Phase"])

def save_log(athlete, df):
    df.to_csv(f"{DATA_DIR}/{athlete}_log.csv", index=False)

def get_countdown():
    delta = IRONMAN_DATE - ist_now()
    return f"{delta.days}d {delta.seconds//3600}h:{(delta.seconds//60)%60}m left"

def generate_daily_plan(athlete, today):
    week_num = get_week_num(today)
    phase = get_phase(week_num)
    plan = []

    # Running
    if phase == "Base":
        plan.append({"Activity":"Run 5 km","Time":"6:30 AM"})
    elif phase == "Build":
        plan.append({"Activity":"Run 10 km","Time":"6:30 AM"})
    elif phase == "Peak":
        plan.append({"Activity":"Run 15 km","Time":"6:00 AM"})
    else:
        plan.append({"Activity":"Light Run 5 km","Time":"6:30 AM"})

    # Cycling (from Feb 2026)
    if today >= date(2026,2,1):
        if phase in ["Build","Peak"]:
            km = 15 if phase=="Build" else 30
            plan.append({"Activity":f"Bike {km} km","Time":"7:30 AM"})
        elif phase=="Taper":
            plan.append({"Activity":"Light Bike 10 km","Time":"7:30 AM"})

    # Swimming (from Nov 2025)
    if today >= date(2025,11,1):
        if phase in ["Build","Peak"]:
            plan.append({"Activity":"Swim 1 km","Time":"6:00 PM"})
        elif phase=="Taper":
            plan.append({"Activity":"Light Swim 500 m","Time":"6:00 PM"})

    # Stretching
    plan.append({"Activity":"Stretch 15 min","Time":"7:15 AM"})

    # Nutrition
    nutrition = [
        {"Meal":"Breakfast","Time":"7:30 AM","Food":"Oats + Banana + Milk"},
        {"Meal":"Lunch","Time":"1:00 PM","Food":"Rice + Dal + Veg"},
        {"Meal":"Snack","Time":"4:30 PM","Food":"Fruits / Nuts"},
        {"Meal":"Dinner","Time":"8:00 PM","Food":"Roti + Paneer/Chicken + Salad"}
    ]

    return plan, nutrition, phase

# -------------------- SIDEBAR --------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg", use_column_width=True)
athlete_name = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown("### Countdown to Ironman Hamburg 2028")
st.sidebar.markdown(f"**{get_countdown()}**")
st.sidebar.markdown("### Quote of the Day")
st.sidebar.info(random.choice(QUOTE_LIST))

# -------------------- MAIN PAGE --------------------
st.title(f"{get_greeting()}, {athlete_name}!")
today = ist_now().date()
st.markdown(f"**Today:** {today.strftime('%A, %d %b %Y')}")
st.markdown(f"**Week:** {get_week_num(today)} ({get_phase(get_week_num(today))})")

# Load log
df_log = load_log(athlete_name)

# Tabs
tab1, tab2, tab3 = st.tabs(["Today's Plan","Next Day Plan","Team Overview"])

# -------------------- TODAY'S PLAN --------------------
with tab1:
    st.subheader("Activities & Nutrition")
    plan, nutrition, phase = generate_daily_plan(athlete_name, today)

    for act in plan:
        completed = st.checkbox(f"{act['Time']} - {act['Activity']}", key=f"{athlete_name}_{act['Activity']}_{today}")
        if completed:
            if not ((df_log['Date']==str(today)) & (df_log['Activity']==act['Activity'])).any():
                df_log = pd.concat([df_log,pd.DataFrame([{
                    "Date":today,"Activity":act['Activity'],"Completed":True,"Phase":phase
                }])],ignore_index=True)

    st.markdown("**Nutrition Plan**")
    for meal in nutrition:
        st.markdown(f"{meal['Time']} - {meal['Meal']}: {meal['Food']}")

    st.markdown("**Weight Tracker**")
    weight_input = st.number_input("Enter current weight (kg)", value=ATHLETES[athlete_name]["weight"])
    st.markdown(f"Target weight: **{ATHLETES[athlete_name]['target_weight']} kg**")

    save_log(athlete_name, df_log)

# -------------------- NEXT DAY PLAN --------------------
with tab2:
    next_day = today + timedelta(days=1)
    plan_next, nutrition_next, phase_next = generate_daily_plan(athlete_name, next_day)
    st.subheader(f"Plan for {next_day.strftime('%A, %d %b %Y')}")
    for act in plan_next:
        st.markdown(f"{act['Time']} - {act['Activity']}")
    st.markdown("**Nutrition**")
    for meal in nutrition_next:
        st.markdown(f"{meal['Time']} - {meal['Meal']}: {meal['Food']}")

# -------------------- TEAM OVERVIEW --------------------
with tab3:
    st.subheader("Team Progress")
    progress_data = []
    for athlete in ATHLETES:
        df = load_log(athlete)
        completed = df[df['Completed']==True].shape[0]
        total = df.shape[0] if df.shape[0]>0 else 1
        progress_data.append({"Athlete":athlete,"Progress (%)":round((completed/total)*100,1)})
    df_progress = pd.DataFrame(progress_data)
    st.dataframe(df_progress.style.bar(subset=["Progress (%)"], color='#4CAF50'))
