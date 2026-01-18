import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px

st.set_page_config(page_title="Life Tracker", layout="wide")

DATA_FILE = "life_tracker_data.csv"
USER_FILE = "users.csv"
GOAL_FILE = "goals.csv"

# -------------------- Utilities --------------------

def safe_read_csv(path, cols):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def load_users():
    return safe_read_csv(USER_FILE, ["username", "password"])

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def authenticate(username, password):
    users = load_users()
    if len(users) == 0:
        return False
    return ((users["username"] == username) & (users["password"] == password)).any()

def load_data():
    return safe_read_csv(DATA_FILE, ["Username", "Date", "Time", "Task", "Productive"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_goals():
    return safe_read_csv(GOAL_FILE, ["Username", "Goal", "Type", "Completed", "Date"])

def save_goals(df):
    df.to_csv(GOAL_FILE, index=False)

# -------------------- Session --------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.title("💎 Life Tracker — FINAL SYSTEM (PATCHED)")

# -------------------- Login --------------------

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        nu = st.text_input("New Username")
        npw = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            users = load_users()
            if nu in users["username"].values:
                st.warning("Username exists")
            else:
                users = pd.concat(
                    [users, pd.DataFrame([[nu, npw]], columns=["username","password"])]
                )
                save_users(users)
                st.success("Account created!")

    st.stop()

# -------------------- Sidebar --------------------

st.sidebar.success(f"Logged in: {st.session_state.username}")

menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Planner", "Weekly", "Monthly", "Insights", "Goals", "Streaks"]
)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# -------------------- Load Data --------------------

df = load_data()
goals_df = load_goals()
user_data = df[df["Username"] == st.session_state.username]

# -------------------- Dashboard --------------------

if menu == "Dashboard":
    st.header("📊 Dashboard")

    if len(user_data) == 0:
        st.info("No data yet. Start using Planner.")
    else:
        user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")

        total = len(user_data)
        productive = len(user_data[user_data["Productive"] == "Yes"])
        score = int((productive / total) * 100) if total > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Hours", total)
        c2.metric("Productive", productive)
        c3.metric("Score", f"{score}%")

        prod_counts = user_data["Productive"].value_counts().reset_index()
        prod_counts.columns = ["Type", "Hours"]

        fig = px.pie(prod_counts, names="Type", values="Hours", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# -------------------- Planner --------------------

# -------------------- 24-Hour Planner (NEW CORE) --------------------

def hour_to_label(h):
    # Converts 0–23 → 12 AM, 1 AM, ..., 11 PM
    if h == 0:
        return "12 AM"
    elif h < 12:
        return f"{h} AM"
    elif h == 12:
        return "12 PM"
    else:
        return f"{h-12} PM"

def hour_range_label(h):
    return f"{hour_to_label(h)} – {hour_to_label((h+1) % 24)}"

def get_section(h):
    if 0 <= h <= 5:
        return "🌙 Night"
    elif 6 <= h <= 11:
        return "🌅 Morning"
    elif 12 <= h <= 17:
        return "🌞 Afternoon"
    else:
        return "🌙 Evening"

SECTION_COLORS = {
    "🌙 Night": "#1f2a44",
    "🌅 Morning": "#f5c542",
    "🌞 Afternoon": "#4aa3df",
    "🌙 Evening": "#7b4ae2"
}

if menu == "Planner":
    st.header("🕒 24-Hour Planner")

    selected_date = st.date_input("Select Date", datetime.today())
    now_hour = datetime.now().hour

    hours = list(range(24))
    planner_rows = []

    # Group hours into sections
    sections = {
        "🌙 Night": [0,1,2,3,4,5],
        "🌅 Morning": [6,7,8,9,10,11],
        "🌞 Afternoon": [12,13,14,15,16,17],
        "🌙 Evening": [18,19,20,21,22,23]
    }

    for section, hrs in sections.items():
        with st.expander(section, expanded=True):
            st.markdown(
                f"<div style='padding:8px; border-radius:6px; background-color:{SECTION_COLORS[section]}; color:white; font-weight:bold;'>"
                f"{section}</div>",
                unsafe_allow_html=True
            )

            for h in hrs:
                label = hour_range_label(h)

                is_current = (h == now_hour)
                bg = "#e8f0ff" if is_current else "transparent"

                c1, c2, c3 = st.columns([2, 6, 2])
                with c1:
                    st.markdown(
                        f"<div style='padding:6px; background:{bg}; border-radius:4px;'>⏰ {label}</div>",
                        unsafe_allow_html=True
                    )
                with c2:
                    task = st.text_input(f"Task {h}", key=f"task_{selected_date}_{h}")
                with c3:
                    prod = st.selectbox("Productive?", ["Yes", "No"], key=f"prod_{selected_date}_{h}")

                planner_rows.append([
                    st.session_state.username,
                    selected_date,
                    h,                  # INTERNAL hour (0–23)
                    label,              # DISPLAY label
                    task,
                    prod
                ])

    if st.button("💾 Save Day"):
        new_df = pd.DataFrame(
            planner_rows,
            columns=["Username", "Date", "Hour", "TimeLabel", "Task", "Productive"]
        )

        # Backward compatibility: keep old "Time" column if needed
        new_df["Time"] = new_df["TimeLabel"]

        df = pd.concat([df, new_df], ignore_index=True)
        save_data(df)
        st.success("Day saved successfully!")

    st.subheader("Your Past Entries")
    if len(user_data) == 0:
        st.info("No past data yet.")
    else:
        st.dataframe(user_data.tail(200))

# -------------------- Weekly (24-Hour Aware) --------------------

if menu == "Weekly":
    st.header("📅 Weekly Report (24-Hour Aware)")

    if len(user_data) == 0:
        st.info("No data available.")
    else:
        user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")
        user_data["Week"] = user_data["Date"].dt.isocalendar().week
        user_data["Year"] = user_data["Date"].dt.year

        weeks = user_data[["Week", "Year"]].drop_duplicates().sort_values(
            ["Year", "Week"], ascending=False
        )

        if len(weeks) == 0:
            st.info("No valid weeks found.")
        else:
            row = weeks.iloc[0]
            w, y = int(row["Week"]), int(row["Year"])

            week_data = user_data[(user_data["Week"] == w) & (user_data["Year"] == y)]

            total = len(week_data)
            productive = len(week_data[week_data["Productive"] == "Yes"])
            score = int((productive / total) * 100) if total > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Hours", total)
            c2.metric("Productive", productive)
            c3.metric("Score", f"{score}%")

            daily = (
                week_data
                .groupby(week_data["Date"].dt.day_name())
                .size()
                .reset_index(name="Hours")
            )

            st.subheader("Day-wise Activity")
            st.plotly_chart(
    px.bar(daily, x="Date", y="Hours", text="Hours"),
    use_container_width=True,
    key="weekly_daywise_chart"
)


            # 24-hour distribution
            if "Hour" in week_data.columns:
                hour_dist = (
                    week_data
                    .groupby("Hour")
                    .size()
                    .reset_index(name="Entries")
                )
                st.subheader("24-Hour Distribution")
                st.plotly_chart(
    px.bar(hour_dist, x="Hour", y="Entries"),
    use_container_width=True,
    key="weekly_hour_dist_chart"
)


# -------------------- Monthly (24-Hour Aware) --------------------

if menu == "Monthly":
    st.header("🗓 Monthly Report (24-Hour Aware)")

    if len(user_data) == 0:
        st.info("No data available.")
    else:
        user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")
        user_data["Month"] = user_data["Date"].dt.month
        user_data["Year"] = user_data["Date"].dt.year
        user_data["Day"] = user_data["Date"].dt.day

        months = user_data[["Month", "Year"]].drop_duplicates().sort_values(
            ["Year", "Month"], ascending=False
        )

        if len(months) == 0:
            st.info("No valid months found.")
        else:
            row = months.iloc[0]
            m, y = int(row["Month"]), int(row["Year"])

            month_data = user_data[
                (user_data["Month"] == m) & (user_data["Year"] == y)
            ]

            total = len(month_data)
            productive = len(month_data[month_data["Productive"] == "Yes"])
            score = int((productive / total) * 100) if total > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Hours", total)
            c2.metric("Productive", productive)
            c3.metric("Score", f"{score}%")

            daily = (
                month_data
                .groupby("Day")
                .size()
                .reset_index(name="Hours")
            )

            st.subheader("Day-wise Activity")
            st.plotly_chart(
    px.bar(daily, x="Day", y="Hours", text="Hours"),
    use_container_width=True,
    key="monthly_daywise_chart"
)


            # 24-hour distribution
            if "Hour" in month_data.columns:
                hour_dist = (
                    month_data
                    .groupby("Hour")
                    .size()
                    .reset_index(name="Entries")
                )
                st.subheader("24-Hour Distribution")
                st.plotly_chart(
    px.bar(hour_dist, x="Hour", y="Entries"),
    use_container_width=True,
    key="monthly_hour_dist_chart"
)


# -------------------- Monthly --------------------

if menu == "Monthly":
    st.header("🗓 Monthly Report")

    if len(user_data) == 0:
        st.info("No data available.")
    else:
        user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")
        user_data["Month"] = user_data["Date"].dt.month
        user_data["Year"] = user_data["Date"].dt.year
        user_data["Day"] = user_data["Date"].dt.day

        months = user_data[["Month", "Year"]].drop_duplicates().sort_values(
            ["Year", "Month"], ascending=False
        )

        if len(months) == 0:
            st.info("No valid months found.")
        else:
            row = months.iloc[0]
            m, y = int(row["Month"]), int(row["Year"])

            month_data = user_data[
                (user_data["Month"] == m) & (user_data["Year"] == y)
            ]

            total = len(month_data)
            productive = len(month_data[month_data["Productive"] == "Yes"])
            score = int((productive / total) * 100) if total > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Hours", total)
            c2.metric("Productive", productive)
            c3.metric("Score", f"{score}%")

            # FIXED GROUPING
            daily = (
                month_data
                .groupby("Day")
                .size()
                .reset_index(name="Hours")
            )

            st.subheader("Day-wise Activity")
            st.plotly_chart(
                px.bar(daily, x="Day", y="Hours", text="Hours"),
                use_container_width=True
            )
# -------------------- Insights --------------------

# -------------------- Insights (24-Hour Aware) --------------------

def hour_to_ampm(h):
    if h == 0:
        return "12 AM"
    elif h < 12:
        return f"{h} AM"
    elif h == 12:
        return "12 PM"
    else:
        return f"{h-12} PM"

def hour_bucket(h):
    if 0 <= h <= 5:
        return "Night"
    elif 6 <= h <= 11:
        return "Morning"
    elif 12 <= h <= 17:
        return "Afternoon"
    else:
        return "Evening"

if menu == "Insights":
    st.header("🧠 Productivity Intelligence (24-Hour Core)")

    if len(user_data) == 0:
        st.info("No data available yet.")
    else:
        # Use Hour column if available, else fallback to Time parsing
        if "Hour" not in user_data.columns:
            def extract_hour(t):
                try:
                    return int(str(t).split(":")[0])
                except:
                    return None
            user_data["Hour"] = user_data["Time"].apply(extract_hour)

        hour_data = user_data.dropna(subset=["Hour"])

        if len(hour_data) == 0:
            st.info("No valid time data found.")
        else:
            # Productivity by hour
            summary = hour_data.groupby("Hour").agg(
                total=("Productive", "count"),
                productive=("Productive", lambda x: (x == "Yes").sum())
            ).reset_index()

            summary["Score"] = (summary["productive"] / summary["total"]) * 100
            summary["Label"] = summary["Hour"].apply(lambda x: hour_to_ampm(int(x)))
            summary["Bucket"] = summary["Hour"].apply(lambda x: hour_bucket(int(x)))

            # Best & worst hours
            best_row = summary.sort_values("Score", ascending=False).iloc[0]
            worst_row = summary.sort_values("Score", ascending=True).iloc[0]

            st.success(f"🔥 Best focus hour: {hour_to_ampm(int(best_row['Hour']))}")
            st.warning(f"⚠️ Worst focus hour: {hour_to_ampm(int(worst_row['Hour']))}")

            # Focus window detection (top 3)
            top_hours = summary.sort_values("Score", ascending=False).head(3)
            focus_window = ", ".join(top_hours["Label"].tolist())
            st.info(f"🎯 Your peak focus window: {focus_window}")

            # Bucket analysis
            bucket_summary = summary.groupby("Bucket").agg(
                avg_score=("Score", "mean"),
                total_hours=("total", "sum")
            ).reset_index()

            st.subheader("Time of Day Performance")
            st.plotly_chart(
                px.bar(
                    bucket_summary,
                    x="Bucket",
                    y="avg_score",
                    text=bucket_summary["avg_score"].round(1),
                    labels={"avg_score": "Average Productivity (%)"}
                ),
                use_container_width=True
            )

            # Hour-wise productivity chart
            st.subheader("Hour-wise Productivity")
            st.plotly_chart(
                px.bar(
                    summary,
                    x="Label",
                    y="Score",
                    text=summary["Score"].round(1),
                    labels={"Score": "Productivity (%)"}
                ),
                use_container_width=True
            )

            # Smart textual insights
            best_bucket = bucket_summary.sort_values("avg_score", ascending=False).iloc[0]["Bucket"]
            worst_bucket = bucket_summary.sort_values("avg_score", ascending=True).iloc[0]["Bucket"]

            st.markdown("### 🧠 Smart Insights")
            st.write(f"• You perform best during the **{best_bucket}**.")
            st.write(f"• Your lowest energy period is **{worst_bucket}**.")
            st.write(f"• Your top focus hours are: **{focus_window}**.")
            st.write("• Schedule deep work during your peak focus window for best results.")

# -------------------- Goals --------------------

if menu == "Goals":
    st.header("🎯 Goals")

    goal_text = st.text_input("Enter your goal")
    goal_type = st.selectbox("Goal Type", ["Daily", "Weekly", "Monthly"])

    if st.button("Add Goal"):
        if goal_text.strip() == "":
            st.warning("Goal cannot be empty.")
        else:
            new_goal = pd.DataFrame(
                [[st.session_state.username, goal_text, goal_type, "No", datetime.today()]],
                columns=["Username", "Goal", "Type", "Completed", "Date"]
            )
            goals_df = pd.concat([goals_df, new_goal], ignore_index=True)
            save_goals(goals_df)
            st.success("Goal added!")

    user_goals = goals_df[goals_df["Username"] == st.session_state.username]

    if len(user_goals) == 0:
        st.info("No goals yet.")
    else:
        for i, row in user_goals.iterrows():
            c1, c2 = st.columns([5, 2])
            with c1:
                st.write(f"🎯 {row['Goal']} ({row['Type']})")
            with c2:
                if row["Completed"] == "No":
                    if st.button("Mark Done", key=f"goal_{i}"):
                        goals_df.loc[i, "Completed"] = "Yes"
                        save_goals(goals_df)
                        st.rerun()
                else:
                    st.success("Completed")

# -------------------- Streaks --------------------

if menu == "Streaks":
    st.header("🔥 Streaks")

    if len(user_data) == 0:
        st.info("No activity yet.")
    else:
        user_data["Date"] = pd.to_datetime(user_data["Date"], errors="coerce")
        days = sorted(user_data["Date"].dt.date.dropna().unique())

        if len(days) == 0:
            st.info("No valid dates.")
        else:
            streak = 1
            max_streak = 1

            for i in range(1, len(days)):
                if days[i] == days[i-1] + timedelta(days=1):
                    streak += 1
                    max_streak = max(max_streak, streak)
                else:
                    streak = 1

            st.metric("Current Streak", streak)
            st.metric("Longest Streak", max_streak)
