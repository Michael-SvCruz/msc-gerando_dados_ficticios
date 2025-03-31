from faker import Faker
from pymongo import MongoClient
from datetime import datetime
import random
import os
import json
from typing import List, Dict

# Configurações
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:senha123@mongodb:27017/")
DB_NAME = "financial_db"
CUSTOMERS_COLLECTION = "customers"
ACCOUNTS_COLLECTION = "accounts"

class AccountGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")
        self.last_account_id = self._get_last_account_id()
        self.existing_account_numbers = set()

    def _get_last_account_id(self) -> int:
        """Obtém o último account_id do MongoDB ou inicia em 10000"""
        with MongoClient(MONGO_URI) as client:
            last_account = client[DB_NAME][ACCOUNTS_COLLECTION].find_one(
                {}, sort=[("account_id", -1)]
            )
            return last_account["account_id"] if last_account else 10000

    def _generate_account_number(self) -> str:
        """Gera número de conta no formato 00000-1 (BBAN básico)"""
        while True:
            number = f"{random.randint(10000, 99999)}-{random.randint(1, 9)}"
            if number not in self.existing_account_numbers:
                self.existing_account_numbers.add(number)
                return number

    def generate_accounts(self, customers: List[Dict], max_accounts_per_customer: int = 3) -> List[Dict]:
        """Gera contas para cada cliente com dados únicos"""
        accounts = []
        for customer in customers:
            num_accounts = random.randint(1, max_accounts_per_customer)
            
            for _ in range(num_accounts):
                self.last_account_id += 1
                created_at = self.faker.date_time_this_decade()
                
                accounts.append({
                    "account_id": self.last_account_id,
                    "account_number": self._generate_account_number(),
                    "customer_id": customer["customer_id"],
                    "type": random.choice(["CHECKING", "SAVINGS", "INVESTMENT", "BUSINESS"]),
                    "balance": round(random.uniform(100, 1000000), 2),
                    "currency": "BRL",
                    "opening_date": created_at,
                    "last_activity": self.faker.date_time_between_dates(datetime_start=created_at),
                    "status": random.choices(
                        ["ACTIVE", "INACTIVE", "BLOCKED"], 
                        weights=[0.85, 0.1, 0.05]
                    )[0],
                    "metadata": {
                        "branch_code": f"{random.randint(1000, 9999)}",
                        "generated_at": datetime.now()
                    }
                })
        return accounts

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
    
    def get_customers(self, sample_size: int = None) -> List[Dict]:
        """Obtém clientes existentes do MongoDB"""
        collection = self.db[CUSTOMERS_COLLECTION]
        query = {} if not sample_size else {"$sample": {"size": sample_size}}
        return list(collection.find(query, {"customer_id": 1}))

    def save_accounts(self, accounts: List[Dict]) -> Dict:
        """Salva contas no MongoDB com tratamento de erros"""
        try:
            result = self.db[ACCOUNTS_COLLECTION].insert_many(accounts, ordered=False)
            return {
                "inserted": len(result.inserted_ids),
                "errors": []
            }
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
    print("🚀 Iniciando geração de contas bancárias...")
    
    # Inicializa serviços
    db_handler = MongoDBHandler()
    account_generator = AccountGenerator()
    
    # Obtém clientes existentes
    customers = db_handler.get_customers()
    if not customers:
        raise Exception("❌ Nenhum cliente encontrado no MongoDB. Execute customers.py primeiro!")
    
    print(f"🔍 Encontrados {len(customers)} clientes no banco de dados")
    
    # Gera contas
    accounts = account_generator.generate_accounts(customers)
    print(f"💳 Geradas {len(accounts)} contas (média de {len(accounts)/len(customers):.1f} por cliente)")
    
    # Salva no MongoDB
    result = db_handler.save_accounts(accounts)
    
    # Resultados
    print("\n📊 Resultado:")
    print(f"→ Contas inseridas com sucesso: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo duplicado: {error['field']} = {error['value']}")
    
    # Backup
    save_backup(accounts, "/app/datasets/accounts_backup.json")
    print("✅ Concluído!")