from controllers.auth import Auth
from controllers.aside import AsidebarConfig
import streamlit as st
from views.login import LoginView
from views.cargar import CargarArchivosView
from views.servicios import ServiciosView
from views.dashboard import DashboardView
from views.analsisTemporal import AnalisisTemporal
from views.usuario import UsuarioView
from PIL import Image
import os
from dotenv import load_dotenv
import jwt

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
servicios = ServiciosView()
dashboard = DashboardView()
analisisTemporal = AnalisisTemporal()
usuario = UsuarioView()

auth = Auth()
asidebar = AsidebarConfig()

config_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(dotenv_path=config_path)
SECRET_KEY = os.getenv("SECRET_KEY")

if 'auth' in st.session_state:
    user_session = jwt.decode(st.session_state['auth'], SECRET_KEY, algorithms="HS256")
    permisos = auth.get_permissions(user_session['username'])
else:
    permisos = []

@st.cache_data 
def getPfactura():
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

    serviciosData = auth.get_services(user_session['username'])
    selectServicio = st.sidebar.multiselect('Servicio:', serviciosData, default=serviciosData, key='selectServicio')

    rutasPorServicio = servicios.getRutasPorLecturado(selectServicio)
    
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
    dashboard.view(selectPeriodo, periodoPrevio, selectCiclo, selectRuta, rutasPorServicio)

def tableroMandoTemporal():
    periodos_map = {
        '3 meses': 3,
        '6 meses': 6,
        '1 año': 12
    }
    pfacturas = getPfactura()
    st.session_state.filtros_habilitados = st.session_state.get("filtros_habilitados", True)

    selectPeriodo = st.sidebar.selectbox('Periodo:', ['3 meses', '6 meses', '1 año'], key='selectPeriodo')
    num_periodos = periodos_map.get(selectPeriodo, 3)
    
    pfacturas_ordenadas = sorted(pfacturas, reverse=True)
    pfacturas_filtradas = pfacturas_ordenadas[:num_periodos]

    serviciosData = auth.get_services(user_session['username'])
    selectServicio = st.sidebar.multiselect('Servicio:', serviciosData, default=serviciosData, key='selectServicio')
    rutasPorServicio = servicios.getRutasPorLecturado(selectServicio)

    st.sidebar.markdown("---")
    analisisTemporal.view(pfacturas_filtradas, rutasPorServicio)

auth.validate_session()
# st.cache_data.clear()

if 'auth' not in st.session_state:
    st.warning("Debes iniciar sesión para acceder a esta página.")
    hide_sidebar()
    login.login_view()

else:

    paginas_visibles = [
        st.Page(tableroMando, title="Tablero de Mando", icon='📊', url_path="tablero"),
        st.Page(tableroMandoTemporal, title="Analisis temporal", icon='📊', url_path="tableroTemporal")
    ]

    if "Cargar sigof" in permisos or "Cargar optimus" in permisos:
        paginas_visibles.append(
            st.Page(cargarAchivos.view, title="Cargar Datos", icon='📤', url_path="cargar-datos")
        )

    if "Servicios Electricos" in permisos:
        paginas_visibles.append(
            st.Page(servicios.view, title="Servicios Electricos", icon='🛣️', url_path="servicios-electricos")
        )

    if "Gestion usuario" in permisos:
        paginas_visibles.append(
            st.Page(usuario.view, title="Gestion de usuarios", icon='🕵🏻️', url_path="gestion-usuarios")
        )

    pages = {
        "Opciones": paginas_visibles
    }

    pg = st.navigation(pages)
    pg.run()

    st.sidebar.write(f"Usuario: {auth.user_session['username']}")
    if st.sidebar.button("Cerrar Sesión"):
        auth.end_session()
