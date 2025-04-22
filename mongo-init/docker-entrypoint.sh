#!/bin/bash
set -e

# Função para log com timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Função para aguardar o MongoDB ficar pronto
wait_for_mongo() {
    local retries=30
    while [ $retries -gt 0 ]; do
        if mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries-1))
        sleep 1
    done
    return 1
}

# Tratamento de erro
handle_error() {
    log "❌ Erro na linha $1"
    exit 1
}
trap 'handle_error $LINENO' ERR

log "🔐 Ajustando permissões do keyfile..."
chmod 400 /etc/mongo-keyfile

log "🌐 Obtendo IP externo..."
EXTERNAL_IP=$(curl -s ifconfig.me)
if [ -z "$EXTERNAL_IP" ]; then
    log "❌ Falha ao obter IP externo"
    exit 1
fi
log "→ IP externo detectado: $EXTERNAL_IP"

log "🚀 Iniciando mongod temporariamente sem autenticação..."
mongod --replSet rs0 --bind_ip_all --keyFile /etc/mongo-keyfile --fork --logpath /var/log/mongod.log

log "⏳ Aguardando mongod subir..."
if ! wait_for_mongo; then
    log "❌ MongoDB não iniciou corretamente"
    exit 1
fi

log "🔄 Iniciando replica set com IP externo..."
if ! mongosh --quiet <<EOF
rs.initiate({
  _id: "rs0",
  members: [{ 
    _id: 0, 
    host: "$EXTERNAL_IP:27017",
    priority: 1
  }]
})
EOF
then
    log "❌ Falha ao iniciar replica set"
    exit 1
fi

log "⏳ Aguardando replica set inicializar..."
sleep 10

log "👤 Criando usuário admin..."
if ! mongosh --quiet <<EOF
use admin
db.createUser({
  user: "$MONGO_INITDB_ROOT_USERNAME",
  pwd: "$MONGO_INITDB_ROOT_PASSWORD",
  roles: [ { role: "root", db: "admin" } ]
})
EOF
then
    log "❌ Falha ao criar usuário admin"
    exit 1
fi

log "🛑 Parando mongod temporário..."
mongosh admin -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --quiet --eval "db.shutdownServer()" || true

log "⏳ Aguardando mongod parar completamente..."
while pgrep mongod > /dev/null; do
    sleep 1
done

log "🚀 Iniciando mongod definitivo com autenticação..."
exec mongod --replSet rs0 --bind_ip_all --auth --keyFile /etc/mongo-keyfile