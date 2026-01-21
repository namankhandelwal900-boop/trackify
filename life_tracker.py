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

# ---------------- USER CSV CLEAN + LOAD ----------------
def clean_users_df(df):
    df = df.copy()

    required_cols = ["email", "username", "password", "status", "reset_requested", "force_change"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "no" if col in ["reset_requested", "force_change"] else ""

    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"] != ""]
    df = df.drop_duplicates(subset=["email"], keep="first")

    return df

def load_users():
    if os.path.exists(USERS_FILE):
        df = pd.read_csv(USERS_FILE, dtype=str).fillna("")

        # Normalize emails
        df["email"] = df["email"].str.strip().str.lower()

        # Auto-add missing columns
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

def is_gmail(email):
    return email.endswith("@gmail.com")

# ---------------- SESSION INIT ----------------
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

# ---------------- LANDING PAGE ----------------
def landing_page():
    st.markdown("<h1 style='text-align:center;'>Trackify</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>From Chaos to Clarity</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Built by <b>Naman Khandelwal</b></p>", unsafe_allow_html=True)

    st.write("")
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
    st.write("A 24-hour productivity & life tracking system.")

# ---------------- LOGIN PAGE ----------------
def login_page():
    st.markdown("## 🔐 Trackify Access")

    tab1, tab2 = st.tabs(["Login", "Request Access"])
    users = load_users()

    # ---------- LOGIN ----------
    with tab1:
        email = st.text_input("Email", key="login_email").strip().lower()
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

                    if match.iloc[0]["force_change"] == "yes":
                        st.session_state.route = "force_change"
                    else:
                        st.session_state.route = "app"

                    st.rerun()
                elif status == "pending":
                    st.warning("Your request is pending approval.")
                else:
                    st.error("Your account is blocked.")

        if st.button("Forgot Password?"):
            st.session_state.route = "forgot_password"
            st.rerun()

    # ---------- SIGNUP ----------
    with tab2:
        email = st.text_input("Email", key="reg_email").strip().lower()
        username = st.text_input("Username", key="reg_user")
        password = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Request Access"):
         users = load_users()

    email_clean = email.strip().lower()

    existing_emails = users["email"].astype(str).str.strip().str.lower().tolist()

    if email_clean == "" or username == "" or password == "":
        st.error("All fields are required.")

    elif email_clean in existing_emails:
        st.warning("Email registered.")

    else:
        status = "approved"  # Instant access (Type B)

        new = pd.DataFrame(
            [[email_clean, username, password, status, "no", "no"]],
            columns=["email", "username", "password", "status", "reset_requested", "force_change"]
        )

        users = pd.concat([users, new], ignore_index=True)
        save_users(users)

        st.success("Account created! You can now login.")
        st.session_state.route = "login"
        st.rerun()

# ---------------- FORGOT PASSWORD PAGE ----------------
def forgot_password_page():
    st.title("🔑 Forgot Password")

    users = load_users()
    email = st.text_input("Enter your registered email").strip().lower()

    if st.button("Request Reset"):
        if email not in users["email"].values:
            st.error("Email not found.")
        else:
            users.loc[users["email"] == email, "reset_requested"] = "yes"
            save_users(users)

            st.success("Reset request sent to admin.")
            st.session_state.route = "login"
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.route = "login"
        st.rerun()


# ---------------- FORCE PASSWORD CHANGE ----------------
def force_change_password_page():
    if not st.session_state.get("email"):
        st.session_state.route = "login"
        st.rerun()

    st.title("🔒 Change Your Password")

    users = load_users()
    email = st.session_state.get("email")

    st.warning("You must change your password before accessing the app.")

    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        if not new_pass or not confirm_pass:
            st.error("All fields are required.")
            return

        if new_pass != confirm_pass:
            st.error("Passwords do not match.")
            return

        users.loc[users["email"] == email, "password"] = new_pass
        users.loc[users["email"] == email, "force_change"] = "no"
        users.loc[users["email"] == email, "reset_requested"] = "no"

        save_users(users)

        st.success("Password updated successfully!")
        st.session_state.route = "app"
        st.rerun()


# ---------------- ADMIN PANEL ----------------
def admin_panel():
    st.title("👑 Trackify Admin Panel")

    users = load_users()

    if users.empty:
        st.info("No users found.")
        return

    total = len(users)
    approved = len(users[users["status"] == "approved"])
    pending = len(users[users["status"] == "pending"])
    blocked = len(users[users["status"] == "blocked"])
    reset_requests = len(users[users["reset_requested"] == "yes"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Users", total)
    c2.metric("Approved", approved)
    c3.metric("Pending", pending)
    c4.metric("Reset Requests", reset_requests)

    st.divider()

    for i, row in users.iterrows():
        with st.expander(row["email"]):
            st.write("Username:", row["username"])
            st.write("Status:", row["status"])
            st.write("Reset Requested:", row["reset_requested"])
            st.write("Force Change:", row["force_change"])

            col1, col2, col3, col4 = st.columns(4)

            if col1.button("Approve", key=f"approve_{i}"):
                users.at[i, "status"] = "approved"
                save_users(users)
                st.rerun()

            if col2.button("Block", key=f"block_{i}"):
                users.at[i, "status"] = "blocked"
                save_users(users)
                st.rerun()

            if col3.button("Allow Reset", key=f"reset_{i}"):
                users.at[i, "force_change"] = "yes"
                users.at[i, "reset_requested"] = "no"
                save_users(users)
                st.success("User will be forced to reset password.")
                st.rerun()

            if col4.button("Delete", key=f"delete_{i}"):
                users = users.drop(i)
                save_users(users)
                st.rerun()


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

    st.session_state.route = "app"
    st.rerun()


# ---------------- APP SHELL ----------------
def app_shell(df, demo=False):
    st.sidebar.success(f"Logged in: {st.session_state.username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.demo = False
        st.session_state.route = "public"
        st.rerun()

    if st.session_state.get("email") == ADMIN_EMAIL:
        if st.sidebar.button("👑 Admin Panel"):
            st.session_state.route = "admin"
            st.rerun()

    if demo:
        st.warning("You are in Demo Mode. Data will not be saved.")

    menu = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Planner", "Weekly", "Monthly", "Insights"]
    )

    if menu == "Dashboard":
        st.title("📊 Dashboard")
        st.write("Welcome to Trackify.")

    elif menu == "Planner":
        planner_view(df, demo)

    elif menu == "Weekly":
        weekly_view(df)

    elif menu == "Monthly":
        monthly_view(df)

    elif menu == "Insights":
        st.title("🔍 Insights")
        st.write("Insights coming soon.")


# ---------------- PLANNER ----------------
def planner_view(df, demo=False):
    st.subheader("🗓️ Daily Planner (24 Hours)")

    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("Date", datetime.today())

    with col2:
        time = st.selectbox("Hour", [f"{i:02d}:00" for i in range(24)])

    with col3:
        productive = st.selectbox("Productive?", ["Yes", "No"])

    task = st.text_input("Task")

    if st.button("Add Task"):
        if task.strip() == "":
            st.error("Task cannot be empty.")
            return

        new_row = {
            "Username": st.session_state.username,
            "Date": date.strftime("%Y-%m-%d"),
            "Time": time,
            "Task": task,
            "Productive": productive
        }

        if demo:
            st.session_state.demo_df = pd.concat(
                [st.session_state.demo_df, pd.DataFrame([new_row])],
                ignore_index=True
            )
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)

        st.success("Task added!")
        st.rerun()


# ---------------- WEEKLY VIEW ----------------
def weekly_view(df):
    st.subheader("📅 Weekly Summary")

    df_user = df[df["Username"] == st.session_state.username].copy()
    if df_user.empty:
        st.info("No data yet.")
        return

    df_user["Date"] = pd.to_datetime(df_user["Date"])
    last_7 = datetime.now() - timedelta(days=7)
    week_df = df_user[df_user["Date"] >= last_7]

    if week_df.empty:
        st.info("No data for last 7 days.")
        return

    fig = px.histogram(
        week_df,
        x="Date",
        color="Productive",
        title="Weekly Productivity"
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------- MONTHLY VIEW ----------------
def monthly_view(df):
    st.subheader("🗓️ Monthly Summary")

    df_user = df[df["Username"] == st.session_state.username].copy()
    if df_user.empty:
        st.info("No data yet.")
        return

    df_user["Date"] = pd.to_datetime(df_user["Date"])
    last_30 = datetime.now() - timedelta(days=30)
    month_df = df_user[df_user["Date"] >= last_30]

    if month_df.empty:
        st.info("No data for last 30 days.")
        return

    fig = px.histogram(
        month_df,
        x="Date",
        color="Productive",
        title="Monthly Productivity"
    )
    st.plotly_chart(fig, use_container_width=True)
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

    if r == "forgot_password":
        forgot_password_page()
        st.stop()

    if r == "force_change":
        force_change_password_page()
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

    if st.session_state.get("demo", False):
        df = st.session_state.demo_df
    else:
        df = load_data()

    app_shell(df, demo=st.session_state.get("demo", False))
    st.stop()


# ---------------- RUN APP ----------------
router()

