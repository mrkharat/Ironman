# ironman_full_app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import plotly.express as px

# ------------------ CONSTANTS ------------------
DATA_DIR = "ironman_logs"
ATHLETES = {
    "Mayur": {"weight": 62, "gender": "M"},
    "Sudeep": {"weight": 73, "gender": "M"},
    "Vaishali": {"weight": 64, "gender": "F"},
}

IRONMAN_HAMBURG_DATE = datetime(2028, 7, 15)
IRONMAN_GOA_DATE = datetime(2026, 5, 10)

# ------------------ CREATE DATA DIR ------------------
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ------------------ HELPER FUNCTIONS ------------------
def get_greeting():
    now = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    hour = now.hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"

def load_logs(athlete):
    path = os.path.join(DATA_DIR, f"{athlete}.csv")
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","Activity","Duration(min)","Nutrition","Sleep(hr)","Weight(kg)"])
        df.to_csv(path, index=False)
        return df

def save_logs(athlete, df):
    path = os.path.join(DATA_DIR, f"{athlete}.csv")
    df.to_csv(path, index=False)

def generate_daily_plan(athlete, date):
    start_swim = datetime(2025, 11, 1)
    start_bike = datetime(2026, 2, 1)
    plan = []
    
    # Running progression
    days_since_start = (date - datetime(2025,5,1)).days
    run_km = min(5 + (days_since_start//7)*0.5, 25)  # progress gradually to 25km
    plan.append({"Activity":"Run","Duration(min)":run_km*6})  # assume 6min/km
    
    # Swim
    if date >= start_swim:
        plan.append({"Activity":"Swim","Duration(min)":30})
    
    # Bike
    if date >= start_bike:
        plan.append({"Activity":"Bike","Duration(min)":60})
    
    # Nutrition
    meals = [
        "Breakfast: Oats/Poha/Daliya",
        "Snack: Nuts/Fruit",
        "Lunch: Roti/Rice+Veg+Dal/Chicken",
        "Snack: Fruit/Yogurt",
        "Dinner: Roti/Rice+Veg+Protein"
    ]
    
    sleep_hr = 7.5
    
    return plan, meals, sleep_hr

def generate_weekly_plan(athlete, start_date):
    week_plan = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        plan, meals, sleep_hr = generate_daily_plan(athlete, date)
        week_plan.append({
            "Date": date,
            "Activities": ", ".join([p["Activity"] for p in plan]),
            "Nutrition": ", ".join(meals),
            "Sleep(hr)": sleep_hr
        })
    return pd.DataFrame(week_plan)

def calculate_progress(df):
    if df.empty:
        return 0
    return min(100, len(df)/365*100)  # rough yearly adherence

# ------------------ STREAMLIT UI ------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide")

# ---- Sidebar ----
st.sidebar.title("Ironman Coach")
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
today = datetime.utcnow() + timedelta(hours=5, minutes=30)
st.sidebar.write(f"{get_greeting()}, {athlete}!")
st.sidebar.write(f"Today: {today.strftime('%A, %d %B %Y')}")
week_start = today - timedelta(days=today.weekday())
st.sidebar.write(f"Week Start: {week_start.strftime('%d %b %Y')}")
days_left = (IRONMAN_HAMBURG_DATE - today).days
st.sidebar.write(f"Ironman Hamburg 2028 in **{days_left} days**")
st.sidebar.write(f"Target Weight for Ironman: **{ATHLETES[athlete]['weight']} kg**")

# ---- Load logs ----
df_log = load_logs(athlete)

# ---- Tabs ----
tabs = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Progress Log","Team Overview","Weight & Nutrition Tracker"])

# ---- Today's Plan ----
with tabs[0]:
    st.subheader("Today's Plan")
    plan, meals, sleep_hr = generate_daily_plan(athlete, today)
    df_today = pd.DataFrame(plan)
    df_today["Intensity"] = ["Medium" for _ in range(len(df_today))]
    st.dataframe(df_today.style.applymap(lambda x: "background-color: lightgreen" if x=="Run" else "background-color: lightblue", subset=["Activity"]))
    
    st.write("**Nutrition:**")
    for m in meals:
        st.write(f"- {m}")
    
    st.write(f"**Sleep Target:** {sleep_hr} hrs")

# ---- Next Day Plan ----
with tabs[1]:
    st.subheader("Next Day Plan")
    next_day = today + timedelta(days=1)
    plan, meals, sleep_hr = generate_daily_plan(athlete, next_day)
    df_next = pd.DataFrame(plan)
    df_next["Intensity"] = ["Medium" for _ in range(len(df_next))]
    st.dataframe(df_next.style.applymap(lambda x: "background-color: lightgreen" if x=="Run" else "background-color: lightblue", subset=["Activity"]))
    
    st.write("**Nutrition:**")
    for m in meals:
        st.write(f"- {m}")
    
    st.write(f"**Sleep Target:** {sleep_hr} hrs")

# ---- Weekly Plan ----
with tabs[2]:
    st.subheader("Weekly Plan")
    df_week = generate_weekly_plan(athlete, week_start)
    st.dataframe(df_week)

# ---- Progress Log ----
with tabs[3]:
    st.subheader("Progress Log")
    st.dataframe(df_log)

# ---- Team Overview ----
with tabs[4]:
    st.subheader("Team Overview")
    team_progress = {ath: calculate_progress(load_logs(ath)) for ath in ATHLETES.keys()}
    df_team = pd.DataFrame(list(team_progress.items()), columns=["Athlete","Progress (%)"])
    fig = px.bar(df_team, x="Athlete", y="Progress (%)", text="Progress (%)", range_y=[0,100], color="Progress (%)", color_continuous_scale="Blues")
    st.plotly_chart(fig)

# ---- Weight & Nutrition Tracker ----
with tabs[5]:
    st.subheader("Weight & Nutrition Tracker")
    if not df_log.empty:
        st.line_chart(df_log.set_index("Date")["Weight(kg)"])
    else:
        st.write("No weight data yet.")
