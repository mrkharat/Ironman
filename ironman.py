import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from PIL import Image
import os
import requests
from io import BytesIO
import matplotlib.pyplot as plt

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Ironman Training Coach", layout="wide")

# Dark theme CSS
st.markdown("""
<style>
body {background-color: #0e1117; color: #ffffff;}
.stTabs [role="tab"] {color: #00bfff;}
.stCheckbox label {color: #ffffff;}
.stDataFrame tbody tr th, .stDataFrame tbody tr td {color: #ffffff;}
</style>
""", unsafe_allow_html=True)

# -------------------- CONSTANTS --------------------
ATHLETES = ["Mayur", "Sudeep", "Vaishali"]
TODAY = date.today()
NOW = datetime.now()
IRONMAN_HAMBURG = date(2028, 7, 15)
DATA_DIR = "data"

# Ensure data folder exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -------------------- SIDEBAR --------------------
st.sidebar.title("Ironman Coaching")

# Logo
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
try:
    response = requests.get(LOGO_URL)
    logo = Image.open(BytesIO(response.content))
    st.sidebar.image(logo, use_container_width=True)
except:
    st.sidebar.write("Logo not available")

# Athlete selection
selected_athlete = st.sidebar.selectbox("Select Athlete", ATHLETES)

# Hamburg countdown
days_left = (IRONMAN_HAMBURG - TODAY).days
st.sidebar.metric(label="Ironman Hamburg 2028", value=f"{days_left} days left")
st.sidebar.write(f"Date: {IRONMAN_HAMBURG.strftime('%d %b %Y')}")

# -------------------- GREETING --------------------
hour = NOW.hour
if 5 <= hour < 12: greeting = "Good Morning"
elif 12 <= hour < 17: greeting = "Good Afternoon"
elif 17 <= hour < 21: greeting = "Good Evening"
else: greeting = "Good Night"

st.markdown(f"## {greeting}, {selected_athlete} 👋")
st.markdown(f"### Today: {TODAY.strftime('%A, %d %B %Y')}")
week_start = TODAY - timedelta(days=TODAY.weekday())
st.markdown(f"### Current Week Start: {week_start.strftime('%d %b %Y')}")

# -------------------- PHASES --------------------
def get_phase(current_date):
    if current_date < date(2026,1,1): return "Base Phase"
    elif current_date < date(2027,1,1): return "Build Phase"
    elif current_date < date(2028,1,1): return "Peak Phase"
    else: return "Race-Specific Phase"

# -------------------- TRAINING PLAN --------------------
def get_daily_activities(current_date):
    phase = get_phase(current_date)
    if phase=="Base Phase":
        return {"Run":"5 km easy","Swim":"Not started","Bike":"Not started","Strength":"15 min core"}
    elif phase=="Build Phase":
        return {"Run":"10 km","Swim":"500 m","Bike":"20 km","Strength":"20 min core"}
    elif phase=="Peak Phase":
        return {"Run":"15 km","Swim":"1000 m","Bike":"40 km","Strength":"30 min core"}
    else:
        return {"Run":"Race pace run","Swim":"Race pace swim","Bike":"Race pace bike","Strength":"Race prep"}

# -------------------- TABS --------------------
tabs = st.tabs(["Today's Plan","Next Day Preview","Weekly Overview","Progress Tracker","Nutrition Log","Graphs"])

# -------------------- TODAY'S PLAN --------------------
with tabs[0]:
    st.subheader("Today's Activities")
    activities = get_daily_activities(TODAY)
    activity_status = {}
    for act, desc in activities.items():
        key = f"{selected_athlete}_{act}_{TODAY}"
        activity_status[act] = st.checkbox(f"{act}: {desc}", key=key)

    # Nutrition plan
    st.subheader("Nutrition Plan")
    nutrition_plan = pd.DataFrame({
        "Meal": ["Breakfast","Snack1","Lunch","Snack2","Dinner"],
        "Food": [
            "Oats porridge + banana + herbal tea",
            "Fruits or nuts",
            "Brown rice, dal, vegetables, paneer/chicken/fish",
            "Smoothie or yogurt",
            "Quinoa/roti, vegetables, protein"
        ],
        "Time": ["7:30 AM","10:30 AM","1:00 PM","4:30 PM","8:00 PM"]
    })
    for i, row in nutrition_plan.iterrows():
        key = f"{selected_athlete}_meal_{i}_{TODAY}"
        nutrition_plan.loc[i,"Completed"] = st.checkbox(f"{row['Meal']} ({row['Food']}) at {row['Time']}", key=key)
    st.dataframe(nutrition_plan.style.set_properties(**{'background-color':'#1e1e2e','color':'#ffffff'}))

