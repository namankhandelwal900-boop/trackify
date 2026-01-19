import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Trackify", layout="wide")

ADMIN_EMAIL = "namankhandelwal900@gmail.com"
DATA_FILE = "life_tracker_data.csv"
USERS_FILE = "users.csv"

# ---------------- SESSION INIT ----------------
if "route" not in st.session_state:
    st.session_state.route = "public"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "demo" not in st.session_state:
    st.session_state.demo = False

# ---------------- DATA ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Username", "Date", "Time", "Task", "Productive"])

def save_data(df):
    if st.session_state.get("demo", False):
        st.warning("Demo mode: data not saved.")
        return
    df.to_csv(DATA_FILE, index=False)

# ---------------- USERS ----------------
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["email", "username", "password", "status"])

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def is_gmail(email):
    return email.lower().endswith("@gmail.com")

# ---------------- FOOTER ----------------
def footer():
    st.markdown(
        "<hr><p style='text-align:center; font-size:13px;'>Built by <b>Naman Khandelwal</b> • Trackify</p>",
        unsafe_allow_html=True
    )

# ---------------- LANDING PAGE ----------------
def landing_page():
    st.markdown("<h1 style='text-align:center;'>Trackify</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>From Chaos to Clarity</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Built by <b>Naman Khandelwal</b></p>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🚀 Try Demo"):
            st.session_state.route = "demo"
            st.rerun()

    with c2:
        if st.button("🔐 Request Access"):
            st.session_state.route = "login"
            st.rerun()

    with c3:
        if st.button("🔑 Login"):
            st.session_state.route = "login"
            st.rerun()

    st.divider()

    st.subheader("What is Trackify?")
    st.write("Trackify is a 24-hour productivity and life tracking system designed to help you gain clarity over your time.")

    st.subheader("Features")
    st.write("""
    • 24-hour planner  
    • Weekly & monthly analytics  
    • Productivity tracking  
    • Demo mode  
    • Invite-only access  
    """)

    footer()

# ---------------- DEMO MODE ----------------
def demo_mode():
    st.session_state.demo = True
    st.session_state.logged_in = True
    st.session_state.username = "Demo User"
    st.session_state.email = "demo@trackify.app"

    if "demo_df" not in st.session_state:
        st.session_state.demo_df = pd.DataFrame(
            columns=["Username", "Date", "Time", "Task", "Productive"]
        )

    st.sidebar.info("🧪 Demo Mode")
    app_shell(st.session_state.demo_df, demo=True)

