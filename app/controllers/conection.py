import yaml
from pymongo.mongo_client import MongoClient
import pymongo
import streamlit as st

class MongoDBConnection:
    # def __init__(self):
    #     config_path = os.path.join(os.path.dirname(__file__), "../../config/settings.yaml")
    #     with open(config_path, "r") as file:
    #         config = yaml.safe_load(file)
    #         db_config = config["database"]
    #         self.client = MongoClient(db_config["host"])
    #         self.database = self.client[db_config["name"]]
    def __init__(self):
        uri = f"mongodb+srv://{st.secrets['mongo']['username']}:{st.secrets['mongo']['password']}@cluster0.zd4gw.mongodb.net/?retryWrites=true&w=majority"

        self.client = pymongo.MongoClient(uri)

        self.database = self.client["electrocentro"]

    def get_collection(self, collection_name):
        return self.database[collection_name]
    
    def guardar_en_mongo(self, df, collection, session=None):
        records = df.to_dict("records")
        if records:
            collection.insert_many(records, session=session)

    def close_connection(self):
        self.client.close()