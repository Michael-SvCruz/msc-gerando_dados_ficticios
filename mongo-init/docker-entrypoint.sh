#!/bin/bash
set -e

echo "🔐 Ajustando permissões do keyfile..."
chmod 400 /etc/mongo-keyfile

echo "🚀 Iniciando mongod com --auth e --replSet"
mongod --replSet rs0 --bind_ip_all --auth --keyFile /etc/mongo-keyfile --fork --logpath /var/log/mongod.log

echo "⏳ Aguardando mongod subir..."
sleep 5

echo "🧠 Verificando status do replica set..."
if ! mongosh --eval "rs.status()" --quiet | grep -q '"ok" : 1'; then
  echo "🧱 Iniciando replica set..."
  mongosh <<EOF
rs.initiate({
  _id: "rs0",
  members: [{ _id: 0, host: "localhost:27017" }]
})
EOF
  sleep 5
fi

echo "👤 Criando usuário admin (se ainda não existir)..."
mongosh <<EOF || true
use admin
db.createUser({
  user: "admin",
  pwd: "senha123",
  roles: [ { role: "root", db: "admin" } ]
})
EOF


echo "✅ Setup MongoDB finalizado e rodando!"

# Fica rodando em foreground para manter o container vivo
tail -f /dev/null
