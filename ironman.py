# ironman_tracker_firebase.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz, random
import firebase_admin
from firebase_admin import credentials, db

# ---------------- SETTINGS ----------------
st.set_page_config(
    page_title="Ironman 2028 Coach",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- DARK THEME & MOBILE UI ----------------
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.5rem; }
    h1,h2,h3 { font-size: 1.2rem !important; }
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
ironman_date = datetime(2028,7,14,6,0,0,tzinfo=pytz.timezone("Europe/Berlin"))
tz = pytz.timezone("Asia/Kolkata")
now = datetime.now(tz)
days_left = (ironman_date - now).days

# ---------------- QUOTES & SUNDAY ACTIVITIES ----------------
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
st.sidebar.image(logo_url, use_container_width=True)

# ---------------- FIREBASE SETUP ----------------
cred = credentials.Certificate("path/to/serviceAccountKey.json")  # Replace with your JSON
firebase_admin.initialize_app(cred, {"databaseURL": "https://your-project-id.firebaseio.com/"})

def save_today_data(athlete, data_row):
    ref = db.reference(f"/athletes/{athlete}/logs")
    ref.child(data_row["Date"]).set(data_row.to_dict())

def get_all_athletes_data():
    ref = db.reference("/athletes")
    data = ref.get()
    return data or {}

# ---------------- SIDEBAR ----------------
athlete = st.sidebar.selectbox("Select Athlete", list(ATHLETES.keys()))
st.sidebar.write("---")
st.sidebar.subheader("Ironman Hamburg 2028 Countdown")
st.sidebar.write(f"{days_left} Days Left")
st.sidebar.write("---")
st.sidebar.subheader("Quote of the Day")
st.sidebar.write(random.choice(quotes))

today_str = now.strftime("%d-%m")
special = ""
if today_str in festivals: special = f"Festival: {festivals[today_str]}"
elif today_str == ATHLETES[athlete]["dob"]: special = f"Happy Birthday, {athlete}!"
if special:
    st.sidebar.write("---")
    st.sidebar.subheader("Today's Special")
    st.sidebar.write(special)

# ---------------- GREETING ----------------
hour = now.hour
if hour<12: greeting="Good Morning"
elif hour<16: greeting="Good Afternoon"
else: greeting="Good Evening"
st.title(f"{greeting}, {athlete}!")
st.write(f"📅 {now.strftime('%A, %d %B %Y')} | Week starting { (now - timedelta(days=now.weekday())).strftime('%d %b %Y')}")

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
    "Mayur":[
        {"07:30":"Poha + Milk","10:30":"Fruits/Nuts","13:30":"Chapati + Dal + Veg","16:30":"Eggs + Salad","20:00":"Bhakri + Chicken Curry"},
        {"07:30":"Upma + Curd","10:30":"Banana","13:30":"Rice + Fish Curry","16:30":"Nuts","20:00":"Chapati + Veg + Soup"}
    ],
    "Sudeep":[
        {"07:30":"Oats + Milk","10:30":"Chikki","13:30":"Bhakri + Mutton Curry","16:30":"Fruits","20:00":"Chapati + Veg"},
        {"07:30":"Idli + Sambhar","10:30":"Fruit","13:30":"Rice + Dal + Veg","16:30":"Protein Shake","20:00":"Bhakri + Fish Curry"}
    ],
    "Vaishali":[
        {"07:30":"Upma + Tea","10:30":"Fruits","13:30":"Chapati + Veg + Dal","16:30":"Nuts","20:00":"Bhakri + Paneer Curry"},
        {"07:30":"Poha + Curd","10:30":"Banana","13:30":"Rice + Dal","16:30":"Sprouts","20:00":"Chapati + Veg"}
    ]
}

# ---------------- DAILY PLAN ----------------
def generate_daily_plan(athlete,today):
    if current_phase=="Base": run,bike,swim=5+0.1*week_number,0,0
    elif current_phase=="Build": run,bike,swim=10+0.2*week_number,20,200
    elif current_phase=="Peak": run,bike,swim=15+0.2*week_number,40,500
    else: run,bike,swim=8,20,200
    meals = meal_plans[athlete][today.day % len(meal_plans[athlete])]
    sunday_activity = random.choice(sunday_activities) if today.weekday()==6 else ""
    return run,bike,swim,meals,sunday_activity

