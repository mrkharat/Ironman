import streamlit as st
import pandas as pd
import datetime

# -------------------- Page Config --------------------
st.set_page_config(
    page_title="Ironman Training Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Sidebar --------------------
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("Ironman Dashboard")

TODAY = datetime.datetime.now()
race_day = datetime.datetime(2025, 8, 17)  # Example: Hamburg race date
days_left = (race_day - TODAY).days

st.sidebar.metric("🏁 Race Day Countdown", f"{days_left} days")

# -------------------- User Profile --------------------
athlete = "Mayur"
MEALS = ["Balanced breakfast", "Hydration with electrolytes", "Protein-rich dinner"]
SLEEP_HOURS = 7.5

# -------------------- Training Calendar --------------------
df_calendar = pd.DataFrame({
    "Week Start": pd.date_range(start="2025-01-01", periods=10, freq="7D"),
    "Run (km)": [20, 25, 30, 35, 40, 30, 45, 50, 55, 60],
    "Bike (km)": [100, 120, 130, 140, 150, 160, 170, 180, 200, 220],
    "Swim (km)": [2, 2.5, 3, 3.2, 3.5, 3.7, 4, 4.2, 4.5, 5],
    "Strength (min)": [60, 70, 75, 80, 90, 95, 100, 110, 120, 130]
})

# -------------------- Greeting & Today’s Tasks --------------------
now = datetime.datetime.now()
if now.hour < 12:
    greet = "Good Morning"
elif now.hour < 17:
    greet = "Good Afternoon"
else:
    greet = "Good Evening"

st.markdown(f"## {greet}, {athlete}! 👋")
st.markdown(f"### Today: {TODAY.strftime('%A, %d %B %Y')}")

today_week_df = df_calendar[df_calendar["Week Start"] <= TODAY]

if today_week_df.empty:
    st.warning("Today's date is before the training plan start.")
else:
    today_plan = today_week_df.iloc[-1]
    st.markdown("### 🏋️ Today's Training Plan")
    st.dataframe(
        pd.DataFrame({
            "Activity":["Run (km)","Bike (km)","Swim (km)","Strength (min)"],
            "Target":[today_plan["Run (km)"], today_plan["Bike (km)"], today_plan["Swim (km)"], today_plan["Strength (min)"]]
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### 🍎 Nutrition & Sleep Recommendation")
    st.write(f"- Meals: {', '.join(MEALS)}")
    st.write(f"- Sleep: ~{SLEEP_HOURS} hours")

st.markdown("---")

# -------------------- Tabs --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📅 Weekly Plan", "📊 Phase Tracker", "🍽️ Meal & Sleep Log", "💡 Coaching Suggestions", "👥 Team Dashboard"]
)

with tab1:
    st.subheader("Weekly Training Plan")
    st.dataframe(df_calendar, use_container_width=True)

with tab2:
    st.subheader("Phase Tracker")
    df_phase = pd.DataFrame({
        "Phase": ["Base", "Build", "Peak", "Taper"],
        "Progress (%)": [40, 20, 0, 0]
    })
    st.dataframe(df_phase, use_container_width=True)

    readiness = sum([row[2]*w for row,w in zip(df_phase.itertuples(), [0.1,0.4,0.25,0.25])])
    st.metric("Readiness Score", f"{readiness:.1f} %")

with tab3:
    st.subheader("Meal & Sleep Log")
    st.info("Here you can add daily meals and sleep tracking (to be integrated).")

with tab4:
    st.subheader("Coaching Suggestions")
    st.write("✅ Focus on endurance in biking this week.")
    st.write("✅ Add more stretching sessions post runs.")

with tab5:
    st.subheader("Team Dashboard")
    st.info("Team comparison & leaderboard will be added here.")
