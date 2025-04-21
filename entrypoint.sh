#!/bin/bash
set -e

# Permissão no keyfile
chmod 400 /etc/mongo-keyfile

# Inicia o mongod temporariamente sem auth
mongod --replSet rs0 --bind_ip_all --keyFile /etc/mongo-keyfile --fork --logpath /var/log/mongod.log

# Espera o mongod subir
sleep 5

# Inicia o replica set
mongosh <<EOF
rs.initiate({
  _id: "rs0",
  members: [{ _id: 0, host: "mongodb:27017" }]
})
EOF

# Espera o PRIMARY
sleep 5

# Cria o usuário root
mongosh <<EOF
use admin
db.createUser({
  user: "admin",
  pwd: "senha123",
  roles: [ { role: "root", db: "admin" } ]
})
EOF

# Para o mongod temporário
mongosh -u admin -p senha123 --authenticationDatabase admin --eval "db.shutdownServer()"

# Espera sair do ar
sleep 3

# Inicia o mongod definitivo com auth e replicaset
exec mongod --replSet rs0 --bind_ip_all --auth --keyFile /etc/mongo-keyfile
