import yaml
from pymongo.mongo_client import MongoClient
import os

class MongoDBConnection:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "../../config/settings.yaml")
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
            db_config = config["database"]
            self.client = MongoClient(db_config["host"])
            self.database = self.client[db_config["name"]]

    def get_collection(self, collection_name):
        return self.database[collection_name]
    
    def guardar_en_mongo(self, df, collection_name, session=None):
        collection = self.get_collection(collection_name)
        records = df.to_dict("records")
        if records:
            collection.insert_many(records, session=session)

    def close_connection(self):
        self.client.close()