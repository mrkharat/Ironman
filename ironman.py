import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# ----------------- SETTINGS -----------------
st.set_page_config(page_title="Ironman Coach App", layout="wide", initial_sidebar_state="expanded")

# ---------- CONSTANTS ----------
ATHLETES = {
    "Mayur": {"gender":"M", "weight":62},
    "Sudeep": {"gender":"M", "weight":73},
    "Vaishali": {"gender":"F", "weight":64}
}

IRONMAN_DATE = datetime(2028, 7, 1, 6, 0, 0)  # Ironman Hamburg 2028 assumed
TIMEZONE = pytz.timezone('Asia/Kolkata')

# ----------------- SIDEBAR -----------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg", use_column_width=True)
st.sidebar.header("Select Athlete")
athlete = st.sidebar.selectbox("Athlete", list(ATHLETES.keys()))
st.sidebar.markdown("---")

# Countdown to Ironman Hamburg 2028
now = datetime.now(TIMEZONE)
delta = IRONMAN_DATE - now
st.sidebar.subheader("Ironman Hamburg 2028 Countdown")
st.sidebar.write(f"{delta.days} days, {delta.seconds//3600} hrs")

# ----------------- MAIN PAGE -----------------
# Greeting
hour = now.hour
if hour<12:
    greet="Good Morning"
elif hour<17:
    greet="Good Afternoon"
else:
    greet="Good Evening"

st.title(f"{greet}, {athlete}!")
st.subheader(now.strftime("%A, %d %B %Y"))

# Current week (starting Monday)
week_start = now - timedelta(days=now.weekday())
st.write(f"Current Week: {week_start.strftime('%d %b %Y')} - {(week_start + timedelta(days=6)).strftime('%d %b %Y')}")

# ---------- SAMPLE PLAN (FOR DEMO) ----------
# Weekly Activity
activity_plan = {
    "Monday":["Run 5 km 6:00-7:00", "Breakfast 7:30", "Office work", "Lunch 13:00", "Stretching 18:00", "Dinner 20:00"],
    "Tuesday":["Run 6 km 6:00-7:00", "Breakfast 7:30", "Office work", "Lunch 13:00", "Core exercises 18:00", "Dinner 20:00"],
    "Wednesday":["Rest / Walk", "Breakfast 7:30", "Office work", "Lunch 13:00", "Swimming 19:00 (Nov+)", "Dinner 20:00"],
    "Thursday":["Run 8 km 6:00-7:00", "Breakfast 7:30", "Office work", "Lunch 13:00", "Strength 18:00", "Dinner 20:00"],
    "Friday":["Cycle 20 km 6:00-7:30 (Feb 2026+)", "Breakfast 7:30", "Office work", "Lunch 13:00", "Dinner 20:00"],
    "Saturday":["Long Run 10-15 km", "Breakfast 7:30", "Lunch 13:00", "Optional Swim 18:00 (Nov+)", "Dinner 20:00"],
    "Sunday":["Rest / Yoga", "Breakfast 7:30", "Lunch 13:00", "Dinner 20:00"]
}

# Tabs for main page
tab1, tab2, tab3, tab4 = st.tabs(["Today's Plan", "Next Day Plan", "Teams Overview", "Tips & Motivation"])

# --------------- TAB 1: TODAY -----------------
with tab1:
    today_name = now.strftime("%A")
    st.header(f"Today's Plan: {today_name}")
    for task in activity_plan[today_name]:
        st.checkbox(task, key=f"{athlete}_{today_name}_{task}")

# --------------- TAB 2: NEXT DAY -----------------
with tab2:
    next_day = (now + timedelta(days=1)).strftime("%A")
    st.header(f"Next Day Plan: {next_day}")
    for task in activity_plan[next_day]:
        st.write(task)

# --------------- TAB 3: TEAMS OVERVIEW -----------------
with tab3:
    st.header("Teams Overview")
    df_progress = pd.DataFrame({
        "Athlete": list(ATHLETES.keys()),
        "Weekly Completion (%)": [np.random.randint(20,100) for _ in range(3)],
        "Next Week Load (%)": [np.random.randint(20,100) for _ in range(3)]
    })
    def highlight_max(val, column):
        max_val = df_progress[column].max()
        return ['background-color: lightgreen' if v==max_val else '' for v in val]

    styled_df = df_progress.style.apply(highlight_max, column="Weekly Completion (%)", axis=0)\
                                 .apply(highlight_max, column="Next Week Load (%)", axis=0)\
                                 .format({"Weekly Completion (%)":"{:.0f}%", "Next Week Load (%)":"{:.0f}%"})
    st.write(styled_df)

# --------------- TAB 4: TIPS & MOTIVATION -----------------
with tab4:
    st.header("Tips & Motivation")
    tips = [
        "Consistency is key: Stick to your plan daily.",
        "Recovery matters: Rest properly to avoid injuries.",
        "Nutrition fuels performance: Eat balanced meals and hydrate.",
        "Visualization helps: Imagine crossing the finish line!",
        "Track your progress weekly and celebrate small wins."
    ]
    for t in tips:
        st.info(t)

# ----------------- NUTRITION & WEIGHT TRACKER -----------------
st.subheader("Nutrition & Weight Tracker")
st.write(f"Target Ironman Weight for {athlete}: {ATHLETES[athlete]['weight']} kg")
weight = st.number_input(f"Current Weight ({athlete})", min_value=40, max_value=120, value=ATHLETES[athlete]['weight'])
st.write("Sample Meals (Indian-friendly)")
st.table(pd.DataFrame({
    "Meal":["Breakfast 7:30","Lunch 13:00","Snack 16:00","Dinner 20:00"],
    "Menu":["Oats + Milk + Banana","Roti + Sabzi + Dal","Fruits + Nuts","Rice + Dal + Veg + Chicken/Fish"],
    "Notes":["Protein-rich","Balanced carbs & protein","Energy boost","Recovery meal"]
}))
