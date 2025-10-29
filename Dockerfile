FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/* 

WORKDIR /app

COPY backend/requirements.txt /app/backend/

RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

CMD ["python3", "backend/main.py"]