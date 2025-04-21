#!/bin/bash
set -e

# Permissão no keyfile
chmod 400 /etc/mongo-keyfile
echo "🔐 Permissão no keyfile ajustada"

# Inicia o mongod temporariamente sem auth
mongod --replSet rs0 --bind_ip_all --keyFile /etc/mongo-keyfile --fork --logpath /var/log/mongod.log
echo "🚀 Iniciando mongod temporário para configuração inicial"

# Espera o mongod subir
sleep 5

# Inicia o replica set
mongosh <<EOF
rs.initiate({
  _id: "rs0",
  members: [{ _id: 0, host: "mongodb:27017" }]
})
EOF
echo "🧠 Replica set iniciado"

# Espera o PRIMARY
sleep 5

# Cria o usuário root
mongosh <<EOF
use admin
db.createUser({
  user: "$MONGO_INITDB_ROOT_USERNAME",
  pwd: "$MONGO_INITDB_ROOT_PASSWORD",
  roles: [ { role: "root", db: "admin" } ]
})
EOF
echo "👤 Usuário root criado"

# Para o mongod temporário
mongosh -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --eval "db.shutdownServer()"
echo "🛑 Parando mongod temporário"

# Espera sair do ar
sleep 3

# Inicia o mongod definitivo com auth e replicaset
exec mongod --replSet rs0 --bind_ip_all --auth --keyFile /etc/mongo-keyfile
echo "✅ MongoDB pronto com autenticação e replica set"