import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date
import base64

# ✅ Page config MUST be the first Streamlit command
st.set_page_config(page_title="Expense Tracker", layout="wide")

# ✅ Set background from local image

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_url = get_img_as_base64(r"C:\\Users\\krish\\OneDrive\\Desktop\\exp track monit\\str_ui\\bg.jpg")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{img_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

API_URL = "http://localhost:8000"

# 🔐 Smart login system with incorrect-password feedback
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_failed" not in st.session_state:
        st.session_state.login_failed = False

    if not st.session_state.logged_in:
        with st.sidebar:
            st.title("🔐 Login")
            username = st.text_input("Username", key="user")
            password = st.text_input("Password", type="password", key="pass")

            if st.button("Login"):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.login_failed = False
                    st.rerun()
                else:
                    st.session_state.login_failed = True

            if st.session_state.login_failed:
                st.error("❌ Incorrect username or password.")

        return False
    return True

# 🚪 Logout button only after login
if "logged_in" in st.session_state and st.session_state.logged_in:
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.login_failed = False
        st.rerun()

# 🔒 Block access if not logged in
if not login():
    st.stop()

# ------------------ Main App UI ------------------ #

st.title("💰 Expense Tracker")
menu = st.sidebar.selectbox("Menu", ["Add Expense", "View & Analyze", "Update/Delete"])
monthly_budget = st.sidebar.number_input("Set Monthly Budget 💸", min_value=0.0, value=10000.0)

# ➕ Add Expense
if menu == "Add Expense":
    st.subheader("➕ Add a New Expense")
    title = st.text_input("Title")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.text_input("Category")
    exp_date = st.date_input("Date", value=date.today())

    # Show warning ONLY if amount is greater than 0
    if amount > 0:
        try:
            response = requests.get(f"{API_URL}/expenses/")
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df["date"] = pd.to_datetime(df["date"])
                df["month"] = df["date"].dt.to_period("M").astype(str)
                current_month = exp_date.strftime("%Y-%m")
                current_total = df[df["month"] == current_month]["amount"].sum()

                predicted_total = current_total + amount
                if predicted_total > monthly_budget:
                    st.warning(f"⚠ Adding ₹{amount:.2f} on {current_month} will exceed your monthly budget of ₹{monthly_budget:.2f}.\nCurrent: ₹{current_total:.2f}, After Add: ₹{predicted_total:.2f}")
        except:
            st.info("Could not check budget. Backend may be unavailable.")

    # Submit Expense
    if st.button("Submit"):
        if title and category:
            payload = {"title": title, "amount": amount, "category": category, "date": str(exp_date)}
            response = requests.post(f"{API_URL}/expenses/", json=payload)
            if response.status_code == 200:
                st.success("Expense added successfully!")
            else:
                st.error("Failed to add expense.")
        else:
            st.warning("Please fill all fields.")

# 📊 View & Analyze
elif menu == "View & Analyze":
    st.subheader("📊 View & Analyze Expenses")
    response = requests.get(f"{API_URL}/expenses/")
    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])

            st.write("### 📅 Filter by Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=df["date"].min().date())
            with col2:
                end_date = st.date_input("End Date", value=df["date"].max().date())
            filtered_df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

            st.dataframe(filtered_df)

            # Monthly Summary
            st.write("### 📆 Monthly Summary")
            filtered_df["month"] = filtered_df["date"].dt.to_period("M").astype(str)
            monthly_summary = filtered_df.groupby("month")["amount"].sum().reset_index().rename(columns={"amount": "Total"})
            st.table(monthly_summary)
            st.line_chart(monthly_summary.set_index("month"))

            # Weekly Summary
            st.write("### 🗓 Weekly Summary")
            filtered_df["week"] = filtered_df["date"].dt.to_period("W").astype(str)
            weekly_summary = filtered_df.groupby("week")["amount"].sum().reset_index().rename(columns={"amount": "Total"})
            st.table(weekly_summary)
            st.bar_chart(weekly_summary.set_index("week"))

            # Charts
            st.write("### 📦 Category-wise Bar Chart")
            cat_data = filtered_df.groupby("category")["amount"].sum().reset_index()
            st.bar_chart(cat_data.set_index("category"))
            st.write("### 🥧 Pie Chart")
            st.plotly_chart(px.pie(cat_data, names='category', values='amount', title='Category Breakdown'))

            # Cumulative
            st.write("### 📈 Cumulative Expense")
            filtered_df["cumulative"] = filtered_df["amount"].cumsum()
            st.line_chart(filtered_df.set_index("id")["cumulative"])

            # Budget Check
            current_month = date.today().strftime("%Y-%m")
            current_month_total = monthly_summary[monthly_summary["month"] == current_month]["Total"].sum()
            st.write(f"### 💡 This Month ({current_month}) Spent: ₹{current_month_total:.2f}")
            if current_month_total > monthly_budget:
                st.error(f"🚨 Budget Exceeded! Limit: ₹{monthly_budget:.2f}")
            else:
                st.success("✅ Within Budget")

            # Export CSV
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("📁 Download CSV", csv, "filtered_expenses.csv", "text/csv")
        else:
            st.info("No data to display.")
    else:
        st.error("Error fetching expenses.")

# ✏ Update/Delete
elif menu == "Update/Delete":
    st.subheader("✏ Update or ❌ Delete Expense")
    exp_id = st.number_input("Enter Expense ID", min_value=1, step=1)

    with st.expander("Update"):
        new_title = st.text_input("New Title")
        new_amount = st.number_input("New Amount", min_value=0.0)
        new_category = st.text_input("New Category")
        new_date = st.date_input("New Date", value=date.today())
        if st.button("Update"):
            payload = {"title": new_title, "amount": new_amount, "category": new_category, "date": str(new_date)}
            res = requests.put(f"{API_URL}/expenses/{exp_id}", json=payload)
            if res.status_code == 200:
                st.success("Updated successfully!")
            else:
                st.error("Update failed. Check ID or data.")

    with st.expander("Delete"):
        if st.button("Delete"):
            res = requests.delete(f"{API_URL}/expenses/{exp_id}")
            if res.status_code == 200:
                st.success("Deleted successfully.")
            else:
                st.error("Failed to delete. Check ID.")