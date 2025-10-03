# -------------------- Ironman 3-Year Coaching App --------------------
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
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
st.set_page_config(layout="wide")  # Sidebar always expanded
st.sidebar.title("🏊 Ironman Coaching")

# Logo
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
try:
    response = requests.get(LOGO_URL)
    logo = Image.open(BytesIO(response.content))
    st.sidebar.image(logo, use_container_width=True)
except:
    st.sidebar.write("Logo not available")

# Athlete selection dropdown
st.sidebar.markdown("### 👤 Select Athlete")
selected_athlete = st.sidebar.selectbox("Choose Athlete:", ATHLETES)

# Hamburg countdown
days_hamburg = (IRONMAN_HAMBURG - TODAY).days
st.sidebar.markdown("### 🏁 Ironman Hamburg 2028")
st.sidebar.metric(label="Days Left", value=days_hamburg)
st.sidebar.write(f"Date: {IRONMAN_HAMBURG.strftime('%d %b %Y')}")

# Quick Tips
st.sidebar.markdown("### 💡 Quick Tips")
st.sidebar.write("- Follow weekly training plan")
st.sidebar.write("- Track nutrition & sleep")
st.sidebar.write("- Complete all activities daily")

# -------------------- Main Page --------------------
st.title(f"Hello {selected_athlete}! Today is {TODAY.strftime('%A, %d %B %Y')}")
st.subheader("Your weekly guidance:")

# -------------------- Training Plan --------------------
def generate_weekly_plan(today):
    """Generate simple weekly guidance based on progressive training"""
    week_plan = {
        "Run": "5 km easy / interval / long run",
        "Swim": "30 min drills",
        "Bike": "20 km endurance",
        "Strength": "Core + bodyweight exercises"
    }

    # Example: gradually increase distances over months
    month = today.month
    if month in [10,11,12]:  # Base phase
        week_plan.update({"Run": "5 km easy", "Swim": "500 m drills", "Bike": "20 km", "Strength":"15 min core"})
    elif month in [1,2,3,4,5,6,7,8,9]:  # Build phase
        week_plan.update({"Run": "10 km tempo", "Swim": "1 km", "Bike": "40 km", "Strength":"30 min core & bodyweight"})
    return week_plan

weekly_plan = generate_weekly_plan(TODAY)

st.markdown("### ✅ Activities")
activity_status = {}
for act_type, desc in weekly_plan.items():
    key = f"{selected_athlete}_{act_type}"
    activity_status[key] = st.checkbox(f"{act_type}: {desc}", key=key)

# -------------------- Nutrition --------------------
st.markdown("### 🥗 Daily Nutrition Guide")
nutrition_plan = pd.DataFrame({
    "Meal": ["Breakfast", "Snack1", "Lunch", "Snack2", "Dinner"],
    "Food Suggestion": [
        "Oats porridge with banana + herbal tea",
        "Fruits or nuts",
        "Brown rice, dal, vegetables, paneer/chicken/fish",
        "Smoothie or yogurt",
        "Quinoa/roti, vegetables, protein"
    ],
    "Time": ["7:30 AM", "10:30 AM", "1:00 PM", "4:30 PM", "8:00 PM"]
})
st.dataframe(nutrition_plan, width=700)

# -------------------- Sleep & Recovery --------------------
st.markdown("### 💤 Sleep & Recovery")
sleep_hours = st.number_input("Sleep hours", min_value=0.0, max_value=12.0, step=0.5, key=f"{selected_athlete}_sleep")
st.write("Aim for 7-8 hours for optimal recovery.")

# -------------------- Load Athlete Data --------------------
selected_file = athlete_files[selected_athlete]
df_athlete = pd.read_csv(selected_file)

# -------------------- Save Today's Entry --------------------
today_str = TODAY.isoformat()
if today_str in df_athlete['Date'].values:
    df_athlete.loc[df_athlete['Date'] == today_str, :] = [
        today_str,
        activity_status[f"{selected_athlete}_Run"],
        activity_status[f"{selected_athlete}_Swim"],
        activity_status[f"{selected_athlete}_Bike"],
        activity_status[f"{selected_athlete}_Strength"],
        True, True, True, True, True,  # assume following nutrition
        sleep_hours
    ]
else:
    df_athlete.loc[len(df_athlete)] = [
        today_str,
        activity_status[f"{selected_athlete}_Run"],
        activity_status[f"{selected_athlete}_Swim"],
        activity_status[f"{selected_athlete}_Bike"],
        activity_status[f"{selected_athlete}_Strength"],
        True, True, True, True, True,
        sleep_hours
    ]

df_athlete.to_csv(selected_file, index=False)

# -------------------- Weekly Progress --------------------
st.markdown("### 📊 Weekly Progress Summary")
run_done = 1 if activity_status[f"{selected_athlete}_Run"] else 0
swim_done = 1 if activity_status[f"{selected_athlete}_Swim"] else 0
bike_done = 1 if activity_status[f"{selected_athlete}_Bike"] else 0
strength_done = 1 if activity_status[f"{selected_athlete}_Strength"] else 0

df_progress = pd.DataFrame([{
    "Athlete": selected_athlete,
    "Run (%)": f"{run_done*100}%",
    "Swim (%)": f"{swim_done*100}%",
    "Bike (%)": f"{bike_done*100}%",
    "Strength (%)": f"{strength_done*100}%"
}])
st.dataframe(df_progress, width=700)

# -------------------- Suggestions --------------------
st.markdown("### 💡 Suggestions / Alerts")
if run_done != 1:
    st.warning(f"{selected_athlete}: Complete your running today to stay on track.")
if swim_done != 1:
    st.warning(f"{selected_athlete}: Focus on swimming sessions.")
if bike_done != 1:
    st.warning(f"{selected_athlete}: Don’t skip cycling workouts.")
if strength_done != 1:
    st.warning(f"{selected_athlete}: Strength & core training is important.")

# -------------------- Logs Tabs --------------------
st.markdown("### 📚 Logs")
tab1, tab2, tab3 = st.tabs(["Activity Log", "Nutrition Log", "Sleep Log"])

with tab1:
    st.dataframe(df_athlete[['Date', 'Run', 'Swim', 'Bike', 'Strength']], width=700)

with tab2:
    st.dataframe(df_athlete[['Date', 'Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner']], width=700)

with tab3:
    st.dataframe(df_athlete[['Date', 'Sleep Hours']], width=700)
