import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import random

# ---------------------------- SETTINGS ----------------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide", initial_sidebar_state="expanded")

# Dark theme styling
st.markdown("""
    <style>
    .css-1d391kg {background-color: #0e1117;}
    .css-1v3fvcr {background-color: #0e1117;}
    .stButton>button {background-color:#1f77b4;color:white;border-radius:5px;}
    .st-bf {color:white;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------- CONSTANTS ----------------------------
tz = pytz.timezone('Asia/Kolkata')
today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

ATHLETES = {
    "Mayur": {"gender":"M", "weight":62},
    "Sudeep": {"gender":"M", "weight":73},
    "Vaishali": {"gender":"F", "weight":64}
}

IRONMAN_DATE = tz.localize(datetime(2028, 7, 14, 6, 0))  # Hamburg Ironman
QUOTES = [
    "Every champion was once a beginner.",
    "Consistency is the key to improvement.",
    "Train hard, race easy."
]

BIRTHDAYS = {
    "Mayur": (25,12),
    "Sudeep": (31,10),
    "Vaishali": (2,4)
}

# Sample Sunday activities
SUNDAY_ACTIVITIES = ["Hiking", "Long drive", "Plantation drive", "Beach walk", "Cycling together", "Meditation session"]

# ---------------------------- SIDEBAR ----------------------------
st.sidebar.image("https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg", use_column_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
delta = IRONMAN_DATE - datetime.now(tz)
st.sidebar.markdown(f"**Countdown to Ironman Hamburg:** {delta.days} days")

quote_today = random.choice(QUOTES)
st.sidebar.markdown(f"**Quote of the Day:**\n> {quote_today}")

# Todays special (birthday or Indian festival placeholder)
day, month = today.day, today.month
special_msg = ""
for name, (b_day, b_month) in BIRTHDAYS.items():
    if b_day==day and b_month==month:
        special_msg = f"🎉 Happy Birthday {name}!"
st.sidebar.markdown(f"**Today's Special:** {special_msg if special_msg else 'None'}")

# ---------------------------- MAIN PAGE ----------------------------
st.title(f"Hello {athlete}!")
hour = datetime.now(tz).hour
if hour<12:
    greeting="Good Morning"
elif hour<17:
    greeting="Good Afternoon"
else:
    greeting="Good Evening"
st.subheader(f"{greeting}! Today is {today.strftime('%A, %d %B %Y')}")

# Week info
week_start = today - timedelta(days=today.weekday())
week_number = (today - tz.localize(datetime(2025,10,1))).days//7 + 1
st.markdown(f"**Week {week_number}** | Phase: Base/Build/Peak/Taper")

# ---------------------------- TRAINING PLAN ----------------------------
def generate_daily_plan(athlete_name, date):
    """Generate daily plan dynamically based on athlete and phase"""
    base_plan = {
        "Running (km)": 0,
        "Cycling (km)": 0,
        "Swimming (m)": 0,
        "Strength (min)": 0,
        "Recovery":0,
        "Breakfast":"Poha", "Lunch":"Dal, Rice, Veg", "Snacks":"Fruits", "Dinner":"Chapati, Veg, Dal",
        "Breakfast Time":"7:30 am","Lunch Time":"1:00 pm","Snacks Time":"4:30 pm","Dinner Time":"8:00 pm",
        "Weight":ATHLETES[athlete_name]["weight"], "Sleep":7
    }
    weekday = date.weekday()
    # Adjust cycling & swimming based on date
    if date>=tz.localize(datetime(2025,11,1)):
        base_plan["Swimming (m)"]=500
    if date>=tz.localize(datetime(2026,2,1)):
        base_plan["Cycling (km)"]=20
    if weekday==6: # Sunday suggestions
        base_plan["Running (km)"]=5
        base_plan["Cycling (km)"]=0
        base_plan["Swimming (m)"]=0
        base_plan["Activity Suggestion"]=random.choice(SUNDAY_ACTIVITIES)
    else:
        base_plan["Running (km)"]=5+random.randint(0,5)
        base_plan["Strength (min)"]=30
    return base_plan

df_today = pd.DataFrame([generate_daily_plan(athlete, today)])

# Checkbox for tasks
st.markdown("### Today's Plan")
for col in df_today.columns:
    if col not in ["Weight","Sleep","Activity Suggestion"]:
        completed = st.checkbox(f"{col}: {df_today[col].values[0]}", key=f"{athlete}_{col}")
    else:
        st.markdown(f"**{col}: {df_today[col].values[0]}**")

# ---------------------------- NEXT DAY PLAN ----------------------------
next_day = today + timedelta(days=1)
df_next = pd.DataFrame([generate_daily_plan(athlete, next_day)])
st.markdown("### Next Day Plan")
for col in df_next.columns:
    if col not in ["Weight","Sleep","Activity Suggestion"]:
        st.markdown(f"{col}: {df_next[col].values[0]}")
    else:
        st.markdown(f"**{col}: {df_next[col].values[0]}**")

# ---------------------------- TEAMS OVERVIEW ----------------------------
st.markdown("### Team Overview")
team_status = []
for a in ATHLETES.keys():
    plan = generate_daily_plan(a, today)
    team_status.append([a, plan["Running (km)"], plan["Cycling (km)"], plan["Swimming (m)"], plan["Sleep"], plan["Weight"]])
df_team = pd.DataFrame(team_status, columns=["Athlete","Run (km)","Cycle (km)","Swim (m)","Sleep (h)","Weight (kg)"])
st.dataframe(df_team)

# ---------------------------- DAILY TIPS ----------------------------
st.markdown("### Tips & Motivation")
st.markdown("Stay consistent, hydrate well, and follow your nutrition. Remember, every small improvement adds up for Ironman 2028!")

# ---------------------------- END ----------------------------
