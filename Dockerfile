# Use uma imagem oficial do Python como base
FROM python:3.9-slim-buster

# Define o diretório de trabalho no container
WORKDIR /app

# Copia o arquivo .env para o container
COPY .env ./

# Copia o arquivo de dependências para o container
COPY Pipfile Pipfile.lock ./

# Instala as dependências do projeto
RUN pip install pipenv && pipenv install --system --deploy

# Copia o restante do código para o container
COPY . .

# Comando para iniciar o bot
CMD ["python", "simbi-info.py"]