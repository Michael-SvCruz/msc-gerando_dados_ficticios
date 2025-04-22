import random
from faker import Faker
from pymongo import MongoClient
from datetime import datetime
import os
import json
from typing import List, Dict

# Configurações do MongoDB
MONGO_URI = os.getenv("MONGO_URI", "$MONGO_URI")
DB_NAME = "financial_db"
CUSTOMERS_COLLECTION = "customers"
DIGITAL_ACTIVITY_COLLECTION = "digital_activity"

class DigitalActivityGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_digital_activity(self, customers: List[Dict], max_activities_per_customer: int = 5) -> List[Dict]:
        """Gera atividades digitais para os clientes"""
        digital_activity_data = []
        for customer in customers:
            num_activities = random.randint(1, max_activities_per_customer)

            for _ in range(num_activities):
                activity_id = self.faker.uuid4()
                activity_type = random.choice(["Login", "Transfer", "Payment", "Card Purchase"])
                timestamp = self.faker.date_time_this_year()
                ip_address = self.faker.ipv4_public()
                device_type = random.choice(["Mobile", "Desktop", "Tablet", "Smart TV"])

                digital_activity_data.append({
                    "activity_id": activity_id,
                    "customer_id": customer["customer_id"],
                    "activity_type": activity_type,
                    "timestamp": timestamp,
                    "ip_address": ip_address,
                    "device_type": device_type,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return digital_activity_data

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_customers(self, sample_size: int = None) -> List[Dict]:
        """Obtém clientes do MongoDB"""
        collection = self.db[CUSTOMERS_COLLECTION]
        query = {} if not sample_size else {"$sample": {"size": sample_size}}
        return list(collection.find(query, {"customer_id": 1}))

    def save_digital_activities(self, digital_activities_data: List[Dict]) -> Dict:
        """Salva as atividades digitais no MongoDB"""
        try:
            result = self.db[DIGITAL_ACTIVITY_COLLECTION].insert_many(digital_activities_data, ordered=False)
            return {"inserted": len(result.inserted_ids), "errors": []}
        except Exception as e:
            error_details = []
            if hasattr(e, 'details') and 'writeErrors' in e.details:
                for error in e.details['writeErrors']:
                    error_details.append({
                        "field": list(error['keyPattern'].keys())[0],
                        "value": error['keyValue']
                    })
            return {
                "inserted": e.details.get('nInserted', 0),
                "errors": error_details
            }

def save_backup(data: List[Dict], filename: str):
    """Salva backup em JSON"""
    with open(filename, "w") as f:
        json.dump(data, f, default=str, indent=2)
    print(f"📁 Backup salvo em {filename}")

if __name__ == "__main__":
    print("🚀 Iniciando geração de atividades digitais...")

    # Inicializa os serviços
    db_handler = MongoDBHandler()
    activity_generator = DigitalActivityGenerator()

    # Obtém clientes do MongoDB
    customers = db_handler.get_customers()
    if not customers:
        raise Exception("❌ Nenhum cliente encontrado no MongoDB. Execute customers.py primeiro!")

    print(f"🔍 Encontrados {len(customers)} clientes no banco de dados")

    # Gera atividades digitais
    digital_activities = activity_generator.generate_digital_activity(customers)
    print(f"✅ Geradas {len(digital_activities)} atividades digitais")

    # Salva no MongoDB
    result = db_handler.save_digital_activities(digital_activities)

    # Exibe resultados
    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")

    # Backup
    save_backup(digital_activities, "/app/datasets/digital_activity_backup.json")
    print("✅ Concluído!")
