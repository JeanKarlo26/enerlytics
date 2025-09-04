# import streamlit as st
# import pandas as pd
# from controllers.auth import Auth
# from controllers.servicios import ServicioController

# class RutasServicioView:
#     def __init__(self):
#         self.authController = Auth()
#         self.servicioController = ServicioController()
#         self.dfFicha = self.servicioController.dfFicha
#         self.dfServicio = self.servicioController.dfServicio
#         self.collectionSE = self.servicioController.collectionSE
#         self.collectionResultados = self.conexion.get_collection('tblResultadoFinal')

#     def addRuta(self, servicio, nueva_ruta):
#         self.collectionSE.update_one(
#             {'nombre': servicio},
#             {'$addToSet': {'rutas': nueva_ruta}}
#         )
#         if 'dfRutas' in st.session_state:
#             df_actual = st.session_state.dfRutas
#             df_filtrado = df_actual[df_actual != nueva_ruta]  # Elimina la ruta
#             st.session_state.dfRutas = df_filtrado.dropna()

#     def view(self, periodo, rutas):
#         df2 = pd.DataFrame(list(self.collectionResultados.find({'periodo': periodo})))

#         ruta2 = df2['ruta'].unique().tolist()


#         rutas_exclusivas = set(rutas) - set(ruta2)
#         # Mostrar en Streamlit
#         st.dataframe(rutas_exclusivas)
#         # st.write(st.session_state)
#         # serviciosData = self.authController.get_services(user_session['username'])
#         st.session_state.dfRutas = rutas_exclusivas
#         selectRuta = st.selectbox('Ruta: ', rutas_exclusivas)
#         selectServicio = st.selectbox('Servicio: ', self.dfServicio['nombre'].unique().tolist())
#         st.button(
#             'Actualizar servicio', icon='🔄', 
#             on_click=self.addRuta(selectServicio, selectRuta)
#         )

import streamlit as st
import pandas as pd
from controllers.auth import Auth
from controllers.servicios import ServicioController

class RutasServicioView:
    def __init__(self):
        self.authController = Auth()
        self.servicioController = ServicioController()
        self.dfFicha = self.servicioController.dfFicha
        self.dfServicio = self.servicioController.dfServicio
        self.collectionSE = self.servicioController.collectionSE
        self.collectionResultados = self.servicioController.conexion.get_collection('tblResultadoFinal')

    def addRuta(self, servicio, nueva_ruta):
        # Actualiza en MongoDB
        self.collectionSE.update_one(
            {'nombre': servicio},
            {'$addToSet': {'rutas': nueva_ruta}}
        )

        # Elimina la ruta del estado
        if 'dfRutas' in st.session_state:
            rutas_actuales = st.session_state.dfRutas
            rutas_filtradas = [r for r in rutas_actuales if r != nueva_ruta]
            st.session_state.dfRutas = rutas_filtradas

    def view(self, periodo, rutas):
        # Obtener rutas ya registradas en el periodo
        df2 = pd.DataFrame(list(self.collectionResultados.find({'periodo': periodo})))
        rutas_existentes = df2['ruta'].unique().tolist()

        # Filtrar rutas exclusivas
        rutas_exclusivas = sorted(list(set(rutas_existentes) - set(rutas)))

        # Mostrar tabla y controles
        # st.dataframe(pd.DataFrame({'Rutas disponibles': rutas_exclusivas}))
        # st.session_state.dfRutas = rutas_exclusivas

        if rutas_exclusivas:
            selectRuta = st.selectbox('Ruta:', rutas_exclusivas)
            selectServicio = st.selectbox('Servicio:', self.dfServicio['nombre'].unique().tolist())

            # st.button(
            #     'Actualizar servicio', icon='🔄', 
            #     on_click= lambda: self.addRuta(selectServicio, selectRuta)
            # )
            # Botón con ejecución diferida
            if st.button('Actualizar servicio', icon='🔄'):
                self.addRuta(selectServicio, selectRuta)
                st.success(f"Ruta '{selectRuta}' añadida al servicio '{selectServicio}'.")
        else:
            st.warning("No hay rutas disponibles para asignar.")