import streamlit as st
from controllers.auth import Auth


class LoginView:
    def __init__(self):
        self.authController = Auth()

    def login_view(self):        
        with st.form("formLogin"):
            st.title("🔐 Inicio de Sesión")
            username = st.text_input("Nombre de Usuario")
            password = st.text_input("Contraseña", type="password")

            if st.form_submit_button('Iniciar Sesión'):

                if self.authController.verify_password(username, password):

                    self.authController.getToken(username)

                    if self.authController.user_session:
                        self.authController.validate_session()

                        if not self.authController.user_session:
                            self.authController.create_session(username)

                    else:
                        self.authController.create_session(username)
                        
                    st.rerun()
                else:
                    st.error("Nombre de usuario o contraseña incorrectos")
