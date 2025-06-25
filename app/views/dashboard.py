import streamlit as st
from controllers.auth import Auth


class DashboardView:
    def __init__(self):
        self.authController = Auth()

    def view(self):
        st.write('hola')