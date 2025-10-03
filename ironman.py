# ironman_professional.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PIL import Image

# -------------------- Constants --------------------
st.set_page_config(page_title="Ironman Pro Coach", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    "<style>body{background-color:#121212;color:white;} .stButton>button{background-color:#1E90FF;color:white;}</style>", 
    unsafe_allow_html=True
)

ATHLETES = {
    "Mayur": {"sex": "M", "weight": 62},
    "Sudeep": {"sex": "M", "weight": 73},
    "Vaishali": {"sex": "F", "weight": 64}
}

IRONMAN_HAMBURG_DATE = datetime(2028, 7, 15, 7, 0)

# -------------------- Helper Functions --------------------
def get_ist_time():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def get_greeting():
    hour = get_ist_time().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 21:
        return "Good Evening"
    else:
        return "Good Night"

def generate_weekly_plan(athlete):
    today = get_ist_time()
    week_start = today - timedelta(days=today.weekday())
    plan = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_plan = {"Date": day, "Activity": [], "Nutrition": [], "Sleep": "7-8 hrs", "Tips": []}
        
        # Activities based on timeline
        if day < datetime(2025,11,1):
            day_plan["Activity"].append("Run 5-10 km")
            day_plan["Tips"].append("Focus on running form and breathing")
        else:
            day_plan["Activity"].append("Swim 500-1000 m")
            day_plan["Tips"].append("Focus on stroke efficiency")
            if day >= datetime(2026,2,1):
                day_plan["Activity"].append("Cycle 20-40 km")
                day_plan["Tips"].append("Maintain cadence and practice nutrition on bike")
        
        # Nutrition
        day_plan["Nutrition"] = [
            "07:30 - Breakfast",
            "10:30 - Mid-morning Snack",
            "13:00 - Lunch",
            "16:30 - Evening Snack",
            "20:00 - Dinner"
        ]
        day_plan["Tips"].append("Stay hydrated and follow meal timings")
        
        plan.append(day_plan)
    return plan

def get_today_tip(plan_today, completed_activities=[]):
    tips = []
    for idx, act in enumerate(plan_today["Activity"]):
        if act not in completed_activities:
            tips.append(f"Reminder: {act} – {plan_today['Tips'][idx]}")
    return tips if tips else ["Excellent! You completed today's activities."]

# -------------------- Sidebar --------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg?raw=true", use_container_width=True)
st.sidebar.title("Ironman Pro Coach")
selected_athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
today = get_ist_time()
st.sidebar.write(f"{get_greeting()}, {selected_athlete}!")
st.sidebar.write(f"Today: {today.strftime('%A, %d %B %Y')}")
week_start = today - timedelta(days=today.weekday())
st.sidebar.write(f"Week Start: {week_start.strftime('%d %b %Y')}")
days_left = (IRONMAN_HAMBURG_DATE - today).days
st.sidebar.write(f"Ironman Hamburg 2028 in **{days_left} days**")
st.sidebar.write(f"Target Weight: **{ATHLETES[selected_athlete]['weight']} kg**")

# -------------------- Main Page --------------------
st.title(f"{get_greeting()}, {selected_athlete}!")
st.subheader(f"Today: {today.strftime('%A, %d %B %Y')} | Week Start: {week_start.strftime('%d %b %Y')}")

weekly_plan = generate_weekly_plan(selected_athlete)

# -------------------- Tabs --------------------
tab1, tab2, tab3 = st.tabs(["Today's Plan", "Next Day Preview", "Teams Overview"])

# ----------- Today's Plan Tab -----------
with tab1:
    st.header("Today's Plan")
    today_plan = weekly_plan[0]
    completed_activities = []
    
    st.subheader("Activities")
    for idx, act in enumerate(today_plan["Activity"]):
        if st.checkbox(act, key=f"activity_{selected_athlete}_{idx}"):
            completed_activities.append(act)
            
    st.subheader("Nutrition")
    for idx, meal in enumerate(today_plan["Nutrition"]):
        st.checkbox(meal, key=f"meal_{selected_athlete}_{idx}")
        
    st.subheader("Sleep")
    st.checkbox(today_plan["Sleep"], key=f"sleep_{selected_athlete}")
    
    st.subheader("Coach's Tips & Motivation")
    for tip in get_today_tip(today_plan, completed_activities):
        st.info(tip)

# ----------- Next Day Preview Tab -----------
with tab2:
    st.header("Next Day Plan Preview")
    next_day_plan = weekly_plan[1]
    st.subheader("Activities")
    for act in next_day_plan["Activity"]:
        st.text(act)
    st.subheader("Nutrition")
    for meal in next_day_plan["Nutrition"]:
        st.text(meal)
    st.subheader("Sleep")
    st.text(next_day_plan["Sleep"])
    st.subheader("Tips")
    for tip in next_day_plan["Tips"]:
        st.info(tip)

# ----------- Teams Overview Tab -----------
with tab3:
    st.header("Teams Overview")
    df_progress = pd.DataFrame({
        "Athlete": list(ATHLETES.keys()),
        "Weekly Completion (%)": [np.random.randint(20,100) for _ in range(3)],
        "Next Week Load (%)": [np.random.randint(20,100) for _ in range(3)]
    })
    st.dataframe(df_progress.style.format("{:.0f}%").highlight_max(axis=0, color='lightgreen'))

# -------------------- End --------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.caption("Ironman Pro Coach App – Personalized Plan | Interactive Checkboxes | Tips & Motivation")
