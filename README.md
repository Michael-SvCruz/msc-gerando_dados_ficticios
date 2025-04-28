# 🏦 Geração de dados fictícios 
Gere dados fictícios de operações financeiras para portfólio, testes e demonstrações, com ambiente totalmente automatizado via Docker e MongoDB em replica set.
&nbsp;

# ✨ Objetivo
Este projeto simula um ambiente bancário completo, gerando dados sintéticos de clientes, contas, cartões, empréstimos, investimentos, transações e atividades digitais.\
Ideal para praticar ETL, ELT, integração com diversas ferramentas em ambiente Local ou em Cloud.
&nbsp;

# 🛠️ Principais Tecnologias Utilizadas
- Python 3.11 + Faker  
- MongoDB 6.0  
- Docker Desktop 
&nbsp;

# 🚀 Como executar o projeto
## Pré requisitos
- Docker Desktop
- Git

## Clone o repositório
Através do terminal navegue até a pasta que deseja clonar o repositório e execute o comando para clonar o mesmo.
```bash
git clone https://github.com/Michael-SvCruz/msc-gerando_dados_ficticios.git
```
## Configure as variáveis de ambiente
Crie o arquivo .env conforme abaixo.
#### Exemplo
Substitua ```<user>``` pelo usuário de sua escolha e ```<password>``` pela senha de sua escolha 
```bash
# MongoDB
MONGO_INITDB_ROOT_USERNAME=<user>
MONGO_INITDB_ROOT_PASSWORD=<password>

# Mongo Express (credenciais para acessar a interface web)
ME_CONFIG_BASICAUTH_USERNAME=<user>
ME_CONFIG_BASICAUTH_PASSWORD=<password>

# URLs de conexão
MONGO_URI=mongodb://<user>:<password>@mongodb:27017/?replicaSet=rs0&authSource=admin
```

## Suba o ambiente com o Docker Compose
Pelo terminal, na pasta raiz do projeto execute
```bash
docker compose up -d --build
```
Isso irá construir 3 Containers:
- financial_mongodb : MongoDB com configuração Replica Set e autenticação;
- mongo_express : Mongo Express (interface Web do MongoDB), lembre-se de utilizar as credenciais escolhidas no **.env** quando for acessar via navegador.
- data_generator_container : responsável por gerar os dados fictícios.

## Acesse os serviços
- **MongoDB:**
   - Host: localhost
   - Porta: 27017
   - Usuário/senha: conforme .env
   - Replica set: rs0
- **Mongo Express**
   - url: http://localhost:8081
   - Usuário/senha: conforme .env

## 🏗️ Estrutura do Projeto
```
.
├── scripts/
│   ├── accounts.py
│   ├── branches.py
│   ├── compliance.py
│   ├── credit_cards.py
│   ├── customers.py
│   ├── digital_activity.py
│   ├── investments.py
│   ├── loans.py
│   └── transactions.py
├── Dockerfile
├── Dockerfile.mongo
├── docker-compose.yml
├── mongo-init/
│   └── docker-entrypoint.sh
├── mongodb-keyfile
├── requirements.txt
├── .env
├── .gitignore
├── .gitattributes
└── LICENSE
```

## Como gerar dados fictícios
Primeiramente a ordem de execução dos arquivos de scripts dever ser a seguinte:
1. customers.py
2. accounts.py
3. o restante dos arquivos pode seguir a ordem que desejar.
Segue um exemplo de como executar um script:
```bash
docker exec -it data_generator_container python scripts/customers.py
```
OBS.: No script customers, controle a quantidade de registro criados alterando esse trecho do código:
```bash
# Gera dados
    customers = generator.generate_customers(100)
    print(f"🔢 IDs gerados: {customers[0]['customer_id']} a {customers[-1]['customer_id']}")
```
No caso do exemplo é gerado 100 registros por vez, os outros scripts geram registro dependendo da quantidade de registros já criados em customers.
#### Dica: 
A integração desse banco foi testada com a ferramenta Airbyte.

## 🔒 Segurança
- As credenciais do MongoDB são definidas via .env (não exponha em repositórios públicos);
- O replica set está configurado com autenticação e keyfile;
- O acesso externo é permitido para facilitar integrações, mas pode ser restrito em produção.

## 📄 Licença
Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).

## 🙋‍♂️ Contribuição
Sugestões, issues e pull requests são bem-vindos!
Sinta-se à vontade para adaptar o projeto para outros domínios de dados.

## 📞 Contato
Dúvidas ou sugestões?
Entre em contato pelo [LinkedIn](http://www.linkedin.com/in/michael-svcruz) ou abra uma issue no repositório.