# ironman_full_maharashtra.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pytz
import random
import plotly.express as px

# --------------------- CONFIG ---------------------
PAGE_TITLE = "Ironman 2028 Coach — Maharashtra Plan"
DATA_DIR = "athlete_data"
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")

# --------------------- TIME / CONSTANTS ---------------------
TZ = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(TZ)
IRONMAN_DATE = TZ.localize(datetime(2028, 7, 14, 6, 0, 0))  # Hamburg example
START_DATE = TZ.localize(datetime(2025, 10, 1, 0, 0, 0))

ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "dob": "25-12"},
    "Sudeep": {"gender": "M", "weight": 73, "dob": "31-10"},
    "Vaishali": {"gender": "F", "weight": 64, "dob": "02-04"}
}

PHASES = ["Base", "Build", "Peak", "Taper"]
PHASE_WEEKS = {"Base": 20, "Build": 40, "Peak": 20, "Taper": 10}  # approx weeks

# --------------------- THEME ---------------------
st.markdown(
    """
    <style>
      body { background-color: #0E1117; color: #FFFFFF; }
      .stButton>button { background-color: #1F2A40; color: #FFFFFF; }
      .stCheckbox>div>label { color: #FFFFFF; }
      .stDataFrame th { color: #FFFFFF; }
      .stSelectbox>div { color: #FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------- UTILS ---------------------
def countdown_days(target_dt):
    delta = target_dt - datetime.now(TZ)
    return delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60

def current_week_number(now_dt):
    return ((now_dt - START_DATE).days) // 7 + 1

def current_phase_for_date(date_dt):
    weeks = ((date_dt - START_DATE).days) // 7
    idx = (weeks // 12) % 4
    return PHASES[idx]

def ensure_log(athlete):
    fp = os.path.join(DATA_DIR, f"{athlete}_log.csv")
    if not os.path.exists(fp):
        df = pd.DataFrame(columns=[
            "Date", "Phase", "Activity", "CompletedMeals", "Protein_g",
            "Carbs_g", "Fat_g", "Calories", "SleepHours", "Note"
        ])
        df.to_csv(fp, index=False)
    return fp

def load_log(athlete):
    fp = ensure_log(athlete)
    df = pd.read_csv(fp, parse_dates=["Date"]) if os.path.exists(fp) else pd.DataFrame()
    return df

def save_log(athlete, df):
    fp = ensure_log(athlete)
    df.to_csv(fp, index=False)

# --------------------- FOOD / MACROS DATABASE (ESTIMATES) ---------------------
# These are approximate macro estimates per serving for common Maharashtrian-style meals.
# Values = (protein_g, carbs_g, fat_g, calories)
FOOD_MACROS = {
    # breakfasts
    "Poha": (6, 40, 6, 240),
    "Upma": (6, 42, 7, 250),
    "Bhakri (jowar) + Egg": (12, 40, 12, 360),
    "Rotti/Chapati (1)": (3, 15, 1.5, 80),
    "Oats + Milk": (8, 30, 6, 220),

    # mid-morning/snacks
    "Fruits": (1, 20, 0.5, 90),
    "Nuts": (6, 8, 15, 180),
    "Sprouts": (8, 18, 2, 140),
    "Protein Shake": (20, 10, 2, 140),
    "Boiled Eggs (2)": (12, 1, 10, 150),

    # lunch/dinner veg
    "Rice + Dal + Veg": (10, 80, 6, 460),
    "Bhakri + Veg + Dal": (10, 50, 8, 380),
    "Roti + Paneer Curry": (18, 60, 20, 520),

    # non-veg options
    "Bhakri + Chicken Curry": (30, 45, 15, 520),
    "Rice + Mutton Curry": (35, 75, 25, 720),
    "Rice + Fish Curry": (28, 70, 18, 580),

    # evening
    "Buttermilk + Nuts": (6, 8, 10, 150),
    "Fruit Salad": (2, 25, 0.5, 110),

    # generic
    "Protein Bar": (15, 25, 8, 250),
}

# Meal pools reflecting Maharashtrian preferences, but rotated
# Each day's meal plan for an athlete will pick one option from each time slot,
# ensuring not to have chicken+mutton same day and not everyone gets non-veg daily.
MEAL_POOLS = {
    "breakfast": ["Poha", "Upma", "Bhakri (jowar) + Egg", "Oats + Milk"],
    "midmorning": ["Fruits", "Nuts", "Sprouts", "Protein Shake", "Boiled Eggs (2)"],
    "lunch": ["Rice + Dal + Veg", "Bhakri + Veg + Dal", "Roti + Paneer Curry", "Bhakri + Chicken Curry", "Rice + Fish Curry", "Rice + Mutton Curry"],
    "afternoon": ["Buttermilk + Nuts", "Fruit Salad", "Protein Bar", "Fruits"],
    "dinner": ["Roti + Paneer Curry", "Bhakri + Veg + Dal", "Rice + Chicken Curry", "Rice + Fish Curry"]
}

# For fish pairings, show suggestion
FISH_PAIRINGS = {
    "Rice + Fish Curry": "Steamed basmati rice / Jeera rice"
}

# --------------------- PROTEIN ROTATION RULES ---------------------
# We'll choose a protein type per athlete per day in cycle: veg, egg, fish, chicken, mutton
PROTEIN_CYCLE = ["veg", "egg", "fish", "chicken", "mutton"]

def pick_daily_meals(athlete, date_dt):
    """Return meals dict for the athlete for given date.
       Ensures not to have chicken+mutton same day and rotates proteins sensibly."""
    weekday = date_dt.weekday()
    # pick protein type using athlete index + day to vary across athletes/days
    idx = list(ATHLETES.keys()).index(athlete)
    cycle_choice = PROTEIN_CYCLE[(idx + weekday) % len(PROTEIN_CYCLE)]

    # helper to select meal from pool avoiding certain non-veg combinations
    def choose(pool, allow_nonveg=True):
        # prioritize veg if cycle_choice is veg; otherwise allow forms
        options = MEAL_POOLS[pool].copy()
        # remove mutton/chicken when not allowed
        if not allow_nonveg:
            options = [o for o in options if ("Chicken" not in o and "Mutton" not in o and "Fish" not in o)]
        # if cycle_choice forces a protein, try to include it
        if cycle_choice == "egg":
            # try to include egg at breakfast or midmorning
            egg_options = [o for o in options if "Egg" in o]
            if egg_options:
                return random.choice(egg_options)
        if cycle_choice == "fish":
            fish_options = [o for o in options if "Fish" in o]
            if fish_options:
                return random.choice(fish_options)
        if cycle_choice == "chicken":
            chicken_options = [o for o in options if "Chicken" in o]
            if chicken_options:
                return random.choice(chicken_options)
        if cycle_choice == "mutton":
            mutton_options = [o for o in options if "Mutton" in o]
            if mutton_options:
                return random.choice(mutton_options)
        # fallback: choose a veg-heavy or mixed option randomly but avoid mutton/chicken if another protein chosen
        filtered = options
        # ensure we don't include mutton if cycle_choice==chicken and vice versa
        if cycle_choice == "chicken":
            filtered = [o for o in filtered if "Mutton" not in o]
        if cycle_choice == "mutton":
            filtered = [o for o in filtered if "Chicken" not in o]
        if not filtered:
            filtered = options
        return random.choice(filtered)

    # build meals
    breakfast = choose("breakfast", allow_nonveg=True)
    mid = choose("midmorning", allow_nonveg=True)
    # For lunch/dinner we enforce the cycle: if cycle_choice is non-veg pick one non-veg, else veg
    if cycle_choice in ("chicken", "mutton", "fish"):
        # pick one non-veg for main meal, but not both chicken+mutton
        lunch = choose("lunch", allow_nonveg=True)
        # ensure lunch contains the chosen protein if possible
        if cycle_choice == "fish" and "Fish" not in lunch:
            lunch_candidates = [o for o in MEAL_POOLS["lunch"] if "Fish" in o]
            if lunch_candidates:
                lunch = random.choice(lunch_candidates)
    elif cycle_choice == "egg":
        # give egg at breakfast or mid (already handled), use veg options at lunch
        lunch = choose("lunch", allow_nonveg=False)
    else:
        lunch = choose("lunch", allow_nonveg=False)

    afternoon = choose("afternoon", allow_nonveg=False)
    # dinner: if lunch was non-veg, dinner should be veg or fish (avoid chicken + mutton same day)
    if any(x in lunch for x in ("Chicken","Mutton")):
        # pick veg dinner or fish only
        dinner_options = [o for o in MEAL_POOLS["dinner"] if ("Chicken" not in o and "Mutton" not in o)]
        if dinner_options:
            dinner = random.choice(dinner_options)
        else:
            dinner = random.choice(MEAL_POOLS["dinner"])
    else:
        dinner = choose("dinner", allow_nonveg=True)

    # ensure we haven't selected both chicken and mutton across lunch/dinner
    proteins = " ".join([breakfast, mid, lunch, afternoon, dinner])
    if "Chicken" in proteins and "Mutton" in proteins:
        # remove mutton from dinner if present
        if "Mutton" in dinner:
            dinner = choose("dinner", allow_nonveg=False)
        elif "Mutton" in lunch:
            lunch = choose("lunch", allow_nonveg=False)

    meals = {
        "07:30": breakfast,
        "10:30": mid,
        "13:30": lunch,
        "16:30": afternoon,
        "20:00": dinner
    }
    return meals

def macros_for_meals(meals):
    """Return total protein, carbs, fat, calories for a dict of meals."""
    p = c = f = cal = 0.0
    for m in meals.values():
        if m in FOOD_MACROS:
            mp, mc, mf, mcal = FOOD_MACROS[m]
        else:
            # fallback approximate
            mp, mc, mf, mcal = (8, 30, 8, 250)
        p += mp
        c += mc
        f += mf
        cal += mcal
    return round(p,1), round(c,1), round(f,1), round(cal,0)

# --------------------- SUNDAY & JOINT ACTIVITY ---------------------
SUNDAY_ACTIVITIES = [
    "Hike around Lonavala",
    "Plantation drive",
    "Beach cleanup at Alibaug",
    "Long drive to Mahabaleshwar",
    "Community cycling tour"
]

def sunday_suggestion(date_dt):
    # 1st Sunday of each month -> joint activity (predictable)
    if date_dt.weekday() != 6:
        return ""
    if 1 <= date_dt.day <= 7:
        return random.choice(SUNDAY_ACTIVITIES)
    return random.choice(["Rest / gentle walk", "Light yoga", "Easy family outing"])

# --------------------- APP UI ---------------------
# Sidebar
LOGO = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
st.sidebar.image(LOGO, use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown("---")
d_days, d_hours, d_mins = countdown_days(IRONMAN_DATE)
st.sidebar.markdown(f"**Countdown to Ironman Hamburg 2028:** {d_days} days, {d_hours}h")
st.sidebar.markdown("---")
quotes = [
    "Consistency beats intensity.",
    "Small steps every day.",
    "Ironman is built by habits."
]
st.sidebar.markdown(f"**Quote of the day:** {random.choice(quotes)}")
# Today's special only if exists
today_str = NOW.strftime("%d-%m")
if ATHLETES[athlete]["dob"] == today_str:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Today's Special:** 🎉 Happy Birthday {athlete}!")
else:
    # festival example
    if today_str in ("13-11",):  # note: add more if needed
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Today's Special:** Diwali")

# Greeting & header
hour = NOW.hour
greet = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
st.title(f"{greet}, {athlete}!")
st.markdown(f"**Date:** {NOW.strftime('%A, %d %B %Y')}")
st.markdown(f"**Week starting:** {(NOW - timedelta(days=NOW.weekday())).strftime('%d %b %Y')}")

# Persisted log for athlete
log_fp = ensure_log(athlete)
df_log = load_log(athlete)

# Tabs
tab_today, tab_next, tab_week, tab_progress, tab_nutrition, tab_team = st.tabs(
    ["Today's Plan", "Next Day Plan", "Weekly Plan", "Progress", "Nutrition & Sleep Tracker", "Team Overview"]
)

# ---------- TODAY'S PLAN ----------
with tab_today:
    st.header("Today's Plan")
    today = NOW.date()
    phase = current_phase_for_date(NOW)
    st.markdown(f"**Phase:** {phase}")

    # activities based on phase (simplified)
    if phase == "Base":
        run = f"{5 + 0.1*current_week_number(NOW):.1f} km"
        bike = "0 km (bike later)"
        swim = "0 m (swim later)"
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

    c1, c2, c3 = st.columns(3)
    done_run = c1.checkbox(f"Run: {run}", key=f"run_{athlete}_{today}")
    done_bike = c2.checkbox(f"Bike: {bike}", key=f"bike_{athlete}_{today}")
    done_swim = c3.checkbox(f"Swim: {swim}", key=f"swim_{athlete}_{today}")

    # Nutrition plan (daily, rotated)
    meals = pick_daily_meals(athlete, NOW)
    st.subheader("Nutrition (Maharashtrian-style, rotated per athlete/day)")
    meal_checks = {}
    cols = st.columns(5)
    for i,(time,label) in enumerate(meals.items()):
        meal_checks[time] = cols[i].checkbox(f"{time}\n{label}", key=f"{athlete}_meal_{time}_{today}")

    # Show estimated macros for the planned meals (sum of all meals)
    prot, carbs, fat, kcal = macros_for_meals(meals)
    st.markdown(f"**Planned macros (total for day):** Protein {prot} g • Carbs {carbs} g • Fat {fat} g • Calories {kcal} kcal")

    # Sleep input
    sleep = st.number_input("Planned / Actual sleep hours (tonight / last night)", min_value=0.0, max_value=12.0, value=7.0, step=0.5, key=f"sleep_{athlete}_{today}")

    # Notes
    note = st.text_area("Notes / Tip", placeholder="How did training feel? Any nutrition issues?")

    # Sunday suggestion
    sunday_sugg = sunday_suggestion(NOW)
    if sunday_sugg:
        st.info(f"Sunday suggestion: {sunday_sugg}")

    # Save log button
    if st.button("Save today's nutrition & sleep and activity status"):
        # determine which meals were eaten
        eaten = ",".join([meals[t] for t,v in meal_checks.items() if v])
        # macros of eaten meals only
        eaten_meals = {t:meals[t] for t,v in meal_checks.items() if v}
        p_e, c_e, f_e, cal_e = macros_for_meals(eaten_meals) if eaten_meals else (0,0,0,0)
        entry = {
            "Date": pd.to_datetime(today),
            "Phase": phase,
            "Activity": ",".join([k for k,v in [("Run",done_run),("Bike",done_bike),("Swim",done_swim)] if v]),
            "CompletedMeals": eaten,
            "Protein_g": p_e,
            "Carbs_g": c_e,
            "Fat_g": f_e,
            "Calories": cal_e,
            "SleepHours": sleep,
            "Note": note
        }
        # append to df_log and save
        df_log = df_log[df_log["Date"] != pd.to_datetime(today)]
        df_log = pd.concat([df_log, pd.DataFrame([entry])], ignore_index=True)
        save_log(athlete, df_log)
        st.success("Saved today's log.")

# ---------- NEXT DAY PLAN ----------
with tab_next:
    st.header("Next Day Plan")
    nd = NOW + timedelta(days=1)
    st.markdown(f"**Date:** {nd.strftime('%A, %d %b %Y')}")
    phase_nd = current_phase_for_date(nd)
    st.markdown(f"**Phase:** {phase_nd}")
    # show plan (activities minimal version)
    if phase_nd == "Base":
        st.write("Run + Strength")
    elif phase_nd == "Build":
        st.write("Run + Bike + Strength (introduce/expand swim if applicable)")
    elif phase_nd == "Peak":
        st.write("Long Run + Long Bike + Swim + Brick session")
    else:
        st.write("Taper – light sessions, focus on recovery")
    # show nutrition for next day rotated
    next_meals = pick_daily_meals(athlete, nd)
    st.subheader("Nutrition (next day)")
    for t,m in next_meals.items():
        pairing = FISH_PAIRINGS.get(m, "")
        line = f"{t} - {m}"
        if pairing:
            line += f"  (pair with: {pairing})"
        st.write(line)

    # If next day is Sunday, show monthly joint suggestion
    if nd.weekday() == 6:
        st.subheader("Sunday / Joint activity")
        # first Sunday of month -> joint; else optional
        if 1 <= nd.day <= 7:
            st.info("Monthly joint activity suggestion: " + random.choice(SUNDAY_ACTIVITIES))
        else:
            st.info("This Sunday: " + sunday_suggestion(nd))

# ---------- WEEKLY PLAN ----------
with tab_week:
    st.header("Weekly Plan (Mon → Sun)")
    week_start = NOW - timedelta(days=NOW.weekday())
    table_rows = []
    for d in [week_start + timedelta(days=i) for i in range(7)]:
        mealsd = pick_daily_meals(athlete, d)
        run_km_str = ("Run: " + (f"{5 + 0.1*current_week_number(NOW):.1f} km" if current_phase_for_date(d)=="Base"
                      else f"{10 + 0.2*current_week_number(NOW):.1f} km"))
        table_rows.append({
            "Day": d.strftime("%A"),
            "ActivitySummary": run_km_str,
            "MealsSample": ", ".join([mealsd["07:30"], mealsd["13:30"]]),
            "SundayActivity": sunday_suggestion(d) if d.weekday()==6 else ""
        })
    st.dataframe(pd.DataFrame(table_rows)[["Day","ActivitySummary","MealsSample","SundayActivity"]])

# ---------- PROGRESS TAB ----------
with tab_progress:
    st.header("Progress — weekly / monthly overview")
    if not df_log.empty:
        # show weekly sums for last 12 weeks for calories & protein
        df_log2 = df_log.copy()
        df_log2["Date"] = pd.to_datetime(df_log2["Date"])
        df_log2 = df_log2.sort_values("Date")
        # aggregate last 12 weeks
        last_date = pd.to_datetime(NOW.date())
        start_12w = last_date - pd.Timedelta(weeks=12)
        df_recent = df_log2[df_log2["Date"] >= start_12w]
        if not df_recent.empty:
            # weekly resample
            df_recent = df_recent.set_index("Date")
            weekly = df_recent.resample("W").sum()[["Protein_g","Calories"]].fillna(0)
            weekly = weekly.reset_index()
            fig = px.bar(weekly, x="Date", y=["Protein_g","Calories"], title="Weekly Protein & Calories (last 12 weeks)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No logs yet to show progress. Start logging daily nutrition & sleep.")
    else:
        st.info("No logs yet — start saving today's log to populate progress charts.")

# ---------- NUTRITION & SLEEP TRACKER ----------
with tab_nutrition:
    st.header("Nutrition & Sleep Tracker")
    st.write("This tab shows your logged daily macros and sleep. Use it to monitor adherence to recommended protein/carbs/fat for endurance training.")
    df_log_view = df_log.copy()
    if df_log_view.empty:
        st.info("No nutrition logs yet. Save today's log to view here.")
    else:
        # show last 30 entries summarized
        df_view = df_log_view.sort_values("Date", ascending=False).head(30)
        # keep only essential columns
        show_df = df_view[["Date","Protein_g","Carbs_g","Fat_g","Calories","SleepHours","CompletedMeals"]].copy()
        st.dataframe(show_df)

        # show averages
        avg_protein = show_df["Protein_g"].mean()
        avg_cal = show_df["Calories"].mean()
        st.markdown(f"**Average (last {len(show_df)} days)** — Protein: {avg_protein:.1f} g • Calories: {avg_cal:.0f} kcal")

# ---------- TEAM OVERVIEW ----------
with tab_team:
    st.header("Team Overview")
    # Build short summary table (only necessary columns)
    team_summary = []
    for a in ATHLETES.keys():
        fp = os.path.join(DATA_DIR, f"{a}_log.csv")
        if os.path.exists(fp):
            dfa = pd.read_csv(fp, parse_dates=["Date"])
            if not dfa.empty:
                recent = dfa.tail(14)  # last two weeks
                total_prot = recent["Protein_g"].sum()
                total_cal = recent["Calories"].sum()
                avg_sleep = recent["SleepHours"].mean() if "SleepHours" in recent.columns else np.nan
                team_summary.append({"Athlete": a, "Protein_14d_g": round(total_prot,1), "Calories_14d": int(total_cal), "AvgSleep_h": round(avg_sleep,1)})
            else:
                team_summary.append({"Athlete": a, "Protein_14d_g": 0, "Calories_14d": 0, "AvgSleep_h": 0})
        else:
            team_summary.append({"Athlete": a, "Protein_14d_g": 0, "Calories_14d": 0, "AvgSleep_h": 0})
    summary_df = pd.DataFrame(team_summary)
    st.dataframe(summary_df[["Athlete","Protein_14d_g","Calories_14d","AvgSleep_h"]])

    # Plots
    if not summary_df.empty:
        figp = px.bar(summary_df, x="Athlete", y="Protein_14d_g", title="Protein intake last 14 days (g)")
        figc = px.bar(summary_df, x="Athlete", y="Calories_14d", title="Calories last 14 days")
        st.plotly_chart(figp, use_container_width=True)
        st.plotly_chart(figc, use_container_width=True)

# --------------------- END ---------------------
st.markdown("---")
st.markdown("**Notes:**\n- Meals are sample/rotated suggestions and macros are approximate estimates.\n- You can edit `FOOD_MACROS` if you want different macro estimates.\n- All dates & times use Indian Standard Time (Asia/Kolkata).")
