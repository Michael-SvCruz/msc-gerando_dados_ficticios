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
ACCOUNTS_COLLECTION = "accounts"
INVESTMENTS_COLLECTION = "investments"

class InvestmentGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_investments(self, accounts: List[Dict], max_investments_per_account: int = 3) -> List[Dict]:
        """Gera investimentos para cada conta"""
        investment_data = []
        for account in accounts:
            num_investments = random.randint(1, max_investments_per_account)

            for _ in range(num_investments):
                investment_id = self.faker.uuid4()
                investment_type = random.choice(["Stocks", "Fixed Income", "Real Estate Funds", "Crypto"])
                amount = round(random.uniform(1000, 100000), 2)

                # Geração de datas seguras
                purchase_date = self.faker.date_this_decade()
                maturity_date = purchase_date + relativedelta(years=random.randint(1, 10))

                status = random.choice(["Active", "Closed"])

                investment_data.append({
                    "investment_id": investment_id,
                    "customer_id": account["customer_id"],
                    "account_id": account["account_id"],
                    "investment_type": investment_type,
                    "amount": amount,
                    "purchase_date": purchase_date.isoformat(),
                    "maturity_date": maturity_date.isoformat(),
                    "status": status,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return investment_data

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_accounts(self) -> List[Dict]:
        """Obtém contas com os respectivos customer_id e account_id"""
        collection = self.db[ACCOUNTS_COLLECTION]
        return list(collection.find({}, {"customer_id": 1, "account_id": 1}))

    def save_investments(self, investment_data: List[Dict]) -> Dict:
        """Salva investimentos no MongoDB"""
        try:
            result = self.db[INVESTMENTS_COLLECTION].insert_many(investment_data, ordered=False)
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
    print("🚀 Iniciando geração de investimentos...")

    # Inicializa os serviços
    db_handler = MongoDBHandler()
    investment_generator = InvestmentGenerator()

    # Obtém contas do MongoDB
    accounts = db_handler.get_accounts()
    if not accounts:
        raise Exception("❌ Nenhuma conta encontrada no MongoDB. Execute accounts.py primeiro!")

    print(f"🔍 Encontradas {len(accounts)} contas no banco de dados")

    # Gera investimentos
    investments = investment_generator.generate_investments(accounts)
    print(f"✅ Gerados {len(investments)} investimentos")

    # Salva no MongoDB
    result = db_handler.save_investments(investments)

    # Exibe resultados
    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")

    # Backup
    save_backup(investments, "/app/datasets/investments_backup.json")
    print("✅ Concluído!")
