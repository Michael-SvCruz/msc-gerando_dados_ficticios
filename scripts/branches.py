from faker import Faker
from pymongo import MongoClient
from datetime import datetime
import random
import os
import json
from typing import List, Dict

# Configurações
MONGO_URI = os.getenv("MONGO_URI", "$MONGO_URI")
DB_NAME = "financial_db"
COLLECTION_NAME = "branches"

class BranchGenerator:
    def __init__(self):
        self.faker = Faker("pt_BR")
        self.existing_codes = set()

    def _generate_branch_code(self) -> str:
        """Gera código de agência único no formato XXXX-Y"""
        while True:
            code = f"{random.randint(1000, 9999)}-{random.randint(1, 9)}"
            if code not in self.existing_codes:
                self.existing_codes.add(code)
                return code

    def generate_branches(self, num_branches: int = 50) -> List[Dict]:
        """Gera dados de agências bancárias (versão simplificada)"""
        branches = []
        for _ in range(num_branches):
            created_at = self.faker.date_time_this_decade()
            
            branches.append({
                "branch_id": self.faker.uuid4(),
                "branch_code": self._generate_branch_code(),
                "name": self.faker.company(),
                "address": {
                    "street": self.faker.street_address(),
                    "city": self.faker.city(),
                    "state": self.faker.estado_sigla(),
                    "zip_code": self.faker.postcode()
                },
                "phone": self.faker.phone_number(),
                "opening_date": created_at,
                "last_renovation": self.faker.date_time_between_dates(datetime_start=created_at),
                "metadata": {
                    "generated_at": datetime.now()
                }
            })
        return branches

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Garante índices únicos"""
        self.collection.create_index("branch_code", unique=True)
        self.collection.create_index("branch_id", unique=True)

    def insert_branches(self, branches: List[Dict]) -> Dict:
        """Insere agências no MongoDB"""
        try:
            result = self.collection.insert_many(branches, ordered=False)
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
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    print(f"📁 Backup salvo em {filename}")

if __name__ == "__main__":
    print("🏦 Iniciando geração de agências bancárias...")
    
    generator = BranchGenerator()
    db_handler = MongoDBHandler()
    
    # Gera dados (50 agências por padrão)
    branches = generator.generate_branches()
    print(f"🏛  Geradas {len(branches)} agências")
    
    # Insere no MongoDB
    result = db_handler.insert_branches(branches)
    
    # Resultados
    print("\n📊 Resultado:")
    print(f"→ Agências inseridas: {result['inserted']}")
    if result['errors']:
        print(f"→ Erros de duplicata: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - Campo '{error['field']}' duplicado: {error['value']}")
    
    # Backup
    save_backup(branches, "/app/datasets/branches_backup.json")
    print("✅ Concluído!")