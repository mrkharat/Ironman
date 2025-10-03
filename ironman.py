import streamlit as st
import pandas as pd
import numpy as np
import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Ironman Hamburg 2028 Training", layout="wide")

IRONMAN_DATE = datetime.datetime(2028, 7, 2)
ATHLETES = ["Vaishali", "Sudeep", "Mayur"]

# ---------------- UTILS ----------------
def countdown():
    now = datetime.datetime.now()
    delta = IRONMAN_DATE - now
    return delta.days

def get_quote():
    quotes = [
        "Consistency beats intensity.",
        "Small steps daily build Iron legs.",
        "Fuel the body, focus the mind.",
        "Sleep is training too.",
        "Progress, not perfection."
    ]
    return np.random.choice(quotes)

def get_today_special():
    today = datetime.datetime.now()
    specials = {
        (4, 2): "Happy Birthday Vaishali 🎉",
        (10, 31): "Happy Birthday Sudeep 🎉",
        (12, 25): "Happy Birthday Mayur 🎉",
        (10, 2): "Mahatma Gandhi Jayanti 🇮🇳",
        (8, 15): "Independence Day 🇮🇳",
        (1, 26): "Republic Day 🇮🇳",
        (11, 12): "Diwali 🎆",
    }
    return specials.get((today.month, today.day), None)

def suggest_sunday_activity():
    activities = [
        "Group hike in Western Ghats",
        "Cycling trip to Lonavala",
        "Long drive + local food trail",
        "Beach yoga session",
        "Plantation drive together",
        "Cultural heritage walk in Pune/Mumbai"
    ]
    return np.random.choice(activities)

# ---------------- INIT SESSION ----------------
if "data" not in st.session_state:
    st.session_state.data = {a: pd.DataFrame(columns=[
        "Date","Swim_km","Bike_km","Run_km","Recovery_hr",
        "Protein_g","Carbs_g","Fat_g","Calories","Sleep_hr"
    ]) for a in ATHLETES}
if "targets" not in st.session_state:
    st.session_state.targets = {a: {"Protein_g":120,"Carbs_g":300,"Fat_g":60,"Calories":2200,"Sleep_hr":7} for a in ATHLETES}

