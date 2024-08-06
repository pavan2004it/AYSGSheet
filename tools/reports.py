import pandas as pd
import streamlit as st
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
# Set up Google Sheets credentials
scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


def reports():
    st.title("Attendance Reports")

    # Fetch all data from the Google Sheet

    gc = gspread.service_account_from_dict(dict(st.secrets["gsheets"]["service_account"]))
    sheet = gc.open('ays').sheet1
    # gc, authorized_user = gspread.oauth_from_dict(credentials)
    # sheet = gc.open('ays').sheet1
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        st.warning("No attendance records found.")
        return

    # Group by email and count unique dates
    attendance_summary = df.groupby('Email').agg({
        'Name': 'first',  # Get the first name associated with each email
        'Date': 'nunique'  # Count unique dates for each email
    }).reset_index()
    attendance_summary.columns = ['Email', 'Name', 'Days Present']

    # Display summary table
    st.subheader("Attendance Summary")
    st.dataframe(attendance_summary)

    # Bar chart of attendance
    st.subheader("Attendance Visualization")
    fig = px.bar(attendance_summary, x='Email', y='Days Present', text='Days Present',
                 hover_data=['Name'], color='Days Present',
                 height=400, title="Days Present by Member")
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig)

    # Pie chart of attendance distribution
    st.subheader("Attendance Distribution")
    fig_pie = px.pie(attendance_summary, values='Days Present', names='Email',
                     title='Distribution of Attendance')
    st.plotly_chart(fig_pie)

    # Recent attendance records
    st.subheader("Recent Attendance Records")
    recent_records = df.sort_values('Date', ascending=False).head(10)
    st.table(recent_records)

    # Download full report
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Full Report",
        data=csv,
        file_name="full_attendance_report.csv",
        mime="text/csv",
    )


# Call the function
reports()
