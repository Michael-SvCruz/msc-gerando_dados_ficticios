from faker import Faker
from pymongo import MongoClient
from datetime import datetime
import random
import os
import json

# Configuração do MongoDB (usando variáveis de ambiente)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:senha123@mongodb:27017/")
DB_NAME = "financial_db"
COLLECTION_NAME = "customers"

def generate_customers(num_customers=1000):  # Reduzi para 1000 para testes
    faker = Faker("pt_BR")
    customers = []
    
    for _ in range(num_customers):
        customer_type = random.choice(["Individual", "Business"])
        created_at = faker.date_time_this_decade()
        
        customer = {
            "customer_id": faker.uuid4(),
            "name": faker.name(),
            "email": faker.email(),
            "phone_number": faker.phone_number(),
            "address": faker.address().replace("\n", ", "),
            "customer_type": customer_type,
            "cpf": faker.cpf() if customer_type == "Individual" else None,
            "cnpj": faker.cnpj() if customer_type == "Business" else None,
            "created_at": created_at,
            "updated_at": faker.date_time_between_dates(datetime_start=created_at),
            "metadata": {
                "generated_at": datetime.now(),
                "source": "script_initial_load"
            }
        }
        customers.append(customer)
    
    return customers

def save_to_mongodb(data):
    try:
        # Conexão com o MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Insere os dados (em lotes de 100 para melhor performance)
        result = collection.insert_many(data)
        print(f"✅ {len(result.inserted_ids)} clientes inseridos com sucesso!")
        
        # Cria índices para consultas rápidas
        collection.create_index("customer_id", unique=True)
        collection.create_index("email")
        collection.create_index("cpf")
        collection.create_index("cnpj")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar no MongoDB: {e}")
        return False

if __name__ == "__main__":
    # Gerar dados
    customers_data = generate_customers(1000)  # Gera 1000 registros
    
    # Salvar no MongoDB
    if save_to_mongodb(customers_data):
        # Opcional: Salvar backup local em JSON
        with open("/app/datasets/customers_backup.json", "w") as f:
            json.dump(customers_data, f, default=str, indent=4)
        print("Backup JSON salvo em /app/datasets/customers_backup.json")