# -------------------- NEXT DAY PREVIEW --------------------
with tabs[1]:
    st.subheader("Next Day Plan")
    tomorrow = TODAY + timedelta(days=1)
    next_activities = get_daily_activities(tomorrow)
    for act, desc in next_activities.items():
        st.markdown(f"**{act}**: {desc}")

# -------------------- WEEKLY OVERVIEW --------------------
with tabs[2]:
    st.subheader("Weekly Overview")
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    overview_data = []
    for d in week_dates:
        daily_act = get_daily_activities(d)
        overview_data.append({
            "Date": d.strftime("%d %b"),
            **daily_act
        })
    df_week = pd.DataFrame(overview_data)
    st.dataframe(df_week.style.set_properties(**{'background-color':'#1e1e2e','color':'#ffffff'}))

# -------------------- PROGRESS TRACKER --------------------
with tabs[3]:
    st.subheader("Progress Tracker")
    progress_file = os.path.join(DATA_DIR, f"{selected_athlete}_progress.csv")
    if os.path.exists(progress_file):
        df_progress = pd.read_csv(progress_file)
    else:
        df_progress = pd.DataFrame(columns=["Date","Run Completed","Swim Completed","Bike Completed","Strength Completed"])
        df_progress.to_csv(progress_file,index=False)
    st.dataframe(df_progress.style.set_properties(**{'background-color':'#1e1e2e','color':'#ffffff'}))

# -------------------- NUTRITION LOG --------------------
with tabs[4]:
    st.subheader("Nutrition Log")
    nutrition_file = os.path.join(DATA_DIR, f"{selected_athlete}_nutrition.csv")
    if os.path.exists(nutrition_file):
        df_nutri = pd.read_csv(nutrition_file)
    else:
        df_nutri = pd.DataFrame(columns=["Date","Meal","Food","Completed"])
        df_nutri.to_csv(nutrition_file,index=False)
    st.dataframe(df_nutri.style.set_properties(**{'background-color':'#1e1e2e','color':'#ffffff'}))

# -------------------- GRAPHS --------------------
with tabs[5]:
    st.subheader("Progress Graphs")
    if not df_progress.empty:
        df_plot = df_progress.copy()
        df_plot['Date'] = pd.to_datetime(df_plot['Date'])
        df_plot.set_index('Date', inplace=True)
        df_plot = df_plot.fillna(0)
        fig, ax = plt.subplots(figsize=(10,4))
        for col in ["Run Completed","Swim Completed","Bike Completed","Strength Completed"]:
            ax.plot(df_plot.index, df_plot[col], marker='o', label=col)
        ax.set_facecolor('#0e1117')
        fig.patch.set_facecolor('#0e1117')
        ax.set_xlabel("Date")
        ax.set_ylabel("Completion (%)")
        ax.set_title("Weekly Activity Completion")
        ax.legend(facecolor='#1e1e2e', edgecolor='white')
        ax.tick_params(axis='x', rotation=45, colors='white')
        ax.tick_params(axis='y', colors='white')
        st.pyplot(fig)

# -------------------- AUTOMATIC GUIDANCE --------------------
st.markdown("---")
st.subheader("Coach's Suggestions")
missed_activities = [act for act, done in activity_status.items() if not done]
if missed_activities:
    st.warning(f"Try to complete missed activities today: {', '.join(missed_activities)}")
else:
    st.success("Great job! All planned activities completed for today ✅")
