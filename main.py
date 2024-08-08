import datetime
import os
from datetime import date
import streamlit as st
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv
import gspread

load_dotenv('.env')


REDIRECT_URI = os.environ['REDIRECT_URI']
OKTA_CLIENT_ID = os.environ['OKTA_CLIENT_ID']
OKTA_CLIENT_SECRET = os.environ['OKTA_CLIENT_SECRET']
OKTA_AUTHORIZATION_ENDPOINT = os.environ['OKTA_AUTHORIZATION_ENDPOINT']
OKTA_TOKEN_ENDPOINT = os.environ['OKTA_TOKEN_ENDPOINT']
OKTA_USERINFO_ENDPOINT = os.environ['OKTA_USERINFO_ENDPOINT']
client = OAuth2Session(OKTA_CLIENT_ID, OKTA_CLIENT_SECRET, redirect_uri=REDIRECT_URI)


# Custom CSS
def load_css():
    st.markdown("""
  <style>
  .big-font {
      font-size:30px !important;
      font-weight: bold;
  }
  .stButton>button {
      color: #4F8BF9;
      border-radius: 50px;
      height: 3em;
      width: 100%;
  }
  </style>
  """, unsafe_allow_html=True)


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def add_bg_gradient():
    st.markdown(
        f"""
           <style>
           .stApp {{
               background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
           }}
           </style>
           """,
        unsafe_allow_html=True
    )
    st.query_params.clear()


def list_emails() -> list:
    gc = gspread.service_account_from_dict(dict(st.secrets["gsheets"]["service_account"]))
    sheet = gc.open('ays').sheet1
    all_values = sheet.col_values(2)
    return all_values[1:]


def login():
    add_bg_gradient()
    st.markdown("<h1 style='text-align: center;'>Welcome to AYS Attendance App</h1>", unsafe_allow_html=True)

    authorization_url, state = client.create_authorization_url(
        OKTA_AUTHORIZATION_ENDPOINT,
        scope="openid"
    )
    st.session_state.auth_url = authorization_url

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("Login with Okta", st.session_state.auth_url)


def callback():
    if 'code' in st.query_params:
        code = st.query_params['code']
        try:
            with st.spinner("Logging you in..."):
                token = client.fetch_token(
                    OKTA_TOKEN_ENDPOINT,
                    code=code,
                    scope="openid",
                    grant_type="authorization_code"
                )
                userinfo = client.get(OKTA_USERINFO_ENDPOINT).json()
                st.session_state['user'] = userinfo
                st.session_state.logged_in = True
                st.success("Successfully logged in!")
        except OAuthError as e:
            st.error(f"OAuth error: {e}")


def logout():
    add_bg_gradient()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()


def user_attendance():
    add_bg_gradient()
    st.title("User Attendance")
    with st.form("attendance_form", clear_on_submit=True):
        options = list_emails()
        email = st.selectbox("Select Email", options)
        present_date = date.today()
        today = st.date_input("Select Date", present_date)
        submit_button = st.form_submit_button("Submit Attendance")
    if submit_button:
        if email:  # Check if name and email are not empty
            gc = gspread.service_account_from_dict(dict(st.secrets["gsheets"]["service_account"]))
            sheet = gc.open('ays').sheet1
            last_row = len(sheet.get_all_values())
            sheet.update_cell(last_row + 1, 2, email)
            sheet.update_cell(last_row + 1, 3, str(today))
            # sheet.append_row([email, str(today)])
            st.success("Attendance recorded successfully!")
        else:
            st.error("Please enter both name and email.")


def registration():
    add_bg_gradient()
    st.title("User Registration")
    with st.form("registration_form", clear_on_submit=True):
        name = st.text_input("Enter your name")
        email = st.text_input("Enter your email")
        phone = st.text_input("Enter your phone number")
        present_date = date.today()
        today = st.date_input("Select Date", present_date)
        submit_button = st.form_submit_button("Submit Registration")
    if submit_button:
        if name and email:  # Check if name and email are not empty
            gc = gspread.service_account_from_dict(dict(st.secrets["gsheets"]["service_account"]))
            sheet = gc.open('ays').sheet1
            sheet.append_row([name, email, str(today), phone])
            st.success(f"Registration was successful {name}")
        else:
            st.error("Please enter both name and email.")


login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
user_attendance_page = st.Page(user_attendance, title="User Attendance")
reports = st.Page("tools/reports.py", title="Reports", icon="📊")
registration = st.Page(registration, title="Registration", icon="📝")


def main():
    load_css()
    # App header
    if 'code' in st.query_params:
        callback()

    if st.session_state.logged_in:
        st.sidebar.markdown(f"Welcome, {st.session_state['user'].get('name', 'Admin')}!")
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Tools": [reports],
            }
        )
    else:
        pg = st.navigation([login_page, user_attendance_page, registration])

    pg.run()


if __name__ == "__main__":
    main()
