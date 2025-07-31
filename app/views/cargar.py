import streamlit as st
from controllers.auth import Auth
from controllers.cargaArchivos import CargaArchivos
import time

class CargarArchivosView:
    def __init__(self):
        self.authController = Auth()
        self.cargarController = CargaArchivos()

    def view(self):
        st.title("Cargar Archivos en la Base de Datos")
        tipo = st.radio('Seleccione el Origen del Archivo', options=['Sigof', 'Optimus NGC', 'Reclamos'], horizontal=True)
        uploader = st.file_uploader('Cargar Archivo', type='xlsx', accept_multiple_files=True)
        st.divider()

        if st.button('Subir archivos', type="primary"):
            with st.status('Espere mientras procesamos la informacion...', expanded=True) as status:
                if len(uploader) != 0:

                    tipo, df = self.cargarController.verificarArchivo(tipo, uploader)

                    if tipo == 'noCoincide':
                        status.update(label="Error en la Carga!", state="error", expanded=False)
                    
                    if tipo == 'Optimus NGC':
                        self.cargarController.tratamientoDatosOptimus(df)
                        status.update(label="Carga de Archivos completa!", state="complete", expanded=False)

                    if tipo == 'Sigof':
                        resumen = self.cargarController.tratamientoDatosSigof(df)
                        status.update(label="Carga de Archivos completa!", state="complete", expanded=False)

                    if tipo == 'Reclamos':
                        st.write('Reclamos')
                        st.success('Por ahora')

                else:
                    st.warning("No se encontraron archivos.")


            if tipo == 'Sigof':
                st.write('Sigof')
                # self.cardsResult(totalDias, totalDuplicados, totalNuevos, totalRetirados, totalReincorporados, totalCambiados, totalNormal, totalSinLectura, totalObs, resumenObs)

            if tipo == 'noCoincide':
                st.write('No Coincide')
                # st.warning("El archivo no coincide con el tipo seleccionado.")