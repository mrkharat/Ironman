import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
from PIL import Image
import requests
from io import BytesIO

# -------------------- Constants --------------------
ATHLETES = ["Mayur", "Sudeep", "Vaishali"]
TODAY = date.today()
IRONMAN_HAMBURG = date(2028, 7, 15)
DATA_DIR = "athlete_data"

# -------------------- Create Data Folder --------------------
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

athlete_files = {athlete: os.path.join(DATA_DIR, f"{athlete}_log.csv") for athlete in ATHLETES}

# -------------------- Initialize Logs --------------------
def init_athlete_log(file_path):
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=[
            "Date", "Run", "Swim", "Bike", "Strength",
            "Breakfast", "Snack1", "Lunch", "Snack2", "Dinner", "Sleep Hours"
        ])
        df.to_csv(file_path, index=False)

for file_path in athlete_files.values():
    init_athlete_log(file_path)

# -------------------- Sidebar --------------------
st.set_page_config(layout="wide")
st.sidebar.title("Ironman Coaching 2025-2028")

# Logo
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
try:
    response = requests.get(LOGO_URL)
    logo = Image.open(BytesIO(response.content))
    st.sidebar.image(logo, use_container_width=True)
except:
    st.sidebar.write("Logo not available")

# Athlete selection dropdown
st.sidebar.markdown("Select Athlete")
selected_athlete = st.sidebar.selectbox("Athlete:", ATHLETES)

# Hamburg countdown
days_hamburg = (IRONMAN_HAMBURG - TODAY).days
st.sidebar.markdown("Ironman Hamburg 2028")
st.sidebar.metric(label="Days Left", value=days_hamburg)
st.sidebar.write(f"Date: {IRONMAN_HAMBURG.strftime('%d %b %Y')}")

# Quick professional tips
st.sidebar.markdown("Quick Tips")
st.sidebar.write("- Follow weekly training plan")
st.sidebar.write("- Track nutrition & sleep")
st.sidebar.write("- Complete all activities daily")

# -------------------- Generate Weekly Calendar --------------------
start_date = date(2025, 10, 1)
end_date = IRONMAN_HAMBURG
weeks = []
current = start_date

while current <= end_date:
    if current < date(2025, 11, 1):
        phase = "Base"
        activities = {"Run": "5 km easy", "Strength": "15 min core & bodyweight"}
    elif current < date(2026, 4, 1):
        phase = "Base + Swim"
        activities = {"Run": "5-10 km easy", "Swim": "500 m drills", "Strength": "20 min core"}
    elif current < date(2028, 1, 1):
        phase = "Build"
        activities = {"Run": "10 km tempo", "Swim": "1 km drills", "Bike": "20-40 km endurance", "Strength":"30 min core & bodyweight"}
    else:
        phase = "Specialty/Peak"
        activities = {"Run": "15 km long run", "Swim": "1.5 km open water", "Bike": "40-80 km endurance", "Strength":"30 min core & bodyweight"}

    weeks.append({
        "Week Start": current,
        "Phase": phase,
        "Run": activities.get("Run", ""),
        "Swim": activities.get("Swim", ""),
        "Bike": activities.get("Bike", ""),
        "Strength": activities.get("Strength", "")
    })
    current += timedelta(days=7)

df_calendar = pd.DataFrame(weeks)

# -------------------- Load Athlete Data --------------------
selected_file = athlete_files[selected_athlete]
df_athlete = pd.read_csv(selected_file)

# -------------------- Tabs --------------------
tab_today, tab_next, tab_week, tab_logs, tab_progress = st.tabs([
    "Today's Plan", "Next Day Plan", "Weekly Summary", "Logs", "Progress Overview"
])

# -------------------- Helper Functions --------------------
def get_current_week(today):
    return df_calendar[df_calendar["Week Start"] <= today].iloc[-1]

def save_entry(date_str, activities, sleep_hours):
    entry = [
        date_str,
        activities.get("Run", False),
        activities.get("Swim", False),
        activities.get("Bike", False),
        activities.get("Strength", False),
        True, True, True, True, True,  # Nutrition assumed followed
        sleep_hours
    ]
    if date_str in df_athlete['Date'].values:
        df_athlete.loc[df_athlete['Date'] == date_str, :] = entry
    else:
        df_athlete.loc[len(df_athlete)] = entry
    df_athlete.to_csv(selected_file, index=False)

