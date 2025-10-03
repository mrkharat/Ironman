# ironman_coach_app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pytz
import random

# ----------------------------- Configuration -----------------------------
st.set_page_config(page_title="Ironman Coach", layout="wide")
st.markdown(
    """
    <style>
    .css-1d391kg {padding-top: 0rem;}
    .css-18ni7ap {padding-top: 0rem;}
    .stButton>button {color:white;background-color:#007ACC;}
    .stRadio>div>div>label {color:white;}
    </style>
    """, unsafe_allow_html=True
)

# ----------------------------- Dark Theme -----------------------------
st.markdown(
    """
    <style>
    .main {background-color:#0E1117;color:white;}
    .stMarkdown p, .stTextInput input, .stTextArea textarea {color:white;}
    .stCheckbox>div>label {color:white;}
    </style>
    """, unsafe_allow_html=True
)

# ----------------------------- Global Variables -----------------------------
ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "dob": "1990-12-25"},
    "Sudeep": {"gender": "M", "weight": 73, "dob": "1990-10-31"},
    "Vaishali": {"gender": "F", "weight": 64, "dob": "1991-04-02"}
}

SUNDAY_ACTIVITIES = ["Hike", "Long Drive", "Plantation Drive", "Cycling Tour", "Beach Walk", "Group Yoga"]

MEALS = {
    "Breakfast": ["Oats with milk & fruits", "Poha with peanuts", "Idli with sambar", "Upma with veggies"],
    "Mid-Morning": ["Fruits", "Nuts", "Buttermilk"],
    "Lunch": ["Chapati + Dal + Sabzi + Rice", "Vegetable Pulao", "Paneer Curry with Chapati"],
    "Evening Snack": ["Sprouts Salad", "Smoothie", "Peanut Butter Sandwich"],
    "Dinner": ["Grilled Veg + Quinoa/Rice", "Roti + Dal + Salad", "Light Soup + Chapati"]
}

IRONMAN_DATE = datetime(2028, 7, 15)  # Hamburg 2028

DATA_DIR = "athlete_logs"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------------------- Utility Functions -----------------------------
def ist_now():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz)

def greeting():
    hour = ist_now().hour
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 21:
        return "Good Evening"
    else:
        return "Good Night"

