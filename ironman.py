# ironman_app_full.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pytz
from pathlib import Path

# ---------------------- Config ----------------------
DATA_DIR = Path("ironman_data")
DATA_DIR.mkdir(exist_ok=True)
ATHLETES = {
    "Mayur": {"gender":"male", "weight":62, "dob":"25-12"},
    "Sudeep": {"gender":"male", "weight":73, "dob":"31-10"},
    "Vaishali": {"gender":"female", "weight":64, "dob":"02-04"}
}

IRONMAN_DATE = datetime(2028, 7, 1, 6, 0)
INDIA_TZ = pytz.timezone("Asia/Kolkata")
PHASES = ["Base", "Build", "Peak", "Taper"]

START_DATE = datetime(2025,10,1)

# ---------------------- Utilities ----------------------
def load_log(athlete):
    file_path = DATA_DIR / f"{athlete}_log.csv"
    if file_path.exists():
        df = pd.read_csv(file_path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","Phase","Activity","Completed","Nutrition","Weight","Sleep","Tip"])
    return df

def save_log(athlete, df):
    df.to_csv(DATA_DIR / f"{athlete}_log.csv", index=False)

def current_phase(date):
    weeks = ((date - START_DATE).days)//7
    phase_idx = (weeks//12)%4
    return PHASES[phase_idx]

def greeting(now):
    if now.hour<12:
        return "Good Morning"
    elif now.hour<16:
        return "Good Afternoon"
    else:
        return "Good Evening"

def countdown(ironman_date):
    now = datetime.now(INDIA_TZ)
    delta = ironman_date - now
    return f"{delta.days} days, {delta.seconds//3600}h remaining"

def birthday_message(athlete, today):
    dob = ATHLETES[athlete]["dob"]
    if today.strftime("%d-%m")==dob:
        return f"Happy Birthday {athlete}!"
    return ""

def festival_message(today):
    festivals = {"15-08":"Independence Day","26-01":"Republic Day","25-12":"Christmas"}
    return festivals.get(today.strftime("%d-%m"), "")

def sunday_activity_suggestion(date):
    if date.weekday()==6:
        if date.day<=7:
            return "Team Activity: Plantation drive / Hiking / Long drive"
        return "Relaxing Sunday: Optional light activity"
    return ""

def suggest_activity_tip(activity_done):
    tips = {
        "Run":"Maintain steady pace, focus on breathing.",
        "Cycle":"Keep cadence consistent; hydrate well.",
        "Swim":"Focus on technique and efficiency.",
        "Strength":"Use correct form, avoid injury.",
        "Recovery":"Stretch properly and rest well."
    }
    for act in activity_done:
        if activity_done[act]==False:
            return tips.get(act,"Keep consistent.")
    return "Great job! Keep up the momentum."

# ---------------------- Generate 3-Year Training Plan ----------------------
def generate_plan_for_athlete(athlete):
    df = pd.DataFrame()
    current_date = START_DATE
    while current_date <= IRONMAN_DATE:
        phase = current_phase(current_date)
        activities = []
        if current_date.weekday()==6:  # Sunday rest or activity
            activities.append(sunday_activity_suggestion(current_date))
        else:
            # Base phase: run + strength; Build: add bike/swim; Peak: all; Taper: reduce volume
            if phase=="Base":
                activities.append("Run")
                activities.append("Strength")
            elif phase=="Build":
                activities.append("Run")
                if current_date >= datetime(2026,2,1):
                    activities.append("Cycle")
                if current_date >= datetime(2025,11,1):
                    activities.append("Swim")
                activities.append("Strength")
            elif phase=="Peak":
                activities.extend(["Run","Cycle","Swim","Strength"])
            elif phase=="Taper":
                activities.append("Run")
                if current_date >= datetime(2026,2,1):
                    activities.append("Cycle")
                if current_date >= datetime(2025,11,1):
                    activities.append("Swim")
                activities.append("Recovery")
        # Nutrition & Sleep
        nutrition = ["Breakfast","Mid-Morning","Lunch","Evening Snack","Dinner"]
        sleep = 7 if ATHLETES[athlete]["gender"]=="female" else 6
        # Tip
        tip = suggest_activity_tip({a:False for a in ["Run","Cycle","Swim","Strength","Recovery"]})
        # Weight tracker (example: goal 60kg male, 58kg female)
        goal_weight = 60 if ATHLETES[athlete]["gender"]=="male" else 58
        df = pd.concat([df,pd.DataFrame({
            "Date":[current_date],
            "Phase":[phase],
            "Activity":[",".join(activities)],
            "Completed":[""],
            "Nutrition":[",".join(nutrition)],
            "Weight":[ATHLETES[athlete]["weight"]],
            "Goal Weight":[goal_weight],
            "Sleep":[sleep],
            "Tip":[tip]
        })])
        current_date += timedelta(days=1)
    return df

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide")
st.markdown("""
    <style>
        .sidebar .sidebar-content {width: 300px;}
        .stApp {background-color:#0e1117; color:white;}
        .stDataFrame table {background-color:#1e1e1e; color:white;}
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg", use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown(f"**Countdown to Ironman Hamburg 2028:** {countdown(IRONMAN_DATE)}")
st.sidebar.markdown("**Quote of the Day:** Stay consistent and trust the process.")

today = datetime.now(INDIA_TZ)
bday_msg = birthday_message(athlete, today)
festival_msg = festival_message(today)
sunday_msg = sunday_activity_suggestion(today)
special_msg = bday_msg or (f"🎉 Today: {festival_msg} 🎉" if festival_msg else sunday_msg)
if special_msg:
    st.sidebar.markdown(f"**Today's Special:** {special_msg}")

tabs = st.tabs(["Today's Plan","Next Day Plan","Team Overview","Logs"])

# Load or generate plan
log_file = DATA_DIR / f"{athlete}_plan.csv"
if log_file.exists():
    df_plan = pd.read_csv(log_file, parse_dates=["Date"])
else:
    df_plan = generate_plan_for_athlete(athlete)
    df_plan.to_csv(log_file, index=False)

# ---------- Today's Plan ----------
with tabs[0]:
    today_plan = df_plan[df_plan["Date"]==today]
    if not today_plan.empty:
        st.subheader(f"{greeting(today)}, {athlete}!")
        st.write(f"Date: {today.strftime('%A, %d %B %Y')}")
        st.write(f"Week: {((today-START_DATE).days)//7 + 1}")
        st.write(f"Phase: {today_plan['Phase'].values[0]}")
        # Activities
        st.markdown("### Activities")
        activities = today_plan["Activity"].values[0].split(",")
        activity_done = {}
        for act in activities:
            activity_done[act] = st.checkbox(act, value=False, key=f"{athlete}_{act}_{today}")
        # Nutrition
        st.markdown("### Nutrition")
        for meal in today_plan["Nutrition"].values[0].split(","):
            st.write(meal)
        # Weight & Sleep
        weight = st.number_input("Weight (kg)", value=int(today_plan["Weight"].values[0]))
        sleep_hours = st.number_input("Sleep Hours", min_value=0, max_value=12, value=int(today_plan["Sleep"].values[0]))
        # Tip
        st.markdown(f"**Tip for today:** {today_plan['Tip'].values[0]}")

        # Save today's completion
        if st.button("Save Today's Log"):
            df_plan.loc[df_plan["Date"]==today, "Completed"] = ",".join([k for k,v in activity_done.items() if v])
            df_plan.loc[df_plan["Date"]==today, "Weight"] = weight
            df_plan.loc[df_plan["Date"]==today, "Sleep"] = sleep_hours
            df_plan.to_csv(log_file, index=False)
            st.success("Today's log saved!")

# ---------- Next Day Plan ----------
with tabs[1]:
    next_day = today + timedelta(days=1)
    next_plan = df_plan[df_plan["Date"]==next_day]
    if not next_plan.empty:
        st.subheader(f"Next Day Plan ({next_day.strftime('%A, %d %B %Y')})")
        st.write(f"Phase: {next_plan['Phase'].values[0]}")
        st.markdown("### Activities")
        for act in next_plan["Activity"].values[0].split(","):
            st.write(act)
        st.markdown("### Nutrition")
        for meal in next_plan["Nutrition"].values[0].split(","):
            st.write(meal)
        st.write(f"Goal Weight: {next_plan['Goal Weight'].values[0]} kg")
        st.write(f"Sleep Hours: {next_plan['Sleep'].values[0]}")
        st.markdown(f"**Tip:** {next_plan['Tip'].values[0]}")

# ---------- Team Overview ----------
with tabs[2]:
    all_logs = []
    for ath in ATHLETES:
        df = load_log(ath)
        if not df.empty:
            df["Athlete"] = ath
            all_logs.append(df)
    if all_logs:
        df_team = pd.concat(all_logs)
        st.dataframe(df_team[["Date","Athlete","Activity","Completed","Weight","Sleep"]])

# ---------- Logs ----------
with tabs[3]:
    st.subheader("Saved Logs")
    st.dataframe(df_plan[["Date","Phase","Activity","Completed","Weight","Sleep"]])

