from controllers.conection import MongoDBConnection

class AsidebarConfig:
    def __init__(self):
        self.conexion = MongoDBConnection()
        self.collectionResultados = self.conexion.get_collection('tblResultadoFinal')

    def obtenerPeriodos(self):
        pipeline = [
            { '$group': { '_id': '$periodo' } },
            { '$sort': { '_id': -1 } }
        ]
        resultado = list(self.collectionResultados.aggregate(pipeline))
        return [doc['_id'] for doc in resultado]

    def obtenerCiclos(self, periodo):
        pipelineCiclo = [
            { '$match': { 'periodo': periodo } },
            { '$group': { '_id': '$ciclo' } },
            { '$sort': { '_id': 1 } }
        ]
        resultadoCiclo = list(self.collectionResultados.aggregate(pipelineCiclo))
        return [doc['_id'] for doc in resultadoCiclo]

    def obtenerRutas(self, periodo, ciclo):
        pipelineRuta = [
            { '$match': { 'periodo': periodo, 'ciclo': ciclo } },
            { '$group': { '_id': '$ruta' } },
            { '$sort': { '_id': 1 } }
        ]
        resultadoRuta = list(self.collectionResultados.aggregate(pipelineRuta))
        return [doc['_id'] for doc in resultadoRuta]

    def getAllCiclos(self):
        pipelineCiclo = [
            { '$group': { '_id': '$ciclo' } },
            { '$sort': { '_id': 1 } }
        ]
        resultadoCiclo = list(self.collectionResultados.aggregate(pipelineCiclo))
        return [doc['_id'] for doc in resultadoCiclo]

    def getRoutesCiclo(self, ciclo):
        pipelineRuta = [
            { '$match': { 'ciclo': ciclo } },
            { '$group': { '_id': '$ruta' } },
            { '$sort': { '_id': 1 } }
        ]
        resultadoRuta = list(self.collectionResultados.aggregate(pipelineRuta))
        return [doc['_id'] for doc in resultadoRuta]

    def getDataComplete(self, periodo):
        pipelineCiclo = [
            { '$match': { 'periodo': periodo } },
            { '$group': { 
                # "_id": NULL,
                "sumaTotalVenta": { "$sum": "$total_venta" },
                "sumaDescuento": { "$sum": "$descuento" }
             } },
            { '$sort': { '_id': 1 } }
        ]
        resultadoCiclo = list(self.collectionResultados.aggregate(pipelineCiclo))
        return [doc['_id'] for doc in resultadoCiclo]