# ---------------- TABS ----------------
tabs = st.tabs(["Today's Plan","Next Day Plan","Weekly Plan","Progress Tracker & Nutrition","Team Overview"])

# ---------------- TODAY ----------------
with tabs[0]:
    run,bike,swim,meals,sun_act = generate_daily_plan(athlete, now)
    st.subheader("Training")
    run_chk = st.checkbox(f"Run {run:.1f} km")
    bike_chk = st.checkbox(f"Bike {bike:.1f} km")
    swim_chk = st.checkbox(f"Swim {swim:.0f} m")
    st.subheader("Nutrition")
    meal_chk = {t: st.checkbox(f"{t} - {m}") for t,m in meals.items()}
    st.subheader("Sleep & Recovery")
    sleep = st.slider("Sleep Hours",0,12,8)
    recovery = st.slider("Recovery Level",0,100,60)

    # Nutrition macros
    macros = {"Protein_g":0,"Carbs_g":0,"Fat_g":0,"Calories":0}
    for m in meals.values():
        if any(x in m for x in ["Egg","Chicken","Fish","Mutton","Paneer"]): macros["Protein_g"]+=25; macros["Calories"]+=300
        else: macros["Carbs_g"]+=30; macros["Calories"]+=200
    macros["Fat_g"]=0.25*macros["Calories"]/9

    # Save to Firebase
    today_data = {
        "Date":now.strftime("%Y-%m-%d"),"Phase":current_phase,
        "Run_km":run if run_chk else 0,"Bike_km":bike if bike_chk else 0,"Swim_m":swim if swim_chk else 0,
        "Protein_g":macros["Protein_g"],"Carbs_g":macros["Carbs_g"],"Fat_g":macros["Fat_g"],"Calories":macros["Calories"],
        "Sleep":sleep,"Recovery":recovery
    }
    if st.button("Submit Today's Data"): save_today_data(athlete,today_data); st.success("Data saved!")

    if sun_act: st.info(f"Sunday Activity: {sun_act}")

# ---------------- NEXT DAY ----------------
with tabs[1]:
    nd = now + timedelta(days=1)
    run,bike,swim,meals,sun_act = generate_daily_plan(athlete, nd)
    st.subheader(f"Plan for {nd.strftime('%A, %d %B %Y')}")
    st.write(f"Run {run:.1f} km | Bike {bike:.1f} km | Swim {swim:.0f} m")
    st.subheader("Meals")
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

# ---------------- PROGRESS TRACKER & NUTRITION ----------------
with tabs[3]:
    st.subheader("Progress Tracker & Nutrition")
    all_data = get_all_athletes_data()
    if athlete in all_data:
        df_athlete = pd.DataFrame(all_data[athlete]["logs"]).T
        df_athlete["Date"]=pd.to_datetime(df_athlete["Date"])
        st.line_chart(df_athlete.set_index("Date")[["Run_km","Bike_km","Swim_m"]])
        st.line_chart(df_athlete.set_index("Date")[["Protein_g","Carbs_g","Calories","Sleep"]])
        progress = (week_number/total_weeks)*100
        st.metric("Overall Training Progress", f"{progress:.1f}%")

# ---------------- TEAM OVERVIEW ----------------
with tabs[4]:
    st.subheader("Team Overview")
    all_logs = []
    for ath in ATHLETES.keys():
        if ath in all_data:
            df = pd.DataFrame(all_data[ath]["logs"]).T
            df["Date"]=pd.to_datetime(df["Date"])
            df["Athlete"]=ath
            all_logs.append(df)
    if all_logs:
        team_df = pd.concat(all_logs)
        st.line_chart(team_df.pivot(index="Date",columns="Athlete",values="Protein_g").fillna(0))
        st.line_chart(team_df.pivot(index="Date",columns="Athlete",values="Run_km").fillna(0))
        st.success(f"Team is {(week_number/total_weeks)*100:.1f}% on track for Ironman Hamburg 2028")
