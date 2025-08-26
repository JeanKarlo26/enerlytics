import streamlit as st
from controllers.auth import Auth
from controllers.servicios import ServicioController
import pandas as pd
import itertools
from itertools import chain


def changeSelectServicio(servicio):
        st.session_state.selectBoxServicio = servicio

def volverRutas():
    st.session_state.pop('vista_actual', None)

def addServicioVista():
    st.session_state.vista_actual = 'addService'

class ServiciosView:
    def __init__(self):
        self.authController = Auth()
        self.servicioController = ServicioController()
        self.dfFicha = self.servicioController.dfFicha
        self.dfServicio = self.servicioController.dfServicio

        self.servicios_existentes = self.dfServicio['nombre'].dropna().unique().tolist()
        self.ciclos = sorted(self.dfFicha['ciclo'].unique().tolist())
        self.dfRutasTotales = self.dfFicha[['ruta', 'ciclo']].dropna().drop_duplicates()
        self.rutasAsignadas = list(itertools.chain.from_iterable(self.dfServicio['rutas'].dropna()))

        st.session_state.selectBoxServicio = ''
        st.session_state.selectBoxCiclo = '' 

    def getRutasPorLecturado(self, servicios):
        listas = self.dfServicio[self.dfServicio['nombre'].isin(servicios)]['rutas'].tolist()
        lista_total = list(chain.from_iterable(listas))
        return lista_total

    def addService(self):
        with st.form("formServicio", border=False):
            col1, col2 = st.columns(2, vertical_alignment="bottom")
            with col1:
                nuevo_servicio = st.text_input('Nombre del servicio', key="inputServicio")
            with col2:
                if st.form_submit_button('Agregar', icon='💾'):
                    servicio = {
                        'nombre': nuevo_servicio,
                        'rutas': []
                    }
                    self.servicioController.guardarServicio(servicio)
                    st.success(f'Guardado el servicio {nuevo_servicio}')

        st.button('Volver', icon='❌', on_click=volverRutas)

    def deleteRuta(self, ruta):
        rutas_actualizadas = [r for r in self.rutas[0] if r != ruta]
        service = {
            'nombre': st.session_state.selectBoxServicio,
            'rutas': rutas_actualizadas
        }
        self.servicioController.updateServicio(service)

    def addRuta(self):
        rutasGuardar = self.rutas[0] + st.session_state.rutaMultiSelect
        service = {
            'nombre': st.session_state.selectBoxServicio,
            'rutas': rutasGuardar
        }
        self.servicioController.updateServicio(service)

    def addRoutes(self):
        st.button('Agregar servicio', icon='➕', on_click=addServicioVista)
        
        col1, col2 = st.columns(2)
        with col1:
            if self.servicios_existentes:
                selectServcio = st.selectbox(
                    'Seleccionar servicio:',
                    self.servicios_existentes,
                    key="selectServicio"
                )
            else:
                st.info("Agrega al menos un servicio para continuar.")

        if selectServcio != st.session_state.selectBoxServicio: 
            st.session_state.selectBoxServicio = selectServcio

        dfTempRutas = self.dfServicio[self.dfServicio['nombre'] == st.session_state.selectBoxServicio]
        self.rutas = dfTempRutas['rutas'].tolist()

        with col2:
            selectCiclo = st.selectbox(
                'Seleccionar ciclo:',
                self.ciclos,
                key="selectCiclo"
            )

        if selectCiclo != st.session_state.selectBoxCiclo: 
            st.session_state.selectBoxCiclo = selectCiclo
        
        dfTemp = self.dfFicha[self.dfFicha['ciclo'] == st.session_state.selectBoxCiclo]
        rutasFU = dfTemp['ruta'].unique().tolist()

        rutasCoincidentes = list(set(rutasFU) & set(self.rutas[0]))
        rutasDisponibles = list(set(rutasFU) - set(self.rutas[0]))

        col1, col2 = st.columns(2)

        with col1:
            with st.expander(f'Todas las rutas del servicio: {len(self.rutas[0])}'):
                st.dataframe(pd.DataFrame(self.rutas[0]), hide_index=True)

            with st.expander(f'Lista de rutas en el servicio del ciclo seleccionado: {len(rutasCoincidentes)}'):
                for ruta in rutasCoincidentes:
                    col3, col4 = st.columns([3,1], vertical_alignment='center')
                    with col3:
                        st.write(ruta)
                    with col4:
                        st.button(f"❌ Eliminar", key=f"del_{ruta}", on_click=lambda r=ruta: self.deleteRuta(r))

        with col2:
            rutasMultiSelect =  st.multiselect('Rutas por servicio:', rutasDisponibles, key='rutaMultiSelect')

            if self.rutas[0] == st.session_state.rutaMultiSelect:
                st.warning('No se detectaron cambios.')

            st.button(
                'Actualizar ficha única', icon='🔄', 
                disabled=self.rutas[0] == st.session_state.rutaMultiSelect, 
                on_click=self.addRuta
            )

        dfPendientes = self.dfRutasTotales[~self.dfRutasTotales['ruta'].isin(self.rutasAsignadas)]
        with st.expander(f'Rutas pendientes de asignar: {len(dfPendientes)}'):
            st.dataframe(dfPendientes, hide_index=True)

    def view(self):
        st.title("🛣️ Gestión de servicios eléctricos")
        if 'vista_actual' in st.session_state:
            self.addService() 
        else:
            self.addRoutes()