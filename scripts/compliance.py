import random
from faker import Faker
from pymongo import MongoClient
from datetime import datetime
import os
import json
from typing import List, Dict

# Configurações
MONGO_URI = os.getenv("MONGO_URI", "$MONGO_URI")
DB_NAME = "financial_db"
CUSTOMERS_COLLECTION = "customers"
COMPLIANCE_COLLECTION = "compliance"

class ComplianceGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_compliance(self, customers: List[Dict], max_records_per_customer: int = 2) -> List[Dict]:
        """Gera registros de compliance para cada cliente"""
        compliance_data = []
        for customer in customers:
            num_records = random.randint(1, max_records_per_customer)
            
            for _ in range(num_records):
                compliance_id = self.faker.uuid4()
                compliance_type = random.choice(["KYC", "AML", "LGPD"])
                status = random.choices(
                    ["Pending", "Completed", "Rejected"], 
                    weights=[0.4, 0.5, 0.1]  # Distribuição mais realista
                )[0]
                review_date = self.faker.date_time_this_year()
                comments = self.faker.sentence() if status == "Rejected" else ""

                compliance_data.append({
                    "compliance_id": compliance_id,
                    "customer_id": customer["customer_id"],
                    "compliance_type": compliance_type,
                    "status": status,
                    "review_date": review_date,
                    "comments": comments,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return compliance_data

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_customers(self, sample_size: int = None) -> List[Dict]:
        """Obtém clientes do MongoDB"""
        collection = self.db[CUSTOMERS_COLLECTION]
        query = {} if not sample_size else {"$sample": {"size": sample_size}}
        return list(collection.find(query, {"customer_id": 1}))

    def save_compliance(self, compliance_data: List[Dict]) -> Dict:
        """Salva os registros de compliance no MongoDB"""
        try:
            result = self.db[COMPLIANCE_COLLECTION].insert_many(compliance_data, ordered=False)
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
    print("🚀 Iniciando geração de registros de compliance...")

    # Inicializa serviços
    db_handler = MongoDBHandler()
    compliance_generator = ComplianceGenerator()

    # Obtém clientes do MongoDB
    customers = db_handler.get_customers()
    if not customers:
        raise Exception("❌ Nenhum cliente encontrado no MongoDB. Execute customers.py primeiro!")

    print(f"🔍 Encontrados {len(customers)} clientes no banco de dados")

    # Gera registros de compliance
    compliance_records = compliance_generator.generate_compliance(customers)
    print(f"✅ Gerados {len(compliance_records)} registros de compliance")

    # Salva no MongoDB
    result = db_handler.save_compliance(compliance_records)
    
    # Exibe resultados
    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")

    # Backup
    save_backup(compliance_records, "/app/datasets/compliance_backup.json")
    print("✅ Concluído!")
