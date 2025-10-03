# -------------------- Ironman 3-Year Coach App --------------------
import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from datetime import date, timedelta

# -------------------- SETTINGS --------------------
st.set_page_config(page_title="Ironman Coach", layout="wide")
st.markdown("""
<style>
body {background-color:#121212; color:white;}
.stSidebar {background-color:#1e1e1e;}
.stButton>button {background-color:#4CAF50;color:white;}
</style>
""", unsafe_allow_html=True)

# -------------------- ATHLETE INFO --------------------
athlete_info = {
    "Mayur":{"weight":62, "target_weight":60},
    "Sudeep":{"weight":73, "target_weight":70},
    "Vaishali":{"weight":64, "target_weight":58}
}

# -------------------- DATA DIR --------------------
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# -------------------- SIDEBAR --------------------
st.sidebar.title("Ironman Coach")
athlete_selected = st.sidebar.selectbox("Select Athlete", list(athlete_info.keys()))
hamburg_date = datetime.date(2028,7,16)

# Countdown timer
today = datetime.date.today()
days_left = (hamburg_date - today).days
hours_left = ((hamburg_date - today).total_seconds())//3600
st.sidebar.markdown(f"**Ironman Hamburg 2028 Countdown:** {days_left} days ({int(hours_left)} hours)")

st.sidebar.image("https://github.com/mrkharat/Ironman/blob/main/Ironman-Logo.jpg", use_container_width=True)

# -------------------- GREETING --------------------
now = datetime.datetime.now()
hour = now.hour
greet = "Good Morning" if hour<12 else "Good Afternoon" if hour<17 else "Good Evening"
st.title(f"{greet}, {athlete_selected}!")
st.write(f"Today: {now.strftime('%A, %d %B %Y')}")
week_no = now.isocalendar()[1]
st.write(f"Week: {week_no}")

# -------------------- UTILS --------------------
def generate_weekly_plan(athlete, current_date):
    """Generate a sample weekly plan based on athlete info & current date."""
    plan = []
    swim_start = datetime.date(2025,11,1)
    bike_start = datetime.date(2026,2,1)
    for i in range(7):
        day_date = current_date + timedelta(days=i)
        day = day_date.strftime("%A")
        # Assign activities based on start date
        run = "5-10 km" if i%2==0 else "Rest"
        swim = "30 min" if day_date>=swim_start else "Rest"
        bike = "30-45 min" if day_date>=bike_start else "Rest"
        strength = "30 min" if i%2==1 else "Rest"
        nutrition = "Breakfast/Lunch/Dinner/Snack"
        plan.append({
            "Date": day_date,
            "Day": day,
            "Run": run,
            "Swim": swim,
            "Bike": bike,
            "Strength": strength,
            "Nutrition": nutrition
        })
    return pd.DataFrame(plan)

def load_logs(athlete):
    filepath = os.path.join(DATA_DIR, f"{athlete}_logs.csv")
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        df = generate_weekly_plan(athlete, today)
        for col in ["Run Done","Swim Done","Bike Done","Strength Done"]:
            df[col] = False
        df.to_csv(filepath, index=False)
        return df

def save_logs(athlete, df):
    filepath = os.path.join(DATA_DIR, f"{athlete}_logs.csv")
    df.to_csv(filepath, index=False)

# -------------------- LOAD LOGS --------------------
df_log = load_logs(athlete_selected)

# -------------------- TABS --------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Today's Plan","Next Day","Weekly Plan","Team Overview","Logs","Nutrition"])

