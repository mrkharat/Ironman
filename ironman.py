# ---------------- Ironman 2025-2028 Professional Coaching Dashboard ----------------
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

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

# ---------------- Countdown ----------------
IRONMAN_HAMBURG_DATE = pd.Timestamp("2028-07-14")
days_left = (IRONMAN_HAMBURG_DATE - TODAY).days
st.sidebar.markdown(f"### Days Left to Ironman Hamburg 2028: {days_left} days")

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

# ---------------- Meal & Sleep ----------------
MEALS = ["Pre-Breakfast","Breakfast","Mid-Morning Snack","Lunch",
         "Pre-Workout","Post-Workout","Evening Snack","Dinner","Before Bed"]
SLEEP_HOURS = 7.5

# ---------------- Generate 3-Year Calendar ----------------
start_date = pd.Timestamp("2025-10-01")
end_date = pd.Timestamp("2028-07-31")
weeks = pd.date_range(start=start_date,end=end_date,freq='W-MON')  # Mondays as week start

calendar_data = []
for week_start in weeks:
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
df_calendar['Total Load'] = df_calendar["Run (km)"] + df_calendar["Bike (km)"] + df_calendar["Swim (km)"] + df_calendar["Strength (min)"]/10

# ---------------- Tabs ----------------
tabs = st.tabs(["3-Year Calendar","Weekly Plan","Phase Tracker","Meal & Sleep Log","Coaching Suggestions","Team Dashboard"])

# ---------------- TAB 1: 3-Year Calendar ----------------
with tabs[0]:
    st.header(f"{athlete} - 3-Year Training Calendar")
    st.info("Total weekly load heatmap: green=high, yellow=medium, red=low")
    st.dataframe(df_calendar[['Week','Phase','Total Load']].style.background_gradient(cmap="Greens"))

# ---------------- TAB 2: Weekly Plan ----------------
with tabs[1]:
    st.header(f"{athlete} - Current Week Training Plan")
    current_week_df = df_calendar[df_calendar["Week Start"]<=TODAY]
    if current_week_df.empty:
        st.warning("Today's date is before the start of the training plan.")
    else:
        week_plan = current_week_df.iloc[-1]
        week_plan_display = week_plan[["Run (km)","Bike (km)","Swim (km)","Strength (min)"]].to_frame().T
        st.dataframe(week_plan_display.style.background_gradient(cmap="Greens"))

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
    st.dataframe(df_phase.style.background_gradient(subset=['Progress (%)'], cmap="Blues").format({"Progress (%)":"{:.1f}%"}))
    
    weights = [0.1, 0.4, 0.25, 0.25]
    readiness = sum(df_phase['Progress (%)'] * weights)
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
    st.dataframe(df_meal_log[['Day','Meals Adherence (%)','Sleep Adherence (%)']].style.background_gradient(cmap="Oranges"))
    st.info(f"Weekly Meals Adherence: {df_meal_log['Meals Adherence (%)'].mean():.1f}% | Sleep Adherence: {df_meal_log['Sleep Adherence (%)'].mean():.1f}%")

# ---------------- TAB 5: Coaching Suggestions ----------------
with tabs[4]:
    st.header(f"{athlete} - Weekly Coaching Suggestions")
    st.write("- Gradually increase mileage by 5–10% per week to avoid injuries.")
    st.write("- Incorporate brick sessions (Bike→Run) starting Endurance Build phase.")
    st.write("- Track sleep & meals consistently; low adherence may reduce next week's intensity.")
    st.write("- Monitor fatigue and adjust strength sessions if needed.")

