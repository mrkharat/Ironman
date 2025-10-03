# ironman_tracker_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os, random, pytz

# ---------------- SETTINGS ----------------
st.set_page_config(
    page_title="Ironman 2028 Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)
DATA_DIR = "athlete_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- DARK THEME & MOBILE UI ----------------
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.5rem; }
    h1, h2, h3 { font-size: 1.2rem !important; }
    .stButton>button { width: 100%; }
}
body { background-color: #0E1117; color: #FFFFFF; }
.stButton>button { background-color: #1F2A40; color: #FFFFFF; border-radius: 6px; }
.stCheckbox>div>label, .stDataFrame th { color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ---------------- ATHLETES ----------------
ATHLETES = {
    "Mayur": {"gender":"M","weight":62,"dob":"25-12"},
    "Sudeep": {"gender":"M","weight":73,"dob":"31-10"},
    "Vaishali": {"gender":"F","weight":64,"dob":"02-04"}
}

# ---------------- IRONMAN DATE ----------------
ironman_date = datetime(2028, 7, 14, 6, 0, 0, tzinfo=pytz.timezone("Europe/Berlin"))
tz = pytz.timezone("Asia/Kolkata")
now = datetime.now(tz)
days_left = (ironman_date - now).days

# ---------------- QUOTES & ACTIVITIES ----------------
quotes = [
    "Consistency beats intensity.",
    "Every stroke, every pedal, every step counts.",
    "Ironman is 90% mental.",
    "Progress, not perfection.",
    "Strong body, stronger mind."
]

sunday_activities = [
    "Hike in Sanjay Gandhi National Park",
    "Group cycling to Lonavala",
    "Beach run at Juhu",
    "Yoga session together",
    "Visit a village for plantation drive",
    "Long drive to Malshej Ghat",
    "Meditation session"
]

# ---------------- FESTIVALS ----------------
festivals = {
    "01-01":"New Year",
    "15-08":"Independence Day",
    "02-10":"Gandhi Jayanti",
    "25-12":"Christmas"
}

# ---------------- LOGO ----------------
logo_url = "https://raw.githubusercontent.com/mrkharat/Ironman/main/Ironman-Logo.jpg"

# ---------------- SIDEBAR ----------------
st.sidebar.image(logo_url, use_container_width=True)
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.write("---")
st.sidebar.subheader("Ironman Hamburg 2028 Countdown")
st.sidebar.write(f"{days_left} Days Left")

st.sidebar.write("---")
st.sidebar.subheader("Quote of the Day")
st.sidebar.write(random.choice(quotes))

today_str = now.strftime("%d-%m")
special = ""
if today_str in festivals:
    special = f"Festival: {festivals[today_str]}"
elif today_str == ATHLETES[athlete]["dob"]:
    special = f"Happy Birthday, {athlete}!"
if special:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(special)

# ---------------- GREETING ----------------
hour = now.hour
if hour < 12: greeting = "Good Morning"
elif hour < 16: greeting = "Good Afternoon"
else: greeting = "Good Evening"

st.title(f"{greeting}, {athlete}!")
st.write(f"📅 {now.strftime('%A, %d %B %Y')} | Week starting { (now - timedelta(days=now.weekday())).strftime('%d %b %Y')}")

# ---------------- DATA FILE ----------------
data_file = os.path.join(DATA_DIR, f"{athlete}_log.csv")
if os.path.exists(data_file):
    df_log = pd.read_csv(data_file, parse_dates=["Date"])
else:
    df_log = pd.DataFrame(columns=["Date","Phase","Run_km","Bike_km","Swim_m",
                                   "Protein_g","Carbs_g","Fat_g","Calories","Sleep","Recovery"])
    df_log.to_csv(data_file,index=False)

# ---------------- TRAINING PHASE ----------------
phases = ["Base","Build","Peak","Taper"]
phase_weeks = {"Base":20,"Build":40,"Peak":20,"Taper":10}
week_number = ((now - datetime(2025,10,1,tzinfo=tz)).days)//7 + 1
phase_cumsum = np.cumsum(list(phase_weeks.values()))
for i, pc in enumerate(phase_cumsum):
    if week_number <= pc: current_phase = phases[i]; break
else: current_phase = "Taper"
total_weeks = sum(phase_weeks.values())

# ---------------- MEAL PLANS ----------------
meal_plans = {
    "Mayur": [
        {"07:30":"Poha + Milk","10:30":"Fruits/Nuts","13:30":"Chapati + Dal + Veg","16:30":"Eggs + Salad","20:00":"Bhakri + Chicken Curry"},
        {"07:30":"Upma + Curd","10:30":"Banana","13:30":"Rice + Fish Curry","16:30":"Nuts","20:00":"Chapati + Veg + Soup"}
    ],
    "Sudeep": [
        {"07:30":"Oats + Milk","10:30":"Chikki","13:30":"Bhakri + Mutton Curry","16:30":"Fruits","20:00":"Chapati + Veg"},
        {"07:30":"Idli + Sambhar","10:30":"Fruit","13:30":"Rice + Dal + Veg","16:30":"Protein Shake","20:00":"Bhakri + Fish Curry"}
    ],
    "Vaishali": [
        {"07:30":"Upma + Tea","10:30":"Fruits","13:30":"Chapati + Veg + Dal","16:30":"Nuts","20:00":"Bhakri + Paneer Curry"},
        {"07:30":"Poha + Curd","10:30":"Banana","13:30":"Rice + Dal","16:30":"Sprouts","20:00":"Chapati + Veg"}
    ]
}

# ---------------- GENERATE PLAN ----------------
def generate_daily_plan(athlete, today):
    if current_phase=="Base":
        run, bike, swim = 5+0.1*week_number, 0, 0
    elif current_phase=="Build":
        run, bike, swim = 10+0.2*week_number, 20, 200
    elif current_phase=="Peak":
        run, bike, swim = 15+0.2*week_number, 40, 500
    else:
        run, bike, swim = 8, 20, 200
    meals = meal_plans[athlete][today.day % len(meal_plans[athlete])]
    sunday_activity = random.choice(sunday_activities) if today.weekday()==6 else ""
    return run, bike, swim, meals, sunday_activity

# ---------------- TABS ----------------
tabs = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Progress Tracker","Team Overview"])

# ---------------- TODAY ----------------
with tabs[0]:
    st.subheader("Today's Plan & Input")
    run,bike,swim,meals,sun_act = generate_daily_plan(athlete, now)

    st.write("### Training")
    run_cb = st.checkbox(f"Run {run:.1f} km")
    bike_cb = st.checkbox(f"Bike {bike:.1f} km")
    swim_cb = st.checkbox(f"Swim {swim:.0f} m")

    st.write("### Nutrition")
    meal_cb = {t: st.checkbox(f"{t} - {m}") for t,m in meals.items()}

    st.write("### Sleep & Recovery")
    sleep = st.slider("Sleep Hours",0,12,8)
    recovery = st.slider("Recovery Level",0,100,60)

    submit = st.button("Submit Today's Data")

    if submit:
        macros = {"Protein_g":0,"Carbs_g":0,"Fat_g":0,"Calories":0}
        for t,m in meals.items():
            if any(x in m for x in ["Egg","Chicken","Fish","Mutton","Paneer"]):
                macros["Protein_g"] += 25; macros["Calories"] += 300
            else:
                macros["Carbs_g"] += 30; macros["Calories"] += 200
        macros["Fat_g"] = 0.25*macros["Calories"]/9

        df_log = df_log[df_log["Date"]!=now.strftime("%Y-%m-%d")]
        df_log = pd.concat([df_log, pd.DataFrame([{
            "Date":now.strftime("%Y-%m-%d"),"Phase":current_phase,
            "Run_km":run if run_cb else 0,
            "Bike_km":bike if bike_cb else 0,
            "Swim_m":swim if swim_cb else 0,
            "Protein_g":macros["Protein_g"],"Carbs_g":macros["Carbs_g"],
            "Fat_g":macros["Fat_g"],"Calories":macros["Calories"],
            "Sleep":sleep,"Recovery":recovery
        }])])
        df_log.to_csv(data_file,index=False)
        st.success("Today's data submitted!")

    if sun_act: st.info(f"Sunday Activity: {sun_act}")

# ---------------- NEXT DAY ----------------
with tabs[1]:
    nd = now + timedelta(days=1)
    run,bike,swim,meals,sun_act = generate_daily_plan(athlete, nd)
    st.subheader(f"Plan for {nd.strftime('%A, %d %B %Y')}")
    st.write(f"Run {run:.1f} km | Bike {bike:.1f} km | Swim {swim:.0f} m")
    st.write("### Meals")
    for t,m in meals.items(): st.write(f"{t} - {m}")
    if sun_act: st.info(f"Sunday Special: {sun_act}")
    nd_str = nd.strftime("%d-%m")
    if nd_str in festivals: st.success(f"Festival: {festivals[nd_str]}")
    elif nd_str == ATHLETES[athlete]["dob"]: st.success(f"Happy Birthday, {athlete}!")

# ---------------- WEEKLY PLAN ----------------
with tabs[2]:
    week_start = now - timedelta(days=now.weekday())
    week_dates = [week_start+timedelta(days=i) for i in range(7)]
    week_data = []
    for d in week_dates:
        run,bike,swim,_,sa = generate_daily_plan(athlete,d)
        week_data.append({"Date":d.strftime("%a"),"Run":run,"Bike":bike,"Swim":swim,"Sunday":sa})
    st.dataframe(pd.DataFrame(week_data))

# ---------------- PROGRESS TRACKER ----------------
with tabs[3]:
    st.subheader("Progress Tracker")
    target_protein = st.number_input("Target Protein (g/day)",40,200,100,key="prot")
    target_carbs = st.number_input("Target Carbs (g/day)",100,400,200,key="carb")
    target_calories = st.number_input("Target Calories (kcal/day)",1500,4000,2500,key="cal")

    if not df_log.empty:
        last = df_log.iloc[-1]
        st.markdown(f"**Today's Protein:** {last['Protein_g']} g {'🟢' if last['Protein_g']>=target_protein else '🔴'}")
        st.markdown(f"**Today's Carbs:** {last['Carbs_g']} g {'🟢' if last['Carbs_g']>=target_carbs else '🔴'}")
        st.markdown(f"**Today's Calories:** {last['Calories']} kcal {'🟢' if last['Calories']>=target_calories else '🔴'}")
        st.markdown(f"**Sleep:** {last['Sleep']} h")

    st.write("### Training Progress")
    st.line_chart(df_log.set_index("Date")[["Run_km","Bike_km","Swim_m"]])

    st.write("### Nutrition & Sleep")
    df_macro = df_log.set_index("Date")[["Protein_g","Carbs_g","Calories","Sleep"]]
    st.line_chart(df_macro)

# ---------------- TEAM OVERVIEW ----------------
with tabs[4]:
    st.subheader("Team Overview")
    all_logs = []
    for ath in ATHLETES.keys():
        f = os.path.join(DATA_DIR,f"{ath}_log.csv")
        if os.path.exists(f): all_logs.append(pd.read_csv(f,parse_dates=["Date"]).assign(Athlete=ath))
    if all_logs:
        team_df = pd.concat(all_logs)
        st.write("### Protein Intake")
        team_protein = team_df.pivot(index="Date",columns="Athlete",values="Protein_g").fillna(0)
        st.line_chart(team_protein)
        st.write("### Carbs Intake")
        team_carbs = team_df.pivot(index="Date",columns="Athlete",values="Carbs_g").fillna(0)
        st.line_chart(team_carbs)
        st.write("### Calories")
        team_cal = team_df.pivot(index="Date",columns="Athlete",values="Calories").fillna(0)
        st.line_chart(team_cal)
        st.write("### Training")
        st.line_chart(team_df.pivot(index="Date",columns="Athlete",values="Run_km").fillna(0))
        st.line_chart(team_df.pivot(index="Date",columns="Athlete",values="Bike_km").fillna(0))
        st.line_chart(team_df.pivot(index="Date",columns="Athlete",values="Swim_m").fillna(0))
        on_track = (week_number/total_weeks)*100
        st.success(f"Team is {on_track:.1f}% on track for Ironman Hamburg 2028")
