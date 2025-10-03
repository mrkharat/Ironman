# ironman.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pytz
import random
import plotly.express as px

# ---------------- CONFIG ----------------
PAGE_TITLE = "Ironman 2028 Coach — Maharashtra Plan"
DATA_DIR = "athlete_data"
os.makedirs(DATA_DIR, exist_ok=True)
st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")

# ---------------- TIME / CONSTANTS ----------------
TZ = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(TZ)
IRONMAN_DATE = TZ.localize(datetime(2028, 7, 14, 6, 0, 0))
START_DATE = TZ.localize(datetime(2025, 10, 1, 0, 0, 0))

ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "dob": "25-12"},
    "Sudeep": {"gender": "M", "weight": 73, "dob": "31-10"},
    "Vaishali": {"gender": "F", "weight": 64, "dob": "02-04"}
}

PHASES = ["Base", "Build", "Peak", "Taper"]

# ---------------- THEME ----------------
st.markdown(
    """
    <style>
      body { background-color: #0E1117; color: #FFFFFF; }
      .stButton>button { background-color: #1F2A40; color: #FFFFFF; }
      .stCheckbox>div>label { color: #FFFFFF; }
      .stDataFrame th { color: #FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HELPERS ----------------
REQUIRED_LOG_COLS = [
    "Date", "Phase", "Activity", "CompletedMeals", "Protein_g",
    "Carbs_g", "Fat_g", "Calories", "SleepHours", "Note"
]

def ensure_log(athlete):
    """Ensure CSV file exists and has required columns."""
    fp = os.path.join(DATA_DIR, f"{athlete}_log.csv")
    if not os.path.exists(fp):
        df = pd.DataFrame(columns=REQUIRED_LOG_COLS)
        df.to_csv(fp, index=False)
    return fp

def load_log(athlete):
    """Load log and ensure required columns exist and types are correct."""
    fp = ensure_log(athlete)
    try:
        df = pd.read_csv(fp, parse_dates=["Date"]) if os.path.exists(fp) else pd.DataFrame(columns=REQUIRED_LOG_COLS)
    except Exception:
        # fallback empty with columns
        df = pd.DataFrame(columns=REQUIRED_LOG_COLS)
    # ensure columns
    for c in REQUIRED_LOG_COLS:
        if c not in df.columns:
            df[c] = np.nan
    # coerce numeric columns
    for c in ["Protein_g","Carbs_g","Fat_g","Calories","SleepHours"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # ensure Date is datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

def save_log(athlete, df):
    fp = ensure_log(athlete)
    # ensure Date saved as ISO
    df = df.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df.to_csv(fp, index=False)

def countdown_days(target_dt):
    delta = target_dt - datetime.now(TZ)
    return delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60

def current_week_number(now_dt):
    return ((now_dt - START_DATE).days) // 7 + 1

def current_phase_for_date(date_dt):
    weeks = ((date_dt - START_DATE).days) // 7
    idx = (weeks // 12) % 4
    return PHASES[idx]

# ---------------- FOOD & MACROS ----------------
FOOD_MACROS = {
    "Poha": (6, 40, 6, 240),
    "Upma": (6, 42, 7, 250),
    "Bhakri (jowar) + Egg": (12, 40, 12, 360),
    "Rotti/Chapati (1)": (3, 15, 1.5, 80),
    "Oats + Milk": (8, 30, 6, 220),
    "Fruits": (1, 20, 0.5, 90),
    "Nuts": (6, 8, 15, 180),
    "Sprouts": (8, 18, 2, 140),
    "Protein Shake": (20, 10, 2, 140),
    "Boiled Eggs (2)": (12, 1, 10, 150),
    "Rice + Dal + Veg": (10, 80, 6, 460),
    "Bhakri + Veg + Dal": (10, 50, 8, 380),
    "Roti + Paneer Curry": (18, 60, 20, 520),
    "Bhakri + Chicken Curry": (30, 45, 15, 520),
    "Rice + Mutton Curry": (35, 75, 25, 720),
    "Rice + Fish Curry": (28, 70, 18, 580),
    "Buttermilk + Nuts": (6, 8, 10, 150),
    "Fruit Salad": (2, 25, 0.5, 110),
    "Protein Bar": (15, 25, 8, 250),
}

MEAL_POOLS = {
    "breakfast": ["Poha", "Upma", "Bhakri (jowar) + Egg", "Oats + Milk"],
    "midmorning": ["Fruits", "Nuts", "Sprouts", "Protein Shake", "Boiled Eggs (2)"],
    "lunch": ["Rice + Dal + Veg", "Bhakri + Veg + Dal", "Roti + Paneer Curry", "Bhakri + Chicken Curry", "Rice + Fish Curry", "Rice + Mutton Curry"],
    "afternoon": ["Buttermilk + Nuts", "Fruit Salad", "Protein Bar", "Fruits"],
    "dinner": ["Roti + Paneer Curry", "Bhakri + Veg + Dal", "Rice + Chicken Curry", "Rice + Fish Curry"]
}

FISH_PAIRINGS = {"Rice + Fish Curry": "Steamed basmati rice or jeera rice"}

PROTEIN_CYCLE = ["veg", "egg", "fish", "chicken", "mutton"]

SUNDAY_ACTIVITIES = [
    "Hike around Lonavala",
    "Plantation drive",
    "Beach cleanup at Alibaug",
    "Long drive to Mahabaleshwar",
    "Community cycling tour"
]

def macros_for_meals(meals):
    p=c=f=cal=0.0
    for m in meals.values():
        if m in FOOD_MACROS:
            mp, mc, mf, mcal = FOOD_MACROS[m]
        else:
            mp, mc, mf, mcal = (8, 30, 8, 250)
        p += mp; c += mc; f += mf; cal += mcal
    return round(p,1), round(c,1), round(f,1), round(cal,0)

def pick_daily_meals(athlete, date_dt):
    weekday = date_dt.weekday()
    idx = list(ATHLETES.keys()).index(athlete)
    cycle_choice = PROTEIN_CYCLE[(idx + weekday) % len(PROTEIN_CYCLE)]

    def choose(pool, allow_nonveg=True):
        options = MEAL_POOLS[pool].copy()
        if not allow_nonveg:
            options = [o for o in options if ("Chicken" not in o and "Mutton" not in o and "Fish" not in o)]
        # prefer protein type
        if cycle_choice == "egg":
            egg_options = [o for o in options if "Egg" in o]
            if egg_options:
                return random.choice(egg_options)
        if cycle_choice == "fish":
            fish_options = [o for o in options if "Fish" in o]
            if fish_options:
                return random.choice(fish_options)
        if cycle_choice == "chicken":
            ck = [o for o in options if "Chicken" in o]
            if ck:
                return random.choice(ck)
        if cycle_choice == "mutton":
            mt = [o for o in options if "Mutton" in o]
            if mt:
                return random.choice(mt)
        # fallback filter to avoid chicken+mutton same day if later chosen
        filtered = options
        if cycle_choice == "chicken":
            filtered = [o for o in filtered if "Mutton" not in o]
        if cycle_choice == "mutton":
            filtered = [o for o in filtered if "Chicken" not in o]
        if not filtered:
            filtered = options
        return random.choice(filtered)

    breakfast = choose("breakfast", allow_nonveg=True)
    mid = choose("midmorning", allow_nonveg=True)
    if cycle_choice in ("chicken","mutton","fish"):
        lunch = choose("lunch", allow_nonveg=True)
        # try ensure protein present
        if cycle_choice=="fish" and "Fish" not in lunch:
            fish_opts = [o for o in MEAL_POOLS["lunch"] if "Fish" in o]
            if fish_opts: lunch = random.choice(fish_opts)
    elif cycle_choice=="egg":
        lunch = choose("lunch", allow_nonveg=False)
    else:
        lunch = choose("lunch", allow_nonveg=False)

    afternoon = choose("afternoon", allow_nonveg=False)
    # dinner rules
    if any(x in lunch for x in ("Chicken","Mutton")):
        dinner_opts = [o for o in MEAL_POOLS["dinner"] if ("Chicken" not in o and "Mutton" not in o)]
        dinner = random.choice(dinner_opts) if dinner_opts else random.choice(MEAL_POOLS["dinner"])
    else:
        dinner = choose("dinner", allow_nonveg=True)

    # avoid chicken+mutton same day
    proteins = " ".join([breakfast, mid, lunch, afternoon, dinner])
    if "Chicken" in proteins and "Mutton" in proteins:
        if "Mutton" in dinner:
            dinner = choose("dinner", allow_nonveg=False)
        elif "Mutton" in lunch:
            lunch = choose("lunch", allow_nonveg=False)

    meals = {"07:30": breakfast, "10:30": mid, "13:30": lunch, "16:30": afternoon, "20:00": dinner}
    return meals

def sunday_suggestion(date_dt):
    if date_dt.weekday() != 6:
        return ""
    if 1 <= date_dt.day <= 7:
        return random.choice(SUNDAY_ACTIVITIES)
    return random.choice(["Rest / gentle walk", "Light yoga", "Easy family outing"])

# ---------------- UI START ----------------
LOGO = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
st.sidebar.image(LOGO, use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown("---")
d_days, d_hours, d_mins = countdown_days(IRONMAN_DATE)
st.sidebar.markdown(f"**Countdown:** {d_days} days, {d_hours}h")
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Quote:** {random.choice(['Consistency beats intensity.','Small steps every day.','Progress, not perfection.'])}")

# Today's special only if present
today_str = NOW.strftime("%d-%m")
if ATHLETES[athlete]["dob"] == today_str:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Today's Special:** 🎉 Happy Birthday {athlete}!")
elif today_str in ("13-11",):  # example Diwali date
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Today's Special:** Diwali")

# Header
hour = NOW.hour
greet = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
st.title(f"{greet}, {athlete}!")
st.markdown(f"**Date:** {NOW.strftime('%A, %d %B %Y')}")
st.markdown(f"**Week starting:** {(NOW - timedelta(days=NOW.weekday())).strftime('%d %b %Y')}")

# Load log & ensure columns
ensure_log(athlete)
df_log = load_log(athlete)

# Tabs
tab_today, tab_next, tab_week, tab_progress, tab_nutrition, tab_team = st.tabs(
    ["Today's Plan","Next Day Plan","Weekly Plan","Progress","Nutrition & Sleep Tracker","Team Overview"]
)

# ---------- Today's Plan ----------
with tab_today:
    st.header("Today's Plan")
    phase = current_phase_for_date(NOW)
    st.markdown(f"**Phase:** {phase}")

    # Activity summary
    if phase == "Base":
        run = f"{5 + 0.1*current_week_number(NOW):.1f} km"
        bike = "0 km"
        swim = "0 m"
    elif phase == "Build":
        run = f"{10 + 0.2*current_week_number(NOW):.1f} km"
        bike = "20-40 km"
        swim = "200-1000 m"
    elif phase == "Peak":
        run = f"{15 + 0.2*current_week_number(NOW):.1f} km"
        bike = "50-80 km"
        swim = "1500-2500 m"
    else:
        run, bike, swim = "Light run", "Light bike", "Light swim"

    c1,c2,c3 = st.columns(3)
    run_done = c1.checkbox(f"Run: {run}", key=f"run_{athlete}_{NOW.date()}")
    bike_done = c2.checkbox(f"Bike: {bike}", key=f"bike_{athlete}_{NOW.date()}")
    swim_done = c3.checkbox(f"Swim: {swim}", key=f"swim_{athlete}_{NOW.date()}")

    # Meals
    meals = pick_daily_meals(athlete, NOW)
    st.subheader("Nutrition (Maharashtrian-style, rotated)")
    meal_checks = {}
    cols = st.columns(5)
    for i,(time,label) in enumerate(meals.items()):
        meal_checks[time] = cols[i].checkbox(f"{time}\n{label}", key=f"{athlete}_meal_{time}_{NOW.date()}")

    prot_total_planned, carbs_total_planned, fat_total_planned, cal_total_planned = macros_for_meals(meals)
    st.markdown(f"**Planned macros (day total):** Protein {prot_total_planned} g • Carbs {carbs_total_planned} g • Fat {fat_total_planned} g • Calories {cal_total_planned} kcal")

    # Sleep & note
    sleep_hours = st.number_input("Sleep hours (last night / planned)", min_value=0.0, max_value=12.0, value=7.0, step=0.5, key=f"sleep_{athlete}_{NOW.date()}")
    note = st.text_area("Notes / feelings (optional)")

    # Sunday suggestion
    sunday_msg = sunday_suggestion(NOW)
    if sunday_msg:
        st.info(f"Sunday suggestion: {sunday_msg}")

    # Save button
    if st.button("Save today's log"):
        eaten_meals = {t:meals[t] for t,v in meal_checks.items() if v}
        prot_e, carbs_e, fat_e, cal_e = macros_for_meals(eaten_meals) if eaten_meals else (0,0,0,0)
        entry = {
            "Date": pd.to_datetime(NOW.date()),
            "Phase": phase,
            "Activity": ",".join([x for x,y in [("Run",run_done),("Bike",bike_done),("Swim",swim_done)] if y]),
            "CompletedMeals": ",".join(eaten_meals.values()),
            "Protein_g": prot_e,
            "Carbs_g": carbs_e,
            "Fat_g": fat_e,
            "Calories": cal_e,
            "SleepHours": sleep_hours,
            "Note": note
        }
        df_log = df_log[df_log["Date"] != pd.to_datetime(NOW.date())]
        df_log = pd.concat([df_log, pd.DataFrame([entry])], ignore_index=True)
        save_log(athlete, df_log)
        st.success("Saved today's log.")

# ---------- Next Day ----------
with tab_next:
    st.header("Next Day Plan")
    nd = NOW + timedelta(days=1)
    st.markdown(f"**Date:** {nd.strftime('%A, %d %b %Y')}")
    phase_nd = current_phase_for_date(nd)
    st.markdown(f"**Phase:** {phase_nd}")
    if phase_nd == "Base":
        st.write("Run + Strength")
    elif phase_nd == "Build":
        st.write("Run + Bike + Strength (introduce/expand swim if available)")
    elif phase_nd == "Peak":
        st.write("Long Run + Long Bike + Swim")
    else:
        st.write("Taper – light, recovery-focused sessions")

    next_meals = pick_daily_meals(athlete, nd)
    st.subheader("Nutrition (next day)")
    for t,m in next_meals.items():
        pairing = FISH_PAIRINGS.get(m, "")
        line = f"{t} - {m}"
        if pairing:
            line += f" (pair with: {pairing})"
        st.write(line)

    if nd.weekday() == 6:
        st.subheader("Sunday / Joint activity")
        if 1 <= nd.day <= 7:
            st.info("Monthly joint activity suggestion: " + random.choice(SUNDAY_ACTIVITIES))
        else:
            st.info("This Sunday: " + sunday_suggestion(nd))

# ---------- Weekly Plan ----------
with tab_week:
    st.header("Weekly Plan (Mon → Sun)")
    week_start = NOW - timedelta(days=NOW.weekday())
    table_rows = []
    for d in [week_start + timedelta(days=i) for i in range(7)]:
        m = pick_daily_meals(athlete, d)
        activity_summary = "Run" if current_phase_for_date(d) == "Base" else "Run/Bike/Swim" if current_phase_for_date(d) in ("Build","Peak") else "Light"
        table_rows.append({
            "Day": d.strftime("%A"),
            "ActivitySummary": activity_summary,
            "MealsSample": f"{m['07:30']} | {m['13:30']}",
            "SundayActivity": sunday_suggestion(d) if d.weekday()==6 else ""
        })
    st.dataframe(pd.DataFrame(table_rows)[["Day","ActivitySummary","MealsSample","SundayActivity"]])

# ---------- Progress ----------
with tab_progress:
    st.header("Progress")
    if df_log.empty:
        st.info("No logs yet. Save today's log to populate progress charts.")
    else:
        df_recent = df_log.copy()
        df_recent["Date"] = pd.to_datetime(df_recent["Date"])
        last_12w = pd.to_datetime(NOW.date()) - pd.Timedelta(weeks=12)
        df_recent = df_recent[df_recent["Date"] >= last_12w]
        if df_recent.empty:
            st.info("No recent logs in last 12 weeks.")
        else:
            # ensure numeric cols exist
            for col in ["Protein_g","Calories"]:
                if col not in df_recent.columns:
                    df_recent[col] = 0
            weekly = df_recent.set_index("Date").resample("W").sum(numeric_only=True).reset_index()
            # reindex to include columns safely
            weekly = weekly.reindex(columns=["Date","Protein_g","Calories"], fill_value=0)
            if not weekly.empty:
                fig = px.bar(weekly, x="Date", y=["Protein_g","Calories"], title="Weekly Protein & Calories (last 12 weeks)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for weekly chart.")

# ---------- Nutrition & Sleep Tracker ----------
with tab_nutrition:
    st.header("Nutrition & Sleep Tracker")
    if df_log.empty:
        st.info("No nutrition logs yet. Save today's log to view here.")
    else:
        view = df_log.copy().sort_values("Date", ascending=False).head(60)
        # show essential columns
        cols = ["Date","Protein_g","Carbs_g","Fat_g","Calories","SleepHours","CompletedMeals"]
        for c in cols:
            if c not in view.columns:
                view[c] = 0
        st.dataframe(view[cols])
        st.markdown("---")
        st.markdown(f"**Average Protein (last {len(view)} entries):** {view['Protein_g'].mean():.1f} g")
        st.markdown(f"**Average Calories (last {len(view)} entries):** {view['Calories'].mean():.0f} kcal")
        st.markdown(f"**Average Sleep (last {len(view)} entries):** {view['SleepHours'].mean():.1f} h")

# ---------- Team Overview ----------
with tab_team:
    st.header("Team Overview")
    summary = []
    for a in ATHLETES.keys():
        fp = os.path.join(DATA_DIR, f"{a}_log.csv")
        if os.path.exists(fp):
            dfa = pd.read_csv(fp, parse_dates=["Date"])
            # ensure columns exist
            for c in ["Protein_g","Calories","SleepHours"]:
                if c not in dfa.columns:
                    dfa[c] = 0
            recent = dfa.tail(14)
            total_prot = recent["Protein_g"].sum()
            total_cal = recent["Calories"].sum()
            avg_sleep = recent["SleepHours"].mean() if len(recent)>0 else 0
            summary.append({"Athlete": a, "Protein_14d_g": round(total_prot,1), "Calories_14d": int(total_cal), "AvgSleep_h": round(float(avg_sleep),1)})
        else:
            summary.append({"Athlete": a, "Protein_14d_g": 0, "Calories_14d": 0, "AvgSleep_h": 0})
    sum_df = pd.DataFrame(summary)
    st.dataframe(sum_df[["Athlete","Protein_14d_g","Calories_14d","AvgSleep_h"]])

    if not sum_df.empty:
        figp = px.bar(sum_df, x="Athlete", y="Protein_14d_g", title="Protein in last 14 days (g)")
        figc = px.bar(sum_df, x="Athlete", y="Calories_14d", title="Calories in last 14 days")
        st.plotly_chart(figp, use_container_width=True)
        st.plotly_chart(figc, use_container_width=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("Notes: meals and macros are approximate. Meals rotate by athlete/day — chicken/mutton/fish/egg rotation enforced so not everyone gets non-veg daily and chicken & mutton are not on same day. All times are IST (Asia/Kolkata).")