def dynamic_suggestions(df_week):
    suggestions = []
    for act in ["Run","Swim","Bike","Strength"]:
        if df_week.empty:
            continue
        completion_rate = df_week[act].sum()/len(df_week)
        if completion_rate < 0.7:
            suggestions.append(f"Increase {act.lower()} frequency next week.")
        elif completion_rate > 0.9:
            suggestions.append(f"Keep current {act.lower()} volume.")
        else:
            suggestions.append(f"Maintain {act.lower()} schedule.")
    return suggestions

# -------------------- Today Plan --------------------
with tab_today:
    st.header(f"Hello {selected_athlete}, Today: {TODAY.strftime('%A, %d %B %Y')}")
    current_week = get_current_week(TODAY)

    st.subheader(f"Week Starting {current_week['Week Start'].strftime('%d %b %Y')} | Phase: {current_week['Phase']}")
    st.markdown("Today's Activities")
    activity_status = {}
    for act_type in ["Run", "Swim", "Bike", "Strength"]:
        if current_week[act_type]:
            key = f"{selected_athlete}_{act_type}_{TODAY}"
            activity_status[key] = st.checkbox(f"{act_type}: {current_week[act_type]}", key=key)

    st.markdown("Nutrition")
    nutrition_plan = pd.DataFrame({
        "Meal": ["Breakfast", "Snack1", "Lunch", "Snack2", "Dinner"],
        "Food": [
            "Oats porridge + banana + herbal tea",
            "Fruits or nuts",
            "Brown rice, dal, vegetables, paneer/chicken/fish",
            "Smoothie or yogurt",
            "Quinoa/roti, vegetables, protein"
        ],
        "Time": ["7:30 AM", "10:30 AM", "1:00 PM", "4:30 PM", "8:00 PM"]
    })
    st.dataframe(nutrition_plan, width=700)

    sleep_hours = st.number_input("Sleep hours", min_value=0.0, max_value=12.0, step=0.5, key=f"{selected_athlete}_sleep_{TODAY}")
    st.write("Target: 7-8 hours sleep")

    save_entry(TODAY.isoformat(), {k:v for k,v in activity_status.items()}, sleep_hours)

    st.markdown("Suggestions")
    week_start = current_week['Week Start']
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    df_week = df_athlete[df_athlete['Date'].isin([d.isoformat() for d in week_dates])]
    suggestions = dynamic_suggestions(df_week)
    for s in suggestions:
        st.info(s)

# -------------------- Next Day Plan --------------------
with tab_next:
    next_day = TODAY + timedelta(days=1)
    st.header(f"Next Day Plan: {next_day.strftime('%A, %d %B %Y')}")
    next_week = get_current_week(next_day)
    st.subheader(f"Week Starting {next_week['Week Start'].strftime('%d %b %Y')} | Phase: {next_week['Phase']}")
    st.markdown("Activities")
    for act_type in ["Run", "Swim", "Bike", "Strength"]:
        if next_week[act_type]:
            st.write(f"{act_type}: {next_week[act_type]}")
    st.markdown("Nutrition")
    st.dataframe(nutrition_plan, width=700)
    st.write("Sleep Target: 7-8 hours")

# -------------------- Weekly Summary --------------------
with tab_week:
    st.header("Weekly Completion Summary")
    summary = {}
    for act in ["Run","Swim","Bike","Strength"]:
        if not df_week.empty:
            summary[act] = int(df_week[act].sum()/len(df_week)*100)
        else:
            summary[act] = 0
    st.dataframe(pd.DataFrame([summary]), width=700)

# -------------------- Logs --------------------
with tab_logs:
    st.header("Logs")
    logs_tab1, logs_tab2, logs_tab3 = st.tabs(["Activity","Nutrition","Sleep"])
    with logs_tab1:
        st.dataframe(df_athlete[['Date','Run','Swim','Bike','Strength']], width=700)
    with logs_tab2:
        st.dataframe(df_athlete[['Date','Breakfast','Snack1','Lunch','Snack2','Dinner']], width=700)
    with logs_tab3:
        st.dataframe(df_athlete[['Date','Sleep Hours']], width=700)

# -------------------- Progress Overview --------------------
with tab_progress:
    st.header("Progress Overview")
    weekly_summary = df_athlete.copy()
    weekly_summary['Week'] = pd.to_datetime(weekly_summary['Date']).dt.isocalendar().week
    chart_data = weekly_summary.groupby('Week')[["Run","Swim","Bike","Strength"]].mean()
    st.bar_chart(chart_data)
