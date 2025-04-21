#!/bin/bash
set -e

echo "🔐 Ajustando permissões do keyfile..."
chmod 400 /etc/mongo-keyfile

echo "🚀 Iniciando mongod com --auth e --replSet"
mongod --replSet rs0 --bind_ip_all --auth --keyFile /etc/mongo-keyfile --fork --logpath /var/log/mongod.log

echo "⏳ Aguardando mongod subir..."
sleep 5

echo "🌐 Obtendo IP externo..."
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "→ IP externo detectado: $EXTERNAL_IP"

echo "🧠 Verificando status do replica set..."
if ! mongosh --eval "rs.status()" --quiet | grep -q '"ok" : 1'; then
  echo "🔄 Iniciando replica set..."
  mongosh <<EOF
rs.initiate({
  _id: "rs0",
  members: [{ _id: 0, host: "mongodb:27017" }]
})
EOF

  echo "⏳ Aguardando replica set inicializar..."
  sleep 5

  echo "📝 Reconfigurando com IP externo..."
  mongosh <<EOF
cfg = rs.conf()
cfg.members[0].host = "$EXTERNAL_IP:27017"
rs.reconfig(cfg, { force: true })
EOF
fi

echo "👤 Criando usuário admin (se ainda não existir)..."
mongosh <<EOF || true
use admin
db.createUser({
  user: "$MONGO_INITDB_ROOT_USERNAME",
  pwd: "$MONGO_INITDB_ROOT_PASSWORD",
  roles: [ { role: "root", db: "admin" } ]
})
EOF

echo "✅ Setup MongoDB finalizado e rodando!"
echo "→ Replica set configurado com IP: $EXTERNAL_IP"
echo "→ Mongo Express deve estar acessível em: http://$EXTERNAL_IP:8081"

# Mantém o container rodando e mostra os logs do MongoDB
tail -f /var/log/mongod.log