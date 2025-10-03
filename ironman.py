# ironman_3year_app.py
import streamlit as st
import pandas as pd
import datetime
from PIL import Image

# ----------------- Config -----------------
TODAY = datetime.date.today()
ATHLETES = ["Mayur", "Sudeep", "Vaishali"]

# Ironman Dates
IRONMAN_GOA = datetime.date(2026, 6, 1)
IRONMAN_EUROPE = datetime.date(2028, 7, 15)

# Sidebar logo
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
try:
    logo = Image.open(st.experimental_get_url(LOGO_URL))
except:
    logo = None
if logo:
    st.sidebar.image(logo, use_column_width=True)

st.sidebar.title("🏊 Ironman Tracker")
st.sidebar.write(f"Days until Ironman 70.3 Goa 2026: {(IRONMAN_GOA - TODAY).days}")
st.sidebar.write(f"Days until Full Ironman Europe 2028: {(IRONMAN_EUROPE - TODAY).days}")

# ----------------- Greeting -----------------
st.title(f"Hello! Today is {TODAY.strftime('%A, %d %B %Y')}")
st.subheader("Your weekly guidance:")

# ----------------- Generate 3-year weekly plan -----------------
# For simplicity, define 3 phases: Beginner (Oct-Dec 2025), Intermediate (2026-2027), Advanced (2028)
# Weekly plan template
def generate_weekly_plan():
    start_date = datetime.date(2025, 10, 1)
    end_date = datetime.date(2028, 7, 15)
    delta = datetime.timedelta(days=7)

    weeks = []
    current = start_date
    week_num = 1

    while current <= end_date:
        # Phase logic
        if current <= datetime.date(2025, 12, 31):
            phase = "Beginner"
            run = "Run 5-10 km"
            swim = "Learn swimming 20-30 min"
            bike = "Bike 20-30 km (if bike available)"
            strength = "Strength 30 min"
        elif current <= datetime.date(2027, 12, 31):
            phase = "Intermediate"
            run = "Run 10-20 km / brick sessions"
            swim = "Swimming 30-60 min"
            bike = "Bike 40-80 km"
            strength = "Strength 40 min / core"
        else:
            phase = "Advanced"
            run = "Run 15-25 km / brick sessions"
            swim = "Swimming 60-90 min"
            bike = "Bike 80-120 km"
            strength = "Strength 40-50 min / core + mobility"

        # Nutrition & sleep guidance
        nutrition = "Follow weekly diet plan (India-friendly)"
        sleep = "Sleep 7-8 hrs / optional nap 20-30 min"

        weeks.append({
            "Week Number": week_num,
            "Week Start": current,
            "Week End": current + delta - datetime.timedelta(days=1),
            "Phase": phase,
            "Run": run,
            "Swim": swim,
            "Bike": bike,
            "Strength": strength,
            "Nutrition": nutrition,
            "Sleep": sleep
        })
        current += delta
        week_num += 1

    return pd.DataFrame(weeks)

df_weeks = generate_weekly_plan()

# ----------------- Determine current week -----------------
current_week_row = df_weeks[(df_weeks["Week Start"] <= TODAY) & (df_weeks["Week End"] >= TODAY)]
if current_week_row.empty:
    current_week_row = df_weeks.iloc[[0]]
current_week = current_week_row.iloc[0]
st.markdown(f"**Current Week ({current_week['Week Number']}) - Phase: {current_week['Phase']}**")

# ----------------- Activities -----------------
st.markdown("### ✅ Activities (Check what you complete)")
activity_status = {}
for act_type in ["Run", "Swim", "Bike", "Strength"]:
    for athlete in ATHLETES:
        key = f"{athlete}_{act_type}"
        label = f"{athlete}: {current_week[act_type]}"
        activity_status[key] = st.checkbox(label, key=key)

# ----------------- Nutrition -----------------
st.markdown("### 🥗 Daily Nutrition Guide")
nutrition_plan = pd.DataFrame({
    "Meal": ["Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack", "Dinner"],
    "Food Suggestion": [
        "Oats porridge with banana + herbal tea",
        "Fruit (apple/orange) or nuts",
        "Brown rice, dal, vegetables, grilled chicken/fish",
        "Greek yogurt or smoothie",
        "Quinoa, vegetables, paneer or fish"
    ],
    "Time": ["7:30 AM", "10:30 AM", "1:00 PM", "4:30 PM", "8:00 PM"]
})
st.dataframe(nutrition_plan, width=700)

# ----------------- Sleep -----------------
st.markdown("### 💤 Sleep & Recovery")
sleep_plan = pd.DataFrame({
    "Parameter": ["Sleep Duration", "Bedtime", "Wake-up Time", "Nap"],
    "Recommendation": ["7-8 hours", "10:30 PM", "6:30 AM", "20-30 min if needed"]
})
st.dataframe(sleep_plan, width=700)

# ----------------- Progress Summary -----------------
st.markdown("### 📊 Weekly Progress Summary")
progress_data = []
for athlete in ATHLETES:
    run_done = 1 if activity_status[f"{athlete}_Run"] else 0
    swim_done = 1 if activity_status[f"{athlete}_Swim"] else 0
    bike_done = 1 if activity_status[f"{athlete}_Bike"] else 0
    strength_done = 1 if activity_status[f"{athlete}_Strength"] else 0
    progress_data.append({
        "Athlete": athlete,
        "Run (%)": run_done*100,
        "Swim (%)": swim_done*100,
        "Bike (%)": bike_done*100,
        "Strength (%)": strength_done*100
    })

df_progress = pd.DataFrame(progress_data)
st.dataframe(df_progress.style.format("{:.0f}%").highlight_max(axis=0, color='lightgreen'))

# ----------------- Suggestions -----------------
st.markdown("### 💡 Suggestions / Alerts")
for athlete in ATHLETES:
    row = df_progress[df_progress["Athlete"]==athlete].iloc[0]
    if row["Run (%)"] < 100:
        st.warning(f"{athlete}: Complete your running this week to stay on track.")
    if row["Swim (%)"] < 100:
        st.warning(f"{athlete}: Focus on swimming sessions.")
    if row["Bike (%)"] < 100:
        st.warning(f"{athlete}: Don’t skip cycling workouts.")
    if row["Strength (%)"] < 100:
        st.warning(f"{athlete}: Strength & core training is important.")

# ----------------- Logs Tabs -----------------
st.markdown("### 📚 Logs")
tab1, tab2, tab3 = st.tabs(["Activity Log", "Nutrition Log", "Sleep Log"])
with tab1:
    st.write("✅ Weekly activities checkbox above act as activity log.")
with tab2:
    st.write("🥗 Follow weekly nutrition plan above.")
with tab3:
    st.write("💤 Track sleep according to guidance above.")
