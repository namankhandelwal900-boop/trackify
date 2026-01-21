import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Trackify", layout="wide")

DATA_FILE = "life_tracker_data.csv"
USERS_FILE = "users.csv"
ADMIN_EMAIL = "namankhandelwal900@gmail.com"

# ---------------- DATA HELPERS ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Username", "Date", "Time", "Task", "Productive"])

def save_data(df):
    if st.session_state.get("demo", False):
        return
    df.to_csv(DATA_FILE, index=False)

# ---------------- USERS ----------------
def load_users():
    if os.path.exists(USERS_FILE):
        df = pd.read_csv(USERS_FILE, dtype=str).fillna("")
        df["email"] = df["email"].str.strip().str.lower()
        for col in ["reset_requested", "force_change"]:
            if col not in df.columns:
                df[col] = "no"
        return df

    return pd.DataFrame(columns=[
        "email", "username", "password",
        "status", "reset_requested", "force_change"
    ])

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

# ---------------- SESSION ----------------
if "route" not in st.session_state:
    st.session_state.route = "public"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "demo" not in st.session_state:
    st.session_state.demo = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "email" not in st.session_state:
    st.session_state.email = ""

# ---------------- LANDING ----------------
def landing_page():
    st.markdown("<h1 style='text-align:center;'>Trackify</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>From Chaos to Clarity</h3>", unsafe_allow_html=True)

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

# ---------------- LOGIN ----------------
def login_page():
    st.title("🔐 Trackify Access")
    users = load_users()

    tab1, tab2 = st.tabs(["Login", "Request Access"])

    # LOGIN
    with tab1:
        email = st.text_input("Email", key="login_email").strip().lower()
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_btn"):
            match = users[(users["email"] == email) & (users["password"] == password)]
            if match.empty:
                st.error("Invalid credentials")
            else:
                if match.iloc[0]["status"] == "approved":
                    st.session_state.logged_in = True
                    st.session_state.username = match.iloc[0]["username"]
                    st.session_state.email = email
                    st.session_state.route = "app"
                    st.rerun()
                else:
                    st.warning("Account not approved.")

        if st.button("Forgot Password?", key="forgot_btn"):
            st.session_state.route = "forgot_password"
            st.rerun()

    # SIGNUP
    with tab2:
        email = st.text_input("Email", key="reg_email").strip().lower()
        username = st.text_input("Username", key="reg_user")
        password = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Request Access", key="signup_btn"):
            users = load_users()
            existing_emails = users["email"].tolist()

            if not email or not username or not password:
                st.error("All fields are required.")
            elif email in existing_emails:
                st.warning("Email registered.")
            else:
                new = pd.DataFrame(
                    [[email, username, password, "approved", "no", "no"]],
                    columns=["email", "username", "password", "status", "reset_requested", "force_change"]
                )
                users = pd.concat([users, new], ignore_index=True)
                save_users(users)
                st.success("Account created! Please login.")
                st.session_state.route = "login"
                st.rerun()

# ---------------- FORGOT PASSWORD ----------------
def forgot_password_page():
    st.title("🔑 Forgot Password")
    users = load_users()
    email = st.text_input("Registered Email").strip().lower()

    if st.button("Request Reset", key="reset_btn"):
        if email not in users["email"].values:
            st.error("Email not found.")
        else:
            users.loc[users["email"] == email, "reset_requested"] = "yes"
            save_users(users)
            st.success("Reset request sent.")
            st.session_state.route = "login"
            st.rerun()

    if st.button("Back", key="back_login"):
        st.session_state.route = "login"
        st.rerun()

# ---------------- DEMO ----------------
def demo_mode():
    st.session_state.demo = True
    st.session_state.logged_in = True
    st.session_state.username = "Demo User"
    st.session_state.route = "app"
    st.rerun()

# ---------------- APP ----------------
def app_shell(df):
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("Menu", ["Planner", "Weekly", "Monthly"])

    if menu == "Planner":
        planner_view(df)
    elif menu == "Weekly":
        weekly_view(df)
    elif menu == "Monthly":
        monthly_view(df)

# ---------------- PLANNER ----------------
def planner_view(df):
    st.title("🗓️ Daily Planner")

    date = st.date_input("Date", datetime.today())
    time = st.selectbox("Hour", [f"{i:02d}:00" for i in range(24)])
    productive = st.selectbox("Productive?", ["Yes", "No"])
    task = st.text_input("Task")

    if st.button("Add Task"):
        new = {
            "Username": st.session_state.username,
            "Date": date.strftime("%Y-%m-%d"),
            "Time": time,
            "Task": task,
            "Productive": productive
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_data(df)
        st.success("Task added!")
        st.rerun()

# ---------------- STATS ----------------
def weekly_view(df):
    st.title("📅 Weekly Summary")
    if df.empty:
        st.info("No data yet.")
        return
    df["Date"] = pd.to_datetime(df["Date"])
    fig = px.histogram(df, x="Date", color="Productive")
    st.plotly_chart(fig, use_container_width=True)

def monthly_view(df):
    st.title("🗓️ Monthly Summary")
    weekly_view(df)

# ---------------- ROUTER ----------------
def router():
    if st.session_state.route == "public":
        landing_page()
    elif st.session_state.route == "login":
        login_page()
    elif st.session_state.route == "forgot_password":
        forgot_password_page()
    elif st.session_state.route == "demo":
        demo_mode()
    else:
        df = load_data()
        app_shell(df)

router()
