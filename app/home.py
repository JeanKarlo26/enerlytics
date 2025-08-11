from controllers.auth import Auth
from controllers.aside import AsidebarConfig
import streamlit as st
from views.login import LoginView
from views.cargar import CargarArchivosView
from views.dashboard import DashboardView
from PIL import Image
import os

st.set_page_config(
    page_icon="📊",
    page_title="Enerlytics",
    layout="wide"
)

img1_path = os.path.abspath("assets/img/logo-electro.png")
img2_path = os.path.abspath("assets/img/logo-electro-2.png")

imagen = Image.open(img1_path)
imagen2 = Image.open(img2_path)
st.logo(imagen, icon_image=imagen2)

login = LoginView()
cargarAchivos = CargarArchivosView()
dashboard = DashboardView()

auth = Auth()
asidebar = AsidebarConfig()

@st.cache_data 
def getPfactura():
    print('hola')
    return asidebar.obtenerPeriodos()

def getPreviousPfactura(pfacturas, periodo):
    selected_index = pfacturas.index(periodo)
    if selected_index + 1 == len(pfacturas):
        return pfacturas[selected_index]
    return pfacturas[selected_index + 1]
        
@st.cache_data 
def getCiclo(periodo): 
    return asidebar.obtenerCiclos(periodo)

@st.cache_data 
def getRuta(periodo, ciclo): 
    return asidebar.obtenerRutas(periodo, ciclo)


def hide_sidebar():
    st.markdown( """ <style> [data-testid="stSidebar"] { display: none; } </style> """, unsafe_allow_html=True, )

######  FUNCIONES DE VISTA ###### 
def tableroMando():
    pfacturas = getPfactura()
    st.session_state.filtros_habilitados = st.session_state.get("filtros_habilitados", True)

    selectPeriodo = st.sidebar.selectbox('Periodo:', pfacturas, key='selectPeriodo', disabled=not st.session_state.filtros_habilitados)
    periodoPrevio = getPreviousPfactura(pfacturas, selectPeriodo)

    def seleccionar_ciclo(periodo):
        ciclos = getCiclo(periodo)
        if "-- Todos --" not in ciclos:
            ciclos.insert(0, "-- Todos --") 
        return st.sidebar.selectbox('Ciclo:', ciclos, key='selectCiclos', disabled=not st.session_state.filtros_habilitados)

    def seleccionar_ruta(periodo, ciclo):
        if ciclo == "-- Todos --":
            return "-- Todos --"
        rutas = getRuta(periodo, ciclo)
        if "-- Todos --" not in rutas:
            rutas.insert(0, "-- Todos --")
        return st.sidebar.selectbox('Ruta:', rutas, key='selectRuta', disabled=not st.session_state.filtros_habilitados)

    # selectCiclo = seleccionar_ciclo(selectPeriodo)
    # selectRuta = seleccionar_ruta(selectPeriodo, selectCiclo)

    selectCiclo = '-- Todos --'
    selectRuta = '-- Todos --'

    st.sidebar.markdown("---")
    dashboard.view(selectPeriodo, periodoPrevio, selectCiclo, selectRuta)

def page2():
    st.title("Second page")

auth.validate_session()
if 'auth' not in st.session_state:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    hide_sidebar()
    login.login_view()

else:

    pages = {
        "Opciones": [ 
            st.Page(tableroMando, title="Tablero de Mando", icon='📊'),
            st.Page(cargarAchivos.view, title="Cargar Datos", icon='📤'),
            st.Page(page2, title="Otro", icon='📤')
        ]
    }


    pg = st.navigation(pages)
    pg.run()

    st.sidebar.write(f"Usuario: {auth.user_session['username']}")
    if st.sidebar.button("Cerrar Sesión"):
        auth.end_session()
