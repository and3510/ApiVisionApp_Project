FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Evita prompts interativos ao instalar pacotes
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza e instala dependências necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    libboost-all-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements.txt para usar cache
COPY requirements.txt .

# Instala as dependências Python sem cache de pip
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto
COPY . .

# Expõe a porta da aplicação
EXPOSE 8000

# Comando para iniciar o servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