# ---------------- LOGIN ----------------
def login_page():
    st.title("🔐 Trackify Access")

    users = load_users()
    tab1, tab2 = st.tabs(["Login", "Request Access"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            match = users[(users["email"] == email) & (users["password"] == password)]
            if match.empty:
                st.error("Invalid credentials")
            else:
                status = match.iloc[0]["status"]
                if status == "approved":
                    st.session_state.logged_in = True
                    st.session_state.username = match.iloc[0]["username"]
                    st.session_state.email = email
                    st.session_state.route = "app"
                    st.rerun()
                elif status == "pending":
                    st.warning("Your request is pending approval.")
                else:
                    st.error("Your account is blocked.")

    with tab2:
        email = st.text_input("Email", key="reg_email")
        username = st.text_input("Username", key="reg_user")
        password = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Request Access"):
            if email in users["email"].values:
                st.warning("Email already exists.")
            else:
                status = "approved" if is_gmail(email) else "pending"
                new = pd.DataFrame([[email, username, password, status]],
                                   columns=["email", "username", "password", "status"])
                users = pd.concat([users, new], ignore_index=True)
                save_users(users)
                st.success("Your request has been submitted. You’ll be notified once approved.")

    footer()

# ---------------- ADMIN PANEL ----------------
def admin_panel():
    st.title("👑 Admin Panel")

    users = load_users()

    total = len(users)
    approved = len(users[users["status"] == "approved"])
    pending = len(users[users["status"] == "pending"])
    blocked = len(users[users["status"] == "blocked"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users", total)
    c2.metric("Approved", approved)
    c3.metric("Pending", pending)
    c4.metric("Blocked", blocked)

    st.divider()

    for i, row in users.iterrows():
        with st.expander(row["email"]):
            st.write("Username:", row["username"])
            st.write("Status:", row["status"])

            col1, col2, col3 = st.columns(3)

            if col1.button("Approve", key=f"a{i}"):
                users.at[i, "status"] = "approved"
                save_users(users)
                st.rerun()

            if col2.button("Block", key=f"b{i}"):
                users.at[i, "status"] = "blocked"
                save_users(users)
                st.rerun()

            if col3.button("Delete", key=f"d{i}"):
                users = users.drop(i)
                save_users(users)
                st.rerun()

    footer()
# ---------------- APP SHELL ----------------
def app_shell(df, demo=False):
    user = st.session_state.username

    st.sidebar.success(f"Logged in: {user}")

    menu = st.sidebar.radio("Menu", ["Dashboard", "Planner", "Weekly", "Monthly"])

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.demo = False
        st.session_state.route = "public"
        st.rerun()

    if demo:
        st.warning("You are in Demo Mode. Data will not be saved.")

    # Filter by user
    user_df = df[df["Username"] == user]

    # ---------------- DASHBOARD ----------------
    if menu == "Dashboard":
        st.title("📊 Dashboard")

        if user_df.empty:
            st.info("No data yet.")
        else:
            prod = user_df["Productive"].value_counts().get("Yes", 0)
            non_prod = user_df["Productive"].value_counts().get("No", 0)

            c1, c2 = st.columns(2)
            c1.metric("Productive Tasks", prod)
            c2.metric("Non-Productive Tasks", non_prod)

            st.subheader("Recent Entries")
            st.dataframe(user_df.sort_values(by=["Date", "Time"], ascending=False))

    # ---------------- PLANNER ----------------
    elif menu == "Planner":
        st.title("🗓️ 24-Hour Planner")

        date = st.date_input("Select Date", datetime.today())
        time = st.selectbox("Hour", [f"{i:02d}:00" for i in range(24)])
        task = st.text_input("Task")
        productive = st.radio("Was it productive?", ["Yes", "No"])

        if st.button("Save Entry"):
            new_row = {
                "Username": user,
                "Date": str(date),
                "Time": time,
                "Task": task,
                "Productive": productive
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            if demo:
                st.session_state.demo_df = df
            else:
                save_data(df)

            st.success("Saved!")
            st.rerun()

        st.subheader("Your Entries")
        if user_df.empty:
            st.info("No entries yet.")
        else:
            st.dataframe(user_df.sort_values(by=["Date", "Time"], ascending=False))

    # ---------------- WEEKLY ----------------
    elif menu == "Weekly":
        st.title("📅 Weekly Summary")

        if user_df.empty:
            st.info("No data yet.")
        else:
            temp = user_df.copy()
            temp["Date"] = pd.to_datetime(temp["Date"])
            temp["Week"] = temp["Date"].dt.to_period("W").astype(str)

            weekly = temp.groupby("Week")["Productive"].value_counts().unstack(fill_value=0)

            st.dataframe(weekly)

            fig = px.bar(weekly, barmode="group", title="Weekly Productivity")
            st.plotly_chart(fig, use_container_width=True)

    # ---------------- MONTHLY ----------------
    elif menu == "Monthly":
        st.title("🗓️ Monthly Summary")

        if user_df.empty:
            st.info("No data yet.")
        else:
            temp = user_df.copy()
            temp["Date"] = pd.to_datetime(temp["Date"])
            temp["Month"] = temp["Date"].dt.to_period("M").astype(str)

            monthly = temp.groupby("Month")["Productive"].value_counts().unstack(fill_value=0)

            st.dataframe(monthly)

            fig = px.bar(monthly, barmode="group", title="Monthly Productivity")
            st.plotly_chart(fig, use_container_width=True)

    footer()


# ---------------- ROUTER ----------------
def router():
    r = st.session_state.route

    if r == "public":
        landing_page()
        st.stop()

    if r == "demo":
        demo_mode()
        st.stop()

    if r == "login":
        login_page()
        st.stop()

    if r == "admin":
        if st.session_state.get("email") != ADMIN_EMAIL:
            st.session_state.route = "public"
            st.rerun()
        admin_panel()
        st.stop()

    if not st.session_state.get("logged_in", False):
        st.session_state.route = "login"
        st.rerun()

    df = load_data()
    app_shell(df, demo=st.session_state.get("demo", False))
    st.stop()


# ---------------- RUN ----------------
router()
