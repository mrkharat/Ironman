# ironman_app_final.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import os
import random
import plotly.express as px

# -------------------- CONFIG --------------------
APP_TITLE = "Ironman Hamburg 2028 — Coach"
DATA_DIR = "athlete_data"
TARGETS_FILE = os.path.join(DATA_DIR, "athlete_targets.csv")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# -------------------- TIME / CONSTANTS --------------------
TZ = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(TZ)
START_DATE = TZ.localize(datetime(2025, 10, 1, 0, 0, 0))
IRONMAN_DATE = TZ.localize(datetime(2028, 7, 14, 6, 0, 0))

ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "dob": "25-12"},
    "Sudeep": {"gender": "M", "weight": 73, "dob": "31-10"},
    "Vaishali": {"gender": "F", "weight": 64, "dob": "02-04"}
}

PHASES = ["Base", "Build", "Peak", "Taper"]

# -------------------- THEME & MOBILE CSS --------------------
st.markdown(
    """
    <style>
      /* Mobile-friendly */
      @media (max-width: 768px) {
         .block-container { padding: 0.6rem 0.6rem; }
         h1 { font-size: 1.1rem; }
      }
      body { background-color: #0E1117; color: #FFFFFF; }
      .stButton>button { background-color: #1F2A40; color: #FFFFFF; border-radius:8px; }
      .stMetric > div { color: #FFFFFF; }
      .stCheckbox>div>label { color: #FFFFFF; }
      .stDataFrame th { color: #FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- FOOD / MEALS (Maharashtrian rotated) --------------------
FOOD_MACROS = {
    "Poha": (6, 40, 6, 240),
    "Upma": (6, 42, 7, 250),
    "Bhakri (jowar) + Egg": (12, 40, 12, 360),
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
    "Chapati (2) + Veg": (8, 40, 6, 320)
}

MEAL_POOLS = {
    "breakfast": ["Poha", "Upma", "Bhakri (jowar) + Egg", "Oats + Milk"],
    "midmorning": ["Fruits", "Nuts", "Sprouts", "Protein Shake", "Boiled Eggs (2)"],
    "lunch": ["Rice + Dal + Veg", "Bhakri + Veg + Dal", "Roti + Paneer Curry", "Bhakri + Chicken Curry", "Rice + Fish Curry", "Rice + Mutton Curry"],
    "afternoon": ["Buttermilk + Nuts", "Fruit Salad", "Protein Bar", "Fruits"],
    "dinner": ["Roti + Paneer Curry", "Bhakri + Veg + Dal", "Rice + Chicken Curry", "Rice + Fish Curry", "Chapati (2) + Veg"]
}

PROTEIN_CYCLE = ["veg", "egg", "fish", "chicken", "mutton"]

SUNDAY_ACTIVITIES = [
    "Hike in Lonavala/Mahabaleshwar",
    "Group cycling to Lonavala",
    "Beach run",
    "Yoga & meditation",
    "Plantation drive"
]

FESTIVALS = {
    "01-01":"New Year",
    "26-01":"Republic Day",
    "15-08":"Independence Day",
    "02-10":"Gandhi Jayanti",
    "25-12":"Christmas",
    "13-11":"Diwali"
}

# -------------------- LOG / TARGET UTILITIES --------------------
LOG_COLS = ["Date","Phase","Activity","CompletedMeals","Protein_g","Carbs_g","Fat_g","Calories","SleepHours","Note"]

def ensure_log_file(ath):
    fp = os.path.join(DATA_DIR, f"{ath}_log.csv")
    if not os.path.exists(fp):
        pd.DataFrame(columns=LOG_COLS).to_csv(fp, index=False)
    return fp

def load_log(ath):
    fp = ensure_log_file(ath)
    try:
        df = pd.read_csv(fp, parse_dates=["Date"])
    except Exception:
        df = pd.DataFrame(columns=LOG_COLS)
    for c in LOG_COLS:
        if c not in df.columns:
            df[c] = np.nan
    for c in ["Protein_g","Carbs_g","Fat_g","Calories","SleepHours"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

def save_log(ath, df):
    fp = ensure_log_file(ath)
    df2 = df.copy()
    if "Date" in df2.columns:
        df2["Date"] = pd.to_datetime(df2["Date"]).dt.date
    df2.to_csv(fp, index=False)

# targets persistence
def load_targets():
    if not os.path.exists(TARGETS_FILE):
        # defaults
        rows = []
        for a in ATHLETES.keys():
            rows.append({"Athlete": a, "Protein_g": 120, "Carbs_g": 350, "Fat_g": 70, "Calories": 2600, "SleepHours": 7.0})
        pd.DataFrame(rows).to_csv(TARGETS_FILE, index=False)
    df = pd.read_csv(TARGETS_FILE)
    return {r["Athlete"]: {"Protein_g": r["Protein_g"], "Carbs_g": r["Carbs_g"], "Fat_g": r["Fat_g"], "Calories": r["Calories"], "SleepHours": r["SleepHours"]} for _, r in df.iterrows()}

def save_targets(targets_dict):
    df = pd.DataFrame([{"Athlete": a, **targets_dict[a]} for a in targets_dict.keys()])
    df.to_csv(TARGETS_FILE, index=False)

# -------------------- MEAL PICKER / MACROS --------------------
def pick_daily_meals(athlete, date_dt):
    weekday = date_dt.weekday()
    idx = list(ATHLETES.keys()).index(athlete)
    choice = PROTEIN_CYCLE[(idx + weekday) % len(PROTEIN_CYCLE)]
    def choose(slot, allow_nonveg=True):
        opts = MEAL_POOLS[slot].copy()
        if not allow_nonveg:
            opts = [o for o in opts if ("Chicken" not in o and "Mutton" not in o and "Fish" not in o)]
        # prioritize protein choice
        if choice == "egg":
            egg = [o for o in opts if "Egg" in o]
            if egg: return random.choice(egg)
        if choice == "fish":
            fish = [o for o in opts if "Fish" in o]
            if fish: return random.choice(fish)
        if choice == "chicken":
            ck = [o for o in opts if "Chicken" in o]
            if ck: return random.choice(ck)
        if choice == "mutton":
            mt = [o for o in opts if "Mutton" in o]
            if mt: return random.choice(mt)
        filt = opts
        if choice == "chicken":
            filt = [o for o in filt if "Mutton" not in o]
        if choice == "mutton":
            filt = [o for o in filt if "Chicken" not in o]
        if not filt: filt = opts
        return random.choice(filt)
    breakfast = choose("breakfast", allow_nonveg=True)
    mid = choose("midmorning", allow_nonveg=True)
    if choice in ("chicken","mutton","fish"):
        lunch = choose("lunch", allow_nonveg=True)
    elif choice == "egg":
        lunch = choose("lunch", allow_nonveg=False)
    else:
        lunch = choose("lunch", allow_nonveg=False)
    afternoon = choose("afternoon", allow_nonveg=False)
    if any(x in lunch for x in ("Chicken","Mutton")):
        dinner_opts = [o for o in MEAL_POOLS["dinner"] if ("Chicken" not in o and "Mutton" not in o)]
        dinner = random.choice(dinner_opts) if dinner_opts else random.choice(MEAL_POOLS["dinner"])
    else:
        dinner = choose("dinner", allow_nonveg=True)
    # avoid both chicken + mutton
    proteins = " ".join([breakfast, mid, lunch, afternoon, dinner])
    if "Chicken" in proteins and "Mutton" in proteins:
        if "Mutton" in dinner:
            dinner = choose("dinner", allow_nonveg=False)
        elif "Mutton" in lunch:
            lunch = choose("lunch", allow_nonveg=False)
    return {"07:30": breakfast, "10:30": mid, "13:30": lunch, "16:30": afternoon, "20:00": dinner}

def macros_for_meals(meals):
    p=c=f=cal=0.0
    for m in meals.values():
        if m in FOOD_MACROS:
            mp, mc, mf, mcal = FOOD_MACROS[m]
        else:
            mp, mc, mf, mcal = (8, 30, 8, 250)
        p += mp; c += mc; f += mf; cal += mcal
    return round(p,1), round(c,1), round(f,1), int(round(cal,0))

# -------------------- TRAINING PHASE --------------------
def current_phase(date_dt):
    weeks = ((date_dt - START_DATE).days)//7
    idx = (weeks // 12) % len(PHASES)
    return PHASES[idx]

# -------------------- UI SIDEBAR --------------------
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
st.sidebar.image(LOGO_URL, use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.markdown("---")
delta = IRONMAN_DATE - NOW
st.sidebar.subheader("Countdown to Ironman Hamburg 2028")
st.sidebar.write(f"{delta.days} days, {delta.seconds//3600}h")
st.sidebar.markdown("---")
st.sidebar.subheader("Quote of the day")
st.sidebar.write(random.choice([
    "Consistency beats intensity.",
    "Small steps progress to big wins.",
    "Sleep is part of training."
]))
# Today's special
today_str = NOW.strftime("%d-%m")
if today_str in FESTIVALS:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(FESTIVALS[today_str])
elif ATHLETES[athlete]["dob"] == today_str:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(f"Happy Birthday, {athlete}!")

# -------------------- LOAD LOGS & TARGETS --------------------
df_log = load_log(athlete)
targets = load_targets()

# -------------------- TABS --------------------
tabs = st.tabs(["Today's Plan", "Next Day Plan", "Weekly Plan", "Progress Tracker", "Team Overview"])

# -------------------- TODAY'S PLAN --------------------
with tabs[0]:
    st.header("Today's Plan")
    phase = current_phase(NOW)
    st.markdown(f"**Phase:** {phase}")

    # activity suggestions
    if phase == "Base":
        run_s = f"{5 + 0.1* ((NOW-START_DATE).days//7):.1f} km"
        bike_s = "Short / technical rides"
        swim_s = "Technique drills"
    elif phase == "Build":
        run_s = f"{10 + 0.2* ((NOW-START_DATE).days//7):.1f} km"
        bike_s = "20-60 km progressive"
        swim_s = "200-1000 m"
    elif phase == "Peak":
        run_s = f"{15 + 0.2* ((NOW-START_DATE).days//7):.1f} km"
        bike_s = "Long rides 60-150 km"
        swim_s = "1500-3000 m"
    else:
        run_s = "Short easy run"
        bike_s = "Short easy ride"
        swim_s = "Short easy swim"

    col1, col2, col3 = st.columns(3)
    r_done = col1.checkbox(f"Run: {run_s}", key=f"run_{athlete}_{NOW.date()}")
    b_done = col2.checkbox(f"Bike: {bike_s}", key=f"bike_{athlete}_{NOW.date()}")
    s_done = col3.checkbox(f"Swim: {swim_s}", key=f"swim_{athlete}_{NOW.date()}")

    # meals & macros
    meals = pick_daily_meals(athlete, NOW)
    st.subheader("Nutrition — sample Maharashtrian meals (rotated)")
    meal_checks = {}
    cols = st.columns(5)
    i = 0
    for t, m in meals.items():
        meal_checks[t] = cols[i].checkbox(f"{t}\n{m}", key=f"{athlete}_meal_{t}_{NOW.date()}")
        i += 1

    p_plan, c_plan, f_plan, kcal_plan = macros_for_meals(meals)
    st.markdown(f"**Planned daily macros:** Protein {p_plan} g • Carbs {c_plan} g • Fat {f_plan} g • Calories {kcal_plan} kcal")

    sleep = st.number_input("Sleep hours (last night / planned)", min_value=0.0, max_value=12.0, value=7.0, step=0.5, key=f"sleep_{athlete}_{NOW.date()}")

    sunday_msg = ""
    if NOW.weekday() == 6:
        sunday_msg = random.choice(SUNDAY_ACTIVITIES)
        st.info(f"Sunday suggestion: {sunday_msg}")

    # Save today's log
    if st.button("Save today's entry"):
        eaten = {t: meals[t] for t, v in meal_checks.items() if v}
        p_e, c_e, f_e, kcal_e = macros_for_meals(eaten) if eaten else (0,0,0,0)
        activity_list = []
        if r_done: activity_list.append("Run")
        if b_done: activity_list.append("Bike")
        if s_done: activity_list.append("Swim")
        entry = {
            "Date": pd.to_datetime(NOW.date()),
            "Phase": phase,
            "Activity": ",".join(activity_list),
            "CompletedMeals": ",".join(eaten.values()),
            "Protein_g": p_e,
            "Carbs_g": c_e,
            "Fat_g": f_e,
            "Calories": kcal_e,
            "SleepHours": sleep,
            "Note": ""
        }
        df_log = df_log[df_log["Date"] != pd.to_datetime(NOW.date())]
        df_log = pd.concat([df_log, pd.DataFrame([entry])], ignore_index=True)
        save_log(athlete, df_log)
        st.success("Today's entry saved.")

# -------------------- NEXT DAY PLAN --------------------
with tabs[1]:
    st.header("Next Day Plan")
    nd = NOW + timedelta(days=1)
    st.write(f"Date: {nd.strftime('%A, %d %B %Y')}")
    phase_nd = current_phase(nd)
    st.write(f"Phase: {phase_nd}")
    if nd.weekday() == 6:
        st.info("Next day is Sunday — suggested joint activity:")
        st.write(random.choice(SUNDAY_ACTIVITIES))
    else:
        if phase_nd == "Base":
            st.write("Run + Strength")
        elif phase_nd == "Build":
            st.write("Run + Bike + Technique swim")
        elif phase_nd == "Peak":
            st.write("Long Run + Long Bike + Swim")
        else:
            st.write("Taper — easy & recovery")
    next_meals = pick_daily_meals(athlete, nd)
    st.subheader("Next day meals (sample)")
    for t,m in next_meals.items():
        st.write(f"{t} - {m}")

# -------------------- WEEKLY PLAN --------------------
with tabs[2]:
    st.header("Weekly Plan (Mon → Sun)")
    ws = NOW - timedelta(days=NOW.weekday())
    rows = []
    for i in range(7):
        d = ws + timedelta(days=i)
        mealsd = pick_daily_meals(athlete, d)
        rows.append({
            "Day": d.strftime("%A"),
            "Activity": ("Run" if current_phase(d)=="Base" else "Run/Bike/Swim" if current_phase(d) in ("Build","Peak") else "Light"),
            "MealsSample": f"{mealsd['07:30']} | {mealsd['13:30']}",
            "SundayActivity": random.choice(SUNDAY_ACTIVITIES) if d.weekday()==6 else ""
        })
    st.dataframe(pd.DataFrame(rows)[["Day","Activity","MealsSample","SundayActivity"]])

# -------------------- PROGRESS TRACKER (MERGED) --------------------
with tabs[3]:
    st.header("Progress Tracker — Activity, Nutrition & Sleep")

    # Show / edit per-athlete targets
    st.subheader("Targets (per day)")
    if athlete not in targets:
        targets[athlete] = {"Protein_g":120, "Carbs_g":350, "Fat_g":70, "Calories":2600, "SleepHours":7.0}
    t = targets[athlete]
    colp, colc, colf, colcal, cols = st.columns(5)
    p_t = colp.number_input("Protein (g/day)", 40, 400, int(t["Protein_g"]), step=1, key=f"prot_target_{athlete}")
    c_t = colc.number_input("Carbs (g/day)", 100, 800, int(t["Carbs_g"]), step=5, key=f"carb_target_{athlete}")
    f_t = colf.number_input("Fat (g/day)", 10, 200, int(t["Fat_g"]), step=1, key=f"fat_target_{athlete}")
    cal_t = colcal.number_input("Calories (kcal/day)", 1000, 6000, int(t["Calories"]), step=50, key=f"cal_target_{athlete}")
    s_t = cols.number_input("Sleep (hrs/day)", 4.0, 12.0, float(t["SleepHours"]), step=0.5, key=f"sleep_target_{athlete}")

    if st.button("Save targets"):
        targets[athlete] = {"Protein_g": p_t, "Carbs_g": c_t, "Fat_g": f_t, "Calories": cal_t, "SleepHours": s_t}
        save_targets(targets)
        st.success("Targets saved.")

    # show latest log and color-coded alerts
    st.subheader("Latest log vs targets")
    if df_log.empty:
        st.info("No logs yet — save today's entry in Today's Plan tab.")
    else:
        latest = df_log.sort_values("Date").iloc[-1]
        # display metrics for Protein, Calories, Sleep
        prot_val = latest.get("Protein_g", 0)
        cal_val = latest.get("Calories", 0)
        sleep_val = latest.get("SleepHours", 0)
        # color-coded logic
        def color_status(val, target):
            if val >= target:
                return "good"
            elif val >= 0.85 * target:
                return "warn"
            else:
                return "bad"
        st.write("**Protein**")
        status_p = color_status(prot_val, targets[athlete]["Protein_g"])
        if status_p == "good":
            st.metric("Protein (g)", f"{prot_val}", f"Target {targets[athlete]['Protein_g']}", delta_color="normal")
        elif status_p == "warn":
            st.warning(f"Protein slightly below target: {prot_val} g (target {targets[athlete]['Protein_g']} g)")
        else:
            st.error(f"Protein well below target: {prot_val} g (target {targets[athlete]['Protein_g']} g)")

        st.write("**Calories**")
        status_c = color_status(cal_val, targets[athlete]["Calories"])
        if status_c == "good":
            st.metric("Calories (kcal)", f"{cal_val}", f"Target {targets[athlete]['Calories']}", delta_color="normal")
        elif status_c == "warn":
            st.warning(f"Calories slightly below target: {cal_val} kcal (target {targets[athlete]['Calories']} kcal)")
        else:
            st.error(f"Calories well below target: {cal_val} kcal (target {targets[athlete]['Calories']} kcal)")

        st.write("**Sleep**")
        status_s = color_status(sleep_val, targets[athlete]["SleepHours"])
        if status_s == "good":
            st.metric("Sleep (hrs)", f"{sleep_val}", f"Target {targets[athlete]['SleepHours']}", delta_color="normal")
        elif status_s == "warn":
            st.warning(f"Sleep slightly below target: {sleep_val} h (target {targets[athlete]['SleepHours']} h)")
        else:
            st.error(f"Sleep well below target: {sleep_val} h (target {targets[athlete]['SleepHours']} h)")

        # Activity trends charts
        st.subheader("Activity trends (last 30 entries)")
        df_recent = df_log.sort_values("Date").tail(30)
        if not df_recent.empty:
            activity_chart_df = df_recent.set_index("Date")[["Run_km","Bike_km","Swim_m"]].fillna(0)
            st.plotly_chart(px.line(activity_chart_df, title="Run / Bike / Swim (last entries)"), use_container_width=True)
            nut_chart_df = df_recent.set_index("Date")[["Protein_g","Carbs_g","Fat_g","Calories","SleepHours"]].fillna(0)
            st.plotly_chart(px.line(nut_chart_df, title="Protein / Carbs / Fat / Calories / Sleep (last entries)"), use_container_width=True)

# -------------------- TEAM OVERVIEW --------------------
with tabs[4]:
    st.header("Team Overview — Activity & Nutrition")
    # build summary table for last 14 days
    team_rows = []
    for a in ATHLETES.keys():
        df_a = load_log(a)
        if df_a.empty:
            team_rows.append({"Athlete": a, "Protein_14d": 0, "Calories_14d": 0, "Sleep_avg_14d": 0.0})
            continue
        df_a["Date"] = pd.to_datetime(df_a["Date"])
        recent = df_a[df_a["Date"] >= (pd.to_datetime(NOW.date()) - pd.Timedelta(days=14))]
        prot_sum = recent["Protein_g"].sum() if "Protein_g" in recent.columns else 0
        cal_sum = recent["Calories"].sum() if "Calories" in recent.columns else 0
        sleep_avg = recent["SleepHours"].mean() if "SleepHours" in recent.columns and len(recent)>0 else 0
        team_rows.append({"Athlete": a, "Protein_14d": round(prot_sum,1), "Calories_14d": int(cal_sum), "Sleep_avg_14d": round(float(sleep_avg),1)})
    team_df = pd.DataFrame(team_rows)
    st.dataframe(team_df[["Athlete","Protein_14d","Calories_14d","Sleep_avg_14d"]])

    # visuals
    if not team_df.empty:
        st.plotly_chart(px.bar(team_df, x="Athlete", y="Protein_14d", title="Protein — last 14 days (g)"), use_container_width=True)
        st.plotly_chart(px.bar(team_df, x="Athlete", y="Calories_14d", title="Calories — last 14 days (kcal)"), use_container_width=True)

    # readiness heuristic (simple)
    st.subheader("On-track heuristic for Ironman Hamburg 2028")
    readiness = []
    for a in ATHLETES.keys():
        df_a = load_log(a)
        if df_a.empty:
            readiness.append({"Athlete": a, "Score": 0})
            continue
        df_a["Date"] = pd.to_datetime(df_a["Date"])
        recent28 = df_a[df_a["Date"] >= (pd.to_datetime(NOW.date()) - pd.Timedelta(days=28))]
        prot = recent28["Protein_g"].sum() if "Protein_g" in recent28.columns else 0
        cal = recent28["Calories"].sum() if "Calories" in recent28.columns else 0
        days_logged = recent28.shape[0]
        targ = targets.get(a, {"Protein_g": 120, "Calories": 2600})
        prot_target_28 = targ["Protein_g"] * 28
        cal_target_28 = targ["Calories"] * 28
        s1 = min(prot / max(1, prot_target_28), 1.0)
        s2 = min(cal / max(1, cal_target_28), 1.0)
        s3 = min(days_logged / 28.0, 1.0)
        score = (0.5 * s1) + (0.3 * s2) + (0.2 * s3)
        readiness.append({"Athlete": a, "Score": round(score*100,1)})
    rd_df = pd.DataFrame(readiness).sort_values("Score", ascending=False)
    st.dataframe(rd_df)

    st.markdown("**Interpretation:** The readiness score is a simple heuristic combining recent protein adherence, calories and consistency (0–100). Aim for >70 as a practical target — this is a guide, not a full training load model.")

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown("App optimized for mobile and desktop. Meals are sample/rotated Maharashtrian-style and macros are approximate. Adjust targets per athlete for personalized tracking.")