# ---------------- SIDEBAR ----------------
st.sidebar.image("logo.png", use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", ATHLETES)
st.sidebar.markdown(f"**Countdown to Ironman Hamburg 2028:** {countdown()} days")
st.sidebar.markdown(f"**Quote of the Day:** {get_quote()}")
special = get_today_special()
if special:
    st.sidebar.markdown(f"**Today’s Special:** {special}")

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📅 Next Day Plan", "📊 Progress", "🥗 Nutrition & Sleep", "👥 Team Overview"])

# --- TAB 1: NEXT DAY PLAN ---
with tab1:
    st.header(f"Next Day Plan for {athlete}")
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    if tomorrow.weekday() == 6:  # Sunday
        st.subheader("Sunday = Active Rest Day")
        st.write(f"Suggested Group Activity: **{suggest_sunday_activity()}**")
        tomorrow_special = get_today_special()
        if tomorrow_special:
            st.success(f"🎉 Tomorrow Special: {tomorrow_special}")
    else:
        st.write("Structured training as per Base/Build/Peak/Taper phases.")

# --- TAB 2: PROGRESS ---
with tab2:
    st.header(f"Training Progress - {athlete}")
    df = st.session_state.data[athlete]
    if df.empty:
        st.info("No training data yet.")
    else:
        df_recent = df.tail(30)
        df_recent = df_recent.set_index("Date")
        st.line_chart(df_recent[["Swim_km","Bike_km","Run_km"]])

# --- TAB 3: NUTRITION & SLEEP ---
with tab3:
    st.header(f"Nutrition & Sleep Tracking - {athlete}")

    # Input today's data
    with st.form(f"nutrition_{athlete}"):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        swim = st.number_input("Swim (km)",0.0,10.0,0.0,0.1)
        bike = st.number_input("Bike (km)",0.0,200.0,0.0,1.0)
        run = st.number_input("Run (km)",0.0,50.0,0.0,0.5)
        rec = st.number_input("Recovery (hrs)",0.0,24.0,0.0,0.5)

        protein = st.number_input("Protein (g)",0.0,300.0,0.0,1.0)
        carbs = st.number_input("Carbs (g)",0.0,600.0,0.0,1.0)
        fat = st.number_input("Fat (g)",0.0,150.0,0.0,1.0)
        calories = st.number_input("Calories",0.0,6000.0,0.0,10.0)
        sleep = st.number_input("Sleep (hrs)",0.0,24.0,0.0,0.5)

        submit = st.form_submit_button("Log Today")
        if submit:
            new_row = pd.DataFrame([{
                "Date": today,"Swim_km":swim,"Bike_km":bike,"Run_km":run,"Recovery_hr":rec,
                "Protein_g":protein,"Carbs_g":carbs,"Fat_g":fat,"Calories":calories,"Sleep_hr":sleep
            }])
            st.session_state.data[athlete] = pd.concat([df,new_row],ignore_index=True)
            st.success("Logged successfully!")

    # Display targets & alerts
    st.subheader("Macro Targets")
    target_protein = st.number_input("Protein Target (g/day)",50,300,st.session_state.targets[athlete]["Protein_g"],1)
    target_carbs = st.number_input("Carbs Target (g/day)",100,700,st.session_state.targets[athlete]["Carbs_g"],5)
    target_fat = st.number_input("Fat Target (g/day)",20,150,st.session_state.targets[athlete]["Fat_g"],1)
    target_cal = st.number_input("Calories Target (kcal/day)",1000,6000,st.session_state.targets[athlete]["Calories"],50)
    target_sleep = st.number_input("Sleep Target (hrs/day)",4,12,st.session_state.targets[athlete]["Sleep_hr"],1)

    st.session_state.targets[athlete] = {
        "Protein_g":target_protein,"Carbs_g":target_carbs,"Fat_g":target_fat,"Calories":target_cal,"Sleep_hr":target_sleep
    }

    if not df.empty:
        latest = df.iloc[-1]
        for macro in ["Protein_g","Carbs_g","Fat_g","Calories","Sleep_hr"]:
            if latest[macro] < st.session_state.targets[athlete][macro]:
                st.warning(f"{macro} below target! ({latest[macro]} < {st.session_state.targets[athlete][macro]})")

        st.line_chart(df.set_index("Date")[["Protein_g","Carbs_g","Fat_g","Calories","Sleep_hr"]])

# --- TAB 4: TEAM OVERVIEW ---
with tab4:
    st.header("Team Overview - Combined Progress")

    combined = pd.concat(st.session_state.data.values(), keys=st.session_state.data.keys())
    if combined.empty:
        st.info("No team data yet.")
    else:
        combined = combined.reset_index(level=0).rename(columns={"level_0":"Athlete"})
        st.subheader("Activity Comparison")
        st.bar_chart(combined.groupby("Athlete")[["Swim_km","Bike_km","Run_km"]].sum())

        st.subheader("Nutrition & Sleep Comparison")
        st.bar_chart(combined.groupby("Athlete")[["Protein_g","Carbs_g","Calories","Sleep_hr"]].mean())

        # Ironman readiness
        swim_total = combined["Swim_km"].sum()
        bike_total = combined["Bike_km"].sum()
        run_total = combined["Run_km"].sum()

        st.subheader("Ironman Hamburg 2028 Readiness Check")
        if swim_total>3800 and bike_total>180 and run_total>42:
            st.success("On Track! Distances covered are in line with Ironman Hamburg goals.")
        else:
            st.warning("Still building up towards Ironman distances. Keep training!")
