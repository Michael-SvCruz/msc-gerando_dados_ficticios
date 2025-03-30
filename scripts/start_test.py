import os
from pymongo import MongoClient

# Conexão usando a variável de ambiente
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["financial_db"]

print("✅ Conectado ao MongoDB!")
print(f"Versão do Python: {os.sys.version}")
print(f"Coleções disponíveis: {db.list_collection_names()}")