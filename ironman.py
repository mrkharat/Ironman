# ---------------- Ironman 2025-2028 Coaching Dashboard ----------------
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ---------------- App Config ----------------
st.set_page_config(
    page_title="Ironman 2025-2028 Coaching",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Sidebar ----------------
st.sidebar.image("https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg", use_column_width=True)
st.sidebar.title("Ironman Coaching Dashboard")
TEAM = ["Mayur","Sudeep","Vaishali"]
athlete = st.sidebar.selectbox("Select Athlete", TEAM)
TODAY = pd.Timestamp(datetime.today().date())

# ---------------- Phases ----------------
PHASES = {
    "Base Phase":[pd.Timestamp("2025-10-01"), pd.Timestamp("2025-12-31")],
    "Endurance Build":[pd.Timestamp("2026-01-01"), pd.Timestamp("2027-06-30")],
    "Strength & Long Distance":[pd.Timestamp("2027-07-01"), pd.Timestamp("2027-12-31")],
    "Peak Ironman Prep":[pd.Timestamp("2028-01-01"), pd.Timestamp("2028-07-31")]
}

# ---------------- Weekly Plan Generator ----------------
def generate_weekly_plan(phase):
    if phase=="Base Phase":
        return {"Run":5,"Bike":10,"Swim":1,"Strength":20}
    elif phase=="Endurance Build":
        return {"Run":10,"Bike":25,"Swim":2,"Strength":20}
    elif phase=="Strength & Long Distance":
        return {"Run":15,"Bike":35,"Swim":3,"Strength":30}
    else:
        return {"Run":20,"Bike":45,"Swim":4,"Strength":30}

# ---------------- Meal & Sleep Generator ----------------
MEALS = ["Pre-Breakfast","Breakfast","Mid-Morning Snack","Lunch",
         "Pre-Workout","Post-Workout","Evening Snack","Dinner","Before Bed"]
SLEEP_HOURS = 7.5

# ---------------- Generate 3-Year Calendar ----------------
start_date = pd.Timestamp("2025-10-01")
end_date = pd.Timestamp("2028-07-31")
weeks = pd.date_range(start=start_date,end=end_date,freq='W-MON')  # Mondays as week start

calendar_data = []
for week_start in weeks:
    # Determine phase
    phase = None
    for pname,(start,end) in PHASES.items():
        if start <= week_start <= end:
            phase = pname
            break
    if not phase:
        phase = "Base Phase"
    plan = generate_weekly_plan(phase)
    calendar_data.append({
        "Week Start":week_start,
        "Phase":phase,
        "Run (km)":plan["Run"],
        "Bike (km)":plan["Bike"],
        "Swim (km)":plan["Swim"],
        "Strength (min)":plan["Strength"],
        "Meals Adherence (%)":0,
        "Sleep Adherence (%)":0
    })

df_calendar = pd.DataFrame(calendar_data)
df_calendar["Week"] = df_calendar["Week Start"].dt.strftime("%Y-%m-%d")

# ---------------- Tabs ----------------
tabs = st.tabs(["3-Year Calendar","Weekly Plan","Phase Tracker","Meal & Sleep Log","Coaching Suggestions"])

# ---------------- TAB 1: 3-Year Calendar (Colored Table) ----------------
with tabs[0]:
    st.header(f"{athlete} - 3-Year Training Calendar (Colored Table)")
    st.info("Cells color intensity shows total training load. Green=High, Yellow=Medium, Red=Low")
    
    df_calendar['Total Load'] = df_calendar["Run (km)"] + df_calendar["Bike (km)"] + df_calendar["Swim (km)"] + df_calendar["Strength (min)"]/10
    
    def color_load(val):
        if val==0:
            color = 'red'
        elif val<30:
            color='yellow'
        else:
            color='green'
        return f'background-color: {color}'
    
    st.dataframe(df_calendar[['Week','Phase','Total Load']].style.applymap(color_load, subset=['Total Load']))

# ---------------- TAB 2: Weekly Plan ----------------
with tabs[1]:
    st.header(f"{athlete} - Current Week Training Plan")
    current_week_df = df_calendar[df_calendar["Week Start"]<=TODAY]
    if current_week_df.empty:
        st.warning("Today's date is before the start of the training plan.")
    else:
        week_plan = current_week_df.iloc[-1]
        st.write(f"Week Start: {week_plan['Week']}, Phase: {week_plan['Phase']}")
        st.dataframe(week_plan[["Run (km)","Bike (km)","Swim (km)","Strength (min)"]])

# ---------------- TAB 3: Phase Tracker ----------------
with tabs[2]:
    st.header(f"{athlete} - Phase Progression Tracker")
    phase_progress=[]
    for pname,(start,end) in PHASES.items():
        total_days=(end-start).days+1
        days_done=(min(TODAY,end)-start).days+1
        progress_pct=max(0,min(100,(days_done/total_days)*100))
        phase_progress.append({"Phase":pname,"Start":start.date(),"End":end.date(),"Progress (%)":round(progress_pct,1)})
    df_phase=pd.DataFrame(phase_progress)
    st.dataframe(df_phase)
    readiness = sum([row['Progress (%)']*w for row,w in zip(df_phase.itertuples(), [0.1,0.4,0.25,0.25])])
    st.info(f"Estimated Ironman 2028 Readiness: {readiness:.1f}%")

# ---------------- TAB 4: Meal & Sleep Log ----------------
with tabs[3]:
    st.header(f"{athlete} - Weekly Meal & Sleep Tracking")
    week_days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    MEAL_LOG = []
    for day in week_days:
        st.markdown(f"### {day}")
        daily_log = {}
        for meal in MEALS:
            key = f"{athlete}_{day}_{meal}"
            checked = st.checkbox(f"{meal}", key=key)
            daily_log[meal] = int(checked)
        sleep_key = f"{athlete}_{day}_sleep"
        slept = st.checkbox(f"Sleep (~{SLEEP_HOURS} hrs)", key=sleep_key)
        daily_log["Sleep"] = int(slept)
        MEAL_LOG.append({"Day":day, **daily_log})
    df_meal_log = pd.DataFrame(MEAL_LOG)
    df_meal_log['Meals Completed'] = df_meal_log[MEALS].sum(axis=1)
    df_meal_log['Meals Adherence (%)'] = df_meal_log['Meals Completed']/len(MEALS)*100
    df_meal_log['Sleep Adherence (%)'] = df_meal_log['Sleep']/1*100
    st.dataframe(df_meal_log[['Day','Meals Adherence (%)','Sleep Adherence (%)']])
    weekly_meals = df_meal_log['Meals Adherence (%)'].mean()
    weekly_sleep = df_meal_log['Sleep Adherence (%)'].mean()
    st.info(f"Weekly Meals Adherence: {weekly_meals:.1f}% | Sleep Adherence: {weekly_sleep:.1f}%")

# ---------------- TAB 5: Coaching Suggestions ----------------
with tabs[4]:
    st.header(f"{athlete} - Weekly Coaching Suggestions")
    st.write("- Gradually increase mileage by 5–10% per week to avoid injuries.")
    st.write("- Incorporate brick sessions (Bike→Run) starting Endurance Build phase.")
    st.write("- Track sleep & meals consistently; low adherence may reduce next week's intensity.")
    st.write("- Monitor fatigue and adjust strength sessions if needed.")
