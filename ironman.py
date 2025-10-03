# ironman_app_full.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import os
import random
import plotly.express as px

# ---------------------- CONFIG ----------------------
APP_TITLE = "Ironman Hamburg 2028 — Trainer (Maharashtra)"
DATA_DIR = "athlete_data"
os.makedirs(DATA_DIR, exist_ok=True)
st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")

# ---------------------- TIME / CONSTANTS ----------------------
TZ = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(TZ)
START_DATE = TZ.localize(datetime(2025, 10, 1, 0, 0, 0))
IRONMAN_DATE = TZ.localize(datetime(2028, 7, 14, 6, 0, 0))  # target event

ATHLETES = {
    "Mayur": {"gender": "M", "weight": 62, "dob": "25-12"},
    "Sudeep": {"gender": "M", "weight": 73, "dob": "31-10"},
    "Vaishali": {"gender": "F", "weight": 64, "dob": "02-04"}
}

PHASES = ["Base", "Build", "Peak", "Taper"]

# ---------------------- THEME ----------------------
st.markdown("""
<style>
body { background-color: #0E1117; color: #FFFFFF; }
.stButton>button { background-color: #1F2A40; color: #FFFFFF; border-radius:6px;}
.stCheckbox>div>label, .stText { color: #FFFFFF; }
.stDataFrame th { color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ---------------------- MEALS & MACROS ----------------------
# Approx macro database (per serving)
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
    "Hike in Western Ghats",
    "Plantation drive",
    "Beach cleanup at Alibaug",
    "Long drive to Mahabaleshwar",
    "Community cycling tour"
]

FESTIVALS = {
    "01-01":"New Year",
    "26-01":"Republic Day",
    "15-08":"Independence Day",
    "02-10":"Gandhi Jayanti",
    "25-12":"Christmas",
    "13-11":"Diwali"
}

LOG_REQUIRED_COLS = [
    "Date","Phase","Activity","CompletedMeals","Protein_g","Carbs_g","Fat_g","Calories","SleepHours","Note"
]

# ---------------------- HELPERS ----------------------
def ensure_log_file(athlete):
    fp = os.path.join(DATA_DIR, f"{athlete}_log.csv")
    if not os.path.exists(fp):
        pd.DataFrame(columns=LOG_REQUIRED_COLS).to_csv(fp, index=False)
    return fp

def load_log(athlete):
    fp = ensure_log_file(athlete)
    try:
        df = pd.read_csv(fp, parse_dates=["Date"])
    except Exception:
        df = pd.DataFrame(columns=LOG_REQUIRED_COLS)
    # ensure columns exist
    for c in LOG_REQUIRED_COLS:
        if c not in df.columns:
            df[c] = np.nan
    # coerce numeric
    for c in ["Protein_g","Carbs_g","Fat_g","Calories","SleepHours"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

def save_log(athlete, df):
    fp = ensure_log_file(athlete)
    df2 = df.copy()
    if "Date" in df2.columns:
        # store ISO date (date only)
        df2["Date"] = pd.to_datetime(df2["Date"]).dt.date
    df2.to_csv(fp, index=False)

def macros_for_meals(meals_dict):
    p=c=f=cal=0.0
    for m in meals_dict.values():
        if m in FOOD_MACROS:
            mp, mc, mf, mcal = FOOD_MACROS[m]
        else:
            mp, mc, mf, mcal = (8,30,8,250)
        p += mp; c += mc; f += mf; cal += mcal
    return round(p,1), round(c,1), round(f,1), int(round(cal,0))

def pick_daily_meals(athlete, date_dt):
    weekday = date_dt.weekday()
    idx = list(ATHLETES.keys()).index(athlete)
    protein_choice = PROTEIN_CYCLE[(idx + weekday) % len(PROTEIN_CYCLE)]
    def choose(slot, allow_nonveg=True):
        opts = MEAL_POOLS[slot].copy()
        if not allow_nonveg:
            opts = [o for o in opts if ("Chicken" not in o and "Mutton" not in o and "Fish" not in o)]
        # try to pick preferred protein
        if protein_choice=="egg":
            egg = [o for o in opts if "Egg" in o]
            if egg: return random.choice(egg)
        if protein_choice=="fish":
            fish = [o for o in opts if "Fish" in o]
            if fish: return random.choice(fish)
        if protein_choice=="chicken":
            ck = [o for o in opts if "Chicken" in o]
            if ck: return random.choice(ck)
        if protein_choice=="mutton":
            mt = [o for o in opts if "Mutton" in o]
            if mt: return random.choice(mt)
        # fallback
        filt = opts
        if protein_choice=="chicken":
            filt = [o for o in filt if "Mutton" not in o]
        if protein_choice=="mutton":
            filt = [o for o in filt if "Chicken" not in o]
        if not filt: filt = opts
        return random.choice(filt)
    breakfast = choose("breakfast", allow_nonveg=True)
    mid = choose("midmorning", allow_nonveg=True)
    if protein_choice in ("chicken","mutton","fish"):
        lunch = choose("lunch", allow_nonveg=True)
        # try ensure the chosen protein appears
        if protein_choice=="fish" and "Fish" not in lunch:
            fish_opts = [o for o in MEAL_POOLS["lunch"] if "Fish" in o]
            if fish_opts: lunch = random.choice(fish_opts)
    elif protein_choice=="egg":
        lunch = choose("lunch", allow_nonveg=False)
    else:
        lunch = choose("lunch", allow_nonveg=False)
    afternoon = choose("afternoon", allow_nonveg=False)
    # dinner rule: avoid chicken+mutton same day
    if any(x in lunch for x in ("Chicken","Mutton")):
        dinner_opts = [o for o in MEAL_POOLS["dinner"] if ("Chicken" not in o and "Mutton" not in o)]
        dinner = random.choice(dinner_opts) if dinner_opts else random.choice(MEAL_POOLS["dinner"])
    else:
        dinner = choose("dinner", allow_nonveg=True)
    # final safety: if both chicken and mutton exist, remove mutton if possible
    proteins = " ".join([breakfast, mid, lunch, afternoon, dinner])
    if "Chicken" in proteins and "Mutton" in proteins:
        if "Mutton" in dinner:
            dinner = choose("dinner", allow_nonveg=False)
        elif "Mutton" in lunch:
            lunch = choose("lunch", allow_nonveg=False)
    return {"07:30": breakfast, "10:30": mid, "13:30": lunch, "16:30": afternoon, "20:00": dinner}

def sunday_suggestion(date_dt):
    if date_dt.weekday()!=6: return ""
    if 1 <= date_dt.day <=7:
        return random.choice(SUNDAY_ACTIVITIES)
    return random.choice(["Rest / gentle walk", "Light yoga", "Easy family outing"])

def current_phase(date_dt):
    # simple 12-week per-phase cycle
    weeks = ((date_dt - START_DATE).days)//7
    idx = (weeks // 12) % len(PHASES)
    return PHASES[idx]

# ---------------------- PERSISTENCE / TARGETS ----------------------
# per-athlete macro targets (defaults); will be editable in UI
TARGETS_FP = os.path.join(DATA_DIR, "athlete_targets.csv")
if not os.path.exists(TARGETS_FP):
    df_t = pd.DataFrame([{"Athlete": a, "Protein_g":120, "Carbs_g":350, "Fat_g":70, "Calories":2600, "SleepHours":7} for a in ATHLETES.keys()])
    df_t.to_csv(TARGETS_FP, index=False)
targets_df = pd.read_csv(TARGETS_FP)
targets = {row["Athlete"]: {"Protein_g": row["Protein_g"], "Carbs_g": row["Carbs_g"], "Fat_g": row["Fat_g"], "Calories": row["Calories"], "SleepHours": row["SleepHours"]} for _,row in targets_df.iterrows()}

# ---------------------- SIDEBAR ----------------------
LOGO_URL = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"
st.sidebar.image(LOGO_URL, use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.write("---")
days_left, hours_left, mins_left = (IRONMAN_DATE - NOW).days, ((IRONMAN_DATE - NOW).seconds // 3600), (((IRONMAN_DATE - NOW).seconds // 60) % 60)
st.sidebar.subheader("Ironman Hamburg 2028 Countdown")
st.sidebar.write(f"{days_left} days, {hours_left}h")
st.sidebar.write("---")
st.sidebar.subheader("Quote of the day")
st.sidebar.write(random.choice(["Consistency beats intensity.","Small steps every day.","Sleep is training too."]))
# Today's special: birthday / festival
today_str = NOW.strftime("%d-%m")
special_msg = ""
if today_str in FESTIVALS:
    special_msg = f"Festival: {FESTIVALS[today_str]}"
elif ATHLETES[athlete]["dob"] == today_str:
    special_msg = f"Happy Birthday, {athlete}!"
if special_msg:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(special_msg)

# ---------------------- MAIN HEADER ----------------------
hour = NOW.hour
greeting = "Good Morning" if hour<12 else "Good Afternoon" if hour<17 else "Good Evening"
st.title(f"{greeting}, {athlete}!")
st.write(f"Date: {NOW.strftime('%A, %d %B %Y')}")
week_start = NOW - timedelta(days=NOW.weekday())
st.write(f"Week starting: {week_start.strftime('%d %b %Y')}")

# ---------------------- LOAD LOG ----------------------
df_log = load_log(athlete)

# ---------------------- UI TABS ----------------------
tabs = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Progress Tracker","Nutrition & Sleep Tracker","Team Overview"])

# ---------------------- TODAY'S PLAN TAB ----------------------
with tabs[0]:
    st.header("Today's Plan")
    phase_now = current_phase(NOW)
    st.markdown(f"**Phase:** {phase_now}")

    # Activity suggestions based on phase
    if phase_now=="Base":
        run_suggestion = f"{5 + 0.1*((NOW-START_DATE).days//7):.1f} km"
        bike_suggestion = "No long rides (focus on run/strength)"
        swim_suggestion = "Technique drills (if started)"
    elif phase_now=="Build":
        run_suggestion = f"{10 + 0.2*((NOW-START_DATE).days//7):.1f} km"
        bike_suggestion = "20-60 km (progressive)"
        swim_suggestion = "200-1000 m"
    elif phase_now=="Peak":
        run_suggestion = f"{15 + 0.2*((NOW-START_DATE).days//7):.1f} km"
        bike_suggestion = "Long rides 60-150 km"
        swim_suggestion = "1500-3000 m"
    else:
        run_suggestion = "Short easy run"
        bike_suggestion = "Short easy ride"
        swim_suggestion = "Short easy swim"

    c1,c2,c3 = st.columns(3)
    run_done = c1.checkbox(f"Run: {run_suggestion}", key=f"run_{athlete}_{NOW.date()}")
    bike_done = c2.checkbox(f"Bike: {bike_suggestion}", key=f"bike_{athlete}_{NOW.date()}")
    swim_done = c3.checkbox(f"Swim: {swim_suggestion}", key=f"swim_{athlete}_{NOW.date()}")

    st.subheader("Nutrition (Maharashtrian-style, rotated)")
    meals = pick_daily_meals(athlete, NOW)
    meal_checks = {}
    cols = st.columns(5)
    for i,(t,m) in enumerate(meals.items()):
        meal_checks[t] = cols[i].checkbox(f"{t}\n{m}", key=f"{athlete}_meal_{t}_{NOW.date()}")

    prot_plan, carbs_plan, fat_plan, cal_plan = macros_for_meals(meals)
    st.markdown(f"**Planned macros today (all meals):** Protein {prot_plan} g • Carbs {carbs_plan} g • Fat {fat_plan} g • Calories {cal_plan} kcal")

    st.subheader("Sleep & Notes")
    sleep_hours = st.number_input("Sleep hours (last night / planned)", 0.0, 12.0, 7.0, 0.5, key=f"sleep_{athlete}_{NOW.date()}")
    note = st.text_area("Notes (how you felt / tips)")

    sunday_msg = sunday_suggestion(NOW)
    if sunday_msg:
        st.info(f"Sunday suggestion: {sunday_msg}")

    if st.button("Save today's entry"):
        eaten = {t:meals[t] for t,v in meal_checks.items() if v}
        prot_e, carbs_e, fat_e, cal_e = macros_for_meals(eaten) if eaten else (0,0,0,0)
        entry = {
            "Date": pd.to_datetime(NOW.date()),
            "Phase": phase_now,
            "Activity": ",".join([x for x,y in [("Run",run_done),("Bike",bike_done),("Swim",swim_done)] if y]),
            "CompletedMeals": ",".join(eaten.values()),
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

# ---------------------- NEXT DAY TAB ----------------------
with tabs[1]:
    st.header("Next Day Plan")
    nd = NOW + timedelta(days=1)
    st.write(f"Date: {nd.strftime('%A, %d %B %Y')}")
    phase_nd = current_phase(nd)
    st.write(f"Phase: {phase_nd}")
    if nd.weekday()==6:
        st.info("Next day is Sunday — suggested group activity:")
        st.write(sunday_suggestion(nd))
    else:
        st.write("Suggested session (summary):")
        if phase_nd=="Base":
            st.write("Run + Strength")
        elif phase_nd=="Build":
            st.write("Run + Bike + Swim/Strength")
        elif phase_nd=="Peak":
            st.write("Big sessions: long run + long ride + swim")
        else:
            st.write("Taper: short/easy sessions, recovery focus")
    next_meals = pick_daily_meals(athlete, nd)
    st.subheader("Next day nutrition (sample)")
    for t,m in next_meals.items():
        st.write(f"{t} - {m}")

    # show birthday/festival next day if any
    nd_str = nd.strftime("%d-%m")
    if nd_str in FESTIVALS:
        st.success(f"Upcoming festival: {FESTIVALS[nd_str]}")
    for a,v in ATHLETES.items():
        if v["dob"] == nd_str:
            st.success(f"Upcoming birthday: {a}")

# ---------------------- WEEKLY PLAN TAB ----------------------
with tabs[2]:
    st.header("Weekly Plan Overview")
    ws = NOW - timedelta(days=NOW.weekday())
    rows = []
    for i in range(7):
        d = ws + timedelta(days=i)
        mealsd = pick_daily_meals(athlete, d)
        rows.append({
            "Day": d.strftime("%A"),
            "ActivitySummary": ("Run" if current_phase(d)=="Base" else "Run/Bike/Swim" if current_phase(d) in ("Build","Peak") else "Light"),
            "MealsSample": f"{mealsd['07:30']} | {mealsd['13:30']}",
            "SundayActivity": sunday_suggestion(d) if d.weekday()==6 else ""
        })
    st.dataframe(pd.DataFrame(rows)[["Day","ActivitySummary","MealsSample","SundayActivity"]])

# ---------------------- PROGRESS TAB ----------------------
with tabs[3]:
    st.header("Progress Tracker")
    st.write("Activity progress & nutrition trends based on logged days.")
    df_display = df_log.copy()
    if df_display.empty:
        st.info("No logs yet. Save today's log to populate charts.")
    else:
        df_display["Date"] = pd.to_datetime(df_display["Date"])
        df_display = df_display.sort_values("Date")
        # Activity summary: weekly totals for last 12 weeks (if distances were logged they'd be in 'Note' or Activity field — here we show nutrition progress & sleep)
        # Weekly nutrition aggregation (Protein & Calories)
        df_recent = df_display.set_index("Date").resample("W").sum(numeric_only=True).reset_index()
        # guard for missing columns
        for col in ["Protein_g","Calories","SleepHours"]:
            if col not in df_recent.columns:
                df_recent[col] = 0
        if not df_recent.empty:
            fig = px.bar(df_recent, x="Date", y=["Protein_g","Calories"], title="Weekly Protein (g) & Calories")
            st.plotly_chart(fig, use_container_width=True)
        # Sleep trend
        if "SleepHours" in df_display.columns:
            st.line_chart(df_display.set_index("Date")[["SleepHours"]])

        # per-day table
        st.subheader("Recent logs")
        st.dataframe(df_display[["Date","Phase","Activity","CompletedMeals","Protein_g","Calories","SleepHours","Note"]].tail(30))

# ---------------------- NUTRITION & SLEEP TRACKER TAB ----------------------
with tabs[4]:
    st.header("Nutrition & Sleep Tracker")
    st.write("Set per-athlete daily macro & sleep targets. Alerts show if latest entry is below target.")
    # load targets (in memory; allow edit then save to file)
    target = targets.get(athlete, {"Protein_g":120, "Carbs_g":350, "Fat_g":70, "Calories":2600, "SleepHours":7})
    st.subheader("Set / adjust daily targets")
    colp, colc, colf, colcal, cols = st.columns(5)
    p_t = colp.number_input("Protein target (g/day)", 40, 400, int(target["Protein_g"]), step=1)
    c_t = colc.number_input("Carbs target (g/day)", 100, 800, int(target["Carbs_g"]), step=5)
    f_t = colf.number_input("Fat target (g/day)", 10, 200, int(target["Fat_g"]), step=1)
    cal_t = colcal.number_input("Calories target (kcal/day)", 1000, 6000, int(target["Calories"]), step=50)
    s_t = cols.number_input("Sleep target (hrs)", 4.0, 12.0, float(target["SleepHours"]), step=0.5)
    if st.button("Save targets"):
        # update CSV file
        targets[athlete] = {"Protein_g":p_t, "Carbs_g":c_t, "Fat_g":f_t, "Calories":cal_t, "SleepHours":s_t}
        df_t = pd.DataFrame([{"Athlete": a, **targets[a]} for a in targets.keys()])
        df_t.to_csv(os.path.join(DATA_DIR, "athlete_targets.csv"), index=False)
        st.success("Targets saved.")

    # show latest log and compare to targets
    if df_log.empty:
        st.info("No nutrition logs yet for this athlete.")
    else:
        latest = df_log.sort_values("Date").iloc[-1]
        st.markdown("**Latest logged day**")
        st.write(f"Date: {pd.to_datetime(latest['Date']).date()}")
        st.write(f"Protein: {latest.get('Protein_g',0)} g  •  Calories: {latest.get('Calories',0)} kcal  •  Sleep: {latest.get('SleepHours',0)} h")
        # alerts
        alerts = []
        if latest.get("Protein_g",0) < p_t:
            alerts.append(f"Protein below target: {latest.get('Protein_g',0)} < {p_t} g")
        if latest.get("Calories",0) < cal_t:
            alerts.append(f"Calories below target: {latest.get('Calories',0)} < {cal_t} kcal")
        if latest.get("SleepHours",0) < s_t:
            alerts.append(f"Sleep below target: {latest.get('SleepHours',0)} < {s_t} h")
        if alerts:
            for a in alerts:
                st.warning(a)
        else:
            st.success("Latest day met or exceeded targets!")

        # Show 14-day rolling averages vs targets
        recent = df_log.sort_values("Date").tail(14)
        if not recent.empty:
            avg_prot = recent["Protein_g"].mean()
            avg_cal = recent["Calories"].mean()
            avg_sleep = recent["SleepHours"].mean()
            st.markdown(f"14-day averages — Protein: {avg_prot:.1f} g • Calories: {avg_cal:.0f} kcal • Sleep: {avg_sleep:.2f} h")
            fig = px.line(recent, x="Date", y=["Protein_g","Calories","SleepHours"], title="Last 14 entries — Protein / Calories / Sleep")
            st.plotly_chart(fig, use_container_width=True)

# ---------------------- TEAM OVERVIEW TAB ----------------------
with tabs[5]:
    st.header("Team Overview")
    # build summary for each athlete
    summary_rows = []
    for a in ATHLETES.keys():
        df_a = load_log(a)
        if df_a.empty:
            summary_rows.append({"Athlete": a, "Protein_14d": 0, "Calories_14d": 0, "Sleep_avg_14d": 0})
            continue
        df_a["Date"] = pd.to_datetime(df_a["Date"])
        recent = df_a[df_a["Date"] >= (pd.to_datetime(NOW.date()) - pd.Timedelta(days=14))]
        prot14 = recent["Protein_g"].sum() if "Protein_g" in recent.columns else 0
        cal14 = recent["Calories"].sum() if "Calories" in recent.columns else 0
        sleep14 = recent["SleepHours"].mean() if "SleepHours" in recent.columns and len(recent)>0 else 0
        summary_rows.append({"Athlete": a, "Protein_14d": round(prot14,1), "Calories_14d": int(cal14), "Sleep_avg_14d": round(float(sleep14),1)})
    sum_df = pd.DataFrame(summary_rows)
    st.dataframe(sum_df[["Athlete","Protein_14d","Calories_14d","Sleep_avg_14d"]])

    # visual comparisons
    if not sum_df.empty:
        fig1 = px.bar(sum_df, x="Athlete", y="Protein_14d", title="Team: Protein last 14 days (g)")
        fig2 = px.bar(sum_df, x="Athlete", y="Calories_14d", title="Team: Calories last 14 days")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

    # Readiness check (heuristic)
    st.subheader("Ironman readiness heuristic (4-week projection)")
    # Collect last 28 days totals per athlete
    readiness = []
    for a in ATHLETES.keys():
        df_a = load_log(a)
        if df_a.empty:
            readiness.append({"Athlete": a, "ReadinessScore": 0})
            continue
        df_a["Date"] = pd.to_datetime(df_a["Date"])
        recent28 = df_a[df_a["Date"] >= (pd.to_datetime(NOW.date()) - pd.Timedelta(days=28))]
        # Use nutrition & simple activity indicators — here we use calories & protein as proxy + number of logged activity days
        prot = recent28["Protein_g"].sum() if "Protein_g" in recent28.columns else 0
        cal = recent28["Calories"].sum() if "Calories" in recent28.columns else 0
        days_logged = recent28.shape[0]
        # simple score: weighted normalized values
        score = 0.0
        # protein target per 28 days = target_protein * 28 (get from targets or defaults)
        targ = targets.get(a, {"Protein_g":120,"Calories":2600})
        prot_target_28 = targ["Protein_g"] * 28
        cal_target_28 = targ["Calories"] * 28
        s1 = min(prot / max(1,prot_target_28), 1.0)
        s2 = min(cal / max(1,cal_target_28), 1.0)
        s3 = min(days_logged / 28.0, 1.0)
        score = (0.5 * s1) + (0.3 * s2) + (0.2 * s3)
        readiness.append({"Athlete": a, "ReadinessScore": round(score*100,1)})
    rd_df = pd.DataFrame(readiness).sort_values("ReadinessScore", ascending=False)
    st.dataframe(rd_df)
    st.markdown("**Interpretation:** Readiness score is a heuristic combining recent protein adherence, calories & consistency (0-100). Aim >70 to be in a good preparation zone; this is a guide — training volumes & specific workouts determine actual race readiness.")

# ---------------------- FOOTER ----------------------
st.markdown("---")
st.markdown("Notes: This app uses rotated Maharashtrian meal samples (chapati/bhakri/rice/jowar) with eggs/fish/chicken/mutton rotation so non-veg is not on every day and chicken & mutton are not on the same day. Macros are approximate; edit `FOOD_MACROS` in the code if you want different values. All times are IST (Asia/Kolkata).")

