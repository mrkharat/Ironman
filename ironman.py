# ironman_training_app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import random
import os

# ---------------------- App Settings ----------------------
st.set_page_config(page_title="Ironman Coach App", layout="wide", initial_sidebar_state="expanded", page_icon=None)

# ---------------------- Dark Theme Styling ----------------------
st.markdown("""
    <style>
        .reportview-container {
            background-color: #0E1117;
            color: #FFFFFF;
        }
        .sidebar .sidebar-content {
            background-color: #111520;
        }
        .stButton>button {
            color: #FFFFFF;
            background-color: #1E2230;
        }
        .stDataFrame div.row_heading, .stDataFrame th {
            color: #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------- Athletes Info ----------------------
ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "target_weight": 60},
    "Sudeep": {"gender": "M", "weight": 73, "target_weight": 70},
    "Vaishali": {"gender": "F", "weight": 64, "target_weight": 60}
}

BIRTHDAYS = {"Vaishali": "02-04", "Sudeep": "31-10", "Mayur": "25-12"}

# ---------------------- Sidebar ----------------------
st.sidebar.image("https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg", use_column_width=True)
athlete_selected = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))

# Countdown to Ironman Hamburg 2028
hamburg_date = datetime(2028, 7, 16)
today_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
days_left = (hamburg_date - today_ist).days
st.sidebar.markdown(f"### Ironman Hamburg Countdown")
st.sidebar.markdown(f"**{days_left} days left**")

# Quote of the Day
quotes = [
    "Your only limit is you.",
    "Sweat is your fat crying.",
    "Stronger every day.",
    "Train insane or remain the same."
]
st.sidebar.markdown(f"**Quote of the Day:** {random.choice(quotes)}")

# Birthday / Festival info
today_md = today_ist.strftime("%d-%m")
birthday_today = [name for name, date in BIRTHDAYS.items() if date == today_md]
if birthday_today:
    st.sidebar.markdown(f"🎉 Happy Birthday {', '.join(birthday_today)}!")

# ---------------------- Greetings ----------------------
hour = today_ist.hour
if hour < 12:
    greeting = "Good Morning"
elif hour < 17:
    greeting = "Good Afternoon"
else:
    greeting = "Good Evening"

st.markdown(f"# {greeting}, {athlete_selected}!")
st.markdown(f"**Today:** {today_ist.strftime('%A, %d %B %Y')}")

# ---------------------- Weekly Plan ----------------------
# Example Phases
PHASES = [
    ("Base", 12),
    ("Build", 12),
    ("Peak", 12),
    ("Taper", 4)
]

# Create plan for each athlete
def generate_weekly_plan(start_date, athlete):
    plan = []
    current_date = start_date
    phase_index = 0
    phase_weeks = PHASES[phase_index][1]
    for week in range(1, 157):  # ~3 years
        if week > sum([p[1] for p in PHASES[:phase_index+1]]):
            phase_index += 1
        phase = PHASES[phase_index][0]
        plan.append({
            "Week": week,
            "Phase": phase,
            "Run_km": min(30 + week, 70),
            "Bike_km": 0 if week < 16 else min(50 + week*2, 180),
            "Swim_m": 0 if week < 14 else min(500 + week*50, 3800),
            "Athlete": athlete
        })
    return pd.DataFrame(plan)

# ---------------------- Log / Tracker ----------------------
DATA_DIR = "athlete_logs"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

log_file = os.path.join(DATA_DIR, f"{athlete_selected}_log.csv")
if os.path.exists(log_file):
    df_log = pd.read_csv(log_file, parse_dates=["Date"])
else:
    df_log = pd.DataFrame(columns=["Date","Activity","Completed","Nutrition","Weight","Sleep","Tips"])

# ---------------------- Main Tabs ----------------------
tabs = st.tabs(["Today's Plan", "Next Day Plan", "Weekly Plan", "Nutrition & Sleep", "Weight Tracker", "Team Overview"])

# ---------------------- Tab 1: Today's Plan ----------------------
with tabs[0]:
    st.subheader("Today's Plan")
    # Determine current week
    start_date = datetime(2025, 10, 1)
    weeks_passed = (today_ist - start_date).days // 7
    df_week_plan = generate_weekly_plan(start_date, athlete_selected)
    today_plan = df_week_plan.iloc[weeks_passed]
    
    # Sunday activity suggestion
    sunday_activities = ["Go for hike", "Long drive", "Plantation drive", "Family outing"]
    if today_ist.weekday() == 6:
        sunday_tip = random.choice(sunday_activities)
        st.info(f"Sunday Activity Suggestion: {sunday_tip}")
    
    # Display plan as checkboxes
    run_cb = st.checkbox(f"Run {today_plan['Run_km']} km", key="run")
    bike_cb = st.checkbox(f"Bike {today_plan['Bike_km']} km", key="bike")
    swim_cb = st.checkbox(f"Swim {today_plan['Swim_m']} m", key="swim")
    
    # Nutrition
    st.markdown("**Nutrition (Indian Meals):**")
    nutrition_times = [("Breakfast", "07:30"), ("Mid Meal", "10:30"), ("Lunch", "13:00"), ("Evening Snack", "16:30"), ("Dinner", "20:00")]
    for meal, time in nutrition_times:
        st.checkbox(f"{meal} at {time}", key=meal)
    
    # Sleep
    sleep_hours = st.slider("Sleep hours", 0, 12, 8)
    
    # Tips
    tips_list = [
        "Stay hydrated.",
        "Focus on technique over speed.",
        "Consistency beats intensity.",
        "Recover well and stretch."
    ]
    tip_today = random.choice(tips_list)
    st.markdown(f"**Tip:** {tip_today}")
    
    # Save today's log
    new_log = {
        "Date": today_ist.strftime("%Y-%m-%d"),
        "Activity": f"Run:{run_cb},Bike:{bike_cb},Swim:{swim_cb}",
        "Completed": run_cb and bike_cb and swim_cb,
        "Nutrition": "Completed" if all([st.session_state.get(meal) for meal,_ in nutrition_times]) else "Pending",
        "Weight": ATHLETES[athlete_selected]["weight"],
        "Sleep": sleep_hours,
        "Tips": tip_today
    }
    df_log = pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True)
    df_log.to_csv(log_file, index=False)

# ---------------------- Tab 2: Next Day Plan ----------------------
with tabs[1]:
    st.subheader("Next Day Plan")
    next_day = today_ist + timedelta(days=1)
    next_week_index = (next_day - start_date).days // 7
    next_plan = df_week_plan.iloc[next_week_index]
    st.write(next_plan[["Phase","Run_km","Bike_km","Swim_m"]])

# ---------------------- Tab 3: Weekly Plan ----------------------
with tabs[2]:
    st.subheader("Weekly Plan Overview")
    st.dataframe(df_week_plan.head(20))  # Show first 20 weeks for brevity

# ---------------------- Tab 4: Nutrition & Sleep ----------------------
with tabs[3]:
    st.subheader("Nutrition & Sleep Logs")
    st.dataframe(df_log[["Date","Nutrition","Sleep"]].tail(30))

# ---------------------- Tab 5: Weight Tracker ----------------------
with tabs[4]:
    st.subheader("Weight Tracker")
    st.line_chart(df_log.set_index("Date")["Weight"])

# ---------------------- Tab 6: Team Overview ----------------------
with tabs[5]:
    st.subheader("Team Overview")
    # Load all athlete logs
    df_team = pd.DataFrame()
    for athlete in ATHLETES.keys():
        f = os.path.join(DATA_DIR, f"{athlete}_log.csv")
        if os.path.exists(f):
            df_a = pd.read_csv(f, parse_dates=["Date"])
            df_a["Athlete"] = athlete
            df_team = pd.concat([df_team, df_a])
    if not df_team.empty:
        pivot_team = df_team.pivot(index="Date", columns="Athlete", values="Weight")
        st.line_chart(pivot_team)
