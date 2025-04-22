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
CREDIT_CARDS_COLLECTION = "credit_cards"

class CreditCardGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_credit_cards(self, customers: List[Dict], max_cards_per_customer: int = 2) -> List[Dict]:
        """Gera cartões de crédito para os clientes"""
        credit_card_data = []
        for customer in customers:
            num_cards = random.randint(1, max_cards_per_customer)
            
            for _ in range(num_cards):
                card_id = self.faker.uuid4()
                card_number = self.faker.credit_card_number()
                card_type = random.choice(["Visa", "MasterCard", "Elo", "American Express"])
                expiry_date = self.faker.date_this_decade().strftime("%m/%Y")  # Formato MM/YYYY
                credit_limit = round(random.uniform(1000, 50000), 2)
                current_balance = round(random.uniform(0, credit_limit), 2)

                # Gerando timestamps realistas
                created_at = self.faker.date_time_this_decade()
                updated_at = self.faker.date_time_between_dates(datetime_start=created_at)

                credit_card_data.append({
                    "card_id": card_id,
                    "customer_id": customer["customer_id"],
                    "card_number": card_number,
                    "card_type": card_type,
                    "expiry_date": expiry_date,
                    "credit_limit": credit_limit,
                    "current_balance": current_balance,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return credit_card_data

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_customers(self, sample_size: int = None) -> List[Dict]:
        """Obtém clientes do MongoDB"""
        collection = self.db[CUSTOMERS_COLLECTION]
        query = {} if not sample_size else {"$sample": {"size": sample_size}}
        return list(collection.find(query, {"customer_id": 1}))

    def save_credit_cards(self, credit_cards_data: List[Dict]) -> Dict:
        """Salva os cartões de crédito no MongoDB"""
        try:
            result = self.db[CREDIT_CARDS_COLLECTION].insert_many(credit_cards_data, ordered=False)
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
    print("🚀 Iniciando geração de cartões de crédito...")

    # Inicializa os serviços
    db_handler = MongoDBHandler()
    card_generator = CreditCardGenerator()

    # Obtém clientes do MongoDB
    customers = db_handler.get_customers()
    if not customers:
        raise Exception("❌ Nenhum cliente encontrado no MongoDB. Execute customers.py primeiro!")

    print(f"🔍 Encontrados {len(customers)} clientes no banco de dados")

    # Gera cartões de crédito
    credit_cards = card_generator.generate_credit_cards(customers)
    print(f"✅ Gerados {len(credit_cards)} cartões de crédito")

    # Salva no MongoDB
    result = db_handler.save_credit_cards(credit_cards)

    # Exibe resultados
    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")

    # Backup
    save_backup(credit_cards, "/app/datasets/credit_cards_backup.json")
    print("✅ Concluído!")
