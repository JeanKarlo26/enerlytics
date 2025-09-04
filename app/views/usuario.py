import streamlit as st
from controllers.servicios import ServicioController
from controllers.auth import Auth
import bcrypt

def volver():
    st.session_state.pop('vista_actual', None)
    st.session_state.pop('usuarioPassword', None)
    st.session_state.pop('usuarioEditar', None)

class UsuarioView:
    def __init__(self):
        self.permissions = ["Cargar sigof", "Cargar optimus", "Gestion usuario", "Recalcular coordenadas", "Servicios Electricos","Regularizar rutas"]
        self.servicioController = ServicioController()
        self.authController = Auth()
        self.servicio = self.servicioController.dfServicio['nombre'].unique().tolist()   

    def registroUsuario(self):
        with st.form("form_registro_usuario", clear_on_submit=True):
            st.subheader("🆕 Registrar nuevo usuario")
            username = st.text_input("Nombre de usuario")
            password = st.text_input("Contraseña", type="password")
            permisos = st.multiselect("Permisos", self.permissions)
            servicio = st.multiselect("Servicios", self.servicio)
            estado = st.checkbox("Activo", value=True)

            if st.form_submit_button("Registrar"):
                if username and password:
                    if self.authController.validar_duplicates(username):
                        self.authController.register_user(username, password, permissions=permisos, services=servicio, estado=estado)
                        st.success(f"✅ Usuario '{username}' registrado correctamente.")
                    else:
                        st.warning("⚠️ Debes ingresar nombre y contraseña.")
                else:
                    st.warning("⚠️ Debes ingresar nombre y contraseña.")

        st.button('Volver', icon='❌', key='1', on_click=volver)

    def callRegistroUsuario(self):
        st.session_state.vista_actual = "register_user"

    def actualizacionClave(self, username):
        st.subheader("🔒 Cambiar contraseña")
        nueva_pw = st.text_input("Nueva contraseña", type="password", key="nuevaPassword")

        if st.button("Actualizar contraseña"):
            if nueva_pw:
                hashed = bcrypt.hashpw(nueva_pw.encode('utf-8'), bcrypt.gensalt())
                self.authController.colectionUsers.update_one(
                    {"username": username},
                    {"$set": {"password": hashed}}
                )
                st.success(f"🔐 Contraseña actualizada.")
            else:
                st.warning("⚠️ Ingresa una nueva contraseña.")
        st.button('Volver', icon='❌', key='2', on_click=volver)

    def callChangePassword(self, usuario):
        st.session_state.vista_actual = "cambiar_password"
        st.session_state.usuarioPassword = usuario

    def editarUsuario(self, usuario_seleccionado):
        st.subheader("✏️ Editar usuario existente")

        datos_usuario = self.authController.colectionUsers.find_one({"username": usuario_seleccionado})

        if datos_usuario:
            permisos_actuales = datos_usuario.get("permissions", [])
            servicios_actuales = datos_usuario.get("services", [])
            estado_actual = datos_usuario.get("estado", False)

            with st.form("form_edicion_usuario"):
                nuevos_permisos = st.multiselect("Permisos", self.permissions, default=permisos_actuales)
                nuevos_servicios = st.multiselect("Permisos", self.servicio, default=servicios_actuales)
                nuevo_estado = st.checkbox("Activo", value=estado_actual)

                if st.form_submit_button("Guardar cambios"):
                    self.authController.colectionUsers.update_one(
                        {"username": usuario_seleccionado},
                        {"$set": {"permissions": nuevos_permisos, "services": nuevos_servicios, "estado": nuevo_estado}}
                    )
                    st.success(f"✅ Usuario '{usuario_seleccionado}' actualizado.")

        st.button('Volver', icon='❌', key='3', on_click=volver)
        

    def callEditUser(self, usuario):
        st.session_state.vista_actual = "editar_usuario"
        st.session_state.usuarioEditar = usuario

    def viewPrincipal(self):
        st.button('Agregar usuario', icon='➕', key='add', on_click=lambda: self.callRegistroUsuario())
        
        usuarios = list(self.authController.colectionUsers.find({}, {"_id": 0}))

        col1, col2 = st.columns(2)
        for i, usuario in enumerate(usuarios):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                with st.container():
                    st.markdown(f"### 🧑 {usuario['username']}")
                    estado = "🟢 Activo" if usuario.get("estado") else "🔴 Inactivo"
                    st.markdown(f"**Estado:** {estado}")

                    permisos = usuario.get("permissions", [])
                    if permisos:
                        st.markdown("**Permisos:** " + " ".join([f"`{p}`" for p in permisos]))
                    else:
                        st.markdown("**Permisos:** _Sin asignar_")

                    servicios = usuario.get("services", [])
                    if servicios:
                        st.markdown("**Servicios:** " + " ".join([f"`{p}`" for p in servicios]))
                    else:
                        st.markdown("**Servicios:** _Sin asignar_")

                    colA, colB = st.columns(2)
                    with colA:
                        st.button("✏️ Editar", key=f"edit_{usuario['username']}", on_click=lambda: self.callEditUser(usuario['username']))
                    with colB:
                        st.button("🔒 Cambiar contraseña", key=f"pw_{usuario['username']}", on_click=lambda: self.callChangePassword(usuario['username']))

                    st.markdown("---")

    def view(self):
        st.title("👥 Panel de usuarios")
        
        if 'vista_actual' not in st.session_state:
            self.viewPrincipal()

        elif st.session_state.vista_actual == "cambiar_password":
            self.actualizacionClave(st.session_state.usuarioPassword)

        elif st.session_state.vista_actual == "editar_usuario":
            self.editarUsuario(st.session_state.usuarioEditar)

        else:
            self.registroUsuario()