def load_log(athlete):
    file_path = os.path.join(DATA_DIR, f"{athlete}_log.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=["Date"])
    else:
        df = pd.DataFrame(columns=["Date","Phase","Run","Bike","Swim","Strength","Recovery",
                                   "Nutrition","Weight","Sleep","Completed","SundayActivity"])
        df.to_csv(file_path, index=False)
        return df

def save_log(athlete, df):
    file_path = os.path.join(DATA_DIR, f"{athlete}_log.csv")
    df.to_csv(file_path, index=False)

def get_phase(date):
    # Simple logic: Base 6 months, Build 12 months, Peak 12 months, Taper 6 months
    start = datetime(2025,10,1)
    diff = (date - start).days
    if diff < 180:
        return "Base"
    elif diff < 540:
        return "Build"
    elif diff < 900:
        return "Peak"
    else:
        return "Taper"

def quote_of_the_day():
    quotes = [
        "Pain is temporary, pride is forever.",
        "One step at a time, one day at a time.",
        "Discipline is the bridge between goals and accomplishment.",
        "You don’t have to be extreme, just consistent.",
        "Ironman is won in the mind before the body."
    ]
    return random.choice(quotes)

def indian_festival_today():
    festivals = {
        "01-01":"New Year",
        "15-08":"Independence Day",
        "02-10":"Gandhi Jayanti",
        "25-12":"Christmas"
    }
    today = ist_now().strftime("%d-%m")
    return festivals.get(today, "")

def birthday_today():
    today = ist_now().strftime("%d-%m")
    for name, info in ATHLETES.items():
        dob = datetime.strptime(info["dob"], "%Y-%m-%d").strftime("%d-%m")
        if dob == today:
            return name
    return ""

def generate_nutrition_plan(athlete):
    # Simplified random meal plan based on MEALS
    plan = {}
    for meal, items in MEALS.items():
        plan[meal] = random.choice(items)
    return plan

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.image("https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg", use_container_width=True)
    athlete = st.selectbox("Select Athlete", list(ATHLETES.keys()))
    
    # Countdown
    days_left = (IRONMAN_DATE - ist_now()).days
    st.markdown(f"### Ironman Hamburg 2028 Countdown: {days_left} days")
    
    # Quote
    st.markdown(f"**Quote of the Day:**\n> {quote_of_the_day()}")
    
    # Birthday
    bday_name = birthday_today()
    if bday_name:
        st.markdown(f"**🎂 Happy Birthday {bday_name}!**")
    
    # Festival
    festival = indian_festival_today()
    if festival:
        st.markdown(f"**Today's Special: {festival}**")

# ----------------------------- Main Page -----------------------------
st.markdown(f"# {greeting()}, {athlete}!")
st.markdown(f"**Date:** {ist_now().strftime('%A, %d %B %Y')}")

week_start = ist_now() - timedelta(days=ist_now().weekday())
st.markdown(f"**Week Starting:** {week_start.strftime('%d %b %Y')}")

# ----------------------------- Tabs -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Today's Plan","Weekly Plan","Nutrition & Weight","Team Overview"])

# ----------------------------- Today's Plan -----------------------------
with tab1:
    st.markdown("### Activities for Today")
    df_log = load_log(athlete)
    today = ist_now().replace(hour=0, minute=0, second=0, microsecond=0)
    phase = get_phase(today)
    
    # Auto-set Sunday's joint activity
    if today.weekday()==6:
        st.markdown("**Sunday Joint Activity**")
        selected_activity = st.radio("Choose activity:", SUNDAY_ACTIVITIES, key=f"{athlete}_sunday")
        if st.button("Confirm Sunday Activity"):
            for a in ATHLETES.keys():
                df = load_log(a)
                if any(df["Date"]==today):
                    df.loc[df["Date"]==today,"SundayActivity"] = selected_activity
                else:
                    df = df.append({"Date":today,"Phase":phase,"Run":0,"Bike":0,"Swim":0,"Strength":0,
                                    "Recovery":0,"Nutrition","","Weight":ATHLETES[a]["weight"],"Sleep":0,
                                    "Completed":False,"SundayActivity":selected_activity}, ignore_index=True)
                save_log(a, df)
            st.success(f"Sunday activity '{selected_activity}' set for all athletes!")
    
    # Show today's activities with checkbox
    default_activities = ["Run", "Bike", "Swim", "Strength", "Recovery"]
    activity_status = {}
    for act in default_activities:
        val = st.checkbox(f"{act} done?", key=f"{athlete}_{act}")
        activity_status[act] = val
    
    if st.button("Mark Today's Activities Completed"):
        df_log = load_log(athlete)
        if any(df_log["Date"]==today):
            idx = df_log.index[df_log["Date"]==today][0]
            for act in default_activities:
                df_log.at[idx, act] = int(activity_status[act])
            df_log.at[idx,"Completed"]=all(activity_status.values())
        else:
            df_new = {"Date":today,"Phase":phase}
            for act in default_activities:
                df_new[act]=int(activity_status[act])
            df_new.update({"Recovery":0,"Nutrition":"","Weight":ATHLETES[athlete]["weight"],"Sleep":0,"Completed":all(activity_status.values()),
                           "SundayActivity":""})
            df_log = df_log.append(df_new, ignore_index=True)
        save_log(athlete, df_log)
        st.success("Today's activities saved!")
    
    # Show nutrition plan
    st.markdown("### Today's Nutrition")
    plan = generate_nutrition_plan(athlete)
    for meal, item in plan.items():
        st.markdown(f"**{meal}:** {item}")
    
    # Sleep and weight tracker
    sleep_hours = st.number_input("Sleep Hours Last Night", min_value=0.0, max_value=12.0, step=0.5, value=7.0)
    weight_val = st.number_input(f"Current Weight (kg) [{ATHLETES[athlete]['weight']}]", min_value=40, max_value=150, value=ATHLETES[athlete]['weight'])
    
    # Save weight & sleep
    if st.button("Save Sleep & Weight"):
        df_log = load_log(athlete)
        if any(df_log["Date"]==today):
            idx = df_log.index[df_log["Date"]==today][0]
            df_log.at[idx,"Sleep"]=sleep_hours
            df_log.at[idx,"Weight"]=weight_val
        else:
            df_new = {"Date":today,"Phase":phase,"Run":0,"Bike":0,"Swim":0,"Strength":0,
                      "Recovery":0,"Nutrition":"","Weight":weight_val,"Sleep":sleep_hours,
                      "Completed":False,"SundayActivity":""}
            df_log = df_log.append(df_new, ignore_index=True)
        save_log(athlete, df_log)
        st.success("Weight & Sleep saved!")

# ----------------------------- Weekly Plan -----------------------------
with tab2:
    st.markdown("### Weekly Plan")
    week_end = week_start + timedelta(days=6)
    week_plan = df_log[(df_log["Date"]>=week_start) & (df_log["Date"]<=week_end)]
    st.dataframe(week_plan.fillna(""), use_container_width=True)

# ----------------------------- Nutrition & Weight -----------------------------
with tab3:
    st.markdown("### Weight & Sleep Overview")
    df_overview = df_log[["Date","Weight","Sleep","Phase"]].sort_values("Date")
    st.line_chart(df_overview.set_index("Date")[["Weight","Sleep"]])

# ----------------------------- Team Overview -----------------------------
with tab4:
    st.markdown("### Team Training Status")
    team_df = pd.DataFrame()
    for a in ATHLETES.keys():
        df_temp = load_log(a)[["Date","Completed"]].copy()
        df_temp.rename(columns={"Completed":a}, inplace=True)
        if team_df.empty:
            team_df = df_temp
        else:
            team_df = pd.merge(team_df, df_temp, on="Date", how="outer")
    st.dataframe(team_df.fillna(False), use_container_width=True)
    st.line_chart(team_df.fillna(0).set_index("Date"))

st.markdown("---")
st.markdown("All data auto-adjusts for Ironman 2028 phases (Base, Build, Peak, Taper).")