# -------------------- TAB 1: TODAY --------------------
with tab1:
    st.subheader("Today's Plan")
    today_plan = df_log[df_log["Date"]==today]
    if not today_plan.empty:
        today_plan = today_plan.iloc[0]
        st.markdown(f"**Day:** {today_plan['Day']}")
        st.markdown(f"**Run:** {today_plan['Run']}")
        st.markdown(f"**Swim:** {today_plan['Swim']}")
        st.markdown(f"**Bike:** {today_plan['Bike']}")
        st.markdown(f"**Strength:** {today_plan['Strength']}")
        st.markdown(f"**Nutrition:** {today_plan['Nutrition']}")
        st.markdown(f"**Current Weight:** {athlete_info[athlete_selected]['weight']} kg | **Target Weight:** {athlete_info[athlete_selected]['target_weight']} kg")
    else:
        st.write("No plan available for today.")

# -------------------- TAB 2: NEXT DAY --------------------
with tab2:
    st.subheader("Next Day Plan")
    next_date = today + timedelta(days=1)
    next_plan = df_log[df_log["Date"]==next_date]
    if not next_plan.empty:
        next_plan = next_plan.iloc[0]
        st.markdown(f"**Day:** {next_plan['Day']}")
        st.markdown(f"**Run:** {next_plan['Run']}")
        st.markdown(f"**Swim:** {next_plan['Swim']}")
        st.markdown(f"**Bike:** {next_plan['Bike']}")
        st.markdown(f"**Strength:** {next_plan['Strength']}")
        st.markdown(f"**Nutrition:** {next_plan['Nutrition']}")
    else:
        st.write("No plan available for next day.")

# -------------------- TAB 3: WEEKLY PLAN --------------------
with tab3:
    st.subheader("Weekly Plan")
    week_plan = df_log[(df_log["Date"]>=today) & (df_log["Date"]<today+timedelta(days=7))]
    st.dataframe(week_plan[["Date","Day","Run","Swim","Bike","Strength","Nutrition"]])

# -------------------- TAB 4: TEAM OVERVIEW --------------------
with tab4:
    st.subheader("Team Progress Overview")
    team_data = []
    for athlete in athlete_info:
        df = load_logs(athlete)
        total = len(df)
        team_data.append({
            "Athlete": athlete,
            "Run %": df["Run Done"].sum()/total*100,
            "Swim %": df["Swim Done"].sum()/total*100,
            "Bike %": df["Bike Done"].sum()/total*100,
            "Strength %": df["Strength Done"].sum()/total*100,
            "Weight": f"{athlete_info[athlete]['weight']}/{athlete_info[athlete]['target_weight']}"
        })
    team_df = pd.DataFrame(team_data)
    fig = px.bar(team_df, x="Athlete", y=["Run %","Swim %","Bike %","Strength %"], barmode="group", text_auto=True, height=400, title="Training Completion %")
    st.plotly_chart(fig)
    st.table(team_df[["Athlete","Weight"]])

# -------------------- TAB 5: LOGS --------------------
with tab5:
    st.subheader("Logs")
    for i, row in df_log.iterrows():
        st.markdown(f"**{row['Day']} ({row['Date']})**")
        df_log.at[i,"Run Done"] = st.checkbox("Run", key=f"{athlete_selected}_run_{i}", value=row["Run Done"])
        df_log.at[i,"Swim Done"] = st.checkbox("Swim", key=f"{athlete_selected}_swim_{i}", value=row["Swim Done"])
        df_log.at[i,"Bike Done"] = st.checkbox("Bike", key=f"{athlete_selected}_bike_{i}", value=row["Bike Done"])
        df_log.at[i,"Strength Done"] = st.checkbox("Strength", key=f"{athlete_selected}_strength_{i}", value=row["Strength Done"])
    save_logs(athlete_selected, df_log)
    st.dataframe(df_log)

# -------------------- TAB 6: NUTRITION --------------------
with tab6:
    st.subheader("Nutrition Plan")
    st.markdown("**India-friendly example plan:**")
    nutrition_df = pd.DataFrame({
        "Meal":["Breakfast","Snack","Lunch","Snack","Dinner"],
        "Food":["Oats/Poha/Idli","Fruits","Rice+Dal+Veg","Nuts/Yogurt","Roti+Veg+Protein"]
    })
    st.table(nutrition_df)
