# Use a imagem oficial do Python 3.11
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os scripts
COPY scripts/ ./scripts/

# Comando padrão (opcional)
CMD ["python", "--version"]