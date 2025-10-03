import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random
import plotly.express as px

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Ironman Coach",
    layout="wide"
)

# ------------------ DARK THEME ------------------
st.markdown(
    """
    <style>
    .main {background-color: #121212; color: white;}
    .stSidebar {background-color: #1e1e1e;}
    .css-1d391kg {background-color:#121212;}
    .css-18ni7ap {color:white;}
    </style>
    """, unsafe_allow_html=True
)

# ------------------ ATHLETES ------------------
ATHLETES = {
    "Mayur": {"gender":"male","weight":62,"dob":"25-12","target_weight":62},
    "Sudeep": {"gender":"male","weight":73,"dob":"31-10","target_weight":70},
    "Vaishali": {"gender":"female","weight":64,"dob":"02-04","target_weight":60}
}

# ------------------ DATA FOLDER ------------------
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ------------------ UTILS ------------------
def indian_time():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def greeting():
    now = indian_time()
    if now.hour < 12:
        return "Good Morning"
    elif now.hour < 16:
        return "Good Afternoon"
    else:
        return "Good Evening"

def countdown(date):
    delta = date - indian_time()
    return delta.days, delta.seconds//3600, (delta.seconds//60)%60

def quote_of_day():
    quotes = [
        "Consistency beats intensity.",
        "Small daily improvements lead to long-term results.",
        "Discipline is choosing between what you want now and what you want most.",
        "Ironman is not a race, it’s a lifestyle."
    ]
    return random.choice(quotes)

def today_special():
    # Simple demo: festivals or birthdays
    today_str = indian_time().strftime("%d-%m")
    festivals = {"15-08":"Independence Day","26-01":"Republic Day"}
    for athlete, info in ATHLETES.items():
        if today_str == info["dob"]:
            return f"Happy Birthday {athlete}!"
    return festivals.get(today_str,"")

# ------------------ SIDEBAR ------------------
st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg?raw=true", use_column_width=True)
selected_athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
hamburg_date = datetime(2028,7,20)  # Ironman Hamburg 2028
d, h, m = countdown(hamburg_date)
st.sidebar.markdown(f"### Ironman Hamburg 2028 Countdown")
st.sidebar.markdown(f"**{d} days, {h} hours, {m} mins** remaining")
st.sidebar.markdown(f"### Quote of the Day")
st.sidebar.markdown(f"_{quote_of_day()}_")
st.sidebar.markdown(f"### Today Special")
st.sidebar.markdown(f"_{today_special()}_")

# ------------------ LOAD/CREATE LOG ------------------
log_file = os.path.join(DATA_DIR,f"{selected_athlete}_log.csv")
if os.path.exists(log_file):
    df_log = pd.read_csv(log_file, parse_dates=["Date"])
else:
    df_log = pd.DataFrame(columns=["Date","Run","Bike","Swim","Recovery","Nutrition","Weight","Sleep"])

# ------------------ TRAINING PLAN ------------------
# Phases: Base, Build, Peak, Taper (auto-adjust)
today = indian_time().date()

def generate_daily_plan(athlete):
    w = ATHLETES[athlete]["weight"]
    plan = {}
    # If before Nov 2025, only run
    if today < datetime(2025,11,1).date():
        plan["Run"]=5  # km
        plan["Bike"]=0
        plan["Swim"]=0
    elif today < datetime(2026,2,1).date():
        plan["Run"]=7
        plan["Bike"]=0
        plan["Swim"]=1
    else:
        plan["Run"]=10
        plan["Bike"]=15
        plan["Swim"]=2
    plan["Recovery"]=1
    plan["Nutrition"]="Indian meals"
    plan["Weight"]=w
    plan["Sleep"]=7
    return plan

# ------------------ TODAY PLAN ------------------
st.title(f"{greeting()}, {selected_athlete}!")
st.markdown(f"**Date:** {today.strftime('%A, %d %B %Y')}")
week_start = today - timedelta(days=today.weekday())
st.markdown(f"**Week starting:** {week_start.strftime('%d %b %Y')}")

today_plan = generate_daily_plan(selected_athlete)
st.subheader("Today's Plan")
for k,v in today_plan.items():
    if k in ["Run","Bike","Swim","Recovery"]:
        checked = st.checkbox(f"{k}: {v} km/hr" if k!="Recovery" else f"{k}: {v} hr", key=f"{selected_athlete}_{k}_{today}")
        today_plan[k]=v if checked else 0
    elif k=="Nutrition":
        st.markdown(f"**Nutrition:** {v} (Breakfast 7:30am, Lunch 1pm, Snack 5pm, Dinner 8pm)")
    else:
        st.markdown(f"**{k}: {v}**")

# ------------------ SAVE LOG ------------------
if not df_log[(df_log["Date"]==pd.to_datetime(today))].empty:
    df_log.loc[df_log["Date"]==pd.to_datetime(today), ["Run","Bike","Swim","Recovery","Nutrition","Weight","Sleep"]]=[
        today_plan["Run"], today_plan["Bike"], today_plan["Swim"], today_plan["Recovery"],
        today_plan["Nutrition"], today_plan["Weight"], today_plan["Sleep"]
    ]
else:
    new_row = {"Date":today, **today_plan}
    df_log = pd.concat([df_log,pd.DataFrame([new_row])], ignore_index=True)
df_log.to_csv(log_file,index=False)

# ------------------ NEXT DAY PLAN ------------------
st.subheader("Next Day Plan")
next_day = today + timedelta(days=1)
next_plan = generate_daily_plan(selected_athlete)
st.write(next_plan)

# ------------------ WEEKLY OVERVIEW ------------------
st.subheader("Weekly Overview")
week_mask = (df_log["Date"]>=week_start) & (df_log["Date"]<=today)
week_data = df_log.loc[week_mask]
if not week_data.empty:
    fig = px.bar(week_data, x="Date", y=["Run","Bike","Swim"], barmode='group', title="Weekly Training")
    st.plotly_chart(fig)

# ------------------ TEAM OVERVIEW ------------------
st.subheader("Team Overview")
team_df = pd.DataFrame()
for athlete in ATHLETES:
    lf = os.path.join(DATA_DIR,f"{athlete}_log.csv")
    if os.path.exists(lf):
        df_a = pd.read_csv(lf, parse_dates=["Date"])
        total = df_a[["Run","Bike","Swim"]].sum()
        team_df[athlete]=total
team_df=team_df.T
team_df["Total"]=team_df.sum(axis=1)
fig2 = px.bar(team_df, x=team_df.index, y=["Run","Bike","Swim"], barmode='stack', title="Team Progress")
st.plotly_chart(fig2)

# ------------------ LOGS ------------------
st.subheader("Logs")
st.dataframe(df_log)

# ------------------ SUNDAY SUGGESTIONS ------------------
if today.weekday()==6:
    st.subheader("Sunday Fun Suggestions")
    suggestions = ["Go for a hike","Long drive","Plantation drive","Joint team activity once a month"]
    st.write(", ".join(suggestions))
