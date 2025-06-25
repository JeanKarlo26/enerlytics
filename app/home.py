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

@st.cache_resource 
def getPfactura(): 
    return asidebar.obtenerPeriodos()

def getPreviousPfactura(pfacturas, periodo):
    selected_index = pfacturas.index(periodo)
    return pfacturas[selected_index + 1]
        
@st.cache_resource 
def getCiclo(periodo): 
    return asidebar.obtenerCiclos(periodo)

@st.cache_resource 
def getRuta(periodo, ciclo): 
    return asidebar.obtenerRutas(periodo, ciclo)


def hide_sidebar():
    st.markdown( """ <style> [data-testid="stSidebar"] { display: none; } </style> """, unsafe_allow_html=True, )

######  FUNCIONES DE VISTA ###### 
def tableroMando():
    pfacturas = getPfactura()
    selectPeriodo = st.sidebar.selectbox('Periodo:', pfacturas, key='selectPeriodo')
    periodoPrevio = getPreviousPfactura(pfacturas, selectPeriodo)

    ciclos = getCiclo(selectPeriodo)
    if "-- Todos --" not in ciclos:
        ciclos.insert(0, "-- Todos --")
    selectCiclo = st.sidebar.selectbox('Ciclo:', ciclos, key='selectCiclos')

    if selectCiclo != '-- Todos --':
        rutas = getRuta(selectPeriodo, selectCiclo)
        if "-- Todos --" not in rutas:
            rutas.insert(0, "-- Todos --")
        selectRuta = st.sidebar.selectbox('Ruta:', rutas, key='selectRuta')
    st.sidebar.markdown("---")
    dashboard.view()

def page2():
    st.title("Second page")

def carga_de_datos():
    cargarAchivos.view()

auth.validate_session()
if 'auth' not in st.session_state:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    hide_sidebar()
    login.login_view()

else:

    pages = {
        "Opciones": [ 
            st.Page(tableroMando, title="Tablero de Mando", icon='📊'),
            st.Page(carga_de_datos, title="Cargar Datos", icon='📤'),
            st.Page(page2, title="Otro", icon='📤')
        ]
    }


    pg = st.navigation(pages)
    pg.run()

    st.sidebar.write(f"Usuario: {auth.user_session['username']}")
    if st.sidebar.button("Cerrar Sesión"):
        auth.end_session()
