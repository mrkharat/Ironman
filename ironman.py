# ironman_app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import random

# ---------------------------- CONFIG ----------------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide", initial_sidebar_state="expanded")

# ---------------------------- CONSTANTS ----------------------------
ATHLETES = {
    "Mayur": {"gender":"M", "weight":62, "dob":"25-12"},
    "Sudeep": {"gender":"M", "weight":73, "dob":"31-10"},
    "Vaishali": {"gender":"F", "weight":64, "dob":"02-04"}
}

PHASES = ["Base", "Build", "Peak", "Taper"]

QUOTE_OF_THE_DAY = [
    "Push yourself because no one else is going to do it for you.",
    "Don’t limit your challenges. Challenge your limits.",
    "Sweat is fat crying."
]

SUNDAY_ACTIVITIES = [
    "Go for a hike", "Plantation drive", "Long drive with friends", "Yoga & meditation", "Community volunteering"
]

# ---------------------------- SIDEBAR ----------------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg?raw=true", use_column_width=True)
athlete_selected = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
today = datetime.now(pytz.timezone("Asia/Kolkata"))
ironman_date = datetime(2028, 7, 14, tzinfo=pytz.timezone("Asia/Kolkata")) # Hamburg example

# Countdown
days_left = (ironman_date - today).days
st.sidebar.markdown(f"**Ironman Hamburg Countdown:** {days_left} days")

# Quote
st.sidebar.markdown("**Quote of the Day:**")
st.sidebar.markdown(f"*{random.choice(QUOTE_OF_THE_DAY)}*")

# Today special
dob = ATHLETES[athlete_selected]["dob"]
today_special = ""
if today.strftime("%d-%m") == dob:
    today_special = "🎉 Happy Birthday!"
else:
    # Example festivals
    if today.strftime("%d-%m") == "12-10":
        today_special = "🎊 Dussehra"
st.sidebar.markdown(f"**Today's Special:** {today_special if today_special else 'None'}")

# ---------------------------- GREETINGS ----------------------------
hour = today.hour
greet = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
st.title(f"{greet}, {athlete_selected}!")
st.subheader(today.strftime("%A, %d %B %Y"))

# ---------------------------- TRAINING PLAN ----------------------------
# Define weekly phases (Base->Build->Peak->Taper) over 3 years
def generate_plan(start_date, end_date):
    df = pd.DataFrame()
    current = start_date
    phase_idx = 0
    while current <= end_date:
        week_start = current - timedelta(days=current.weekday())
        df = pd.concat([df, pd.DataFrame({
            "Week Start": [week_start],
            "Phase": [PHASES[phase_idx % 4]],
            "Activity": [["Run 5km","Strength training","Rest","Run 8km","Cross training","Run 10km","Rest"]],
            "Nutrition": [["Breakfast 7:30","Lunch 1:00","Snack 4:30","Dinner 8:00"]],
            "Sleep": [7]
        })], ignore_index=True)
        current += timedelta(days=7)
        phase_idx += 1
    return df

df_plan = generate_plan(today, datetime(2028, 7, 14))

# ---------------------------- TABS ----------------------------
tab_today, tab_next, tab_week, tab_team, tab_nutrition = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Team Overview","Nutrition & Trackers"])

# ---------------------------- TODAY'S PLAN ----------------------------
with tab_today:
    st.subheader("Today's Activities")
    week_plan = df_plan[df_plan["Week Start"] <= today].iloc[-1]
    day_idx = today.weekday()
    activity_today = week_plan["Activity"][day_idx]
    checkbox = st.checkbox(f"Complete: {activity_today}", key=f"{athlete_selected}_{today}")
    if checkbox:
        st.success("Great! Activity marked complete.")
    st.markdown("**Nutrition**")
    for meal in week_plan["Nutrition"][0]:
        st.markdown(f"- {meal}")
    st.markdown(f"**Planned Sleep:** {week_plan['Sleep']} hours")
    st.markdown("**Tip / Motivation:**")
    st.info("Stay consistent, focus on form, hydrate well!")

# ---------------------------- NEXT DAY PLAN ----------------------------
with tab_next:
    st.subheader("Next Day Plan")
    next_day = today + timedelta(days=1)
    week_plan_next = df_plan[df_plan["Week Start"] <= next_day].iloc[-1]
    day_idx_next = next_day.weekday()
    st.markdown(f"**Activity:** {week_plan_next['Activity'][day_idx_next]}")
    st.markdown("**Nutrition**")
    for meal in week_plan_next["Nutrition"][0]:
        st.markdown(f"- {meal}")
    st.markdown(f"**Planned Sleep:** {week_plan_next['Sleep']} hours")

# ---------------------------- WEEKLY PLAN ----------------------------
with tab_week:
    st.subheader("Weekly Plan Overview")
    week_plan_table = pd.DataFrame({
        "Day": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        "Activity": week_plan["Activity"][0]
    })
    st.table(week_plan_table)

# ---------------------------- TEAM OVERVIEW ----------------------------
with tab_team:
    st.subheader("Team Status Overview")
    status_df = pd.DataFrame({
        "Athlete": list(ATHLETES.keys()),
        "Weight": [ATHLETES[a]["weight"] for a in ATHLETES],
        "Sleep": [7,7,7],
        "Progress (%)": [random.randint(10,50) for _ in ATHLETES]
    })
    st.table(status_df)

# ---------------------------- NUTRITION & TRACKERS ----------------------------
with tab_nutrition:
    st.subheader("Nutrition & Weight Tracker")
    st.markdown("**Target Weight for Ironman 2028**")
    target_weight = {"Mayur":60,"Sudeep":70,"Vaishali":60}
    st.markdown(f"{athlete_selected}: {target_weight[athlete_selected]} kg")
    st.markdown("**Daily Trackers**")
    weight_today = st.number_input("Weight (kg)", value=ATHLETES[athlete_selected]["weight"])
    sleep_today = st.number_input("Sleep (hours)", value=7)
    st.success("Trackers updated!")

