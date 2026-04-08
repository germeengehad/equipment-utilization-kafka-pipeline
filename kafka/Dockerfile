# FROM python:3.10-slim

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# ENV PYTHONUNBUFFERED=1

# CMD ["python", "kafka/kafka_to_postgres.py"]

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --default-timeout=300 --retries 10 --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "kafka/kafka_to_postgres.py"]