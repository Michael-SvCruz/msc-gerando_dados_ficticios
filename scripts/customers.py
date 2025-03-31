from faker import Faker
from pymongo import MongoClient, UpdateOne
from datetime import datetime
import random
import os
import json
from typing import List, Dict

# Configurações
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:senha123@mongodb:27017/")
DB_NAME = "financial_db"
COLLECTION_NAME = "customers"
SEQUENCE_COLLECTION = "counters"  # Coleção para controle de sequência

class CustomerGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")
        self.existing_emails = set()
        self.existing_cpf_cnpj = set()
        self.last_customer_id = self._get_last_customer_id()

    def _get_last_customer_id(self) -> int:
        """Obtém o último ID usado do MongoDB ou inicia em 100000"""
        with MongoClient(MONGO_URI) as client:
            last_customer = client[DB_NAME][COLLECTION_NAME].find_one(
                {}, sort=[("customer_id", -1)]
            )
            return last_customer["customer_id"] if last_customer else 100000

    def _generate_customer_id(self) -> int:
        """Gera ID incremental único"""
        self.last_customer_id += 1
        return self.last_customer_id

    def _generate_unique_email(self) -> str:
        """Gera email único"""
        while True:
            email = self.faker.unique.email()
            if email not in self.existing_emails:
                self.existing_emails.add(email)
                return email

    def _generate_unique_cpf_cnpj(self, customer_type: str) -> str:
        """Gera CPF/CNPJ único"""
        while True:
            doc = self.faker.cpf() if customer_type == "Individual" else self.faker.cnpj()
            if doc not in self.existing_cpf_cnpj:
                self.existing_cpf_cnpj.add(doc)
                return doc

    def generate_customers(self, num_customers: int) -> List[Dict]:
        """Gera clientes com todos os campos únicos"""
        customers = []
        for _ in range(num_customers):
            customer_type = random.choice(["Individual", "Business"])
            created_at = self.faker.date_time_this_decade()
            
            customers.append({
                "customer_id": self._generate_customer_id(),
                "name": self.faker.name(),
                "email": self._generate_unique_email(),
                "phone_number": self.faker.phone_number(),
                "address": self.faker.address().replace("\n", ", "),
                "customer_type": customer_type,
                "cpf": self._generate_unique_cpf_cnpj("Individual") if customer_type == "Individual" else None,
                "cnpj": self._generate_unique_cpf_cnpj("Business") if customer_type == "Business" else None,
                "created_at": created_at,
                "updated_at": self.faker.date_time_between_dates(datetime_start=created_at),
                "metadata": {
                    "generated_at": datetime.now(),
                    "source": "script_v3",
                    "batch_id": self.faker.uuid4()
                }
            })
        return customers

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Garante índices únicos"""
        self.collection.create_index("customer_id", unique=True)
        self.collection.create_index("email", unique=True)
        self.collection.create_index("cpf", unique=True, partialFilterExpression={"cpf": {"$type": "string"}})
        self.collection.create_index("cnpj", unique=True, partialFilterExpression={"cnpj": {"$type": "string"}})

    def insert_customers(self, customers: List[Dict]) -> Dict:
        """Insere clientes com tratamento de erros"""
        try:
            result = self.collection.insert_many(customers, ordered=False)
            return {
                "inserted": len(result.inserted_ids),
                "errors": []
            }
        except Exception as e:
            error_details = []
            if hasattr(e, 'details') and 'writeErrors' in e.details:
                for error in e.details['writeErrors']:
                    if error['code'] == 11000:  # Código de duplicata
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
    print("🚀 Iniciando geração de clientes...")
    generator = CustomerGenerator()
    db_handler = MongoDBHandler()
    
    # Gera dados
    customers = generator.generate_customers(10000)
    print(f"🔢 IDs gerados: {customers[0]['customer_id']} a {customers[-1]['customer_id']}")
    
    # Insere no MongoDB
    result = db_handler.insert_customers(customers)
    
    # Resultados
    print("\n📊 Resultado:")
    print(f"→ Clientes inseridos com sucesso: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:  # Mostra até 3 erros
            print(f"   - Campo '{error['field']}' com valor duplicado: {error['value']}")
    
    # Backup
    save_backup(customers, "/app/datasets/customers_backup.json")
    print("✅ Concluído!")