# ---------------- TAB 6: Team Dashboard ----------------
with tabs[5]:
    st.header("Team Dashboard - Weekly Overview")
    team_data = []
    for member in TEAM:
        week_df = df_calendar[df_calendar["Week Start"]<=TODAY]
        if week_df.empty:
            week_plan = {"Run (km)":0,"Bike (km)":0,"Swim (km)":0,"Strength (min)":0}
        else:
            week_plan = week_df.iloc[-1][["Run (km)","Bike (km)","Swim (km)","Strength (min)"]].to_dict()
        phase_progress=[]
        for pname,(start,end) in PHASES.items():
            total_days=(end-start).days+1
            days_done=(min(TODAY,end)-start).days+1
            progress_pct=max(0,min(100,(days_done/total_days)*100))
            phase_progress.append(progress_pct)
        weights = [0.1,0.4,0.25,0.25]
        readiness = sum(np.array(phase_progress)*np.array(weights))
        team_data.append({
            "Athlete":member,
            "Run (km)":week_plan["Run (km)"],
            "Bike (km)":week_plan["Bike (km)"],
            "Swim (km)":week_plan["Swim (km)"],
            "Strength (min)":week_plan["Strength (min)"],
            "Readiness (%)":round(readiness,1)
        })
    df_team = pd.DataFrame(team_data)
    st.subheader("Weekly Training Load & Readiness")
    st.dataframe(df_team.style.background_gradient(subset=['Run (km)','Bike (km)','Swim (km)','Strength (min)'], cmap='Greens').background_gradient(subset=['Readiness (%)'], cmap='Blues'))
    
    st.subheader("Team Nutrition & Sleep Adherence (Weekly)")
    team_meal_sleep = []
    for member in TEAM:
        total_meals = 0
        total_sleep = 0
        total_days = len(week_days)
        for day in week_days:
            meals_checked = sum([st.session_state.get(f"{member}_{day}_{meal}",0) for meal in MEALS])
            sleep_checked = st.session_state.get(f"{member}_{day}_sleep",0)
            total_meals += meals_checked/len(MEALS)*100
            total_sleep += sleep_checked/1*100
        avg_meals = round(total_meals/total_days,1)
        avg_sleep = round(total_sleep/total_days,1)
        team_meal_sleep.append({
            "Athlete":member,
            "Avg Meals Adherence (%)":avg_meals,
            "Avg Sleep Adherence (%)":avg_sleep
        })
    df_team_meal_sleep = pd.DataFrame(team_meal_sleep)
    st.dataframe(df_team_meal_sleep.style.background_gradient(subset=['Avg Meals Adherence (%)','Avg Sleep Adherence (%)'], cmap='Oranges'))
    
    # ---------------- Suggested Actions ----------------
    st.subheader("Suggested Actions (Weekly)")
    for member in TEAM:
        week_df = df_calendar[df_calendar["Week Start"]<=TODAY]
        if week_df.empty:
            week_plan = {"Run (km)":0,"Bike (km)":0,"Swim (km)":0,"Strength (min)":0}
        else:
            week_plan = week_df.iloc[-1][["Run (km)","Bike (km)","Swim (km)","Strength (min)"]].to_dict()
        
        # Meals & Sleep
        total_meals = 0
        total_sleep = 0
        for day in week_days:
            meals_checked = sum([st.session_state.get(f"{member}_{day}_{meal}",0) for meal in MEALS])
            sleep_checked = st.session_state.get(f"{member}_{day}_sleep",0)
            total_meals += meals_checked/len(MEALS)*100
            total_sleep += sleep_checked/1*100
        avg_meals = total_meals/len(week_days)
        avg_sleep = total_sleep/len(week_days)
        
        st.markdown(f"**{member}**")
        load_actual = sum([week_plan["Run (km)"], week_plan["Bike (km)"], week_plan["Swim (km)"], week_plan["Strength (min)"]/10])
        load_planned = df_calendar[df_calendar["Week Start"]==week_df.iloc[-1]["Week Start"]]["Total Load"].values[0]
        if load_actual < 0.8*load_planned:
            st.write("- ⚠️ Increase training load carefully to reach weekly target.")
        elif load_actual > 1.2*load_planned:
            st.write("- ⚠️ Training load high! Reduce intensity to avoid overtraining.")
        else:
            st.write("- ✅ Training load on track.")
        if avg_meals < 80:
            st.write("- ⚠️ Focus on nutrition this week.")
        else:
            st.write("- ✅ Good nutrition adherence.")
        if avg_sleep < 80:
            st.write("- ⚠️ Increase sleep hours for better recovery.")
        else:
            st.write("- ✅ Sleep on track.")
