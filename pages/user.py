import streamlit as st
import requests

st.header("User DashBoard")

user_page = st.sidebar.selectbox(
    "User",
    [
        "Today's Task",
        "Day wise Task",
        "Overall Analytics"
    ])