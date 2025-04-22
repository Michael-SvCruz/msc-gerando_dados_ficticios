import random
from faker import Faker
from dateutil.relativedelta import relativedelta
from pymongo import MongoClient
from datetime import datetime
import os
import json
from typing import List, Dict

# Configurações do MongoDB
MONGO_URI = os.getenv("MONGO_URI", "$MONGO_URI")
DB_NAME = "financial_db"
CUSTOMERS_COLLECTION = "customers"
LOANS_COLLECTION = "loans"

class LoanGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_loans(self, customers: List[Dict], max_loans_per_customer: int = 2) -> List[Dict]:
        """Gera empréstimos para cada cliente"""
        loan_data = []
        for customer in customers:
            num_loans = random.randint(1, max_loans_per_customer)

            for _ in range(num_loans):
                loan_id = self.faker.uuid4()
                loan_type = random.choice(["Mortgage", "Auto", "Personal", "Business"])
                loan_amount = round(random.uniform(5000, 500000), 2)
                interest_rate = round(random.uniform(3, 15), 2)
                term = random.randint(12, 360)  # Prazo do empréstimo em meses

                # Geração de datas seguras
                start_date = self.faker.date_this_decade()
                end_date = start_date + relativedelta(months=term)

                loan_status = random.choice(["Active", "Paid Off", "Default"])

                loan_data.append({
                    "loan_id": loan_id,
                    "customer_id": customer["customer_id"],
                    "loan_type": loan_type,
                    "loan_amount": loan_amount,
                    "interest_rate": interest_rate,
                    "term": term,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "loan_status": loan_status,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return loan_data

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_customers(self) -> List[Dict]:
        """Obtém clientes com seus respectivos IDs"""
        collection = self.db[CUSTOMERS_COLLECTION]
        return list(collection.find({}, {"customer_id": 1}))

    def save_loans(self, loan_data: List[Dict]) -> Dict:
        """Salva empréstimos no MongoDB"""
        try:
            result = self.db[LOANS_COLLECTION].insert_many(loan_data, ordered=False)
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
    print("🚀 Iniciando geração de empréstimos...")

    # Inicializa os serviços
    db_handler = MongoDBHandler()
    loan_generator = LoanGenerator()

    # Obtém clientes do MongoDB
    customers = db_handler.get_customers()
    if not customers:
        raise Exception("❌ Nenhum cliente encontrado no MongoDB. Execute customers.py primeiro!")

    print(f"🔍 Encontrados {len(customers)} clientes no banco de dados")

    # Gera empréstimos
    loans = loan_generator.generate_loans(customers)
    print(f"✅ Gerados {len(loans)} empréstimos")

    # Salva no MongoDB
    result = db_handler.save_loans(loans)

    # Exibe resultados
    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")

    # Backup
    save_backup(loans, "/app/datasets/loans_backup.json")
    print("✅ Concluído!")
