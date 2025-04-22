import random
from faker import Faker
from pymongo import MongoClient
import os
import json
from datetime import datetime
from typing import List, Dict

# Configuração do MongoDB
MONGO_URI = os.getenv("MONGO_URI", "$MONGO_URI")
DB_NAME = "financial_db"
ACCOUNTS_COLLECTION = "accounts"
TRANSACTIONS_COLLECTION = "transactions"

class TransactionGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")

    def generate_transactions(self, accounts: List[Dict], max_transactions_per_account: int = 50) -> List[Dict]:
        """Gera transações aleatórias para cada conta"""
        transactions = []
        for account in accounts:
            num_transactions = random.randint(10, max_transactions_per_account)

            for _ in range(num_transactions):
                transaction_id = self.faker.uuid4()
                transaction_type = random.choice(["Deposit", "Withdrawal", "Transfer", "Payment"])
                amount = round(random.uniform(10, 5000), 2)
                currency = "BRL"
                transaction_date = self.faker.date_time_this_year().isoformat()
                description = self.faker.sentence()

                transactions.append({
                    "transaction_id": transaction_id,
                    "account_id": account["account_id"],
                    "customer_id": account["customer_id"],  # Inclui customer_id para rastreabilidade
                    "transaction_type": transaction_type,
                    "amount": amount,
                    "currency": currency,
                    "transaction_date": transaction_date,
                    "description": description,
                    "metadata": {
                        "generated_at": datetime.now()
                    }
                })
        return transactions

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]

    def get_accounts(self) -> List[Dict]:
        """Obtém contas bancárias vinculadas aos clientes"""
        collection = self.db[ACCOUNTS_COLLECTION]
        return list(collection.find({}, {"account_id": 1, "customer_id": 1}))

    def save_transactions(self, transactions: List[Dict]) -> Dict:
        """Salva transações no MongoDB"""
        try:
            result = self.db[TRANSACTIONS_COLLECTION].insert_many(transactions, ordered=False)
            return {"inserted": len(result.inserted_ids), "errors": []}
        except Exception as e:
            return {"inserted": 0, "errors": str(e)}

def save_backup(data: List[Dict], filename: str):
    """Salva backup em JSON"""
    with open(filename, "w") as f:
        json.dump(data, f, default=str, indent=2)
    print(f"📁 Backup salvo em {filename}")

if __name__ == "__main__":
    print("🚀 Iniciando geração de transações...")

    # Inicializa os serviços
    db_handler = MongoDBHandler()
    transaction_generator = TransactionGenerator()

    # Obtém contas do MongoDB
    accounts = db_handler.get_accounts()
    if not accounts:
        raise Exception("❌ Nenhuma conta encontrada no MongoDB. Execute accounts.py primeiro!")

    print(f"🔍 Encontradas {len(accounts)} contas no banco de dados")

    # Gera transações
    transactions = transaction_generator.generate_transactions(accounts)
    print(f"✅ Geradas {len(transactions)} transações")

    # Salva no MongoDB
    result = db_handler.save_transactions(transactions)

    print("\n📊 Resultado:")
    print(f"→ Registros inseridos: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros: {result['errors']}")

    # Backup
    save_backup(transactions, "/app/datasets/transactions_backup.json")
    print("✅ Concluído!")
