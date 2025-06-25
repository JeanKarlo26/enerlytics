import jwt
import streamlit as st
import os
from dotenv import load_dotenv
from controllers.conection import MongoDBConnection
import bcrypt
import uuid
import time

config_path = os.path.join(os.path.dirname(__file__), "../../config/.env")

load_dotenv(dotenv_path=config_path)
SECRET_KEY = os.getenv("SECRET_KEY")

class Auth:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.colectionUsers = self.conexion.get_collection('tblUsers')
        self.colectionSessions = self.conexion.get_collection('tblSessions')

        if 'auth' not in st.session_state:
            self.user_session = None
        else:
            user_session = jwt.decode(st.session_state['auth'], SECRET_KEY, algorithms="HS256")
            self.user_session = user_session

    def verify_password(self, username, password):
        user = self.colectionUsers.find_one({"username": username})
        if user:
            return bcrypt.checkpw(password.encode('utf-8'), user['password'])
        return False

    def register_user(self, username, password, permissions=[], estado=False):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.colectionUsers.insert_one({"username": username, "password": hashed, "permissions": permissions, "estado": estado})
        return True

    def get_permissions(self, username):
        user = self.colectionUsers.find_one({"username": username})
        if user:
            return user.get('permissions', [])
        return []

    def has_permission(self, username, permission):
        user_permissions = self.get_permissions(username)
        return permission in user_permissions

    def create_session(self, username):
        token = str(uuid.uuid4())
        self.colectionSessions.delete_many({"username": username})

        session_data = {
            "username": username,
            "token": token,
            "created_at": time.time()
        }

        self.colectionSessions.insert_one(session_data)
        session_data["_id"] = str(session_data["_id"])
        session = jwt.encode(session_data, SECRET_KEY, algorithm="HS256")
        st.session_state['auth'] = session
        self.user_session = session
    
    def getToken(self, username):
        session = self.colectionSessions.find_one(
            {"username": username},
            sort=[("created_at", -1)]
        )

        if session:
            session["_id"] = str(session["_id"])
            user_session = jwt.encode(session, SECRET_KEY, algorithm="HS256")
            self.user_session = session
            st.session_state['auth'] = user_session


    def validate_session(self, session_duration=7200):
        if self.user_session:
            session = self.colectionSessions.find_one({"token": self.user_session['token']})

            if session and (time.time() - session['created_at']) < session_duration:
                session["_id"] = str(session["_id"])
                user_session = jwt.encode(session, SECRET_KEY, algorithm="HS256")
                self.user_session = session
                st.session_state['auth'] = user_session

    def end_session(self):
        self.colectionSessions.delete_one({"token": self.user_session['token']})
        st.session_state.pop('auth', None)
        self.user_session = None
        st.rerun()